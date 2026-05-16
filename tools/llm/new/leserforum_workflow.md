# Leserforum Workflow

How to format the `Leserforum` (reader Q&A column) article in an issue. The Leserforum is a recurring rubric that appears in every issue and uses a specific Q&A HTML structure shared across issues so the styling is consistent.

## How to run

```
Format issues/YYMM/<page> Leserforum.html per tools/llm/new/leserforum_workflow.md.
```

**Input:** the merged-OCR `<page> Leserforum.html` produced by the body workflow (typically flat `<h2>`/`<p>` paragraphs in ALL CAPS, with reader names in ALL CAPS at paragraph ends).

**Output:** same file, restructured into the Q&A shape, with a banner image cropped from page N.

## CRITICAL: preserve magazine content 100%

This is the single most important rule for the Leserforum. **Every printed letter, name, address, and answer line stays.** Don't summarize, drop, or normalize beyond the structural reshaping listed below.

- **Reader addresses** stay verbatim. Some readers include their full postal address (street + ZIP + town) so other readers can write directly. Those are part of the magazine — keep them.
- **Original typos in names** stay (`Wolfgang Fäer`, `Frits Sanderds`, `Ing. Othmar Kreil`). OCR-only fixes (per `cleanup_workflow.md`).
- **Source-issue markers** (`Ausgabe N/YY`) stay — they tell readers which prior issue's letter this is a follow-up to.
- **Guest-replier names** stay (when an answer is by a named expert, not the editorial team).
- **Info: footer** stays. Often contains vendor addresses or product info — `<p class="source">`.

## HTML structure

Match the convention established in 8601–8605:

```html
<!DOCTYPE html>
<html lang="de">

<head>
    <title>Leserforum</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../style.css">
    <meta name="64er.issue" content="N/YY">
    <meta name="64er.pages" content="16-17">
    <meta name="64er.head1" content="Leserforum">
    <meta name="64er.toc_category" content="Rubriken">
    <meta name="64er.id" content="leserforum">
</head>

<body>
    <article class="qa">
        <header>
            <img src="16-0.png" alt="Leserforum" title="Leserforum">
        </header>

        <section>
            <h2>Topic title in Title Case?</h2>

            <div class="q">
                <p>Question text…</p>
                <p class="author">Reader Name<br>Street 12, 9999 City</p>   <!-- address inside author, separated by <br> -->
                <p class="noindent">Ausgabe N/YY</p>                  <!-- if printed -->
            </div>

            <div class="a">
                <p>Editor's reply…</p>
                <p class="author">Guest Replier Name</p>              <!-- if reply is signed -->
            </div>

            <p class="source">Info: vendor info, address, product details</p>   <!-- if printed -->
        </section>

        <!-- repeat <section> per topic -->
    </article>
</body>

</html>
```

### Required meta tags

- **`64er.head1`** = `Leserforum` (so the rubric banner renders)
- **`64er.toc_category`** = `Rubriken`
- **`64er.id`** = `leserforum` (canonical across issues — see `64er_id_workflow.md`)
- **NO** `<meta name="author">` — Leserforum has no overall author; every question has its own asker, every reply may have its own guest signer.

### Banner image (`16-N.png`)

Each Leserforum has a stylized title banner photo at the top of page N (envelopes / letter motif). Crop it from the high-res scan:

```bash
magick _work/p<NNN>/page_300.png -crop <W>x<H>+<X>+<Y> +repage <N>-0.png
```

Verify by `Read`ing the crop. The banner sits in the upper-left of the first Leserforum page. Filename is `<startpage>-0.png` (e.g. `16-0.png`).

### Section structure

One `<section>` per topic. Each `<section>` contains:

1. `<h2>` — the topic heading in **Title Case** (the OCR import usually delivers ALL CAPS; convert).
2. One or more `<div class="q">` — questions. Multiple `<div class="q">` per section when the editor groups two readers asking the same thing (the answer below then addresses both).
3. Optionally one `<div class="a">` — the editor's reply (when printed). Some questions are unanswered ("Wer kann helfen?" calls for reader replies in the next issue).
4. Optionally one `<p class="source">` — the Info/addresses footer.

### Inside `<div class="q">`

In order:
- One or more `<p>` for the question body. Multi-part questions use `(1) …` `(2) …` numbering as separate paragraphs:
  ```html
  <div class="q">
      <p>(1) First sub-question…</p>
      <p>(2) Second sub-question…</p>
      <p class="author">Reader Name</p>
  </div>
  ```
  Don't use `<ol>` — the (N) prefix in plain `<p>` is the convention.
- `<p class="author">` for the asker. Convert ALL CAPS OCR import to Title Case (`HANS FUSS` → `Hans Fuss`). Preserve original punctuation and umlauts. **If the asker's address is printed, append it inside the same `<p class="author">` after a `<br>`** — not a separate paragraph.
- `<p class="noindent">` for the source-issue marker `Ausgabe N/YY`, if this is a follow-up to a prior question. Always last inside the `<div class="q">`.

### Inside `<div class="a">`

- One or more `<p>` for the reply body. Multi-part answers mirror the question's `(1)` `(2)` numbering.
- Optionally one `<p class="author">` at the end if the reply is signed by a guest expert (not the editorial team). The editorial team's own answers are unsigned.

### `<p class="source">`

Goes after `</div>` of the last `<div class="a">`, inside the same `<section>`. Used for the printed `Info:` block (typically vendor address + price + product details). Multiple lines via `<br>`:

```html
<p class="source">Info: Vendor Name, Street 1, 12345 City<br>
    Product Name, 49 Mark</p>
```

### Special: long reader letters

Occasionally a "reader letter" is not a question but a fan letter or opinion piece (typical: 8606's "Eine Lanze für die 1541…"). Treat it like a single-question `<section>`: `<h2>` title, `<div class="q">` with all the prose `<p>`s in order, `<p class="author">` at the end, no `<div class="a">`. The fact that it's an opinion rather than a question doesn't change the HTML structure.

### Optional intro `<aside>`

Some Leserforums (e.g. 8601) include a short intro `<aside>` between sections explaining how to submit questions ("Fragen Sie doch"). Reproduce as a normal `<aside>` between two `<section>` elements:

```html
<aside>
    <h2>Aside title</h2>
    <p>Aside body…</p>
</aside>
```

## Things to fix during conversion

In the OCR-imported article, expect to handle:

- **ALL CAPS → Title Case** in `<h2>` and `<p class="author">`. The print uses ALL CAPS for both; every other issue's HTML normalizes to Title Case.
- **`<ol>` → `<p>(N) …</p>`** for multi-part questions. The OCR import sometimes wraps sub-questions as `<ol><li>` — replace with separate `<p>(N)` paragraphs.
- **Inline name + `<br>`** at end of `<p>` → split into `<p class="author">Name</p>`.
- **OCR errors in headings**: typical confusions like `INTEREACE` → `Interface` (F↔E), `PROIEKTOREN` → `Projektoren` (I↔J), `DlN-A4` → `DIN-A4` (l↔I). See `cleanup_workflow.md`. Don't fix original typos in reader names.
- **Stray punctuation**: `.als Hardcopy` → `als Hardcopy` (stray period before word), etc.
- **`<meta name="author" content="XXX">`**: remove. Leserforum has no overall author.
- **Missing `<meta name="64er.head1">`**: add.

## What NOT to do

- Don't drop addresses, source-issue markers, or guest-replier names. **Preserve 100%.**
- Don't invent answers. If a printed question has no printed reply, the `<section>` has no `<div class="a">`. Period.
- Don't merge two reader letters into one `<div class="q">` just because they share a topic. The print groups them by section (`<h2>`) but each gets its own `<div class="q">` with its own author.
- Don't normalize names (drop "Dipl.-Kfm.", drop suffix "Niederlande" / "Ing.", remove middle initials). Match what's printed.
- Don't translate or modernize old German spelling (`muß`, `daß`, `Adreß`). See `cleanup_workflow.md`.

## Final report — present a summary table

After the conversion, present:

| Section heading | Asker | Address? | Source-issue? | Reply? | Guest replier? | Info? |
|---|---|---|---|---|---|---|
| Wer kann helfen? | Hans Fuss | — | — | — | — | — |
| MIDI mit C 64? | Jürgen Driessen | yes | — | — | — | — |
| »Apfelmännchen« mit MPS-Drucker | Michael Nappe | — | Ausgabe 4/86 | yes | Udo Kern | yes |
| … | | | | | | |

Flag explicitly:
- Sections where the answer was attributed to a guest replier (verify the name).
- Sections without a reply (the editor is forwarding the question to other readers — verify by reading the scan that no reply was printed).
- Headings that required Title Case conversion (verify against scan that you didn't accidentally lowercase a proper noun).
- Any OCR error fixes applied to a heading.
- Whether the banner image (`<page>-0.png`) was successfully cropped.

The user will scan this table to decide where to spot-check.
