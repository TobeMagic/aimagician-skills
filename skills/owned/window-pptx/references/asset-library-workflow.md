# Asset Library Workflow

Use this workflow when a PPT project needs stock images, illustrations, vectors, backgrounds, or design references.

## Principle

Assets must be local, traceable, and reusable.

Do not insert remote image URLs directly into PowerPoint. Download selected assets into the project folder and record source metadata.

## Default Folder Layout

```text
ppt-project/
  assets/
    downloads/
      pixabay/
    icons/
    photos/
    backgrounds/
  .window-pptx/
    asset_manifest.json
    cache/
      pixabay/
```

## Pixabay Setup

Use environment variable:

```powershell
# Set PIXABAY_API_KEY in the Windows/user environment before running.
```

Do not write API keys into:

- `REQUEST.md`
- generated scripts
- manifests
- logs
- git-tracked files
- final deck notes

If a key was pasted in chat or a document, treat it as exposed and recommend rotating it.

## Search Command

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --search-images "technology background" `
  --image-lang zh `
  --image-type photo `
  --image-orientation horizontal `
  --image-order popular `
  --image-per-page 20 `
  --no-save `
  --json
```

Default search policy:

- `safesearch=true`
- `order=popular`
- `per_page=20`
- `image_type=all` unless the requested style is clear
- `orientation=horizontal` for wide slide backgrounds
- `lang=zh` for Chinese prompts, `en` for English design terms

## Download Command

Download a selected result URL:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --download-image "https://..." `
  --no-save `
  --json
```

Or search and download the first usable result:

```powershell
python ~/.codex/skills/window-pptx/scripts/window_pptx_automation.py `
  --project-dir C:\ppt-project `
  --search-images "gold laurel award" `
  --image-type vector `
  --download-top-image `
  --no-save `
  --json
```

## Manifest Requirements

Every downloaded asset should be recorded with:

- local path
- provider
- source URL
- page URL
- creator/user if available
- tags
- download time
- where it is used

Use the manifest to avoid losing provenance when the PPT is revised later.

## Selection Rules

Prefer:

- transparent PNG or vector for icons/components
- high-resolution horizontal photos for backgrounds
- simple backgrounds when text will sit on top
- illustrations with enough empty space for title placement
- consistent visual language across one deck

Avoid:

- watermarked previews
- low-resolution screenshots
- dense photos behind body text
- mixed icon styles
- hotlinked URLs
- assets with unclear usage rights

## PPT Integration Rules

- Use local downloaded files in `Shapes.AddPicture`.
- Crop through PowerPoint only for simple rectangular framing.
- For exact clipping, masks, or Boolean-like shapes, generate transparent PNG assets with Python/PIL and insert them.
- Record the final local asset path and used slide/module in `.window-pptx/asset_manifest.json`.

## Pixabay API Notes

Pixabay webformat URLs can be temporary. Download assets before use and do not rely on remote URLs during final deck generation.

Official API reference: https://pixabay.com/api/docs/
