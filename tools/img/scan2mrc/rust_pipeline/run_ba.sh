#!/usr/bin/env bash
set -uo pipefail
B=./target/release/mrcpipe
for n in 006 016; do
  "$B" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy val/after_${n}.pdf >/dev/null 2>&1
  BK=9999 OBJF=2 BC=9999 "$B" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy val/before_${n}.pdf >/dev/null 2>&1
  echo "done $n"
done
echo ALLDONE
