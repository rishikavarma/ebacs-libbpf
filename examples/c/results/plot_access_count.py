import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Function to read access counts from a file
def read_access_counts(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return [int(line.split()[2]) for line in lines]

# Function to calculate and plot the graph
import numpy as np
import matplotlib.pyplot as plt

def plot_cdf(data, name, title="Cumulative Distribution Function (CDF)", xlabel="Data Values", ylabel="Cumulative Probability"):
    """
    Plots the Cumulative Distribution Function (CDF) of the given data.
    
    Parameters:
    - data: array-like, the dataset to compute the CDF for
    - title: str, title of the plot (default: "Cumulative Distribution Function (CDF)")
    - xlabel: str, label for the x-axis (default: "Data Values")
    - ylabel: str, label for the y-axis (default: "Cumulative Probability")
    """
    # Sort the data
    sorted_data = np.sort(data)

    # Calculate the cumulative probabilities
    cumulative_prob = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

    # Plot the CDF
    plt.figure(figsize=(8, 5))
    plt.plot(sorted_data, cumulative_prob, linestyle='-.', linewidth=2, label='CDF')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid()
    plt.legend()
    plt.savefig(name)

# Example usage
# data = np.random.randn(1000)  # Replace with your dataset
# plot_cdf(data)

def plot_kde(data, name, title="Page Access Count Density", threshold_percent = 0.9):
    
    max_value = max(data)
    threshold = threshold_percent * max_value
    
    # Filter data to include only values within threshold
    adjusted_data = [x for x in data if x <= threshold]
    # data = adjusted_data
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    sns.kdeplot(data=data, shade=True, color='blue', linewidth=2)
    
    # Customize the plot
    plt.xlabel('Page Access Counts')
    plt.ylabel('Density')
    plt.title(title)
    plt.grid(True)
    
    # Show the plot
    plt.savefig(name)

# For a combined histogram and KDE plot, use this alternative function:
def plot_hist_kde(data, name):
    
    plt.figure(figsize=(10, 6))
    sns.histplot(data=data, kde=True, stat='density')
    plt.xlabel('Data Values')
    plt.ylabel('Density')
    plt.title('Distribution with Density Curve')
    plt.grid(True)
    plt.savefig(name)


# Main script
if __name__ == "__main__":
    # Replace 'data.txt' with the path to your file
    file_path = './../lru_metrics_ran/time_128'
    access_counts = read_access_counts(file_path)
    plot_kde(access_counts, "ran_cdf.png", title = "Page Access Count Density(Uniform)")
    
    file_path = './../lru_metrics_hs/time_128'
    access_counts = read_access_counts(file_path)
    plot_kde(access_counts, "hs_cdf.png", title = "Page Access Count Density(Hotspots)")
