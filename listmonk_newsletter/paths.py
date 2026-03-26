"""
Resolves the active data directory based on DATA_SUBDIRECTORY env var.
Used by __init__.py and readwise.py to locate state files and templates.
"""

from pathlib import Path

from decouple import config

ROOT_DIRECTORY = Path(__file__).parent.parent.resolve()
DATA_DIRECTORY = ROOT_DIRECTORY / "data"

_subdirectory = config("DATA_SUBDIRECTORY", default=None)
ACTIVE_DATA_DIRECTORY = DATA_DIRECTORY / _subdirectory if _subdirectory else DATA_DIRECTORY
