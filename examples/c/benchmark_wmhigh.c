#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <errno.h>
#include <sys/mman.h>

#define NUM_FILES 30           // Number of files to create
#define FILE_SIZE_MB 500       // Size of each file in MB
#define READ_RATIO 0.7         // Percentage of operations that are reads
#define NUM_ITERATIONS 5      // Number of iterations for averaging
#define BLOCK_SIZE 4096        // Block size for read/write in bytes
#define FILE_PATH "./test_files" // Directory for storing files

void generate_files() {
    // Create directory for files
    if (mkdir(FILE_PATH, 0755) && errno != EEXIST) {
        perror("Failed to create directory");
        exit(EXIT_FAILURE);
    }

    // Generate files with random data
    for (int i = 0; i < NUM_FILES; i++) {
        char file_name[256];
        snprintf(file_name, sizeof(file_name), "%s/file_%d.dat", FILE_PATH, i);

        printf("Creating %s...\n", file_name);

        int fd = open(file_name, O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd < 0) {
            perror("Failed to open file for writing");
            exit(EXIT_FAILURE);
        }

        char *buffer = malloc(BLOCK_SIZE);
        if (!buffer) {
            perror("Failed to allocate buffer");
            exit(EXIT_FAILURE);
        }

        for (size_t j = 0; j < (FILE_SIZE_MB * 1024 * 1024) / BLOCK_SIZE; j++) {
            for (int k = 0; k < BLOCK_SIZE; k++) {
                buffer[k] = rand() % 256;
            }
            if (write(fd, buffer, BLOCK_SIZE) != BLOCK_SIZE) {
                perror("Failed to write to file");
                exit(EXIT_FAILURE);
            }
        }

        free(buffer);
        close(fd);
    }

    printf("File generation complete.\n");
}

long long get_time_in_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

double simulate_workload(int total_iterations) {
    char file_names[NUM_FILES][256];
    for (int i = 0; i < NUM_FILES; i++) {
        snprintf(file_names[i], sizeof(file_names[i]), "%s/file_%d.dat", FILE_PATH, i);
    }

    double total_latency = 0.0;

    for (int iteration = 0; iteration < total_iterations; iteration++) {
        printf("Iteration %d/%d...\n", iteration + 1, total_iterations);

        long long start_time = get_time_in_ns();

        for (int op = 0; op < 100000; op++) { // Perform 100 operations per iteration
            int file_index = rand() % NUM_FILES;
            const char *file_name = file_names[file_index];
            int is_read = (rand() % 100) < (READ_RATIO * 100);

            int fd = open(file_name, is_read ? O_RDONLY : O_RDWR);
            if (fd < 0) {
                perror("Failed to open file");
                exit(EXIT_FAILURE);
            }

            // Memory-map the file
            void *mapped = mmap(NULL, FILE_SIZE_MB * 1024 * 1024, PROT_READ | (is_read ? 0 : PROT_WRITE), MAP_SHARED, fd, 0);
            if (mapped == MAP_FAILED) {
                perror("Failed to mmap file");
                close(fd);
                exit(EXIT_FAILURE);
            }

            // Perform the read or write operation
            if (is_read) {
                volatile char tmp;
                size_t offset = rand() % ((FILE_SIZE_MB * 1024 * 1024) - BLOCK_SIZE);
                for (size_t i = 0; i < BLOCK_SIZE; i++) {
                    tmp = ((char *)mapped)[offset + i]; // Simulate read
                }
            } else {
                size_t offset = rand() % ((FILE_SIZE_MB * 1024 * 1024) - BLOCK_SIZE);
                for (size_t i = 0; i < BLOCK_SIZE; i++) {
                    ((char *)mapped)[offset + i] = rand() % 256; // Simulate write
                }
            }

            // Unmap the memory
            if (munmap(mapped, FILE_SIZE_MB * 1024 * 1024) < 0) {
                perror("Failed to unmap memory");
                close(fd);
                exit(EXIT_FAILURE);
            }

            close(fd);
        }

        long long end_time = get_time_in_ns();
        long long latency = (end_time - start_time);
        printf("Iteration %d latency: %.2f ms\n", iteration + 1, latency / 1e6);
        total_latency += latency;
    }

    return total_latency / NUM_ITERATIONS;
}

int main() {
    printf("Generating files...\n");
    // generate_files();
    sleep(20);
    double avg_latency = simulate_workload(2);
    printf("Starting workload simulation...\n");
    avg_latency = simulate_workload(NUM_ITERATIONS);
    printf("Average latency over %d iterations: %.5f ms\n", NUM_ITERATIONS, avg_latency / 1e6);

    return 0;
}
