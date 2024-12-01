#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define ALLOCATION_SIZE_MB 512  // Size of each allocation burst (in MB)
#define NUM_ALLOCATION_BURSTS 70 // Number of bursts before deallocation
#define NUM_ALLOCATION_PASSIVE 10
#define PAGE_SIZE 4096  // System page size (4 KB)
#define SLEEP_BETWEEN_BURSTS 0.01  // Sleep time between bursts (in seconds)
#define SLEEP_AFTER_RELEASE 0.5   // Sleep time after releasing memory (in seconds)

long long get_time_in_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

int compare(const void *a, const void *b) {
    return (*(int *)a - *(int *)b);
}

// Function to calculate the average
long long calculate_average(long long *arr, int n) {
    long long sum = 0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum / n;
}

// Function to calculate the median
long long calculate_median(long long *arr, int n) {
    if (n % 2 == 0) {
        return (arr[n / 2 - 1] + arr[n / 2]) / 2.0;
    } else {
        return arr[n / 2];
    }
}

long long calculate_standard_deviation(long long *arr, int n, long long mean) {
    long long sum_squared_diff = 0;
    for (int i = 0; i < n; i++) {
        long long diff = arr[i] - mean;
        sum_squared_diff += diff * diff;
    }
    return sqrt(sum_squared_diff / n);
}

// Function to calculate the percentile
long long calculate_percentile(long long *arr, int n, int percentile) {
    double rank = (percentile / 100.0) * (n - 1);
    int lower_index = (int)rank;
    int upper_index = lower_index + 1;

    if (upper_index >= n) {
        return arr[lower_index];
    }

    double weight = rank - lower_index;
    return arr[lower_index] * (1 - weight) + arr[upper_index] * weight;
}

void touch_memory(void *addr, size_t size) {
    char *ptr = (char *)addr;
    for (size_t i = 0; i < size; i += PAGE_SIZE) {
        ptr[i] = (char)i;  // Write to each page to ensure it's marked as accessed
    }
}

void access_memory(char *buffer, size_t size) {
    for (size_t i = 0; i < size; i += PAGE_SIZE) {
        buffer[i] = (char)(i % 256); // Access each page
    }
}
// Allocate memory and simulate workload
void bursty_memory_usage() {
    void **buffers = malloc(NUM_ALLOCATION_BURSTS * sizeof(void *));
    void **buffers_passive = malloc(NUM_ALLOCATION_PASSIVE * sizeof(void *));
    if (!buffers || !buffers_passive) {
        perror("malloc failed");
        exit(EXIT_FAILURE);
    }

    printf("Starting passive memory allocation...\n");

    for (int i = 0; i < NUM_ALLOCATION_PASSIVE; i++) {
        // printf("Allocating %d MB (Burst %d/%d)\n", ALLOCATION_SIZE_MB, i + 1, NUM_ALLOCATION_PASSIVE);

        // Allocate memory
        buffers_passive[i] = malloc(ALLOCATION_SIZE_MB);
        if (!buffers_passive[i]) {
            perror("malloc failed");
            exit(EXIT_FAILURE);
        }

        // Touch all pages to ensure they are allocated in DRAM
        memset(buffers_passive[i], i, ALLOCATION_SIZE_MB);

        // Simulate work
        // sleep(0.1);
    }

    printf("Starting bursty memory allocation...\n");

    for (int i = 0; i < NUM_ALLOCATION_BURSTS; i++) {
        // printf("Allocating %d MB (Burst %d/%d)\n", ALLOCATION_SIZE_MB, i + 1, NUM_ALLOCATION_BURSTS);

        // Allocate memory
        buffers[i] = malloc(ALLOCATION_SIZE_MB * 1024 * 1024);
        if (!buffers[i]) {
            perror("malloc failed");
            exit(EXIT_FAILURE);
        }

        // Touch all pages to ensure they are allocated in DRAM
        // memset(buffers[i], i, ALLOCATION_SIZE_MB * 1024 * 1024);

        access_memory(buffers[i], ALLOCATION_SIZE_MB * 1024 * 1024);

        // Simulate work
        // sleep(SLEEP_BETWEEN_BURSTS);
    }

    // printf("All bursts allocated. Sleeping for %d seconds...\n", SLEEP_AFTER_RELEASE);
    // sleep(SLEEP_AFTER_RELEASE);

    // Free memory abruptly
    printf("Releasing memory...\n");
    for (int i = 0; i < NUM_ALLOCATION_BURSTS; i++) {
        free(buffers[i]);
    }
    for (int i = 0; i < NUM_ALLOCATION_PASSIVE; i++) {
        free(buffers_passive[i]);
    }

    free(buffers);
    free(buffers_passive);
    printf("Memory released.\n");
    
}

int main() {
    int n = 100;
    long long latencies[n];
    int i =0;

    printf("Sleeping...");
    sleep(10);
    // printf("Sleeping...2");
    // sleep(10);

    while (i < n) {
        printf("Iter: %d\n", i);
        long long start_time = get_time_in_ns();

        bursty_memory_usage();

        printf("Cycle completed. Sleeping before the next cycle...\n\n");
        long long end_time = get_time_in_ns();
        long long latency_ns = end_time - start_time;
        double latency_ms = latency_ns / 1e6; // Convert to milliseconds
        printf("Total latency: %.2f ms\n", latency_ms);
        latencies[i] = latency_ns;
        // sleep(SLEEP_AFTER_RELEASE);
        i++;
    }
    qsort(latencies, n, sizeof(long long), compare);

    long long average = calculate_average(latencies, n);
    long long std_dev = calculate_standard_deviation(latencies, n, average);
    long long median = calculate_median(latencies, n);
    long long p75 = calculate_percentile(latencies, n, 75);
    long long p99 = calculate_percentile(latencies, n, 99);

    printf("Average: %lld\n", average);
    printf("Standard Deviation: %lld\n", std_dev);
    printf("Median: %lld\n", median);
    printf("75th Percentile (P75): %lld\n", p75);
    printf("99th Percentile (P99): %lld\n", p99);

    return 0;
}
