/* pipeline.c -- Lab 3, part 2: producer-consumer, and what the buffer is for.
 *
 * One producer, one consumer, a bounded buffer between them, and a mutex with
 * two condition variables. The producer is slightly faster than the consumer,
 * so somebody is always waiting. The only thing that changes between runs is
 * the size of the buffer.
 *
 *   cc -O2 -o pipeline pipeline.c && ./pipeline
 */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ITEMS 200000
#define MAXCAP 4096

static int buf[MAXCAP];
static int cap, head, tail, count;
static long producer_waits, consumer_waits;

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t not_full  = PTHREAD_COND_INITIALIZER;
static pthread_cond_t not_empty = PTHREAD_COND_INITIALIZER;

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}
static double spin(int n) {           /* stands in for real per-item work */
    double s = 0; for (int i = 0; i < n; i++) s += (double)(i & 63) * 1.000001; return s;
}

static void *producer(void *v) {
    (void)v;
    for (int i = 0; i < ITEMS; i++) {
        spin(200);
        pthread_mutex_lock(&m);
        while (count == cap) { producer_waits++; pthread_cond_wait(&not_full, &m); }
        buf[tail] = i; tail = (tail + 1) % cap; count++;
        pthread_cond_signal(&not_empty);
        pthread_mutex_unlock(&m);
    }
    return NULL;
}
static void *consumer(void *v) {
    (void)v; double sink = 0;
    for (int i = 0; i < ITEMS; i++) {
        pthread_mutex_lock(&m);
        while (count == 0) { consumer_waits++; pthread_cond_wait(&not_empty, &m); }
        (void)buf[head]; head = (head + 1) % cap; count--;
        pthread_cond_signal(&not_full);
        pthread_mutex_unlock(&m);
        sink += spin(240);
    }
    if (sink == 1.0) printf("");
    return NULL;
}

static void run(int c) {
    cap = c; head = tail = count = 0; producer_waits = consumer_waits = 0;
    pthread_t p, q;
    double t0 = now();
    pthread_create(&p, NULL, producer, NULL);
    pthread_create(&q, NULL, consumer, NULL);
    pthread_join(p, NULL); pthread_join(q, NULL);
    double dt = now() - t0;
    printf("buffer %5d | %6.3f s | %8.0f items/s | producer blocked %7ld x | consumer blocked %7ld x\n",
           c, dt, ITEMS / dt, producer_waits, consumer_waits);
    fflush(stdout);
}

int main(void) {
    printf("one producer, one consumer, %d items; the consumer is the slower stage\n\n", ITEMS);
    for (int c = 1; c <= 1024; c *= 8) run(c);
    return 0;
}
