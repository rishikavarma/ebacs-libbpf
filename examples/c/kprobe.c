// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
/* Copyright (c) 2021 Sartura
 * Based on minimal.c by Facebook */

#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <errno.h>
#include <sys/resource.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include "kprobe.skel.h"

static int libbpf_print_fn(enum libbpf_print_level level, const char *format, va_list args)
{
	return vfprintf(stderr, format, args);
}

static volatile sig_atomic_t stop;

static void sig_int(int signo)
{
	stop = 1;
}

struct page_key {
    struct address_space *mapping; // Mapping address
    unsigned long index; // Index within the mapping
	pid_t pid;
};

struct metric {
	uint64_t ref_count;
	uint64_t rank;
};

void concatenate_string_and_integer(const char *str, int num, char *result, size_t result_size) {
    char num_str[20]; // Buffer to hold the string representation of the integer

    snprintf(num_str, sizeof(num_str), "%d", num);

    // Check if the concatenation fits within the result buffer
    if (strlen(str) + strlen(num_str) + 1 > result_size) {
        fprintf(stderr, "Error: Result buffer is too small.\n");
        exit(EXIT_FAILURE);
    }

    // Concatenate the string and the integer string
    snprintf(result, result_size, "%s%s", str, num_str);
}

int main(int argc, char **argv)
{
	struct kprobe_bpf *skel;
	int err;

	int n;

	printf("Enter number of applications: ");

	if (scanf("%d", &n) != 1 || n <= 0) {
        printf("Invalid input! Please enter a positive integer.\n");
        return 1;  // Exit with error
    }

	int *array = malloc(n * sizeof(int));

	printf("Enter %d integers:\n", n);
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &array[i]) != 1) {
            printf("Invalid input! Please enter an integer.\n");
            free(array);
            return 1;  // Exit with error
        }
    }
	
	/* Set up libbpf errors and debug info callback */
	libbpf_set_print(libbpf_print_fn);

	/* Open load and verify BPF application */
	skel = kprobe_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open BPF skeleton\n");
		return 1;
	}

	/* Attach tracepoint handler */
	err = kprobe_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF skeleton\n");
		goto cleanup;
	}

	if (signal(SIGINT, sig_int) == SIG_ERR) {
		fprintf(stderr, "can't set signal handler: %s\n", strerror(errno));
		goto cleanup;
	}

	for (int i = 0; i < n; i++) {
		pid_t pid = (pid_t) array[i];
		uint8_t dummy = 1;
		if (bpf_map__update_elem(skel->maps.pid_map,  &pid, sizeof(pid), &dummy,
					sizeof(dummy), BPF_ANY) == 0) {
						
			printf("Added %d\n", array[i]);
		} else {
			perror("Failed to add pid");
		}
	}

	printf("Successfully started! Please run `sudo cat /sys/kernel/debug/tracing/trace_pipe` "
	       "to see output of the BPF programs.\n");

	// while (!stop) {
	// 	fprintf(stderr, ".");
	// 	sleep(1);
	// }

    struct page_key key, next_key;
    struct metric value;
	FILE *file;
	char path[30] = "./lru_metrics/time_";
	int i = 0;
	while(1){
		memset(&key, 0, sizeof(key));
		char result[30];
		// Open the file in append mode
		concatenate_string_and_integer(path, i, result, sizeof(result));
        file = fopen(result, "w");
        if (file == NULL) {
            perror("Failed to open file");
            return 1;
        }

		while (bpf_map__get_next_key(skel->maps.page_access_map, &key, &next_key, sizeof(struct page_key)) == 0) {
			// Lookup value for the current key
			if (bpf_map__lookup_elem(skel->maps.page_access_map,  &next_key, sizeof(next_key), &value,
					sizeof(value), BPF_ANY) == 0) {
						
				fprintf(file,"%ld %d %ld\n", next_key.index, next_key.pid, value.ref_count);
				// fprintf(file,"Key: {index: %ld} {pid: %d}, Value: %ld, %ld\n", next_key.index, next_key.pid, value.ref_count, value.rank);
			} else {
				perror("Failed to lookup map element");
			}
			key = next_key;
		}
		usleep(500000);
		i++;
		fclose(file); // Close the file after writing
	}

	

cleanup:
	kprobe_bpf__destroy(skel);
	return -err;
}
