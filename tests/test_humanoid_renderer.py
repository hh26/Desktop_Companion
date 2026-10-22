"""Tests for procedural humanoid renderer and palette cycling for Boy and Girl characters."""

import pytest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from backend.humanoid_renderer import HumanoidRenderer, BOY_PALETTES, GIRL_PALETTES
from backend.state_machine import State, Direction


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


def test_boy_renderer_init(qapp):
    renderer = HumanoidRenderer(character_type="boy_main", palette_name="default")
    assert renderer.palette_name == "default"
    assert renderer.character_type == "boy_main"
    pixmap = renderer.get_pixmap("idle", Direction.RIGHT)
    assert isinstance(pixmap, QPixmap)
    assert pixmap.width() == 256
    assert pixmap.height() == 256


def test_girl_renderer_init(qapp):
    renderer = HumanoidRenderer(character_type="girl_friend", palette_name="default")
    assert renderer.palette_name == "default"
    assert renderer.character_type == "girl_friend"
    pixmap = renderer.get_pixmap("walking", Direction.LEFT)
    assert isinstance(pixmap, QPixmap)
    assert pixmap.width() == 256
    assert pixmap.height() == 256


def test_palette_cycling(qapp):
    renderer = HumanoidRenderer(character_type="boy_main", palette_name="default")
    next_palette = renderer.cycle_palette()
    assert next_palette == "emerald"
    assert renderer.palette_name == "emerald"


def test_all_states_render_both_characters(qapp):
    states = ["idle", "walking", "sitting", "sleeping", "dragged", "falling", "hanging", "hugging", "waiting_hug", "kissing", "waiting_kiss"]
    for c_type in ["boy_main", "girl_friend"]:
        renderer = HumanoidRenderer(character_type=c_type)
        for s in states:
            for d in [Direction.LEFT, Direction.RIGHT]:
                pix = renderer.get_pixmap(s, d)
                assert pix is not None
                assert not pix.isNull()


def test_unified_render_mode(qapp):
    boy_renderer = HumanoidRenderer(character_type="boy_main")
    assert boy_renderer.render_mode == "unified"
    pix = boy_renderer.create_sprite("walking", Direction.RIGHT, walk_phase=1.0)
    assert not pix.isNull()
    assert pix.width() == 256
    assert pix.height() == 256

    girl_renderer = HumanoidRenderer(character_type="girl_friend")
    assert girl_renderer.render_mode == "unified"
    pix_g = girl_renderer.create_sprite("hugging", Direction.LEFT)
    assert not pix_g.isNull()
    assert pix_g.width() == 256
    assert pix_g.height() == 256


def test_hugging_embrace_rendering(qapp):
    boy_renderer = HumanoidRenderer(character_type="boy_main")
    pix_boy_hug = boy_renderer.create_sprite("hugging", Direction.RIGHT, walk_phase=1.5)
    assert not pix_boy_hug.isNull()

    girl_renderer = HumanoidRenderer(character_type="girl_friend")
    pix_girl_hug = girl_renderer.create_sprite("hugging", Direction.LEFT, walk_phase=1.5)
    assert not pix_girl_hug.isNull()


def test_kissing_animation_rendering(qapp):
    boy_renderer = HumanoidRenderer(character_type="boy_main")
    # Test cheek kiss lunge and heart particle peak
    pix_boy_kiss_peak = boy_renderer.create_sprite("kissing", Direction.RIGHT, walk_phase=1.2)
    assert not pix_boy_kiss_peak.isNull()
    pix_boy_kiss_recoil = boy_renderer.create_sprite("kissing", Direction.RIGHT, walk_phase=2.0)
    assert not pix_boy_kiss_recoil.isNull()

    girl_renderer = HumanoidRenderer(character_type="girl_friend")
    pix_girl_kiss = girl_renderer.create_sprite("kissing", Direction.LEFT, walk_phase=1.2)
    assert not pix_girl_kiss.isNull()
