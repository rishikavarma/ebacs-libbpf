# Demo BPF applications

## Minimal

`minimal` is just that – a minimal practical BPF application example. It
doesn't use or require BPF CO-RE, so should run on quite old kernels. It
installs a tracepoint handler which is triggered once every second. It uses
`bpf_printk()` BPF helper to communicate with the world. To see it's output,
read `/sys/kernel/debug/tracing/trace_pipe` file as a root:

```shell
$ make minimal
$ sudo ./minimal
$ sudo cat /sys/kernel/debug/tracing/trace_pipe
           <...>-3840345 [010] d... 3220701.101143: bpf_trace_printk: BPF triggered from PID 3840345.
           <...>-3840345 [010] d... 3220702.101265: bpf_trace_printk: BPF triggered from PID 3840345.
```

`minimal` is great as a bare-bones experimental playground to quickly try out
new ideas or BPF features.

## Bootstrap

`bootstrap` is an example of a simple (but realistic) BPF application. It
tracks process starts (`exec()` family of syscalls, to be precise) and exits
and emits data about filename, PID and parent PID, as well as exit status and
duration of the process life. With `-d <min-duration-ms>` you can specify
minimum duration of the process to log. In such mode process start
(technically, `exec()`) events are not output (see example output below).

`bootstrap` was created in the similar spirit as
[libbpf-tools](https://github.com/iovisor/bcc/tree/master/libbpf-tools) from
BCC package, but is designed to be more stand-alone and with simpler Makefile
to simplify adoption to user's particular needs. It demonstrates the use of
typical BPF features:
  - cooperating BPF programs (tracepoint handlers for process `exec` and `exit`
    events, in this particular case);
  - BPF map for maintaining the state;
  - BPF ring buffer for sending data to user-space;
  - global variables for application behavior parameterization.
  - it utilizes BPF CO-RE and vmlinux.h to read extra process information from
    kernel's `struct task_struct`.

`bootstrap` is intended to be the starting point for your own BPF application,
with things like BPF CO-RE and vmlinux.h, consuming BPF ring buffer data,
command line arguments parsing, graceful Ctrl-C handling, etc. all taken care
of for you, which are crucial but mundane tasks that are no fun, but necessary
to be able to do anything useful. Just copy/paste and do simple renaming to get
yourself started.

Here's an example output in minimum process duration mode:

```shell
$ sudo ./bootstrap -d 50
TIME     EVENT COMM             PID     PPID    FILENAME/EXIT CODE
19:18:32 EXIT  timeout          3817109 402466  [0] (126ms)
19:18:32 EXIT  sudo             3817117 3817111 [0] (259ms)
19:18:32 EXIT  timeout          3817110 402466  [0] (264ms)
19:18:33 EXIT  python3.7        3817083 1       [0] (1026ms)
19:18:38 EXIT  python3          3817429 3817424 [1] (60ms)
19:18:38 EXIT  sh               3817424 3817420 [0] (79ms)
19:18:38 EXIT  timeout          3817420 402466  [0] (80ms)
19:18:43 EXIT  timeout          3817610 402466  [0] (70ms)
19:18:43 EXIT  grep             3817619 3817617 [1] (271ms)
19:18:43 EXIT  timeout          3817609 402466  [0] (321ms)
19:18:44 EXIT  iostat           3817585 3817531 [0] (3006ms)
19:18:44 EXIT  tee              3817587 3817531 [0] (3005ms)
...
```

# Building

```shell
$ git submodule update --init --recursive       # check out libbpf
$ cd src
$ make
$ sudo ./bootstrap
TIME     EVENT COMM             PID     PPID    FILENAME/EXIT CODE
00:21:22 EXIT  python3.8        4032353 4032352 [0] (123ms)
00:21:22 EXEC  mkdir            4032379 4032337 /usr/bin/mkdir
00:21:22 EXIT  mkdir            4032379 4032337 [0] (1ms)
00:21:22 EXEC  basename         4032382 4032381 /usr/bin/basename
00:21:22 EXIT  basename         4032382 4032381 [0] (0ms)
00:21:22 EXEC  sh               4032381 4032380 /bin/sh
00:21:22 EXEC  dirname          4032384 4032381 /usr/bin/dirname
00:21:22 EXIT  dirname          4032384 4032381 [0] (1ms)
00:21:22 EXEC  readlink         4032387 4032386 /usr/bin/readlink
^C
```

# Troubleshooting

Libbpf debug logs are quire helpful to pinpoint the exact source of problems,
so it's usually a good idea to look at them before starting to debug or
posting question online.

`./minimal` is always running with libbpf debug logs turned on.

For `./bootstrap`, run it in verbose mode (`-v`) to see libbpf debug logs:

```shell
$ sudo ./bootstrap -v
libbpf: loading object 'bootstrap_bpf' from buffer
libbpf: elf: section(2) tp/sched/sched_process_exec, size 384, link 0, flags 6, type=1
libbpf: sec 'tp/sched/sched_process_exec': found program 'handle_exec' at insn offset 0 (0 bytes), code size 48 insns (384 bytes)
libbpf: elf: section(3) tp/sched/sched_process_exit, size 432, link 0, flags 6, type=1
libbpf: sec 'tp/sched/sched_process_exit': found program 'handle_exit' at insn offset 0 (0 bytes), code size 54 insns (432 bytes)
libbpf: elf: section(4) license, size 13, link 0, flags 3, type=1
libbpf: license of bootstrap_bpf is Dual BSD/GPL
...
```
