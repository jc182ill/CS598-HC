"""Side-by-side comparison figure: Hippocampus MR vs Spleen CT.

Produces ``examples/figures/ablation_comparison.png`` with two rows:

    Top row:    Hippocampus (small-lesion MR)   — hard regime
    Bottom row: Spleen      (large-organ CT)    — easier regime

and two columns: final-epoch segmentation IoU + final-epoch detection F1
as bar charts per λ, with the λ = 0 baseline drawn as a dashed line on
each subplot.

This is the single figure we want to put on a slide for the video: it
shows the paper's central claim reproduced on two modalities with very
different object scales, dataset sizes, and difficulties.
"""

import json
import pathlib

import matplotlib.pyplot as plt
import numpy as np


FIG_DIR = pathlib.Path(__file__).parent / "figures"
HIPPO_JSON = FIG_DIR / "ablation_results.json"
SPLEEN_JSON = FIG_DIR / "ablation_results_spleen.json"
OUT = FIG_DIR / "ablation_comparison.png"


def load(path: pathlib.Path):
    with open(path) as f:
        d = json.load(f)
    histories = {float(k): v for k, v in d["histories"].items()}
    return histories, d.get("config", {})


def final_values(histories, key):
    return {lam: hist[-1][key] for lam, hist in sorted(histories.items())}


def lambda_colors(lambdas):
    base_color = "#888888"
    cmap = plt.get_cmap("viridis")
    non_zero = [l for l in sorted(lambdas) if l > 0]
    colors = {0.0: base_color}
    for i, lam in enumerate(non_zero):
        colors[lam] = cmap(0.15 + 0.75 * (i / max(len(non_zero) - 1, 1)))
    return colors


def draw_bar(ax, data_dict, title, ylabel, max_scale=1.15):
    lambdas = sorted(data_dict.keys())
    values = [data_dict[l] for l in lambdas]
    colors = lambda_colors(lambdas)
    bar_colors = [colors[l] for l in lambdas]
    bars = ax.bar([str(l) for l in lambdas], values, color=bar_colors,
                  edgecolor="black", linewidth=0.6)
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3, axis="y")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + max(values) * 0.015,
                f"{val:.3f}", ha="center", fontsize=8)
    ax.set_ylim(0, max(max(values) * max_scale, 0.02))
    ax.axhline(values[0], color="#888888", ls="--", lw=0.8, alpha=0.8)


def main():
    hippo_hist, hippo_cfg = load(HIPPO_JSON)
    spleen_hist, spleen_cfg = load(SPLEEN_JSON)

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))

    hippo_seg = final_values(hippo_hist, "val_seg_iou")
    spleen_seg = final_values(spleen_hist, "val_seg_iou")

    # Prefer AP if present (threshold-free), fall back to F1 for legacy JSONs.
    def _final_detection(hist):
        final = hist[list(hist.keys())[0]][-1] if isinstance(hist, dict) else hist[-1]
        return "val_ap_30" if "val_ap_30" in final else "val_f1"

    hippo_key = _final_detection(hippo_hist)
    spleen_key = _final_detection(spleen_hist)
    hippo_det = final_values(hippo_hist, hippo_key)
    spleen_det = final_values(spleen_hist, spleen_key)
    hippo_det_label = "AP @ IoU 0.3" if hippo_key == "val_ap_30" else "F1 @ IoU 0.3"
    spleen_det_label = "AP @ IoU 0.3" if spleen_key == "val_ap_30" else "F1 @ IoU 0.3"

    hippo_lift = hippo_seg[1.0] / hippo_seg[0.0] if hippo_seg[0.0] > 0 else float("inf")
    spleen_lift = spleen_seg[1.0] / spleen_seg[0.0] if spleen_seg[0.0] > 0 else float("inf")

    draw_bar(axes[0, 0], hippo_seg,
             f"Hippocampus MR — seg IoU (λ=1 vs λ=0: {hippo_lift:.1f}× lift)",
             "seg IoU")
    draw_bar(axes[0, 1], hippo_det,
             f"Hippocampus MR — detection ({hippo_det_label})",
             hippo_det_label)
    draw_bar(axes[1, 0], spleen_seg,
             f"Spleen CT — seg IoU (λ=1 vs λ=0: {spleen_lift:.0f}× lift)",
             "seg IoU")
    draw_bar(axes[1, 1], spleen_det,
             f"Spleen CT — detection ({spleen_det_label})",
             spleen_det_label)

    for ax in axes[1]:
        ax.set_xlabel("seg_weight (λ)")

    hippo_n_train = len(hippo_cfg.get("train_ids", []))
    spleen_n_train = len(spleen_cfg.get("train_ids", []))

    fig.suptitle(
        "Retina U-Net λ ablation — seg supervision lifts both modalities over the RetinaNet baseline\n"
        f"Hippocampus MR: {hippo_n_train} train pts, ~490 slices, 36×~50×~50 vols   |   "
        f"Spleen CT: {spleen_n_train} train pts, ~680 lesion slices, 512×512×~70 vols",
        fontsize=10, y=1.00,
    )
    fig.tight_layout()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
