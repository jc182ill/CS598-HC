class BaseDataset:
    """Minimal BaseDataset placeholder.

    Mirrors the subset of the upstream ``pyhealth.datasets.BaseDataset``
    interface that concrete subclasses actually call on ``super()``.
    The full upstream implementation is tabular/EHR-oriented and is not
    carried in this PR branch; when this contribution lands in PyHealth
    proper, the real base class takes over.
    """

    def __init__(
        self,
        root: str = ".",
        tables=None,
        dataset_name=None,
        config_path=None,
        **kwargs,
    ) -> None:
        self.root = root
        self.tables = tables or []
        self.dataset_name = dataset_name or self.__class__.__name__
        self.config_path = config_path
