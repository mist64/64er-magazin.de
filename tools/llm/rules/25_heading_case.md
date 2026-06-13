# 25 — Convert ALL-CAPS headings to German natural case

**Goal:** every `<h1>` and `<h2>` heading in the article HTML reads in
**German sentence case**: first character of the heading capitalised,
proper nouns + product names + abbreviations capitalised, everything
else lowercased. The OCR import sometimes delivers ALL CAPS because
the print typeset section headings in caps; this rule normalises
them to the project convention used since 8601.

The Leserforum h2 conversion is a special case of this rule but is
handled by rule 18 (Leserforum's import-time ALL CAPS → Title Case
is what 8601-8605 used; later issues moved to natural case). New
issues use **natural case for both** Leserforum and regular article
headings.

## DEFAULT: don't change heading text

Heading text is whatever the OCR'd / post-step-0 markdown produced.
**Default action: leave it.** Change a heading's case only when the
ALL-CAPS detection trigger below fires unambiguously.

Cross-reference: this mirrors rule 28's `DEFAULT: DON'T CHANGE HEADER
LEVELS` framing. Rule 28 protects heading *levels*; this rule
protects heading *text*. Both default to "trust the input"; both
reserve change for a mechanically-detectable trigger.

### "Predominantly ALL CAPS" trigger

A heading qualifies for re-casing iff **all** of the following hold:

1. Of all word-characters (letters) in the heading text, at least
   **80 %** are uppercase.
2. At least **3 of those uppercase characters appear in a row** (i.e.
   the regex `[A-ZÄÖÜẞ]{3,}` matches somewhere in the heading).

The 3-in-a-row clause excludes mixed-case headings where one
Umlaut OCR'd as upper, or where a 2-letter acronym (`DR`, `IM`) sits
adjacent to a real word — those are NOT predominantly ALL CAPS and
must be left alone.

### Anti-pattern

❌ **"This heading reads HARD on the screen, let me re-case it."**
That's an aesthetic call, not a print-typography decision. If the
print set the heading in mixed case, the OCR delivered mixed case,
and the 80 %/3-in-a-row trigger does not fire — leave it.

## What "German natural case" means

German sentence case is NOT English Title Case. The rules:

- **First word** of the heading: leading character capitalised, rest
  lowercase unless a proper noun / acronym / product name (rules
  below).
- **All other words**: lowercase unless:
  - **Nouns** — capitalised per standard German orthography (`Modem`,
    `Schnittstelle`, `Bilder`).
  - **Proper nouns / company names** — verbatim from print (`Comline`,
    `Springboard`, `Movie Monster`, `Microsoft`).
  - **Acronyms / abbreviations** — kept uppercase (`RS232`, `C 64`,
    `CMOS-RAM`, `MIDI`, `DOS`, `MPS`, `CP/M`, `DFÜ`).
  - **Product/brand model numbers** — verbatim (`8500`, `MP-1300 AI`,
    `CV 19.2`, `V.24`).
- **Hyphenated compounds**: each side capitalised per the rule for
  its part of speech (`Anti-Hacker-Modem`, `Sprach- und Datenmodem`,
  `Farb-Digitizer`, `Computer-Knobeleien`).
- **Umlauts / ß**: keep as in the lowercase form (`für`, `daß`,
  `Großbuchstaben`).
- **First word `Die / Der / Das / Ein / Eine`** when present —
  capitalised because it's the leading word.

## Examples (from the 8606 convention + 8607 fixes)

| ALL CAPS print/OCR | Natural-case HTML |
|---|---|
| `PROGRAMMIERBARES RS232/V.24-KABEL` | `Programmierbares RS232/V.24-Kabel` |
| `ERSTER FÄRB-DIGITIZER FÜR C 64` | `Erster Farb-Digitizer für C 64` (note: `FÄRB`→`Farb` is also an OCR fix per [[feedback-ocr-vs-typos]]) |
| `COMPUTERCAMP` | `Computercamp` |
| `PROFESSIONAL-1541-DOS` | `Professional-1541-DOS` |
| `COMIC-GRUSEL MIT MOVIE MONSTER` | `Comic-Grusel mit Movie Monster` |
| `ASSI/M-ASSEMBLER IN NEUER VERSION` | `ASSI/M-Assembler in neuer Version` |
| `ANTI-HACKER-MODEM` | `Anti-Hacker-Modem` |
| `NEUE BILDER FÜR DEN NEWSROOM` | `Neue Bilder für den Newsroom` |
| `LIBYEN-ANGRIFF UMGESETZT` | `Libyen-Angriff umgesetzt` |
| `TURBONIBBLER VERBESSERT` | `Turbonibbler verbessert` |
| `CMOS-RAM-PLATINE` | `CMOS-RAM-Platine` |
| `MODEM KONTRA AKUSTIKKOPPLER` | `Modem kontra Akustikkoppler` |
| `SIMULTANES SPRACH- UND DATENMODEM` | `Simultanes Sprach- und Datenmodem` |
| `DFÜ-NEWS: DATEX-P-PARAMETER` | `DFÜ-News: Datex-P-Parameter` |

## Briefing for the sub-agent

For every article HTML in `issues/<YYMM>/*.html`:

1. Find all `<h1>` and `<h2>` headings whose content is predominantly
   ALL CAPS:
   ```bash
   grep -nE '<h[12]>[A-ZÄÖÜẞ][A-ZÄÖÜẞ0-9 .,/&\-]+</h[12]>' issues/<YYMM>/*.html
   ```
2. For each match, decide the natural-case version per the rules
   above. Anti-memory: the proper nouns / product names come from
   reading the article body (or the scan if uncertain), not from
   memory. The body usually mentions the same product / company
   name in its lowercase form a few sentences in — match the
   article's own spelling.
3. Apply word-level OCR fixes encountered along the way (e.g.
   `FÄRB` → `Farb` because the lowercase form would have read
   `Farb-`, not `Färb-`; uppercase Ä was an OCR misread of A in
   the print's section banner typeface).
4. Replace each match.
5. Beautify (`npx --yes js-beautify …`).
6. **Rename the article HTML file to match the new h1.** Filenames
   are emitted by rule 5 (split.py) from the h1 text, so when rule
   25 lower-cases the h1 the filename also needs `git mv`. Match
   the natural-case form (e.g.
   `16 DER C 64 IN FORSCHUNG UND TECHNIK.html` →
   `16 Der C 64 in Forschung und Technik.html`). Strip-trailing-
   page-number convention from rule 5 still applies (`<startpage> <h1>.html`).
7. **Update the `<title>` tag too.** Rule 5 emits `<title>{h1_plain}</title>`
   from the same h1 text. When rule 25 rewrites the h1, the
   `<title>` lags behind unless it's updated in the same pass.
   Match `<title>` to the new natural-case h1.
8. **Do not commit.** Return per-article table of headings touched
   (before → after) + per-file rename log + `<title>` updates.

Critical guardrails:
- **Don't change non-ALL-CAPS headings.** A heading that's already
  in natural case (e.g. 8606's `Universeller Programmcompressor`)
  stays untouched.
- **Don't change `<h3>` Leserforum topic headings** — rule 18
  handles those (their convention historically was Title Case;
  going forward Leserforum h2s should also be natural case, but
  that's rule 18's call).
- **Don't change Fehlerteufelchen `<h3>` correction headings** —
  those are article-title references and follow the print's mixed
  case.

## Verification

```bash
dir=issues/<YYMM>

# 1. no h1/h2 left entirely in ALL CAPS
grep -nE '<h[12]>[A-ZÄÖÜẞ][A-ZÄÖÜẞ0-9 .,/&\-]+</h[12]>' "$dir"/*.html && \
  echo "  FAIL: ALL CAPS heading survived"

# 2. spot-check: every h1/h2 starts with a capital letter
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<h([12])>([^<]+)</h\1>', s):
        h = m.group(2).strip()
        if not h: continue
        first = next((c for c in h if c.isalpha()), None)
        if first and not first.isupper():
            print(f"  lowercase first letter in {f}: {h!r}")
PY
)" "$dir"
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every heading-case change the sub-agent applies must
be backed by **runnable verifier evidence pasted verbatim into the
report**:

- For each re-cased heading, paste the one-line `pdftotext` cross-
  check (rule 27's evidence form) showing the print's actual case at
  that position, e.g.
  ```
  pdftotext -layout -f 8 -l 8 issues/<YYMM>/64er_19XX-XX.pdf - | grep -i "PROGRAMMIERBARES RS232"
  ```
- For each retained proper noun / acronym / product name (`geoWrite`,
  `dBase`, `RS232`, `C 64`, …), paste the article-body grep showing
  that exact spelling in the prose, e.g.
  ```
  grep -h 'geoWrite' "issues/<YYMM>/<file>.html" | head -1
  ```
- For each `git mv` rename, paste the before/after filenames and the
  matching `<title>` update.
- For each OCR fix applied alongside the case change (`FÄRB` →
  `Farb`), paste the rule-27-style `pdftotext` cross-check showing
  the print actually has the corrected glyph.

**No verifier output, no claimed re-casing.** A heading change
reported without the `pdftotext` evidence is treated as a guess; the
orchestrator will re-dispatch. "Trust me, the proper noun is …" is
never acceptable.

## Notes / lessons

- The 8606 conventions (`Europäische Gemeinschaft für Computer-
  Spiele`, `Die Konzentration beginnt`, `Freeze Frame jetzt noch
  besser`) are the canonical reference. Match that style.
- Products / programs from the print stay with their exact
  capitalisation: `geoWrite`, `dBase II`, `CompuServe`, `Newsroom`,
  `Movie Monster`, `F-15 Strike Eagle`.
- Roman numerals in product names (`Pitstop II`) stay uppercase.
- 64'er-style Vornschriften (`C 64`, `C 128`, `VC 20`) keep their
  uppercase prefix + space + digit format verbatim.
- A heading that contains an OCR artifact like
  `DFÜ-<a href="NEWS:">NEWS:</a> DATEX-P-PARAMETER` needs the
  autolink stripped first (rule 26), then the heading case
  converted — running rule 26 before rule 25 avoids touching the
  same h1 twice.
