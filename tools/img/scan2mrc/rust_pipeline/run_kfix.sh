#!/usr/bin/env bash
B=./target/release/mrcpipe
for n in 040 050 002; do
  "$B" mrc ../pages/${n}_2400_cropped.png ../screened/screened_${n}.npy val/kfix_${n}.pdf >/dev/null 2>&1
  rm -rf val/.mrctmp_kfix_${n}
  echo "kfix $n -> $(ls -la val/kfix_${n}.pdf 2>/dev/null|awk '{print $5}')"
done
echo KFIX-DONE
