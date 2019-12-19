# parseKokkosMemEvents

The following code parses output from [kokkos-tools MemoryEvents](https://github.com/kokkos/kokkos-tools/wiki/MemoryEvents) to create an area plot (example below) that is grouped by the highest consuming 'regions' (defined by the Kokkos Profiling APIs `pushRegion(...)` and `popRegion(...)`).

## dependencies

python3 with `pyparsing`, `pandas`, and `matplotlib`

## run

`python ./memEventParse.py /path/to/h##n##-####.mem_events /path/to/plot.png` 
