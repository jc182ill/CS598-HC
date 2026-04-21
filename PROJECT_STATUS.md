# Project Status: Contrast with Rubric and Proposal

Deadline: **2026-04-22** (today is 2026-04-21 — ~24 hours remaining).

There are three separate layers of "completeness" to look at: the rubric, the proposal, and the paper reproduction itself.

## 1. What was delivered

A single **Standalone Task** — `RetinaUNetDetectionTask` in `pyhealth/tasks/retina_unet_detection.py`. It converts segmentation masks into bounding boxes (connected-components style), plus one example, one ablation script (`min_area` sweep on synthetic data), an RST doc page, and 7 pytest-style tests. That maps to the rubric's **Option 3 (Standalone Task, 50 pts)**.

## 2. Gap vs. the Project Proposal (the biggest gap)

The proposal (`CS598 Project Proposal.txt`, Tab 3) explicitly promised a **full pipeline** — this maps to **Option 4 (60 pts = 50 + 10 EC)**:

| Proposal commitment | Delivered? |
|---|---|
| PyHealth dataset class loading CT volumes → 2D slices with boxes + masks | **No** — no dataset class at all |
| RetinaNet backbone + U-Net decoder model in PyHealth/PyTorch | **No** — no model code |
| Multi-task training loop (focal + segmentation loss) | **No** — no training code |
| Ablation on segmentation loss weight λ | **No** — only an unrelated `min_area` sweep |
| Baseline comparison: Retina U-Net vs. RetinaNet-only | **No** — no baseline, no numbers |

What was actually built is the *data-pre-processing helper* (masks → boxes), which in the paper is a trivial one-off, not the contribution. The paper's core claim — segmentation supervision improves detection — is untested here.

## 3. Gap vs. the Rubric (for what *was* built as Option 3)

The Standalone-Task rubric weights (50 pts) roughly map like this against what's in the repo:

- **Core Implementation — 20 pts.** At risk: docstrings are effectively absent (Google-style, 2 pts), and `BaseTask` is a stub (the "properly inherits" 2 pts is fragile until the real upstream base class is used). Type hints and PEP8 are fine.
- **Required File Updates — 12 pts.** `pyhealth/tasks/__init__.py` is empty (no export), and there's no update to `docs/api/tasks.rst` index — likely **−2 to −3 pts** ("Missing file updates" deduction).
- **Test Cases — 11 pts.** In good shape: fast, synthetic, covers empty-mask, multi-object, min-area filtering, collate.
- **Ablation — 5 pts.** At risk: rubric says "Show how feature variations affect **model performance** using an existing PyHealth model" — current ablation only counts bounding boxes, no model, no metric. Likely partial credit.
- **PR Formatting — 7 pts.** `Pull_Request` has names/NetIDs, paper link, file guide. **But**: it lists `examples/retina_unet_task_ablation.py` which does not exist — the actual file is `examples/synthetic_detection_retinaunet.py`. Rubric also prescribes filename `examples/{dataset}_{task_name}_{model}.py`, not followed. Expect minor deductions and reviewer confusion.
- **The PR itself.** The rubric requires an actual PR to `sunlabuiuc/PyHealth` (link submitted in Gradescope). `Pull_Request` in this repo is a draft text file — unclear whether it's been opened upstream. If not opened, the contribution grade is at serious risk.

Also unaccounted for in the repo: **Video Presentation (10 pts)**, **Final-Project Google Form (15 pts)**, and **Gradescope submission**. These may exist outside the repo, but worth confirming.

## 4. Summary

- **Against the proposal**: project is **substantially under-scope** — dataset, model, training, and the headline ablation/baseline were all promised and none of them are in the repo.
- **Against the rubric for Option 3**: the skeleton is in place and passes the mechanical checks, but three concrete issues will cost points — missing docstrings, missing index/`__init__` updates, and the ablation not running against a model. Filename/Pull_Request mismatches invite further deductions.
- **Paper reproduction**: essentially not attempted. No Retina U-Net model was built or compared.

## 5. Highest-leverage moves before deadline

Given ~24 hours to the deadline:

1. Fix the `Pull_Request` file-guide mismatch and rename the ablation file to the `examples/{dataset}_{task_name}_{model}.py` convention.
2. Add Google-style docstrings to `RetinaUNetDetectionTask` and its methods, export it in `pyhealth/tasks/__init__.py`, and add an entry in the `docs/api/tasks.rst` index.
3. Decide whether to open the PR upstream to `sunlabuiuc/PyHealth` now — without the upstream PR link, the contribution grade is at serious risk.
4. Record the video presentation (10 pts, completion-graded) and submit the Final-Project Google Form (15 pts, completion-graded) — these are the cheapest points remaining.
5. Building the actual Retina U-Net model in one day is unrealistic; the pragmatic play is to make the Option-3 submission as clean as possible and be honest in the video about scope reduction relative to the proposal.
