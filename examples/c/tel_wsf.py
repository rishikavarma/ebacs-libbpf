import os
import time
import sys
import numpy as np


def get_memory_stats():
    """Fetches memory stats from /proc/meminfo and calculates memory usage."""
    mem_info = {}
    try:
        with open('/proc/meminfo', 'r') as meminfo:
            for line in meminfo:
                key, value = line.split(':')
                mem_info[key.strip()] = int(value.split()[0])  # Value in kB
    except FileNotFoundError:
        print("Error: /proc/meminfo not found. Cannot fetch memory stats.")
        return 0, 0

    total_memory_kb = mem_info.get("MemTotal", 0)
    free_memory_kb = mem_info.get("MemAvailable", 0)

    # Convert kB to pages (assuming 4KB pages)
    total_pages = total_memory_kb // 4
    free_pages = free_memory_kb // 4
    return free_pages, total_pages


def calculate_dynamic_buckets(max_scale_factor):
    """Generates dynamic bucket thresholds starting from 0.3."""
    bucket_ranges = np.linspace(10, max_scale_factor, num=8)[1:]  # Exclude the first (0)
    return bucket_ranges

def update_kernel_watermark_scale_factor(scale_factor, log_file, start_time):
    """
    Updates the kernel's watermark scale factor and logs the update to a file with elapsed time.
    Args:
        scale_factor (int): The scale factor to set.
        log_file (str): Path to the log file for recording updates.
        start_time (float): The program's start time in seconds since the epoch.
    """
    scale_factor = max(10, min(scale_factor, 1000))  # Ensure scale factor is within bounds

    # try:
    #     with open('/proc/sys/vm/watermark_scale_factor', 'w') as wsf:
    #         wsf.write(str(scale_factor))
    #     print(f"Kernel watermark scale factor updated to: {scale_factor}")
    # except PermissionError:
    #     print("Permission denied: Unable to update kernel watermark scale factor. Run as root.")

    # Calculate elapsed time
    elapsed_time = time.time() - start_time

    # Log the update
    with open(log_file, 'a') as log:
        log.write(f"{elapsed_time:.2f}, {scale_factor}\n")


def process_logs(directory, log_file):
    """Processes log files to adjust the kernel watermark scale factor."""
    watermark_scale_factor = 10  # Initial scale factor
    start_time = time.time()

    print(f"Monitoring directory '{directory}' for logs...")
    while True:
        free_pages, total_pages = get_memory_stats()

        if total_pages == 0:
            print("Error: Could not retrieve memory stats. Exiting.")
            break

        free_pages = 0.03*free_pages
        used_memory_ratio = 1 - (free_pages / total_pages)
        print(f"Used Memory Ratio: {used_memory_ratio:.2f}")

        if used_memory_ratio > 0.95:
            utilization_above_threshold = used_memory_ratio - 0.95
            max_scale_factor = int(10 + (990 * (utilization_above_threshold / 0.05)))
        else:
            max_scale_factor = 10  # Minimal scale factor when memory usage is under 95%

        print(f"Max Scale Factor: {max_scale_factor}")

        bucket_thresholds = calculate_dynamic_buckets(max_scale_factor)

        log_files = [f for f in os.listdir(directory) if f.startswith("time_")]
        log_files.sort(key=lambda x: int(x.split('_')[-1]))

        if len(log_files) < 2:
            time.sleep(0.5)
            continue

        current_file = os.path.join(directory, log_files[-2])
        print(f"Processing file: {current_file}")

        access_counts = []
        with open(current_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue
                _, _, access_count = parts
                access_count = int(access_count)
                if access_count < 1000:
                    access_counts.append(access_count)

        if not access_counts:
            # print(f"No valid access counts in {current_file}. Skipping...")
            continue

        # Calculate and print the standard deviation
        # std_deviation = np.std(access_counts)
        # print(f"Standard Deviation of Access Counts: {std_deviation:.2f}")

        total_accesses = sum(access_counts)
        cumulative_sum = 0
        split_index = 0

        for i, count in enumerate(sorted(access_counts, reverse=True)):
            cumulative_sum += count
            if cumulative_sum >= 0.7 * total_accesses:
                split_index = i
                break

        working_set_split = (split_index + 1) / len(access_counts)
        working_set_split = 1 - working_set_split
        print(f"Working Set Split: {working_set_split:.2f}")


        for i, threshold in enumerate(bucket_thresholds):
            bucket_start = 0.3 + i * 0.1
            bucket_end = bucket_start + 0.1
            if bucket_start <= working_set_split < bucket_end:
                watermark_scale_factor = int(threshold)
                break

        print(f"Watermark Scale Factor: {watermark_scale_factor}")
        update_kernel_watermark_scale_factor(watermark_scale_factor, log_file, start_time)

        time.sleep(0.5)  # Check for new files every 1 second



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_directory>")
        sys.exit(1)

    log_directory = sys.argv[1]

    # Ensure the directory exists
    if not os.path.exists(log_directory):
        print(f"Error: Directory '{log_directory}' does not exist.")
        sys.exit(1)

    # Log file for watermark scale factor updates
    wm_log_file = os.path.join(os.path.dirname(__file__), "watermark_scale_factor.log")

    with open(wm_log_file, 'w') as log:
        log.write("Time, Watermark_scale Factor\n")

    # Start processing logs
    process_logs(log_directory, wm_log_file)

# import os
# import time
# import sys
# import numpy as np


# def update_kernel_watermark_scale_factor(scale_factor, log_file, start_time):
#     """
#     Updates the kernel's watermark scale factor and logs the update to a file with elapsed time.
#     Args:
#         scale_factor (int): The scale factor to set.
#         log_file (str): Path to the log file for recording updates.
#         start_time (float): The program's start time in seconds since the epoch.
#     """
#     scale_factor = max(10, min(scale_factor, 1000))  # Ensure scale factor is within bounds

#     # try:
#     #     with open('/proc/sys/vm/watermark_scale_factor', 'w') as wsf:
#     #         wsf.write(str(scale_factor))
#     #     print(f"Kernel watermark scale factor updated to: {scale_factor}")
#     # except PermissionError:
#     #     print("Permission denied: Unable to update kernel watermark scale factor. Run as root.")

#     # Calculate elapsed time
#     elapsed_time = time.time() - start_time

#     # Log the update
#     with open(log_file, 'a') as log:
#         log.write(f"Time: {elapsed_time:.2f}s, Watermark Scale Factor: {scale_factor}\n")

# def calculate_dynamic_buckets(min_scale_factor, max_scale_factor, num_buckets):
#     """
#     Calculates dynamic bucket thresholds for the watermark scale factor.

#     Parameters:
#     - min_scale_factor (int): The minimum scale factor.
#     - max_scale_factor (int): The maximum scale factor.
#     - num_buckets (int): The number of buckets.

#     Returns:
#     - list: A list of scale factors representing the bucket thresholds.
#     """
#     if num_buckets < 1:
#         raise ValueError("Number of buckets must be at least 1.")

#     step = (max_scale_factor - min_scale_factor) / (num_buckets - 1)
#     return [int(min_scale_factor + i * step) for i in range(num_buckets)]

# def get_memory_stats():
#     """Retrieves the number of free and total pages from /proc/meminfo."""
#     free_pages = 0
#     total_pages = 0
#     page_size_kb = os.sysconf('SC_PAGE_SIZE') // 1024  # Page size in KB

#     with open('/proc/meminfo', 'r') as meminfo:
#         for line in meminfo:
#             if line.startswith('MemFree:'):
#                 free_kb = int(line.split()[1])
#                 free_pages = free_kb // page_size_kb
#             elif line.startswith('MemTotal:'):
#                 total_kb = int(line.split()[1])
#                 total_pages = total_kb // page_size_kb

#     return free_pages, total_pages

# def get_bucket_index(value, thresholds):
#     """
#     Determines the index of the bucket for a given value based on thresholds.

#     Parameters:
#     - value (float): The value to categorize into a bucket.
#     - thresholds (list or np.ndarray): The boundaries of the buckets.

#     Returns:
#     - int: The index of the bucket in which the value falls.
#     """
#     for i, threshold in enumerate(thresholds):
#         if value <= threshold:
#             return i
#     return len(thresholds) - 1  # If value exceeds all thresholds, return the last bucket


# def process_logs(directory, log_file):
#     """
#     Processes log files to adjust the kernel watermark scale factor based on memory usage and page access patterns.
#     Args:
#         directory (str): Directory containing log files.
#         log_file (str): Path to the log file for recording updates.
#     """
#     print(f"Monitoring directory '{directory}' for logs...")

#     # Track start time
#     start_time = time.time()

#     while True:
#         # Get memory stats
#         free_pages, total_pages = get_memory_stats()
#         if total_pages == 0:
#             print("Error: Could not retrieve memory stats. Exiting.")
#             break
    
#         free_pages = 0.1*free_pages # assuming high load in background
#         used_memory_ratio = 1 - (free_pages / total_pages)

#         print(f"Used Memory Ratio: {used_memory_ratio:.2f}")
#         # print(f"Free Pages: {free_pages}, Total Pages: {total_pages}")

#         # Only apply watermark scale factor when memory usage exceeds 95%
#         if used_memory_ratio > 0.95:
#             utilization_above_threshold = used_memory_ratio - 0.95
#             max_scale_factor = int(10 + (990 * (utilization_above_threshold / 0.05)))
#         else:
#             max_scale_factor = 10  # Minimal scale factor when memory usage is under 95%

#         print(f"Max Scale Factor: {max_scale_factor}")

#         # Simulate processing a log file
#         log_files = [f for f in os.listdir(directory) if f.startswith("time_")]
#         log_files.sort(key=lambda x: int(x.split('_')[-1]))  # Sort by numerical suffix

#         if len(log_files) < 2:
#             time.sleep(0.5)  # Wait for more files
#             continue

#         current_file = os.path.join(directory, log_files[-2])
#         print(f"Processing file: {current_file}")

#         access_counts = []
#         with open(current_file, 'r') as f:
#             for line in f:
#                 parts = line.strip().split()
#                 if len(parts) != 3:
#                     continue
#                 _, _, access_count = parts
#                 access_count = int(access_count)
#                 # if access_count <= 4000:  # Discard access counts > 4000
#                 access_counts.append(access_count)

#         if not access_counts:
#             continue

#         # Calculate and normalize the standard deviation
#         mean_access_count = np.mean(access_counts)
#         std_deviation = np.std(access_counts)
#         if mean_access_count > 0:
#             normalized_std_dev = std_deviation / mean_access_count
#         else:
#             normalized_std_dev = 0  # Avoid division by zero

#         # print(f"Standard Deviation of Access Counts: {std_deviation:.2f}")
#         print(f"Normalized Standard Deviation: {normalized_std_dev:.2f}")

#         # Calculate bucket thresholds and determine bucket index
#         bucket_thresholds = calculate_dynamic_buckets(10, max_scale_factor, 10)
#         bucket_index = get_bucket_index(normalized_std_dev, np.linspace(0, 1, len(bucket_thresholds)))
#         watermark_scale_factor = int(bucket_thresholds[bucket_index])

#         print(f"Selected Watermark Scale Factor: {watermark_scale_factor}")

#         # Update the kernel with the new scale factor and log the update
#         update_kernel_watermark_scale_factor(watermark_scale_factor, log_file, start_time)

#         time.sleep(1)  # Check for new files every 1 second


# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python script.py <log_directory>")
#         sys.exit(1)

#     log_directory = sys.argv[1]

#     # Ensure the directory exists
#     if not os.path.exists(log_directory):
#         print(f"Error: Directory '{log_directory}' does not exist.")
#         sys.exit(1)

#     # Log file for watermark scale factor updates
#     wm_log_file = os.path.join(os.path.dirname(__file__), "watermark_scale_factor.log")

#     with open(wm_log_file, 'w') as log:
#         log.write("Time, Watermark Scale Factor\n")

#     # Start processing logs
#     process_logs(log_directory, wm_log_file)
