#!/usr/bin/env bash
set -uo pipefail
B=./target/release/mrcpipe; LOG=../mrc_pdf/render.log; : > "$LOG"
ok=0; skip=0
for i in $(seq 1 168); do
  n=$(printf "%03d" $i)
  pg="../pages/${n}_2400_cropped.png"; sc="../screened/screened_${n}.npy"
  [ -f "$pg" ] && [ -f "$sc" ] || { echo "SKIP $n (no input)" >>"$LOG"; skip=$((skip+1)); continue; }
  t0=$SECONDS
  if "$B" mrc "$pg" "$sc" "../mrc_pdf/${n}.pdf" >>"$LOG" 2>&1; then
    echo "ok $n $((SECONDS-t0))s" >>"$LOG"; ok=$((ok+1))
  else echo "FAIL $n" >>"$LOG"; fi
  rm -rf "../mrc_pdf/.mrctmp_${n}" 2>/dev/null
done
echo "ALLDONE ok=$ok skip=$skip" >>"$LOG"
