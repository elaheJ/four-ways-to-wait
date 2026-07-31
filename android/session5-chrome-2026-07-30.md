# Android phone — Chrome 150, session 5 (30 July 2026)

Clean re-run of Chrome on the **current** page revision ("Run each section at
least twice…"), replacing [session 3](session3-chrome-2026-07-30.md), which
rendered a stale cached copy and therefore had an ambiguous power state.

## 1. What did you bring?

```
hardwareConcurrency : 8 threads
deviceMemory        : not reported
platform            : Linux armv81
user agent          : Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36
```

"Android 10; K" is Chrome's frozen UA. The device really runs **Android 15**,
per Firefox in [session 4](session4-firefox-2026-07-30.md).

## 2. Scaling sweep

| workers | time | speedup | efficiency |
|---------|------|---------|------------|
| 1 | 593 ms | 1.00× | 100% |
| 2 | 340 ms | 1.74× | 87% |
| 3 | 231 ms | 2.56× | 85% |
| 4 | 173 ms | 3.44× | 86% |
| 5 | 215 ms | 2.76× | 55% |
| 6 | 204 ms | 2.91× | 48% |
| 7 | 175 ms | 3.38× | 48% |
| 8 | 144 ms | 4.13× | 52% |
| 9 | 144 ms | 4.11× | 46% |
| 10 | 142 ms | 4.17× | 42% |
| 11 | 142 ms | 4.17× | 38% |
| 12 | 161 ms | 3.68× | 31% |
| 13 | 149 ms | 3.99× | 31% |
| 14 | 143 ms | 4.16× | 30% |
| 15 | 133 ms | 4.47× | 30% |
| 16 | 153 ms | 3.87× | 24% |

Knee at 4 workers (86% efficiency through 4, then 55%). Peak 4.47× at 15 —
the highest peak recorded on this device.

**Worker 5 slower in absolute time than worker 4: 173 ms → 215 ms.**

## 3. Block vs dynamic

| schedule | makespan | busiest | idlest | imbalance | vs block |
|----------|----------|---------|--------|-----------|----------|
| block (static) | 847 ms | 815 | 54 | 1.86 | 1.00× |
| dynamic, chunk 64 | 650 ms | 618 | 551 | 1.06 | 1.30× |
| dynamic, chunk 8 | 686 ms | 637 | 601 | 1.03 | 1.23× |

## 4. Task graph

work T1 = 5200 ms | span T∞ = 2750 ms | parallelism = 1.9 workers

| workers | makespan | lower bound | speedup | efficiency |
|---------|----------|-------------|---------|------------|
| 1 | 5224 ms | 5200 ms | 1.00× | 100% |
| 2 | 3471 ms | 2750 ms | 1.50× | 75% |
| 3 | 2769 ms | 2750 ms | 1.88× | 63% |
| 4 | 2784 ms | 2750 ms | 1.87× | 47% |
| 6 | 2791 ms | 2750 ms | 1.86× | 31% |
| 8 | 2796 ms | 2750 ms | 1.86× | 23% |

## Analysis

### Worker-5 regression: 5 sessions of 5

| session | browser | 4 workers | 5 workers | penalty |
|---------|---------|-----------|-----------|---------|
| 1 | Chrome | 171 ms | 203 ms | +19% |
| 2 | Chrome | 294 ms | 342 ms | +16% |
| 3 | Chrome | 155 ms | 196 ms | +26% |
| 4 | Firefox | 172 ms | 227 ms | +32% |
| 5 | Chrome | 173 ms | 215 ms | +24% |

Five for five, across two engines, penalty always between +16% and +32%. This
is the most robust single fact in the corpus.

### RETRACTION: there is no measurable Chrome-vs-Firefox speed gap

Session 4's writeup claimed SpiderMonkey trails V8 by ~14% on this loop,
comparing Firefox's 600 ms baseline against session 3's 527 ms. **That claim
does not survive this run** and should not be repeated.

One-worker baselines, all Chrome except where noted:

| session | baseline |
|---------|----------|
| 1 | 531 ms |
| 2 | 606 ms |
| 3 | 527 ms |
| 4 (Firefox) | 600 ms |
| 5 | 593 ms |

Chrome alone spans 527–606 ms, a 1.15× spread. Firefox's 600 ms sits inside
that range, 1.2% from this session's Chrome. The apparent engine gap was an
artifact of comparing against the fastest Chrome session on record. Any
engine difference on this workload is below the device's noise floor.

This is the module's own thesis catching an error in the module's own notes:
a millisecond difference was quoted as a result before it had been repeated.

### The session spread is wider than the paper currently states

Peak speedups: 4.15× (s1), 3.17× (s2), 4.02× (s3), 3.95× (s4), 4.47× (s5).
Spread is now **1.41×** (4.47 / 3.17), not the 1.31× quoted in
`instructor/reference_results_android.csv` from the first two sessions. If the
paper cites a session-to-session spread, 1.41× across five sessions is the
better-supported number — and it strengthens the argument rather than weakening
it.

### Chunk 64 vs chunk 8: still not quotable, but watch it

Chunk 64 has now led in 4 of 5 sessions (s2 reversed; s4 was a 1% tie). That is
not significant — a 4-of-5 split has a one-sided p ≈ 0.19 under a sign test, and
the margins are small. The existing CSV guidance ("the ordering is noise; do not
build a lesson on it") still stands. Worth revisiting only if a deliberate
repeated-measures run is ever done.

### Unmoved, as always

Knee at 4 of 8 reported threads. Dynamic beats block, imbalance 1.86 → 1.03.
Span bound 1.86–1.88×. The device still never approaches the 8 threads it
advertises, peaking at 4.47× on its best session ever.
