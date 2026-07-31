#!/usr/bin/env python3
"""taskgraph.py -- Lab 1: the two numbers that bound every parallel program.

A task graph is a list of jobs, each with a duration and a list of jobs that
must finish before it may start. Two numbers fall out of the graph alone,
before any hardware is chosen:

    work  T1   -- add up every duration.        One worker takes at least this.
    span  Tinf -- the longest chain of arrows.  All the workers on earth cannot
                  finish sooner than this.

Everything a scheduler can do lives between them:  Tp >= max(T1/p, Tinf).

This script runs the graph for real on p worker threads, with a greedy
scheduler that starts any task whose inputs are ready, and prints the measured
makespan next to the two bounds. Durations are modelled by sleeping, so the
numbers are the same on a phone, a laptop, and a login node.

    python3 taskgraph.py            # the built-in "morning build" graph
    python3 taskgraph.py --workers 8
    python3 taskgraph.py --graph mine.csv     # name,duration,dependencies
"""
import argparse, csv, threading, time, queue, sys

# name -> (duration in seconds, list of prerequisites)
BUILD = {
    "checkout":   (0.30, []),
    "compile_a":  (0.90, ["checkout"]),
    "compile_b":  (0.60, ["checkout"]),
    "compile_c":  (0.45, ["checkout"]),
    "compile_d":  (0.45, ["checkout"]),
    "link":       (0.40, ["compile_a", "compile_b", "compile_c", "compile_d"]),
    "unit_test":  (0.80, ["link"]),
    "docs":       (0.70, ["checkout"]),
    "lint":       (0.25, ["checkout"]),
    "package":    (0.35, ["unit_test", "docs", "lint"]),
}


def load(path):
    g = {}
    with open(path) as f:
        for row in csv.reader(f):
            if not row or row[0].lstrip().startswith("#"):
                continue
            name, dur, *deps = [c.strip() for c in row]
            g[name] = (float(dur), [d for d in deps if d])
    return g


def work_and_span(g):
    """T1 is the sum of the durations. Tinf is the longest path. No hardware involved."""
    t1 = sum(d for d, _ in g.values())
    memo, path = {}, {}

    def longest(n):
        if n not in memo:
            best, via = 0.0, []
            for p in g[n][1]:
                if longest(p) > best:
                    best, via = longest(p), path[p] + [p]
            memo[n], path[n] = best + g[n][0], via
        return memo[n]

    end = max(g, key=longest)
    return t1, memo[end], path[end] + [end]


def run(g, p):
    """Greedy list scheduling on p worker threads. A task starts as soon as a
    worker is free and every prerequisite has finished."""
    remaining = {n: len(deps) for n, (_, deps) in g.items()}
    children = {n: [] for n in g}
    for n, (_, deps) in g.items():
        for d in deps:
            children[d].append(n)

    ready = queue.Queue()
    for n, k in remaining.items():
        if k == 0:
            ready.put(n)

    lock = threading.Lock()
    left = len(g)
    log = []
    t0 = time.perf_counter()

    def worker(wid):
        nonlocal left
        while True:
            try:
                n = ready.get(timeout=0.05)
            except queue.Empty:
                with lock:
                    if left == 0:
                        return
                continue
            start = time.perf_counter() - t0
            time.sleep(g[n][0])                      # the task actually running
            end = time.perf_counter() - t0
            with lock:
                log.append((n, wid, start, end))
                left -= 1
                for c in children[n]:
                    remaining[c] -= 1
                    if remaining[c] == 0:
                        ready.put(c)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(p)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.perf_counter() - t0, sorted(log, key=lambda r: r[2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph")
    ap.add_argument("--workers", type=int, default=0, help="0 = sweep 1..8")
    ap.add_argument("--trace", action="store_true", help="print who ran what, when")
    a = ap.parse_args()

    g = load(a.graph) if a.graph else BUILD
    t1, tinf, crit = work_and_span(g)
    print(f"{len(g)} tasks")
    print(f"work  T1   = {t1:.2f} s   (one worker can do no better)")
    print(f"span  Tinf = {tinf:.2f} s   (no number of workers can do better)")
    print(f"critical path: {' -> '.join(crit)}")
    print(f"most parallelism worth buying: T1/Tinf = {t1/tinf:.1f} workers\n")

    ps = [a.workers] if a.workers else [1, 2, 3, 4, 6, 8]
    print(f"{'p':>3} {'makespan':>9} {'lower bound':>12} {'speedup':>8} {'efficiency':>11}")
    for p in ps:
        mk, log = run(g, p)
        bound = max(t1 / p, tinf)
        print(f"{p:>3} {mk:>8.2f}s {bound:>11.2f}s {t1/mk:>8.2f} {t1/mk/p:>10.0%}")
        if a.trace:
            for n, w, s, e in log:
                print(f"      worker {w}  {s:5.2f} -> {e:5.2f}  {n}")
    print("\nAdding workers stops helping once the makespan reaches the span.")
    print("At that point the graph, not the machine, is the constraint.")


if __name__ == "__main__":
    sys.exit(main())
