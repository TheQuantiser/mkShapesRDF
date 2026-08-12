from pathlib import Path
import sys

import pytest


FAMILY_DIR = Path(__file__).resolve().parents[2]
if str(FAMILY_DIR) not in sys.path:
    sys.path.insert(0, str(FAMILY_DIR))


@pytest.fixture(scope="session")
def ROOT():
    root = pytest.importorskip("ROOT")
    root.gInterpreter.Declare(
        f'#include "{FAMILY_DIR / "common/macros/objects.cc"}"'
    )
    return root
