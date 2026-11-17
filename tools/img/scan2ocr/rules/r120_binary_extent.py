#!/usr/bin/env python3
r"""r120 check 5: does each RAW BINARY on the disk hold the whole printed program?

    $PY tools/img/scan2ocr/rules/r120_binary_extent.py issues/<ID> <tmp>/scratch_120/extent.txt

THE GAP THIS FILLS.  Check 4 round-trips every BASIC listing: the .txt must
re-tokenise to the .prg it came from, so a disk file that is not the printed
program is caught there.  A program that ships as a RAW BINARY has no .txt and
nothing to round-trip against, so until this check existed NO step compared a
binary disk file to its print at all -- not 120, not 130, not 190.

MEASURED, SH09 p119 `turbotapecopy.prg`: the disk file loads at $C700 and is
273 bytes of code, while the printed listing runs from $C350.  The disk holds
the last fifth of the program and does not run alone.  It was found at 130 by
an agent reading the page, by hand and by luck -- the kind of find that does not
happen twice.

WHAT IS AND IS NOT MECHANICAL.  The disk file's extent is exact: load address
from the first two bytes, end from the length.  THE PRINTED EXTENT IS NOT
MECHANICAL and this script does not pretend otherwise -- on p119 the OCR of the
MSE hexdump reads `c35@`, `c3588`, `cIID`, `c5d®`, so a min/max over OCR'd hex
columns would compare a correct disk file against a misread page and go red, or
worse, green.  A printed assembler or MSE listing names its own first and last
address in its header row; reading those two numbers off the page is two
glances, and that is what this check asks for.

So: the script derives the disk span, demands a printed span per binary, and
compares.  The gate fails on an UNANSWERED line, not only on a mismatch -- a
check that can only go red when someone has already done the reading is no
check at all.

THE ANSWERS, and `not printed` IS NOT ONE OF THEM ON ITS OWN:
  * `not printed`          -- the program is not in the magazine at all.  A
                              disk-only extra.  Silent.
  * `$C000-$C01A disasm`   -- printed, but with no `Name :` header: a monitor
                              disassembly, a BASIC loader, a screen dump.  The
                              span comes off the FIRST and LAST printed address.
                              Compared exactly like a header span.
  * `$C350-$C818 excl`     -- printed with a header, whose end is one past the
                              last byte.
  * any span + `; reason`  -- the spans DISAGREE and the difference is already
                              disposed of.  Reported, never counted, exactly as
                              check 4 honours a `;inkl. Fehlerteufelchen`
                              header.  The reason is the evidence, so it names
                              what the print says: MEASURED on SH09,
                              `format-system` prints a loader that pokes 1139
                              bytes to $0C73 and then `POKE 45,119:POKE 46,12`,
                              setting the end pointer to $0C77 -- so the disk's
                              four extra bytes (`33 2C 31 3F`) lie between the
                              printed DATA and the printed POINTER, and all
                              1139 bytes of program agree.
  * `no span` + a reason   -- printed, and the extent could NOT be established.
                              Stays RED.  This is the answer `not printed` was
                              being used for, and it is the one that matters:
                              MEASURED on SH09, six of thirteen `not printed`
                              lines were programs the magazine DOES print,
                              without a header -- `mse` (loader p100),
                              `format-system` (loader p59, disassembly p57-58),
                              `quicksort m 1` (loader p112), `spooling` (screen
                              dump p43), `c64.open.ass` and `c64.read_wr.ass`
                              (disassemblies p66, p68).  The check compared
                              nothing and said nothing, which is the vacuous
                              gate this file keeps re-learning (HARVEST 11, 19).
  * spans disagree         -- a difference that changes what the reader gets.
                              r300 disposes of it: an incomplete disk file is
                              not an erratum in the magazine, it is a defect in
                              OUR input, and the article needs r170 to recreate
                              the program from the print (SH09 p119).

AND THE TAIL WINDOW IS NOT WIDENED TO SWALLOW A SECOND PHENOMENON.  SH09's
`format-system` has a FOUR-byte tail, one past the window below, and its cause
is not a sector tail at all -- it is the end-of-BASIC pointer the printed loader
sets, four bytes past the data the printed loader writes.  One number standing
for two unrelated causes is a tolerance without a scale (HARVEST 16): widening
to 4 would also, silently, pass a program genuinely truncated by four bytes.
A second cause gets a REASON, not a bigger number.

A DISK TAIL OF ONE TO THREE BYTES IS THE DOCUMENTED CASE, NOT A FINDING.  A
.prg read off a D64 can carry bytes past the end of the program -- r120 measured
1 to 3 on every remaining BASIC "failure" across SH8606 and SH8608.  MEASURED
here: SH09's `c64.open.ass` and `c64.read_wr.ass` disassemblies stop at RTS,
2 bytes before the disk file's end, and `turbotapecopy.prg` carries one byte
($01 at $C810) past the printed end.  So a print end SHORT of the disk end by
1-3 bytes is reported and not counted -- and turbotapecopy stays red anyway,
on the 944-byte head it is missing, which is the difference that matters.
"""
import os, re, sys

HEX = r"\$?([0-9a-fA-F]{4})"

# WHOSE END IS IT.  An MSE or assembler header prints the end as one PAST the
# last byte -- `c0fd` for a program whose last byte is $C0FC -- while a disk
# span derived from load address and length is INCLUSIVE.  Comparing the two
# straight goes red by one byte on every correct binary, which is the
# cry-wolf defect this file's REM-only case already records.  So the answer
# says which convention it is in: an end written as the page prints it carries
# `excl`, and the script subtracts.  Transcribing the page verbatim and naming
# the convention is safer than hand-arithmetic on 28 lines.


def disk_span(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    if len(blob) < 3:
        return None
    load = blob[0] | (blob[1] << 8)
    return load, load + len(blob) - 3          # last byte of the program


def binaries(root):
    """Every listing in prg.txt that ships as a raw binary, in disk order."""
    text = open(os.path.join(root, "prg.txt"), encoding="utf-8").read()
    # The marker is the download <div>: a BASIC listing is served as text and
    # has none.  `data-mse` does NOT discriminate -- a BASIC listing carries an
    # MSE proposal too.
    out = []
    for m in re.finditer(r'<div class="binary_download"[^>]*data-filename="([^"]+)"', text):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out


def read_answers(path):
    """`<filename> <TAB> $start-$end | not printed | ?`"""
    answers = {}
    if not os.path.exists(path):
        return answers
    for line in open(path, encoding="utf-8"):
        # A `#` IS A COMMENT ONLY AT THE START OF A LINE.  SH09's disk carries
        # `c64.input#.prg`, and stripping from the first `#` anywhere truncated
        # its name to `c64.input`, so a line that HAD been answered read as
        # unanswered -- and the gate's whole point is that an unanswered line
        # is a failure.  Measured while testing this script.
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, _, rest = line.partition("\t")
        name, rest = name.strip(), rest.strip()
        # AN UNANSWERED LINE NEVER OVERWRITES AN ANSWER.  The script appends a
        # `?` line per unanswered binary, so a file can hold both -- in either
        # order, after a re-run.  Last-line-wins would silently discard the
        # reading someone just did.
        if rest in ("", "?") and answers.get(name):
            continue
        answers[name] = rest
    return answers


# A SEQ FILE HAS NO LOAD ADDRESS, SO IT HAS NO SPAN TO COMPARE.  This check
# reads the first two bytes of every binary as a load address; a sequential
# file is pure data -- a text, a table, a screen -- and its first two bytes are
# the first two bytes of that data.  Asked for a printed extent it demands one
# that does not exist, and an answer written to satisfy it would be a fiction.
# MEASURED: 20 of the 1,792 downloads in the published corpus are `.seq`.
# They are LISTED, with the reason, and not counted against the gate: silence
# would make the omission indistinguishable from a file nobody looked at.
def is_seq(name):
    return name.lower().endswith(".seq")


def main(root, answers_path):
    files = binaries(root)
    answers = read_answers(answers_path)
    rows, bad, missing = [], [], []
    seq = [n for n in files if is_seq(n)]
    files = [n for n in files if not is_seq(n)]
    if seq:
        print(f"  SEQ, no load address and therefore no span to check "
              f"({len(seq)}): " + ", ".join(seq))

    for name in files:
        p = os.path.join(root, "prg", name)
        span = disk_span(p) if os.path.exists(p) else None
        got = answers.get(name, "")
        rows.append((name, span, got))
        if not span:
            bad.append(f"{name}: no file in prg/ (or shorter than a load address)")
            continue
        if not got or got == "?":
            missing.append(name)
            continue
        if got.lower().startswith("not printed"):
            continue
        if got.lower().startswith("no span"):
            bad.append(f"{name}: printed, and its extent is not established "
                       f"-- {got[7:].strip() or 'no reason given'}")
            continue
        got, _, reason = got.partition(";")
        got, reason = got.strip(), reason.strip()
        m = re.match(HEX + r"\s*-\s*" + HEX + r"(\s+excl)?(\s+disasm)?$", got)
        if not m:
            bad.append(f"{name}: cannot read the printed span {got!r} -- "
                       "write it as $C350-$C818 (end INCLUSIVE), or "
                       "$C350-$C819 excl as the header prints it, or "
                       "`not printed`")
            continue
        ps, pe = int(m.group(1), 16), int(m.group(2), 16)
        if m.group(3):
            pe -= 1                     # the header's end is one past the last byte
        source = "disassembly" if m.group(4) else "header"
        ds, de = span
        if ds != ps or de != pe:
            short_head = ds - ps
            short_tail = pe - de
            if reason:
                # AN EXPECTED MISMATCH IS REPORTED AND NOT COUNTED (check 4's
                # convention).  The reason carries the evidence; a bare
                # "expected" is not one.
                print(f"  ok  {name}: disk ${ds:04X}-${de:04X}, print "
                      f"${ps:04X}-${pe:04X} -- expected: {reason}")
                continue
            if short_head == 0 and -3 <= short_tail < 0:
                # THE DISK FILE'S TAIL IS NOT PART OF THE PROGRAM (see r120's
                # check 4): reported, never counted.
                print(f"  ok  {name}: {-short_tail} byte(s) of disk tail past "
                      f"the printed end (${pe:04X}), {source} span")
                continue
            why = []
            if short_head > 0:
                why.append(f"the disk file starts {short_head} bytes INTO the "
                           "printed listing")
            if short_head < 0:
                why.append(f"the disk file starts {-short_head} bytes BEFORE the print")
            if short_tail > 0:
                why.append(f"and stops {short_tail} bytes SHORT of its end"
                           if why else
                           f"the disk file stops {short_tail} bytes SHORT of the "
                           "printed end")
            if short_tail < 0:
                why.append(f"and runs {-short_tail} bytes PAST the printed end"
                           if why else
                           f"the disk file runs {-short_tail} bytes PAST the "
                           "printed end")
            hint = ""
            if abs(short_tail) == 1 and short_head == 0:
                hint = ("  ONE byte: is this the header's end-exclusive "
                        "convention?  Write the span `excl` and re-run.")
            bad.append(f"{name}: disk ${ds:04X}-${de:04X}, print ${ps:04X}-${pe:04X}"
                       f" -- " + ", ".join(why) + hint)

    print(f"{root}: {len(files)} raw binaries on the disk")
    for name, span, got in rows:
        d = f"${span[0]:04X}-${span[1]:04X}" if span else "(no file)"
        print(f"  {name:34s} disk {d:14s} print {got or '?'}")

    if missing:
        # Write the worklist out so the reading can be recorded as it is done.
        os.makedirs(os.path.dirname(answers_path) or ".", exist_ok=True)
        with open(answers_path, "a", encoding="utf-8") as fh:
            if not answers:
                fh.write("# r120 check 5: the printed extent of each raw binary.\n"
                         "# <filename> TAB $start-$end        end INCLUSIVE "
                         "(the last byte of the program)\n"
                         "# <filename> TAB $start-$end excl   end AS THE HEADER "
                         "PRINTS IT, one past the last byte\n"
                         "# <filename> TAB $start-$end disasm  span off the "
                         "FIRST and LAST printed address (no `Name :` header)\n"
                         "# <filename> TAB not printed        not in the "
                         "magazine at all -- a disk-only extra\n"
                         "# <filename> TAB no span <reason>   printed, extent "
                         "NOT established -- stays red\n"
                         "# ... TAB $start-$end ; <reason>    the spans "
                         "disagree and the difference is disposed of; the "
                         "reason is the evidence\n")
            for name in missing:
                fh.write(f"{name}\t?\n")
        print(f"\n  wrote {len(missing)} unanswered lines to {answers_path}")

    if bad or missing:
        print("\nFAIL")
        for b in bad:
            print("  *", b)
        if missing:
            print(f"  * {len(missing)} binaries whose printed extent nobody has "
                  "read yet: " + ", ".join(missing))
        return 1
    print("\nOK -- every raw binary holds exactly what the page prints, or is "
          "recorded as not printed.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
