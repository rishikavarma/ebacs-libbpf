#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

char LICENSE[] SEC("license") = "Dual BSD/GPL";

struct page_key {
    struct address_space *mapping; // Mapping address
    unsigned long index; // Index within the mapping
};

struct metric {
	u64 ref_count;
	u64 rank;
	u64 page_count;
	pid_t pid;
};

// Map to store page access counts
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, struct page_key); // Page address
    __type(value, struct metric);        // Access count
    __uint(max_entries,409600); // Max number of tracked pages
} page_access_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);  // Only one element to act as the static variable
    __type(key, __u32);      // Array index
    __type(value, __u64);    // Counter value
} static_counter SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 120);
    __type(key, pid_t);  // PID as the key
    __type(value, __u8); // Just a placeholder value (can use for flags)
} pid_map SEC(".maps");

SEC("kprobe/folio_mark_accessed")
int BPF_KPROBE(folio_mark_accessed, const struct folio *f1)
{
	pid_t pid;
	pid = bpf_get_current_pid_tgid() >> 32;

	__u32 rank_index = 0;  // Array index for the static variable
    __u64 *counter;
	__u8 *value;

    // Check if the PID exists in the hash map
    value = bpf_map_lookup_elem(&pid_map, &pid);
    if (!value) {
        // PID is not in the map;
        return 0;
    }


    // Get pointer to the counter value
    
	struct page_key key = {0};
	struct metric *access_count, new_count = {1, 0, 1, 0};
	key.mapping = BPF_CORE_READ(f1, mapping);
	key.index = BPF_CORE_READ(f1, index);
	__u64 page_count = BPF_CORE_READ(f1, _folio_nr_pages);
	new_count.page_count = page_count;
	new_count.pid = pid;

	// Look up the current access count
    access_count = bpf_map_lookup_elem(&page_access_map, &key);
    if (!access_count) {
		// Initialize the count to 1
		counter = bpf_map_lookup_elem(&static_counter, &rank_index);
		if (counter) {
			// Increment the counter
			(*counter)++;
			new_count.rank = *counter;
		}
		
		// new_count.page_count = BPF_CORE_READ(f1, _folio_nr_pages);
		
		bpf_map_update_elem(&page_access_map, &key, &new_count, BPF_ANY);
		// bpf_printk("KPROBE ENTRY pid = %d, access count = %ld, rank = %ld, page count = %ld\n", pid, new_count.ref_count, new_count.rank, new_count.page_count);
    } else {
        // Increment the existing count
        (access_count->ref_count)++;
		counter = bpf_map_lookup_elem(&static_counter, &rank_index);
		if (counter) {
			// Increment the counter
			(*counter)++;
			access_count->pid = pid;
			access_count->rank = *counter;
		}
		
		access_count->page_count = page_count;

        bpf_map_update_elem(&page_access_map, &key, access_count, BPF_ANY);
		// bpf_printk("KPROBE ENTRY pid = %d, access count = %ld, rank = %ld, page count = %ld\n", pid, access_count->ref_count, access_count->rank, access_count->page_count);
    }
	// struct page tmp_page = BPF_CORE_READ(f1, page);
	// unsigned int num_page = BPF_CORE_READ(f1, _folio_nr_pages);
	// bpf_printk("KPROBE ENTRY pid = %d, num_pages = %d, page count = %d\n", pid, num_page, f1._refcount);
	return 0;
}

// Deallocate -- 
// __folio_put(struct folio *folio)
SEC("kprobe/filemap_free_folio")
int BPF_KPROBE(filemap_free_folio, struct address_space *tmp_mapping, struct folio *f1)
{
	pid_t pid;
	pid = bpf_get_current_pid_tgid() >> 32;

	struct page_key key = {0};
	struct metric *access_count;

	key.mapping = tmp_mapping;
	key.index = BPF_CORE_READ(f1, index);

	// Look up the current access count
    access_count = bpf_map_lookup_elem(&page_access_map, &key);
    if (!access_count) {
		return 0;
    }
	bpf_printk("KPROBE ENTRY delete pid = %d, index = %ld\n", pid, key.index);
	// delete
	bpf_map_delete_elem(&page_access_map, &key);

	return 0;
}
