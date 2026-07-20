# PPT Homework Execution Playbook

Use this playbook when a user gives a folder that contains a homework/request `.pptx`, materials, examples, fonts, GIF/video references, and asks the agent to complete the deck with PowerPoint COM.

The goal is not to "edit whatever slide looks unfinished". The goal is to understand the assignment intent, rebuild deliverable slides from source materials, verify the rendered result, and leave a deterministic rerunnable workflow for future fixes.

## 1. Operating Contract

Always preserve the source deck.

Default output strategy for homework decks:

1. keep all original instruction/material/reference slides
2. create one new completed slide for each assignment
3. insert the completed slide immediately after the relevant original target/reference slide
4. save the final deck under `output/`
5. keep scripts, logs, media inventory, exports, and audits under `.window-pptx/`

Only overwrite an existing slide when the user explicitly says to overwrite that page.

For WSL-hosted repositories, WSL is only the orchestrator. Run real COM work from Windows:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
  "python 'D:\path\to\project\.window-pptx\complete_homework.py'"
```

The Windows Python process must import `win32com.client` and open `PowerPoint.Application`.

## 2. Required First Pass

Before writing the final editing script, create enough evidence to avoid confusing instruction pages, material pages, and reference pages.

Minimum first pass:

1. export all slides to PNG
2. extract `ppt/media/*`
3. create a media contact sheet
4. extract visible text into `analysis.json` or equivalent
5. identify assignment groups and expected deliverable slides
6. identify fonts mentioned by the deck and any font folders near the project
7. identify GIF/video/media references for animation-sensitive tasks

Use the slide roles from `windows-pptx-lessons.md`:

- `instruction slides`: requirements, timing, grading rules
- `material slides`: logos, raw text, colors, fonts, people/photos/assets
- `reference result slides`: examples of expected polish or animation
- `output slides`: the slides the agent must create, duplicate, or append

If a polished page appears after a requirement page, treat it as a reference result first, not as a screenshot to reuse.

## 3. Build From Raw Assets

Prefer extracted media files over screenshots of finished slides.

Good source assets:

- original JPEG/PNG photos from `ppt/media/*`
- transparent PNG logos or cutouts
- GIF/video frames used as motion references
- text copied from material slides
- color chips or font names shown on material slides

Avoid:

- placing a screenshot of a reference slide as the deliverable
- cropping a finished slide unless the user explicitly asks for exact replication
- stretching people or product photos to fit a box
- placing opaque masks over text without checking the exported PNG

When a user says the rendered/image version is visually correct but the final deck must be editable, load `editable-deliverable-rebuild.md` and treat that rendered page as a gold reference only. Rebuild the deliverable from independent picture assets plus native PPT text boxes, shapes, masks, cards, timelines, and lines.

If the user says "only change layout", preserve the original title colors, brand colors, typography role, and content hierarchy. Do not import another slide or template if it changes those visual constants.

For image clipping / Boolean-like work:

- PowerPoint COM shape operations can be fragile and version-dependent
- when exact visual clipping matters, generate a transparent PNG with Python/PIL alpha masks
- use the clipped PNG in PowerPoint, and keep the generated asset in `.window-pptx/generated_assets*`

For person/team pages:

- extract people from source images when possible
- remove backgrounds with a local tool such as `rembg` when available
- preserve aspect ratio
- do not crop away body edges unless the reference requires it
- inspect watermarks from source photos and report if they remain

For gradient masks:

- use native PowerPoint gradients when they are simple and stable
- for diagonal/irregular masks over images, generate transparent PNG overlays with PIL
- keep text above masks unless the mask is intentionally part of the text treatment
- use lighter transparency over body text than over image-only areas

## 4. Font Workflow

Do not guess fonts from what the terminal happens to display.

Audit three separate things:

1. fonts mentioned in the deck/material pages
2. fonts installed in Windows
3. fonts already used inside the current PPT

Recommended checks:

```powershell
Add-Type -AssemblyName System.Drawing
$fonts = New-Object System.Drawing.Text.InstalledFontCollection
$fonts.Families | ForEach-Object { $_.Name } | Sort-Object
```

PowerPoint COM can inspect fonts already used in the deck:

- `Presentation.Fonts`
- recursive traversal of `Slide.Shapes`
- `Shape.TextFrame.TextRange.Font.Name`
- grouped shapes and table cells must be traversed explicitly

For local font files, parse internal family names with `fontTools` before using them:

```python
from fontTools.ttLib import TTFont
font = TTFont("path/to/font.ttf")
```

Default professional font policy from the observed workflow:

- Chinese decorative title: use the user's specified display font, such as `云峰飞云体`
- Chinese body: use the user's specified body font, or a stable installed black font such as `Noto Sans SC`
- English: use `Arial`

When recipient machines may not have the same fonts:

- rasterize large decorative titles into PNGs using the `.ttf` / `.otf` file directly
- rasterize typography-sensitive body copy if exact layout matters
- keep normal editable text only when fallback risk is acceptable
- normalize fonts on duplicated reference slides before adding animations

Do not claim "PowerPoint cannot check fonts". The precise rule is:

- COM can check fonts used by a presentation
- Windows font APIs are better for checking installed fonts

## 5. Design Implementation Patterns

Keep one project-specific script, for example:

```text
.window-pptx/
  complete_homework.py
  analysis.json
  media/
  generated_assets/
  exports/
  run_log.json
  animation_effects.json
  font_audit.json
```

The script should be deterministic and rerunnable:

- define source, output, media, generated asset, export, log paths at the top
- never modify the source deck in place
- use late-bound `win32com.client.dynamic.Dispatch("PowerPoint.Application")`
- close presentations in `finally`
- quit PowerPoint in `finally`
- remove previous exports before rerunning
- write a JSON run log with slide names, source assets, output paths, and verification data

Useful COM helpers to include in project scripts:

- `rgb(r, g, b)`
- `const(name, fallback)`
- `add_text(...)`
- `add_box(...)`
- `add_picture(...)`
- `set_text_font(...)`
- `normalize_slide_text_fonts(...)`
- `duplicate_slide_after(...)`
- `clear_slide(...)`
- `clear_animations(...)`
- `export_sample(...)`
- `effect_rows(...)`
- `transition_row(...)`

If duplicating slides, remember:

- `Slides(index).Duplicate()` does not guarantee final position
- explicitly move the duplicated slide to the desired index
- name completed slides predictably, such as `assignment_4_completed`

## 6. Animation and Transition Tasks

Animation homework cannot be validated by screenshots alone.

For each animation-sensitive completed slide, export a structured effect table:

- sequence index
- target shape name
- effect type
- trigger type
- duration
- delay
- transition entry effect
- transition duration/speed when available

Compare the table with the visible requirement.

Examples:

- "fade in + left-to-right path + disappear" must be separate effects on the moving object
- "title wipes with the light" means the title wipe trigger should be tied to the light movement timing
- "dynamic carousel based on GIF" means inspect GIF/reference frames, then sequence image fade-in/fade-out steps
- "Morph / smooth transition" may require `SlideShowTransition.EntryEffect = 3954` when pywin32 constants do not expose `ppEffectMorphByObject`

Do not say animation is complete just because an effect count is nonzero.

## 7. Visual QA Loop

Every serious visual deck task needs at least one render-and-review loop.

Required QA artifacts:

- exported PNG for every completed slide
- contact sheet of all completed slides
- animation effect JSON for animation slides
- font audit JSON when fonts matter
- run log JSON listing output paths and slide indexes

Inspect exported PNGs for:

- masks covering text
- unreadable contrast
- people stretched or clipped incorrectly
- body text overflow
- decorative image clipping that looks accidental
- copied reference-slide artifacts
- slide order mistakes
- missing assignment output slides

If the user says a page is unsatisfactory, do not patch blindly:

1. restate the concrete failure
2. update the deterministic script or generated assets
3. rerun the full generation
4. regenerate PNG/contact sheet
5. show the updated artifact paths

For editable rebuild work, add a structural QA step:

1. unpack or inspect the generated `.pptx`
2. verify completed slides do not contain a full-slide picture named like `full_slide_image`
3. verify completed slides contain multiple `shape/text/picture` objects
4. verify reference/instruction pages are the only pages allowed to use full-slide screenshots

## 8. Plugin Policy During Homework

iSlide, OKPlus, and similar PowerPoint add-ins may be installed but are optional.

Safe workflow:

1. list registered add-ins through the 32/64-bit registry-only route
2. inspect ProgID, CLSID, load behavior, and manifest metadata without starting PowerPoint
3. consult vendor documentation for any public automation contract
4. investigate live objects only in a separately approved interactive run
5. call only documented, safe plugin APIs
6. otherwise reproduce the output with native PowerPoint COM

Do not depend on plugin-only UI behavior for the core deliverable unless the user provides a documented callable API.

## 9. Completion Criteria

Only report completion after:

- output deck exists under `output/`
- completed slide count matches assignment count
- completed slides are inserted at the intended locations
- exported PNGs exist for all completed slides
- visual QA has been performed on the PNGs or contact sheet
- animation effect JSON exists for animation tasks
- font audit is done when fonts are part of the requirement
- unresolved limitations are explicitly stated

The final response should include the output deck path, review/contact-sheet path, and any known limitations such as source-photo watermarks or plugin APIs not being callable.
