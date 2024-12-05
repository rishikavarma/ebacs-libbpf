#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/mman.h>  // For mmap
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <math.h>
#include <errno.h>
#include <stdbool.h>   // For bool type

#define FILE_SIZE_MB 1         // Size of each file (1 MB)
#define OLD_FILE_SIZE_MB 64
#define FILES_PER_ITERATION 20 // Number of files to create in each iteration
#define OLD_FILES 2       // Ratio of old files
#define BURSTS 60          // Number of iterations
#define ITERATIONS 20          // Number of iterations

long long get_time_in_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

// Function to generate random data
void generate_random_data(char *buffer, size_t size) {
    for (size_t i = 0; i < size; i++) {
        buffer[i] = rand() % 256;  // Random byte between 0 and 255
    }
}

void read_random_data(char *buffer, size_t size){
    char buffer2[size];
    for (size_t i = 0; i < size; i++) {
        buffer2[i] = buffer[i];
    }
}

int fds_old[OLD_FILES];
void *buffers_old[OLD_FILES];

// Function to process all files in one iteration
void generate_files(size_t file_size, bool old_visit) {
    int fds[FILES_PER_ITERATION];
    void *buffers[FILES_PER_ITERATION] = {NULL};

    // Create, open, and mmap all files
    for (int file_index = 0; file_index < FILES_PER_ITERATION; file_index++) {
        char filename[256];
        snprintf(filename, sizeof(filename), "file_%d.dat", file_index);
        

        // Create and open the file
        fds[file_index] = open(filename, O_RDWR | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
        if (fds[file_index] == -1) {
            perror("Failed to open file");
            continue;
        }

        // Set file size
        if (ftruncate(fds[file_index], file_size) == -1) {
            perror("Failed to set file size");
            close(fds[file_index]);
            fds[file_index] = -1;
            continue;
        }

        // Memory map the file
        buffers[file_index] = mmap(NULL, file_size, PROT_READ | PROT_WRITE, MAP_SHARED, fds[file_index], 0);
        if (buffers[file_index] == MAP_FAILED) {
            perror("Failed to map the file");
            close(fds[file_index]);
            fds[file_index] = -1;
            buffers[file_index] = NULL;
            continue;
        }

        // Write random data to the mapped memory
        generate_random_data((char *)buffers[file_index], file_size);

        if (old_visit) {
            for (int i = 0; i < OLD_FILES; i++){
                read_random_data((char *)buffers_old[i], file_size);
            }
        }
    }

    // Unmap and close all files
    
    for (int file_index = 0; file_index < FILES_PER_ITERATION; file_index++) {
        if (buffers[file_index] != NULL) {
            if (munmap(buffers[file_index], file_size) == -1) {
                    perror("Failed to unmap memory");
            }
        }
        if (fds[file_index] != -1) {
            close(fds[file_index]);

                // Delete the file
            char filename[256];
            snprintf(filename, sizeof(filename), "file_%d.dat", file_index);
            if (unlink(filename) == -1) {
                perror("Failed to delete file");
            }
        }
    }
    
}

void generate_old_files(){
    size_t file_size = OLD_FILE_SIZE_MB * 1024 * 1024;
    for (int file_index = 0; file_index < OLD_FILES; file_index++) {
        char filename[256];
        snprintf(filename, sizeof(filename), "file_old_%d.dat", file_index);
        // Create and open the file
        fds_old[file_index] = open(filename, O_RDWR | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
        if (fds_old[file_index] == -1) {
            perror("Failed to open file");
            continue;
        }

        // Set file size
        if (ftruncate(fds_old[file_index], file_size) == -1) {
            perror("Failed to set file size");
            close(fds_old[file_index]);
            fds_old[file_index] = -1;
            continue;
        }

        // Memory map the file
        buffers_old[file_index] = mmap(NULL, file_size, PROT_READ | PROT_WRITE, MAP_SHARED, fds_old[file_index], 0);
        if (buffers_old[file_index] == MAP_FAILED) {
            perror("Failed to map the file");
            close(fds_old[file_index]);
            fds_old[file_index] = -1;
            buffers_old[file_index] = NULL;
            continue;
        }

        // Write random data to the mapped memory
        generate_random_data((char *)buffers_old[file_index], file_size);
    }
}

void destroy_old_files(){
    size_t file_size = OLD_FILE_SIZE_MB * 1024 * 1024;
    for (int i = 0; i < OLD_FILES; i++) {
        if (buffers_old[i] != NULL) {
            if (munmap(buffers_old[i], file_size) == -1) {
                perror("Failed to unmap memory");
            }
        }
        if (fds_old[i] != -1) {
            close(fds_old[i]);

                // Delete the file
            char filename[256];
            snprintf(filename, sizeof(filename), "file_old_%d.dat", i);
            if (unlink(filename) == -1) {
                perror("Failed to delete file");
            }
        }
    }
}

long long calculate_average(long long *arr, int n) {
    long long sum = 0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum / n;
}

int main() {
    srand(time(NULL));  // Seed random number generator
    printf("Starting file generation...\n");

    size_t file_size = FILE_SIZE_MB * 1024 * 1024;
    long long latencies[ITERATIONS];

    for(int iteration=0; iteration< ITERATIONS; iteration++){
        long long start_time = get_time_in_ns();

        printf("Iteration %d...\n", iteration + 1);

        // generate_old_files();
        printf("Created old files...\n");

        // Perform iterations
        
        for (int burst = 0; burst < BURSTS; burst++) {
            // long long start_time = get_time_in_ns();
            generate_files(file_size, false);
            // long long end_time = get_time_in_ns();
            // sleep(1);  // Pause between iterations
        }

        // destroy_old_files(file_size);
        long long end_time = get_time_in_ns();
        long long latency_ns = end_time - start_time;
        double latency_ms = latency_ns / 1e6; // Convert to milliseconds
        printf("Total latency: %.2f ms\n", latency_ms);
        latencies[iteration] = latency_ns;
    }

    printf("File generation complete.\n");
    long long average = calculate_average(latencies, ITERATIONS) / 1e6;
    printf("Average: %lld ms\n", average);
    return 0;
}
