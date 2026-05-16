# 64er.id Workflow

How to fill the `<meta name="64er.id">` for every article in an issue.

`64er.id` is required by the generator. It is unique within the issue and becomes the article's output filename (`<id>.html`). Recurring columns share the same `64er.id` across all issues so the cross-issue index can group them.

## How to run

```
Fill all 64er.id placeholders in issues/YYMM/*.html
per tools/llm/new/64er_id_workflow.md.
```

**Input:** `issues/YYMM/*.html` with `<meta name="64er.id" content="XXX">` (or commented-out placeholders) in `<head>`.

**Output:** same files, with `XXX` (or missing meta) replaced by a real ID per the rules below.

## What `64er.id` is

A short lowercase keyword used in two places by `generate.py`:

- **Filename**: `target_filename = id + ".html"` (`generate.py:668`) — the article is published at `<issue>/<id>.html`.
- **Uniqueness check**: every article in an issue must have a `64er.id`, and two articles in the same issue may not share one (`generate.py:589–596`, raises `SystemExit` on missing or duplicate).

The generator does not enforce a character set. By convention (look at other issues):

- **Lowercase**, hyphens or underscores OK: `leserforum`, `tips_einsteiger`, `master-text`, `c128-reisebericht`.
- **German umlauts and `ß` are FINE** — use them. Don't transliterate to `oe`/`ae`/`ue`/`ss`. `druckermöbel`, `computerwäsche`, `floppyzubehör`, `bücher`, `schloß` are all preferred over their transliterated forms.
- **Digits OK**: `1541`, `6510`, `c64`, `c128d`, `vc20`.
- Short. Most IDs are 4–20 characters.

## Rules

### Rule 1 — recurring columns keep the same ID across issues

Whenever an article is part of a recurring series or department, its `64er.id` matches what previous issues used. The cross-issue index groups by ID.

Canonical IDs for the common recurring columns (verify against the most recent prior issue before reusing — IDs sometimes drift):

| Recurring column / department | Canonical `64er.id` |
|---|---|
| Editorial (any title) | `editorial` |
| Aktuelles / Aktuell | `aktuelles` (newer) or `aktuell` (older — pick whichever the predecessor issue used) |
| CeBIT-Berichterstattung | `cebit` |
| Leserforum | `leserforum` |
| Fehlerteufelchen | `fehlerteufelchen` |
| Bücher | `bücher` (with `ü`) |
| Impressum | `impressum` |
| Vorschau | `vorschau` |
| 64'er Extra (the back-section reference column) | `extra` |
| Memory Map mit Wandervorschlägen | `memory_map` |
| Computer-Knobeleien | `knobeleien` |
| Wir suchen die Anwendung des Monats | `anwendung_des_monats` |
| Einmal im Monat … Listing des Monats | `listing_des_monats` |
| Von Basic zu Assembler / Assembler ist keine Alchimie | `assembler` |
| Programmieren Sie strukturiert! | `strukturiert` |
| Tips & Tricks für Einsteiger | `tips_einsteiger` |
| Tips & Tricks für Profis | `tips_profis` |
| Tips & Tricks zum C 128 | `tips_c128` |
| Tips & Tricks zum C 16 | `tips_c16` |
| Die CP/M-Ecke / Tips zu CP/M | `cpm` |
| Tips & Tricks zu Vizawrite | `tips_vizawrite` |
| Tips & Tricks zu Superbase | `superbase` |
| Streifzüge durch die Grafik-Welt | `grafik_welt` |
| Pascal-Kurs | `pascal` |

Don't invent a new ID for a recurring article. `git grep '<meta name="64er.id"' issues/<prev-issue>/*.html` for the previous issue first.

### Rule 2 — program-listing articles use the program's name

When an article is fundamentally **about a specific program/listing** (the kind that ships with `data-filename` in `<pre>`), its `64er.id` is the program's user-visible name, lowercased, with spaces/punctuation cleaned up.

Examples:

| Article title | Program | `64er.id` |
|---|---|---|
| »Master-Text — Textverarbeitung hoch drei« | Master-Text | `master-text` |
| »ProDisc — eine professionelle Diskettenverwaltung« | ProDisc | `prodisc` |
| »Cursor selbst gemacht« | Wahl Cursor | `wahlcursor` |
| »Neues aus der Heimdruckerei« (Print Master review) | PrintMaster | `printmaster` |
| »Ein ausgefuchstes Programm« (Printfox review) | Printfox | `printfox` |
| »Über den Wolken …« (Shades music piece) | Shades | `shades` |
| »Greatprint« | Greatprint | `greatprint` |
| »Steel Slab« | Steel Slab | `steel_slab` |
| »Abrakadabra« (Disk-Wizard listing) | Disk-Wizard | `disc-wizard` |

This rule wins over the article's German title: the article "Cursor selbst gemacht" gets `wahlcursor` because Wahl Cursor is the program, not `cursor-selbst-gemacht`.

When in doubt, ask: "what's the name the reader will type or download?" — that's the ID.

### Rule 3 — articles not in either category

For articles that are neither a recurring column nor a single-program writeup, invent a short German keyword that captures the topic:

- »Der Neue« (review of the C 64 II) → `c64ii`
- »Druckermöbel« → `druckermoebel`
- »Datenbanken« → `datenbanken`
- »Zwei fliegende Holländer« (Power Cart / Final Cart review) → `cartridges`
- »Dem Täter auf der Spur« (Perry Mason + Borrowed Time adventures) → `spiele2` (paired with the `spiele1` Action-spiel article in the same issue)

Keep umlauts and `ß` — they're part of the language. `druckermöbel`, `computerwäsche`, `bücher` are correct; the transliterated forms `druckermoebel`, `computerwaesche`, `buecher` are wrong.

### Rule 4 — uniqueness within the issue

`generate.py` raises `duplicate 64er.id 'XXX'` if two articles share an ID. After you fill all placeholders, run:

```bash
grep -h '64er\.id' issues/YYMM/*.html | sort | uniq -d
```

Output should be empty. If a duplicate exists, prefix one with a discriminator (`spiele1` / `spiele2`, `mode_a` / `mode_b`).

### Rule 5 — placeholder `XXX` is invalid

The article template ships with `<meta name="64er.id" content="XXX">`. `XXX` is not a valid ID — the generator will treat two `XXX`-articles as duplicates and abort. Every placeholder must be replaced before the generator runs successfully on the issue.

## Procedure

1. **List every article in the issue** with its current ID:
   ```bash
   cd issues/YYMM/
   for f in *.html; do
     id=$(grep 'name="64er.id"' "$f" | sed 's/.*content="\([^"]*\)".*/\1/')
     echo "  $f → $id"
   done
   ```
2. **For each article**, decide its ID using the rules above, in priority order:
   - Rule 1 (recurring column) — look up the predecessor issue with `grep '64er.id' issues/<prev>/*.html`
   - Rule 2 (program-listing) — what's the program name?
   - Rule 3 (topical keyword)
3. **Build a mapping** in a one-shot Python script with explicit `MAPPING = {filename: id}`, including sanity checks:
   - Every HTML in the dir is mapped.
   - No two filenames map to the same ID.
   - Every ID is non-empty and lowercase-ASCII-ish.
4. **Apply** by replacing each `<meta name="64er.id" content="XXX">` with the chosen ID. Some articles may have the meta as a comment (`<!-- <meta name="64er.id" content="XXX"> -->`); uncomment and fill those too.
5. **Verify**:
   ```bash
   grep -L '64er\.id' issues/YYMM/*.html              # should be empty (every file has the meta)
   grep -h '64er\.id' issues/YYMM/*.html | sort | uniq -d   # should be empty (no duplicates)
   grep -l 'content="XXX"' issues/YYMM/*.html          # should be empty (no placeholder left)
   ```
6. **End-to-end check**: run the generator and confirm no `64er.id` error:
   ```bash
   python3 generate.py --issues YYMM local
   ```

## Placement in HTML

The `<meta name="64er.id">` is the LAST meta tag in `<head>`, after `toc_category` / `toc_title` / `index_category` / `index_title`:

```html
<meta name="64er.toc_category" content="Listings zum Abtippen">
<meta name="64er.toc_title" content="Listings des Monats: Professionelle Textverarbeitung">
<meta name="64er.id" content="master-text">
```

## What NOT to do

- Don't invent an ID for a recurring column without checking what the previous issue used. Continuity across issues is the whole point of the convention.
- Don't transliterate `ü`/`ö`/`ä`/`ß` — use them as-is. `bücher`, `druckermöbel`, `computerwäsche` are all correct.
- Don't use `XXX` or any placeholder — the generator aborts.
- Don't reuse the same ID for two articles in one issue, even if they cover related topics. Pair them with a discriminator (`spiele1` / `spiele2`).
- Don't make the ID a full sentence. Short keyword, ideally fewer than 20 characters.
- Don't change a recurring column's ID just because you think a different name is "cleaner" — the cross-issue index relies on stability. If the convention is genuinely wrong, fix it for ALL past + future issues at once or not at all.
