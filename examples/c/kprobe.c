// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
/* Copyright (c) 2021 Sartura
 * Based on minimal.c by Facebook */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <errno.h>
#include <sys/resource.h>
#include <bpf/libbpf.h>
#include <stdint.h>   // For uint64_t
#include <inttypes.h> // For PRIx64
#include <pthread.h>
#include "kprobe.skel.h"

// Function for libbpf debugging output
static int libbpf_print_fn(enum libbpf_print_level level, const char *format, va_list args) {
    return vfprintf(stderr, format, args);
}

// Signal handling for stopping the program
static volatile sig_atomic_t stop;
static void sig_int(int signo) {
    stop = 1;
}

// Data structures for keys and values
struct page_key {
    struct address_space *mapping; // Mapping address
    unsigned long index;           // Index within the mapping
};

struct metric {
    uint64_t ref_count;
    uint64_t rank;
    uint64_t page_count;
    pid_t pid;                     // Process ID
};

struct thread_data {
    struct kprobe_bpf *skel;
};

// Concatenate a string and an integer
void concatenate_string_and_integer(const char *str, int num, char *result, size_t result_size) {
    char num_str[20];
    snprintf(num_str, sizeof(num_str), "%d", num);
    if (strlen(str) + strlen(num_str) + 1 > result_size) {
        fprintf(stderr, "Error: Result buffer is too small.\n");
        exit(EXIT_FAILURE);
    }
    snprintf(result, result_size, "%s%s", str, num_str);
}

// Hash function for combining `index` and `mapping`
uint64_t hash_index_mapping(unsigned long index, struct address_space *mapping) {
    return ((uint64_t)index ^ (uint64_t)(uintptr_t)mapping);
}

void* pid_receiver(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    struct kprobe_bpf *skel = data->skel;
    const char *pid_file = "./vm_files/pids.txt";
    FILE *file;
    char line[256];
    long file_pos = 0;

    printf("PID receiver thread started. Monitoring for new PIDs\n");
    
    while (!stop) {
        file = fopen(pid_file, "r");
        if (!file) {
            usleep(100000);  // Wait before retry if file doesn't exist
            continue;
        }

        // Seek to the last position we read
        fseek(file, file_pos, SEEK_SET);

        // Read any new lines that were added
        while (fgets(line, sizeof(line), file)) {
            pid_t pid;
            if (sscanf(line, "%d", &pid) == 1) {
                uint8_t dummy = 1;
                if (bpf_map__update_elem(skel->maps.pid_map, &pid, sizeof(pid), &dummy,
                                        sizeof(dummy), BPF_ANY) == 0) {
                    printf("Added PID %d\n", pid);
                } else {
                    perror("Failed to add PID");
                }
            }
        }

        // Save current position for next iteration
        file_pos = ftell(file);
        fclose(file);
        
        // Small sleep to prevent CPU hogging
        usleep(100000);
    }
    return NULL;
}



int main(int argc, char **argv) {
    struct kprobe_bpf *skel;
    int err;
    pthread_t pid_thread;
    struct thread_data thread_data;

    // printf("Enter number of applications: ");
    // if (scanf("%d", &n) != 1 || n <= 0) {
    //     printf("Invalid input! Please enter a positive integer.\n");
    //     return 1;
    // }

    // int *array = malloc(n * sizeof(int));
    // if (!array) {
    //     perror("Failed to allocate memory for array");
    //     return 1;
    // }

    // printf("Enter %d integers:\n", n);
    // for (int i = 0; i < n; i++) {
    //     if (scanf("%d", &array[i]) != 1) {
    //         printf("Invalid input! Please enter an integer.\n");
    //         free(array);
    //         return 1;
    //     }
    // }

    // Set up libbpf errors and debug info callback
    libbpf_set_print(libbpf_print_fn);

    // Open, load, and verify the BPF application
    skel = kprobe_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }

    // Attach the BPF skeleton
    err = kprobe_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF skeleton\n");
        goto cleanup;
    }

    if (signal(SIGINT, sig_int) == SIG_ERR) {
        fprintf(stderr, "Can't set signal handler: %s\n", strerror(errno));
        goto cleanup;
    }

    // for (int i = 0; i < n; i++) {
    //     pid_t pid = (pid_t)array[i];
    //     uint8_t dummy = 1;
    //     if (bpf_map__update_elem(skel->maps.pid_map, &pid, sizeof(pid), &dummy,
    //                              sizeof(dummy), BPF_ANY) == 0) {
    //         printf("Added PID %d\n", array[i]);
    //     } else {
    //         perror("Failed to add PID");
    //     }
    // }

    printf("Successfully started! Please run `sudo cat /sys/kernel/debug/tracing/trace_pipe` "
           "to see output of the BPF programs.\n");

    struct page_key key, next_key;
    struct metric value;
    FILE *file;
    char path[30] = "./lru_metrics/time_";
    int i = 0;

    thread_data.skel = skel;

    // Create threads
    if (pthread_create(&pid_thread, NULL, pid_receiver, &thread_data) != 0) {
        fprintf(stderr, "Failed to create PID receiver thread\n");
        goto cleanup;
    }

    while (!stop) {
        memset(&key, 0, sizeof(key));
        char result[30];
        concatenate_string_and_integer(path, i, result, sizeof(result));

        // Open the file in append mode
        file = fopen(result, "w");
        if (file == NULL) {
            perror("Failed to open file");
            // free(array);
            return 1;
        }

        // Iterate through the BPF map
        while (bpf_map__get_next_key(skel->maps.page_access_map, &key, &next_key, sizeof(struct page_key)) == 0) {
            // Lookup value for the current key
            if (bpf_map__lookup_elem(skel->maps.page_access_map, &next_key, sizeof(next_key), &value,
                                     sizeof(value), BPF_ANY) == 0) {
                // Calculate hash of index and mapping
                uint64_t hash = hash_index_mapping(next_key.index, next_key.mapping);

                // Write hash, PID, and ref_count to the file
                fprintf(file, "%" PRIx64 " %d %ld \n", hash, value.pid, value.ref_count);
            } else {
                perror("Failed to lookup map element");
            }
            key = next_key;
        }

        usleep(500000); // Sleep for 500ms
        i++;
        fclose(file); // Close the file after writing
    }
    pthread_join(pid_thread, NULL);
cleanup:
    kprobe_bpf__destroy(skel);
    // free(array);
    return -err;
}
