# Video Script — Retina U-Net Reproduction

**CS598 DL4H Spring 2026** · Jeffrey Chen (jc182) · Mark Chen (mc2115)
**Paper**: Jaeger et al., *Retina U-Net: Embarrassingly Simple Exploitation of Segmentation Supervision for Medical Object Detection*, [arXiv:1811.08661](https://arxiv.org/abs/1811.08661)

**Target length**: 5:30–6:00 (inside the 4–7 min grading band with buffer)
**Slide count**: 9
**Format**: each slide has its bullets + a speaker script (read-aloud). Speech is roughly 150 wpm, so the time estimates are measured against the script word counts.

**Two-person split suggestion** (optional): Slides 1–4 on one speaker, 5–9 on the other. Transition lines provided at slide 4→5.

Recording tip: open the `examples/figures/ablation_comparison.png` full-screen when you hit slide 6 — it's the headline visual. All other figures live in `examples/figures/`.

---

## Slide 1 — Title · ~20s

**Visual**
- Title: *Reproducing Retina U-Net: Medical Object Detection via Segmentation Supervision*
- Your names + NetIDs
- Paper link: arxiv.org/abs/1811.08661
- "CS598 DL4H — Spring 2026 Final Project"

**Script**
> "Hi, I'm Jeffrey Chen, and I'm Mark Chen. We're reproducing *Retina U-Net*, a 2018 paper by Jaeger et al. that proposes a simple way to use segmentation masks to improve object detection in medical images."

---

## Slide 2 — The Problem · ~45s

**Visual**
- Two columns, left: "segmentation output → heuristic post-processing → boxes"; right: "object detector → boxes directly (but ignores masks)"
- A sample medical slice with both a mask overlay and a bounding box overlay

**Bullets**
- Medical imaging needs **object-level** outputs: find the tumor, the lesion, the nodule.
- **Segmentation models** (like U-Net): use pixel-level masks well, but need hand-crafted post-processing (thresholding, connected components) to turn pixels into boxes.
- **Object detectors** (like RetinaNet): emit boxes cleanly, but **throw away** the pixel masks that medical datasets often provide.
- Medical datasets are small, and pixel annotations are expensive. Wasting supervision is bad.

**Script** (~90 words, ~36s)
> "Medical imaging tasks often need object-level outputs — where is the tumor, draw a box around the nodule. But medical datasets typically come with pixel-level segmentation masks, which are expensive to produce. The two obvious approaches each leave something on the table. Segmentation models use those masks well but need heuristic post-processing to turn pixels into boxes. Object detectors emit boxes cleanly but ignore the masks entirely. The paper asks: can we exploit both at once in a simple end-to-end model?"

---

## Slide 3 — The Method · ~60s

**Visual**
- Simplified architecture diagram. Left-to-right flow: *Input image → ResNet backbone → FPN → two heads (RetinaNet + U-Net decoder)*. FPN arrows split to both heads.
- Optional overlay: L = L_cls + L_bbox + λ·L_seg

**Bullets**
- **Shared ResNet-FPN backbone** (feature pyramid at P3–P7)
- **RetinaNet detection head**: classification (focal loss) + bbox regression (smooth-L1)
- **U-Net-style decoder** over the FPN features → pixel-wise segmentation map
- **Combined loss**: `L = L_cls + L_bbox + λ · L_seg`
- Segmentation is used **only during training** for extra supervision — inference still returns detection boxes (plus the mask if you want it)

**Script** (~130 words, ~52s)
> "Retina U-Net's answer is, as the paper title says, embarrassingly simple. Attach a U-Net-style segmentation decoder to the same ResNet-FPN backbone that RetinaNet already uses. Then train the whole thing jointly with a combined loss: focal loss on classification, smooth-L1 on bounding boxes, plus per-pixel binary cross-entropy on segmentation, weighted by a hyperparameter lambda. The segmentation decoder exists to inject richer supervision during training — radiologists' mask annotations become gradient signal. At inference you can take the detections, or the mask, or both. And that's basically it — it's not a new architecture, it's a training objective."

---

## Slide 4 — Our Reproduction · ~45s

**Visual**
- A four-box diagram labeled: `RetinaUNetCTDataset` / `RetinaUNetDetectionTask` / `RetinaUNet` / `train_one_epoch + evaluate`
- Bottom bar: "54 unit tests · Colab notebook · CLI scripts"
- Corner label: "**Scope:** 2D slice-wise (paper is 3D patch-wise)"

**Bullets**
- PyHealth contribution: **Dataset + Task + Model + Training loop**
- Built on **torchvision 2D RetinaNet** (shared backbone via a forward hook; seg decoder runs off the cached FPN output)
- **ResNet-18 FPN backbone**, pyramidal U-Net decoder over P3–P7
- `seg_weight` (λ) is a first-class knob → baseline vs. Retina U-Net ablation comes free
- 54 unit tests, Colab notebook, `scripts/download_data.sh`, `run_ablation.sh`, `run_tests.sh`
- **Scope reduction**: 2D slice-wise reimplementation (paper is 3D). We'll explain the cost at the end.

**Script** (~110 words, ~44s)
> "We built a full PyHealth contribution: a CT dataset class, the detection task, the Retina U-Net model itself, plus training helpers and a Colab notebook. We lean on torchvision's 2D RetinaNet for the detector and attach our own pyramidal U-Net decoder to the same backbone via a forward hook, so both heads share one backbone pass. The segmentation weight lambda is a first-class parameter, which means setting it to zero gives us the pure RetinaNet baseline for free. One upfront caveat: the paper is 3D end-to-end; we're 2D, because torchvision has no 3D RetinaNet and porting is weeks of work. We'll come back to what that costs."

---

**[transition]** *Jeffrey hands off to Mark:* "Mark will walk through our datasets and results."

---

## Slide 5 — Datasets · ~45s

**Visual**
- Three sample axial slices side-by-side with bounding boxes overlaid (use `examples/figures/hippocampus_demo.png` as the hippocampus panel; build equivalents for spleen and LUNA16 if time allows, otherwise just bullet the specs)

**Bullets**
- **Hippocampus** (MSD Task04, MR, 22 train patients, ~490 lesion slices) — small substructure, anatomically consistent across slices.
- **Spleen** (MSD Task09, CT, 9 train patients, ~680 lesion slices, abdominal window HU [-160, 240]) — a large, high-contrast organ; easiest detection target.
- **LUNA16** (preprocessed, CT, 400 train slices, lung window HU [-1000, 400]) — 5–25 pixel nodules, well under 1% foreground — the paper's actual target domain.
- All three are publicly downloadable without TCIA/LIDC credentialing.

**Script** (~90 words, ~36s)
> "We evaluated on three public datasets. Hippocampus is an MR dataset with small substructures, anatomically consistent across slices, and it's our easy MR baseline. Spleen is a CT dataset with a large high-contrast organ — the easiest CT detection target. LUNA16 is the hard one — lung nodules five to twenty-five pixels across, under one percent foreground, and it's the regime the paper was actually built for. All three are freely downloadable. We explicitly avoided LIDC-IDRI itself because it requires credentialing and doesn't fit on our disk."

---

## Slide 6 — Main Result · ~90s

**Visual**
- Full-bleed **`examples/figures/ablation_comparison.png`** (the 3-row, 2-column grid: hippocampus / spleen / LUNA16 × seg IoU / detection AP or F1)

**Bullets** (annotate while pointing at the figure)
- **Segmentation IoU (left column)**: λ > 0 lifts every dataset massively over the RetinaNet-only baseline.
  - Hippocampus: **3.3× lift**
  - Spleen: **50× lift** (0.012 → 0.633)
  - LUNA16: **12× lift** (0.002 → 0.025)
- **Detection AP@0.3 / F1 (right column)**: same direction everywhere, magnitude scales with target difficulty.
  - Spleen: AP@0.3 **0.93 → 0.98** (near-saturation)
  - LUNA16: AP@0.3 **0.002 → 0.005** (small absolute, 2× lift)
- **The paper's central claim reproduces on every dataset and both metrics.**

**Script** (~170 words, ~68s)
> "This is the headline figure. Three rows — hippocampus on top, spleen in the middle, LUNA16 on the bottom. Left column is segmentation IoU, right column is detection. Each bar is one value of lambda, with lambda equals zero being the pure RetinaNet baseline.
>
> Look at the seg-IoU column first. Every single dataset shows a big lift when lambda is greater than zero. Three point three times on hippocampus. Fifty times on spleen, from barely working to six-tenths IoU. Twelve times on LUNA16.
>
> The detection column tells the same story in a different magnitude. On spleen, Average Precision at IoU point three goes from zero point nine-three to zero point nine-eight — practically at ceiling. On LUNA16, the magnitudes are small because nodules are genuinely hard, but the direction is still right: lambda equals one beats the baseline by a factor of two. Every dataset, both metrics, the paper's central claim reproduces."

---

## Slide 7 — λ Ablation & Extensions · ~45s

**Visual**
- Either `examples/figures/ablation_headline_spleen.png` or the seg-IoU-per-epoch line chart from it (fastest and clearest)

**Bullets**
- **Baseline vs. Retina U-Net in one sweep**: `seg_weight = 0` *is* the RetinaNet-only baseline. No separate training run needed.
- Swept **λ ∈ {0, 0.5, 1.0, 2.0}** on each dataset.
- **λ = 1 is consistently the sweet spot** for seg IoU on all three.
- Added **PASCAL VOC Average Precision (AP@0.3, AP@0.5)** as the primary detection metric — threshold-free, directly comparable to detection-literature numbers.
- Added **`seg_pos_weight`** to BCE for class-imbalanced segmentation (LUNA16 nodules). Without it, the seg head collapses to the all-background solution.

**Script** (~100 words, ~40s)
> "A few things worth calling out as our extensions. The paper's baseline comparison comes free from the same ablation — lambda equals zero is just RetinaNet — so we get it in one training loop. Lambda equals one is the sweet spot every time. We added PASCAL VOC Average Precision as our main detection metric; it's threshold-free, which matters because low-confidence RetinaNet scores can make fixed-threshold F1 misleading. And on LUNA16 we added a positive-class weight to the seg loss, without which the head collapses to all-background on point-one-percent foreground."

---

## Slide 8 — Why Our Numbers Differ from the Paper · ~45s

**Visual**
- A two-column table: "Paper" vs "Ours" with rows: Conv dim (3D vs 2D), Input (96³ patches vs 2D slices), Anchors (3D vs 2D), Backbone context (full 3D locality vs single slice)

**Bullets**
- **Primary gap: 2D vs. 3D.** Paper uses 3D convs, 3D anchors, 96³ patches — a nodule decision aggregates ~5 adjacent slices of evidence.
- **Small cost on hippocampus / spleen**: targets are either large or recurrent — 2D suffices.
- **Large cost on LUNA16**: nodules span only 2–5 slices; Z-axis context is *how* radiologists find them.
- **Why we stayed in 2D**: torchvision has no 3D RetinaNet; porting is a multi-week effort.
- Not a bug in our training — a disclosed scope reduction.

**Script** (~90 words, ~36s)
> "Where our numbers are weaker than the paper's, the main reason is the 2D-versus-3D gap. The paper's 3D model can aggregate evidence from five-plus neighboring slices per decision. Ours sees one slice at a time. For large or recurring targets like spleen, that doesn't matter — we match near-ceiling. For small sparse targets like lung nodules, it matters a lot. The 3D port is the clear next step, but it requires leaving torchvision and building 3D backbone, anchors, and FPN from scratch — roughly two weeks we didn't have."

---

## Slide 9 — Wrap-up · ~25s

**Visual**
- Three-bullet summary slide
- QR code or text link to the GitHub repo + commit hash

**Bullets**
- Reproduced the paper's central claim on **three datasets, two modalities** — 2D slice-wise.
- Packaged as a **PyHealth contribution**: dataset + task + model + training + 54 tests + Colab.
- Natural next step: **3D port**.
- **Code**: github.com/jc182ill/CS598-HC — branch `implementation1`.

**Script** (~60 words, ~24s)
> "To wrap up: we reproduced Retina U-Net's central claim on three public medical datasets. The full contribution — dataset class, task, model, training loop, fifty-four unit tests, and a Colab notebook — is packaged as a PyHealth pull request. The natural extension is a 3D port. Code's on GitHub under branch `implementation1`. Thanks for watching."

---

## Timing summary

| Slide | Topic | Time |
|---|---|---|
| 1 | Title | 0:20 |
| 2 | Problem | 0:45 |
| 3 | Method | 0:60 |
| 4 | Our reproduction | 0:45 |
| 5 | Datasets | 0:45 |
| 6 | Main result | 1:30 |
| 7 | λ ablation | 0:45 |
| 8 | 2D vs 3D | 0:45 |
| 9 | Wrap-up | 0:25 |
| **Total** | | **~6:20** |

Leaves ~40s of dead time within the 7-min cap for pauses / transitions / brief demos.

## Slides-to-figures cheat sheet

All committed under `examples/figures/`:

| Slide | Figure file |
|---|---|
| 2 (optional) | (no figure — pure conceptual) |
| 3 | hand-drawn or simple block diagram (not in repo) |
| 5 | `hippocampus_demo.png` (shows bbox overlay) |
| 6 | **`ablation_comparison.png`** ← the headline |
| 7 | `ablation_headline_spleen.png` (has AP panel + seg-IoU curves) |
| 8 | 2D-vs-3D table from `IMPLEMENTATION_NOTES.md` (easy to paste) |

## Recording checklist

- [ ] GPU available for one more dry-run if you want to re-generate any figure
- [ ] Slide deck exported (Google Slides / Keynote → PDF or kept live)
- [ ] Script rehearsed once end-to-end with a timer
- [ ] Zoom / OBS window showing slides, not slide-plus-notes
- [ ] Video uploaded to a public URL (MediaSpace, YouTube-unlisted, GDrive-link-anyone)
- [ ] Link added to the Gradescope submission

## If you run long

Trim priority (most-trimmable first):
1. Slide 2 (cut the "segmentation models vs. object detectors" prose; the visual is enough) — saves ~20s
2. Slide 5 (bullets only, skip the read-aloud) — saves ~30s
3. Slide 7 (skip the AP/pos_weight bullet; leave only the λ sweet-spot line) — saves ~15s

## If you run short (<4:30 — unlikely)

Add priority:
1. Slide 6: walk through one epoch curve from the spleen figure (20–30s)
2. Slide 7: a one-sentence mention that we ran on real GPU in ~2 hours, not days
