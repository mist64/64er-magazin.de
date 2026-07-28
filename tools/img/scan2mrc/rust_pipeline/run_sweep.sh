#!/usr/bin/env bash
set -uo pipefail
BIN=./target/release/mrcpipe
: > val/sweep_diag.txt
for i in $(seq 21 40); do
  n=$(printf "%03d" $i)
  [ -f ../pages/${n}_2400_cropped.png ] || continue
  echo "### page $n" >> val/sweep_diag.txt
  MRC_DIAG=1 "$BIN" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy /tmp/sweep_${n}.pdf 2>>val/sweep_diag.txt 1>>val/sweep_diag.txt
  rm -rf /tmp/.mrctmp_sweep_${n} 2>/dev/null
done
echo "ALL DONE" >> val/sweep_diag.txt
