"""
Compact PPO (clipped surrogate) for MultiDiscrete actions.
Deliberately minimal and identical across all policy arms — the *only*
experimental manipulation is the policy architecture passed in.
"""
from __future__ import annotations

import dataclasses
import numpy as np
import torch
from torch.distributions import Categorical


@dataclasses.dataclass
class PPOConfig:
    steps_per_update: int = 2048
    epochs: int = 4
    minibatch: int = 256
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip: float = 0.2
    lr: float = 3e-4
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5


def _dist(logits):
    return Categorical(logits=logits)  # (B, n_nodes, n_levels) -> independent per node


def rollout(env, policy, n_steps, device):
    obs_l, act_l, logp_l, val_l, rew_l, done_l, infos = [], [], [], [], [], [], []
    obs, _ = env.reset()
    for _ in range(n_steps):
        o = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            logits, value = policy(o)
            d = _dist(logits)
            action = d.sample()                      # (1, n_nodes)
            logp = d.log_prob(action).sum(-1)        # (1,)
        a = action.squeeze(0).cpu().numpy()
        nobs, r, term, trunc, info = env.step(a)
        obs_l.append(obs); act_l.append(a); logp_l.append(logp.item())
        val_l.append(value.item()); rew_l.append(r); done_l.append(term or trunc)
        infos.append(info)
        obs = nobs if not (term or trunc) else env.reset()[0]
    batch = dict(
        obs=np.array(obs_l, dtype=np.float32), act=np.array(act_l),
        logp=np.array(logp_l, dtype=np.float32), val=np.array(val_l, dtype=np.float32),
        rew=np.array(rew_l, dtype=np.float32), done=np.array(done_l, dtype=np.float32),
    )
    return batch, infos


def gae(batch, cfg: PPOConfig):
    T = len(batch["rew"])
    adv = np.zeros(T, dtype=np.float32)
    last = 0.0
    for t in reversed(range(T)):
        nonterm = 1.0 - batch["done"][t]
        nxt_val = batch["val"][t + 1] if t + 1 < T else 0.0
        delta = batch["rew"][t] + cfg.gamma * nxt_val * nonterm - batch["val"][t]
        adv[t] = last = delta + cfg.gamma * cfg.gae_lambda * nonterm * last
    ret = adv + batch["val"]
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    return adv, ret


def ppo_update(policy, opt, batch, adv, ret, cfg: PPOConfig, device):
    obs = torch.as_tensor(batch["obs"], device=device)
    act = torch.as_tensor(batch["act"], device=device)
    old_logp = torch.as_tensor(batch["logp"], device=device)
    adv_t = torch.as_tensor(adv, device=device)
    ret_t = torch.as_tensor(ret, device=device)
    T = obs.shape[0]
    for _ in range(cfg.epochs):
        idx = torch.randperm(T, device=device)
        for s in range(0, T, cfg.minibatch):
            b = idx[s : s + cfg.minibatch]
            logits, value = policy(obs[b])
            d = _dist(logits)
            logp = d.log_prob(act[b]).sum(-1)
            ratio = torch.exp(logp - old_logp[b])
            surr = torch.min(
                ratio * adv_t[b],
                torch.clamp(ratio, 1 - cfg.clip, 1 + cfg.clip) * adv_t[b],
            )
            pi_loss = -surr.mean()
            v_loss = ((value - ret_t[b]) ** 2).mean()
            ent = d.entropy().sum(-1).mean()
            loss = pi_loss + cfg.vf_coef * v_loss - cfg.ent_coef * ent
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), cfg.max_grad_norm)
            opt.step()


def train(env, policy, total_steps, cfg: PPOConfig, device="cpu", log=None, phase=""):
    """Train `policy` in-place; append per-update stats to `log` (list of dicts)."""
    opt = torch.optim.Adam(policy.parameters(), lr=cfg.lr)
    steps_done = 0
    while steps_done < total_steps:
        n = min(cfg.steps_per_update, total_steps - steps_done)
        batch, infos = rollout(env, policy, n, device)
        adv, ret = gae(batch, cfg)
        ppo_update(policy, opt, batch, adv, ret, cfg, device)
        steps_done += n
        if log is not None:
            log.append(dict(
                phase=phase, steps=steps_done,
                mean_reward=float(batch["rew"].mean()),
                energy_saved=float(np.mean([i["energy_saved"] for i in infos])),
                budget_violation=float(np.mean([i["budget_violation"] for i in infos])),
                thermal_violation=float(np.mean([i["thermal_violation"] for i in infos])),
                slowdown=float(np.mean([i["slowdown"] for i in infos])),
            ))
    return policy


@torch.no_grad()
def evaluate(env, policy, n_episodes, device="cpu"):
    """Deterministic (argmax) evaluation; returns per-episode metric dicts."""
    out = []
    for _ in range(n_episodes):
        obs, _ = env.reset()
        done, ep = False, dict(reward=0.0, energy_saved=0.0, budget_violation=0.0,
                               thermal_violation=0.0, slowdown=0.0, n=0)
        while not done:
            o = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            logits, _ = policy(o)
            a = logits.argmax(-1).squeeze(0).cpu().numpy()
            obs, r, term, trunc, info = env.step(a)
            done = term or trunc
            ep["reward"] += r; ep["n"] += 1
            for k in ("energy_saved", "budget_violation", "thermal_violation", "slowdown"):
                ep[k] += info[k]
        for k in ("energy_saved", "budget_violation", "thermal_violation", "slowdown"):
            ep[k] /= ep["n"]
        out.append(ep)
    return out


class RuleBasedController:
    """Facility-style baseline: cap everything harder as draw approaches budget,
    protect hot nodes first. Mirrors what a BMS/operator script would do."""

    def __init__(self, env):
        self.env = env

    def act(self, obs):
        n = self.env.n_nodes
        temps = obs[n : 2 * n]
        draw = obs[2 * n]
        K = self.env.n_cap_levels
        if draw > self.env.budget_frac:
            base = 0                      # hard cap when over budget
        elif draw > 0.9 * self.env.budget_frac:
            base = K // 2
        else:
            base = K - 1                  # no throttle when comfortably under
        a = np.full(n, base, dtype=np.int64)
        a[temps > 0.9 * self.env.TEMP_LIMIT] = 0
        return a


def evaluate_rule_based(env, n_episodes):
    ctrl = RuleBasedController(env)
    out = []
    for _ in range(n_episodes):
        obs, _ = env.reset()
        done, ep = False, dict(reward=0.0, energy_saved=0.0, budget_violation=0.0,
                               thermal_violation=0.0, slowdown=0.0, n=0)
        while not done:
            obs, r, term, trunc, info = env.step(ctrl.act(obs))
            done = term or trunc
            ep["reward"] += r; ep["n"] += 1
            for k in ("energy_saved", "budget_violation", "thermal_violation", "slowdown"):
                ep[k] += info[k]
        for k in ("energy_saved", "budget_violation", "thermal_violation", "slowdown"):
            ep[k] /= ep["n"]
        out.append(ep)
    return out
