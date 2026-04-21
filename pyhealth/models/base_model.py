import torch.nn as nn


class BaseModel(nn.Module):
    """Minimal BaseModel placeholder.

    Mirrors the subset of the upstream ``pyhealth.models.BaseModel``
    interface that concrete model subclasses actually rely on. The
    upstream class ties into PyHealth's trainer and metric plumbing,
    which this PR branch does not carry. When the contribution lands
    in PyHealth proper, the real base class takes over.
    """

    def __init__(self) -> None:
        super().__init__()
