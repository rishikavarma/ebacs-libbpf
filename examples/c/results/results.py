import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_percentile(content, pattern):
    match = re.search(pattern, content, re.DOTALL)
    return float(match.group(1)) if match else 0

def parse_fio_logs(directory):
    data = {
        'swappiness': [],
        'read_iops': [],
        'read_bw': [],
        'write_iops': [],
        'write_bw': [],
        'read_lat_1': [],
        'read_lat_20': [],
        'read_lat_50': [],
        'read_lat_70': [],
        'read_lat_99': [],
        'write_lat_1': [],
        'write_lat_20': [],
        'write_lat_50': [],
        'write_lat_70': [],
        'write_lat_99': [],
        'cpu_usr': [],
        'cpu_sys': [],
        'cpu_ctx': [],
        'majf': [],
        'minf': []
    }
    
    for filename in os.listdir(directory):
        if not filename.startswith('swappiness_') or not filename.endswith('.log'):
            continue
            
        print(f"Processing {filename}")
        with open(os.path.join(directory, filename), 'r') as f:
            content = f.read()
            
        swappiness = int(re.search(r'swappiness_(\d+)', filename).group(1))
        
        # Basic metrics
        read_iops_match = re.search(r'read: IOPS=(\d+)k', content)
        read_bw_match = re.search(r'read: IOPS=\d+k, BW=(\d+)MiB/s', content)
        write_iops_match = re.search(r'write: IOPS=(\d+)k', content)
        write_bw_match = re.search(r'write: IOPS=\d+k, BW=(\d+)MiB/s', content)
        
        # CPU and Memory metrics
        cpu_match = re.search(r'cpu\s+: usr=(\d+\.\d+)%, sys=(\d+\.\d+)%, ctx=(\d+), majf=(\d+), minf=(\d+)', content)
        
        # Parse latency percentiles
        read_lat_patterns = {
            '1': r'read.*?clat percentiles.*?\n\s*\|\s*1\.00th=\[\s*(\d+)\]',
            '20': r'read.*?clat percentiles.*?20\.00th=\[\s*(\d+)\]',
            '50': r'read.*?clat percentiles.*?50\.00th=\[\s*(\d+)\]',
            '70': r'read.*?clat percentiles.*?70\.00th=\[\s*(\d+)\]',
            '99': r'read.*?clat percentiles.*?99\.00th=\[\s*(\d+)\]'
        }
        
        write_lat_patterns = {
            '1': r'write.*?clat percentiles.*?\n\s*\|\s*1\.00th=\[\s*(\d+)\]',
            '20': r'write.*?clat percentiles.*?20\.00th=\[\s*(\d+)\]',
            '50': r'write.*?clat percentiles.*?50\.00th=\[\s*(\d+)\]',
            '70': r'write.*?clat percentiles.*?70\.00th=\[\s*(\d+)\]',
            '99': r'write.*?clat percentiles.*?99\.00th=\[\s*(\d+)\]'
        }
        
        # Extract basic metrics
        data['swappiness'].append(swappiness)
        data['read_iops'].append(int(float(read_iops_match.group(1)) * 1000) if read_iops_match else 0)
        data['read_bw'].append(int(read_bw_match.group(1)) if read_bw_match else 0)
        data['write_iops'].append(int(float(write_iops_match.group(1)) * 1000) if write_iops_match else 0)
        data['write_bw'].append(int(write_bw_match.group(1)) if write_bw_match else 0)
        
        # Extract CPU and memory metrics
        if cpu_match:
            data['cpu_usr'].append(float(cpu_match.group(1)))
            data['cpu_sys'].append(float(cpu_match.group(2)))
            data['cpu_ctx'].append(int(cpu_match.group(3)))
            data['majf'].append(int(cpu_match.group(4)))
            data['minf'].append(int(cpu_match.group(5)))
        else:
            data['cpu_usr'].append(0)
            data['cpu_sys'].append(0)
            data['cpu_ctx'].append(0)
            data['majf'].append(0)
            data['minf'].append(0)
        
        # Extract latency percentiles
        for perc, pattern in read_lat_patterns.items():
            data[f'read_lat_{perc}'].append(parse_percentile(content, pattern))
        
        for perc, pattern in write_lat_patterns.items():
            data[f'write_lat_{perc}'].append(parse_percentile(content, pattern))
    
    return pd.DataFrame(data).sort_values('swappiness')

def plot_metrics(df):
    sns.set_style("whitegrid")
    sns.set_context("paper", font_scale=1.2)
    
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8)) = plt.subplots(4, 2, figsize=(15, 24))
    
    # Colors
    colors = ['#2ecc71', '#e74c3c']  # green, red
    percentile_colors = ['#3498db', '#f1c40f', '#e67e22', '#9b59b6', '#c0392b']
    
    # Plot IOPS
    ax1.plot(df['swappiness'], df['read_iops'], 'o-', label='Read IOPS', color=colors[0], linewidth=2, markersize=8)
    ax1.plot(df['swappiness'], df['write_iops'], 'o-', label='Write IOPS', color=colors[1], linewidth=2, markersize=8)
    ax1.set_title('IOPS vs Swappiness', fontsize=14, pad=20)
    ax1.set_xlabel('Swappiness Value', fontsize=12)
    ax1.set_ylabel('IOPS', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Plot Bandwidth
    ax2.plot(df['swappiness'], df['read_bw'], 'o-', label='Read Bandwidth', color=colors[0], linewidth=2, markersize=8)
    ax2.plot(df['swappiness'], df['write_bw'], 'o-', label='Write Bandwidth', color=colors[1], linewidth=2, markersize=8)
    ax2.set_title('Bandwidth vs Swappiness', fontsize=14, pad=20)
    ax2.set_xlabel('Swappiness Value', fontsize=12)
    ax2.set_ylabel('Bandwidth (MiB/s)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Plot Read Latencies
    percentiles = ['1', '20', '50', '70', '99']
    for i, perc in enumerate(percentiles):
        ax3.plot(df['swappiness'], df[f'read_lat_{perc}'], 'o-', 
                label=f'{perc}th percentile', 
                color=percentile_colors[i], 
                linewidth=2, 
                markersize=8)
    ax3.set_title('Read Latency Percentiles vs Swappiness', fontsize=14, pad=20)
    ax3.set_xlabel('Swappiness Value', fontsize=12)
    ax3.set_ylabel('Latency (ns)', fontsize=12)
    ax3.legend(fontsize=10)
    ax3.grid(True, linestyle='--', alpha=0.7)
    ax3.set_yscale('log')
    
    # Plot Write Latencies
    for i, perc in enumerate(percentiles):
        ax4.plot(df['swappiness'], df[f'write_lat_{perc}'], 'o-', 
                label=f'{perc}th percentile', 
                color=percentile_colors[i], 
                linewidth=2, 
                markersize=8)
    ax4.set_title('Write Latency Percentiles vs Swappiness', fontsize=14, pad=20)
    ax4.set_xlabel('Swappiness Value', fontsize=12)
    ax4.set_ylabel('Latency (ns)', fontsize=12)
    ax4.legend(fontsize=10)
    ax4.grid(True, linestyle='--', alpha=0.7)
    ax4.set_yscale('log')
    
    # Plot CPU Usage
    ax5.plot(df['swappiness'], df['cpu_usr'], 'o-', label='User CPU %', color='#3498db', linewidth=2, markersize=8)
    ax5.plot(df['swappiness'], df['cpu_sys'], 'o-', label='System CPU %', color='#e74c3c', linewidth=2, markersize=8)
    ax5.set_title('CPU Usage vs Swappiness', fontsize=14, pad=20)
    ax5.set_xlabel('Swappiness Value', fontsize=12)
    ax5.set_ylabel('CPU Usage (%)', fontsize=12)
    ax5.legend(fontsize=10)
    ax5.grid(True, linestyle='--', alpha=0.7)
    
    # Plot Context Switches
    ax6.plot(df['swappiness'], df['cpu_ctx'], 'o-', color='#2ecc71', linewidth=2, markersize=8)
    ax6.set_title('Context Switches vs Swappiness', fontsize=14, pad=20)
    ax6.set_xlabel('Swappiness Value', fontsize=12)
    ax6.set_ylabel('Context Switches', fontsize=12)
    ax6.grid(True, linestyle='--', alpha=0.7)
    
    # Plot Page Faults
    ax7.plot(df['swappiness'], df['majf'], 'o-', label='Major Faults', color='#e74c3c', linewidth=2, markersize=8)
    ax7.set_title('Major Page Faults vs Swappiness', fontsize=14, pad=20)
    ax7.set_xlabel('Swappiness Value', fontsize=12)
    ax7.set_ylabel('Major Faults', fontsize=12)
    ax7.grid(True, linestyle='--', alpha=0.7)
    
    ax8.plot(df['swappiness'], df['minf'], 'o-', label='Minor Faults', color='#3498db', linewidth=2, markersize=8)
    ax8.set_title('Minor Page Faults vs Swappiness', fontsize=14, pad=20)
    ax8.set_xlabel('Swappiness Value', fontsize=12)
    ax8.set_ylabel('Minor Faults', fontsize=12)
    ax8.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('fio_metrics_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_summary(df):
    print("\nSummary Statistics:")
    
    print("\nRead IOPS and Bandwidth:")
    print(df[['swappiness', 'read_iops', 'read_bw']].to_string(index=False))
    
    print("\nWrite IOPS and Bandwidth:")
    print(df[['swappiness', 'write_iops', 'write_bw']].to_string(index=False))
    
    print("\nRead Latency Percentiles (ns):")
    read_lat_cols = ['swappiness'] + [f'read_lat_{p}' for p in ['1', '20', '50', '70', '99']]
    print(df[read_lat_cols].to_string(index=False))
    
    print("\nWrite Latency Percentiles (ns):")
    write_lat_cols = ['swappiness'] + [f'write_lat_{p}' for p in ['1', '20', '50', '70', '99']]
    print(df[write_lat_cols].to_string(index=False))
    
    print("\nCPU and Memory Statistics:")
    print(df[['swappiness', 'cpu_usr', 'cpu_sys', 'cpu_ctx', 'majf', 'minf']].to_string(index=False))

if __name__ == "__main__":
    try:
        df = parse_fio_logs('seq_results')
        if len(df) == 0:
            print("No valid data found in the log files.")
        else:
            plot_metrics(df)
            print_summary(df)
    except Exception as e:
        print(f"An error occurred: {str(e)}")