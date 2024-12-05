import re
import csv
import matplotlib.pyplot as plt
import pandas as pd

# File paths
input_file = "results_workload_hs.txt"  # Replace with your actual file path
output_csv = "parsed_latencies_hs.csv"

# # Initialize data storage
# data = []

# # Read the entire file
# with open(input_file, "r") as f:
#     content = f.read()

# # Split the file into chunks based on the delimiter
# chunks = content.split("----------------------------------")

# # Regular expressions to extract required information
# scale_factor_regex = re.compile(r"Running with water_mark_scale_factor=(\d+)")
# background_regex = re.compile(r"Dropped caches before fio \((\d+)% vm-bytes\)")
# allocstall_regex = re.compile(r"allocstall_movable\s+(\d+)")
# clat_percentiles_regex = re.compile(r"\|\s*([\d\.]+)th=\[\s*(\d+)]")

# current_sf = 0
# last_allocstall = 0
# for chunk in chunks:
#     lines = chunk.strip().split("\n")
#     if not lines:
#         continue  # Skip empty chunks

#     # Initialize variables for each chunk
#     scale_factor = None
#     background = None
#     allocstall_movable = None
#     read_percentiles = {}
#     write_percentiles = {}
#     current_section = None  # To track whether we're in read or write section

#     # Extract scale factor
#     for line in lines:
#         scale_match = scale_factor_regex.search(line)
#         if scale_match:
#             scale_factor = int(scale_match.group(1))
#             break  # Assuming scale factor appears once per chunk

#     # Extract background usage
#     for line in lines:
#         bg_match = background_regex.search(line)
#         if bg_match:
#             background = int(bg_match.group(1))
#             break  # Assuming background usage appears once per chunk

#     # Extract allocstall_movable
#     for line in lines:
#         allocstall_match = allocstall_regex.search(line)
#         if allocstall_match:
#             allocstall_movable = int(allocstall_match.group(1))
#             tmp = allocstall_movable
#             allocstall_movable = allocstall_movable - last_allocstall 
#             last_allocstall = tmp
#             break  # Assuming allocstall_movable appears once per chunk

#     if background is None:
#         continue  # Skip chunks that don't have necessary info

#     if scale_match is None:
#         scale_factor = current_sf
#     else:
#         current_sf = scale_factor

#     # Extract clat percentiles
#     for i, line in enumerate(lines):
#         if "read:" in line:
#             current_section = "read"
#         elif "write:" in line:
#             current_section = "write"
#         elif "clat percentiles (nsec):" in line:
#             # Get the 3rd and 4th lines after the current line, if they exist
#             p50_line = lines[i + 2] if i + 2 < len(lines) else ""
#             p99_line = lines[i + 4] if i + 4 < len(lines) else ""
            
#             # Regex to capture percentile values from the respective lines
#             p50_match = re.search(r"50\.00th=\[\s*(\d+)\]", p50_line)  # For 50th percentile
#             p99_match = re.search(r"99\.00th=\[\s*(\d+)\]", p99_line)

#             # Extract and store the percentile values
#             if p50_match:
#                 p50_value = int(p50_match.group(1))
#                 if current_section == "read":
#                     read_percentiles['50th'] = p50_value
#                 elif current_section == "write":
#                     write_percentiles['50th'] = p50_value

#             if p99_match:
#                 p99_value = int(p99_match.group(1))
#                 if current_section == "read":
#                     read_percentiles['99th'] = p99_value
#                 elif current_section == "write":
#                     write_percentiles['99th'] = p99_value

#     # Ensure that all required percentiles are found
#     if ('50th' in read_percentiles and '99th' in read_percentiles and
#         '50th' in write_percentiles and '99th' in write_percentiles):
#         data.append({
#             "scale_factor": scale_factor,
#             "background": background,
#             "allocstall_movable": allocstall_movable,
#             "read_50th": read_percentiles['50th'],
#             "read_99th": read_percentiles['99th'],
#             "write_50th": write_percentiles['50th'],
#             "write_99th": write_percentiles['99th']
#         })

# # Write the extracted data to a CSV file
# with open(output_csv, "w", newline="") as csvfile:
#     fieldnames = ["scale_factor", "background", "allocstall_movable", "read_50th", "read_99th", "write_50th", "write_99th"]
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#     writer.writeheader()
#     for row in data:
#         writer.writerow(row)

# print(f"Data successfully written to {output_csv}")

# Load data into a pandas DataFrame for easier manipulation
df = pd.read_csv(output_csv)

# Get unique background usages and scale factors
backgrounds = sorted(df['background'].unique())
scale_factors = sorted(df['scale_factor'].unique())

# Plotting for each background usage
for bg in backgrounds:
    bg_data = df[df['background'] == bg].sort_values('scale_factor')
    plt.figure(figsize=(10, 6))
    
    plt.plot(bg_data['scale_factor'], bg_data['read_50th'], marker='o', label='Read 50th Percentile')
    plt.plot(bg_data['scale_factor'], bg_data['read_99th'], marker='o', label='Read 99th Percentile')
    plt.plot(bg_data['scale_factor'], bg_data['write_50th'], marker='x', label='Write 50th Percentile')
    plt.plot(bg_data['scale_factor'], bg_data['write_99th'], marker='x', label='Write 99th Percentile')
    
    plt.title(f"Latency Percentiles for Background {bg}%")
    plt.xlabel("Watermark Scale Factor")
    plt.ylabel("Latency (nsec)")
    plt.legend()
    plt.grid(True)
    plt.xticks(scale_factors)  # Ensure all scale factors are shown on x-axis
    plt.savefig(f"latency_percentiles_bg_{bg}.png")

# Separate plot for allocstall_movable across different background values
plt.figure(figsize=(10, 6))
for bg in backgrounds:
    bg_data = df[df['background'] == bg]
    plt.plot(bg_data['scale_factor'], bg_data['allocstall_movable'], marker='o', label=f"Constant b/g load - {bg}%")

plt.title("Allocstalls for different Memory pressure (Hotspots)")
plt.xlabel("Watermark Scale Factor")
plt.ylabel("Allocstall Events")
plt.legend()
plt.grid(True)
plt.xticks(scale_factors)  # Ensure all scale factors are shown on x-axis
plt.savefig("allocstall_movable_plot.png")

print("Allocstall movable plot has been generated and saved as PNG.")
