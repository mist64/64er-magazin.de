#!/bin/bash
# THE pipeline. One script, one place where every stage's invocation and parameters live.
#
#   pipeline.sh                     run every stage, all pages
#   pipeline.sh --from cache        resume from a stage
#   pipeline.sh --only geom,cache   just these
#   pipeline.sh --pages 62 98 146   a subset (stages that support it)
#   pipeline.sh --force             re-run even where outputs exist
#   pipeline.sh --list              show the stages and stop
#
# WHY THIS EXISTS. There were two partial drivers and eleven one-off run_*.sh, plus a hand-written
# driver for nearly every experiment. Each copy re-stated the same invocation, and copies drift --
# one sweep driver rendered at a background dpi the pipeline never ships, another fed the detector
# an unmasked score, and both produced numbers for files that did not exist. So: ONE definition.
#
# STATUS 2026-08-02: the renderer was DELETED (see FINDINGS.md). What survives here is the FRONT
# END -- master scan to deskewed, matted, A4-cropped, graded CMYK -- which is exact and verified.
# The mask/mrc/debug/assemble stages come back when the new screen-field renderer lands.
#
# STAGE ORDER AND WHAT ACTUALLY FLOWS BETWEEN THEM
#
#   stack    stack_render.py            deskew + matte + spine -> stack600/NNN.png (RGBA)
#   window   03-crop/fit_window.py      -> crop_windows_v2.json  (the A4 window per page)
#   geom     03-crop/emit_geometry.py   -> page_geometry.json + page_geometry/NNN/  (CUT PROFILES)
#   cache    mrcpipe apply              -> graded CMYK @2400, known mask, per-page report
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
LANES="${LANES:-3}"
JOBS="${JOBS:-3}"         # for the Python stages
FORCE="${FORCE:-0}"

STAGES=(stack window geom cache)
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
  say cache "apply (${LANES} lanes)"
  mkdir -p "$T/render/deliver"
  cache_one() {
    n=$(printf "%03d" "$1")
    if [ "$FORCE" != "1" ] && [ -s "$T/render/deliver/${n}_known.png" ]; then
      return 0
    fi
    [ -d "$T/page_geometry/$n" ] || { echo "  p$n NO GEOMETRY -- run --from geom"; return 1; }
    # the per-page report carries unknown_pct / gcr_ok / dead_px / holes_filled, which is what
    # verify_stages.py reads. Discarding it is why an earlier run could not be audited afterwards.
    "$MP" apply "$1" --out "$T/render/deliver" --inpaint --detect-too \
        2>/dev/null | tail -1 >> "$T/apply_reports.jsonl" || { echo "  p$n APPLY FAILED"; return 1; }
    echo "  p$n cached"
  }
  export -f cache_one; export MP T FORCE
  pagelist | xargs -P "$LANES" -I{} bash -c 'cache_one {}'
fi

say done "cached=$(ls "$T"/render/deliver/*_known.png 2>/dev/null | wc -l | tr -d ' ')"
