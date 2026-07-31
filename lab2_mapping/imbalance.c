/* imbalance.c -- Lab 2: the same loop, four ways of handing it out.
 *
 * 4096 iterations. Iteration i costs about i units of work, so the loop is
 * deliberately lopsided: the last iteration is 4096x the cost of the first.
 * Total work is identical under every schedule. Only the assignment changes.
 *
 *   block   : thread k gets one contiguous chunk        (static, owner-computes)
 *   cyclic  : thread k gets iterations k, k+T, k+2T ... (static, round robin)
 *   dyn-64  : threads pull chunks of 64 from a queue    (dynamic)
 *   dyn-1   : threads pull one iteration at a time      (dynamic, finest)
 *
 * Reports makespan, the busiest and idlest thread, and the imbalance ratio
 * (busiest / average). Perfect balance is 1.00.
 *
 *   cc -O2 -o imbalance imbalance.c && ./imbalance 4
 */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 4096
#define MAX_T 32

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* The body of one loop iteration. Cost grows with i. */
static double iteration(int i) {
    double acc = 0.0;
    long reps = (long)i * 3000L;
    for (long k = 0; k < reps; k++) acc += (double)(k & 255) * 1.000001;
    return acc;
}

typedef enum { BLOCK, CYCLIC, DYN } sched_t;

typedef struct {
    int id, nthreads, chunk;
    sched_t sched;
    double busy, sink;
    long iters;
} arg_t;

static int next_chunk = 0;
static pthread_mutex_t queue_lock = PTHREAD_MUTEX_INITIALIZER;

static void *worker(void *v) {
    arg_t *a = (arg_t *)v;
    double t0 = now(), s = 0.0;
    long count = 0;

    if (a->sched == BLOCK) {
        int per = N / a->nthreads;
        int lo = a->id * per, hi = (a->id == a->nthreads - 1) ? N : lo + per;
        for (int i = lo; i < hi; i++) { s += iteration(i); count++; }
    } else if (a->sched == CYCLIC) {
        for (int i = a->id; i < N; i += a->nthreads) { s += iteration(i); count++; }
    } else {
        for (;;) {
            pthread_mutex_lock(&queue_lock);
            int lo = next_chunk;
            next_chunk += a->chunk;
            pthread_mutex_unlock(&queue_lock);
            if (lo >= N) break;
            int hi = lo + a->chunk; if (hi > N) hi = N;
            for (int i = lo; i < hi; i++) { s += iteration(i); count++; }
        }
    }
    a->busy = now() - t0;
    a->sink = s;
    a->iters = count;
    return NULL;
}

static void run(const char *name, sched_t sched, int chunk, int T) {
    pthread_t th[MAX_T];
    arg_t a[MAX_T];
    next_chunk = 0;
    double t0 = now();
    for (int i = 0; i < T; i++) {
        a[i] = (arg_t){ .id = i, .nthreads = T, .chunk = chunk, .sched = sched };
        pthread_create(&th[i], NULL, worker, &a[i]);
    }
    for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
    double makespan = now() - t0;

    double sum = 0, mx = 0, mn = 1e18;
    for (int i = 0; i < T; i++) {
        sum += a[i].busy;
        if (a[i].busy > mx) mx = a[i].busy;
        if (a[i].busy < mn) mn = a[i].busy;
    }
    double avg = sum / T;
    printf("%-8s makespan %6.3f s | busiest %6.3f | idlest %6.3f | imbalance %4.2f | idle %5.1f%%\n",
           name, makespan, mx, mn, mx / avg, 100.0 * (1.0 - avg / makespan));
    fflush(stdout);
}

int main(int argc, char **argv) {
    int T = (argc > 1) ? atoi(argv[1]) : 4;
    printf("%d iterations, %d threads, cost of iteration i grows with i\n\n", N, T);
    run("block",  BLOCK,  0,  T);
    run("cyclic", CYCLIC, 0,  T);
    run("dyn-64", DYN,    64, T);
    run("dyn-1",  DYN,    1,  T);
    return 0;
}
