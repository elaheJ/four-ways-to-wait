"""
Data collection for the study. Pre-registered design:

  Arms (between-subjects factor, all width-tuned to the same <=5k parameter budget):
      classical | hybrid | ablated
  Seeds: PRE-REGISTERED list below. Never add seeds after seeing results;
      if more power is needed, extend by a pre-declared block (e.g. +10) and report both.
  Protocol per (arm, seed):
      Phase 1 TRAIN     on regime A          -> checkpoint
      Phase 2 EVAL      on regime A held-out episodes  (Q1 data)
      Phase 3 SHIFT-EVAL on regime B, zero-shot        (context for Q2)
      Phase 4 FINE-TUNE on regime B, eval every update (Q2 data: steps to recover)
  Rule-based baseline evaluated on both regimes (floor / sanity reference).

Outputs (CSV, one row per observation — tidy data for analyze.py):
  results/eval.csv      per-episode eval metrics, keyed by arm/seed/phase
  results/learning.csv  per-update training curves (incl. fine-tuning curve for Q2)
  results/params.csv    realized parameter counts per arm (audit of size-matching)
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pandas as pd
import torch

from power_cap_env import PowerCapEnv, TraceConfig
from policies import build_policy
from ppo import PPOConfig, train, evaluate, evaluate_rule_based

# ----------------------------- pre-registration ---------------------------- #
SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]  # frozen before any run
ARMS = ["classical", "hybrid", "ablated"]
PARAM_BUDGET = 5000
N_QUBITS, N_LAYERS = 6, 3
EVAL_EPISODES = 20  # full-study default; override with --eval-episodes for smoke runs
# --------------------------------------------------------------------------- #


def make_env(regime: str, seed: int) -> PowerCapEnv:
    return PowerCapEnv(TraceConfig(regime=regime), seed=seed)


def run_cell(arm: str, seed: int, train_steps: int, ft_steps: int, outdir: str,
             device: str = "cpu", eval_episodes: int = EVAL_EPISODES):
    torch.manual_seed(seed)
    np.random.seed(seed)

    env_A = make_env("A", seed)
    obs_dim = env_A.observation_space.shape[0]
    policy = build_policy(arm, obs_dim, env_A.n_nodes, env_A.n_cap_levels,
                          budget=PARAM_BUDGET, n_qubits=N_QUBITS, n_layers=N_LAYERS)
    cfg = PPOConfig()
    curves: list[dict] = []
    rows: list[dict] = []

    # Phase 1: train on regime A
    t0 = time.time()
    train(env_A, policy, train_steps, cfg, device, log=curves, phase="train_A")
    train_wall = time.time() - t0

    # Phase 2: eval on regime A (fresh env seed -> held-out traces)
    for ep in evaluate(make_env("A", seed + 5000), policy, eval_episodes, device):
        rows.append(dict(arm=arm, seed=seed, phase="eval_A", **ep))

    # Phase 3: zero-shot eval on shifted regime B
    for ep in evaluate(make_env("B", seed + 6000), policy, eval_episodes, device):
        rows.append(dict(arm=arm, seed=seed, phase="eval_B_zeroshot", **ep))

    # Phase 4: fine-tune on regime B, logging the curve (Q2)
    env_B = make_env("B", seed + 7000)
    train(env_B, policy, ft_steps, cfg, device, log=curves, phase="finetune_B")
    for ep in evaluate(make_env("B", seed + 8000), policy, eval_episodes, device):
        rows.append(dict(arm=arm, seed=seed, phase="eval_B_finetuned", **ep))

    for c in curves:
        c.update(arm=arm, seed=seed)
    meta = dict(arm=arm, seed=seed, n_params=policy.meta["n_params"],
                core_w=policy.meta["core_w"], head_w=policy.meta["head_w"],
                train_wall_s=round(train_wall, 1))
    return rows, curves, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-steps", type=int, default=60_000)
    ap.add_argument("--ft-steps", type=int, default=20_000)
    ap.add_argument("--seeds", type=int, default=len(SEEDS),
                    help="use first N pre-registered seeds (smoke tests only; full runs use all)")
    ap.add_argument("--arms", nargs="+", default=ARMS, choices=ARMS)
    ap.add_argument("--eval-episodes", type=int, default=EVAL_EPISODES)
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    all_rows, all_curves, all_meta = [], [], []

    # Rule-based floor on both regimes (no training, seed loop for CI width parity)
    for seed in SEEDS[: args.seeds]:
        for regime, phase in [("A", "eval_A"), ("B", "eval_B_zeroshot")]:
            for ep in evaluate_rule_based(make_env(regime, seed + 9000), args.eval_episodes):
                all_rows.append(dict(arm="rule_based", seed=seed, phase=phase, **ep))

    for arm in args.arms:
        for seed in SEEDS[: args.seeds]:
            print(f"[cell] arm={arm} seed={seed}", flush=True)
            rows, curves, meta = run_cell(arm, seed, args.train_steps, args.ft_steps, args.outdir,
                                          eval_episodes=args.eval_episodes)
            all_rows += rows; all_curves += curves; all_meta.append(meta)

    pd.DataFrame(all_rows).to_csv(f"{args.outdir}/eval.csv", index=False)
    pd.DataFrame(all_curves).to_csv(f"{args.outdir}/learning.csv", index=False)
    pd.DataFrame(all_meta).to_csv(f"{args.outdir}/params.csv", index=False)
    print(f"wrote {args.outdir}/eval.csv, learning.csv, params.csv")


if __name__ == "__main__":
    main()
