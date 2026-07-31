/* scaling.c -- Lab 4: how much does one more thread buy?
 *
 * Two kernels, identical thread structure, opposite answers.
 *   compute : arithmetic in registers, nothing shared, no memory traffic
 *   memory  : streaming reduction over a large array, bandwidth bound
 *
 * Total work is fixed; only the number of threads changes.
 *
 *   cc -O2 -o scaling scaling.c && ./scaling
 */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_T 32

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ---- compute-bound: no memory traffic, no sharing ---- */
static long long COMPUTE_ITERS = 400000000LL;

typedef struct {
    long long lo, hi;      /* iteration range for this thread */
    double *arr;           /* memory kernel only */
    double result;
} arg_t;

static void *compute_worker(void *v) {
    arg_t *a = (arg_t *)v;
    double x = 1.0000001, acc = 0.0;
    for (long long i = a->lo; i < a->hi; i++) acc += x * (double)(i & 1023);
    a->result = acc;
    return NULL;
}

/* ---- memory-bound: streaming read, one flop per 8 bytes ---- */
#define MEM_REPS 12
static void *memory_worker(void *v) {
    arg_t *a = (arg_t *)v;
    double acc = 0.0;
    const double *p = a->arr;
    for (int r = 0; r < MEM_REPS; r++)
        for (long long i = a->lo; i < a->hi; i++) acc += p[i];
    a->result = acc;
    return NULL;
}

static double once(int t, void *(*fn)(void *), long long n, double *arr) {
    pthread_t th[MAX_T];
    arg_t a[MAX_T];
    long long chunk = n / t;
    double t0 = now();
    for (int i = 0; i < t; i++) {
        a[i].lo = i * chunk;
        a[i].hi = (i == t - 1) ? n : (i + 1) * chunk;
        a[i].arr = arr;
        pthread_create(&th[i], NULL, fn, &a[i]);
    }
    double sink = 0.0;
    for (int i = 0; i < t; i++) { pthread_join(th[i], NULL); sink += a[i].result; }
    double dt = now() - t0;
    if (sink == 12345.6789) printf("");   /* keep the compiler honest */
    return dt;
}

/* Best of three. The first pass at any thread count warms caches and page
   tables; timing it would make later runs look superlinear. */
static double run(int t, void *(*fn)(void *), long long n, double *arr) {
    double best = 1e18;
    for (int trial = 0; trial < 4; trial++) {
        double dt = once(t, fn, n, arr);
        if (trial > 0 && dt < best) best = dt;
    }
    return best;
}

int main(int argc, char **argv) {
    int maxt = (argc > 1) ? atoi(argv[1]) : 16;
    if (maxt > MAX_T) maxt = MAX_T;

    long long nmem = 64LL * 1024 * 1024;               /* 512 MiB of doubles */
    double *arr = malloc((size_t)nmem * sizeof(double));
    for (long long i = 0; i < nmem; i++) arr[i] = 1.0;
    (void)once(1, memory_worker, nmem, arr);           /* global warm-up */

    printf("threads,compute_s,compute_speedup,compute_eff,memory_GBs,memory_speedup,memory_eff\n");
    double c1 = 0, m1 = 0;
    for (int t = 1; t <= maxt; t++) {
        double c = run(t, compute_worker, COMPUTE_ITERS, NULL);
        double m = run(t, memory_worker, nmem, arr);
        if (t == 1) { c1 = c; m1 = m; }
        double gbs = (double)nmem * 8.0 * MEM_REPS / m / 1e9;
        printf("%d,%.3f,%.2f,%.2f,%.1f,%.2f,%.2f\n",
               t, c, c1 / c, (c1 / c) / t, gbs, m1 / m, (m1 / m) / t);
        fflush(stdout);
    }
    free(arr);
    return 0;
}
