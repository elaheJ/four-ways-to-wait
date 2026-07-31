# Phone session screenshots

Raw evidence for the Android numbers quoted in the paper and in the top-level
README. Device: Android 10, Chrome 150, `hardwareConcurrency` = 8, run from
`phone/threads.html` served over LAN.

- `session1-*.jpeg` — first session, on battery (60%), peak speedup **4.15×**.
- `session2-*.jpeg` — second session ~15 minutes later, on charge (57%), peak
  speedup **3.17×**, and showing two workers slower than one (the noise floor).

Counter-intuitively the session **on charge** was the noisier of the two;
charging heats the phone.

The two sessions disagree by 1.31× on the same device and the same page. That
disagreement is reported in the paper rather than resolved by picking the better
run; see the "Three reference devices, and they disagree" section of the
top-level [README](../../README.md).

Note: `session1-1.jpeg` shows an earlier revision of the page, which told
students to plug the phone in. That advice was **removed** for the reason above.
The current `threads.html` no longer gives it.

Tabulated results for both sessions are in
[`instructor/reference_results_android.csv`](../../instructor/reference_results_android.csv).
