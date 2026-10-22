"""Tests for modern SpeechBubble widget boundary clamping, auto-flipping, and real-time repositioning."""

import pytest
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QPoint, QRect
from frontend.speech_bubble import SpeechBubble


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


def test_speech_bubble_left_boundary_clamping(qapp):
    bubble = SpeechBubble()
    screen = QGuiApplication.primaryScreen()
    geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    # Place companion at far left edge (e.g. anchor_x = 5)
    bubble.show_speech("Testing left boundary", anchor_x=5, anchor_y=500)

    # Bubble must stay within screen bounds
    assert bubble.x() >= geo.x()
    assert bubble.x() + bubble.width() <= geo.x() + geo.width()
    bubble.close()


def test_speech_bubble_right_boundary_clamping(qapp):
    bubble = SpeechBubble()
    screen = QGuiApplication.primaryScreen()
    geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    # Place companion at far right edge
    right_anchor = geo.x() + geo.width() - 5
    bubble.show_speech("Testing right boundary", anchor_x=right_anchor, anchor_y=500)

    # Bubble must stay within screen bounds
    assert bubble.x() >= geo.x()
    assert bubble.x() + bubble.width() <= geo.x() + geo.width()
    bubble.close()


def test_speech_bubble_top_edge_auto_flip(qapp):
    bubble = SpeechBubble()
    screen = QGuiApplication.primaryScreen()
    geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    # Companion near top edge (anchor_y = 10)
    anchor_y = geo.y() + 10
    bubble.show_speech("Testing top auto-flip", anchor_x=400, anchor_y=anchor_y, companion_height=112)

    # Bubble should flip below the companion rather than going off-screen
    assert bubble.y() >= anchor_y + 112
    assert bubble.y() + bubble.height() <= geo.y() + geo.height()
    bubble.close()


def test_speech_bubble_avatar_and_initials_badge(qapp):
    bubble = SpeechBubble()
    avatar_path = os.path.join("skins", "avatar_boy.png")
    bubble.show_speech("Hello!", anchor_x=400, anchor_y=500, avatar_path=avatar_path, border_color="#f43f5e", initials="HB")

    assert bubble.initials_badge.text() == "HB"
    assert bubble.initials_badge.isVisible()

    # Verify custom 1-letter initial
    bubble.show_speech("Second line", anchor_x=400, anchor_y=500, initials="H")
    assert bubble.initials_badge.text() == "H"
    bubble.close()


def test_speech_bubble_realtime_repositioning(qapp):
    bubble = SpeechBubble()
    bubble.show_speech("Following companion movement!", anchor_x=300, anchor_y=600)
    orig_x = bubble.x()

    # Move companion by 150px
    bubble.reposition(anchor_x=450, anchor_y=600)
    assert bubble.x() == orig_x + 150
    assert bubble.isVisible()
    bubble.close()
