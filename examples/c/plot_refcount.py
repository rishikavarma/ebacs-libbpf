import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from matplotlib.colors import LinearSegmentedColormap

# Function to parse the output.txt file and process data
def parse_data(file_path):
    data = defaultdict(int)  # Dictionary to store the latest refcount for each (index, pid)

    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 3:
                continue  # Skip malformed lines
            
            index, pid, refcount = map(int, parts)
            key = (index, pid)
            data[key] = refcount  # Update with the latest refcount for this key

    return data

# Function to plot a histogram
def plot_histogram(data):
    refcounts = list(data.values())  # Extract only the refcounts

    # Define bins as powers of 2
    max_refcount = max(refcounts) if refcounts else 1
    max_power = int(np.ceil(np.log2(max_refcount)))  # Determine the largest power of 2 needed
    bins = [2**i for i in range(max_power + 1)]  # Include one more bin to cover all values

    # Define the color gradient (light blue to red)
    cmap = LinearSegmentedColormap.from_list("blue_to_red", ["lightblue", "red"])
    bin_colors = [cmap(i / (len(bins) - 1)) for i in range(len(bins) - 1)]

    # Plot histogram
    plt.figure(figsize=(12, 8))
    n, bins, patches = plt.hist(refcounts, bins=bins, edgecolor='black')

    # Apply color gradient to histogram bars
    for patch, color in zip(patches, bin_colors):
        patch.set_facecolor(color)

    # Customize x-axis with powers of 2 in superscript notation
    plt.xscale('log')
    plt.xticks(
        bins,
        [f"$2^{{{int(np.log2(b))}}}$" for b in bins],  # Superscript formatting for x-axis
        fontsize=16
    )

    # Set y-axis to log scale with base 2
    plt.yscale('log', base=2)
    y_ticks = [2**i for i in range(int(np.log2(max(n)) + 1))]  # Generate y-axis ticks as powers of 2
    plt.yticks(
        y_ticks,
        [f"$2^{{{int(np.log2(y))}}}$" for y in y_ticks],  # Superscript formatting for y-axis
        fontsize=16
    )

    # Labels and grid
    plt.title('Page Access Histogram', fontsize=24)
    plt.xlabel('Page Access Count', fontsize=22)
    plt.ylabel('Number of Pages', fontsize=22)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()  # Adjust layout to prevent overlaps
    plt.savefig("plot.pdf")

if __name__ == "__main__":
    file_path = "output.txt"  # Replace with the path to your file if different
    data = parse_data(file_path)
    plot_histogram(data)
