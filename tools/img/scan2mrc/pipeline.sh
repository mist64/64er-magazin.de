#!/bin/bash
# THE pipeline. One script, one place where every stage's invocation and parameters live.
#
#   pipeline.sh                     run every stage, all pages
#   pipeline.sh --from mrc          resume from a stage
#   pipeline.sh --only mrc,debug    just these
#   pipeline.sh --pages 62 98 146   a subset (stages that support it)
#   pipeline.sh --force             re-run even where outputs exist
#   pipeline.sh --list              show the stages and stop
#
# WHY THIS EXISTS. There were two partial drivers (cache_pages.sh, mrc_pages.sh), eleven one-off
# run_*.sh under rust_pipeline/, and a fresh hand-written driver for nearly every experiment. Each
# copy re-stated the same invocation, and copies drift. Two live examples, both found the same
# afternoon and both silently producing output the pipeline would never ship:
#
#   * a sweep driver omitted --bg-dpi, so it rendered a 200 dpi background where the pipeline
#     ships 150. Every absolute size quoted from that sweep was for a file that does not exist.
#   * the same driver passed score/NNN.npy where the pipeline passes score/NNNm.npy -- the score
#     MASKED by the known-region map, so out-of-page areas cannot form clusters. A different
#     detector input for the entire experiment.
#
# Neither was a thinking error; both were a second copy of a step that had already been got right
# somewhere else. So: one definition, and experiments override it by env var, never by re-writing.
#
# STAGE ORDER AND WHAT ACTUALLY FLOWS BETWEEN THEM
#
#   stack    stack_render.py            deskew + matte + spine -> stack600/NNN.png (RGBA)
#   window   03-crop/fit_window.py      -> crop_windows_v2.json  (the A4 window per page)
#   geom     03-crop/emit_geometry.py   -> page_geometry.json + page_geometry/NNN/  (CUT PROFILES)
#   cache    mrcpipe apply/geometry/detect -> page RGB, known mask, screen geometry, score
#   mask     score/NNN.npy + known.png  -> score/NNNm.npy      (unknown regions zeroed)
#   mrc      mrcpipe mrc                -> mrc/NNN.pdf + NNN.jsonl + NNN_base600.png
#   debug    06-mrc/debug_pdf.py        -> dbg/NNN.png         (decision overlay)
#   assemble 06-mrc/assemble_issue.py   -> 8609.pdf            (lossless)
#
# THE TRAP, stated because it has cost a 7-hour run once: `cache` reads the CUT PROFILES written by
# `geom`, not the matte code. Changing bed_matte.py and re-running `cache` applies nothing. Any
# matte/spine/window change must re-run from `stack`. That is why --from exists and why the default
# is to run everything.
#
# PARALLELISM: 3 lanes. mrcpipe is internally rayon-parallel, so more lanes oversubscribe and
# throughput FALLS. The Python stages set OMP_NUM_THREADS=1 themselves and take --jobs.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
MP="$HERE/rust_pipeline/target/release/mrcpipe"
PY="${PY:-/Users/mist/Documents/git/64er-magazin.de/.venv/bin/python}"
T="${T:-/Users/mist/DNB/8609/tmp}"

# --- the knobs. Every experiment overrides these, none of them re-states an invocation. ----------
BGDPI="${BGDPI:-150}"     # background dpi. 150 because the measured ruling is 133-152 lpi and the
                          # halftone discarded everything above ruling/2 -- 200 was above the
                          # information limit and cost bytes for nothing.
LANES="${LANES:-3}"
JOBS="${JOBS:-3}"         # for the Python stages
OUT="${OUT:-$T/mrc}"      # where mrc/debug write; point at a scratch dir for an experiment
DBGDIR="${DBGDIR:-$OUT/dbg}"
ISSUE="${ISSUE:-$T/8609.pdf}"
FORCE="${FORCE:-0}"

STAGES=(stack window geom cache mask mrc debug assemble)
FROM=""; ONLY=""; PAGES=""

while [ $# -gt 0 ]; do
  case "$1" in
    --from)  FROM="$2"; shift 2;;
    --only)  ONLY="$2"; shift 2;;
    --pages) shift; while [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; do PAGES="$PAGES $1"; shift; done;;
    --force) FORCE=1; shift;;
    --list)  printf '%s\n' "${STAGES[@]}"; exit 0;;
    -h|--help) sed -n '1,40p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

want() {
  local s="$1"
  if [ -n "$ONLY" ]; then case ",$ONLY," in *",$s,"*) return 0;; *) return 1;; esac; fi
  if [ -n "$FROM" ]; then
    local seen=0
    for x in "${STAGES[@]}"; do
      [ "$x" = "$FROM" ] && seen=1
      [ "$x" = "$s" ] && { [ "$seen" = 1 ] && return 0 || return 1; }
    done
    return 1
  fi
  return 0
}
say() { echo "$(date +%H:%M:%S) [$1] $2"; }
# ONE PAGE PER LINE. xargs -I{} splits on lines, so emitting "98 146 171" as one line silently
# renders only the first page and reports success -- which it did, once.
pagelist() { if [ -n "$PAGES" ]; then printf '%s\n' $PAGES; else seq 1 176; fi; }

[ -x "$MP" ] || { echo "no mrcpipe at $MP -- cargo build --release first" >&2; exit 1; }

# ------------------------------------------------------------------------------------------------
if want stack; then
  say stack "deskew + matte + spine -> stack600/"
  (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" stack_render.py --measure --jobs "$JOBS") || exit 1
fi

if want window; then
  say window "fit the A4 window -> crop_windows_v2.json"
  (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" 03-crop/fit_window.py --jobs "$JOBS") || exit 1
fi

if want geom; then
  say geom "cut profiles -> page_geometry.json + page_geometry/NNN/"
  (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" 03-crop/emit_geometry.py --jobs "$JOBS") || exit 1
fi

# ------------------------------------------------------------------------------------------------
if want cache; then
  say cache "apply + screen geometry + detect (${LANES} lanes)"
  mkdir -p "$T/score" "$T/screen_geom" "$T/render/deliver"
  cache_one() {
    n=$(printf "%03d" "$1")
    if [ "$FORCE" != "1" ] && [ -s "$T/score/$n.npy" ] && [ -s "$T/render/deliver/${n}_page_rgb.png" ]; then
      return 0
    fi
    [ -d "$T/page_geometry/$n" ] || { echo "  p$n NO GEOMETRY -- run --from geom"; return 1; }
    det="$T/render/deliver/${n}_cmyk_detect.tif"
    # the per-page report carries unknown_pct / gcr_ok / dead_px / holes_filled, which is what
    # verify_stages.py reads. Discarding it is why an earlier run could not be audited afterwards.
    "$MP" apply "$1" --out "$T/render/deliver" --inpaint --detect-too --page-rgb \
        2>/dev/null | tail -1 >> "$T/apply_reports.jsonl" || { echo "  p$n APPLY FAILED"; return 1; }
    [ -s "$det" ] || { echo "  p$n no detect tif"; return 1; }
    "$MP" geometry "$det" "$T/screen_geom/$n.json" --dpi 2400 >/dev/null 2>&1
    "$MP" detect   "$det" "$T/score/$n"                      >/dev/null 2>&1
    rm -f "$det"          # ~2.2 GB, uncompressed on purpose: it lives a minute and everything
                          # derived from it (geometry + score) is small
    echo "  p$n cached"
  }
  export -f cache_one; export MP T FORCE
  pagelist | xargs -P "$LANES" -I{} bash -c 'cache_one {}'
fi

# ------------------------------------------------------------------------------------------------
if want mask; then
  say mask "mask the score with the known-region map -> score/NNNm.npy"
  # Unknown (off-sheet) regions must not form clusters. The MRC render consumes THIS, never the
  # raw score -- a sweep that passed the raw score fed the detector a different input for a whole
  # experiment without anyone noticing.
  for i in $(pagelist); do
    n=$(printf "%03d" "$i")
    [ -s "$T/score/$n.npy" ] || continue
    [ "$FORCE" != "1" ] && [ -s "$T/score/${n}m.npy" ] && [ -s "$T/score/${n}m_cov.npy" ] && continue
    OMP_NUM_THREADS=1 "$PY" - "$n" "$T" <<'PYEOF'
import sys, shutil
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
n, T = sys.argv[1], sys.argv[2]
s = np.load(f"{T}/score/{n}.npy")
kn = np.asarray(Image.open(f"{T}/render/deliver/{n}_known.png").convert("L")) > 127
H, W = kn.shape; hy, hx = s.shape; cy, cx = H // hy, W // hx
unk = 1 - kn[:hy * cy, :hx * cx].reshape(hy, cy, hx, cx).mean((1, 3))
np.save(f"{T}/score/{n}m.npy", np.where(unk > 0.25, 0.0, s).astype(np.float32))
shutil.copy(f"{T}/score/{n}_cov.npy", f"{T}/score/{n}m_cov.npy")
PYEOF
  done
  echo "  masked: $(ls "$T"/score/*m.npy 2>/dev/null | wc -l | tr -d ' ')"
fi

# ------------------------------------------------------------------------------------------------
if want mrc; then
  say mrc "MRC render, bg-dpi $BGDPI -> $OUT (${LANES} lanes)"
  mkdir -p "$OUT"
  mrc_one() {
    n=$(printf "%03d" "$1")
    [ "$FORCE" != "1" ] && [ -s "$OUT/$n.pdf" ] && return 0
    [ -s "$T/score/${n}m.npy" ] || { echo "  p$n no masked score -- run --only mask"; return 1; }
    MRC_RECORD="$OUT/$n.jsonl" "$MP" mrc --bg-dpi "$BGDPI" \
        "$T/render/deliver/${n}_page_rgb.png" "$T/score/${n}m.npy" "$OUT/$n.pdf" \
        > "$OUT/$n.log" 2>&1 \
      && echo "  p$n -> $(du -h "$OUT/$n.pdf" | cut -f1)" || echo "  p$n MRC FAILED (see $OUT/$n.log)"
    rm -rf "$OUT/.mrctmp_$n"
  }
  export -f mrc_one; export MP T OUT BGDPI FORCE
  pagelist | xargs -P "$LANES" -I{} bash -c 'mrc_one {}'
fi

# ------------------------------------------------------------------------------------------------
if want debug; then
  say debug "decision overlays -> $DBGDIR"
  # Draws on the 600 dpi base the renderer itself emitted, so picture and record cannot disagree.
  # The base is a downsample of the source page RGB and is bit-identical across configs, so these
  # can always be rebuilt from any run's bases plus current records -- ~90 s for all 176, no
  # rendering. Do not queue a re-render to get them.
  mkdir -p "$DBGDIR"
  OMP_NUM_THREADS=1 DBG_REC="$OUT" DBG_BASE="$OUT" DBG_PNG="$DBGDIR" \
    "$PY" "$HERE/06-mrc/debug_pdf.py" --jobs "$JOBS" --png-only ${PAGES:+--pages $PAGES}
fi

# ------------------------------------------------------------------------------------------------
if want assemble; then
  say assemble "lossless issue -> $ISSUE"
  OMP_NUM_THREADS=1 "$PY" "$HERE/06-mrc/assemble_issue.py" --out "$ISSUE" ${PAGES:+--pages $PAGES}
fi

say done "pdfs=$(ls "$OUT"/[0-9][0-9][0-9].pdf 2>/dev/null | wc -l | tr -d ' ')  dbg=$(ls "$DBGDIR"/[0-9][0-9][0-9].png 2>/dev/null | wc -l | tr -d ' ')"
