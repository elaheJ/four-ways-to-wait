"""
Simulated cluster power-capping environment (Gymnasium API).

The agent observes per-node utilization/temperature and facility power vs. budget,
and acts by setting a discrete power-cap level per node. Reward trades off
energy saved against power-budget violations, thermal violations, and job slowdown.

Workload traces are synthetic by default (with an explicit "regime" knob so we can
create a distribution shift for the fine-tuning study, Q2), but `TraceConfig.swf_path`
lets you drop in real Parallel Workloads Archive / Slurm-derived utilization traces.
"""
from __future__ import annotations

import dataclasses
from typing import Optional

import numpy as np
import gymnasium as gym
from gymnasium import spaces


# ----------------------------- workload traces ----------------------------- #

@dataclasses.dataclass
class TraceConfig:
    """Parameters of the synthetic workload generator.

    `regime` shifts the workload distribution: 'A' (training months) has a
    daytime-heavy diurnal cycle; 'B' (held-out shifted months) has higher mean
    load, flatter diurnal shape, and burstier arrivals — a stand-in for
    semester-vs-break or summer-vs-winter shift.
    """
    n_nodes: int = 16
    episode_len: int = 288          # control steps per episode (e.g. 5-min ticks / 24h)
    regime: str = "A"
    swf_path: Optional[str] = None  # hook: path to a real SWF/Slurm-derived CSV of per-node utilization


def make_trace(cfg: TraceConfig, rng: np.random.Generator) -> np.ndarray:
    """Return per-node utilization trace, shape (episode_len, n_nodes), values in [0, 1]."""
    if cfg.swf_path is not None:
        # Real-trace hook: CSV with shape (T, n_nodes) of utilizations in [0,1].
        arr = np.loadtxt(cfg.swf_path, delimiter=",")
        t0 = rng.integers(0, max(1, arr.shape[0] - cfg.episode_len))
        return np.clip(arr[t0 : t0 + cfg.episode_len, : cfg.n_nodes], 0.0, 1.0)

    t = np.arange(cfg.episode_len)[:, None] / cfg.episode_len  # (T,1) in [0,1)
    if cfg.regime == "A":
        base, diurnal_amp, burst_rate, burst_size = 0.45, 0.30, 0.02, 0.25
    elif cfg.regime == "B":  # shifted: hotter, flatter, burstier
        base, diurnal_amp, burst_rate, burst_size = 0.62, 0.12, 0.06, 0.35
    else:
        raise ValueError(f"unknown regime {cfg.regime!r}")

    diurnal = base + diurnal_amp * np.sin(2 * np.pi * (t - 0.25))
    node_offset = rng.uniform(-0.08, 0.08, size=(1, cfg.n_nodes))
    noise = rng.normal(0.0, 0.05, size=(cfg.episode_len, cfg.n_nodes))
    bursts = (rng.random((cfg.episode_len, cfg.n_nodes)) < burst_rate) * burst_size
    return np.clip(diurnal + node_offset + noise + bursts, 0.0, 1.0)


# ------------------------------- environment ------------------------------- #

class PowerCapEnv(gym.Env):
    """Facility power-capping control problem.

    Observation (float32 vector, size 2*n_nodes + 3):
        [util_1..util_N, temp_1..temp_N, facility_draw/budget, time_of_day_sin, time_of_day_cos]
    Action (MultiDiscrete, one of `n_cap_levels` per node):
        cap level k -> node power cap = cap_min + k/(K-1) * (1 - cap_min), as fraction of P_max.
    Reward per step (all terms are per-node means; weights in __init__):
        + energy saved vs. uncapped draw
        - budget-violation penalty (facility draw over budget)
        - thermal-violation penalty (node temp over limit)
        - slowdown penalty (work throttled because cap < demand)
    """

    metadata = {"render_modes": []}

    # simple affine power model: node power fraction = idle + (1-idle)*effective_util
    P_IDLE = 0.35
    TEMP_AMBIENT = 0.30       # normalized temperature units
    TEMP_LIMIT = 0.85
    TEMP_GAIN = 0.65          # heating per unit power
    TEMP_INERTIA = 0.80       # first-order thermal lag

    def __init__(
        self,
        trace_cfg: TraceConfig | None = None,
        n_cap_levels: int = 4,
        cap_min: float = 0.5,
        budget_frac: float = 0.75,   # facility budget as fraction of all-nodes-at-P_max
        w_energy: float = 1.0,
        w_budget: float = 4.0,
        w_thermal: float = 2.0,
        w_slowdown: float = 1.5,
        seed: int | None = None,
    ):
        super().__init__()
        self.cfg = trace_cfg or TraceConfig()
        self.n_nodes = self.cfg.n_nodes
        self.n_cap_levels = n_cap_levels
        self.cap_min = cap_min
        self.budget_frac = budget_frac
        self.w = dict(energy=w_energy, budget=w_budget, thermal=w_thermal, slowdown=w_slowdown)

        obs_dim = 2 * self.n_nodes + 3
        self.observation_space = spaces.Box(-1.0, 2.0, shape=(obs_dim,), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([n_cap_levels] * self.n_nodes)
        self._rng = np.random.default_rng(seed)
        self._trace: np.ndarray | None = None
        self._t = 0
        self._temps = np.full(self.n_nodes, self.TEMP_AMBIENT)

    # -- helpers --
    def _caps_from_action(self, action: np.ndarray) -> np.ndarray:
        k = np.asarray(action, dtype=np.float64)
        return self.cap_min + (k / (self.n_cap_levels - 1)) * (1.0 - self.cap_min)

    def _obs(self) -> np.ndarray:
        util = self._trace[self._t]
        phase = 2 * np.pi * self._t / self.cfg.episode_len
        return np.concatenate(
            [util, self._temps, [self._last_draw_frac, np.sin(phase), np.cos(phase)]]
        ).astype(np.float32)

    # -- gym API --
    def reset(self, *, seed: int | None = None, options=None):
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        self._trace = make_trace(self.cfg, self._rng)
        self._t = 0
        self._temps = np.full(self.n_nodes, self.TEMP_AMBIENT)
        self._last_draw_frac = 0.5
        return self._obs(), {}

    def step(self, action):
        util_demand = self._trace[self._t]                    # what jobs want, [0,1]
        caps = self._caps_from_action(action)                 # allowed power fraction, [cap_min,1]

        # effective utilization is throttled so node power stays under its cap
        power_uncapped = self.P_IDLE + (1 - self.P_IDLE) * util_demand
        power = np.minimum(power_uncapped, caps)
        util_eff = np.clip((power - self.P_IDLE) / (1 - self.P_IDLE), 0.0, 1.0)
        slowdown = np.maximum(util_demand - util_eff, 0.0)    # throttled work

        # thermal dynamics (first-order)
        self._temps = (
            self.TEMP_INERTIA * self._temps
            + (1 - self.TEMP_INERTIA) * (self.TEMP_AMBIENT + self.TEMP_GAIN * power)
        )
        thermal_viol = np.maximum(self._temps - self.TEMP_LIMIT, 0.0)

        draw_frac = float(power.mean())                       # facility draw / (N * P_max)
        self._last_draw_frac = draw_frac
        budget_viol = max(draw_frac - self.budget_frac, 0.0)
        energy_saved = float((power_uncapped - power).mean())

        reward = (
            self.w["energy"] * energy_saved
            - self.w["budget"] * budget_viol
            - self.w["thermal"] * float(thermal_viol.mean())
            - self.w["slowdown"] * float(slowdown.mean())
        )

        self._t += 1
        terminated = False
        truncated = self._t >= self.cfg.episode_len
        info = dict(
            energy_saved=energy_saved,
            budget_violation=budget_viol,
            thermal_violation=float(thermal_viol.mean()),
            slowdown=float(slowdown.mean()),
            draw_frac=draw_frac,
        )
        if truncated:
            obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        else:
            obs = self._obs()
        return obs, reward, terminated, truncated, info
