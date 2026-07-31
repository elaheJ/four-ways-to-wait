# threads.html run log

**Scope.** This log covers the 30 July 2026 *browser/device sweep* only. It does
NOT supersede the established reference corpus in `instructor/`, which already
documents three devices in depth:

| file | device |
|------|--------|
| `instructor/reference_results.csv` | Apple M1, 4P+4E, 8 GB |
| `instructor/reference_results_x86.csv` | Intel Core Ultra 7 265, 20 cores (8P+12E), no SMT |
| `instructor/reference_results_android.csv` | Android 10, 8 logical, big.LITTLE — two sessions |

Android screenshots: `phone/screenshots/` (session1 on battery, session2 on charge).

What this sweep adds that the corpus did not already have:
1. **A genuinely new device class** — the i5-7300U (2 physical cores) is the
   weakest machine measured. The corpus jumps from 8 cores (M1) to 20 (Core
   Ultra); nothing represented the low-end student laptop until now.
2. **Browser diversity on fixed hardware** — the corpus is essentially
   single-browser (headless Chrome 151 on M1). This sweep runs Chrome/Edge/
   Firefox on one Windows box and Safari/Chrome on the M1.

## Devices

| id | device | CPU | cores / logical | RAM | OS |
|----|--------|-----|-----------------|-----|-----|
| WL1 | Home Windows laptop | Intel Core i5-7300U @ 2.60 GHz (Kaby Lake) | 2 / 4 (HT) | 8 GB DDR4-2133 SODIMM | Windows 10/11 x64 |
| WL2 | Office Windows laptop | — | — | — | — |
| MB | MacBook | Apple M1 (arm64) | 8 physical = 4 P + 4 E | 8 GB LPDDR4X-4266 unified | macOS 26.5.1 |
| AP | Android phone | — | — | — | Android |

## Runs

| run | device | browser (engine) | date | power | HC | §2 plateau | §3 dyn-8 vs block | §3 imbalance | §4 speedup vs bound |
|-----|--------|------------------|------|-------|----|------------|--------------------|--------------|----------------------|
| 1 | WL1 | Chrome 138 (Blink) | 2026-07-30 | USB-C AC, battery low | 4 | 2.92× @ 4 | 1.50× | 1.56 → 1.04 | 1.88× / 1.9 max |
| 2 | WL1 | Edge 140 (Blink) | 2026-07-30 | USB-C AC, battery low | 4 | 3.10× @ 5 | 1.93× | 1.59 → 1.03 | 1.88× / 1.9 max |
| 3 | WL1 | Firefox 153 (Gecko) | 2026-07-30 | USB-C AC, battery low | 4 | 3.26× @ 8 * | 1.77× | 1.72 → 1.04 | 1.89× / 1.9 max |
| 3b | WL1 | Firefox 153 (Gecko), rerun | 2026-07-30 | USB-C AC, battery low | 4 | 2.40× @ 8 (≈2.0× @ 4) | 1.30× | 1.59 → 1.01 | 1.89× / 1.9 max |
| 4 | MB | Chrome 150 (Blink) | 2026-07-30 | ? | 8 | ~5.9–6.0× @ 8 (3.72× @ 4, 93% eff) | 1.73× | 1.79 → 1.01 | 1.89× / 1.9 max |
| 5 | MB | Safari 26.5 (WebKit) | 2026-07-30 | ? | 8 | 5.74× @ 8, ~6.0× plateau to 16 (3.74× @ 4, 93% eff) | 1.66× | 1.77 → 1.02 | 1.89× / 1.9 max |
| 6 | AP | Chrome 150 (Blink) | 2026-07-30 | ? (stale page said "plug in") | 8 | 4.02× peak @ 13–15; knee @ 4; **5 slower than 4** | 1.45× (chunk 64) | 2.07 → 1.03 | 1.87× / 1.9 max |
| 7 | AP | Firefox 153 (Gecko) | 2026-07-30 | ? | 8 | 3.95× peak @ 9–14; knee @ 4; **5 slower than 4** | 1.19× (chunk 64) | 1.69 → 1.03 | 1.89× / 1.9 max |
| 8 | AP | Chrome 150 (Blink), current page | 2026-07-30 | ? | 8 | 4.47× peak @ 15; knee @ 4; **5 slower than 4** | 1.30× (chunk 64) | 1.86 → 1.03 | 1.86× / 1.9 max |

\* Firefox §2 anomaly: run 1 collapsed at rows 5–6 (0.53×, 0.27×, recovering at
7–8). Rerun (3b) was clean — no collapse anywhere. Verdict: transient interference
during run 1 (background task or charger/throttle event), not a Gecko scheduling
defect. Textbook "trust what repeats" example for class.
Session variance is real, though: the 1-worker baseline moved 1198 ms → 691 ms
between the two Firefox runs (1.7×, exceeding the page's own 1.3× warning), which
is why 3b's speedups read lower — the denominator got faster, the plateau story
is unchanged. §4 sat at 1.89× on the 2750 ms bound in both runs regardless.
Raw report: windowslaptop-firefox-2ndtime.htm.html

## Observations so far

- WL1 reports hardwareConcurrency 4 but has 2 physical cores — HC counts logical
  processors. All three browsers still reached ~2.9–3.3× speedup, i.e. hyperthreading
  yielded ~45–60% (well above the typical 20–30%), consistent with a stall-heavy
  arithmetic loop the second hyperthread can fill.
- Chrome vs Edge (same Blink engine): same curve shapes within noise — good
  replication pair.
- §4 task graph pinned at the T1/T∞ = 1.9 bound in every run, on every engine.
  Structural results are engine-invariant; only the milliseconds move.
- MB shows a qualitatively different §2 curve from WL1: near-perfect to 4 workers
  (93% eff), then each extra worker worth ~half, plateauing ~6.0× and staying
  there all the way to 16. That is the P/E signature, confirmed against the
  hardware: `sysctl hw.perflevel0/1.physicalcpu` = 4 P + 4 E. Four full-speed
  cores + four cores worth ~0.5 each ≈ 6×. WL1's curve bends at 2 physical
  cores instead. Same lab, two architectures, two different bend stories.
- The 4→5 efficiency drop on MB (93% → 81/86%) is NOT a collapse. Times keep
  falling monotonically (126→117→98→86→82 ms); only efficiency (= speedup/
  workers) declines, which it must once speedup grows slower than worker count.
  Rule for reading the tables: a collapse means the ms column goes UP; an
  efficiency knee means only the % column goes down.
  Two things that ARE collapses, for contrast: the WL1 Firefox run-1 anomaly
  (421→2240→4446 ms, speedup below 1.00×, did not repeat), and — structurally,
  and reproducibly — the Android phone's fifth worker, which is slower in
  absolute ms than its fourth in BOTH recorded sessions (171→203, 294→342).
- Careful with the word "bend": the corpus defines it as where speedup stops
  climbing (M1 bends at 8 of 8; Core Ultra at 20 of 20; phone at 4 of 8).
  Tonight's M1 runs agree — speedup climbs all the way to 8, then plateaus.
  The 4→5 efficiency-slope change is a *softer* P/E signature than the phone's
  outright regression; on the M1 the E cores still help, on the phone the fifth
  worker actively hurts. Do not oversell the M1 knee as the headline — the
  phone's regression is the stronger and already-published signature.
- Tonight's browser M1 plateau (~6× from 8 cores ⇒ an E core ≈ 0.5 of a P core)
  independently corroborates the 0.50 P/E value ratio in reference_results.csv,
  measured there via compiled code rather than JS workers.
- Safari vs Chrome on MB is a near-perfect replication: 1-worker baselines 471 vs
  470 ms (0.2% apart), identical shape, both plateau ~6.0×, §4 identical at
  1.89×. Two independent engines (WebKit vs Blink) agreeing this closely is
  strong evidence the lab measures hardware, not browser.
- Safari did NOT cap hardwareConcurrency — reported 8, same as Chrome, i.e. all
  8 physical cores. (It does omit deviceMemory, which Chrome reports as 8 GB.)
  Both report platform "MacIntel" and a UA saying "Intel Mac OS X 10_15_7" on an
  arm64 M1 — frozen legacy UA strings. Good §1 lesson: the browser's self-report
  is not the machine. Second, independent instance of this on the phone: Chrome
  says Android 10, Firefox says Android 15, same device.

## Still to collect

- WL1: done (optional: one Firefox sweep on a charged battery to see if the
  691 ms vs 1198 ms baseline gap is charging-related)
- WL2 (office): Edge run — open threads.html from Dropbox directly (standalone file)
- MB: done (Safari = MacbookSafari.pdf, Chrome = Macbook-Chrome-2nd.html; the
  earlier MacbookSafari.html is an empty "Save Page As" export — delete or ignore.
  Export rule: use File → Print → Save as PDF, not Save Page As.)
- AP: sessions 3 (Chrome) and 4 (Firefox) recorded 30 Jul in android/.
  Session 3 ran a STALE CACHED revision of threads.html (the one still advising
  "plug the phone in"), so its power state is ambiguous; confirm before folding
  into reference_results_android.csv. Session 4 used the current page.
  Worker-5 regression is now 4/4 sessions and, critically, reproduces on Gecko
  as well as Blink — it is hardware, not a Chromium artifact.
- **Corrections owed to instructor/reference_results_android.csv**:
  1. It records the phone as "Android 10", which is Chrome's frozen UA
     (`Android 10; K`). Firefox reports the true OS: **Android 15**.
  2. The session spread is now **1.41×** (peaks 3.17×–4.47× over five sessions),
     not the 1.31× derived from the first two.
- Do NOT quote a Chrome-vs-Firefox speed difference on the phone. Chrome's own
  1-worker baseline spans 527–606 ms across sessions; Firefox's 600 ms sits
  inside that range. An earlier note in session4-firefox claiming ~14% has been
  retracted — it compared against the fastest Chrome run on record.
- Serving note: `python3 -m http.server` sends no cache-control headers, so
  phones can silently re-render an old page revision. Hard-reload before
  recording.
- Raw exports live in `windows-laptop/` (PDF/saved-page per browser)
