# 27 — Word-level OCR cleanup sweep across every article

**Goal:** after rule 5 (split) has produced one HTML per article, sweep
every `issues/<YYMM>/*.html` for the mechanical word-level OCR damage
that the import pipeline leaves behind: line-break hyphen rejoins,
character-level glyph confusions, and missing or extra spaces between
adjacent words.

This runs **once per issue** as a baseline cleanup. It does NOT do
heavy editorial OCR repair (dictionary lookup, hyphenation
correction by morphology rules, missing-punctuation insertion) —
those are issue #329 item 4 territory and the user explicitly
skipped them. Rule 27 only does the obvious, mechanical, word-level
substitutions the workflow's three passes cover.

## What word-level cleanup means

Per the [[feedback-print-verbatim]] memory and rule 0's cross-cutting
granularity rule:

- **In scope:** single-token substitutions where the surrounding
  text confirms the fix.
- **Out of scope:** rewriting a sentence, fixing print typos,
  changing old German spelling (`daß`, `muß`, `Adreß`).

Diagnostic test before every change: **count characters.** Same
count, different glyph at one position → OCR; fix. Different count
→ either a real OCR add/drop (rare) or a print typo (leave alone).

## Pass 1 — line-break hyphen artifacts

Find every `X-y` token where the second half starts lowercase:

```bash
grep -hoE '[A-Za-zäöüÄÖÜß]+-[a-zäöüß]+' issues/<YYMM>/*.html \
  | sort -u | head -200
```

Most are line-break artifacts: `Drucker` was printed at column edge
as `Druk-ker` and OCR'd as `Druk-ker`. Rejoin to `Drucker`. Also:

- **Old German `ck → k-k`**: `Druk-ker`/`Drük-ken`/`Tük-ken` →
  `Drucker`/`Drücken`/`Tücken`.
- **Multi-hyphen tokens** like `Sinclair-Com-puter` → only the LAST
  hyphen is the line break: `Sinclair-Computer`. Compound hyphens
  before that survive.
- **"X- und Y" enumeration**: `Hard-und` → `Hard- und`,
  `Adreß-oder` → `Adreß- oder`. The hyphen survived as a real
  compound hyphen; the space after it was lost.

Skip tokens whose right half starts uppercase or is digit-only — those
are genuine compounds (`Sub-D-Stecker`, `RS232/V.24-Kabel`,
`MPS-801`).

## Pass 2 — character-level confusions

Walk the article text and apply these only-when-context-confirms
substitutions:

| Pattern | Confusion | Examples |
|---|---|---|
| `U[a-zäöü]+` mid-word | U vs ll | `darsteUen` → `darstellen`, `eventueU` → `eventuell` |
| Initial `U` for `V` | U vs V | `Uerbesserungen` → `Verbesserungen`, `Uon` → `Von`, `uollen` → `vollen` |
| Digit `0` inside letter run | 0 vs O | `CL0SE` → `CLOSE`, `P0KE` → `POKE`, `T0 1000` → `TO 1000`, `0RD` → `ORD` |
| Digit `1` next to letters in code | 1 vs l | `peek(211)+l` → `+1`, `x=l` → `x=1`, `OPEN l,8` → `OPEN 1,8` |
| Capital `I` between lowercase | I vs l | `umherfIiegen` → `umherfliegen` |
| `Q[a-z]` mid-word | Q vs (J | `AQ)` → `A(J)`, `Qa/Nein` → `(Ja/Nein` |
| Stray `ö` for `o` | ö vs o | `geöWrite` → `geoWrite`, `Autöboot` → `Autoboot` |
| Stray `ä` | ä vs a or au | `äuf` → `auf`, `äussehen` → `aussehen` |
| Stray `Ä` for `A` in heading | Ä vs A | `FÄRB-DIGITIZER` → `Farb-Digitizer` (the uppercase Ä in print typeface was misread; the lowercase form is `Farb`, not `Färb`) |
| `<<` / `>>` | brackets vs « » | `»BASIC $B000<<` → `»BASIC $B000«` |
| Stray period | period vs space | `sicher.auch` → `sicher auch`, `Wer. selbst` → `Wer selbst`, `MSE.eingegeben` → `MSE eingegeben` |
| `rn` vs `m`, `cl` vs `d` | classic ligature breaks | `Pmsel` → `Pinsel`, `clas` → `das` (only when context unambiguous) |

## Pass 3 — missing or extra spaces

Find words with internal lowercase→uppercase boundaries:

```bash
grep -hoE '\b[a-zA-Z]+[A-Z]+[a-z]+\b' issues/<YYMM>/*.html \
  | sort -u | head -200
```

Most hits are legitimate CamelCase (`dBase`, `KByte`, `geoWrite`,
`CompuServe`, `HiRes`, `MHz`, `gePOKEt`, `geSAVEt`, …) — skip those.
Real fixes look like:

- `derComputerdabeiist` → `der Computer dabei ist`
- `reichtderC 16` → `reicht der C 16`
- `aufPapier`, `aufBand`, `aufDiskette`, `aufIhre` → `auf Papier`, …
- `MitjedemdieserProgram-me` → `Mit jedem dieser Programme` (also
  has a hyphen artifact)
- `STOPTaste` → `STOP-Taste` (compare `RESTORE-Taste` if already
  correct nearby)

Run-together short words: `injedem` → `in jedem`, `Nachjeder` →
`Nach jeder`, `Beieinem` → `Bei einem`, `derjetzigen` → `der
jetzigen`, `ImJa-nuar` → `Im Januar`.

**Number/word boundaries:** `300,1200/75, 75/1200und` →
`300, 1200/75, 75/1200 und` (digits-then-letters with no
intervening space is almost always a missing-space artifact).

**Hyphen + word run-together:** `Übertragungsgeschwindigkei-tenvon300`
→ `Übertragungsgeschwindigkeiten von 300` (combines Pass 1 rejoin
+ Pass 3 space insertion).

The `C 64II` / `»C 641«` pattern: `C 64II` → `C 64 II`, `»C 641«`
→ `»C 64 I«` (digit `1` misread of Roman `I`, plus lost space).

## Pass 2 hard exception: hex addresses and binary code

The `0`/`O` and `1`/`l`/`I` substitution rules from Pass 2 **must
NOT apply inside hex literals or assembler addresses**. Hex digits
use the characters `0`-`9` and `A`-`F`; the letter `O` is not a
valid hex digit. The same applies to binary digit `1`.

**Skip Pass 2 substitution when:**
- The token starts with `$` (assembler/hex literal: `$C0FE`, `$0801`,
  `$E000`, …) — the `0`s are digits, leave them.
- The token is inside a `<td>` cell whose surrounding row contains
  assembler mnemonics (`STA`, `LDA`, `JSR`, `JMP`, `RTS`, etc.) —
  the cell content is code, not prose.
- The token is part of a number written without `$` but in a context
  that's clearly numeric (an octal byte sequence, a memory dump line
  like `1E15 20 00 23`).

8607 regression caught: `<td>STA $C0FE,X</td>` was rewritten to
`<td>STA $COFE,X</td>` by an over-eager Pass 2 sweep. The fix is
the substitution rule itself — **lookback** to confirm the token is
prose, not code, before applying `0`→`O`.

## What NOT to touch

Per [[feedback-ocr-vs-typos]] and the print-verbatim rule:

- Old German orthography (`ß`, `daß`, `muß`, `Adreß`, elided
  double-L like `Schnellade`).
- Original print typos (`Prinzessinen`, `Anwätte`, `Egentlich`,
  `Löewe`, `Letzendlich`, `Nahrungsmittteln`).
- Reversed `»` ↔ `«` direction errors in original print (the
  guillemets `»…«` open and close in fixed positions; if you see
  `»disk»` (both right-pointing), that is an original typo).
- CamelCase product/jargon names (`dBase`, `geoWrite`, `HiRes`,
  `CompuServe`, `StarDatei`, `ProDisc`, `FrameGrabber`, `GenLock`,
  `gePOKEt`).
- BASIC code variable names that look like substitutions but are
  deliberate (`zahl1`, `zahl2`).
- The `[NNN-NNN]` page-range markers at the end of headers.
- `<address class="author">` content (per
  [[feedback-print-verbatim]] — bylines are never edited).

When unsure, **leave it**. Faithful OCR with original typos
preserved is more valuable than a "corrected" rewrite that
modernises print artefacts.

## Briefing for the sub-agent

The sub-agent must:

1. Run Pass 1 (hyphenated tokens) across every `issues/<YYMM>/*.html`.
   Build a per-article list of fix candidates first, then apply via
   small Python script with explicit `FIX = {old: new}` mapping (so
   the change is reviewable).
2. Run Pass 2 (character confusions) — same approach.
3. Run Pass 3 (missing spaces) — same approach.
4. After each pass, re-run the detection regex to see what
   remains. Don't loop indefinitely; two passes of each is enough.
5. Beautify touched files at the end.
6. **Do not commit.** Return a per-article fix count + sample
   substitutions per article (no need to list every fix — the count
   + 5-10 samples is enough for the orchestrator to spot-check).

The sub-agent should explicitly NOT touch `<address class="author">`,
`<pre>`, `<code>`, or `<meta>` content. Body `<p>`, `<h1>`/`<h2>`,
`<li>`, `<td>`, `<figcaption>` are in scope.

## Verification

```bash
dir=issues/<YYMM>

# 1. obvious hyphen-rejoin candidates remaining
grep -hoE '[A-Za-zäöüÄÖÜß]+-[a-zäöüß]+' "$dir"/*.html | sort -u | head
# review by hand — most remaining should be genuine compounds.

# 2. obvious lost-space candidates remaining
grep -hoE '\b[a-zA-Z]+[A-Z]+[a-z]+\b' "$dir"/*.html | sort -u | head
# legitimate CamelCase only.

# 3. spot a known fix landed
grep -h "Übertragungsgeschwindigkeiten von" "$dir"/*.html >/dev/null && \
  echo "  Übertragungsgeschwindigkeit … fix landed ✓"
```

## Notes / lessons

- This rule runs ONCE per issue, right after rule 5 (split). It
  produces one big commit with many small word fixes; commit it
  separately so the diff is reviewable.
- Word-level only — see rule 0's "OCR cleanup granularity"
  cross-cutting rule and [[feedback-print-verbatim]]. Re-typing a
  sentence "more clearly" is forbidden even if every word change
  individually looks plausible.
- Pass 1 over-fires on tokens like `C 64-Modus` and `RS232/V.24-Kabel`
  if the right-half tokenisation is sloppy. Use the
  starts-with-lowercase filter and skim the candidates before
  applying.
- 64'er-specific known-typo list (do NOT "fix"): `Prinzessinen`,
  `Anwätte`, `Egentlich`, `Löewe`, `Letzendlich`, `Nahrungsmittteln`,
  `Schnellade` (elided LL), `Phytagoras` (in 49 Variosystem's
  C.A.C. box), `Course of live` (also Variosystem).
- The discount engine's older `<` escaping sometimes leaves stray
  `&lt;` constructs (`<RETURN>` becomes literal text) — those are
  rule-2 (escape_tags) territory, not rule 27.
