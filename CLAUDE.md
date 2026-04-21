# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This repo is a narrowly-scoped **PR-style contribution to PyHealth** (upstream: `pyhealth`). It is not a full PyHealth checkout — only the files touched by the contribution plus the minimal scaffolding required to import and test them. The contribution adds a task called `RetinaUNetDetectionTask` inspired by the paper *Retina U-Net: Embarrassingly Simple Exploitation of Segmentation Supervision for Medical Object Detection* (https://arxiv.org/abs/1811.08661).

The course context is CS598 DL4H (Deep Learning for Healthcare). See `Pull_Request` for the PR cover letter, and `CS598 Project Proposal.txt` for the paper reproduction proposal.

## Commands

Tests are plain pytest-style functions (no `unittest.TestCase`); run them with pytest from the repo root:

```
pytest tests/tasks/test_retina_unet_detection.py      # run the task tests
pytest tests/tasks/test_retina_unet_detection.py::test_single_object_bbox_correct   # single test
```

Examples are runnable scripts, not notebooks — execute with `python`:

```
python examples/retina_unet_task_example.py       # minimal smoke example
python examples/synthetic_detection_retinaunet.py # min_area ablation study
```

Sphinx docs live under `docs/` (`make html` from `docs/`); only `docs/api/tasks/pyhealth.tasks.retina_unet_detection.rst` is new work, the rest is copied upstream scaffolding.

## Architecture

### What the task does

`pyhealth/tasks/retina_unet_detection.py` turns instance segmentation masks into detection targets. The input sample is a dict `{"image": HxWxC ndarray, "mask": HxW integer ndarray}`. Each distinct non-zero integer in `mask` is treated as a separate object instance; the task computes its tight axis-aligned bounding box and emits a sample with `boxes` (float32 `[N, 4]` in xyxy order `[x_min, y_min, x_max, y_max]`), `labels` (int64 `[N]`), plus the original `image` and `mask` passed through for segmentation supervision. Instances whose pixel count is below `min_area` are dropped — this is the only configuration knob and is the variable swept in the ablation example.

Current implementation is **single-class**: every surviving instance is labeled `1`. Multi-class support would require threading class info through `_extract_instances`.

### Integration contract with PyHealth

- `pyhealth/tasks/base_task.py` in this repo is a **deliberate minimal stub** (`class BaseTask: pass`-level) so the task can be imported standalone. The real `BaseTask` exists upstream in PyHealth. Do not expand this stub — when the PR lands upstream, the real base class takes over. The task's `__call__` simply delegates to `process_sample` to satisfy the upstream ABC.
- `collate_fn` returns lists (not stacked tensors) because per-sample object counts vary. Downstream training loops are expected to handle the ragged batch.
- Other files under `pyhealth/` (`trainer.py`, `tokenizer.py`, `utils.py`) and most of `examples/` / `docs/` are upstream PyHealth files carried along for context and import resolution — **they are not part of this contribution** and should not be edited as part of this work. `pyhealth/tasks/__init__.py` is empty (1 line) on purpose.

### Where to make changes

The four files owned by this PR (and the only ones that should normally be edited) are:

- `pyhealth/tasks/retina_unet_detection.py` — task implementation
- `tests/tasks/test_retina_unet_detection.py` — unit tests (synthetic masks only; no real data dependencies)
- `examples/retina_unet_task_example.py` and `examples/synthetic_detection_retinaunet.py` — runnable demos
- `docs/api/tasks/pyhealth.tasks.retina_unet_detection.rst` — Sphinx autodoc page

Tests are intentionally numpy-only and do not require torch or a GPU, which keeps CI cheap and the task verifiable in isolation from the rest of PyHealth.
