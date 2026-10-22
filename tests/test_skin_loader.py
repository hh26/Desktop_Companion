"""Unit tests for Skin and asset configuration loading."""

import os
import shutil
import tempfile
import pytest
from backend.skin_loader import Skin, list_available_skins


@pytest.fixture
def temp_skin_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_skin_load_with_defaults(temp_skin_dir):
    # Empty dir should load standard defaults and generate assets
    skin = Skin(temp_skin_dir)
    assert skin.config["name"] is not None
    assert skin.config["render"]["scale"] > 0
    assert len(skin.dialogues["idle_quotes"]) > 0

    # Ensure procedural sprites and sounds were generated
    idle_sprite = skin.get_sprite_path("idle")
    assert os.path.exists(idle_sprite)
    click_sound = skin.get_sound_path("click.wav")
    assert os.path.exists(click_sound)


def test_list_available_skins(temp_skin_dir):
    sub_skin = os.path.join(temp_skin_dir, "custom_pet")
    os.makedirs(sub_skin, exist_ok=True)
    with open(os.path.join(sub_skin, "config.json"), "w") as f:
        f.write('{"name": "Custom Pet"}')

    skins = list_available_skins(temp_skin_dir)
    assert "custom_pet" in skins


def test_skin_load_dialogues_initials_and_menu_labels(temp_skin_dir):
    import json
    dia_file = os.path.join(temp_skin_dir, "dialogues.json")
    with open(dia_file, "w", encoding="utf-8") as f:
        json.dump({
            "initials": {"companion": "AA", "visitor": "BB"},
            "menu_labels": {"kiss": "Custom Kiss", "hug": "Custom Hug"}
        }, f)

    skin = Skin(temp_skin_dir)
    assert skin.dialogues["initials"]["companion"] == "AA"
    assert skin.dialogues["initials"]["visitor"] == "BB"
    assert skin.dialogues["menu_labels"]["kiss"] == "Custom Kiss"

