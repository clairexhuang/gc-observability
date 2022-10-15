# eBPF Project

This repository contains files from my 2022 semester 2 project on 'Diagnosing Garbage Collection Problems with eBPF' (supervised by Professor Steve Blackburn).

We use `bpftrace`.
To incorporate tracing with probes into MMTk-Core:
1. Add probe to `[dependencies]` in `Cargo.toml`:
```
probe = "0.3"
```
2. In `src/lib.rs`, add: 
```
#[macro_use]
extern crate probe;
```
3. Place probes in the code, passing `mmtk` as the first argument, giving a name as the second argument, and adding more arguments where appropriate:
```
probe!(mmtk,probe_name,arg0,arg1);
```
4. Build MMTk with the instructions in the OpenJDK binding: 
5. Write the tracing code. An example is the code which collects statistics about work packets (cumulative time & distribution by packet type): https://github.com/clairexhuang/ebpf/blob/main/do_work_with_stat-tracing/worker_id.bt. See the `bpftrace` reference guide at https://github.com/iovisor/bpftrace/blob/master/docs/reference_guide.md for more information, and the tools page https://github.com/iovisor/bpftrace/tree/master/tools for the tracing code for some sample/existing functionalities. 
