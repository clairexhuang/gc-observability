# eBPF Project

This repository contains files from my 2022 semester 2 project on 'Diagnosing Garbage Collection Problems with eBPF' (supervised by Professor Steve Blackburn).

We use `bpftrace` (see the reference guide at https://github.com/iovisor/bpftrace/blob/master/docs/reference_guide.md).
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
4. 
