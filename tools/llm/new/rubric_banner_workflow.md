# Rubric Banner Workflow

How to add the stylized title-banner image for **Editorial**, **Bücher**, and **Fehlerteufelchen** articles. These three rubrics use the same illustrated banner across every issue (or near-identical variants — Bücher and Fehlerteufelchen actually reuse the exact same image file from issue to issue, while Editorial uses a fresh editor-portrait per issue).

This is companion to `img_workflow.md` (general figure placement) and `leserforum_workflow.md` (which has its own banner convention using `<header>`).

## Which rubrics this covers

| Rubric | Image reused across issues? | Where it sits |
|---|---|---|
| **Editorial** | No — per-issue editor portrait | After `<h1>`, before first `<p>` |
| **Bücher** | Yes — illustrated stack-of-books logo | After `<h1>`, before first `<h2>` |
| **Fehlerteufelchen** | Yes — pink-devil-holding-listing illustration | After `<h1>`, before first `<h3>` |

(Leserforum uses a different convention — see `leserforum_workflow.md`. Its banner sits inside a `<header>` element rather than as a bare `<img class="inline">`.)

## How to run

```
Add rubric banner images for Editorial / Bücher / Fehlerteufelchen
in issues/YYMM per tools/llm/new/rubric_banner_workflow.md.
```

**Input:** the existing article HTML for each rubric in the current issue. For Bücher and Fehlerteufelchen, also the same banner files from the most recent prior issue (`<page>-0.png` named after the prior issue's page number).

**Output:**
- A `<page>-0.png` file in the current issue's dir, named after the current issue's start page.
- The article HTML has `<img src="<page>-0.png" alt="Rubrikname" class="inline">` placed right after the `<h1>`.

## HTML form

Match the convention established for the Editorial across recent issues:

```html
<article>
    <h1>Bücher</h1>

    <img src="97-0.png" alt="Bücher" class="inline">

    <h2>First book section</h2>
    …
</article>
```

Rules:
- **Bare `<img>`, no `<figure>` wrapper.** This differs from the figure-placement rule in `img_workflow.md` for content figures. The rubric banner is a decorative title element, not a captioned figure.
- **`class="inline"`** is required. The site stylesheet uses it to float the banner alongside the first content block.
- **No `width` attribute.** The image's native dimensions (~250–340 px wide) render correctly via CSS.
- **`alt`** is just the rubric name (`Bücher`, `Fehlerteufelchen`). For Editorial, `alt` is the editor's name and title (e.g. `Michael Scharfenberger, Chefredakteur`) since the image is a personal portrait, not a rubric logo.
- **Placement: directly after `<h1>`** and before the first `<h2>`/`<h3>`/`<p>`. One blank line on each side for readability.

## Procedure

### Editorial

The editorial's image is a fresh photo of the issue's Chefredakteur. It's typically already extracted as `<page>-0.png` by the image pass (`img_workflow.md`). If so, just verify the `<img class="inline">` line is in place after the `<h1>` with the editor's name and title in `alt`.

If not extracted: crop the editor portrait from the top of the editorial page, save as `<page>-0.png`, insert the `<img>` line.

### Bücher and Fehlerteufelchen (image reuse)

These two rubrics use a fixed illustrated banner that has been the same file across recent issues (8604 onward, plausibly earlier — check). Don't re-OCR/re-crop it each time; **copy the existing PNG from the most recent prior issue and rename it for the current issue's start page**.

1. Locate the most recent prior issue's banner file:
   ```bash
   ls issues/<prev-YYMM>/*.png | grep -E '\b(73|107|87|66|…)-0\.png'
   ```
   The major number depends on where the rubric appeared in that issue. Confirm visually that you have the right banner by `Read`ing the file.
2. Copy and rename to match the current issue's start page:
   ```bash
   cp issues/<prev-YYMM>/87-0.png issues/<curr-YYMM>/73-0.png   # Fehlerteufelchen, was p.87 in 8605, now p.73 in 8606
   cp issues/<prev-YYMM>/107-0.png issues/<curr-YYMM>/97-0.png  # Bücher, was p.107 in 8605, now p.97 in 8606
   ```
3. Insert the `<img>` line into each article:
   ```html
   <article>
       <h1>Bücher</h1>

       <img src="97-0.png" alt="Bücher" class="inline">

       <h2>First book section</h2>
   ```

### Verifying the image is reusable

Before copying, `Read` the prior-issue PNG to confirm it's the rubric banner and not a content figure that happens to share the `-0` suffix. The Bücher banner should show a stack-of-books illustration with "BÜCHER" text. The Fehlerteufelchen banner should show a pink devil character holding a listing scroll.

If the prior issue's banner image was renumbered/replaced, walk back through earlier issues (`8604`, `8603`, …) until you find a usable copy.

## What NOT to do

- Don't wrap the banner in `<figure>` + `<figcaption>`. It's a decorative title image, not a captioned figure.
- Don't add `width="…"` unless the image renders too large at native dimensions (rare).
- Don't drop `class="inline"` — the site styling needs it.
- Don't re-crop the Bücher/Fehlerteufelchen banner from the new issue's scan — these illustrations are reused identically and re-cropping just introduces slight pixel differences from a known-good source.
- Don't place the `<img>` after the first content block. It goes immediately after `<h1>`.
