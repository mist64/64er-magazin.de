# 9 — Extract listings from the disk image into `prg/`

**Goal:** decompose the issue's official `.D64` (or several, e.g. side A
and side B) into a per-file directory `issues/<YYMM>/prg/` plus a
worklist `issues/<YYMM>/prg.txt` containing one `<figure>` HTML snippet
per listing, pre-filled except for two placeholders.

This step is purely mechanical — it just runs the project's existing
extractor and lands the disk's contents next to the per-article HTML
files. The hand work of placing each `<figure>` in the right article
and filling its caption is the next step.

## What the extractor does

The script (a wrapper around `c1541` from VICE) walks each `.D64`'s
directory and:

- writes BASIC files to `prg/<name>.txt` (petcat-detokenised) and moves
  the binary `.prg` to `prg/del/` so the generator picks the text path;
- writes raw binary files (PRG, USR, …) to `prg/<name>.prg` so the
  generator renders them as MSE hex dumps or as binary downloads;
- emits the disk's "section separator" filenames (`-----------NN`)
  as HTML comments in `prg.txt`. Those comments tell you which article
  the listings under them belong to: `NN` is the article's start page.
- assembles a single `prg.txt` containing one `<figure>` block per
  listing in disk-directory order, with placeholder
  `data-name="XXXXXXXXXXXX"` and `<figcaption>YYYYYYYYYYYYY</figcaption>`
  to be filled by hand from the scan.

## Source `.D64` location

The project's canonical disk-image archive lives at:

```
~/tmp/64er-Disketten/YYXX/<YYMM>.D64
# e.g. ~/tmp/64er-Disketten/86XX/8607.D64
```

For Sonderhefte the file lives under the same root with the SH naming.
**Always confirm the exact source path with the user before running
the extractor** — multiple copies of the same disk may exist on the
machine (TOSEC archive, mirror folders, local downloads). Pick the
canonical one so `prg.txt`'s recorded source comment is meaningful
later.

## Usage

```bash
tools/llm/rules/9_prg_from_d64.sh issues/<YYMM> ~/tmp/64er-Disketten/YYXX/<YYMM>.D64
# or for an issue published as two disks:
tools/llm/rules/9_prg_from_d64.sh issues/<YYMM> \
    ~/tmp/64er-Disketten/.../SideA.D64 \
    ~/tmp/64er-Disketten/.../SideB.D64
```

The wrapper `cd`s into `issues/<YYMM>` and runs `tools/prg_links.sh`
there, so the output (`prg/`, `prg.txt`) lands next to the issue's
article files. The first comment line of `prg.txt` records the
absolute path of each `.D64` consumed — keep that for provenance.

## Verification

```bash
# 1. The output exists.
ls issues/8607/prg/ | head
test -s issues/8607/prg.txt && echo "prg.txt OK"

# 2. Every section-separator comment matches the start page of some
#    article in the issue (otherwise listings will end up orphaned).
grep -oE '"--+[^"]*"' issues/8607/prg.txt | sort -u
# Eyeball: each "----------NN" should map to a `NN ….html` in the issue.

# 3. Cross-check: no <figure> block in prg.txt was emitted without a
#    section separator above it (orphan listing — would have no
#    article to place into):
python3 - issues/8607/prg.txt <<'PY'
import re, sys
s = open(sys.argv[1]).read()
chunks = re.split(r'(<!--[^>]*"----+[^"]*"[^>]*-->)', s)
section = None; orphan = 0
for c in chunks:
    if c.startswith('<!--') and '----' in c:
        section = c.strip(); continue
    if '<figure' in c and section is None:
        orphan += c.count('<figure')
print(f"orphan figures (no section separator yet): {orphan}")
PY
```

If you see orphans, the very first listings on the disk preceded any
section separator — they're typically the boot screen / disk
intro. Treat them per the placement rule (next step): if they don't
match an article, they get reported, not placed.

## Notes / things to watch

- The script's bulk-move uses `mv ./*` (not `mv *`) so filenames
  starting with `-` (the separator placeholders) don't get parsed as
  option flags. If `Processing files with petcat...` runs but `prg/`
  ends up empty, that's the symptom; rerun against a single `.D64`.
- `prg/del/` holds the `.prg` companions of files that were classified
  as BASIC and saved as `.txt`. Don't delete it — the generator may
  still resolve binary downloads from those files via `petcat2prg`.
- Sonderheft disks sometimes mark reprinted utilities from earlier
  issues with separators like `----M/YY-NN`; those listings belong to
  that older issue's article, not the current one. The placement step
  handles them.
- The `.D64` images aren't in the repo. Pass the absolute path on the
  command line every time; do not copy the disk image into the issue
  directory.
