import os
import time
import sys
import numpy as np
from collections import defaultdict


def get_log_files(directory):
    """Returns a sorted list of log files in the directory."""
    files = [f for f in os.listdir(directory) if f.startswith("time_")]
    files.sort(key=lambda x: int(x.split('_')[-1]))  # Sort by numerical suffix
    return files


def calculate_percentile(data, percentile):
    """Calculates the given percentile for a list of numbers."""
    return np.percentile(data, percentile) if data else 0


def get_db_bench_pids():
    """Returns a set of PIDs running './db_bench'."""
    pids = set()
    proc_dir = '/proc'

    # Iterate through all /proc entries
    for pid in os.listdir(proc_dir):
        if not pid.isdigit():
            continue  # Skip non-numeric entries

        cmdline_path = os.path.join(proc_dir, pid, 'cmdline')
        try:
            with open(cmdline_path, 'r') as f:
                cmdline = f.read()
                if './leveldb_tests' in cmdline:
                    pids.add(int(pid))
        except (FileNotFoundError, PermissionError):
            continue  # Skip entries we cannot access

    return pids


def process_logs(directory):
    watermark_scale_factor = 10  # Initial scale factor
    previous_page_access_counts = defaultdict(dict)  # Per-PID page access counts
    last_processed_file = None  # Track the last processed file

    print(f"Monitoring directory '{directory}' for logs of './db_bench'...")
    while True:
        # Discover PIDs running './db_bench'
        tracked_pids = get_db_bench_pids()
        print(f"Discovered PIDs: {tracked_pids}")

        if not tracked_pids:
            print("No './db_bench' processes found. Retrying...")
            time.sleep(0.1)
            continue

        # Get the list of log files
        log_files = get_log_files(directory)
        if len(log_files) < 2:
            time.sleep(0.5)  # Wait for more files
            continue

        # Get the second-to-latest file
        current_file = os.path.join(directory, log_files[-2])

        # Skip if this file was already processed
        if current_file == last_processed_file:
            time.sleep(0.5)  # Wait for new files
            continue

        print(f"Processing file: {current_file}")
        current_page_access_counts = defaultdict(dict)

        with open(current_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue  # Skip malformed lines
                page_index, pid, access_count = parts
                pid = int(pid)
                access_count = int(access_count)

                if pid in tracked_pids:
                    # Update latest access count for each page per PID
                    current_page_access_counts[pid][page_index] = access_count

        # Analyze churn and metrics per PID
        for pid in tracked_pids:
            current_pages = set(current_page_access_counts[pid].keys())
            previous_pages = set(previous_page_access_counts[pid].keys())
            new_pages = current_pages - previous_pages

            churn = len(new_pages) / len(previous_pages) if previous_pages else 0
            print(f"PID {pid} - Churn: {churn:.2f}")

            if churn > 2:
                new_pages_access_counts = [
                    current_page_access_counts[pid][page] for page in new_pages
                ]
                repeated_pages_access_counts = [
                    current_page_access_counts[pid][page]
                    for page in current_pages if page in previous_pages
                ]

                # Calculate 80th percentiles
                new_pages_80th = calculate_percentile(new_pages_access_counts, 80)
                repeated_pages_80th = calculate_percentile(repeated_pages_access_counts, 80)

                if repeated_pages_80th > 0:
                    percentile_ratio = new_pages_80th / repeated_pages_80th
                    print(f"PID {pid} - 80th Percentile Ratio: {percentile_ratio:.2f}")

                    # Adjust watermark scale factor
                    if percentile_ratio > 1.2:
                        watermark_scale_factor *= 2
                    elif percentile_ratio < 0.8:
                        watermark_scale_factor *= 0.5

                    print(f"PID {pid} - Updated Watermark Scale Factor: {watermark_scale_factor:.2f}")

        # Update previous access counts
        previous_page_access_counts = current_page_access_counts
        last_processed_file = current_file  # Update the last processed file

        time.sleep(0.5)  # Check for new files every 0.5 seconds


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_directory>")
        sys.exit(1)

    log_directory = sys.argv[1]

    # Ensure the directory exists
    if not os.path.exists(log_directory):
        print(f"Error: Directory '{log_directory}' does not exist.")
        sys.exit(1)

    # Start processing logs for './db_bench' PIDs
    process_logs(log_directory)
