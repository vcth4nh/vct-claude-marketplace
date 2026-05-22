"""Importable test helpers. Adjusts sys.path so tests can import auto_retry."""
from __future__ import annotations
import pathlib
import sys

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_DIR / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
