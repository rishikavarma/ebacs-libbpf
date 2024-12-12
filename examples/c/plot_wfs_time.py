import matplotlib.pyplot as plt
import pandas as pd

# Read the file and create a DataFrame
file_path = "watermark_scale_factor.log"
data = pd.read_csv(file_path)

# Clean column names to avoid issues with hidden spaces or formatting
data.columns = data.columns.str.strip()

# Calculate relative time
data['Relative Time'] = data['Time'] - data['Time'].iloc[0]

# Plot Watermark Scale Factor vs Relative Time
plt.figure(figsize=(10, 6))
plt.plot(data['Relative Time'], data['Watermark_scale_factor'], label='Watermark Scale Factor', color='blue')

# Highlight ranges with shading and add annotations
plt.axvspan(0, 2, color='blue', alpha=0.1, label="Initial Setup")
plt.axvspan(2, 12, color='green', alpha=0.1, label="Uniform Distribution")
plt.axvspan(12, 22, color='orange', alpha=0.1, label="80:20 Distribution")
plt.axvspan(22, 32, color='purple', alpha=0.1, label="90:10 Distribution")

# Add labels, title, and legend
plt.xlabel("Time (seconds)")
plt.ylabel("Watermark Scale Factor")
plt.title("Watermark Scale Factor vs Time for diff workloads")
plt.legend()
plt.grid(True)

# Show the plot
plt.tight_layout()
plt.savefig("wf_time.pdf")
print("Plotted Watermark Scale Factor (wf_time.pdf)")
