# Impressum Workflow

How to create the `Impressum` article for a new issue. The Impressum (masthead / publisher's notice) is a recurring rubric that's near-identical from issue to issue — most lines are constant publisher info, but a handful change each month (editor roster, advertising staff, prices, Schweiz/USA addresses, etc.).

## How to run

```
Create issues/YYMM/<page> Impressum.html per tools/llm/new/impressum_workflow.md.
```

**Input:**
- The most recent prior issue's `Impressum.html`
- The current issue's PDF (so we can extract page <NNN> for OCR)
- The prior issue's PDF (for diff)

**Output:** `issues/YYMM/<page> Impressum.html` with the current issue's masthead, meta updated.

## Procedure

### 1. Copy the previous issue's file

The Impressum lives at the same page number in most issues (typically `179`, sometimes drifts by ±2). Find it in the prior issue and copy:

```bash
cp "issues/<prev-YYMM>/<NNN> Impressum.html" "issues/<curr-YYMM>/<NNN> Impressum.html"
```

If the current issue's TOC puts the Impressum at a different page, rename the destination to that page.

### 2. Update meta tags

Two fields almost always need a touch-up:
- `<meta name="64er.issue" content="N/YY">` — bump to the current issue.
- `<meta name="64er.pages" content="N">` — set to the Impressum's page in the current issue.

Other meta stays the same:
```html
<title>Impressum</title>
<meta name="64er.toc_category" content="Rubriken">
<meta name="64er.id" content="impressum">
```

(`64er.id` is the canonical recurring ID per `64er_id_workflow.md` — never change it.)

### 3. Extract and diff the printed pages

Both issues print the masthead on a page that also contains an advertisers index (`Inserentenverzeichnis`) and sometimes a `Depot-Händler` list. Layouts make `pdftotext -layout` brittle.

Best workflow:
1. **Extract printed text** from both PDFs:
   ```bash
   pdftotext -layout -f <prev-page> -l <prev-page> issues/<prev-YYMM>/*.pdf /tmp/impressum_prev.txt
   pdftotext -layout -f <curr-page> -l <curr-page> issues/<curr-YYMM>/*.pdf /tmp/impressum_curr.txt
   diff /tmp/impressum_prev.txt /tmp/impressum_curr.txt
   ```
2. **Visually compare** the rightmost column (the Impressum) by cropping with `magick` and `Read`ing both crops. The pdftotext output is column-jumbled because of the 3-column layout; trust the vision read for ambiguous cases.
   ```bash
   magick issues/<curr-YYMM>/_work/p<NNN>/page_300.png -crop 950x3300+1600+0 +repage /tmp/imp_curr.png
   magick issues/<prev-YYMM>/_work*/p<NNN>/page_300.png -crop 950x3300+1600+0 +repage /tmp/imp_prev.png
   ```
   Adjust the crop X-offset and width to match the column geometry for that issue's page layout.

### 4. Apply changes to the copied HTML

Walk the diff and apply field-by-field. Fields that commonly change between issues:

| Field | What to look for |
|---|---|
| `Chefredakteur` | Usually unchanged. Verify. |
| `Stellv. Chefredakteur` | Often changes — sometimes a copy-paste mistake in the prior issue had Chefredakteur listed twice; fix it from the scan. |
| `Leitender Redakteur` | Field may be absent in some issues. |
| `Redakteure` | List of `xx = Full Name`. New names added, old ones removed each month. Verify alphabetical order by initials and that each name's umlauts/spelling matches the scan. |
| `Redaktionsassistenz` | Single name + phone extension. Changes when staff turns over. |
| `Fotografie` / `Titelfoto` | Mostly the same photographer team; verify. |
| `Titelgestaltung` | Mostly constant. |
| `Layout` | List of layouters; may add/remove. |
| `Auslandsrepräsentation` (Schweiz / USA) | Addresses or phone numbers sometimes update — recheck. |
| `Anzeigenverkaufsleitung` / `Anzeigenleitung` / `Anzeigenverwaltung` | Field name itself can change (`Anzeigenverkauf` → `Anzeigenleitung`). Verify person + extension. |
| `Anzeigenpreise` / `-grundpreise` / `Anzeigen im Computer-Markt` / `… in der Fundgrube` | Numbers (DM amounts) update occasionally — always recheck against scan. |
| `Anzeigenpreisliste Nr. X vom <date>` | The reference price list version. |
| `Bezugspreise` | Subscription prices, Luftpost surcharges per Ländergruppe. Update if changed. |
| `Druck` (printer) | Rarely changes. |
| `Verantwortlich` | Update if the editor or ad-leader changed. |
| `Redaktions-Direktor` / `Vorstand` | Top-level execs; change rarely. |
| `Anschrift` block (Hans-Pinsel-Straße…) | Constant — verify nothing moved. |

### 5. Verify

After edits, re-read the touched lines in the HTML and cross-check against the high-res crop of the Impressum column. The most error-prone fields are:
- **Phone numbers** — OCR confuses digits routinely. The 8606 Schweiz line, for example, became `042-415656` from `042-2231 55/56` — verify *every* digit visually.
- **House numbers** — `Kollerstr. 14` vs `Kollerstr. 3` etc.
- **Umlauts in names** — `Wängler` vs `Wangler`.
- **Field labels** — `Anzeigenverkauf` vs `Anzeigenleitung` vs `Anzeigenverkaufsleitung` are three distinct labels that may appear in different issues.

## Common pitfalls

- **Prior issue had a typo.** The 8605 Impressum lists `Michael Scharfenberger (sc)` twice (as both Chefredakteur AND Stellv. Chefredakteur). Don't propagate the bug — verify Stellv. Chefredakteur against the new scan, which probably gives a different name.
- **Field-name renames.** "Anzeigenverkauf" (8605) vs "Anzeigenleitung" (8606) for the same Brigitta Fiebig entry. Match the scan exactly.
- **Reordering of mid-block fields.** Some issues swap the order of `Fotografie` ↔ `Titelgestaltung` or `Redaktionsassistenz`. The block boundaries (separated by `<hr>`) stay; the order inside a block can drift.
- **Page may have moved.** Most issues use page 179, but TOC can place it ±2 pages.
- **pdftotext-layout is column-jumbled on this page.** The 3-column layout (Depot-Händler / Inserentenverzeichnis / Impressum) confuses the layout extractor — pdftotext output may interleave content from the leftmost columns into the Impressum column. Use vision crops for any field that looks suspicious in the text diff.

## What NOT to do

- Don't blindly copy the prior issue's Impressum without diffing — the editor roster and phone numbers WILL have changed.
- Don't try to OCR the Impressum without first doing the diff against the prior HTML; most lines are constant, and the diff is the fast path to the small set of fields that need editing.
- Don't change the canonical `64er.id` value (`impressum`).
- Don't reformat the `<p><em>…</em>…</p>` shape. The site stylesheet expects `<em>` for the field label and the surrounding `<p>` block per entry, with `<hr>` between major groups.
