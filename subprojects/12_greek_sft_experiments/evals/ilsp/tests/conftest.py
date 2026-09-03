"""Keep Hugging Face test downloads in a writable temporary cache."""

import os
from pathlib import Path
from tempfile import gettempdir


_CACHE_ROOT = Path(gettempdir()) / "wp1d-ilsp-test-cache"
os.environ["HF_HOME"] = str(_CACHE_ROOT)
os.environ["HF_HUB_CACHE"] = str(_CACHE_ROOT / "hub")
os.environ["HF_DATASETS_CACHE"] = str(_CACHE_ROOT / "datasets")
