#!/bin/bash

# Ensure the script exits on error
set -e

# Delete all .dat files in the current directory
echo "Deleting all .dat files in the current directory..."
find . -maxdepth 1 -type f -name "*.dat" -exec rm -f {} \;

# Delete all files in the lru_metrics subdirectory
if [ -d "./lru_metrics" ]; then
    echo "Deleting all files in the lru_metrics subdirectory..."
    rm -rf ./lru_metrics/*
    rm ./vm_files/pids.txt
else
    echo "Directory 'lru_metrics' does not exist."
fi

echo "Cleanup completed!"
