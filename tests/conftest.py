from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / "packages" / "core"
API_PATH = ROOT / "apps" / "api"

if str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))
