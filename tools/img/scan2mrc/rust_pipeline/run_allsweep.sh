#!/usr/bin/env bash
set -uo pipefail
BIN=./target/release/mrcpipe
: > val/allsweep_diag.txt
for i in $(seq 1 168); do
  n=$(printf "%03d" $i)
  [ -f ../pages/${n}_2400_cropped.png ] || continue
  [ -f ../screened/screened_${n}.npy ] || { echo "### page $n NOSCORE" >>val/allsweep_diag.txt; continue; }
  echo "### page $n" >> val/allsweep_diag.txt
  MRC_DIAG=1 "$BIN" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy /tmp/as_${n}.pdf >>val/allsweep_diag.txt 2>&1
  rm -rf /tmp/.mrctmp_as_${n} /tmp/as_${n}.pdf 2>/dev/null
done
echo "ALL DONE" >> val/allsweep_diag.txt
