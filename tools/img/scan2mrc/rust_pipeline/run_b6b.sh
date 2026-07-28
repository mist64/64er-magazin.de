#!/usr/bin/env bash
set -uo pipefail
BIN=./target/release/mrcpipe
: > val/b6b_diag.txt
for n in 010 011 012 013 014 017 018 019 020; do
  echo "### page $n" >> val/b6b_diag.txt
  MRC_DIAG=1 "$BIN" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy val/b6_${n}.pdf 2>>val/b6b_diag.txt 1>>val/b6b_diag.txt
done
echo "ALL DONE" >> val/b6b_diag.txt
