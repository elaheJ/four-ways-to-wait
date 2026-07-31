/* deadlock.c -- Lab 3, part 3: a hang you can reproduce, and a one-line fix.
 *
 * Two accounts, two locks, two threads transferring money in opposite
 * directions. Each thread takes the lock on the account it is debiting first.
 * That single choice is the whole bug.
 *
 *   ./deadlock bad    -- lock in the order the transfer happens to name them
 *   ./deadlock good   -- always lock the lower-numbered account first
 *
 * The bad version does not crash and does not print an error. It just stops,
 * which is the point: nothing in the language or the hardware objects.
 * A watchdog reports the hang after 3 seconds without progress, so the lab
 * does not stall.
 */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define TRANSFERS 100

static pthread_mutex_t lockA = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t lockB = PTHREAD_MUTEX_INITIALIZER;
static int balA = 1000, balB = 1000;
static volatile int done = 0;
static volatile long completed = 0;   /* the watchdog watches this, not the clock */
static int ordered = 0;

static void transfer(int from, int amount) {
    pthread_mutex_t *first, *second;
    if (ordered) {                       /* always A then B, whatever the direction */
        first = &lockA; second = &lockB;
    } else {                             /* debited account first -- the bug */
        first = from == 0 ? &lockA : &lockB;
        second = from == 0 ? &lockB : &lockA;
    }
    pthread_mutex_lock(first);
    usleep(1000);                        /* widen the window; the race is real without it */
    pthread_mutex_lock(second);
    if (from == 0) { balA -= amount; balB += amount; }
    else           { balB -= amount; balA += amount; }
    completed++;
    pthread_mutex_unlock(second);
    pthread_mutex_unlock(first);
}

static void *t0(void *v) { (void)v; for (int i = 0; i < TRANSFERS; i++) transfer(0, 1); return NULL; }
static void *t1(void *v) { (void)v; for (int i = 0; i < TRANSFERS; i++) transfer(1, 1); return NULL; }

/* Watch for lack of PROGRESS, not for elapsed time. A deadlocked program stops
   completing transfers; a merely slow one does not. Timing the ordered path
   instead would make this a false alarm on any platform where usleep is coarse
   -- on Windows a 1 ms sleep really takes about 16 ms, which is enough to trip
   a wall-clock watchdog on a program that is working perfectly. */
static void *watchdog(void *v) {
    (void)v;
    long last = -1;
    int stalled = 0;
    while (!done) {
        usleep(500000);
        long now = completed;
        if (now == last) {
            if (++stalled >= 6) {          /* 3 s with nothing finishing */
                printf("DEADLOCK: %ld transfers done, then no progress for 3 s. "
                       "Both threads hold one lock and want the other.\n", now);
                fflush(stdout);
                _exit(2);
            }
        } else {
            stalled = 0;
            last = now;
        }
    }
    return NULL;
}

int main(int argc, char **argv) {
    ordered = (argc > 1 && strcmp(argv[1], "good") == 0);
    printf("lock order: %s\n", ordered ? "ordered (always A then B)" : "as named by the transfer");
    pthread_t a, b, w;
    pthread_create(&w, NULL, watchdog, NULL);
    pthread_create(&a, NULL, t0, NULL);
    pthread_create(&b, NULL, t1, NULL);
    pthread_join(a, NULL); pthread_join(b, NULL);
    done = 1;
    printf("finished. A=%d B=%d total=%d\n", balA, balB, balA + balB);
    return 0;
}
