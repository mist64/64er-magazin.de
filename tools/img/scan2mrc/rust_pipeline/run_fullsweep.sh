#!/usr/bin/env bash
set -uo pipefail
BIN=./target/release/mrcpipe
: > val/fullsweep_diag.txt
for i in $(seq 41 168); do
  n=$(printf "%03d" $i)
  [ -f ../pages/${n}_2400_cropped.png ] || continue
  [ -f ../screened/screened_${n}.npy ] || { echo "### page $n MISSING score" >>val/fullsweep_diag.txt; continue; }
  echo "### page $n" >> val/fullsweep_diag.txt
  MRC_DIAG=1 "$BIN" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy /tmp/fs_${n}.pdf 2>>val/fullsweep_diag.txt 1>>val/fullsweep_diag.txt
  rm -rf /tmp/.mrctmp_fs_${n} /tmp/fs_${n}.pdf 2>/dev/null
done
echo "ALL DONE" >> val/fullsweep_diag.txt
