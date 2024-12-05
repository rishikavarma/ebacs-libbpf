import matplotlib.pyplot as plt
import numpy as np

# Function to read access counts from a file
def read_access_counts(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return [int(line.split()[2]) for line in lines]

# Function to calculate and plot the graph
def plot_80_20_graph(access_counts, name):
    # Sort access counts and their original indexes
    sorted_counts = sorted(enumerate(access_counts), key=lambda x: x[1], reverse=True)
    indexes, sorted_counts = zip(*sorted_counts)
    
    # Calculate cumulative distribution
    total_access = sum(sorted_counts)
    cumulative_access = np.cumsum(sorted_counts)
    cumulative_percentage = cumulative_access / total_access * 100
    
    # Find the threshold index for 80% access
    # threshold_index = next(i for i, percent in enumerate(cumulative_percentage) if percent >= 80)
    # threshold_percentage_indexes = (threshold_index + 1) / len(access_counts) * 100

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(sorted_counts)), cumulative_access, label="Cumulative Access Percentage", color="blue")
    # plt.axhline(y=80, color="red", linestyle="--", label="80% Access")
    # plt.axvline(x=threshold_index, color="green", linestyle="--", label=f"20% Indexes ({threshold_percentage_indexes:.1f}%)")
    plt.title("CDF of access counts")
    plt.xlabel("Indexes (Sorted by Access Counts)")
    plt.ylabel("CDF")
    plt.legend()
    plt.grid(axis="both", linestyle="--", alpha=0.7)
    plt.savefig(name)

# Main script
if __name__ == "__main__":
    # Replace 'data.txt' with the path to your file
    file_path = './../lru_metrics_ran/time_128'
    access_counts = read_access_counts(file_path)
    plot_80_20_graph(access_counts, "ran_cdf.png")
    
    file_path = './../lru_metrics_hs/time_128'
    access_counts = read_access_counts(file_path)
    plot_80_20_graph(access_counts, "hs_cdf.png")
