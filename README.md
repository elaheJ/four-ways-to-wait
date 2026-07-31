# Four Ways to Wait

Four hands-on labs that deliver ten core scheduling and multithreading learning
outcomes on hardware students already own. One question, asked four times:

> **Who is waiting, and why?**

A worker can be waiting on a **dependency**, on an **unequal split** of the work,
on **another thread**, or on **hardware that was never there**. Those four causes
are the four labs.

Companion to the EduHPC-2026 short paper *Four Ways to Wait: Teaching Scheduling
and Multithreading on the Devices Students Already Carry*.

## The capstone

Same machine, same eight threads, four workloads (Apple M1, 4 P-cores + 4 E-cores):

| Workload | Speedup on 8 threads | Who is waiting |
|---|---|---|
| Lab 2, cyclic schedule | **5.82×** | nobody |
| Lab 2, block schedule | **3.75×** | on an unequal split — 43.7% of the machine idle |
| Lab 1, task graph | **1.85×** | on the arrows — the span, not the machine, is the limit |
| Lab 3, shared counter under a mutex | **0.30×** | on each other — 3.3× *slower* than one thread |

Lab 4 measures what the hardware itself gives on work with nothing shared and
nothing waiting: **5.45×**, not 8, because four of those cores are efficiency
cores worth half a performance core each.

## The labs

| Lab | Runs on | What it measures |
|---|---|---|
| **1 — waiting on the arrows** | phone browser, or Python 3.10+ | Work, span, and why more workers stop helping |
| **2 — waiting on an unequal split** | phone browser, or C | Block vs. cyclic vs. dynamic over one lopsided loop |
| **3 — waiting on each other** | C | Races, lost updates, critical-section cost, producer–consumer, deadlock |
| **4 — waiting on hardware that is not there** | C (+ browser) | Thread scaling to 2× core count; P-cores vs. E-cores; bandwidth saturation |

Labs 1 and 2 need **nothing installed** — open `phone/threads.html` on any phone
or laptop. No account, no network after page load, no elevated permission.

## Quick start

```sh
# no install at all — open in any browser, including a phone
open phone/threads.html

# Lab 1
python3 lab1_taskgraph/taskgraph.py            # add --trace to see who ran what, when

# Lab 2
cc -O2 -o imbalance lab2_mapping/imbalance.c && ./imbalance 8

# Lab 3
cc -O2 -o counter  lab3_sync/counter.c  && ./counter 8      # run it five times
cc -O2 -o pipeline lab3_sync/pipeline.c && ./pipeline
cc -O2 -o deadlock lab3_sync/deadlock.c && ./deadlock bad   # hangs, on purpose
                                           ./deadlock good

# Lab 4
cc -O2 -o scaling lab4_hardware/scaling.c && ./scaling 16
taskpolicy -b ./scaling 4        # macOS: same work, efficiency cores only
                                 # Linux: taskset -c <list> ./scaling 4

cc -O2 -o probe lab4_hardware/probe.c && ./probe   # what is one core worth?
taskpolicy -b ./probe                              # the same question, small core

# Advanced extension (optional)
pip install gymnasium numpy
python3 extension_powercap/run_experiment.py --help
```

## Advanced extension — [extension_powercap/](extension_powercap/)

The four labs ask *who is waiting*. The extension asks what to do about it when
the answer is "everyone, because the power budget says so." It is the
power-capping Gymnasium environment from the research codebase behind this
module, forked unchanged: a simulated 16-node cluster where an agent sets
per-node caps each five-minute tick, trading energy saved against budget,
thermal, and slowdown penalties, with a distribution-shift knob.

Students replay the research protocol in miniature — baselines, then a
hand-written policy, then PPO, then evaluation on the shifted regime *without
retuning* — under the house rule that the learned policy must beat the heuristic
on the held-out measurement or the heuristic still wins. Needs Python 3.10+,
NumPy and Gymnasium; no cluster, no GPU.

This is the single canonical copy. The companion module `edge-hpc-labs` points
here rather than shipping a second one.

## Outcome coverage

| Outcome | Lab |
|---|---|
| MIMD in practice; tasks vs. threads | 1, 4 |
| SMT vs. multicore — what is shared | class census |
| Limits of thread-level parallelism | 4 |
| Shared memory: correctness and speed-up | 3, 4 |
| Thread spawning, synchronization, dynamic threads | 2, 3 |
| Creating and assigning work to threads | 1, 2 |
| Critical regions, producer–consumer, monitors | 3 |
| Deadlock, race conditions, determinacy | 3 |
| Static vs. dynamic scheduling, mapping, load imbalance | 2 |
| Dependencies, task graphs, work and makespan | 1 |

The ten outcomes are not ours. They are the scheduling and multithreading
learning outcomes from the **NSF/IEEE-TCPP Curriculum Initiative on Parallel and
Distributed Computing — Core Topics for Undergraduates**, Version I, December
2012 (S. K. Prasad et al.), drawn from its architecture, programming and
algorithms strands and abbreviated here for the table. The wording above is
condensed; the source wording governs. Curriculum website:
<http://www.cs.gsu.edu/~tcpp/curriculum/index.php>

## Reference measurements

Every number in the paper is measured, and each row of the reference tables
carries the device specification and the command that produced it. `make_fig1.py`
regenerates the paper's figure from those values.

Reference device: Apple M1 (4 P + 4 E cores, 8 GB), macOS 26.5, Apple clang 21,
`cc -O2`. Harnesses discard a warm-up pass and report best-of-three; the counter
figures are medians of three sweeps at 40 M increments per thread.

## Four reference devices, and they disagree

| | Apple M1 | Intel Core Ultra 7 265 | Intel i5-7300U | Android phone |
|---|---|---|---|---|
| Reported threads | 8 | 20 | 4 | 8 |
| Cores | 4 P + 4 E | 8 P + 12 E | 2 (homogeneous) | 4 big + 4 little |
| SMT | none | **none** — Intel removed it from this generation | **yes** — 2 cores, 4 threads | none |
| Peak speedup | 5.45× | 14.9× | 2.75× | **3.2–4.5×** |
| Halve the cores, fixed threads | — | **1.93×** (no SMT) | **1.38×** (SMT) | — |
| E-core worth, same kernel | **0.50** of a P-core | **0.99** of a P-core | 1.01 — cores identical | — |

The i5-7300U is a 2017 ultrabook part, and it is in the table because it is the
low end of what students actually carry and the only device here with SMT.

**It is what makes the SMT lesson measurable.** Halving the physical cores under
a fixed thread count costs 1.93× on the Core Ultra, which has no SMT, and 1.38×
here, which does — a control and a treatment on the same test.

**But the sharper finding is that "what is a hyperthread worth" has no single
answer.** On the same core in the same run, the second hyperthread is worth
**1.35×** on the compute kernel and **1.89×** on the memory kernel. A thread
stalled on memory leaves the core's execution units idle, which is precisely the
gap SMT exists to fill; a thread saturating the floating-point pipeline leaves
almost nothing to share. That is the same lesson the E-core comparison teaches,
arrived at from the other side.

**The phone advertises 8 threads and delivers between a third and a half of
that.** In all five sessions the *fifth worker was slower than the fourth*
(171→203, 294→342, 155→196, 172→227, 173→215 ms) — the signature of a 4+4
big.LITTLE part. Adding a worker cost time, on a device the student owns. It
reproduces under Firefox as well as Chrome, so it is the hardware and not one
browser's worker scheduling.

**But the phone is a noisy instrument, and that is the second lesson.** Peak
speedup ranged 3.17× to 4.47× across five sessions on the same device — the
worst and best only hours apart — and one session even showed two workers
running *slower* than one, which is a noise floor, not a result.
Counter-intuitively the run on charge was among the noisier ones; charging heats
the phone. Quote what repeats (where the curve bends, which worker made things
worse), not the milliseconds.

**Browser choice does not move any of this.** Chrome, Edge and Firefox agree
within session noise on the same Windows laptop; Safari and Chrome on the M1
differ by 0.2% at one worker. What the browser *says* is another matter — Chrome
reports `Android 10` on an Android 15 handset and `MacIntel` on arm64 silicon.
The census measures rather than asks, and §1 of the browser lab is where students
find that out.

**The two laptops disagree about their own E-cores**, which is the other finding.
`scaling.c`'s compute kernel compiles to a
scalar single-accumulator loop whose throughput is set by FP-add *latency*, so it
is blind to everything that distinguishes a big core from a small one. Swap in a
dependent integer chain — `lab4_hardware/probe.c` — and the same two Intel cores
separate by 1.43×. **How much a core is worth is a property of the code and the
chip together, not the chip.**

SMT is measured with a pinned comparison that works whether or not the device has
it: hold the thread count fixed and halve the physical cores those threads may
use. Without SMT that costs a factor of 2 — the Core Ultra measures **1.93×**,
the control. With SMT it costs less, and the shortfall is the answer: the
i5-7300U measures **1.38×**, so a second thread on a core is worth about a third
of a second core. Reproduce it on any Windows machine by dropping the two
prebuilt binaries from
[Releases](https://github.com/elaheJ/four-ways-to-wait/releases) into
[windows-laptop/smt-run/](windows-laptop/smt-run/) and double-clicking
`RUN-ME.bat` — nothing else to install.

Per-device numbers, with the device specification and the command that produced
each one: [instructor/reference_results.csv](instructor/reference_results.csv)
(Apple M1), [instructor/reference_results_x86.csv](instructor/reference_results_x86.csv)
(Intel Core Ultra), [instructor/reference_results_i5.csv](instructor/reference_results_i5.csv)
(Intel i5-7300U, the SMT device),
[instructor/reference_results_android.csv](instructor/reference_results_android.csv)
(Android, all five sessions), [run-log.md](run-log.md) (the browser sweep across
all four devices), [android/](android/) (per-session writeups), and
[phone/screenshots/](phone/screenshots/) for the first two phone sessions as the
student sees them.

## Running it in a class

Serve the browser lab to phones with `cd phone && python3 -m http.server 8000`,
then have students browse to `http://<host-lan-ip>:8000/threads.html`. Chrome on
Android auto-upgrades a typed address to HTTPS and fails the first time, so the
`http://` is worth spelling out on the handout. The page also runs from a
`file://` URL with no server at all, which is how it was verified on Chrome/macOS
and Edge/Windows.

`python3 -m http.server` sends no cache-control headers, so a device that loaded
the page in an earlier session can silently re-render the old copy — one of our
own phone sessions did, and its power state had to be recorded as unknown. Tell
students to hard-reload before they record anything.

The concept inventory is an outcome-aligned pre/post quiz: eight items, no
notation, mapped to all ten outcomes.
[Student form](instructor/concept-inventory-student-form.md) is here. The answer
key, the misconception each distractor targets, and the scoring and
administration notes are held back so the items stay usable in class —
instructors can request them from the author. It carries no item statistics; it
is an instrument for the classroom, not a psychometrically validated one.

MIT license.
