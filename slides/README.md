# Slides

`slides.md` is a [Marp](https://marp.app/)-compatible markdown deck for the 4–7 minute final-project video. 9 slides, ~6:20 target speaking time (see `../VIDEO_SCRIPT.md` for the per-slide script and timing).

## How to display / export

Pick whichever is easiest — the markdown file is the source of truth either way.

### Option A: VS Code extension (easiest)

1. Install the **"Marp for VS Code"** extension (marp-team.marp-vscode).
2. Open `slides.md`.
3. Click the preview icon (top-right of editor) — slides render live in a side pane.
4. To export: Ctrl/Cmd+Shift+P → "Marp: Export slide deck" → choose PDF / PPTX / HTML.

### Option B: Marp CLI

```bash
npm install -g @marp-team/marp-cli

# Live preview in browser
marp --server slides/

# Export to PDF (what you'd present from)
marp slides/slides.md --pdf --output slides/slides.pdf

# Export to PPTX (for Keynote / PowerPoint / Google Slides)
marp slides/slides.md --pptx --output slides/slides.pptx

# Standalone HTML (double-click to open in any browser, no server)
marp slides/slides.md --html --output slides/slides.html
```

### Option C: Web-based (no install)

Paste the contents of `slides.md` into [marp.app](https://marp.app/) — renders in the browser.

## Figures referenced

All from `../examples/figures/` (already committed):

| Slide | Figure |
|---|---|
| 5 (Datasets) | `hippocampus_demo.png` |
| 6 (Main result) | **`ablation_comparison.png`** ← the headline |
| 7 (Ablation) | `ablation_headline_spleen.png` |

Slides 1, 2, 3, 4, 8, 9 are text-only (no PNG dependency).

## Editing tips

- Each `---` on its own line is a slide break.
- `<!-- _class: lead -->` styles a slide as a title/centered layout.
- `<!-- _class: big-figure -->` centers the image on the main-result slide.
- `![bg right:40% width:480](path.png)` places an image on the right 40% of the slide as a background.
- Adjust global font size in the top-of-file `style:` block (`section { font-size: 26px; }`).

## Timing reminder

Target: **6:20** (inside the 4–7 min grading window).
If over: trim slide 2 or slide 5 first — see `VIDEO_SCRIPT.md` → "If you run long".
