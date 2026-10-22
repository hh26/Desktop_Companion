"""Sound manager for playing companion audio effects."""

import os
import sys


class SoundManager:
    def __init__(self, is_muted: bool = False):
        self.is_muted = is_muted

    def toggle_mute(self) -> bool:
        self.is_muted = not self.is_muted
        return self.is_muted

    def play(self, sound_path: str) -> None:
        if self.is_muted or not sound_path or not os.path.exists(sound_path):
            return

        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass
        else:
            # Fallback for non-windows
            pass
