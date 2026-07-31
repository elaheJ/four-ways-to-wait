# extension_powercap — from measuring energy to *managing* it (advanced/honors)

Forked from the research codebase behind our energy-aware scheduling program
(`Energy/` strand). This directory is the single canonical copy: it lives here in
`four-ways-to-wait` because it is a *scheduling* environment, and the companion
`edge-hpc-labs` module points here rather than carrying a second copy.

A simulated 16-node cluster where an agent sets per-node
power caps each 5-minute tick, trading energy saved against power-budget
violations, thermal violations, and job slowdown — the real dilemma a
facility operator (or a phone's OS) faces every second.

Student arc, mirroring the research program's protocol:

1. **Baselines first.** Run the hand-written policies in `policies.py`
   (no-cap, static cap, utilization-proportional). Record the reward
   decomposition from `info`.
2. **Write a better heuristic.** One page of Python. Tune it on regime "A".
3. **Train PPO** (`ppo.py`, CPU, minutes): does learning beat your heuristic?
4. **Shift the distribution.** Evaluate everything on regime "B"
   (`TraceConfig(regime="B")`) *without retuning*. Who degrades gracefully?

Rules of the research group apply: the learned policy must beat the
best heuristic *on the measurement*, on the *held-out regime*, or the
heuristic still wins.

```bash
pip install gymnasium numpy
python3 run_experiment.py --help
```

Files: `power_cap_env.py` (Gymnasium env), `policies.py` (baselines),
`ppo.py` (minimal PPO), `run_experiment.py` (driver).
