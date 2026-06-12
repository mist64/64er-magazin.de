#!/bin/bash
# Extract one or more .D64 disk images into <issue-dir>/prg/ plus a
# worklist <issue-dir>/prg.txt with one <figure> snippet per listing.
# Thin wrapper around tools/prg_links.sh that lets the caller stay in
# the repo root.
#
# Usage:
#   tools/llm/rules/9_prg_from_d64.sh <issue-dir> <d64> [<d64>...]
set -e
if [ $# -lt 2 ]; then
  echo "usage: $0 <issue-dir> <d64> [<d64>...]" >&2
  exit 1
fi
issue_dir="$1"; shift
[ -d "$issue_dir" ] || { echo "no such dir: $issue_dir" >&2; exit 1; }
repo_root=$(git rev-parse --show-toplevel)
( cd "$issue_dir" && "$repo_root/tools/prg_links.sh" "$@" )
echo
echo "wrote $issue_dir/prg.txt and $(ls "$issue_dir/prg" 2>/dev/null | wc -l | tr -d ' ') file(s) under $issue_dir/prg/"
