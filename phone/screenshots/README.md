# Phone session screenshots

Raw evidence for the Android numbers quoted in the paper and in the top-level
README. Device: **Android 15**, `hardwareConcurrency` = 8, run from
`phone/threads.html` served over LAN.

(Chrome's user agent claims "Android 10; K" — a frozen string, not the real OS.
Firefox on the same handset reports Android 15. Corrected 30 July 2026.)

- `session1-*.jpeg` — first session, Chrome 150, on battery (60%), peak speedup
  **4.15×**.
- `session2-*.jpeg` — second session ~15 minutes later, Chrome 150, on charge
  (57%), peak speedup **3.17×**, and showing two workers slower than one (the
  noise floor).

Counter-intuitively the session **on charge** was the noisier of the two;
charging heats the phone.

Three further sessions were recorded later the same day with no screenshots —
see [`../../android/`](../../android/) for full writeups (session 3 Chrome,
session 4 Firefox, session 5 Chrome). Across all five, peaks range 3.17×–4.47×,
a spread of **1.41×** on the same device and page. That disagreement is reported
in the paper rather than resolved by picking the better run; see the "Three
reference devices, and they disagree" section of the top-level
[README](../../README.md) — which now describes **four** devices, an Intel
i5-7300U laptop having been added.

Note: `session1-1.jpeg` shows an earlier revision of the page, which told
students to plug the phone in. That advice was **removed** for the reason above.
The current `threads.html` no longer gives it.

Tabulated results for all five sessions are in
[`instructor/reference_results_android.csv`](../../instructor/reference_results_android.csv).
