# Windows PPTX Lessons

Short notes distilled from real PowerPoint automation work on Windows. Load this file when the task is a project-style deck build, especially with Chinese paths, user-edited sample pages, or repeated COM reruns.

## 1. Classify Slides Before Editing

Do not assume every non-empty slide is meant to be edited.

Useful buckets:

- `instruction slides`: describe homework, rules, or acceptance criteria
- `material slides`: provide logo, text, colors, fonts, screenshots, source photos
- `reference result slides`: already-designed examples that show a target style
- `output slides`: the slides you should actually create or overwrite

More detailed design-role buckets:

- `cover slides`: opening page, report title, event/year/owner summary
- `directory slides`: agenda, catalog, contents, information architecture slide
- `section slides`: chapter divider, section opener, transition slide
- `body slides`: normal detail/content slides
- `ending slides`: thanks page, closing statement, final slogan, wrap-up page

Rule:

- If the user says "use the materials to design it yourself", do not copy reference result slides into output.
- If the user says a manually edited page is "the correct format", treat it as a layout reference, not as raw source material.

Practical interpretation:

- `instruction slides` tell you what to build
- `material slides` tell you what assets and copy you may use
- `reference result slides` tell you the expected finish level or one allowable style direction
- `output slides` are the real deliverable

Do not confuse `ending slides` with any available polished closing demo page. A closing demo may still be only a reference result slide.

## 2. Prefer Raw Assets Over Composited Example Pages

When a deck contains both source assets and polished examples:

1. Extract `ppt/media/*` from the source deck.
2. Inspect which files are raw photos, transparent PNG cutouts, logos, or screenshots.
3. Rebuild from those assets instead of cropping finished slides.

Why:

- finished example slides often contain baked typography, effects, or overlays
- reuse of example pages can accidentally violate "design it yourself"
- raw assets give more layout freedom and cleaner outputs

## 3. Use Exported PNGs as the Truth for Visual QA

Text extraction is not enough for PowerPoint design tasks.

Recommended loop:

1. Generate or edit slides with COM.
2. Export target slides to PNG.
3. Inspect the rendered images for:
   - overlap
   - off-canvas elements
   - weak contrast
   - style mismatch
   - accidental reuse of reference-slide artifacts
4. Fix and rerun.

If the user manually corrected a page, export that page first and visually match against it.

## 4. Chinese Paths Are Often Fine for File I/O but Fragile for Automation

Observed pattern:

- PowerShell can usually access Chinese filenames correctly.
- Python file I/O may still work.
- Office COM open/copy flows can become fragile when strings are hardcoded, glob filters are locale-sensitive, or terminal rendering shows mojibake.

Safer pattern:

1. Discover files from the current directory instead of hardcoding Chinese names in Python strings.
2. Use PowerShell for file copy/rename when Python path handling becomes unstable.
3. For repeated COM work, make an ASCII temporary copy such as `temp_review.pptx` or `temp_append.pptx`.
4. Open and edit the ASCII temp file.
5. Copy the final result back to the desired Chinese filename afterward.

## 5. File Locks Are Common; Design for Them

PowerPoint often keeps files open longer than expected.

Typical symptoms:

- copy/delete fails with "file in use"
- `Presentations.Open` throws unexpected COM errors
- reruns behave inconsistently after a previous crash

Safer pattern:

- always close presentations in `finally`
- always quit the application in `finally`
- if reruns still fail, kill lingering `POWERPNT` processes
- prefer working on a copied temp deck so the user can keep their original open

## 6. Some COM Properties Are Not Writable Even If They Look Like They Should Be

Example observed:

- `AddPicture(...).TransparencyColor` was not settable in a pywin32 run

Implication:

- avoid assuming every VBA-looking property is writable in Python COM
- when a PNG already has transparency, do not add unnecessary transparency-property logic
- patch conservatively after the first failing run

## 7. Duplicate Is Not the Same as Append

`Slides(index).Duplicate()` does not guarantee the duplicate ends up at the end of the deck.

If slide order matters:

1. duplicate
2. capture the returned slide/range
3. explicitly `MoveTo(pres.Slides.Count)` when you need the copy appended

This matters when building deliverables by adding completed slides after material/reference slides.

## 8. Use the User's Intent, Not Only the Slide's Contents

A visually complete slide is not automatically valid output.

Examples:

- a beautiful page might only be a demo/reference page
- a page with almost no text might still be the correct user-approved master format

When the user says:

- "this page is the correct format" -> prioritize its structure
- "do not copy" -> rebuild from assets
- "use materials" -> source from logos/photos/text/color chips, not from finished example pages

## 9. Best Project Workflow for Windows PowerPoint Design Tasks

Recommended order:

1. read requirement pages
2. classify each relevant slide by role
3. identify output slide numbers
4. export candidate reference pages to PNG
5. extract raw assets from `ppt/media/*`
6. inspect raw assets
7. generate project-specific COM script
8. render target slides to PNG
9. visually QA
10. deliver final deck and keep the script

## 10. Keep the Project-Specific Script

For nontrivial deck design, keep a per-project Python script in the working folder.

Benefits:

- deterministic reruns
- easier patching after user feedback
- lower chance of accidental manual drift
- reusable for future slide variants
