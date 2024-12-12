#!/bin/bash

# Array of water_mark_scale_factor values
water_mark_scale_factors=(10 100 250 500 750 900 1000)

# Output file for overall results
overall_results="overall_results.txt"
echo "FIO Results and Allocstall Info" > "$overall_results"

# Function to run the experiment for a given fio workload
run_experiment() {
    local fio_workload=$1
    local results_file="results_${fio_workload%.fio}.txt"  # Unique file per workload
    echo "Running experiments with workload: $fio_workload" | tee -a "$overall_results"
    echo "Results for $fio_workload" > "$results_file"

    # Loop through each value in the array
    for scale_factor in "${water_mark_scale_factors[@]}"; do
        echo "Running with water_mark_scale_factor=$scale_factor" | tee -a "$results_file"
        
        # Set the water_mark_scale_factor
        sudo sysctl vm.watermark_scale_factor=$scale_factor
        cat /proc/sys/vm/watermark_scale_factor

        sleep 5
        # Drop caches before running fio
        sudo sysctl -w vm.drop_caches=3
        echo "Dropped caches before fio (90% vm-bytes)" | tee -a "$results_file"
        sleep 5
        
        # Run stress-ng with 90% vm-bytes
        nohup stress-ng --vm 8 --vm-bytes 90% --timeout 200s &
        stress_pid_90=$!
        
        # Run fio and wait for it to complete
        fio_output=$(fio "$fio_workload" 2>&1)
        echo "$fio_output" | tee -a "$results_file"
        
        # Kill stress-ng after fio completes
        sudo kill -9 $stress_pid_90 2>/dev/null || true
        echo "Killed stress-ng (90% vm-bytes) with PID: $stress_pid_90"
        
        # Capture allocstall info
        echo "Allocstall info after 90% vm-bytes:" | tee -a "$results_file"
        grep allocstall /proc/vmstat | tee -a "$results_file"
        echo -e "----------------------------------\n" >> "$results_file"

        sleep 5

        # Drop caches before running fio
        sysctl -w vm.drop_caches=3
        echo "Dropped caches before fio (99% vm-bytes)" | tee -a "$results_file"

        sleep 5
        
        # Run stress-ng with 99% vm-bytes
        nohup stress-ng --vm 8 --vm-bytes 99% --timeout 200s &
        stress_pid_99=$!
        echo "Started stress-ng (99% vm-bytes) with PID: $stress_pid_99"

        # Run fio and wait for it to complete
        fio_output=$(fio "$fio_workload" 2>&1)
        echo "$fio_output" | tee -a "$results_file"
        
        # Kill stress-ng after fio completes
        sudo kill -9 $stress_pid_99 2>/dev/null || true
        echo "Killed stress-ng (99% vm-bytes) with PID: $stress_pid_99"
        
        # Capture allocstall info
        echo "Allocstall info after 99% vm-bytes:" | tee -a "$results_file"
        grep allocstall /proc/vmstat | tee -a "$results_file"
        echo -e "----------------------------------\n" >> "$results_file"
    done

    # Append specific workload results to the overall results file
    cat "$results_file" >> "$overall_results"
}

# Run experiments for both workloads
run_experiment "workload_hs.fio"
run_experiment "workload_ran.fio"

echo "Script completed. Overall results saved to $overall_results."
