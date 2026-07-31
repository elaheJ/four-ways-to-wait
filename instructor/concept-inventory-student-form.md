# Who is waiting? — eight questions

**Your code:** ​\_\_\_\_\_\_\_\_  *(first two letters of the street you grew up on, then
the day of the month you were born — e.g. `MA14`. Not your name. Use the same
code both times you take this.)*

**Date:** ​\_\_\_\_\_\_\_\_

This is not graded on whether you get the answers right. You get credit for
taking it seriously, exactly like the predictions you commit to before each lab.
Most people find several of these hard the first time, which is the point — we
take it again at the end and compare.

Ten minutes. No calculators, no notes, no formulas needed. If you are stuck,
pick your best guess and move on.

Circle one answer per question.

---

**1.** A build script has ten steps. You run it with three workers, and then run
the same script again with five workers. How many steps are there in the second
run?

- **A.** Ten.
- **B.** Five — each worker does one step.
- **C.** Fifty — each worker runs all ten steps.
- **D.** It depends on how fast each worker is.

---

**2.** Two laptops both report "8 threads available." Laptop A has eight separate
cores. Laptop B has four cores, and each of its cores can run two threads at the
same time. You run a workload that keeps every thread busy doing arithmetic, with
nothing shared between them. What should you expect?

- **A.** Laptop B finishes slower, because each pair of B's threads shares one core's arithmetic hardware.
- **B.** They finish at the same time — both report eight threads.
- **C.** Laptop B finishes faster, because its threads are on fewer cores and so can communicate more quickly.
- **D.** Laptop A finishes slower, because it has to coordinate eight cores instead of four.

---

**3.** A program does a fixed amount of arithmetic. Nothing is shared between the
threads and no thread ever waits for another. On a machine with eight cores, you
run it with eight threads, then with sixteen. Both runs take the same wall-clock
time. Why?

- **A.** Past eight, the extra threads take turns on hardware that is already busy, so they add no new capacity.
- **B.** There is a bug — sixteen threads should take half as long as eight.
- **C.** The extra threads are waiting for a lock.
- **D.** The operating system refuses to create more than eight threads.

---

**4.** Four threads each add one to the same shared counter, one million times
each, with no protection of any kind. The right answer is four million. You run
the program five times. What do you expect?

- **A.** Five answers, most or all of them different, none of them above four million.
- **B.** Four million every time — addition is addition.
- **C.** The same wrong answer all five times, because the bug is in the code and the code does not change.
- **D.** Five different answers, some below four million and some above it.

---

**5.** The counter in question 4 is fixed by putting a lock around the increment,
so that only one thread can be adding at a time. It now gives four million every
single run. On one thread the program takes 3 seconds. On eight threads it takes
10 seconds. Which explanation is best?

- **A.** Only one thread can be inside the lock at a time, so the increments happen one after another however many threads there are — and the threads now also spend time handing the lock around.
- **B.** Locks are slow, so the eight-thread version pays a fixed extra cost that the one-thread version does not.
- **C.** The eight threads were spread onto slower efficiency cores.
- **D.** Adding threads cannot make a correct program slower; the measurement must be wrong.

---

**6.** Two threads each move money between two accounts. Thread 1 locks account A
and then tries to lock account B. Thread 2 locks account B and then tries to lock
account A. The program prints no error, does not crash, and does not finish — it
simply stops. What happened, and what is the cheapest fix?

- **A.** Each thread is holding one lock and waiting for the one the other holds. Make both threads take the two locks in the same order.
- **B.** One account went negative; add a balance check before each transfer.
- **C.** The threads crashed silently; wrap each transfer in error handling.
- **D.** The machine ran out of threads; use fewer of them.

---

**7.** A loop has 4000 iterations. The early iterations are quick, and they get
steadily more expensive, so the last iteration takes thousands of times as long
as the first. You want to run it on eight threads. Which way of handing out the
iterations finishes soonest?

- **A.** Hand out small batches to whichever thread is currently free, and keep handing them out until the iterations run out.
- **B.** Give each thread one contiguous block of 500 iterations, so each thread gets the same number of iterations.
- **C.** It makes no difference — the total amount of work is the same however you hand it out.
- **D.** Give all 4000 iterations to a single thread, to avoid the cost of coordinating eight of them.

---

**8.** A build has ten steps. Adding up how long every step takes gives 100
seconds. The longest chain of steps that have to happen strictly one after
another — each waiting on the one before it — takes 60 seconds. You can use as
many workers as you like, and each step needs only one worker. What is the
shortest time the build can possibly take?

- **A.** 60 seconds. No number of workers can beat it, because that chain has to run end to end.
- **B.** 10 seconds, if you use ten workers.
- **C.** 100 seconds — all of that work still has to be done.
- **D.** 25 seconds, because 100 seconds of work divided over four workers is 25.

---

*Hand this in. You will get it back at the end of the module and take it once
more — same eight questions — so you can see what changed.*

---

<sub>These eight items are written against the scheduling and multithreading
learning outcomes of the NSF/IEEE-TCPP Curriculum Initiative on Parallel and
Distributed Computing — *Core Topics for Undergraduates*, Version I, December
2012 (S. K. Prasad et al.). The answer key and per-item rationale are not
published; instructors can request them from the author. Part of
`four-ways-to-wait`, MIT licensed.</sub>
