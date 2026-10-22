"""Skin pack configuration and asset loader for Display Buddy."""

import json
import os
from typing import Dict, Any, List


DEFAULT_CONFIG: Dict[str, Any] = {
    "name": "Default Companion",
    "version": "1.0.0",
    "author": "Display Buddy",
    "render": {
        "scale": 2.0,
        "fps": 10,
        "frame_width": 48,
        "frame_height": 48
    },
    "movement": {
        "walk_speed_px_per_tick": 4,
        "wander_interval_min_seconds": 10,
        "wander_interval_max_seconds": 25,
        "gravity_px_per_tick": 8
    },
    "behavior_weights": {
        "idle": 0.40,
        "wander": 0.40,
        "sleep": 0.20
    }
}

DEFAULT_DIALOGUES: Dict[str, Any] = {
    "idle_quotes": [
        "Just stretching my legs!",
        "Working hard today?",
        "Need some coffee...",
        "I'm keeping your desktop tidy!"
    ],
    "click_quotes": [
        "Hey! That tickles!",
        "Need help with your code?",
        "Right here with you!"
    ],
    "bored_quotes": {
        "dad_joke": [
            "Hi bored, I'm {name}! Nice to meet you! 😄"
        ],
        "creative": [
            "Quick! Stare at the ceiling until you see patterns! 👀",
            "Have you tried spinning around in your chair 3 times? 🔄"
        ]
    },
    "say_something_quotes": {
        "literal": [
            "Something.",
            "Something! 😜"
        ],
        "facts": [
            "Fun fact: Sea otters hold hands when they sleep so they don't drift away! 🦦💤",
            "Did you know octopuses have three hearts and blue blood? 🐙💙"
        ]
    },
    "hanging_quotes": [
        "Look ma, no gravity! 🛸✨",
        "Wait... I forgot how to fall! 🧗‍♂️😅",
        "Gravity is merely a polite suggestion! 😎"
    ],
    "hanging_drop_quotes": [
        "Uh oh... don't look down! 😱",
        "Aaaand gravity's back! 🪂💨"
    ]
}


from backend.asset_generator import ensure_default_assets


class Skin:
    def __init__(self, skin_dir: str):
        self.skin_dir = os.path.abspath(skin_dir)
        ensure_default_assets(self.skin_dir)
        self.config: Dict[str, Any] = self._load_config()
        self.dialogues: Dict[str, List[str]] = self._load_dialogues()

    def _load_config(self) -> Dict[str, Any]:
        cfg_file = os.path.join(self.skin_dir, "config.json")
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                for k, v in user_cfg.items():
                    if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                        merged[k] = {**merged[k], **v}
                    else:
                        merged[k] = v
                return merged
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def _load_dialogues(self) -> Dict[str, List[str]]:
        dia_file = os.path.join(self.skin_dir, "dialogues.json")
        if os.path.exists(dia_file):
            try:
                with open(dia_file, "r", encoding="utf-8") as f:
                    user_dia = json.load(f)
                merged = DEFAULT_DIALOGUES.copy()
                for k, v in user_dia.items():
                    merged[k] = v
                return merged
            except Exception:
                return DEFAULT_DIALOGUES.copy()
        return DEFAULT_DIALOGUES.copy()

    def get_sprite_path(self, state_name: str) -> str:
        sprites_dir = os.path.join(self.skin_dir, "sprites")
        direct = os.path.join(sprites_dir, f"{state_name}.png")
        if os.path.exists(direct):
            return direct
        # Fallback to idle.png
        fallback = os.path.join(sprites_dir, "idle.png")
        return fallback if os.path.exists(fallback) else direct

    def get_sound_path(self, sound_name: str) -> str:
        sounds_dir = os.path.join(self.skin_dir, "sounds")
        path = os.path.join(sounds_dir, sound_name)
        return path if os.path.exists(path) else ""


def list_available_skins(skins_root_dir: str) -> List[str]:
    """Returns a list of skin directory names present in skins_root_dir."""
    if not os.path.exists(skins_root_dir):
        return []
    skins = []
    for item in os.listdir(skins_root_dir):
        full = os.path.join(skins_root_dir, item)
        if os.path.isdir(full) and os.path.exists(os.path.join(full, "config.json")):
            skins.append(item)
    return skins
