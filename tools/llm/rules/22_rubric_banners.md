# 22 — Add rubric banner images (Editorial / Bücher / Fehlerteufelchen)

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

The full procedural spec lives in `tools/llm/new/rubric_banner_workflow.md`.
This rule is the dispatch + verification gate.

Leserforum's banner is covered by rule 18 (the article also gets a full
Q&A restructure, not just a banner).

## Critical: rubric absence is a clean skip

**If the issue has no article for a given rubric, skip that rubric
cleanly. Do not invent a banner, do not create a placeholder article.**
Not every 64'er issue carries every rubric — Bücher in particular is
absent from some issues (e.g. 7/86 has no Bücher article). The
correct behavior is to verify the article exists, and if it doesn't,
report it as N/A and move on.

Test: `ls "issues/<YYMM>/"*[Bb]?cher*.html` (similar greps for
`*Fachredakteur*`, `*Editorial*`, `*Fehlerteufelchen*`). If the glob
matches nothing, that rubric doesn't exist in this issue.

## Briefing for the sub-agent

For each of the three rubrics:

1. **Check the article exists** (per the absence rule above). If it
   doesn't, skip the rubric and report N/A.
2. **Render the start page** at 600 dpi for the banner crop:
   `pdftoppm -r 600 issues/<YYMM>/64er_19XX-XX.pdf
   /tmp/<YYMM>_pages_600/p -png -f <START> -l <START>`.
3. **Find and crop the banner** on the page (top of column for
   Bücher / top of page for Editorial / Fehlerteufelchen). Save as
   `issues/<YYMM>/<START>-0.png`.
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

# For each present rubric, verify the banner + insertion
for rub in Editorial Bücher Fehlerteufelchen Fachredakteur; do
  matches=$(ls "$dir/"*"$rub"*.html 2>/dev/null)
  if [ -z "$matches" ]; then
    echo "  $rub: N/A (no article in this issue)"
    continue
  fi
  for f in $matches; do
    page=$(basename "$f" | grep -oE '^[0-9]+')
    banner="$dir/$page-0.png"
    [ -f "$banner" ] || echo "  FAIL: $f has no banner $banner"
    grep -q "$page-0.png" "$f" || echo "  FAIL: $f doesn't reference banner"
  done
done

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

## Notes / lessons

- 7/86 (issue 8607) has no Bücher article — the rubric was skipped
  cleanly per the absence rule. Don't invent one.
- 7/86's Fehlerteufelchen mascot is rendered in B/W line art (the
  earlier issues had it in colour) — the print is the source, not
  prior issues' tinted versions.
- The Editorial portrait's `alt` text in 8606 reads
  "Michael Scharfenberger, Chefredakteur" — preserve the role suffix.
  8607's Fachredakteur column uses a slightly different role
  ("Porträt Michael Scharfenberger" — the rule-12 image-placement
  agent set this); both work, but pick one and be consistent
  within the issue.
- The Bücher banner image content is identical across the recent
  issue run (8601–8606). You can `cp` the prior issue's
  `<page>-0.png` after renaming to the current page, then verify
  the result matches the new issue's print. Saves a banner crop.
