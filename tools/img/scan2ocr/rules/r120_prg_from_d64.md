# 120 — Extract listings from the disk image into `prg/`

**Applies to:** all — Sonderhefte shipped a Programm-Service disk as well — every `issues/SH85*/prg/` in the repo is the output of this step.

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
tools/img/scan2ocr/rules/r120_prg_from_d64.sh issues/<YYMM> ~/tmp/64er-Disketten/YYXX/<YYMM>.D64
# or for an issue published as two disks:
tools/img/scan2ocr/rules/r120_prg_from_d64.sh issues/<YYMM> \
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

# 4. ROUND-TRIP every listing: the .txt must re-tokenise to the .prg it
#    came from.  This is the only check that sees a WRONG DIALECT -- the
#    decoded text reads fine and the reader's download is the wrong bytes.
#    It re-implements nothing: the address/version/petcat call is
#    generate.py's petcat2prg (generate.py:59-94), so a pass here is a
#    pass on the site.
dir=issues/<YYMM>
python3 - "$dir" <<'PY'
import os, re, subprocess, sys
d = os.path.join(sys.argv[1], "prg")
bad = 0
for f in sorted(os.listdir(d)):
    if not f.endswith(".txt"):
        continue
    listing = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
    m = re.findall(r"^;.*==([0-9A-Fa-f]{4})==", listing, re.M)   # the opener
    addr = m[0] if m else "0801"
    v = re.search(r"^;version=(.*)$", listing, re.M)             # optional tag
    v = v.group(1) if v else "2"
    got = subprocess.run(["petcat", f"-w{v}", "-l", addr, f"-{v}"],
                         input=listing.encode(), capture_output=True).stdout
    stem = f[:-4]
    for cand in (os.path.join(d, stem + ".prg"),
                 os.path.join(d, "del", stem + ".prg")):
        if os.path.exists(cand):
            want = open(cand, "rb").read()
            break
    else:
        print(f"  NO .prg   {f}"); bad += 1; continue
    if got == want:
        print(f"  ok  v{v:<6} {f}")
    else:
        print(f"  MISMATCH v{v:<6} {f}: {len(got)} vs {len(want)} bytes")
        bad += 1
print("round-trip failures:", bad)
PY
```

If you see orphans, the very first listings on the disk preceded any
section separator — they're typically the boot screen / disk
intro. Treat them per the placement rule (next step): if they don't
match an article, they get reported, not placed.

## Check 4: every mismatch is one of three things

None of them is "close enough". A `.txt` that does not re-tokenise to its disk
bytes is a defect until it is dispositioned in `LOG.md`.

1. **The wrong dialect.** The `.txt` was petcat-detokenised as V2 and the
   program is not V2. Fix the `;version=` tag and re-decode from the `.prg`
   (*Non-V2 BASIC dialects need a re-decode*, below), then re-run: the right
   dialect round-trips **byte-identical**, never merely closer. 8610 shipped
   four of these past this step, and none was caught here — all four were found
   by eye at step 130, off the decoded text reading wrong:

   | file | decoded as | actually | evidence |
   |---|---|---|---|
   | `cp_m formatter` | V2 | **C 128 BASIC 7.0**, `;version=70` | V2 round-trip differed by 7 bytes; `-w70` identical |
   | `mfm-scan` | V2 | **C 128 BASIC 7.0**, `;version=70` | V2 differed by 4 bytes; `-w70` identical |
   | `3d-grafik.c16` | V2 | **BASIC 3.5** at `$4001`, `;version=3` | `-w3` identical |
   | `p.pop im kopp` | V2 — `RGR`, `RDOT`, `ERR$`, `TRON`, `CHAR` inside a Speech-Basic demo | **Speech-Basic** at `$1801`, `;version=speech` | V2 gave 1152 bytes against 1111 on disk; `-speech` identical |

   The caption is a hint, not the check: `cp_m formatter`'s printed caption says
   *"für das Basic 7.0 des C 128 geschrieben"* in so many words, and the step
   still ran V2 over it, because nothing compared the output to the disk.

2. **The file is not BASIC at all** — a Hypra-Ass / Top-Ass source, an
   assembler object, a directory sector. Then the `.txt` is the defect, not the
   tag: see *Remediation* and *Sanity-check every extracted file*. 8610's
   `vg-print.src` (2235 against 2766) and `vg-cp80x.src` (4059 against 5033)
   are Profi-Ass sources kept as text on 8609's `viza.patch.quell` precedent —
   a **dispositioned** mismatch, written into `LOG.md`.

3. **Trailing bytes on the disk past the BASIC program's end** — `checksummer`
   1024 against 1027, `programm 1` (saved from a C 128) 121 against 122.
   Harmless, and still written down: an undispositioned mismatch is
   indistinguishable from case 1.

8610 finishes at **4 mismatches, all of them cases 2 and 3**, and that is the
state a finished issue is allowed to be in.

## An ML program with a BASIC stub ships as the RAW BINARY

A `.prg` whose BASIC part is a **loader stub** — one line, a `SYS` — followed
by a machine-code body is not a BASIC listing, and check 4 is where it
announces itself: the stub re-tokenises to a hundred-odd bytes against a disk
file of kilobytes.

8610's `sound-monitor` is the case. The disk file is `1986 SYS2167` plus
**12.6 KByte** of machine code (12797 bytes — the article's "51 Blocks"); the
extractor saw `$0801`, called it BASIC, wrote a 5-line `prg/sound-monitor.txt`
and moved the real program to `prg/del/`. `petcat2prg` over that `.txt` yields
**114 bytes**, so the reader's download would have been the stub alone: a
program that loads, runs, and does nothing.

The rule, which is the *hard rule* above applied to this class:

- the `.prg` sits in **`prg/`**, not `prg/del/` — the generator's
  binary-download resolver does not reach into `del/`;
- the bogus `.txt` is **dropped**: there is nothing for `petcat2prg` to
  materialise from, and nothing the print typeset as BASIC;
- the article gets the MSE / binary-download shape, not a `<pre>` of five
  lines. 8610's `51 Musik wie noch nie` carries
  `<pre data-filename="sound-monitor.prg" data-name="Soundmonitor" data-mse=mse1>`
  and its `binary_download`, on 8609's `82 HiRes Colossal` precedent.

The signature to grep for before the article is written: a `prg/*.txt` of a
handful of lines whose last statement is a bare `SYS`, with a `prg/del/*.prg`
companion an order of magnitude larger. **The reader's download must be the
program.** A 5-line stub passes every markup check in this directory — it is
the omission class that reads as correct.

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
- **Non-V2 BASIC dialects need a re-decode.** `tools/prg_links.sh`
  petcat-detokenises every `.prg` with default V2 mode. If the
  source program uses Simons' BASIC, Final Cartridge BASIC, Speech
  BASIC, Mighty BASIC, etc. (any of the `petcat -<dialect>` flags),
  the extension tokens come out as garbled bytes
  (`($64){CTRL-A}1,6` instead of `hires1,6`). The figcaption is the
  signal — when the print says "mit Simons-Basic" / "Final
  Cartridge" / etc., re-decode the `.prg` via the dialect flag:
  ```bash
  petcat -simon -- "issues/<YYMM>/prg/del/<name>.prg" \
    > "issues/<YYMM>/prg/<name>.txt"
  ```
  Then add `;version=<dialect>` (`;version=simons`, `;version=f` for
  Final Cartridge, etc.) as the SECOND line of the .txt, right after
  the `;<file>.prg ==ADDR==` opener. The generator uses that tag to
  pick the right tokeniser when materialising the binary download.
  Existing examples: `issues/8412/prg/simons-axo.txt`,
  `issues/8510/prg/xref simons bas..txt`. Full dialect list:
  `petcat -help | grep -E "Basic v[0-9]"`.

- **Hypra-Ass / Top-Ass source listings are NOT BASIC.** The
  extractor falls back to petcat for any `.prg` that starts at
  $0801 (BASIC's default load address), but Hypra-Ass and Top-Ass
  source files often live there too — and petcat then tokenises
  the 6502 mnemonics as if they were BASIC keywords, jamming them
  into their operands. Signals:
  - The figcaption labels the listing `Assembler-Listing` /
    `Assembler-Quelltext` / `Quellcode` (or any "Quelltext"
    variant).
  - The petcat-decoded `.txt` contains directive lines like
    `.ba 50000` / `.eq xadr=10` / `.by …` / `.wo …` mixed with
    mnemonic+operand pairs that got run-together (`stxstin`,
    `bcsspr`, `sbc#82`, `adc#1`).
  - The line numbers in the petcat output are NOT 10/20/30/… —
    Hypra-Ass uses 900/901/902/… / 1100/1110/1120/… style
    numbering.
  When you see those signals, **do not re-decode the .txt**. Mark
  the HTML instead:
  ```html
  <pre data-filename="<name>" data-name="…" data-assembler="hypra-ass"></pre>
  <div class="binary_download" data-filename="<name>.prg" data-name="…"></div>
  ```
  The generator routes through `tools/assembler_decode.py`
  (canonical) which knows the Hypra-Ass mnemonic table ($81–$B8 +
  `.`+token for directives). For Top-Ass, use
  `data-assembler="top-ass"`. CLI tool for manual inspection:
  `tools/hypra-ass-decode.py <file.prg>`.
  Precedents:
  - `issues/8604/85 Das Maß der Dinge.html` (`taktzyklen.src`)
  - `issues/8606/95 Endlich_ Hypra-Ass mit Datasette.html`
    (`hypra-ass_cass`)
  - `issues/8606/134 Von Basic zu Assembler (Teil 4).html`
    (BLOCK / SWAP)

## Remediation: Hypra-Ass / Top-Ass misclassified as BASIC

**Hard rule:** a shipping `.prg` may **NEVER** live in `prg/del/`
**when the reader needs the RAW BINARY download**. `del/` is for files
the site does not re-derive from anything else; the generator's
binary-download resolver won't expose a raw `.prg` sitting in `del/`.
So if the download the reader gets must be the raw binary (Hypra-Ass /
Top-Ass source, MSE binaries, compiled programs), the `.prg` must sit
directly in `issues/<YYMM>/prg/`.

**Clarifying exception — BASIC `.prg`s stay in `del/`.** This hard
rule does NOT contradict the normal BASIC flow. A BASIC listing ships
as `prg/<name>.txt` (petcat text) and its `.prg` companion is moved to
`prg/del/` **on purpose** — the reader's download is *materialised
from the `.txt`* via `petcat2prg`, so the raw `.prg` in `del/` is
never needed and correctly stays there. The hard rule only bites when
there is no `.txt` to materialise from and the raw binary itself is
the download.

### Signals of the misclassification

`tools/prg_links.sh` runs every `.prg` that starts at `$0801` through
petcat in default V2 mode. When the source is actually a Hypra-Ass
or Top-Ass listing, the extractor wrongly stashes the raw `.prg`
in `issues/<YYMM>/prg/del/<name>.prg` and emits a bogus
`issues/<YYMM>/prg/<name>.txt` companion. Tells:

- The `.txt` opens with `;<name>.prg ==0801==`.
- The body contains jammed lowercase mnemonic+operand tokens like
  `cpyverl`, `ldax80`, `bcsspr`, `stxstin`, `sbc#82`, `adc#1` —
  petcat tokenised the 6502 mnemonics as if they were BASIC
  keywords and ran them into their operands.
- Line numbers are Hypra-Ass style (`900/901/902/…` /
  `1100/1110/1120/…`), not BASIC's `10/20/30/…`.
- The article's figcaption labels the listing
  `Assembler-Listing` / `Assembler-Quelltext` / `Quellcode` /
  any `Quelltext` variant.

### Remediation steps

1. Promote the `.prg` out of `del/` and drop the bogus `.txt`:
   ```bash
   git mv issues/<YYMM>/prg/del/<name>.prg issues/<YYMM>/prg/<name>.prg
   git rm issues/<YYMM>/prg/<name>.txt
   ```
   (If the `.prg` is untracked, use plain `mv` instead of
   `git mv` — git refuses to mv an untracked path.)
2. Mark the article's `<pre>` with `data-assembler="hypra-ass"`
   (or `top-ass`) **AND** add a sibling
   `<div class="binary_download" data-filename="<name>.prg"
   data-name="…">` so the reader gets a download link.
   **Without the `binary_download` line the `.prg` is in the
   repo but invisible to readers — the page renders the listing
   text but no download link appears.**
   ```html
   <figure>
       <pre data-filename="<name>" data-name="…" data-assembler="hypra-ass"></pre>
       <figcaption>…</figcaption>
   </figure>
   <div class="binary_download" data-filename="<name>.prg" data-name="…"></div>
   ```
3. Beautify the edited article(s) with the project's standard
   `js-beautify` invocation, then rebuild the issue
   (`python3 generate.py --issues <YYMM>`) and verify:
   - `out/<YYMM>/<slug>.html` contains an
     `<aside class="downloads">…<a href="prg/<name>.prg">…</a></aside>`
     entry;
   - the rendered listing shows properly spaced mnemonics
     (`CPY VERL`, `LDA #$0D`, `STX STIN`) — never the
     run-together `cpyverl` / `ldax80` form.

### Why this matters: generator routing

`generate.py:683-698` (the `data-assembler` branch) picks the
raw-PRG decoder via
`assembler_decode.decode_prg_bytes(asm_bin)` iff
`<data_filename>.prg` is present in the scanned `prg/`. The
fallback path uses `assembler_decode.decode_bytes(asm_bin,
topass=False)` against the petcat-tokenised txt, whose
`format_hypra_ass_line` is **case-sensitive** on mnemonics —
the lowercase petcat output misses the table and the listing
comes out garbled. Never rely on the txt-fallback path for
Hypra-Ass / Top-Ass; promote the raw `.prg` instead.

### Canonical examples

- `issues/8606/95 Endlich_ Hypra-Ass mit Datasette.html` —
  `hypra-ass_cass.prg` (single source listing, single
  `binary_download` line).
- `issues/8607/142 Neues zum Thema Sortieren.html` —
  `quicksort.ass.prg` (assembler source sits next to a separate
  MSE compiled `.prg`; one `binary_download` line per file).
- `issues/8606/134 Von Basic zu Assembler (Teil 4).html` —
  BLOCK / SWAP precedent for the layout pattern (compiled `.prg`
  plus source `.prg` ⇒ two `binary_download` lines under one
  `<figure>`).

## Sanity-check every extracted file — a directory sector is not a program

8609 shipped `prg/video-experim..prg` as the master for *Listing 3. Eine
Befehlserweiterung, die den Video-Chip unterstützt*. It is not a program at all:
254 bytes, containing `$A0`-padded CBM directory entries (`FAK`, `XREF 7.0`) and
then zeros — i.e. a raw **directory sector** that the extraction wrote out under
a file name. It rendered as an MSE hex dump while the print shows BASIC, which
is how it was caught.

Checks worth running over every extracted `prg/`:

- **exactly 254 bytes** (a single sector, minus the two link bytes) is a red flag
- a run of `$A0` padding bytes in the first 32 bytes is a directory entry, not
  code or tokenised BASIC
- the load address (first two bytes, little-endian) should be plausible:
  `$0801` for BASIC, or the address the article/caption states
- the rendering must match what the print shows — a listing typeset as BASIC
  must not come out as an MSE hex dump, and vice versa
