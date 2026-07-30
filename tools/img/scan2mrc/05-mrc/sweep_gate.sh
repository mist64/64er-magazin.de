#!/bin/bash
# Run `classify` twice over every cached page -- once with a gate overridden, once without -- so a
# proposed change can be diffed across the whole issue instead of the handful of pages that happen
# to be open.
#
#   sweep_gate.sh <tag> <ENV=VALUE> [first] [last]
#
# e.g.  sweep_gate.sh darkfill DARKFILL_FILLED=0.70
#       -> dbg/rec_darkfill_old/NNN.jsonl   (with the override = the OLD behaviour)
#          dbg/rec_darkfill_new/NNN.jsonl   (as shipped)
#       then: diff_record.py dbg/rec_darkfill_old dbg/rec_darkfill_new
#
# Uses the RAW score, not the sidecar-masked one production feeds `mrc`. That costs nothing here:
# both sides get identical input, so every flip the diff reports is caused by the gate and nothing
# else -- and darkfill/K decisions never read the score at all. Absolute cluster counts will differ
# slightly from a production render; relative changes will not.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MP="$HERE/../rust_pipeline/target/release/mrcpipe"
T=/Users/mist/DNB/8609/tmp

tag=$1; override=$2; first=${3:-1}; last=${4:-176}
old="$T/dbg/rec_${tag}_old"; new="$T/dbg/rec_${tag}_new"
mkdir -p "$old" "$new"

for i in $(seq "$first" "$last"); do
  n=$(printf "%03d" "$i")
  p="$T/render/deliver/${n}_page_rgb.png"
  s="$T/score/${n}.npy"
  [ -s "$p" ] && [ -s "$s" ] || continue
  [ -s "$old/$n.jsonl" ] && [ -s "$new/$n.jsonl" ] && { echo "$n cached"; continue; }
  env "$override" MRC_RECORD="$old/$n.jsonl" "$MP" classify "$p" "$s" >/dev/null 2>&1 \
    || { echo "  p$n OLD FAILED"; continue; }
  MRC_RECORD="$new/$n.jsonl" "$MP" classify "$p" "$s" >/dev/null 2>&1 \
    || { echo "  p$n NEW FAILED"; continue; }
  echo "$(date +%H:%M:%S) p$n  $(wc -l < "$old/$n.jsonl") / $(wc -l < "$new/$n.jsonl") rows"
done
echo "range $first..$last done"
