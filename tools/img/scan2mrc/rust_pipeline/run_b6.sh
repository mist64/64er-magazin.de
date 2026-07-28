#!/usr/bin/env bash
set -uo pipefail
BIN=./target/release/mrcpipe
: > val/b6_diag.txt
for n in 006 007 008 009 016 003 015 028; do
  echo "### page $n" >> val/b6_diag.txt
  MRC_DIAG=1 "$BIN" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy val/b6_${n}.pdf 2>>val/b6_diag.txt 1>>val/b6_diag.txt
done
echo "ALL DONE" >> val/b6_diag.txt
