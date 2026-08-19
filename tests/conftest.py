import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _reset_chroma():
    from chromadb.api.client import SharedSystemClient

    SharedSystemClient.clear_system_cache()
    yield
    SharedSystemClient.clear_system_cache()
