/* counter.c -- Lab 3: four ways to add one, and what each one costs.
 *
 * T threads each add 1 to a shared counter, INCS times. The right answer is
 * T * INCS every single time. Run it five times and watch which versions
 * agree with themselves.
 *
 *   naive   : count++            -- no protection at all
 *   mutex   : lock / count++ / unlock
 *   atomic  : one hardware instruction, no lock
 *   private : each thread counts alone, one addition at the end
 *
 *   cc -O2 -o counter counter.c && ./counter 4
 */
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef INCS
#define INCS 2000000L
#endif
#define MAX_T 32

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* volatile keeps the optimizer from collapsing the whole loop into one add,
   which is what -O2 does otherwise -- and which hides the bug. */
static volatile long   plain_count;
static atomic_long     atomic_count;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

/* One cache line each, so threads do not fight over the same 64 bytes. */
typedef struct { int id; volatile long private_count; char pad[64]; } arg_t;

static void *naive(void *v)  { (void)v; for (long i = 0; i < INCS; i++) plain_count++; return NULL; }
static void *mutexed(void *v){ (void)v; for (long i = 0; i < INCS; i++) { pthread_mutex_lock(&lock); plain_count++; pthread_mutex_unlock(&lock); } return NULL; }
static void *atomiced(void *v){(void)v; for (long i = 0; i < INCS; i++) atomic_fetch_add(&atomic_count, 1); return NULL; }
static void *privateed(void *v) {
    arg_t *a = (arg_t *)v;                          /* nothing is shared until main adds them up */
    for (long i = 0; i < INCS; i++) a->private_count++;
    return NULL;
}

static void run(const char *name, void *(*fn)(void *), int T) {
    pthread_t th[MAX_T]; arg_t a[MAX_T];
    plain_count = 0; atomic_store(&atomic_count, 0);
    double t0 = now();
    for (int i = 0; i < T; i++) { a[i].id = i; a[i].private_count = 0; pthread_create(&th[i], NULL, fn, &a[i]); }
    long total = 0;
    for (int i = 0; i < T; i++) { pthread_join(th[i], NULL); total += a[i].private_count; }
    double dt = now() - t0;

    long got = (fn == atomiced) ? atomic_load(&atomic_count)
             : (fn == privateed) ? total : plain_count;
    long want = (long)T * INCS;
    printf("%-8s %10ld / %10ld  %s  %7.3f s  (%.0f ns per increment)\n",
           name, got, want, got == want ? "correct" : "LOST UPDATES",
           dt, dt * 1e9 / (double)want);
    fflush(stdout);
}

int main(int argc, char **argv) {
    int T = (argc > 1) ? atoi(argv[1]) : 4;
    printf("%d threads x %ld increments each; correct answer is always %ld\n\n", T, INCS, (long)T * INCS);
    run("naive",   naive,     T);
    run("mutex",   mutexed,   T);
    run("atomic",  atomiced,  T);
    run("private", privateed, T);
    return 0;
}
