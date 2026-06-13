# 24 — Tag every contact/reference footer with `<p class="source">`

**Goal:** every paragraph in an article that points the reader at an
external party (where to buy, who to contact, what else to read)
ends up as `<p class="source">…</p>`. Conversely, paragraphs the
import pipeline eagerly tagged based on a "colon after first word"
heuristic but that aren't actually pointers get the `class="source"`
**removed**.

## What `<p class="source">` is for

The site styles `<p class="source">` as a small italicised footer
line. It's a typographic signal to the reader that "this para isn't
article content — it's where you go for more". The print form is
usually a single paragraph at the end of an article (or end of a
sub-section in a news-roundup article like `Aktuelles`) that opens
with a label-like word followed by a colon:

```
Info: FET-Füle Electronic Trading GmbH, Postfach 14 25, D-6057 Dietzenbach 1, Tel. 06074/26429
```

Common label words in 64'er:
- `Info:` — most frequent
- `Bezug:`, `Bezugsquelle:`, `Bezugsadresse:`, `Bezugsquellen:`
- `Hersteller:`, `Vertrieb:`, `Anbieter:`
- `Kontakt:`, `Adresse:`
- `Preis:` when it stands alone as a footer line
- `Literatur:`, `Quelle:`, `Quellen:` — for what-else-to-read pointers / source citations
- `Buchtitel:` / `Buchbesprechung:` — for a book the article reviews

**Implicit / unlabelled footers also qualify** when the paragraph
serves the same function as a labelled one — a pointer to a third
party at the end of the article. Common shapes the OCR pipeline
leaves WITHOUT a label prefix:

- A book / journal **citation** with publisher + place ("Modellrechnung
  der deutschen Bevölkerung im Statistischen Jahrbuch 1985<br>
  Herausgegeben vom Statistischen Bundesamt, Wiesbaden, Verlag W.
  Kohlhammer, Mainz") — implicit `Literatur:` reference.

**Implicit footers that DO NOT qualify** — these structurally look
like multi-line address blocks (and tempt the import pipeline to
tag them) but are body content of the article itself, not a pointer
footer. Leave as plain `<p>`:

- A **contest entry address** ("Die Antworten auf alle drei Fragen
  senden Sie bitte auf einer Postkarte an:<br>Markt&Technik AG<br>
  …") — even though structurally a multi-line address block, this
  is **body content of the contest itself** (the article IS the
  contest), not a reference / vendor footer. Same pattern as
  Fehlerteufelchen Bezugsquellen (next bullet).
- A **Fehlerteufelchen Bezugsquellen / vendor-address list inside a
  correction** ("Hier sind die fehlenden Bezugsquellen.<br>Power
  Cartridge:<br>Kolff Computer Supplies bv, …<br>The Final
  Cartridge:<br>H + P Computers, …") — even though structurally a
  multi-line vendor address block, this is **body content of the
  correction itself**: the very purpose of the Fehlerteufelchen
  entry is to publish the addresses the original article omitted.
  The addresses ARE the correction. Same pattern as the
  contest-entry-address case above. NOT `<p class="source">`.
- A `(byline)`-like signature line printed in source-style typography
  is NOT `<p class="source">` — it's `<address class="author">`.

A paragraph qualifies as `<p class="source">` when **all** of the
following hold:

1. It functions as a pointer to a third party (vendor, distributor,
   author, magazine, book, web/BBS address — in 1986: a postal
   address + phone).
2. It sits at the **end** of an article, or at the **end of a
   sub-section** inside a news-roundup-style article.
3. The print presents it as a standalone footer paragraph — not as
   running prose that happens to mention an address.

## Anti-pattern: false positives from "colon after first word"

The import pipeline historically tagged any `<p>` whose first word
ended in a colon. That catches genuine `Info:` footers — but also
catches plenty of body-text constructs that should remain `<p>`:

- **Question/answer prose**: `Antwort: Das liegt am Timing.` — that's
  the editor answering a reader, not a pointer. Drop the tag.
- **Bullet-list prose flattened to prose**: `Beispiel: 10 PRINT
  "HI"` — example introducer, not a pointer. Drop the tag.
- **Inline label**: `Achtung: Diese Funktion ist nur ab Version 2…`
  — caveat callout. Drop the tag.
- **Definition lead-ins**: `Pixel: Ein einzelner Bildpunkt auf dem
  Bildschirm.` — glossary-style definition. Drop the tag.
- **Continuation of running prose**: paragraph in the middle of an
  article that mentions an address inline ("…wie die Beispiele von
  Firma X (Adresse: …) zeigen…") — drop the tag; this isn't a
  footer.

The test for "remove the tag" is whether removing it would make the
article worse for the reader. If the paragraph is part of the
article's main flow, the tag is wrong.

## Briefing for the sub-agent

For every article in `issues/<YYMM>/*.html`:

### Pass 1 — tag every contact/reference footer

Sweep for `<p>` paragraphs that start with one of the label words
(`Info`, `Bezug`, `Bezugsquelle`, `Bezugsadresse`, `Hersteller`,
`Vertrieb`, `Anbieter`, `Kontakt`, `Adresse`, `Preis`, `Literatur`,
`Buchtitel`, `Buchbesprechung`) followed by `:` and contains a
contact pattern (street address, ZIP code, `Postfach`, phone,
`Tel.`, etc.):

```bash
grep -nE '<p[^>]*>(Info|Bezug|Bezugsquelle|Bezugsadresse|Hersteller|Vertrieb|Anbieter|Kontakt|Adresse|Preis|Literatur|Buchtitel|Buchbesprechung):' \
  issues/<YYMM>/*.html | grep -v 'class="source"'
```

For each hit, change `<p>` → `<p class="source">`. Multi-line
footers (joined by `<br>`) stay as a single `<p class="source">`.

### Pass 2 — audit every existing `<p class="source">` for false positives

```bash
grep -nE '<p class="source">' issues/<YYMM>/*.html
```

For each hit, check:
- Is it actually a pointer (vendor / distributor / author / book /
  address)?
- Does it sit at the end of an article or end of a sub-section?
- Is the paragraph standalone (not part of running prose)?

If any of the three fail → remove `class="source"` from the `<p>`
tag, leaving a plain `<p>`. Do NOT remove the paragraph itself.

When ambiguous, read the surrounding paragraphs to see whether this
paragraph reads like a footer or like running prose. The print
layout helps: in the scan, footer paragraphs are usually visually
separated (smaller font, italics, or set in a different column
break).

### Pass 3 — verify any multi-paragraph footers

Some print footers run for two paragraphs (e.g. one for the German
distributor address, one for the original publisher address). Both
paragraphs are `<p class="source">`. Don't tag the first and skip
the second if they're a contiguous footer block.

### Pass 4 — beautify

```bash
npx --yes js-beautify --type html --indent-size 4 --wrap-line-length 0 --replace <touched files>
```

### Pass 5 — report

Return:
- Per-file table: file → added (how many `class="source"` newly
  applied), removed (how many false-positives stripped), kept.
- Any paragraph you decided not to tag because the print layout was
  ambiguous (flag for human review).
- Any paragraph already tagged but you intentionally left tagged
  even though it doesn't obviously match the rule (e.g. an
  unusual reference form the print author used).

**Do not commit.**

Critical guardrails:
- Anti-memory: don't rewrite paragraph content. This rule only
  toggles the `class` attribute on a `<p>` tag.
- Don't merge two paragraphs into one or split one into two — the
  paragraph boundary is print-given.
- Don't delete the paragraph if you decide it doesn't qualify as
  source — just remove the class.

## Verification

```bash
dir=issues/<YYMM>

# 1. label-words still tagged as plain <p> — flag for review
grep -nE '<p>(Info|Bezug|Hersteller|Vertrieb|Anbieter|Kontakt|Adresse|Preis|Literatur|Buchtitel):' \
  "$dir"/*.html && echo "  WARN: label-word <p> not tagged as source"

# 2. spot-check source-tagged paragraphs are real footers (look at
#    sample to eyeball)
grep -hE '<p class="source">' "$dir"/*.html | head -20

# 3. balanced tags
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    # crude: <p class="source"> opens are followed by </p>
    for m in re.finditer(r'<p class="source">', s):
        nxt = s.find('</p>', m.end())
        if nxt < 0:
            print(f"  unclosed source p in {f} at offset {m.start()}")
PY
)" "$dir"
```

## Notes / lessons

- 64'er's `Aktuelles` column (and similar news roundups) is the
  highest-density source of `class="source"` paragraphs in a
  typical issue — each news-item sub-section ends with an
  `Info:` footer. Treat the column as multiple article-equivalents
  for the purpose of this rule.
- The phone-number formatting in the print is wildly inconsistent
  (`Tel. 06074/26429`, `Tel.: 06074-26429`, `Tel 06074 26429`) —
  preserve verbatim.
- Some `Info:` paragraphs span print-page boundaries and end up
  joined with a stray `<br>` from the OCR pipeline. The line break
  is real (different sub-fields on different lines in print) and
  stays as `<br>` inside the single `<p class="source">`.
- `Hersteller: …  Vertrieb: …` printed as two short paragraphs gets
  TWO `<p class="source">` blocks, not one merged paragraph.
- For book reviews (where `Buchtitel:`, `Autor:`, `Verlag:`,
  `Preis:` appear as four short footer lines), tag all four as
  `<p class="source">` — they collectively form the book's
  bibliographic reference.
- **Fehlerteufelchen Bezugsquellen — history of toggling.** The
  vendor-address block in 8607's `84 Fehlerteufelchen.html` was
  toggled twice during 8607 work: a7cfd7bd3 added `class="source"`
  → da95ac771 added the rule-update + revert → ed32cf29e re-added
  → now reverted permanently. Policy is final: a Bezugsquellen /
  vendor-address list inside a Fehlerteufelchen correction is body
  content of the correction (the addresses ARE the correction);
  leave as plain `<p>`. Future passes must not re-add the class.
