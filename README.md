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

## Three reference devices, and they disagree

| | Apple M1 | Intel Core Ultra 7 265 | Android phone |
|---|---|---|---|
| Reported threads | 8 | 20 | 8 |
| Cores | 4 P + 4 E | 8 P + 12 E | 4 big + 4 little |
| SMT | none | **none** — Intel removed it from this generation | none |
| Peak speedup | 5.45× | 14.9× | **3.2–4.2×** |
| E-core worth, same kernel | **0.50** of a P-core | **0.99** of a P-core | — |

**The phone advertises 8 threads and delivers between a third and a half of
that.** In both sessions the *fifth worker was slower than the fourth*
(171→203 ms, then 294→342 ms) — the signature of a 4+4 big.LITTLE part. Adding a
worker cost time, on a device the student owns.

**But the phone is a noisy instrument, and that is the second lesson.** Peak
speedup was 4.15× in one session and 3.17× in the next, 15 minutes apart on the
same device — and the second session even showed two workers running *slower*
than one, which is a noise floor, not a result. Counter-intuitively the run on
charge was the noisier one; charging heats the phone. Quote what repeats (where
the curve bends, which worker made things worse), not the milliseconds.

**The two laptops disagree about their own E-cores**, which is the other finding.
`scaling.c`'s compute kernel compiles to a
scalar single-accumulator loop whose throughput is set by FP-add *latency*, so it
is blind to everything that distinguishes a big core from a small one. Swap in a
dependent integer chain — `lab4_hardware/probe.c` — and the same two Intel cores
separate by 1.43×. **How much a core is worth is a property of the code and the
chip together, not the chip.**

SMT is measured with a pinned comparison that works whether or not the device has
it: hold the thread count at 4 and go from 4 physical cores to 2. Without SMT that
costs a factor of 2, and both reference devices measure it — **1.93×** — which is
the control the comparison is read against. On a machine with SMT the same
contrast costs noticeably less, and that gap is the lab's answer.

Per-device numbers, with the device specification and the command that produced
each one: [instructor/reference_results.csv](instructor/reference_results.csv)
(Apple M1), [instructor/reference_results_x86.csv](instructor/reference_results_x86.csv)
(Intel), [instructor/reference_results_android.csv](instructor/reference_results_android.csv)
(Android), and [phone/screenshots/](phone/screenshots/) for the phone sessions
as the student sees them.

## Running it in a class

Serve the browser lab to phones with `cd phone && python3 -m http.server 8000`,
then have students browse to `http://<host-lan-ip>:8000/threads.html`. Chrome on
Android auto-upgrades a typed address to HTTPS and fails the first time, so the
`http://` is worth spelling out on the handout. The page also runs from a
`file://` URL with no server at all, which is how it was verified on Chrome/macOS
and Edge/Windows.

The concept inventory is an outcome-aligned pre/post quiz: eight items, no
notation, mapped to all ten outcomes.
[Student form](instructor/concept-inventory-student-form.md) is here. The answer
key, the misconception each distractor targets, and the scoring and
administration notes are held back so the items stay usable in class —
instructors can request them from the author. It carries no item statistics; it
is an instrument for the classroom, not a psychometrically validated one.

MIT license.
