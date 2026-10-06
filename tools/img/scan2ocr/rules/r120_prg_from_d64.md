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
  the listings under them belong to: **`NN` is the PAGE the listings sit on.**
  Map it through `64er.pages`, not through a filename and not as a start page —
  on 8612, 54, 57 and 78 are listing pages *inside* articles 51, 52 and 74, and
  resolve only that way.
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

For Sonderhefte the file lives under the same root with the SH naming. An
issue published as two disks is `<YYMM>A.D64` / `<YYMM>B.D64` -- 8611 is two,
8612 is one; look, do not assume. Each `.D64` has a `.TXT` beside it.

**The Sonderheft names are NOT `<YYMM>A.D64`.** They drop the year and pad the
issue number to two digits, in a directory of the same shape: SH 3/86 is
`SH0X/SH03A.D64` and `SH0X/SH03B.D64`, SH 4/86 is `SH04A` through **`SH04D`**
— four disks, so "two" is not the ceiling either. `ls` the directory.

## Bare `petcat` is BASIC 7.0, and this rule used to say V2

petcat's own help is explicit: `-<version>` means *"use keywords for
`<version>` instead of **the v7.0 ones**"*. So the default is 7.0, and there
is no V2 unless `-2` is passed.

Confirmed empirically on VICE 3.9 with a one-line program whose only token is
`$E3`: bare `petcat` prints `10 gshape` (BASIC 7.0), `petcat -2` prints `10`
and drops it.

What that costs in practice, both seen on SH8603: C16 files came out readable
but **untagged** (`key5,"dsave"…dec(`), and a VC 20 file showed **C16
keywords**. Neither looks like a decode failure — the text is plausible — so
only check 4 exposed it. Pass the dialect explicitly for anything that is not
a C64 BASIC 7.0 program.

## A `.txt` IS BYTES, AND $A0 AFTER `REM` IS NOT `CLOSE`

A PETSCII listing is one byte per character, and a byte ≥ `$80` is a real
character. **`$A0` is the shifted space**, which the magazines use to pad a REM
banner to width.

**petcat emits it as the keyword `CLOSE`.** `$A0` is also the token for CLOSE,
and after `REM` petcat detokenises rather than passing the byte through:

| | |
|---|---|
| disk, SH8604 `der kl. hobbit` line 10000 | `8F 20 4D 4F … 20 20 A0` = `REM MOEGLICHE RICHTUNGEN` + padding + shifted space |
| petcat's `.txt` | `10000 rem moegliche richtungen    close` |

That is a **transcription error in a file we publish**, not a display quirk:
`generate.py` runs `petcat -w` over the `.txt` to build the downloadable
`.prg`, so the reader's download had `CLOSE` — five literal bytes — where the
program has one.

### OUTSIDE A QUOTED STRING, petcat INTERPRETS NO BRACE ESCAPE AT ALL

This is the one fact behind every round-trip surprise in this file, so it is
worth having on its own. MEASURED, tokenising with `-w2`:

| input | inside a string | outside one (bare body, or after `REM`) |
|---|---|---|
| `{$20}` | `20` | `5B 24 32 30 5D` — the literal text `[$20]` |
| `{$a0}` | `A0` | `5B 24 41 30 5D` — the literal text `[$A0]` |
| `{space}` | `20` | — |
| a raw `$20` as the whole body | — | **the line is dropped** |

petcat is not skipping a particular escape; once it is outside quotes it does
no escape processing whatever. Both defects below follow from that:

- **`$A0` after `REM`** is outside a string, so no escape reaches it and **the
  raw byte is the only way to express it** — which is why `generate.py` reads
  the listing and pipes it to petcat as **latin-1** rather than UTF-8 (both
  sites commented there);
- **a space-only line** is outside a string too, so no escape reaches it
  either, and the one byte that would work is the one petcat strips as
  trailing whitespace. It cannot be expressed at all. See *petcat's round trip
  is NOT loss-free*, below.

Measured for the encoding:

```
read utf-8   -> encode utf-8     UnicodeDecodeError: invalid start byte
read latin-1 -> encode utf-8     8F 20 41 42 C2 A0      <- two bytes, wrong
read latin-1 -> encode latin-1   8F 20 41 42 A0         <- correct
```

**Verify by regenerating, not by reading.** Tokenise the `.txt` and compare it
line by line with the file extracted from the D64 — that is the only check
that sees this. SH8604's Hobbit now matches the disk on all 702 lines, the one
difference being the `115 rem` the owner authorised from the 7/86
Fehlerteufelchen.

**Swept the corpus 2026-10-06** for a REM line ending in any BASIC keyword
after padding, which is the general shape: **two damaged lines, both in
`der kl. hobbit`**. SH8504's `etiketten.txt` line 3180 `rem      return` looks
identical and is **genuine** — the disk has `52 45 54 55 52 4E`, the six
letters, not a token. Check the disk before fixing one.

## petcat's round trip is NOT loss-free: a SPACE-ONLY line is dropped

**The known case, measured — and it is not what it first looks like.** A
`.prg → .txt → .prg` round trip through petcat can come back shorter, with a
cascade of differing bytes from the first divergence onward. On SH8604's
`1985/1986` that read as **5,932 differing bytes**; the real difference is
**two lines**.

The cause is a line whose body is a **single space** (`$20`):

```
 2260 print"wollen sie wirklich aufh$ren";:gosub3720
 2270                     <- body is one byte, $20
 2280 ifr$="n"thenprint:print"ich wu&te es.":goto2330
```

petcat's **detokeniser** writes the space out faithfully. petcat's
**tokeniser** strips trailing whitespace, sees an empty body, and **discards
the line**. Verified directly: feeding `10 print"a"` / `20 ` / `30 print"b"`
to `petcat -w2` produces lines 10 and 30 only.

**This is NOT an "empty line", and the distinction matters** because an empty
line is not enterable on a C64 — a bare line number DELETES the line. A line
number followed by a SPACE is a different thing and stores a one-byte body,
which is how these got onto the disk. Reading petcat's output as "nothing
there" instead of dumping the bytes is what made the first diagnosis of this
wrong; **go to the bytes.**

Measured on SH8604: `1985/1986` has 2 such lines, `lader` 1. Nothing `GOTO`s
or `GOSUB`s any of them, so the programs behave identically, and **our shipped
`.txt` keeps them**, so the archive is faithful to the disk. The loss happens
only if someone re-tokenises our `.txt` back into a `.prg`.

Owner, 2026-10-05: *"tiny difference and tiny bugs in print in the context of
MSE are just ok."* So a round-trip difference of this shape is recorded and
left; it is not a transcription error and not a print/disk divergence.

**What this means for check 4's round-trip test:** a length difference plus a
cascade is the SIGNATURE of a dropped line, not of a bad transcription.
Detokenise BOTH files and diff the text — the difference will be a handful of
lines, and if they are space-only lines you are done.

## Three shapes check 4's three cases do not cover

All three found on SH8603, with its own evidence:

1. **petcat's round-trip is not symmetric.** `$9A` detokenises to `{blu}` and
   re-tokenises under `-w3` to `$1F`. A re-tokenise that differs is not
   automatically a transcription error.

   **BUT EACH DIFFERENCE GOES TO THE OWNER WITH ITS OWN BYTE-LEVEL CAUSE —
   NEVER GROUPED UNDER A SHARED LABEL.** This is the one entry in SH8604's
   errata where **a reader's download was wrong**, and the grouping is how it
   happened. Three files round-tripped differently (`1985_1986`, `lader`, `der
   kl. hobbit`); they were filed together as "petcat asymmetries"; the cause
   offered for all three — a space-only line body — is true of the first two
   only. The owner closed all three on that cause, and the third shipped: `der
   kl. hobbit` lines 10000 and 60000 end a REM banner in `$A0`, the shifted
   space, which is also the token for `CLOSE`, so petcat wrote `close` into the
   `.txt` and the re-tokenise put **five literal bytes where the program has
   one**. The symptom was shared; the cause was not. Report each one with the
   hex of the disk bytes beside the hex of the re-tokenised bytes, and let the
   owner rule on each.

   **And a difference inside a REM or a quoted string where the disk byte is
   ≥ `$80` is a TRANSCRIPTION ERROR in a file we publish, until proven
   otherwise** — not an asymmetry. Above `$80` the byte is a token everywhere
   except inside REM/string, which is exactly where petcat's context is
   ambiguous (see *OUTSIDE A QUOTED STRING, petcat INTERPRETS NO BRACE ESCAPE
   AT ALL*). Treat it as our bug first and look for the proof, because
   `generate.py` re-tokenises our `.txt` to build the reader's download: a
   wrong `.txt` is a wrong `.prg` on the site.
2. **A BASIC extension petcat has no dialect for at all** — SH8603's *19
   Grafik-Befehle* for the VC 20. There is no flag to pass; the tokens have to
   be decoded from the article's own table.
3. **Real BASIC with machine code APPENDED** — `fast hardcopy`. This looks
   like case 3's "trailing bytes" and is not harmless: the appended block is
   part of the program and a reader needs it.

And check 4's stub test would wrongly flag `turbo-racer`, a 73-byte loader
with a bare `SYS` and no code appended, which is complete as printed.

## Read errors: see `r120_d64_errors.py`

`c1541 -extract` reports read errors **not at all** — on SH8604's SH04C, a
disk with two bad sectors, it printed four informational lines, exited 0 and
extracted the files; and `tools/prg_links.sh` sent even those to `/dev/null`.
The extracted file COUNT cannot stand in either: `c1541 -list | grep -c '"'`
reads 48 on the healthy SH03A against 27 files extracted, so a count
comparison flags a good disk.

The signal is in the image. A 35-track D64 is 683 × 256 = **174,848 bytes**;
one written by a tool that recorded read errors carries one status byte per
sector appended, so **175,531**. `r120_d64_errors.py` decodes that block, and
reads the BAM to say whether each bad sector holds anything. `prg_links.sh`
now runs it before extracting.

MEASURED over the Sonderheft disks on hand: six are 174,848 with no error info,
and SH04C is 175,531 with exactly 2 sectors at code 5 (*23 checksum error in
data block*), **both in free blocks** — so nothing extracted is affected, which
is a conclusion to record in LOG.md rather than one to assume from a silent
extract.

**Check the canonical path first and use it if it is there** -- VERIFIED
2026-10-01, the archive is mounted and holds `84XX` through `91XX`. Only when
it is absent is the source a question for the operator, because copies of the
same disk exist in other places (TOSEC archive, mirror folders, local
downloads) and `prg.txt` records which one was used.

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

**A RE-RUN REGENERATES `prg.txt` FROM SCRATCH.** Anything added to it by
hand is lost — and this step's own remediations are exactly that. 8611 had
to re-apply three of them after a fix to the extractor: the provenance
digests, a dialect re-decode (`screentest` as 7.0), and a stub promotion
(`sound-monitor` to raw binary). The digests are mechanical and the script
writes them itself now. The other two are per-file judgements and cannot be,
so **list every remediation in `LOG.md` as a re-apply checklist**, not as
prose: a re-run after any tool change starts from the wrapper's output and
walks that list.

**A PATH IS NOT PROVENANCE. Record the sha256 beside it.** 8610's `prg.txt`
opens `<!-- /private/tmp/64er_8610/disks/8610A.D64 -->`, and that file no
longer exists: it sat in `/private/tmp`, which the macOS cleaner sweeps after
three days. The line now points at nothing and nobody can tell which of the
several copies on this machine it was. A digest survives that, and it is the
only thing that actually identifies a disk:

```
<!-- 8611 side A: ~/DNB/8611/disks/8611A.D64
     sha256 622d2a7c032bd7c9…  174848 bytes -->
```

**And the images go somewhere durable before the extractor runs**, for the
same reason `<tmp>` does (r000, *the working directory must be DURABLE*).
`~/DNB/<ID>/disks/` beside the issue's other durable artefacts. They are
170 KB each; there is no reason to leave the only reference pointing into a
directory that gets deleted.

A note that said this root "does not exist on this machine at all" stood here
until 2026-10-01, when it did exist and had for some time -- written during a
build where it happened to be unmounted, and then believed. **A rule that
reports a path as missing must say WHEN it was checked**, or the next agent
inherits a wrong fact with no way to date it. Check, then trust what you see
over what this file says about your filesystem.

## Verification

```bash
# 1. The output exists.
ls issues/8607/prg/ | head
test -s issues/8607/prg.txt && echo "prg.txt OK"

# 2. Every section-separator comment matches the start page of some
#    article in the issue (otherwise listings will end up orphaned).
#    `--+` MISSES A SINGLE-DASH SEPARATOR: SH8604's disks carry
#    "-dateiverwaltung", which is a text separator and not a program, so
#    one dash has to match too.  Match the whole class, then eyeball.
grep -oE '"-+[^"]*"' issues/8607/prg.txt | sort -u
# Eyeball: each "----------NN" should map to a `NN ….html` in the issue.
# TWO SHAPES THIS CANNOT DECIDE FOR YOU, both measured on SH8604:
#   * a separator that is ALL dashes and no page number -- every SH04 disk
#     opens with a bare "----------------".  It is a section to check 3
#     below, so an unnumbered intro file under it passes as "placed" while
#     nothing has said where it goes.  Check 3 is vacuous on these disks;
#     do not read a clean orphan count as an answer.
#   * ONE section spanning TWO articles -- disk 40's section feeds both
#     Kuenstliche Intelligenz and Eliza.  The separator names one start
#     page; the files divide between two articles at step 130.

# 3. Cross-check: no <figure> block in prg.txt was emitted without a
#    section separator above it (orphan listing — would have no
#    article to place into):
$PY - issues/<YYMM>/prg.txt <<'PYEOF'
import re, sys
s = open(sys.argv[1], encoding='utf-8').read()
# A SECOND DISK SIDE RESETS THE SECTION. Without this, side B's files fall
# under side A's LAST separator and are counted as placed. MEASURED on 8611:
# side B has nine files and no separators of its own -- its whole directory
# sits under side A's "Achtung! Rueckseite bespielt" banner -- so the orphan
# count read 1 where the truth was 10, and the check that exists to find
# unplaceable listings reported the issue clean.
chunks = re.split(r'(<!--[^>]*"----+[^"]*"[^>]*-->|<!-- [^>]*\.[Dd]64[^>]*-->)', s)
section = None; orphan = 0; orphans = []
for c in chunks:
    if c.startswith('<!--'):
        section = None if '.D64' in c or '.d64' in c else c.strip()
        continue
    if '<figure' in c and section is None:
        orphan += c.count('<figure')
        orphans += re.findall(r'data-filename="([^"]+)"', c)
print(f"orphan figures (no section separator yet): {orphan}")
for o in orphans[:12]:
    print("   ", o)
PYEOF

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

## A DATA FILE TYPED `prg` ON THE DISK STILL GETS AN MSE PROPOSAL

The SEQ guard in `prg_links.sh` catches data files the directory marks `seq`.
It cannot catch a data file the directory marks `prg` — the disk is the only
thing that knows, and it says the wrong thing. MEASURED on SH8604: disk C holds
101 PRG-typed DATA files and every one came out of the extractor as a
`data-mse=mse1` figure proposal. Expect the pile, un-propose it at step 130,
and do not read 101 proposals as 101 listings.

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

## Four cases the extractor does not route correctly

Each of these was found on 8612 and fixed by hand; none is in the script.

- **BASIC at a load address not ending in `01`.** `find c128` loads at $242B.
  The extractor routes it to the PRG branch and `petcat` produces garbage.
  Relink the line pointers to $1C01, decode, and keep the real load address in
  the download.
- **A stub whose `SYS` is the FIRST statement.** The stub test ("fewer than 3
  content lines" plus "the last statement is a bare `SYS`") misses
  `4gewinnt meister`, where the `SYS` leads and CR-bearing text trails it. Treat
  a bare `SYS` **anywhere** in a short BASIC part as a stub; only check 4 caught
  this one.
- **A line-linked plain-ASCII assembler source.** `hyperscreen ii.s` is neither
  branch's shape: it has BASIC line links but ASCII assembler text. Decode the
  links, emit the text.
- **Re-decode debris.** The recipe leaves `;del/<n>.prg` entries and leading
  blank lines, which 8611's files do not have. Strip both.

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
  petcat-detokenises every `.prg` with **bare `petcat`, which is BASIC 7.0,
  NOT V2** — see *bare petcat is 7.0* below. If the
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

## `data-charset="lower"` — which display charset the listing was typed in

The C 64 has two character sets, and a listing does not say which one it
was written in: the bytes are the same either way, only the glyphs differ.

| byte range | UPPER/graphics (default) | LOWER/uppercase (text) |
|---|---|---|
| `$41-$5A` | `A-Z`                     | `a-z` |
| `$C1-$DA` | graphics glyphs           | `A-Z` |

An author who typed in the text charset therefore produces a listing that
the default reading renders **inverted**: the small letters come out as
capitals, and the capitals come out as Latin-1 garbage. 8610's Listing 3
decoded as

    ;*    ÐÒÏÇÒÁÍÍ 3 / ÍÏÄÕÌ 1    *
    ;*      ÅRWEITERUNG DER       *

where the print (p156) has

    ;*    PROGRAMM 3 / MODUL 1    *
    ;*      Erweiterung der       *

**The printed listing is the evidence.** Mixed case in the print, or those
accented capitals in the decode, means the text charset; declare it:

```html
<pre data-filename="<name>" data-name="…" data-assembler="hypra-ass"
     data-charset="lower"></pre>
```

Nothing in the bytes can be measured to decide this and nothing should try
to guess it — a listing with no lower-case letters at all reads identically
either way. Default is the graphics charset, which is what most listings
are. Known occurrences: 8610 `programm 3 quell` (p156-157), 8606
`hypra-ass_cass` (p95). `quicksort.ass` (8607) and `block`/`swap` (8606)
are graphics-charset and must stay so.

Hypra-Ass's own LIST prints a space between a short directive and its
operand (`.ba $5000`, `.eq forpnt=$49`) even when the source has none;
`decode_prg_bytes` reinserts it, the same way it splits a jammed mnemonic.

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
bare petcat, which is **BASIC 7.0 mode** (below). When the source is actually a Hypra-Ass
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
