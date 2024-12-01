#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <sys/mman.h>  // For mmap
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#define ALLOCATION_SIZE_MB 64  // Size of each allocation burst (in MB)
#define NUM_ALLOCATION_BURSTS 50 // Number of bursts before deallocation
#define PAGE_SIZE 4096  // System page size (4 KB)
#define SLEEP_BETWEEN_BURSTS 1 // Sleep time between bursts (in seconds)

// Function to get current time in nanoseconds
long long get_time_in_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

// Function to touch memory pages to trigger faults
void touch_memory(void *addr, size_t size) {
    char *ptr = (char *)addr;
    for (size_t i = 0; i < size; i += PAGE_SIZE) {
        ptr[i] = (char)i;  // Write to each page to ensure it's marked as accessed
    }
}

void generate_random_data(char *buffer, size_t size) {
    for (size_t i = 0; i < size; i++) {
        buffer[i] = rand() % 256;  // Random byte between 0 and 255
    }
}

// Function to allocate memory and simulate workload
int bursty_memory_usage() {
    size_t allocation_size = ALLOCATION_SIZE_MB * 1024 * 1024;
    void **buffers = malloc(NUM_ALLOCATION_BURSTS * sizeof(void *));
    if (!buffers) {
        perror("malloc failed for buffer array");
        exit(EXIT_FAILURE);
    }

    int fd[NUM_ALLOCATION_BURSTS];

    for (int file_index = 0; file_index < NUM_ALLOCATION_BURSTS; file_index++) {
        char filename[256];
        snprintf(filename, sizeof(filename), "file_%d.dat", file_index);

        // Open the file
        fd[file_index] = open(filename, O_RDWR | O_CREAT, S_IRUSR | S_IWUSR);
        if (fd[file_index] == -1) {
            perror("Failed to open file");
            return 1;
        }

        // Ensure the file is at least 512 MB
        if (ftruncate(fd[file_index], allocation_size) == -1) {
            perror("Failed to set file size");
            close(fd[file_index]);
            return 1;
        }

        // Memory map the file
        buffers[file_index] = mmap(NULL, allocation_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd[file_index], 0);
        if (buffers[file_index] == MAP_FAILED) {
            perror("Failed to map the file");
            close(fd[file_index]);
            return 1;
        }

        // Write random data to the mapped memory
        generate_random_data((char *)buffers[file_index], allocation_size);

        // Optionally, print the first few bytes of the mapped region
        printf("Writing random data to %s...\n", filename);
        printf("First 10 bytes of the file '%s': ", filename);
        for (int i = 0; i < 10; i++) {
            printf("%02x ", ((unsigned char *)buffers[file_index])[i]);
        }
        printf("\n");

        // Unmap the memory
        

        // Close the file
        // close(fd);
        printf("File '%s' completed.\n\n", filename);
    }

    for(int i = 0; i < NUM_ALLOCATION_BURSTS; i++) {
        if (munmap(buffers[i], allocation_size) == -1) {
            perror("Failed to unmap memory");
            close(fd[i]);
            return 1;
        }

    }

    // for (int i = 0; i < NUM_ALLOCATION_BURSTS; i++) {
    //     printf("Burst %d/%d: Allocating %zu bytes using mmap...\n", i + 1, NUM_ALLOCATION_BURSTS, allocation_size);

    //     // Allocate memory with mmap
    //     void *buffer = mmap(NULL, allocation_size, PROT_READ | PROT_WRITE,
    //                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    //     if (buffer == MAP_FAILED) {
    //         perror("mmap failed");
    //         exit(EXIT_FAILURE);
    //     }
    //     buffers[i] = buffer;

    //     // Access the memory to trigger page faults
    //     touch_memory(buffer, allocation_size);

    //     printf("Memory accessed. Sleeping for %d seconds...\n", SLEEP_BETWEEN_BURSTS);
    //     usleep(SLEEP_BETWEEN_BURSTS * 1000000);  // Sleep to simulate bursty behavior
    // }

    // // Free memory after all bursts
    // printf("Releasing allocated memory...\n");
    // for (int i = 0; i < NUM_ALLOCATION_BURSTS; i++) {
    //     if (munmap(buffers[i], allocation_size) == -1) {
    //         perror("munmap failed");
    //     }
    // }

    free(buffers);
    // printf("Memory released successfully.\n");
}

int main() {
    printf("Starting bursty memory usage simulation...\n");
    bursty_memory_usage();
    printf("Simulation complete.\n");
    return 0;
}
