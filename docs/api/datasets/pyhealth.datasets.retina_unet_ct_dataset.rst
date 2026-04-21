Retina U-Net CT Dataset
=======================

``RetinaUNetCTDataset`` loads per-patient 3D CT volumes and their
instance-labeled segmentation masks, slices them axially, and yields
2D samples that are directly consumable by
:class:`pyhealth.tasks.retina_unet_detection.RetinaUNetDetectionTask`.

Disk layout expected by the default constructor::

    root/
      patient_<id>/
        volume.npy   # shape (D, H, W)
        mask.npy     # shape (D, H, W)

An in-memory mode is also available for toy experiments and tests,
which bypasses the filesystem entirely.

Example
-------

.. code-block:: python

    import numpy as np
    from pyhealth.datasets.retina_unet_ct_dataset import RetinaUNetCTDataset
    from pyhealth.tasks.retina_unet_detection import RetinaUNetDetectionTask

    volume = np.random.randn(8, 64, 64).astype(np.float32)
    mask = np.zeros((8, 64, 64), dtype=np.int32)
    mask[3, 20:30, 20:30] = 1  # one lesion on one slice

    ds = RetinaUNetCTDataset(
        volumes={"p1": volume},
        masks={"p1": mask},
        skip_empty_slices=True,
        hu_window=(-1000.0, 400.0),
    )

    samples = ds.set_task(RetinaUNetDetectionTask())
    print(samples[0]["boxes"])

API Reference
-------------

.. automodule:: pyhealth.datasets.retina_unet_ct_dataset
   :members:
   :undoc-members:
   :show-inheritance:
