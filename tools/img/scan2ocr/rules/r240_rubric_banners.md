# 240 — Add rubric banner images (Editorial / Bücher / Fehlerteufelchen)

**Applies to:** monthly — all three banners it owns belong to monthly recurring rubrics. No Sonderheft in the repo carries a rubric banner: zero `<page>-0.png` on any Editorial/Vorwort, Bücher or Fehlerteufelchen article across `SH8501`-`SH8508`, and no Sonderheft has a Fehlerteufelchen article at all. See *Sonderhefte: there is no rubric banner*.

**Goal:** add the stylized title-banner image at the top of each
recurring-rubric article that uses one. Three rubrics carry a banner
that reuses the same illustration issue-to-issue (Bücher,
Fehlerteufelchen) or refreshes per issue (Editorial portrait):

| Rubric | Banner | HTML shape | Position |
|---|---|---|---|
| Editorial | Per-issue editor portrait | `<img class="inline">` (no `<figure>`) | After `<h1>` |
| Bücher | Recurring stack-of-books illustration | `<figure><img></figure>` | After `<h1>`, before first `<h2>` |
| Fehlerteufelchen | Recurring devil-with-listing illustration | `<img class="inline" width="300">` | After `<h1>`, before first `<h3>` |

Each rubric's HTML wrapping is **different on purpose** — don't unify
them. Match exactly what the prior issue's HTML did.

Leserforum's banner is covered by rule 200 (the article also gets a full
Q&A restructure, not just a banner).

## Sonderhefte: there is no rubric banner

This rule is `Applies to: monthly`, and on a `"kind": "sonderheft"` issue the
orchestrator records it `not applicable — kind` rather than running it. The
evidence, from the published corpus:

- **Fehlerteufelchen** — no Sonderheft has the article at all
  (`ls issues/SH85*/*ehlerteufelchen*` → no matches). Errata that correct a
  Sonderheft article are printed in a later MONTHLY and arrive via step 300,
  as an aside on the article, not as a rubric with a banner.
- **Bücher** — one Sonderheft carries the article (`SH8508/104 Bücher.html`)
  and it has NO `104-0.png`: its illustrations are ordinary numbered figures.
  The recurring stack-of-books banner is a monthly fixture.
- **Editorial** — a Sonderheft's opening piece is a Vorwort, and the two that
  carry `64er.id="editorial"` (`SH8501/3 Warum ein Sonderheft.html`,
  `SH8502/3 Abenteuer total.html`) hold no image at all: no editor portrait,
  no `3-0.png`.

Nothing is lost by not running here. A Sonderheft's `<page>-0.png` files are
title images for ordinary feature articles (`SH8502` has seven, one per
adventure), and **step 150 places them** — this rule was never their route.

If a future Sonderheft DOES print one of these three banners, that is the
`Applies to:` contract's evidence line coming back non-empty: re-classify this
rule `all` with the evidence, don't run it behind the contract's back.

## Critical: rubric absence is a clean skip

**If the issue has no article for a given rubric, skip that rubric
cleanly. Do not invent a banner, do not create a placeholder article.**
Not every 64'er issue carries every rubric — Bücher in particular is
absent from some issues (e.g. 7/86 has no Bücher article). The
correct behavior is to verify the article exists, and if it doesn't,
report it as N/A and move on.

Test: `ls "issues/<YYMM>/"*[Bb]?cher*.html` (similar globs for
`*Fachredakteur*`, `*Fehlerteufelchen*`). **Bücher and
Fehlerteufelchen can stay filename-glob** — their article titles equal
the rubric name, so the glob is reliable.

**Editorial must NOT use a filename glob.** The editorial article is
named by its headline, not by the word "Editorial" (8608's editorial
is `8 Ja oder nein ….html`), so `ls *Editorial*.html` misses it.
Detect Editorial by its stable `64er.id` instead:

```bash
grep -l '64er.id" content="editorial"' issues/<YYMM>/*.html
```

If that grep matches nothing, the issue has no editorial. Same clean
skip applies.

## Briefing for the sub-agent

For each of the three rubrics:

1. **Check the article exists** (per the absence rule above). If it
   doesn't, skip the rubric and report N/A.

```bash
# The repo venv, not bare python3: r010_ocr_blocks imports numpy and scipy,
# which the system python does not have, so `python3` makes SRC silently EMPTY
# and every crop below then fails on "/NNN.png". MEASURED on 8611.
PY=${PYTHON:-.venv/bin/python}
SRC=$("$PY" -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.SRC_DIR)')     # <tmp>/masters600
```

2. **The start page is already rendered** at 600 dpi: `"$SRC/<START>.png"`
   from `masters600`, zero-padded to three digits. Do not `pdftoppm` the
   issue PDF — it is assembled at step 006 and does not exist yet. See r000,
   *THE PAGE IMAGE IS `masters600`*.
3. **Find and crop the banner** on the page (top of column for
   Bücher / top of page for Editorial / Fehlerteufelchen). Grep step 010's block index (`<OUT_DIR>/blocks/pNNN.txt`) for the rubric name in the
   blocks file to find a starting bbox; the banner illustration
   typically sits adjacent in the same column. Save the crop as
   `issues/<YYMM>/<START>-0.png`.
   **Deliver it in the right bucket.** `tools/convert-scans.sh` states the
   project's convention: colour / greyscale art ships at **150 dpi** — a
   `-resize 25%` of the 600 dpi crop — and bilevel line art stays at
   **600 dpi**, unresized. The Editorial portrait is a colour photo and is
   resized; a cut outside **335–340 × 278–282** is wrong. **Crop inside the
   photo's keyline.**

   The Fehlerteufelchen devil is line art: crop it at its own printed size and
   let `width="300"` scale it. Do not resize the crop.

   **The Bücher banner is NOT identical across issues** — cut it from this
   issue's master like the others, never `cp` the previous one. Expect
   **245–248 × 202–206**.

4. **Read the crop** to verify it's the banner and not page noise.
5. **Insert into the article HTML** with the rubric-appropriate
   shape:

   **Editorial** (per-issue editor portrait):
   ```html
   <h1>Editorial title…</h1>

   <img src="<START>-0.png" alt="Editor Name, Chefredakteur" class="inline">

   <p>First paragraph…</p>
   ```

   **Bücher** (`<figure>` wrapper, alt is the rubric name):
   ```html
   <h1>Bücher</h1>

   <figure>
       <img src="<START>-0.png" alt="Bücher">
   </figure>

   <h2>First book section</h2>
   ```

   **Fehlerteufelchen** (`<img class="inline" width="300">`):
   ```html
   <h1>Fehlerteufelchen</h1>

   <img src="<START>-0.png" width="300" alt="Fehlerteufelchen" class="inline">

   <h3>First correction</h3>
   ```

6. Beautify the touched file (`npx --yes js-beautify --type html
   --indent-size 4 --wrap-line-length 0 --replace`).
7. **Do not commit.** Return a per-rubric table.

Critical guardrails:
- The three rubrics each have their OWN wrapping — never combine.
- Editor portrait's `alt` is the editor's NAME + ROLE (not the
  rubric name). Bücher and Fehlerteufelchen's `alt` is the rubric
  name.
- Anti-memory: editor name comes from reading the article body's
  closing signature line, not from memory of who chief-edits this
  year.
- The banner file is always `<startpage>-0.png` — the `-0` suffix
  is by convention for "title image".

## Verification

```bash
dir=issues/<YYMM>

# Editorial is detected by stable id (its filename is a headline, not
# the word "Editorial"); the other rubrics by filename glob.
editorial=$(grep -l '64er.id" content="editorial"' "$dir"/*.html 2>/dev/null)
for rub in Bücher Fehlerteufelchen Fachredakteur; do
  matches=$(ls "$dir/"*"$rub"*.html 2>/dev/null)
  if [ -z "$matches" ]; then
    echo "  $rub: N/A (no article in this issue)"
    continue
  fi
  # `for f in $matches` word-splits "144 Bücher.html" at the space, and EVERY
  # article filename in this corpus has spaces. As written this printed 17
  # FAIL lines on published 8610 and 12 on a finished 8611, plus
  # "grep: invalid option -- ." when $page came out empty.
  # The reference test is anchored too: a bare "$page-0.png" substring match
  # accepts 18-0.png for page 8.
  printf '%s\n' "$matches" | while IFS= read -r f; do
    [ -n "$f" ] || continue
    page=$(basename "$f" | grep -oE '^[0-9]+')
    banner="$dir/$page-0.png"
    [ -f "$banner" ] || echo "  FAIL: $f has no banner $banner"
    grep -q "src=\"$page-0\.png\"" "$f" || echo "  FAIL: $f doesn't reference banner"
  done
done
if [ -z "$editorial" ]; then
  echo "  Editorial: N/A (no article in this issue)"
else
  printf '%s\n' "$editorial" | while IFS= read -r f; do
    [ -n "$f" ] || continue
    page=$(basename "$f" | grep -oE '^[0-9]+')
    banner="$dir/$page-0.png"
    [ -f "$banner" ] || echo "  FAIL: $f has no banner $banner"
    # Anchored like the rubric loop above. Unanchored, with the dot
    # unescaped, this accepted a planted src="18-0.png" for page 8.
    grep -q "src=\"$page-0\.png\"" "$f" || echo "  FAIL: $f doesn't reference banner"
    # and the editorial needs the same SHAPE check the rubrics get
    grep -q "<figure" "$f" || echo "  NOTE: $f banner not wrapped in <figure>"
  done
fi

# Per-rubric shape check
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    p = os.path.join(d, f)
    s = open(p).read()
    if 'Bücher' in f:
        if not re.search(r'<figure>\s*<img src="\d+-0\.png" alt="Bücher"', s):
            print(f"  WARN: Bücher shape off in {f}")
    if 'Fehlerteufelchen' in f and 'Fehlerteufelchen' in s[:500]:
        if not re.search(r'<img src="\d+-0\.png" width="300" alt="Fehlerteufelchen" class="inline">', s):
            print(f"  WARN: Fehlerteufelchen shape off in {f}")
PY
)" "$dir"
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every banner the sub-agent inserts (or skips) must
be backed by **runnable verifier evidence pasted verbatim into the
report**:

- For each banner inserted, paste the one-line
  `<OUT_DIR>/blocks/p<START>.txt` line (or the cropped block path) that
  showed the banner's bbox, plus the rubric name verbatim from the
  print band, e.g.
  ```
  84 Fehlerteufelchen.html → blocks/p084.txt block=3
  bbox=900x420+580+200 text= Fehlerteufelchen
  → crop saved as 84-0.png
  ```
- For each Editorial banner, paste the verbatim closing-signature
  line the sub-sub-agent read from the article body (the source of
  the `alt="Editor Name, Chefredakteur"` value).
- For each rubric skipped as N/A, paste the
  `ls "issues/<YYMM>/"*Rubric*.html` output showing zero matches.

**No verifier output, no claimed banner.** A banner reported without
the bbox / verbatim-name evidence is treated as a guess; the
orchestrator will re-dispatch. "Trust me, that's the right
illustration" is never acceptable — banner illustrations differ
issue-to-issue (e.g. 7/86's B/W Fehlerteufelchen vs. earlier
tinted versions).

## Notes / lessons

- 7/86 (issue 8607) has no Bücher article — the rubric was skipped
  cleanly per the absence rule. Don't invent one.
- 7/86's Fehlerteufelchen mascot is rendered in B/W line art (the
  earlier issues had it in colour) — the print is the source, not
  prior issues' tinted versions.
- The Editorial portrait's `alt` text in 8606 reads
  "Michael Scharfenberger, Chefredakteur" — preserve the role suffix.
  8607's Fachredakteur column uses a slightly different role
  ("Porträt Michael Scharfenberger" — the rule 150 image-placement
  agent set this); both work, but pick one and be consistent
  within the issue.
- The Bücher banner image content is identical across the recent
  issue run (8601–8606). (Step 3 above says never `cp` the previous issue's
  banner, and that is the rule: crop this issue's own master. The sentence
  below contradicted it and is kept only as the historical note it is — what
  8601–8606 actually did.) You could `cp` the prior issue's
  `<page>-0.png` after renaming to the current page, then verify
  the result matches the new issue's print. Saves a banner crop.
