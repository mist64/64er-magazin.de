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
#   skew     01-deskew/deskew.py        -> skew_all.txt   (one angle per page, MEASURED only)
#   holes    02b/clip_holes.py          -> clip_holes.json (the 6 binder-clip holes per page)
#   spine    02b/spine.py               -> spine_all.json  (neighbour-page boundary; reads holes)
#   stack    stack_render.py            deskew + matte + spine -> stack600/NNN.png (RGBA)
#   logo     03-crop/logo_detect.py     -> logo_positions.json   (the 64'er wordmark anchor)
#   clear    03-crop/logo_clearance.py  -> logo_clearance.json   (page around the anchor; reads stack)
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

STAGES=(skew holes spine stack logo clear window geom cache)
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
if want skew; then
  # Measured on the 150 dpi thumbs -- the angle is scale-invariant, and this stage MEASURES ONLY;
  # stack_render applies it. It was missing from this driver until 2026-08-02, so a tmp/ wipe left
  # `stack` failing on a file no stage produced. Every input the pipeline needs is made by a stage.
  if [ "$FORCE" = "1" ] || [ ! -s "$T/skew_all.txt" ]; then
    say skew "page angles -> skew_all.txt"
    ls /Users/mist/DNB/8609/thumbs_150/[0-9][0-9][0-9].png \
      | xargs -P "$JOBS" -n 8 "$PY" "$HERE/01-deskew/deskew.py" \
      | sort > "$T/skew_all.txt" || exit 1
    echo "  $(wc -l < "$T/skew_all.txt" | tr -d ' ') pages measured"
  else
    say skew "skew_all.txt exists, skipping"
  fi
fi

# ------------------------------------------------------------------------------------------------
# THE 02b PAIR. clip_holes finds the six binder-clip holes; spine uses them as its prior and finds
# the neighbour-page boundary. Both were run by hand once and never belonged to this driver, so a
# tmp/ wipe left `stack` failing on files no stage produced. Both are sequential over 176 pages
# (neither takes --jobs); if that ever matters, parallelise there, not with a second driver here.
if want holes; then
  if [ "$FORCE" = "1" ] || [ ! -s "$T/clip_holes.json" ]; then
    say holes "binder-clip holes -> clip_holes.json"
    (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" 02b-opposite-page/clip_holes.py \
        --batch /Users/mist/DNB/8609/thumbs_600 --out "$T") > "$T/holes.log" 2>&1 || exit 1
    echo "  $(grep -c '^p[0-9]' "$T/holes.log" | tr -d ' ') pages"
  else
    say holes "clip_holes.json exists, skipping"
  fi
fi

if want spine; then
  if [ "$FORCE" = "1" ] || [ ! -s "$T/spine_all.json" ]; then
    say spine "neighbour-page boundary -> spine_all.json"
    (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" 02b-opposite-page/spine.py \
        --json "$T/spine_all.json") > "$T/spine.log" 2>&1 || exit 1
    echo "  $(grep -c 'FIRE' "$T/spine.log" | tr -d ' ') pages with a measured spine"
  else
    say spine "spine_all.json exists, skipping"
  fi
fi

# ------------------------------------------------------------------------------------------------
if want stack; then
  say stack "deskew + matte + spine -> stack600/"
  (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" stack_render.py --measure --jobs "$JOBS") || exit 1
fi

# ------------------------------------------------------------------------------------------------
# THE 03-crop ANCHOR PAIR. fit_window anchors the A4 window on the 64'er wordmark, so it needs the
# anchor (logo_detect, on the thumbs) and how much page surrounds it (logo_clearance, on stack600).
# Both were run by hand once and never belonged to this driver, so a tmp/ wipe left `window` failing
# on files no stage produced -- the same gap as skew/holes/spine. Every input is made by a stage.
# ORDER: logo reads only the thumbs and could run first, but clearance reads stack600, so the pair
# sits after `stack` and stays contiguous with the rest of 03-crop.
if want logo; then
  if [ "$FORCE" = "1" ] || [ ! -s "$T/logo_positions.json" ]; then
    say logo "64'er wordmark anchor -> logo_positions.json"
    (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" 03-crop/logo_detect.py) >> "$T/logo.log" 2>&1 || exit 1
    # count from the JSON, not the log: the logs are appended (>>), so a grep -c over one
    # accumulates across runs and reports 352 pages on the second pass.
    echo "  $(grep -c '"page":' "$T/logo_positions.json" | tr -d ' ') pages, $(grep -c '"found": false' "$T/logo_positions.json" | tr -d ' ') without a logo"
  else
    say logo "logo_positions.json exists, skipping"
  fi
fi

if want clear; then
  if [ "$FORCE" = "1" ] || [ ! -s "$T/logo_clearance.json" ]; then
    say clear "clearance around the anchor -> logo_clearance.json"
    (cd "$HERE" && OMP_NUM_THREADS=1 "$PY" 03-crop/logo_clearance.py --jobs "$JOBS") \
        >> "$T/clearance.log" 2>&1 || exit 1
    echo "  $(grep -c '"page":' "$T/logo_clearance.json" | tr -d ' ') pages measured (logo-less pages are excluded, not interpolated)"
  else
    say clear "logo_clearance.json exists, skipping"
  fi
fi

# ------------------------------------------------------------------------------------------------
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
    "$MP" apply "$1" --out "$T/render/deliver" --inpaint \
        2>/dev/null | tail -1 >> "$T/apply_reports.jsonl" || { echo "  p$n APPLY FAILED"; return 1; }
    echo "  p$n cached"
  }
  export -f cache_one; export MP T FORCE
  pagelist | xargs -P "$LANES" -I{} bash -c 'cache_one {}'
fi

say done "cached=$(ls "$T"/render/deliver/*_known.png 2>/dev/null | wc -l | tr -d ' ')"
