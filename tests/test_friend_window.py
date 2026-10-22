"""Unit tests for FriendCompanionWindow (visitor entry, walking, ready callback, and exit)."""

import pytest
from PyQt6.QtWidgets import QApplication
from frontend.friend_window import FriendCompanionWindow
from backend.state_machine import State, Direction


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


def test_friend_window_initialization(qapp):
    visitor_ready_called = []

    def on_ready(x_val):
        visitor_ready_called.append(x_val)

    fw = FriendCompanionWindow(
        target_x=500.0,
        floor_y=700.0,
        on_visitor_ready=on_ready,
        interaction_mode="hug"
    )

    # Window must be shown, positioned, and timer ticking
    assert fw.isVisible()
    assert fw.tick_timer.isActive()
    assert fw.y == 700.0
    assert fw.state == State.WALKING

    # Test dialogues helper
    hug_line = fw.get_girl_interaction_dialogue("hug")
    assert hug_line is not None
    assert len(hug_line) > 0

    kiss_line = fw.get_girl_interaction_dialogue("kiss")
    assert kiss_line is not None
    assert len(kiss_line) > 0

    fw.close()


def test_friend_window_walk_and_ready_callback(qapp):
    visitor_ready_called = []

    def on_ready(x_val):
        visitor_ready_called.append(x_val)

    fw = FriendCompanionWindow(
        target_x=300.0,
        floor_y=700.0,
        on_visitor_ready=on_ready,
        interaction_mode="kiss"
    )

    # Force x near stand_x to trigger arrival
    fw.x = fw.stand_x - (fw.walk_speed if fw.direction == Direction.RIGHT else -fw.walk_speed)
    fw._on_tick()

    assert fw.is_waiting_for_companion is True
    assert fw.state == State.WAITING_KISS
    assert len(visitor_ready_called) == 1

    # Start kiss action
    fw.start_kiss()
    assert fw.state == State.KISSING

    fw.close()


def test_friend_window_initials_from_dialogues(qapp):
    custom_dialogues = {
        "initials": {
            "visitor": "VA"
        }
    }
    fw = FriendCompanionWindow(
        target_x=400.0,
        floor_y=700.0,
        dialogues=custom_dialogues
    )
    assert fw.visitor_initials == "VA"
    fw.close()


def test_stand_x_small_distance_from_screen_edge(qapp):
    """Ensures visitor walks in only a small distance from the screen border and exits the same way."""
    fw_left = FriendCompanionWindow(target_x=550.0, floor_y=700.0)
    # Comes in from left edge, stands ~130px onto screen, exits to the left
    assert fw_left.stand_x == fw_left.screen_left + 130.0
    assert fw_left.direction == Direction.RIGHT
    assert fw_left.exit_direction == Direction.LEFT
    fw_left.close()

    fw_right = FriendCompanionWindow(target_x=250.0, floor_y=700.0)
    # Comes in from right edge, stands ~190px from right border, exits to the right
    assert fw_right.stand_x == fw_right.screen_left + fw_right.screen_width - 190.0
    assert fw_right.direction == Direction.LEFT
    assert fw_right.exit_direction == Direction.RIGHT
    fw_right.close()


def test_interaction_end_and_smooth_exit_lifecycle(qapp):
    """Verifies that at 4.8s on_interaction_end is triggered, but visitor window remains alive to walk off-screen."""
    interaction_ended = []
    visitor_finished = []

    fw = FriendCompanionWindow(
        target_x=500.0,
        floor_y=700.0,
        on_interaction_end=lambda: interaction_ended.append(True),
        on_visitor_finished=lambda: visitor_finished.append(True),
        interaction_mode="kiss"
    )

    fw.start_kiss()
    assert fw.state == State.KISSING

    # Advance timer to 4.8s
    fw.hug_timer = 4.79
    fw._on_tick()
    assert len(interaction_ended) == 1
    assert fw.is_exiting is True
    assert fw.state == State.WALKING
    assert len(visitor_finished) == 0  # Still walking, not finished yet!

    # Simulate steps walking off-screen
    if fw.direction == Direction.LEFT:
        fw.x = fw.screen_left - 135.0
    else:
        fw.x = fw.screen_left + fw.screen_width + 125.0
    fw._on_tick()

    # Now she has reached beyond the edge and finished
    assert len(visitor_finished) == 1
    assert not fw.tick_timer.isActive()

