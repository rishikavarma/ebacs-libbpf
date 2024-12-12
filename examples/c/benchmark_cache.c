#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

#define FILE_NAME "example_file.txt"
#define BUFFER_SIZE 4096 // 4 KB
#define ITERATIONS 10000

int main() {
    char *buffer = malloc(BUFFER_SIZE);
    if (!buffer) {
        perror("Failed to allocate buffer");
        exit(EXIT_FAILURE);
    }

    // Initialize buffer with data
    memset(buffer, 'A', BUFFER_SIZE);

    // Open file for writing and reading
    int fd = open(FILE_NAME, O_RDWR | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
    if (fd == -1) {
        perror("Failed to open file");
        free(buffer);
        exit(EXIT_FAILURE);
    }

    // Write data into the file
    for (int i = 0; i < ITERATIONS; i++) {
        if (write(fd, buffer, BUFFER_SIZE) != BUFFER_SIZE) {
            perror("Failed to write to file");
            free(buffer);
            close(fd);
            exit(EXIT_FAILURE);
        }
    }

    // Reset file offset for reading
    lseek(fd, 0, SEEK_SET);

    // Read data from the file repeatedly
    for (int i = 0; i < ITERATIONS; i++) {
        if (read(fd, buffer, BUFFER_SIZE) != BUFFER_SIZE) {
            perror("Failed to read from file");
            free(buffer);
            close(fd);
            exit(EXIT_FAILURE);
        }
    }

    printf("File operations completed successfully.\n");

    // Cleanup
    free(buffer);
    close(fd);
    unlink(FILE_NAME); // Remove the file
    return 0;
}
