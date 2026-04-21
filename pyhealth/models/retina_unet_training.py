"""Training and evaluation helpers for Retina U-Net.

This module bridges the dataset / task pipeline
(``RetinaUNetCTDataset`` + ``RetinaUNetDetectionTask``) and the model
(``RetinaUNet``) in a way that drops into a standard PyTorch
``DataLoader`` + optimizer loop. It provides:

* :class:`RetinaUNetTorchDataset` — wraps a CT dataset + a detection
  task and emits ``(image_tensor, target_dict)`` pairs in the shape
  torchvision's RetinaNet expects (images are ``[C, H, W]`` float
  tensors; targets are dicts with ``boxes``/``labels``/``masks`` keys).
* :func:`collate_fn` — packs a batch into the ``(list[Tensor], list[dict])``
  structure the model consumes.
* :func:`train_one_epoch` — one pass over a training loader, returns
  the mean of every loss component for the epoch.
* :func:`evaluate` — detection F1 @ IoU 0.5 plus binary segmentation
  IoU on a validation loader.

None of this code is novel — it's scaffolding to turn the contribution
into something you can actually run end-to-end and compare against a
RetinaNet-only baseline via the ``seg_weight`` knob.
"""

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from torchvision.ops import box_iou

from pyhealth.datasets.retina_unet_ct_dataset import RetinaUNetCTDataset
from pyhealth.tasks.retina_unet_detection import RetinaUNetDetectionTask


class RetinaUNetTorchDataset(Dataset):
    """PyTorch ``Dataset`` wrapper around ``RetinaUNetCTDataset``.

    Each ``__getitem__`` call runs the underlying slice sample through
    the detection task and returns a tuple::

        (image: Tensor[C, H, W], target: Dict[str, Tensor])

    with ``target`` holding ``"boxes" (N, 4)``, ``"labels" (N,)`` and
    ``"masks" (H, W)``.

    Args:
        ct_dataset: An instantiated :class:`RetinaUNetCTDataset`.
        task: A detection task to apply to each raw sample. Defaults
            to :class:`RetinaUNetDetectionTask`.
        drop_empty: If True, silently skip samples whose mask yields
            zero bounding boxes. torchvision's RetinaNet training path
            handles empty boxes, but dropping them usually stabilizes
            the early epochs on small medical datasets.
    """

    def __init__(
        self,
        ct_dataset: RetinaUNetCTDataset,
        task: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        drop_empty: bool = True,
    ) -> None:
        self.ct_dataset = ct_dataset
        self.task = task if task is not None else RetinaUNetDetectionTask()
        self.drop_empty = drop_empty

        # Pre-filter empty samples so __len__ and __getitem__ align.
        self._indices: List[int] = []
        for i in range(len(self.ct_dataset)):
            if not drop_empty:
                self._indices.append(i)
                continue
            processed = self.task(self.ct_dataset[i])
            if processed["boxes"].shape[0] > 0:
                self._indices.append(i)

    def __len__(self) -> int:
        return len(self._indices)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        raw = self.ct_dataset[self._indices[idx]]
        processed = self.task(raw)

        image = processed["image"]
        # (H, W, C) -> (C, H, W)
        image_tensor = torch.from_numpy(np.ascontiguousarray(image.transpose(2, 0, 1))).float()

        target = {
            "boxes": torch.from_numpy(np.ascontiguousarray(processed["boxes"])).float(),
            "labels": torch.from_numpy(np.ascontiguousarray(processed["labels"])).long(),
            "masks": torch.from_numpy(np.ascontiguousarray(processed["mask"])).long(),
        }
        return image_tensor, target


def collate_fn(
    batch: List[Tuple[torch.Tensor, Dict[str, torch.Tensor]]]
) -> Tuple[List[torch.Tensor], List[Dict[str, torch.Tensor]]]:
    """Collate variable-size detection samples for the RetinaUNet model."""
    images = [item[0] for item in batch]
    targets = [item[1] for item in batch]
    return images, targets


def _to_device(targets: List[Dict[str, torch.Tensor]], device: torch.device):
    return [{k: v.to(device) for k, v in t.items()} for t in targets]


def train_one_epoch(
    model: nn.Module,
    loader: Iterable,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    grad_clip: Optional[float] = None,
) -> Dict[str, float]:
    """Run one training epoch; return mean loss components."""
    model.train()
    totals: Dict[str, float] = {}
    n_batches = 0

    for images, targets in loader:
        images = [img.to(device) for img in images]
        targets = _to_device(targets, device)

        losses = model(images, targets)
        loss = losses["loss_total"]

        optimizer.zero_grad()
        loss.backward()
        if grad_clip is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        for k, v in losses.items():
            totals[k] = totals.get(k, 0.0) + float(v.item())
        n_batches += 1

    if n_batches == 0:
        return {}
    return {k: v / n_batches for k, v in totals.items()}


def _match_predictions(
    pred_boxes: torch.Tensor,
    gt_boxes: torch.Tensor,
    iou_threshold: float = 0.5,
) -> Tuple[int, int, int]:
    """Greedy one-to-one matching of predicted to GT boxes; return (tp, fp, fn).

    For each GT box, take the best-IoU unmatched prediction with IoU
    above threshold. Remaining predictions are false positives; unmatched
    GT boxes are false negatives.
    """
    if pred_boxes.numel() == 0 and gt_boxes.numel() == 0:
        return 0, 0, 0
    if pred_boxes.numel() == 0:
        return 0, 0, gt_boxes.shape[0]
    if gt_boxes.numel() == 0:
        return 0, pred_boxes.shape[0], 0

    ious = box_iou(pred_boxes, gt_boxes)  # [P, G]
    matched_pred = set()
    matched_gt = set()

    # For fair matching, sort GT by size descending (big lesions first)
    # and greedily pick the best unmatched prediction.
    gt_order = torch.argsort(
        (gt_boxes[:, 2] - gt_boxes[:, 0]) * (gt_boxes[:, 3] - gt_boxes[:, 1]),
        descending=True,
    )
    for g in gt_order.tolist():
        best_iou = iou_threshold
        best_p = -1
        for p in range(ious.shape[0]):
            if p in matched_pred:
                continue
            if ious[p, g].item() > best_iou:
                best_iou = ious[p, g].item()
                best_p = p
        if best_p >= 0:
            matched_pred.add(best_p)
            matched_gt.add(int(g))

    tp = len(matched_gt)
    fp = pred_boxes.shape[0] - len(matched_pred)
    fn = gt_boxes.shape[0] - len(matched_gt)
    return tp, fp, fn


def _binary_iou(pred: torch.Tensor, gt: torch.Tensor) -> float:
    """Binary IoU between two 0/1 tensors of the same spatial size."""
    pred_b = pred.bool()
    gt_b = gt.bool()
    inter = (pred_b & gt_b).sum().item()
    union = (pred_b | gt_b).sum().item()
    if union == 0:
        return 1.0  # both empty = perfect match (no foreground)
    return inter / union


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: Iterable,
    device: torch.device,
    iou_threshold: float = 0.3,
    score_threshold: float = 0.01,
) -> Dict[str, float]:
    """Detection F1 @ IoU and binary segmentation IoU on a loader.

    Defaults are deliberately permissive for the tiny-lesion
    small-data regime (hippocampus-sized objects at ~10 px are very
    sensitive to slight box offsets, and under-trained RetinaNet
    heads often sit below a 0.05 score). Returns counts for diagnosis
    (``tp``/``fp``/``fn``, mean predictions per image at both the raw
    and filtered levels).
    """
    model.eval()
    tp = fp = fn = 0
    seg_ious: List[float] = []
    n_samples = 0
    total_preds_raw = 0
    total_preds_kept = 0
    max_score_seen = 0.0

    for images, targets in loader:
        images = [img.to(device) for img in images]
        out = model(images)
        detections = out["detections"]
        seg_logits = out["seg_logits"].cpu()

        for det, target, seg_logit in zip(detections, targets, seg_logits):
            pred_boxes_raw = det["boxes"].cpu()
            pred_scores = det["scores"].cpu()
            if pred_scores.numel() > 0:
                max_score_seen = max(max_score_seen, float(pred_scores.max().item()))
            keep = pred_scores > score_threshold
            pred_boxes = pred_boxes_raw[keep]

            total_preds_raw += pred_boxes_raw.shape[0]
            total_preds_kept += pred_boxes.shape[0]
            n_samples += 1

            gt_boxes = target["boxes"]

            tpi, fpi, fni = _match_predictions(
                pred_boxes, gt_boxes, iou_threshold=iou_threshold
            )
            tp += tpi
            fp += fpi
            fn += fni

            # Binary seg IoU at the logits' resolution (target mask is
            # resized to match so we compare apples to apples).
            seg_pred = (seg_logit.sigmoid() > 0.5).squeeze(0)
            gt_mask_full = (target["masks"] > 0).float().unsqueeze(0).unsqueeze(0)
            gt_mask_resized = torch.nn.functional.interpolate(
                gt_mask_full, size=seg_pred.shape, mode="nearest"
            ).squeeze()
            seg_ious.append(_binary_iou(seg_pred, gt_mask_resized))

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    mean_seg_iou = float(np.mean(seg_ious)) if seg_ious else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "seg_iou": mean_seg_iou,
        "mean_preds_raw": total_preds_raw / max(n_samples, 1),
        "mean_preds_kept": total_preds_kept / max(n_samples, 1),
        "max_score": max_score_seen,
    }
