from typing import Any, Dict, List, Tuple
import numpy as np

from pyhealth.tasks.base_task import BaseTask



class RetinaUNetDetectionTask(BaseTask):
    """
    Task for converting segmentation masks into detection targets for Retina U-Net.

    This task takes medical images and corresponding segmentation masks as input
    and produces:
        - Bounding boxes (derived from masks)
        - Class labels
        - Segmentation maps (for auxiliary supervision)

    This enables joint object detection and segmentation training as described
    in Retina U-Net.

    Example:
        >>> task = RetinaUNetDetectionTask()
        >>> output = task.process_sample(sample)
        >>> print(output.keys())
        dict_keys(['image', 'boxes', 'labels', 'mask'])
    """

    def __init__(self, min_area: int = 10) -> None:
        """
        Initializes the task.

        Args:
            min_area: Minimum pixel area for valid objects.
        """
        super().__init__()
        self.min_area = min_area

    def process_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single dataset sample.

        Args:
            sample: Dictionary containing:
                - "image": np.ndarray (H, W, C)
                - "mask": np.ndarray (H, W)

        Returns:
            Dictionary containing:
                - "image": np.ndarray
                - "boxes": np.ndarray of shape (N, 4)
                - "labels": np.ndarray of shape (N,)
                - "mask": np.ndarray (H, W)
        """
        image = sample["image"]
        mask = sample["mask"]

        boxes, labels = self._extract_instances(mask)

        return {
            "image": image,
            "boxes": boxes,
            "labels": labels,
            "mask": mask,
        }

    def _extract_instances(
        self, mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts object instances from segmentation mask.

        Args:
            mask: Segmentation mask where each object has a unique integer ID.

        Returns:
            boxes: Array of bounding boxes (N, 4) in (x_min, y_min, x_max, y_max)
            labels: Array of class labels (N,)
        """
        instance_ids = np.unique(mask)
        instance_ids = instance_ids[instance_ids != 0]  # remove background

        boxes: List[List[int]] = []
        labels: List[int] = []

        for instance_id in instance_ids:
            binary_mask = mask == instance_id

            if binary_mask.sum() < self.min_area:
                continue

            box = self._mask_to_bbox(binary_mask)

            boxes.append(box)
            labels.append(1)  # single-class (can extend later)

        if len(boxes) == 0:
            return (
                np.zeros((0, 4), dtype=np.float32),
                np.zeros((0,), dtype=np.int64),
            )

        return np.array(boxes, dtype=np.float32), np.array(labels, dtype=np.int64)

    def _mask_to_bbox(self, binary_mask: np.ndarray) -> List[int]:
        """
        Converts a binary mask to a bounding box.

        Args:
            binary_mask: Boolean mask of shape (H, W)

        Returns:
            Bounding box [x_min, y_min, x_max, y_max]
        """
        rows = np.any(binary_mask, axis=1)
        cols = np.any(binary_mask, axis=0)

        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]

        return [x_min, y_min, x_max, y_max]

    def collate_fn(
        self, batch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Custom collate function for batching.

        Args:
            batch: List of processed samples.

        Returns:
            Batched dictionary.
        """
        images = [item["image"] for item in batch]
        boxes = [item["boxes"] for item in batch]
        labels = [item["labels"] for item in batch]
        masks = [item["mask"] for item in batch]

        return {
            "images": images,
            "boxes": boxes,
            "labels": labels,
            "masks": masks,
        }


