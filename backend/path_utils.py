"""Path utility helpers for locating application assets and skins across development and frozen (PyInstaller) environments."""

import os
import sys


def get_base_dir() -> str:
    """
    Returns the absolute root directory of the Display Buddy application.
    - When frozen by PyInstaller (onedir/onefile), returns the directory containing the executable.
    - When running from source, returns the workspace project root directory.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # This file is located at <project_root>/backend/path_utils.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_skins_dir() -> str:
    """Returns the absolute path to the 'skins' directory."""
    return os.path.join(get_base_dir(), "skins")


def get_asset_path(*relative_parts: str) -> str:
    """Returns the absolute path for an asset relative to the base application directory."""
    return os.path.join(get_base_dir(), *relative_parts)
