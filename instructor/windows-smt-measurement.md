# Measuring SMT on the i5-7300U (Windows) — step by step

**Why this run matters.** Every compiled reference device so far lacks SMT, so
the paper has the control without the treatment. The i5-7300U is the first
machine in the set that *has* hyperthreading — 2 physical cores reporting 4
threads. This run closes the missing arm.

**Read this first: you cannot copy the Core Ultra's masks.** That machine ran
"4 threads on 4 physical cores vs 4 threads on 2 physical cores" (masks `C3`
and `3`) and got 1.93×, its no-SMT endpoint. The i5 does not have 4 physical
cores, so that comparison is impossible here. The equivalent test on a 2-core /
4-thread part is **2 threads on two different cores vs 2 threads sharing one
core**, described in step 4.

---

## THE EASY WAY — nothing to install

The binaries are **already built**, cross-compiled with GCC 16.1.0 (the same
compiler version as the Core Ultra reference, so the two Windows machines are
directly comparable). They link only against KERNEL32 and the UCRT, both of
which ship with Windows — there are no DLLs to install and no toolchain to set
up.

Binaries are **not kept in the source tree**. Get `scaling.exe` and `probe.exe`
from the repository's
[Releases page](https://github.com/elaheJ/four-ways-to-wait/releases) and drop
them into `windows-laptop\smt-run\` next to `RUN-ME.bat`.

Then, on the laptop:

1. Open `windows-laptop\smt-run\`.
2. Plug in, set power plan to **High performance**, and close other apps.
3. Double-click **`RUN-ME.bat`**.

It runs everything — topology, the SMT test three times, the scaling sweep three
times, the per-core probe — writes raw CSVs into a `results\` subfolder, and
prints the answer in plain English at the end. About five minutes.

Windows SmartScreen may warn about an unrecognised app; choose **More info →
Run anyway**, or right-click each `.exe` → Properties → **Unblock**. The files
came from your own Dropbox, not the internet, but Windows cannot tell.

Un-pause Dropbox afterwards and the results sync straight back.

Everything below is the manual route, kept in case the binaries need rebuilding.
The cross-compile command used on the Mac was:

```sh
brew install mingw-w64
x86_64-w64-mingw32-gcc -O2 -pthread -static -o scaling.exe lab4_hardware/scaling.c
x86_64-w64-mingw32-gcc -O2 -static -o probe.exe lab4_hardware/probe.c
```

---

## 1. Toolchain (manual route only)

MSVC will not work — it supplies neither POSIX threads nor C11 atomics. Use the
same compiler as the Core Ultra reference so the two machines stay comparable:

1. Download **WinLibs MinGW-w64 GCC**, UCRT runtime, **POSIX** threads variant,
   from <https://winlibs.com/> — take the portable `.zip`, not an installer.
2. Unzip to e.g. `C:\winlibs`.
3. Open **Command Prompt** (cmd.exe, not PowerShell — step 4 uses `start
   /affinity`) and put it on the path for this session:

```bat
set PATH=C:\winlibs\mingw64\bin;%PATH%
gcc --version
```

You should see GCC 16.x. Record the exact version — it goes in the CSV header.

## 2. Build

The lab sources are already on this machine in Dropbox. Navigate to
`four-ways-to-wait\lab4_hardware` and build with the reference flags:

```bat
gcc -O2 -pthread -static -o scaling.exe scaling.c
gcc -O2 -static -o probe.exe probe.c
```

`-static` avoids "missing libwinpthread-1.dll" when the exe runs under `start`.

## 3. Confirm the topology, and prepare the machine

```bat
powershell -c "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors"
```

Expect `2` cores and `4` logical processors.

**Preparation matters more here than on any other device in the set.** This
laptop already showed a 1.7× swing between two browser sessions while charging a
low battery. Before measuring:

- Plug in, and let the battery charge past ~80% first.
- Set the power plan to **High performance** (Settings → System → Power, or
  `powercfg /setactive SCHEME_MIN`).
- Close every other application. With 2 cores, one background task ruins a run.

## 4. THE SMT MEASUREMENT

Hold the thread count at **2** and change only whether those two threads share a
physical core.

`start /affinity` takes a **hex mask with no `0x` prefix**, where bit *n* is
logical processor *n*:

| mask | bits | logical CPUs | meaning (if siblings are adjacent) |
|------|------|--------------|-------------------------------------|
| `5` | 0101 | 0 and 2 | one thread on each physical core |
| `3` | 0011 | 0 and 1 | both threads on the **same** core |

Run each three times, alternating, and keep all six numbers:

```bat
start /affinity 5 /b /wait cmd /c "scaling.exe 2 > smt_diff_cores_run1.csv"
start /affinity 3 /b /wait cmd /c "scaling.exe 2 > smt_same_core_run1.csv"
```

Repeat with `run2`, `run3` in the filenames.

### Reading the result

Take the `compute_s` value on the 2-thread row of each file:

```
smt_ratio = compute_s(same core) / compute_s(different cores)
```

- **≈ 2.0** — the second thread on a core bought nothing. This is what the Core
  Ultra measures (1.93) *because it has no SMT at all*.
- **Meaningfully below 2.0** — SMT is delivering. The shortfall below 2.0 is the
  measurement, and it is the treatment arm the paper currently defers.

Expect somewhere around 1.3–1.6 given the browser sweep already reached ~2.9×
speedup on 2 physical cores, but do not anchor on that — record what you get.

### The test identifies the topology for you

Do not assume logical CPUs 0 and 1 are siblings. If masks `3` and `5` come back
with **nearly identical times**, then the pairing is strided rather than
adjacent, and the labels are simply swapped: **whichever mask is slower is the
same-physical-core pairing**, because those two threads are contending for one
core's execution units. Relabel the files and compute the ratio the same way.
The experiment does not need the topology as an input — it reveals it.

## 5. Full scaling sweep (for the device row)

```bat
scaling.exe 8 > scaling_i5_run1.csv
```

8 = 2× the logical processor count, matching the sweep shape used elsewhere.
Run it three times. The interesting line is where speedup stops climbing, and
whether the compute and memory kernels bend at different thread counts.

## 6. Optional — are the two cores identical?

Unlike the M1 (4 P + 4 E) and the Core Ultra (8 P + 12 E), this chip is
homogeneous: two identical cores. `probe.c` should confirm it, which is a useful
contrast rather than a null result.

```bat
start /affinity 1 /b /wait cmd /c "probe.exe > probe_cpu0.csv"
start /affinity 4 /b /wait cmd /c "probe.exe > probe_cpu2.csv"
```

Both files should agree closely on `fp_Mops` and `int_Mops`. If they do, this is
the module's homogeneous baseline — the machine where "how much is a core worth"
has one answer instead of two.

## 7. What to send back

Copy the CSV files into `four-ways-to-wait\windows-laptop\` (they will sync via
Dropbox) along with:

- the exact `gcc --version` string,
- battery/power state and power plan during the runs,
- whether masks `3` and `5` behaved as labelled or came back swapped.

Those become `instructor/reference_results_i5.csv`, the fourth reference file.

---

## Gotchas

- **Use cmd.exe, not PowerShell.** PowerShell has no `start /affinity`; setting
  `ProcessorAffinity` after launch is racy and can miss the startup phase.
- **`-static` is not optional** if you launch through `start`, or the child
  process may fail to find `libwinpthread-1.dll`.
- **Hex, no prefix.** `/affinity 3`, never `/affinity 0x3`.
- **Two cores is a small machine.** Windows Update, Defender scans, and Dropbox
  syncing will all show up in the numbers. Pause Dropbox sync during the runs —
  it is actively syncing this repository.
