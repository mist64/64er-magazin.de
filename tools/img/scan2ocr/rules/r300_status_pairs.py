#!/usr/bin/env python3
r"""r300: a status comment is a CLAIM ABOUT A FILE, so find the file that records it.

    $PY tools/img/scan2ocr/rules/r300_status_pairs.py issues/<ID>

An aside that says `Korrektur im Programm angewendet` while no program file
records the erratum is an always-GREEN mirror of a check that can never pass
(r000).  MEASURED on SH8608: article 108's aside said `Disk-Version bereits
korrigiert` while `prg/grafik c16.txt` carried no header note at all, and the
check that preceded this one was happy.

WHAT THIS CAN AND CANNOT ASSERT.  The HTML does not say WHICH listing a status
comment is about, and one aside may cite an erratum that corrected PROSE, which
no program file will ever record.  So it asks the weaker question it can answer
-- does ANY program record ANY of the errata this article cites -- which catches
"no record anywhere", the defect seen in the wild.  A wrong PAIRING still needs
a human.

AND A BINARY PROGRAM HAS NOWHERE TO PUT A HEADER COMMENT.  This is why the
check reads `reviewed/errata_status.txt` as well as `prg/*.txt`.  MEASURED on
SH09 article 113: 8612's Datev erratum is conditional on the reader's printer,
`prg/datev.prg` is a raw binary printed as an MSE hexdump, and the new status
comment `Bedingte Korrektur, nicht angewendet` therefore had NO file it could
be recorded in -- the check went red on a correct build, which is the defect
this rule keeps re-learning.  **Do not fabricate a `prg/<name>.txt` to satisfy
it**: generate.py renders `prg/*.txt` as a listing, so an invented text file
would ship to readers as a program.  The record goes in `reviewed/`, which is
whitelisted, durable, and already where dispositions live.

`issues/<ID>/reviewed/errata_status.txt`, one line per program and erratum:

    datev.prg<TAB>Fehlerteufelchen 12/1986<TAB>bedingt, nicht angewandt: the
    correction depends on the reader's printer, so it cannot be applied
    unconditionally

The named program must exist in `prg/`, or the line satisfies the gate while
naming nothing.
"""
import glob, os, re, sys

STATUS = ('Disk-Version bereits korrigiert',
          'Korrektur im Programm angewendet',
          'Bedingte Korrektur, nicht angewendet')
ERR = r'Fehlerteufelchen\s+(\d{1,2}/\d{4})'


def recorded(d):
    """{erratum: [where]} from prg/*.txt headers and reviewed/errata_status.txt."""
    out = {}
    for t in sorted(glob.glob(os.path.join(d, 'prg', '*.txt'))):
        for ln in open(t, encoding='utf-8', errors='replace'):
            # LEADING BLANK LINES COME FIRST IN THESE FILES.  Breaking on the
            # first line that is not a `;` comment read nothing at all: every
            # prg/*.txt in SH8606 opens with two empty lines before the
            # `;name.prg ==addr==` line.
            if not ln.strip():
                continue
            if not ln.startswith(';'):
                break
            for e in re.findall(ERR, ln):
                out.setdefault(e, []).append(os.path.basename(t))
    bad = []
    rv = os.path.join(d, 'reviewed', 'errata_status.txt')
    if os.path.exists(rv):
        for n, ln in enumerate(open(rv, encoding='utf-8'), 1):
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            parts = [p.strip() for p in ln.rstrip('\n').split('\t') if p.strip()]
            if len(parts) < 3:
                bad.append(f"reviewed/errata_status.txt:{n}: needs three "
                           f"tab-separated fields (program, erratum, disposition)")
                continue
            prog, err = parts[0], parts[1]
            if not os.path.exists(os.path.join(d, 'prg', prog)):
                bad.append(f"reviewed/errata_status.txt:{n}: names {prog!r}, "
                           "which is not in prg/")
                continue
            found = re.findall(ERR, err)
            if not found:
                bad.append(f"reviewed/errata_status.txt:{n}: {err!r} names no "
                           "erratum as `Fehlerteufelchen M/YYYY`")
                continue
            for e in found:
                out.setdefault(e, []).append(f"reviewed/ ({prog})")
    return out, bad


def main(d):
    d = d.rstrip('/')
    named, bad = recorded(d)
    checked = 0
    for p in sorted(glob.glob(os.path.join(d, '*.html'))):
        s = open(p, encoding='utf-8').read()
        if not any(st in s for st in STATUS):
            continue
        checked += 1
        cites = set(re.findall(r"<!--\s*64'er\s+(\d{1,2}/\d{4})", s))
        hit = cites & set(named)
        if cites and not hit:
            bad.append(f"{os.path.basename(p)}: carries a status comment citing "
                       f"{', '.join(sorted(cites))}, but no prg/*.txt header and "
                       "no reviewed/errata_status.txt line in this issue names "
                       "any of them")
        elif hit:
            print(f"  ok  {os.path.basename(p)}: {', '.join(sorted(hit))} "
                  f"recorded in {', '.join(sorted({w for e in hit for w in named[e]}))}")
    print(f"{d}: {checked} article(s) with a status comment, "
          f"{len(named)} erratum/errata recorded in files")
    if bad:
        print("\nFAIL")
        for b in bad:
            print("  *", b)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
