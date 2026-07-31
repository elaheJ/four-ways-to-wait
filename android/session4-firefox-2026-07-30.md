# Android phone — Firefox 153, session 4 (30 July 2026)

First non-Chromium run on the Android reference phone, and the first engine
diversity on ARM anywhere in the corpus. Page text confirms the **current**
revision of `threads.html` ("Run each section at least twice…"), so unlike
[session 3](session3-chrome-2026-07-30.md) this was not a stale cache hit.

## 1. What did you bring?

```
hardwareConcurrency : 8 threads
deviceMemory        : not reported
platform            : Linux armv81
user agent          : Mozilla/5.0 (Android 15; Mobile; rv:153.0) Gecko/153.0 Firefox/153.0
```

**This corrects the device record.** `instructor/reference_results_android.csv`
documents the phone as "Android 10" — that came from Chrome's user agent,
`(Linux; Android 10; K)`. Chrome freezes the Android version at 10 and replaces
the model with the literal letter `K` as a fingerprinting countermeasure.
Firefox reports the real value: **Android 15**. The OS in the reference CSV is
wrong and should be updated.

## 2. Scaling sweep

| workers | time | speedup | efficiency |
|---------|------|---------|------------|
| 1 | 600 ms | 1.00× | 100% |
| 2 | 346 ms | 1.73× | 87% |
| 3 | 231 ms | 2.60× | 87% |
| 4 | 172 ms | 3.49× | 87% |
| 5 | 227 ms | 2.64× | 53% |
| 6 | 204 ms | 2.94× | 49% |
| 7 | 184 ms | 3.26× | 47% |
| 8 | 158 ms | 3.80× | 47% |
| 9 | 152 ms | 3.95× | 44% |
| 10 | 155 ms | 3.87× | 39% |
| 11 | 159 ms | 3.77× | 34% |
| 12 | 152 ms | 3.95× | 33% |
| 13 | 154 ms | 3.90× | 30% |
| 14 | 152 ms | 3.95× | 28% |
| 15 | 155 ms | 3.87× | 26% |
| 16 | 159 ms | 3.77× | 24% |

Knee at 4 workers (87% efficiency through 4, then 53%). Peak 3.95×.

**Worker 5 slower in absolute time than worker 4: 172 ms → 227 ms.**

## 3. Block vs dynamic

| schedule | makespan | busiest | idlest | imbalance | vs block |
|----------|----------|---------|--------|-----------|----------|
| block (static) | 798 ms | 785 | 238 | 1.69 | 1.00× |
| dynamic, chunk 64 | 671 ms | 653 | 541 | 1.09 | 1.19× |
| dynamic, chunk 8 | 677 ms | 634 | 569 | 1.03 | 1.18× |

8 workers. Chunk 64 vs chunk 8 is a statistical tie here (1.19× vs 1.18×).

## 4. Task graph

work T1 = 5200 ms | span T∞ = 2750 ms | parallelism = 1.9 workers

| workers | makespan | lower bound | speedup | efficiency |
|---------|----------|-------------|---------|------------|
| 1 | 5218 ms | 5200 ms | 1.00× | 100% |
| 2 | 3463 ms | 2750 ms | 1.50× | 75% |
| 3 | 2759 ms | 2750 ms | 1.88× | 63% |
| 4 | 2764 ms | 2750 ms | 1.88× | 47% |
| 6 | 2762 ms | 2750 ms | 1.88× | 31% |
| 8 | 2757 ms | 2750 ms | 1.89× | 24% |

## Analysis

### The worker-5 regression is now engine-independent: 4 sessions of 4

| session | browser | engine | 4 workers | 5 workers | penalty |
|---------|---------|--------|-----------|-----------|---------|
| 1 | Chrome 150 | Blink | 171 ms | 203 ms | +19% |
| 2 | Chrome 150 | Blink | 294 ms | 342 ms | +16% |
| 3 | Chrome 150 | Blink | 155 ms | 196 ms | +26% |
| 4 | Firefox 153 | **Gecko** | 172 ms | 227 ms | **+32%** |

Sessions 1–3 could all be explained away as a Chromium worker-scheduling
artifact. An independent engine reproducing it removes that explanation: the
fifth worker lands on a little core and is handed an equal share of work
regardless. This is hardware, and the module can now say so without hedging.

### What replicates across engines, and what does not

Replicates:
- Knee at 4 of 8 reported threads (85–87% efficiency through 4, ~50% after).
- Peak ~3.9–4.0× on a device advertising 8 threads. Never close to 8.
- Dynamic always beats block; imbalance always collapses to ~1.0
  (1.69 → 1.03 here).
- Span bound 1.88–1.89×. Unmoved across every device and engine measured.

Does not replicate:
- Absolute times. Firefox's 1-worker baseline is 600 ms vs Chrome session 3's
  527 ms. ~~SpiderMonkey ~14% behind V8 on this loop.~~ **RETRACTED by
  [session 5](session5-chrome-2026-07-30.md):** Chrome's own baselines span
  527–606 ms across sessions, and session 5's Chrome came in at 593 ms — 1.2%
  from Firefox. There is no measurable engine gap; the 14% was an artifact of
  comparing against the fastest Chrome run on record. Within-run ratios are
  safe; cross-session and cross-engine milliseconds are not.
- The size of dynamic's win: 1.04×–1.45× across the four sessions with no
  pattern. Report that dynamic wins, never by how much.
- Chunk 64 vs chunk 8 ordering, still noise (64 ahead in 3 of 4, but session 4's
  margin is 1%, well inside the device's noise floor).

### A useful negative result

Firefox on this phone showed **no anomaly at all** — a clean monotone plateau
with no sub-1.00× rows. That strengthens the verdict on the Windows Firefox
run-1 collapse (421→2240→4446 ms): transient interference on that machine, not
a Gecko worker-scheduling defect. Gecko behaves itself on ARM under the same
harness.

### Teaching value of the user-agent discrepancy

Two browsers on one phone disagree about the operating system, and the more
specific-looking string is the fabricated one: Chrome's `Android 10; K` versus
Firefox's `Android 15`. Alongside the M1 reporting `MacIntel` and
`Intel Mac OS X 10_15_7` on arm64 silicon, §1 now has two independent
demonstrations that the browser's self-report describes a compatibility
contract, not the machine — which is exactly why the lab measures instead of
asking.
