#!/usr/bin/env bash
set -uo pipefail
BIN=./target/release/mrcpipe
LOG=val/run_6_20.log; : > "$LOG"
for i in $(seq 6 20); do
  n=$(printf "%03d" "$i")
  pg="../pages/${n}_2400_cropped.png"; sc="../screened/screened_${n}.npy"
  out="val/mrc_${n}_rs.pdf"
  if [ ! -f "$pg" ] || [ ! -f "$sc" ]; then echo "SKIP $n (missing input)" | tee -a "$LOG"; continue; fi
  t0=$SECONDS
  "$BIN" mrc "$pg" "$sc" "$out" >>"$LOG" 2>&1
  rc=$?
  printf "page %s  rc=%d  %ds  %s\n" "$n" "$rc" "$((SECONDS-t0))" "$([ -f "$out" ]&&du -h "$out"|cut -f1)" | tee -a "$LOG"
done
echo "ALL DONE" | tee -a "$LOG"
