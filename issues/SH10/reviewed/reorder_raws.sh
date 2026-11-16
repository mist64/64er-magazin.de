#!/bin/bash
# SH10: move the four bound-in Zahlkarte leaves after the covers, in the ORIGINAL scans.
# Owner 2026-11-15: "the 4 blue smaller pages should go to the very end. fix in original pngs once".
#   163->165 164->166 165->167 166->168   (the four cards)
#   167->163 168->164                     (the covers)
# /Volumes/S has NO snapshots and is not backed up.  So this script:
#   0. refuses if any .reorder-*.png exists (a half-finished earlier run) or a target is missing
#   1. checksums the six, COPIES them to the local recovery dir and verifies the copy
#   2. phase 1: renames all six to .reorder-NNN.png (same volume: no data moves)
#   3. phase 2: renames each into place with mv -n (never overwrites)
#   4. checksums again and verifies BY MAPPING (new 165 == old 163, ...), 6/6
# Dry run by default: prints the mapping and what it would do.  --doit to act.
# Run ONLY on the owner's own word that /Volumes/S may be written.  Keep the recovery copy until the rebuilt PDF
# is accepted.
set -euo pipefail
SRC=${REORDER_SRC:-/Volumes/S/png/SH10}   # REORDER_SRC/REORDER_REC: test on scratch copies only
REC=${REORDER_REC:-$HOME/DNB/SH10/tmp/recovery/raw-reorder}
MAP="163:165 164:166 165:167 166:168 167:163 168:164"
DOIT=0; [[ "${1:-}" == "--doit" ]] && DOIT=1

echo "mapping (old -> new):"; for m in $MAP; do echo "  ${m%:*}.png -> ${m#*:}.png"; done
shopt -s nullglob; stale=("$SRC"/.reorder-*.png); shopt -u nullglob
(( ${#stale[@]} == 0 )) || { echo "REFUSED: ${stale[*]} exists -- an earlier run stopped half-way; restore by hand from $REC"; exit 1; }
for m in $MAP; do [[ -f "$SRC/${m%:*}.png" ]] || { echo "REFUSED: $SRC/${m%:*}.png missing"; exit 1; }; done
[[ -e "$REC" ]] && { echo "REFUSED: $REC already exists -- a previous run; inspect it first"; exit 1; }
(( DOIT )) || { echo "dry run: would checksum, copy to $REC, rename via .reorder-NNN.png, verify by mapping. --doit to act."; exit 0; }

mkdir -p "$REC"
echo "[1] checksums + recovery copy"
( cd "$SRC" && shasum -a 256 163.png 164.png 165.png 166.png 167.png 168.png ) | tee "$REC/before.sha256"
for n in 163 164 165 166 167 168; do cp -p "$SRC/$n.png" "$REC/$n.png"; done
( cd "$REC" && shasum -a 256 -c before.sha256 ) || { echo "STOP: recovery copy does not verify; nothing renamed"; exit 1; }
cp -p "$SRC/000MISSING.txt" "$REC/000MISSING.txt"

echo "[2] phase 1"
for n in 163 164 165 166 167 168; do mv -n "$SRC/$n.png" "$SRC/.reorder-$n.png"; done
for n in 163 164 165 166 167 168; do
  [[ -f "$SRC/.reorder-$n.png" && ! -e "$SRC/$n.png" ]] || { echo "STOP after phase 1 at $n; restore from $REC"; exit 1; }
done

echo "[3] phase 2"
for m in $MAP; do
  o=${m%:*}; t=${m#*:}
  [[ -e "$SRC/$t.png" ]] && { echo "STOP: $t.png exists before its move; restore from $REC"; exit 1; }
  mv -n "$SRC/.reorder-$o.png" "$SRC/$t.png"
done

echo "[4] verify by mapping"
bad=0
for m in $MAP; do
  o=${m%:*}; t=${m#*:}
  want=$(awk -v f="$o.png" '$2==f{print $1}' "$REC/before.sha256")
  got=$(shasum -a 256 "$SRC/$t.png" | cut -d' ' -f1)
  if [[ "$want" == "$got" ]]; then echo "  ok  new $t.png == old $o.png"; else echo "  BAD new $t.png != old $o.png"; bad=1; fi
done
shopt -s nullglob; left=("$SRC"/.reorder-*.png); shopt -u nullglob
(( ${#left[@]} == 0 )) || { echo "  BAD leftover ${left[*]}"; bad=1; }
(( bad == 0 )) || { echo "STOP: verification failed; originals are in $REC"; exit 1; }
echo "6/6 verified by mapping. 000MISSING.txt still describes the OLD order -- patch it (see LOG.md)."
