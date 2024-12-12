#!/bin/bash

# Navigate to the parent directory
cd ..

# Activate the Python environment
source myenv/bin/activate

# Run the Python telemetry script
python3 tel_wsf.py ./lru_metrics &

# Navigate back to the 'vm_files' directory
cd vm_files

run_fio_with_pids() {
    local fio_command="$1" # Accept fio command as an argument

    # Run fio in the background and capture its PID
    $fio_command --output=fio_output.log &
    fio_pid=$!

    # Wait a moment for fio to start all jobs
    sleep 2

    # Capture PIDs of fio child processes
    fio_child_pids=$(pgrep -P $fio_pid)

    # Print or save the PIDs
    echo "FIO Main PID: $fio_pid"
    echo "$fio_pid" >> pids.txt
    echo "$fio_pid" > current_pids.txt
    echo "FIO Child PIDs: $fio_child_pids"
    echo "$fio_child_pids" >> pids.txt
    echo "$fio_child_pids" >> current_pids.txt

    # Wait for fio to complete
    wait $fio_pid

    # After completion
    echo "FIO jobs have completed."
}

# Example usage:
echo "" > pids.txt
run_fio_with_pids "fio workload_ran.fio"
# run_fio_with_pids "fio workload_med.fio"
run_fio_with_pids "fio workload_hs.fio"
run_fio_with_pids "fio workload_hs_high.fio"
# To run another command, just call the function with a different argument:
# run_fio_with_pids "fio workload_hs.fio"

python3 