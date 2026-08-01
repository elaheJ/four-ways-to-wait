# Four Ways to Wait

Four hands-on labs. They deliver ten core scheduling and multithreading learning
outcomes on hardware students already own. Each lab asks one question: who is
waiting, and why?

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
| Lab 2, block schedule | **3.75×** | on an unequal split, 43.7% of the machine idle |
| Lab 1, task graph | **1.85×** | on the arrows: the span sets the limit, not the machine |
| Lab 3, shared counter under a mutex | **0.30×** | on each other, 3.3× *slower* than one thread |

Lab 4 measures what the hardware gives on work with nothing shared and nothing
waiting. That is **5.45×**, not 8. Four of those cores are efficiency cores,
worth half a performance core each.

## The labs

| Lab | Runs on | What it measures |
|---|---|---|
| **1: waiting on the arrows** | phone browser, or Python 3.10+ | Work, span, and why more workers stop helping |
| **2: waiting on an unequal split** | phone browser, or C | Block vs. cyclic vs. dynamic over one lopsided loop |
| **3: waiting on each other** | C | Races, lost updates, critical-section cost, producer–consumer, deadlock |
| **4: waiting on hardware that is not there** | C (+ browser) | Thread scaling to 2× core count; P-cores vs. E-cores; bandwidth saturation |

Labs 1 and 2 need **nothing installed**. Open `phone/threads.html` on any phone
or laptop. No account, no network after page load, no elevated permission.

## Quick start

```sh
# no install at all: open in any browser, including a phone
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
```

## Outcome coverage

| Outcome | Lab |
|---|---|
| MIMD in practice; tasks vs. threads | 1, 4 |
| SMT vs. multicore: what is shared | class census |
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
2012 (S. K. Prasad et al.). They are drawn from its architecture, programming and
algorithms strands, and abbreviated here for the table. The wording above is
condensed. The source wording governs. Curriculum website:
<http://www.cs.gsu.edu/~tcpp/curriculum/index.php>

## Reference measurements

Every number in the paper is measured. Each row of the reference tables carries
the device specification and the command that produced it. `make_fig1.py`
regenerates the paper's figure from those values.

Reference device: Apple M1 (4 P + 4 E cores, 8 GB), macOS 26.5, Apple clang 21,
`cc -O2`. Harnesses discard a warm-up pass and report best-of-three. The counter
figures are medians of three sweeps at 40 M increments per thread.

## Four reference devices, and they disagree

| | Apple M1 | Intel Core Ultra 7 265 | Intel i5-7300U | Android phone |
|---|---|---|---|---|
| Reported threads | 8 | 20 | 4 | 8 |
| Cores | 4 P + 4 E | 8 P + 12 E | 2 (homogeneous) | 4 big + 4 little |
| SMT | none | **none**. Intel removed it from this generation | **yes**, 2 cores, 4 threads | none |
| Peak speedup | 5.45× | 14.9× | 2.75× | **3.2–4.5×** |
| Halve the cores, fixed threads | — | **1.93×** (no SMT) | **1.38×** (SMT) | — |
| E-core worth, same kernel | **0.50** of a P-core | **0.99** of a P-core | 1.01, cores identical | — |

The i5-7300U is a 2017 ultrabook part. It is in the table for two reasons. It is
the low end of what students actually carry, and it is the only device here with
SMT. That is what makes the SMT lesson measurable. Halving the physical cores
under a fixed thread count costs 1.93× on the Core Ultra, which has no SMT. It
costs 1.38× here, which does. The two runs give a control and a treatment on the
same test.

What a hyperthread is worth has no single answer. On the same core in the same
run, the second hyperthread is worth **1.35×** on the compute kernel and
**1.89×** on the memory kernel. A thread stalled on memory leaves the core's
execution units idle. That is the gap SMT exists to fill. A thread saturating the
floating-point pipeline leaves almost nothing to share. The E-core comparison
teaches the same lesson from the other side.

The phone advertises 8 threads and delivers between a third and a half of that.
In all five sessions the *fifth worker was slower than the fourth* (171→203,
294→342, 155→196, 172→227, 173→215 ms). That is the signature of a 4+4
big.LITTLE part. Adding a worker cost time, on a device the student owns. The
effect reproduces under Firefox as well as Chrome, so it is the hardware rather
than one browser's worker scheduling.

The phone is also a noisy instrument, which is the second lesson. Peak speedup
ranged 3.17× to 4.47× across five sessions on the same device. The worst and best
were only hours apart. One session showed two workers running *slower* than one,
which is a noise floor rather than a result. Counter-intuitively, the run on
charge was among the noisier ones. Charging heats the phone. Quote what repeats:
where the curve bends, and which worker made things worse. Do not quote the
milliseconds.

Browser choice does not move any of this. Chrome, Edge and Firefox agree within
session noise on the same Windows laptop. Safari and Chrome on the M1 differ by
0.2% at one worker. What the browser *says* is another matter. Chrome reports
`Android 10` on an Android 15 handset, and `MacIntel` on arm64 silicon. The
census measures the device instead of asking it. Students find that out in §1 of
the browser lab.

The two laptops disagree about their own E-cores, which is the other finding.
`scaling.c`'s compute kernel compiles to a scalar single-accumulator loop. Its
throughput is set by FP-add *latency*. That makes it blind to everything
distinguishing a big core from a small one. Swap in a dependent integer chain,
`lab4_hardware/probe.c`, and the same two Intel cores separate by 1.43×. How much
a core is worth is a property of the code and the chip together, not of the chip
alone.

SMT is measured with a pinned comparison that works whether or not the device has
it. Hold the thread count fixed. Halve the physical cores those threads may use.
Without SMT that costs a factor of 2. The Core Ultra measures **1.93×**, the
control. With SMT it costs less, and the shortfall is the answer. The i5-7300U
measures **1.38×**, so a second thread on a core is worth about a third of a
second core. Reproduce it on any Windows machine. Drop the two prebuilt binaries
from [Releases](https://github.com/elaheJ/four-ways-to-wait/releases) into
[windows-laptop/smt-run/](windows-laptop/smt-run/), then double-click
`RUN-ME.bat`. Nothing else to install.

Per-device numbers carry the device specification and the command that produced
each one. Apple M1 is in
[instructor/reference_results.csv](instructor/reference_results.csv). Intel Core
Ultra is in
[instructor/reference_results_x86.csv](instructor/reference_results_x86.csv).
Intel i5-7300U, the SMT device, is in
[instructor/reference_results_i5.csv](instructor/reference_results_i5.csv). All
five Android sessions are in
[instructor/reference_results_android.csv](instructor/reference_results_android.csv).
The browser sweep across all four devices is in [run-log.md](run-log.md), and the
per-session writeups are in [android/](android/).
[phone/screenshots/](phone/screenshots/) has the first two phone sessions as the
student sees them.

## Running it in a class

Serve the browser lab to phones with `cd phone && python3 -m http.server 8000`.
Students then browse to `http://<host-lan-ip>:8000/threads.html`. Chrome on
Android auto-upgrades a typed address to HTTPS and fails the first time. Spell
the `http://` out on the handout. The page also runs from a `file://` URL with no
server at all. That is how it was verified on Chrome/macOS and Edge/Windows.

`python3 -m http.server` sends no cache-control headers. A device that loaded the
page in an earlier session can silently re-render the old copy. One of our own
phone sessions did, and its power state had to be recorded as unknown. Tell
students to hard-reload before they record anything.

The concept inventory is an outcome-aligned pre/post quiz. Eight items, no
notation, mapped to all ten outcomes. The
[student form](instructor/concept-inventory-student-form.md) is here. The answer
key, the misconception each distractor targets, and the scoring and
administration notes are held back, so the items stay usable in class.
Instructors can request them from the author. The inventory carries no item
statistics. It is an instrument for the classroom, not a psychometrically
validated one.

MIT license.
