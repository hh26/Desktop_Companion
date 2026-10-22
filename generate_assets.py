"""Pre-generate default companion assets."""

import os
from backend.asset_generator import ensure_default_assets

if __name__ == "__main__":
    skin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skins", "default_companion")
    ensure_default_assets(skin_dir)
    print("Assets successfully generated in:", skin_dir)
