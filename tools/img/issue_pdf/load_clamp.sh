# load_clamp.sh -- HALF OF WHAT IS FREE, AND NEVER A NESTED THREAD.
#
# Source this from any tool that fans out.  It does two things, and the second
# one matters more than the first:
#
#   1. half_of_free_cores   how many jobs this machine can spare RIGHT NOW
#   2. the exports below    one thread per job, always
#
# WHY BOTH.  A job count alone does not bound the load, because every tool we
# run here multithreads on its own: N jobs x M threads is N*M runnable
# threads, and the two multiply silently.  The machine is shared, and the load
# we create is not ours to spend.
#
# THIS HAS NOW HAPPENED THREE TIMES, each time from the same shape:
#   * 8612      make_issue_pdf_mixed.sh at NCPU jobs, each magick taking every
#               core: load ~900, stalled 25+ min.  Fixed by MAGICK_THREAD_LIMIT=1
#               -- in that one file.
#   * SH8605    32 tesseract jobs where the lane rule gave 28.  Survived only
#               because it ran alone; the same over-subscription had already
#               killed step 030 earlier in that build.
#   * SH8607    make_issue_pdf.sh with JOBS=22 and NO thread limits at all --
#               the plain script never got 8612's fix.  tesseract and magick
#               each multithreaded, the 1-minute load reached 386, and the
#               machine's memory watchdog emergency-killed ANOTHER USER'S
#               231 GB model server, then killed it again on every restart
#               until the load fell.  It stayed down.
#
# The lesson each time was written as "pass the right JOBS".  That lesson is
# wrong: it puts a machine-wide outage behind a number every caller has to
# remember.  The script clamps itself, so forgetting is not a failure mode.
#
# A CEILING, NOT A TARGET: an explicitly passed JOBS is clamped DOWN to this
# and never up, so a deliberately small run stays small.

# One thread per job, for every library that reads an environment variable.
# Unconditional and exported: this alone would have prevented all three.
export OMP_THREAD_LIMIT=1
export OMP_NUM_THREADS=1
export MAGICK_THREAD_LIMIT=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Half of the cores that are free right now: (ncpu - 1-minute load) / 2.
# Measured, not assumed -- this box runs with a 350 GB model server resident
# some days and empty others, and a constant would be wrong on one of them.
half_of_free_cores() {
  local ncpu load
  ncpu="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"
  # vm.loadavg prints "{ 14.02 12.44 9.54 }"; field 2 is the 1-minute figure.
  load="$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2+0}')"
  [[ -n "$load" ]] || load=0
  awk -v n="$ncpu" -v l="$load" 'BEGIN {
    f = n - l; if (f < 2) f = 2;      # always leave room for one job
    j = int(f / 2); if (j < 1) j = 1; if (j > n) j = n;
    print j
  }'
}

# Clamp a requested job count to the ceiling, and say so when it bites.
# Usage: JOBS="$(clamp_jobs "${JOBS:-}")"
clamp_jobs() {
  local want="${1:-}" ceiling
  ceiling="$(half_of_free_cores)"
  if [[ -z "$want" ]]; then
    echo "$ceiling"; return
  fi
  if (( want > ceiling )); then
    echo "JOBS=$want exceeds half the free cores; using $ceiling" >&2
    echo "$ceiling"; return
  fi
  echo "$want"
}
