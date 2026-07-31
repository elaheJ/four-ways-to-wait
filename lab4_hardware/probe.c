/* probe.c -- Lab 4, optional: what is one core actually worth?
 *
 * Two strictly serial dependency chains the vectorizer cannot touch, so each
 * number is (clock / latency) for the one core this process is pinned to.
 * Run it pinned to a performance core, then to an efficiency core, and divide.
 * That is the empirical answer, rather than whatever the OS labels the core.
 *
 * The two chains disagree, which is the point: scaling.c's compute kernel is
 * FP-latency bound and rates an Intel E-core at 0.99 of a P-core, while the
 * integer chain rates the same two cores 1.43x apart. How much a core is worth
 * is a property of the code and the chip together.
 *
 *   cc -O2 -o probe probe.c
 *   taskpolicy -b ./probe            # macOS: efficiency cores
 *   taskset -c 0 ./probe             # Linux:  pin to logical processor 0
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    long long n = (argc > 1) ? atoll(argv[1]) : 200000000LL;

    /* serial double-precision multiply-add chain: latency bound */
    double best_fp = 1e18;
    volatile double fsink = 0.0;
    for (int t = 0; t < 3; t++) {
        double x = 1.0, t0 = now();
        for (long long i = 0; i < n; i++) x = x * 1.0000000001 + 1e-12;
        double dt = now() - t0;
        fsink += x;
        if (dt < best_fp) best_fp = dt;
    }

    /* serial integer chain: also latency bound, different unit */
    double best_int = 1e18;
    volatile long long isink = 0;
    for (int t = 0; t < 3; t++) {
        long long a = 1;
        double t0 = now();
        for (long long i = 0; i < n; i++) a = a * 6364136223846793005LL + 1442695040888963407LL;
        double dt = now() - t0;
        isink += a;
        if (dt < best_int) best_int = dt;
    }

    printf("fp_chain_s,%.4f,fp_Mops,%.1f,int_chain_s,%.4f,int_Mops,%.1f\n",
           best_fp, n / best_fp / 1e6, best_int, n / best_int / 1e6);
    return 0;
}
