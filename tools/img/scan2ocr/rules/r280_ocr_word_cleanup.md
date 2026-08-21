# 280 — Word-level OCR cleanup sweep across every article

**Goal:** after rule 080 (split) has produced one HTML per article, sweep
every `issues/<YYMM>/*.html` for the mechanical word-level OCR damage
that the import pipeline leaves behind: line-break hyphen rejoins,
character-level glyph confusions, and missing or extra spaces between
adjacent words.

This runs **once per issue** as a baseline cleanup. It does NOT do
heavy editorial OCR repair (dictionary lookup, hyphenation
correction by morphology rules, missing-punctuation insertion) —
those are issue #329 item 4 territory and the user explicitly
skipped them. Rule 280 only does the obvious, mechanical, word-level
substitutions the workflow's three passes cover.

## What word-level cleanup means

Per the r000 "OCR cleanup granularity" memory and rule 000's cross-cutting
granularity rule:

- **In scope:** single-token substitutions where the surrounding
  text confirms the fix.
- **Out of scope:** rewriting a sentence, fixing print typos,
  changing old German spelling (`daß`, `muß`, `Adreß`).

Diagnostic test before every change: **count characters.** Same
count, different glyph at one position → OCR; fix. Different count
→ either a real OCR add/drop (rare) or a print typo (leave alone).

## OCR vs print typo: character-count heuristic

**The rule.** OCR is a character-level substitution / spacing
operation: glyph confusion, line-break hyphen artifacts, lost
spaces. It does NOT add or drop letters. If a candidate has the
wrong number of letters compared to the German-correct form,
that's a print typo, not OCR. **Leave it.** Apply this heuristic
FIRST; if the candidate fails it, skip — don't even open the block index.

**Valid OCR fixes** (same character count, or pure spacing / hyphen):

- `Druk-ker` → `Drucker` (old German line-break `ck` → `k-k`)
- `Uer` → `Ver`, `Uor` → `Vor` (U ↔ V)
- `0` ↔ `O`, `1` ↔ `l`/`I` (digit/letter glyph confusion)
- `Ghrom` → `Chrom` (G ↔ C)
- `Pmsel` → `Pinsel` (`m` ↔ `in` ligature break)
- `ausjedenfalls` → `aus jedenfalls` (lost space)
- `C 64II` → `C 64 II` (lost space)
- `Sinclair-Com-puter` → `Sinclair-Computer` (trailing line-break
  hyphen drops; leading compound hyphen stays)

**NOT OCR (leave alone)** — character counts disagree:

- `internsiv` (extra `r` vs `intensiv`) — canonical 8607/21 example
- `Akkumulatorl)` (extra trailing `l`) — 8607/139
- `Prinzessinen` (missing `n`), `Anwätte` (`lt` ↔ `tt`),
  `Egentlich` (missing `i`), `Löewe` (extra `e`)
- `muß`, `daß`, `Adreß` (old German spelling, not a typo)

**Compound-hyphen note.** For `X-Y-z` where final `z` starts
lowercase, only the LAST hyphen is the OCR line-break; keep
leading compound hyphens. `Sinclair-Com-puter` →
`Sinclair-Computer` (NOT `SinclairComputer`).

**Lost-space heuristic.** A lowercase→capital boundary inside a
word (`derComputer`), or concatenated short German words
(`derComputerdabeiist`), are lost spaces from OCR — DO fix those.
The rejoined form matches the German letter count; only spacing
changed.

## Mandatory pre-fix check: the two-engine cross-check

This is the **second** gate. The character-count heuristic above is the first;
only candidates that survive it reach this step. Before applying **any**
word-level candidate in Pass 1, Pass 2 or Pass 3, confirm against an
independent reading that the print does not carry the same anomaly.

**Not `pdftotext`.** The delivered PDF's text layer is a re-OCR of the same
scan, so it reproduces our own OCR's errors and can never say "print typo" --
see r000, "the PDF has no usable text layer". This is not a theoretical
objection: rule 280 once "confirmed" `WerhatErfahrungen mitdem` as
print-faithful because `pdftotext` returned the same jam, while the 600 dpi
scan plainly prints "Wer hat Erfahrungen mit dem".

The independent reading is **step 010's block index** -- a *different OCR
engine* on the same paper:

```bash
OUT_DIR=$(python3 -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.OUT_DIR)')
grep -i '<candidate-word>' "$OUT_DIR/blocks/p<NNN>.txt"
```

Read the disagreement, not the agreement:

- the two engines **drop different spaces or read different glyphs** -> the
  print has whatever the disagreement reveals. Apply the fix.
- both engines produce the **same** oddity -> that is weak evidence for a print
  typo and strong evidence of a shared failure mode (same paper, same screen,
  same broken letterform). It does NOT authorise "leave (print typo)".
- anything still ambiguous -> a **600 dpi crop of the master** at the block's
  bbox, read with your own eyes. That is the only source that settles it:

```bash
grep '<candidate-word>' "$OUT_DIR/blocks/p<NNN>.txt"     # gives bbox=WxH+X+Y
magick <SRC_DIR>/<NNN>.png -crop <W>x<H>+<X>+<Y> +repage /tmp/64er_check.png
```

`<SRC_DIR>` is the graded 600 dpi master, a constant at the top of
`r010_ocr_blocks.py`. The bbox is in that image's pixels -- never crop a PDF
render, the two spaces differ by a rotation and an offset.

The `internsiv` precedent (leave it) stands only on a reading that is actually
independent. It must be settled by the scan, never by a circular proxy.


Decision rule:

- The block index shows a **different** word matching the proposed fix -> the
  two engines disagree, the print has the correct word, **apply the fix**.
- The block index shows the **same** oddity -> undecided, NOT confirmed. Two OCR
  passes over the same paper share failure modes, so agreement is not evidence.
  Settle it on a 600 dpi crop before writing anything.
- The crop shows the oddity in print -> **it is a print typo. Do not touch.**

That middle branch is the one that used to be wrong. It read "the proxy agrees,
therefore the print says it", which is how a shared OCR failure gets recorded as
a 1986 typo.

### Anti-pattern: "it's not a German word, so it must be OCR"

This is the trap that produced the 8607/21 `internsiv` regression. The
1986 magazine **has print typos**, including non-words. The fact that
a token isn't in the German dictionary is **not** evidence that the
HTML is wrong — it is, at best, a signal worth checking. The decision
between "fix" and "leave" is always made against the scan, never by
dictionary lookup alone.

Canonical example to remember:

- **`internsiv`** in `issues/8607/21 Die Würfel sind gefallen.html`
  on page 176. Pass 1 candidate `internsiv` → `intensiv` looks
  irresistible; leaving it alone was the right call.

  ⚠️ The evidence originally recorded for it was a `pdftotext` reading, which
  this rule now treats as void. The *lesson* stands on its own — a non-word is
  not proof of an OCR error — but the finding itself has never been settled
  against the scan. **Re-verify it on a 600 dpi crop before citing it as
  precedent for leaving another token alone.**

The same applies to jammed-together compounds. 8607/33's `Derdritte`
and `angeschlossenwerden`, 8607/28's `aufgebautwerden`, 8607/49's
`kannjetztzwischendeneinzelnen`, and 8607/139's `Akkumulatorl)` were
all proposed Pass 1/Pass 3 fixes that were left alone on a `pdftotext` reading.
⚠️ Same caveat as `internsiv`: that evidence is void under this rule, so these
are *undecided*, not confirmed print typos. Leaving them alone remains the safe
default -- a fix needs positive evidence, a leave does not -- but do not cite
them as confirmed until a crop settles them.

### Verification step at the end of every Pass 1 / Pass 2 / Pass 3 candidate

```bash
OUT_DIR=$(python3 -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.OUT_DIR)')
grep -i '<word>' "$OUT_DIR"/blocks/p<NNN>.txt
```

If the block index returns the **corrected** form, the two engines disagree and
the fix is authorised. If it returns the same oddity, the candidate is
undecided -- settle it on a 600 dpi crop or leave it.

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
| Final-position `l` for `t` | t vs l | Lowercase typewriter `t` with hooked descender OCRs as `l`, especially at word end: `Mini-Autostarl` → `Mini-Autostart` (8607/76). The common shape is `…stt` mis-read as `…sl`. Apply only when the t-form is a known German / 64'er-jargon word AND the l-form isn't (eyeball check, not memory): `Autostarl` is not a word, `Autostart` is. Same context-confirms test as the other Pass-2 substitutions. |
| `]` for `1` | serif 1 vs ] | The serif digit `1` in this typeface is regularly read as `]`. Sweep `grep -n ']' ` over the whole issue, not just figure references — 8609 had 27, 8608 zero, so it is scan-specific and easy to miss entirely. Hits look like `Bild ]`, `Listing ]`, `Tabelle ]`, `(0 oder ])`, `VR]`, `CHR$(n])`, `($D60])`, `1541/70/7]`, `Monitor 190]`, `33] Seiten`, `&lt;]>`. Confirm the digit rather than assuming `1`: check the article's own figure list (a `Bild ]` in an article whose captions run Bild 1–3 is only `Bild 1` if the sentence fits Bild 1), or read the line on the scan. |

## Pass 3 — missing or extra spaces

Find words with internal lowercase→uppercase boundaries:

```bash
grep -hoE '\b[a-zA-Z]+[A-Z]+[a-z]+\b' issues/<YYMM>/*.html \
  | sort -u | head -200
```

**CRITICAL: the capital-boundary regex above misses the most common
jam class — lowercase-into-lowercase** (`dernoch`, `Sokann`,
`Beieiner`, `wurdeindenC`, `denEEinsteig`, `Computereizu`,
`neu zuladen`). These have NO internal capital, so the regex is blind
to them, and an 8608 review found ~20 shipping after a Pass-3 run that
relied on this regex alone. You MUST also detect these two ways:

1. **Function-word-pair grep** — jams almost always fuse a short
   function word to its neighbour. Sweep for a function word buried
   inside a token (no space before/after it):
   ```bash
   grep -hoE '[a-zäöüß]{3,}(dem|den|der|die|das|ein|eine|und|oder|nicht|auch|nur|noch|man|sich|ist|zu|jeweils|keiner|gemacht|sein|ich|schon|hat|mit|von|auf|für)([a-zäöüß]|C 6|C 1)' \
     issues/<YYMM>/*.html | sort -u
   # and its mirror (function word + following word):
   grep -hoE '(auf|mit|von|für|der|die|das|den|dem|ein|und|zu|so|da|bei|im|nach|wie)[a-zäöüß]{4,}' \
     issues/<YYMM>/*.html | sort -u
   ```
   Each hit still goes through the two-gate procedure (char-count +
   ground truth) — many are legit compounds (`aufwendig`, `damit`,
   `sobald`, `dabei`) so DO NOT apply blind.
2. **Word-stream diff against step 010's block index** (the most complete
   method): tokenise the article body and the corresponding
   `<OUT_DIR>/blocks/p<NNN>.txt` and flag every position where the two
   OCR engines disagree on a space. A disagreement is proof the print
   has a boundary there (two engines never independently invent the
   same split); settle the exact form with the block text or a crop.

Because the two OCR engines sometimes drop the SAME space (the 8608
`wurdeindenC 64ein` case — neither engine spaced it), the blocks index
alone can't catch everything; a 600 dpi scan crop is the final
tiebreaker for any function-word jam the greps surface.

3. **aspell non-word + function-word-split detector (PREFERRED — run
   this first).** The greps in method 1 are noisy (every `damit`,
   `sobald`, `aufwendig` fires). A far cleaner automated sweep: take
   every prose token, keep only the ones a German spell-checker rejects,
   and among those flag the ones that split into two valid pieces where
   one piece is a function word. That combination — *not a real word*
   **and** *splits around a function word* — is almost always a genuine
   lost-space jam, with very few false positives. This one pass found
   **69 real jams in 8608 that all three earlier methods had missed**
   (the R1 rule-280 sweep, the capital-boundary regex, and the
   function-word greps). hunspell on macOS/Homebrew usually has NO
   dictionary installed (`Can't open affix or dictionary files for
   dictionary named "de_DE"`) — use **`aspell -d de`** instead
   (`brew install aspell`; it ships the German dictionary).

   ```python
   # tools: aspell -d de (NOT hunspell — no dict on brew)
   import re, glob, subprocess, os
   os.chdir('issues/<YYMM>')
   words = {}
   for f in sorted(glob.glob('*.html')):
       s = open(f, encoding='utf-8').read()
       body = re.sub(r'<(pre|code|style|script|address)\b.*?</\1>', '', s, flags=re.S)
       body = re.sub(r'<[^>]+>', ' ', body); body = re.sub(r'&[a-z]+;', ' ', body)
       for w in re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*", body):
           words.setdefault(w, set()).add(f)
   def miss(wl):  # aspell list-mode: echoes only the words it does NOT know
       p = subprocess.run(['aspell','-d','de','--encoding=utf-8','list'],
                          input='\n'.join(wl), capture_output=True, text=True)
       return set(p.stdout.split())
   bad = miss(sorted(words))
   FW = set('der die das den dem des ein eine einen einem einer und oder aber '
            'ist sind war hat man sich noch schon nur auch für mit von zu auf an '
            'im am nach bei so da dann hier dort bereits jede jeder kann muß soll '
            'wird will sei uns ihm ihn sie es dies wie'.split())
   cand = [w for w in sorted(bad) if len(w) >= 7 and w.isalpha()]   # see blind spots below
   pieces = {p for w in cand for i in range(3, len(w)-2) for p in (w[:i], w[i:])}
   badpc  = miss(sorted(pieces))                                    # ONE batched call, not per-word
   for w in cand:
       for i in range(3, len(w)-2):
           a, b = w[:i], w[i:]
           if len(a) >= 2 and len(b) >= 2 and a not in badpc and b not in badpc \
              and (a.lower() in FW or b.lower() in FW):
               print(f'{w:24} = {a} + {b:12} :: {sorted(words.get(w, []))}'); break
   ```

   Then pull the on-page context for each hit (`grep -n`) and eyeball
   the split before applying — a handful are false positives you must
   SKIP: valid closed compounds the dict happens to miss
   (`ausliegen`, `durchprüft`, `durchstrukturiert`, `voreinstellbar`),
   **old-spelling forms** (`wieviel`, `jedesmal` — LEAVE per
   r280 "it's not a German word, so it must be OCR"), company/product names (`Profisoft`),
   Comal/BASIC variable identifiers (`MEINGABE`), and all-caps module
   names (`NEBENMODUL`). Everything else — `aufihre`, `istjede`,
   `dassonst`, `Somerktder`, `bereitshohe` — is a real lost space:
   re-insert it (both words are physically present in the fused token,
   so it is mechanical, not composition — no anti-memory violation).

   **Three blind spots — cover them with a targeted grep / a scan read:**
   - *Tokens shorter than 7 chars* are filtered out (`nurim`, `desC`,
     `soneu`, `Aderan`). Lower the threshold or grep the short
     function-word pairs directly.
   - *Jams where one half is itself a valid-but-not-in-dict compound*
     never satisfy "both pieces valid" (`Sortierprogrammtun` =
     Sortierprogramm+tun, `Zeitinvestiertwerden`, `Zuletztseinoch`).
     Catch these by greping for a bare function word / finite verb glued
     to the END of a long token (`…tun`, `…werden`, `…man`, `…noch`).
   - **Jams that are themselves a valid German word** — NO spell-checker
     (aspell, hunspell, this detector) can EVER flag them, because the
     fused token passes the dictionary. `Inder` is a real word (an
     Indian) hiding `In der`; likewise `Sieirgend`, `dasjenige`-lookalikes.
     8608 shipped a whole `…in`-class (`späterin`, `Meternin`, `Stellungin`,
     `Inder Tat`) that every automated sweep missed. **Only reading the
     prose in context / against the scan catches this class** — it is not
     a tooling gap you can close, it is why an automated pass alone is
     never sufficient.
   All three are why a single automated pass is never enough — always
   finish with a **contextual read** of the prose plus the method-2
   blocks-index diff and a scan spot-check.

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

Per r280 "it's not a German word, so it must be OCR" and the print-verbatim rule:

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
  r000 "OCR cleanup granularity" — bylines are never edited).

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

For **every** candidate in Pass 1 / Pass 2 / Pass 3 the decision
procedure is:

1. **Character-count heuristic** (see section above). If the
   candidate would add or drop letters vs the German-correct form,
   it's a print typo. Skip — do not even open the block index.
2. **Two-engine cross-check** (see mandatory pre-fix check). Only
   if step 1 says "looks like OCR" does the agent grep the block
   index and decide fix vs skip from what it returns.

The sub-agent should explicitly NOT touch `<address class="author">`,
`<pre>`, `<code>`, or `<meta>` content. Body `<p>`, `<h1>`/`<h2>`,
`<li>`, `<td>`, `<figcaption>` are in scope.

## Evidence-in-report requirement

The `internsiv` regression happened because a prior sub-agent claimed
to have verified each fix against the print but actually skipped the
check. To make that failure mode impossible, every Pass-1 / Pass-2 /
Pass-3 fix the sub-agent applies must be backed by **runnable verifier
evidence pasted verbatim into the report**:

- For each candidate the sub-agent decided to fix, include the one-line
  block-index command + its grep output (showing the other engine read the
  **corrected** form), e.g.
  ```
  grep -i intensiv "$OUT_DIR"/blocks/p176.txt
  →  Bedienung des C 64'er sehr intensiv lesen
  ```
- For each candidate the sub-agent decided to SKIP, include the same one-line
  command + its output, e.g.
  ```
  grep -i internsiv "$OUT_DIR"/blocks/p176.txt
  →  block=42 label=body ... text= Bedienung des C 64'er sehr internsiv lesen
  ```
  Both engines reading it the same way is a SKIP, not a confirmation -- report
  it as undecided, and say so in the summary.

**No verifier output, no claimed fix.** A fix reported without the
block-index line is treated as un-applied; the orchestrator will revert
it and re-dispatch. "Trust me, I checked" is never acceptable. Skipping
a candidate is acceptable; claiming an unverified fix is not.

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

- This rule runs ONCE per issue, at its numbered position (280) — AFTER
  the table/listing transcription rules (160/170) so their transcribed
  text is also swept. (An earlier draft said "right after rule 080
  (split)"; that was wrong — running before 13/14 would miss all
  transcribed body text.) It produces one commit with many small word
  fixes; commit it separately so the diff is reviewable.
- Word-level only — see rule 000's "OCR cleanup granularity"
  cross-cutting rule and r000 "OCR cleanup granularity". Re-typing a
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
  rule 050 (escape_tags) territory, not rule 280.
- **t ↔ l word-end pair (8607).** Lowercase typewriter `t` with its
  hooked descender OCRs as `l` at word ends. `Mini-Autostarl` in
  8607/76 was the canonical instance. The shape to watch for is a
  short common German suffix that ends in `t` (`-start`, `-art`,
  `-port`, `-text`) showing up as `-starl`, `-arl`, `-porl`,
  `-texl`. When the l-form isn't a word and the t-form is, fix.

## The badge beside a teaser bleeds into the intro

Pages that carry the »64'er / Test« badge next to the stand-first get the badge
OCR'd into the front of `<p class="intro">`. It surfaces as a stray word or
digit before the real first word:

```
<p class="intro">Gier Können Sie sich ein Programm vorstellen …   -> drop "Gier "
<p class="intro">Test Nun gibt es auch ein eigenes …              -> drop "Test "
<p class="intro">9 Wie gut sind die Hardcopy-Module …             -> drop "9 "
<p class="intro">-F] Mit dem neuen Matrixdrucker …                -> drop "-F] "
```

`Gier` is the OCR of the 64'er wordmark. It is not universal — pages 21, 22, 42
and 151 carry the same badge and came through clean — so grep, do not assume:
an intro starting with `Gier `, `Test `, `64'er `, a bare digit, or punctuation
is suspect.

## Drop-cap sweeps must not bound the word length

The ornamental initial is dropped by the OCR, so the paragraph begins mid-word.
When sweeping for it, match the whole word: a regex capping the tail at ~12
characters silently misses `loppybeschleuniger` (18) → `Floppybeschleuniger`.
Better: check EVERY article opening against the page, since the defect also
appears as a wrong initial (`Bin Computer` → `Ein Computer`) or as junk in place
of the letter (`h n dieser` → `In dieser`, `i m Jahre` → `Im Jahre`), none of
which a lowercase-start grep can find.

## `®` is an OCR'd `?`

`»®FILE NOT FOUND ERROR«` is `»?FILE NOT FOUND ERROR«` — CBM BASIC prints its
errors with a leading `?`. The same substitution turns up in headings. Note the
`®` is already present in the OCR `.md`, so it is a scan misread and NOT
Discount's smartypants `(R)` expansion (that is disabled via `-smarty`).

## A `<br>` inside a running footer is a column wrap

`<p class="source">Info: Berthold Trenkel, Schlesienstr. 10,<br> 7320
Göppingen` — the break is where the narrow column wrapped, not structure. Join
it with a space. Keep `<br>` where it separates genuinely distinct entries (two
different `Info:` sources, a multi-company address block).

## Code lines wrapped by the column are ONE logical line

Where a listing line is too wide for the column, the magazine breaks it and
indents the remainder. That is typography, not program structure — join it:

```
50 BY=J+Y : HB=INT(BY/256) :
   LB=BY-HB*256                 ->  50 BY=J+Y : HB=INT(BY/256) : LB=BY-HB*256
```

This applies even when the wrap falls inside a string literal (p61's line 420
breaks between `H2$+"` and `"+MID$`).

## Model names always carry a space

`C 64`, `C 128`, `C 16`, `C 116`, `Plus/4` — the magazine sets a space in the
model name, and the OCR frequently loses it (`C64`, `C128`). Normalise, but run
it as a **verify pass against the page, not a blind replace**: where the print
genuinely omits the space, the print wins (period typos stay).

## Bold lead-ins are content, not headings

Glossary-style paragraphs set their opening term in bold and continue in body
text on the same line (`**Quartz (18)** — Damit das System …`). Two failure
modes, both in 8609's `124 Wie funktioniert ein Computer?`: the bold is dropped
entirely (term arrives as plain text), or the whole line is promoted to a
heading. Wrap the bolded run in `<strong>` and keep the paragraph a paragraph —
the sibling entries show which it should be.

## Listing/prose separation inside a paragraph

A monospace program line is often glued to the prose around it:
`POKE 2088,1:POKE 2100, 252 Jetzt endlich können Sie …` is a `<pre>` line
followed by a new sentence. Split at the boundary where the typeface changes in
print, and mind that the OCR also inserts a space inside the numeric argument
(`2100, 252` for `2100,252`).

## Scan speckles read as punctuation

A speck of dirt in the left margin OCRs as a leading `.` or `'` on the line, so
a paragraph arrives as `. Die erforderliche Anzahl…` or `'Nach der
Parameterübergabe…`. It is not punctuation and must not be re-attached to the
previous sentence — delete it.

How to tell: look for the same mark at the same x-position on other lines of
the same column, where no punctuation is grammatically possible. In 8609's `67`
an identical speck sits before `durch` and before `cherten`; in `58` before
`Nach`. A genuine sentence-final period is at the END of the preceding line,
not floating at the start of the next.

## Doubled letters are one glyph split in two, not a typing slip

`DDer`, `WWichtig`, `BBrillant`, `EEprom`, `FFunktion`, `PPas`, `MO®S`,
`WWichtig`, `POKESs`, `geLlISTet`, `Rüickumschlages`, `Eiditierung` — this class
recurs across every issue and had been cleaned up by hand each time.

**Where it comes from.** The OCR over-segments a single glyph into two
candidate characters and emits both. Measured on 8609's block JSON: 11
occurrences, **7 of them at the very first character of a block**. That is where
the initial is largest (display type, a bold stand-first, a drop cap) and where
the first glyph has no left neighbour to constrain segmentation. A speck on the
paper does the same thing mid-word: p69 of 8608 prints `MOS 6566` with a mark on
the O, and the OCR emitted `MO®S`.

Note the same root cause produces the OPPOSITE defect too. An ornamental initial
is a separate object of a different size, so the segmenter either drops it
(`asin Ausgabe 4/86` for `Das in …`) or emits it twice (`DDer`). Both classes
cluster at paragraph starts for the same reason.

**`read_alt` is NOT a way to fix this** — I initially thought it was, and it is
not. It holds an alternative *column segmentation* of a block: `rows` (read
straight across, interleaving columns) versus `down` (column by column), plus a
`span` score. It exists on 226 of 6308 blocks (3.6%), essentially all
multi-column matter such as advertisements. The p157 block that suggested the
idea is a two-column Fujitsu ad whose `down` reading happens not to duplicate
the `D`; that is coincidence, not a per-character alternative.

A real stage-A fix would need character-level confidence or the glyph boxes,
which the block JSON does not retain. Worth knowing before anyone tries: the
data to do it properly is not currently kept.

**Until then**, r310 flags `\b([A-ZÄÖÜ])\1[a-zäöüß]{2,}` as SOFT. It is not
HARD because a legitimate population exists: command mnemonics with a
placeholder tail, e.g. 8606's `Rechten Rand setzen RRxxx`.
