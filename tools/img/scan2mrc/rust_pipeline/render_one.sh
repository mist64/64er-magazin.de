#!/usr/bin/env bash
n=$(printf "%03d" "$1")
pg="../pages/${n}_2400_cropped.png"; sc="../screened/screened_${n}.npy"
[ -f "$pg" ] && [ -f "$sc" ] || exit 0
[ -f "../mrc_pdf/${n}.pdf" ] && exit 0
./target/release/mrcpipe mrc "$pg" "$sc" "../mrc_pdf/${n}.pdf" >/dev/null 2>&1
rm -rf "../mrc_pdf/.mrctmp_${n}" 2>/dev/null
