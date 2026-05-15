# Final Issue Cleanup Workflow

How to clean up OCR artifacts in the merged issue markdown (`issues/YYMM/YYMM.md`) after extraction. Catches what `body_workflow.md` missed: leftover line-break hyphens, character-level OCR confusions, lost spaces, and markdown-unsafe `<…>` runs.

## How to run

Point the agent at this file and an issue:

```
Clean up OCR artifacts in issues/YYMM/YYMM.md per tools/llm/new/cleanup_workflow.md.
```

**Input:** `issues/YYMM/YYMM.md` (already produced by `body_workflow.md` + downstream steps).
**Output:** same file, edited in place. Line count is preserved (all changes are substitutions inside lines, not structural).

## CRITICAL RULES

### Rule 1: Only fix OCR errors. Never fix original typos or old German spelling.

The magazine is a 1980s German publication. It uses pre-1996 orthography (`muß`, `daß`, `Adreß`, `Schnellade` with elided third L) and contains real-life author/editor typos. Both are part of the historical record and **must be preserved**.

**OCR errors** = character-level substitutions where two glyphs look alike, line-break hyphen artifacts, or lost/added spaces. OCR **does not add or drop characters**. If a word is missing a letter (`Prinzessinen` for `Prinzessinnen`) or has an extra one (`Nahrungsmittteln`), that is an **original typo**, not OCR — leave it alone.

Diagnostic test: count the characters. Same count, different glyph at one position → OCR. Different count → typo. Apply this every time before editing.

| Type | Example | Fix? |
|------|---------|------|
| OCR letter confusion (substitution) | `Uer-besserungen` → `Verbesserungen` (U↔V) | ✅ fix |
| OCR digit/letter (substitution) | `CL0SE` → `CLOSE` (0↔O), `peek(211)+l` → `+1` (l↔1) | ✅ fix |
| Lost space | `ausjedenfalls` → `aus jedenfalls` | ✅ fix |
| Added space inside word | `uo riginal$` → `uoriginal$` | ✅ fix |
| Lost line-break hyphen | `Druk-ker` → `Drucker` (old German ck→k-k) | ✅ fix |
| Mistaken double hyphen | `Sinclair-Com-puter` → `Sinclair-Computer` (only trailing) | ✅ fix |
| Old German spelling | `muß`, `daß`, `Adreß`, `Schnellade` | ❌ leave |
| Missing letter (original typo) | `Prinzessinen` (one n) | ❌ leave |
| Extra letter (original typo) | `Nahrungsmittteln` (triple t), `Anwätte` for `Anwälte`, `Egentlich` for `Eigentlich`, `Löewe` for `Loewe` | ❌ leave |

### Rule 2: Multi-hyphen words — only the last hyphen is the line break.

When a word `X-Y-z` has its final segment starting lowercase, only the **last** hyphen is a line-break artifact. The earlier hyphens are intentional compound hyphens — keep them.

- ✅ `Sinclair-Com-puter` → `Sinclair-Computer` (keep first hyphen)
- ❌ `Sinclair-Com-puter` → `SinclairComputer` (wrong — destroyed the compound)
- ✅ `IBM-kom-patible` → `IBM-kompatible`
- ✅ `QWER-TY-Reihe` → `QWERTY-Reihe` (when both internal segments form one acronym, judgment call from context)

### Rule 3: `»` ↔ `«` direction is never OCR.

The German guillemets `»…«` open and close in fixed positions. If you see `»disk»` (both right-pointing), that is an **original typo**, not OCR. Do not "correct" it.

Exception: `<<` and `<` are OCR misreads of `«`, and `>>` / `>` are OCR misreads of `»` (the chevron glyphs degrade to ASCII brackets). Those are fair OCR fixes.

## Procedure

Run the passes in order. After each pass, scan for what's left before moving on.

### Pass 1 — Suspicious hyphenated tokens

```python
import re
matches = re.findall(r'[A-Za-zäöüÄÖÜß]+-[A-Za-zäöüÄÖÜß]+', text)
suspicious = [w for w in matches if re.match(r'.+-[a-zäöüß]', w)]
```

Filter to tokens whose right side starts lowercase — those are almost always line-break artifacts. Examples actually seen: `Mo-dus`, `Compu-ter`, `Schnitt-stelle`, `Doppel-laufwerk`, `Apfelmänn-chen`, `ver-kaufen`, `wer-den`, `auf-bereiten`.

Also handle:
- **Old German ck→k-k**: `Druk-ker`→`Drucker`, `Drük-ken`→`Drücken`, `Tük-ken`→`Tücken`. After joining, the bare form is **not** valid German (`Drukker` is wrong in any era).
- **"X- und Y" enumeration**: `Hard-und` → `Hard- und`, `Adreß-oder` → `Adreß- oder`. The hyphen survived as a real compound hyphen; the space after it was lost.

Repeat the scan on three-segment tokens (`X-Y-z` with trailing lowercase) per Rule 2.

### Pass 2 — Character-level confusions

Scan with these patterns:

| Pattern | Confusion | Examples |
|---------|-----------|----------|
| `\bU[a-zäöü]+` then check | U vs V | `Uer-besserungen`→`Verbesserungen`, `Uon`→`Von`, `uollen`→`vollen` |
| Digit-0 inside letter run | 0 vs O | `CL0SE`→`CLOSE`, `P0KE`→`POKE`, `T0 1000`→`TO 1000`, `0RD`→`ORD` |
| Digit-1 next to letters in code | 1 vs l | `peek(211)+l`→`+1`, `x=l`→`x=1`, `OPEN l,8`→`OPEN 1,8`, `K+l`→`K+1` |
| Capital I between lowercase | I vs l | `umherfIiegen`→`umherfliegen` |
| `Q[a-z]` mid-word | Q vs (J | `AQ)`→`A(J)`, `Qa/Nein`→`(Ja/Nein`, `Qe kürzer`→`(Je kürzer` |
| Stray `ö` instead of `o` | ö vs o | `geöWrite`→`geoWrite`, `Autöboot`→`Autoboot` |
| `<<` / `>>` | brackets vs « » | `»BASIC $B000<<`→`»BASIC $B000«` |
| Stray `ä` | ä vs a or au | `äuf`→`auf`, `äussehen`→`aussehen` |
| Stray period | period vs space | `sicher.auch`→`sicher auch`, `Wer. selbst`→`Wer selbst`, `MSE.eingegeben`→`MSE eingegeben` |

Then `Ghrom-`→`Chrom-`, `Pmsel`→`Pinsel` (`in`→`m` is classic OCR), `Koalo`→`Koala`, etc. — case-by-case for one-off substitutions where the count matches.

### Pass 3 — Missing spaces

Regex `\b[a-zA-Z]+[A-Z]+[a-z]+\b` catches words with internal lowercase→uppercase boundaries. Most hits are legitimate CamelCase (`dBase`, `KByte`, `geoWrite`, `CompuServe`, `HiRes`, `MHz`, `gePOKEt`, `geSAVEt`, etc.) — skip those. Real fixes look like:

- `derComputerdabeiist` → `der Computer dabei ist`
- `reichtderC 16` → `reicht der C 16`
- `aufPapier`, `aufBand`, `aufDiskette`, `aufIhre` → `auf Papier`, etc.
- `MitjedemdieserProgram-me` → `Mit jedem dieser Programme` (also has a hyphen artifact)
- `STOPTaste` → `STOP-Taste` (compare `RESTORE-Taste` already correct nearby)

Also check for run-together short words: `injedem`→`in jedem`, `Nachjeder`→`Nach jeder`, `Beieinem`→`Bei einem`, `derjetzigen`→`der jetzigen`, `ImJa-nuar`→`Im Januar`. The `C 64II`/`»C 641«` pattern: `C 64II` → `C 64 II`, `»C 641«` → `»C 64 I«` (digit 1 misread of Roman I, plus lost space).

### Pass 4 — Escape bare `<` for markdown

The merged file contains text fragments like `<RETURN>`, `<SHIFT>`, BASIC code `<>`, `<= 90`, that markdown will try to parse as HTML. Escape every bare `<` with `\<`, **except** intentional HTML tags added by the extraction pipeline.

Preserved tags (the only HTML we emit): `<br>`, `<u>…</u>`, `<b>…</b>`, `<sub>…</sub>`, `<sup>…</sup>`.

```python
HTML_TAGS = ("<br>", "<u>", "</u>", "<b>", "</b>",
             "<sub>", "</sub>", "<sup>", "</sup>")
out = []
i = 0
while i < len(text):
    if text[i] == "<":
        for tag in HTML_TAGS:
            if text.startswith(tag, i):
                out.append(tag); i += len(tag); break
        else:
            out.append(r"\<"); i += 1
    else:
        out.append(text[i]); i += 1
text = "".join(out)
```

Do **not** also touch `>` — bare `>` in body text does not trigger markdown parsing (only blockquotes at line start, which won't accidentally fire here). And do **not** normalize `<RETURN>` to `⟨RETURN⟩` (Unicode angle brackets) — even though much of the file uses `⟨…⟩` already, the user explicitly wanted bare `<…>` preserved as text and just escaped.

## How to work

Use a Python script per pass, not one-by-one Edit calls. Write `_fixN.py`, run it, delete it. Keep the script's `FIX = {old: new}` dict explicit so the change is reviewable. After each pass, re-run the detection regex to see what remains.

When in doubt about a single token, **grep for context** first. The same surface form can be OCR in one spot and a legitimate variable name (`zahl-sgn`, `zahl1`, `zahl2`) in another. Don't replace blindly.

Don't apologize for being thorough — the file is ~3700 lines and ~150 fixes are typical. Don't try to do it in one giant script either; small passes are easier to verify and revert.

## What NOT to touch

- Old German orthography (`ß`, `daß`, `muß`, `Adreß`, elided double-L like `Schnellade`)
- Original typos (`Prinzessinen`, `Anwätte`, `Egentlich`, `Löewe`, `Letzendlich`, `Nahrungsmittteln`)
- `»` vs `«` direction errors in original print
- CamelCase product/jargon names (`dBase`, `geoWrite`, `HiRes`, `CompuServe`, `StarDatei`, `ProDisc`, `FrameGrabber`, `GenLock`, `gePOKEt`)
- BASIC code variable names that look like substitutions but are deliberate (`zahl1`, `zahl2`, control codes `k1:Kursivschrift` etc.)
- The `[NNN-NNN]` page-range markers at the end of headers (structural, not body text)

If unsure, **leave it**. A faithful OCR with original typos preserved is more valuable than a "corrected" one that has rewritten history.
