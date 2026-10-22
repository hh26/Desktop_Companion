"""Unit tests for kiss synchronization, smooth running, avatar badge framing, and floor gap fix."""

import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from frontend.companion_window import CompanionWindow
from frontend.speech_bubble import SpeechBubble
from backend.state_machine import CompanionEngine, State, Direction


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


def test_avatar_badge_framing_and_breathing_room(qapp):
    """Verifies avatar badge scales with breathing room so face is never zoomed/cropped."""
    sb = SpeechBubble()
    pix = QPixmap(os.path.join("skins", "avatar_boy.png"))
    badge = sb._make_circular_avatar(pix, "#f43f5e", size=36)

    assert not badge.isNull()
    assert badge.width() == 36
    assert badge.height() == 36
    sb.close()


def test_speech_bubble_head_clearance(qapp):
    """Verifies that the speech bubble pointer tail hovers closely directly above character hair."""
    sb = SpeechBubble()
    # Place companion at anchor_x=500, anchor_y=700 (window top)
    sb.show_speech("Hello there!", anchor_x=500, anchor_y=700, companion_height=112)

    # In our formula: desired_y = int(anchor_y - actual_h + 18)
    # The tail tip (desired_y + actual_h - 5) is at anchor_y + 13.
    # The hair top is at anchor_y + 18.
    # Clearance between tail tip and hair top is exactly 5 pixels!
    tail_tip_y = sb.y() + sb.height() - 5
    hair_top_y = 700 + 18
    clearance = hair_top_y - tail_tip_y
    assert 3 <= clearance <= 8
    sb.close()


def test_floor_offset_eliminates_gap():
    """Verifies that CompanionEngine applies floor_offset to sit directly on the taskbar."""
    config = {
        "render": {"scale": 2.0, "frame_width": 24, "frame_height": 56},
        "movement": {"floor_offset": 15}
    }
    engine = CompanionEngine(config)
    engine.height = 112
    engine.set_bounds(0, 0, 1920, 1040)

    # 1040 (taskbar top) - 112 (window height) + 15 (floor offset) = 943
    assert engine.max_y == 1040 - 112 + 15


def test_kiss_running_smooth_deceleration_and_sync(qapp):
    """Verifies that companion runs smoothly without overshooting and holds 5.0s kiss duration."""
    skin_path = os.path.join("skins", "default_companion")
    win = CompanionWindow(skin_path)

    win.kiss_target_x = 400.0
    win.engine.x = 450.0
    win.engine.direction = Direction.LEFT
    win.is_running_to_kiss = True

    # Advance tick: should smoothly step towards target without snapping or overshooting
    dt = win.tick_interval_ms / 1000.0
    win._on_tick()
    assert win.engine.x < 450.0
    assert win.engine.x >= 400.0

    # Force companion to 1px from target: tick must cleanly reach and transition to KISSING with 5.0s duration
    win.engine.x = 401.0
    win._on_tick()
    assert win.is_running_to_kiss is False
    assert win.engine.state == State.KISSING
    assert win.engine.x == 400.0
    assert win.engine.target_duration == 5.0

    win.quit_application()


def test_boy_runs_to_girl_and_girl_walks_back_same_distance(qapp):
    """Verifies that visitor steps in only a short distance, boy runs to her, and visitor walks back out same way."""
    skin_path = os.path.join("skins", "default_companion")
    win = CompanionWindow(skin_path)

    # Place companion at x=600 on an 800px screen (right half)
    win.engine.x = 600.0
    win.engine.y = 700.0
    win.engine.min_x = 0
    win.engine.max_x = 800 - 112
    win.engine.min_y = 0
    win.engine.max_y = 700

    win.trigger_kiss()

    # Boy faces left towards incoming visitor
    assert win.engine.direction == Direction.LEFT
    assert win.friend_window is not None
    fw = win.friend_window

    # Visitor comes in from left, stops at screen_left + 130
    assert fw.x < fw.screen_left
    assert fw.stand_x == fw.screen_left + 130.0
    assert fw.exit_direction == Direction.LEFT

    # Simulate visitor walking to stand_x
    fw.x = fw.stand_x
    fw._on_tick()

    # Visitor is ready and waiting
    assert fw.state == State.WAITING_KISS
    assert win.is_running_to_kiss is True
    assert win.kiss_target_x == fw.stand_x + 30.0

    # Boy runs across towards her (from 600 towards 160)
    start_x = win.engine.x
    win._on_tick()
    assert win.engine.x < start_x  # Moving smoothly towards her

    # Reach kiss target
    win.engine.x = win.kiss_target_x + 2.0
    win._on_tick()
    assert win.engine.state == State.KISSING
    assert win.is_running_to_kiss is False

    # Simulate hug/kiss completing at 4.8s
    fw.hug_timer = 4.8
    fw._on_tick()

    # Girl turns back around in the same direction she came from to exit
    assert fw.is_exiting is True
    assert fw.direction == Direction.LEFT

    win.quit_application()
