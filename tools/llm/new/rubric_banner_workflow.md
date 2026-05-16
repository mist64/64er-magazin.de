# Rubric Banner Workflow

How to add the stylized title-banner image for **Editorial**, **Bücher**, **Fehlerteufelchen**, and **Leserforum** articles. Three of the four use a fixed illustrated banner that's reused identically across recent issues; Editorial uses a fresh editor-portrait per issue.

This is companion to `img_workflow.md` (general figure placement) and `leserforum_workflow.md` (Leserforum's article structure).

## Which rubrics this covers

| Rubric | Image reused across issues? | HTML wrapping | Where it sits |
|---|---|---|---|
| **Editorial** | No — per-issue editor portrait | bare `<img class="inline">` | After `<h1>`, before first `<p>` |
| **Bücher** | Yes — illustrated stack-of-books logo | `<figure><img></figure>` (NOT inline) | After `<h1>`, before first `<h2>` |
| **Fehlerteufelchen** | Yes — pink-devil-holding-listing illustration | bare `<img class="inline" width="300">` | After `<h1>`, before first `<h3>` |
| **Leserforum** | Yes — envelopes-on-stripes (from 8604 onward; 8601–8603 used a different stamp/pencil banner) | `<header><img></header>` inside `<article class="qa">` | Top of article body |

Each rubric has its OWN wrapping convention — don't unify them. Match what the prior issue's HTML did.

## How to run

```
Add rubric banner images for Editorial / Bücher / Fehlerteufelchen
in issues/YYMM per tools/llm/new/rubric_banner_workflow.md.
```

**Input:** the existing article HTML for each rubric in the current issue. For Bücher and Fehlerteufelchen, also the same banner files from the most recent prior issue (`<page>-0.png` named after the prior issue's page number).

**Output:**
- A `<page>-0.png` file in the current issue's dir, named after the current issue's start page.
- The article HTML has `<img src="<page>-0.png" alt="Rubrikname" class="inline">` placed right after the `<h1>`.

## HTML forms (per rubric)

Each rubric has a different wrapping. Match the existing convention from the prior issue.

**Editorial** — bare `<img class="inline">`, alt is the editor's name + role:

```html
<article>
    <h1>Im neuen Gehäuse…</h1>

    <img src="8-0.png" alt="Michael Scharfenberger, Chefredakteur" class="inline">

    <p>First paragraph…</p>
</article>
```

**Bücher** — `<figure>` wrapper, alt is the rubric name:

```html
<article>
    <h1>Bücher</h1>

    <figure>
        <img src="97-0.png" alt="Bücher">
    </figure>

    <h2>First book section</h2>
    …
</article>
```

**Fehlerteufelchen** — bare `<img class="inline" width="300">`, alt is the rubric name:

```html
<article>
    <h1>Fehlerteufelchen</h1>

    <img src="73-0.png" width="300" alt="Fehlerteufelchen" class="inline">

    <h3>First correction section</h3>
    …
</article>
```

**Leserforum** — `<header>` wrapper (see `leserforum_workflow.md`):

```html
<article class="qa">
    <header>
        <img src="16-0.png" alt="Leserforum" title="Leserforum">
    </header>

    <section>…</section>
</article>
```

Common rules across all four:
- **Placement: directly after `<h1>` / start of `<article>`** and before the first content block. One blank line on each side for readability.
- **Filename**: `<page>-0.png` where page = the article's start page.

## Procedure

### Editorial

The editorial's image is a fresh photo of the issue's Chefredakteur. It's typically already extracted as `<page>-0.png` by the image pass (`img_workflow.md`). If so, just verify the `<img class="inline">` line is in place after the `<h1>` with the editor's name and title in `alt`.

If not extracted: crop the editor portrait from the top of the editorial page, save as `<page>-0.png`, insert the `<img>` line.

### Bücher / Fehlerteufelchen / Leserforum (image reuse)

These three rubrics use fixed illustrated banners that have been the same file across recent issues. Don't re-OCR/re-crop them each time; **copy the existing PNG from the most recent prior issue and rename it for the current issue's start page**.

1. Locate the most recent prior issue's banner file. The major number = where the rubric sat on that issue's page:
   ```bash
   ls issues/<prev-YYMM>/*.png | grep -E '\b(<prev-page>)-0\.png'
   ```
2. `Read` the file to verify it's the right banner (Bücher = stack-of-books, Fehlerteufelchen = pink devil holding scroll, Leserforum = envelopes on red/orange stripes).
3. Copy and rename to match the **current** issue's start page:
   ```bash
   cp issues/<prev-YYMM>/87-0.png issues/<curr-YYMM>/73-0.png   # Fehlerteufelchen, was p.87 in 8605, now p.73 in 8606
   cp issues/<prev-YYMM>/107-0.png issues/<curr-YYMM>/97-0.png  # Bücher, was p.107 in 8605, now p.97 in 8606
   cp issues/<prev-YYMM>/16-0.png issues/<curr-YYMM>/16-0.png   # Leserforum, page 16 is constant
   ```
4. Insert the `<img>` line into each article per the rubric's wrapping convention (see "HTML forms" above).

### Banner history note

If the prior issue's banner image was renumbered/replaced or doesn't exist, walk back through earlier issues until you find a usable copy. Known history quirks:
- **Leserforum** banner changed between 8603 and 8604 (8601–8603 used a "LESER FORUM 64er" stamp + pencil illustration; 8604 onward uses the envelopes-on-stripes design).
- **Fehlerteufelchen** filename pattern shifted from `*-1.png` (8601–8603) to `*-0.png` (8604+).

Match the current issue's print — if the new issue's scan shows a different banner, fall back to extracting fresh from the page scan rather than reusing.

## What NOT to do

- Don't unify the wrapping. Each rubric has its own convention (Editorial/Fehlerteufelchen = bare `<img class="inline">`; Bücher = `<figure>`; Leserforum = `<header>`). Match the prior issue.
- Don't add `<figcaption>` — these are decorative title images, not captioned figures.
- Don't add `width="…"` unless the prior issue's HTML did (Fehlerteufelchen always uses `width="300"`; the others don't).
- Don't drop `class="inline"` from Editorial/Fehlerteufelchen — the site styling needs it.
- Don't re-crop reused banners (Bücher/Fehlerteufelchen/Leserforum) from the new issue's scan — they're reused identically and re-cropping introduces pixel-level differences from a known-good source.
- Don't place the `<img>` after the first content block. It goes immediately after `<h1>` (or inside `<header>` for Leserforum).
