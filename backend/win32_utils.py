"""Windows OS utility helpers for DPI awareness and Taskbar WorkArea bounds."""

import sys
from typing import Tuple


def enable_dpi_awareness() -> None:
    """
    Enables Windows Per-Monitor DPI awareness.
    Note: Qt 6 automatically manages DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2.
    """
    if sys.platform != "win32":
        return

    try:
        import ctypes
        # Check if already set by Qt or OS before attempting
        shcore = ctypes.windll.shcore
        shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def get_desktop_work_area() -> Tuple[int, int, int, int]:
    """
    Returns (left, top, right, bottom) of the Windows primary desktop work area,
    which excludes the Windows Taskbar.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG)
                ]

            SPI_GETWORKAREA = 0x0030
            rect = RECT()
            res = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
            )
            if res:
                return (rect.left, rect.top, rect.right, rect.bottom)
        except Exception:
            pass

    # Safe fallback if not on Windows or API fails
    return (0, 0, 1920, 1040)
