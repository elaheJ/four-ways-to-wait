# Android phone — Chrome, session 3 (30 July 2026)

Third recorded session on the Android reference phone. Sessions 1 and 2 are
tabulated in [`instructor/reference_results_android.csv`](../instructor/reference_results_android.csv)
with screenshots in [`phone/screenshots/`](../phone/screenshots/).

## Provenance caveat — READ BEFORE QUOTING

This run rendered a **stale, superseded revision of `threads.html`**. Its intro
paragraph reads "Plug the phone in and keep the screen on — a phone on battery
throttles, and that is itself worth noticing." That advice was **removed** from
the page precisely because session 2 showed charging makes results *noisier*,
not steadier. The current `phone/threads.html` says "Keep the screen on and the
browser in front… Run each section at least twice" instead.

Almost certainly a Chrome HTTP cache hit from the morning's sessions (the page
is served by `python3 -m http.server`, which sends no cache-busting headers).

Consequences:
- **Power state is ambiguous.** The page told the user to plug in. If that
  advice was followed, this is an on-charge run and belongs beside session 2,
  not session 1. Confirm before using.
- The §2 sweep still ran to 16 workers (2× hardwareConcurrency), matching
  current behaviour, so the measurement harness is *probably* unchanged — but
  this has not been diffed against the old revision and should not be assumed.

To avoid a repeat: hard-reload on the phone (or serve with no-store headers)
before recording a session.

## 1. What did you bring?

```
hardwareConcurrency : 8 threads
deviceMemory        : not reported
platform            : Linux armv81
user agent          : Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36
```

## 2. Scaling sweep

| workers | time | speedup | efficiency |
|---------|------|---------|------------|
| 1 | 527 ms | 1.00× | 100% |
| 2 | 307 ms | 1.71× | 86% |
| 3 | 207 ms | 2.55× | 85% |
| 4 | 155 ms | 3.40× | 85% |
| 5 | 196 ms | 2.69× | 54% |
| 6 | 177 ms | 2.98× | 50% |
| 7 | 160 ms | 3.29× | 47% |
| 8 | 142 ms | 3.70× | 46% |
| 9 | 139 ms | 3.80× | 42% |
| 10 | 134 ms | 3.95× | 39% |
| 11 | 136 ms | 3.89× | 35% |
| 12 | 139 ms | 3.79× | 32% |
| 13 | 131 ms | 4.02× | 31% |
| 14 | 132 ms | 3.99× | 29% |
| 15 | 131 ms | 4.02× | 27% |
| 16 | 132 ms | 3.98× | 25% |

Knee at 4 workers (85% efficiency through 4, then 54%). Peak 4.02×.

**Worker 5 is slower in absolute time than worker 4: 155 ms → 196 ms.**

## 3. Block vs dynamic

| schedule | makespan | busiest | idlest | imbalance | vs block |
|----------|----------|---------|--------|-----------|----------|
| block (static) | 859 ms | 820 | 108 | 2.07 | 1.00× |
| dynamic, chunk 64 | 594 ms | 566 | 493 | 1.06 | 1.45× |
| dynamic, chunk 8 | 633 ms | 586 | 549 | 1.03 | 1.36× |

8 workers. Chunk 64 beats chunk 8 here (as in session 1; session 2 was the
reverse — the ordering remains noise).

## 4. Task graph

work T1 = 5200 ms | span T∞ = 2750 ms | parallelism = 1.9 workers

| workers | makespan | lower bound | speedup | efficiency |
|---------|----------|-------------|---------|------------|
| 1 | 5228 ms | 5200 ms | 0.99× | 99% |
| 2 | 3468 ms | 2750 ms | 1.50× | 75% |
| 3 | 2772 ms | 2750 ms | 1.88× | 63% |
| 4 | 2773 ms | 2750 ms | 1.88× | 47% |
| 6 | 2778 ms | 2750 ms | 1.87× | 31% |
| 8 | 2787 ms | 2750 ms | 1.87× | 23% |

## What this session contributes

The **worker-5 regression now reproduces 3 sessions out of 3**:

| session | 4 workers | 5 workers |
|---------|-----------|-----------|
| 1 | 171 ms | 203 ms |
| 2 | 294 ms | 342 ms |
| 3 | 155 ms | 196 ms |

Three-for-three on a device whose *magnitudes* swing 1.31× between sessions is
a strong result: the big.LITTLE regression is structural, while the milliseconds
around it are not. This is the module's central claim ("trust what repeats")
demonstrated on its own data.

Peak speedup 4.02× sits between session 1 (4.15×) and session 2 (3.17×), and
the device still never approaches the 8 threads it reports.

Span bound unchanged at 1.87–1.88×, consistent with every other device measured.
