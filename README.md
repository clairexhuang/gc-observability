# eBPF Project

This repository contains files from my 2022 semester 2 project on 'Diagnosing Garbage Collection Problems with eBPF' (supervised by Professor Steve Blackburn). We use MMTk with the OpenJDK binding. 

In this project, we investigate case studies into [lock contention](https://github.com/clairexhuang/ebpf/tree/main/lock-contention) and GC scalability.  

In the GC scalability study, we measured [GC scalability in MMTk](https://github.com/clairexhuang/ebpf/tree/main/scalability) and investigated [work packets](https://github.com/clairexhuang/ebpf/tree/main/work-id) with a focus on [ProcessEdges](https://github.com/clairexhuang/ebpf/tree/main/processedges), and [SweepChunk](https://github.com/clairexhuang/ebpf/tree/main/sweepchunk). We also investigated [object graphs](https://github.com/clairexhuang/ebpf/tree/main/object-count), and measured the [overhead](https://github.com/clairexhuang/ebpf/tree/main/overhead) of bpftrace. My python script for parsing logfiles is also included.

See my MMTk-Core `bpfworkprobe-sweepchunk` [branch](https://github.com/clairexhuang/mmtk-core/tree/bpfworkprobe-sweepchunk) for the exact changes made to MMTk-Core when investigating work packets (in particular, process edges work packets) and GC scalability. See my MMTk-OpenJFK `storeedges` [branch](https://github.com/clairexhuang/mmtk-openjdk/tree/storeedges) for the exact changes made when tracing outgoing graph edges for each node. 

Below are instructions for using eBPF in MMTk on the moma machines. You will need `sudo` permission. 

We use [bpftrace](https://github.com/iovisor/bpftrace). To incorporate tracing with probes into MMTk-Core:
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
4. Force use of frame pointers and then build MMTk with the instructions in the [OpenJDK binding](https://github.com/mmtk/mmtk-openjdk) 
```
export RUSTFLAGS=-Cforce-frame-pointers=yes
```
5. Write the tracing code. An example is the [code](https://github.com/clairexhuang/ebpf/blob/main/work-id/id.bt) which collects statistics about work packets (cumulative time & distribution by packet type). Also, see the [reference guide](https://github.com/iovisor/bpftrace/blob/master/docs/reference_guide.md) for more information, and the [tools page](https://github.com/iovisor/bpftrace/tree/master/tools) for some sample/existing functionalities. 
