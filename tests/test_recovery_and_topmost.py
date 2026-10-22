"""Unit tests for companion recovery, topmost assertion, and tray activation."""

import pytest
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from frontend.tray_icon import TrayIcon
from frontend.companion_window import CompanionWindow
from backend.state_machine import State, Direction


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest", "-platform", "offscreen"])
    return app


def test_tray_icon_reset_and_activation(qapp):
    reset_called = []

    def on_reset():
        reset_called.append(True)

    dummy_pixmap = QPixmap(16, 16)
    dummy_pixmap.fill()
    tray = TrayIcon(
        icon=QIcon(dummy_pixmap),
        on_toggle_pause=lambda: False,
        on_toggle_mute=lambda: False,
        on_trigger_speech=lambda: None,
        on_exit=lambda: None,
        on_reset_position=on_reset
    )

    # Trigger via menu action
    tray.reset_action.trigger()
    assert len(reset_called) == 1

    # Trigger via tray icon activation (single-click)
    tray._handle_activation(QSystemTrayIcon.ActivationReason.Trigger)
    assert len(reset_called) == 2

    # Trigger via tray icon double-click
    tray._handle_activation(QSystemTrayIcon.ActivationReason.DoubleClick)
    assert len(reset_called) == 3


def test_companion_window_reset_position(qapp):
    import os
    skin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skins", "default_companion")
    win = CompanionWindow(skin_path)

    # Intentionally displace companion off bounds and set stuck state
    win.engine.x = -9999.0
    win.engine.y = -9999.0
    win.is_running_to_kiss = True
    win.run_timeout = 10.0

    # Call emergency reset
    win.reset_position()

    # Must be recovered onto visible desktop floor, idle, and reset
    assert win.engine.x >= win.engine.min_x
    assert win.engine.x <= win.engine.max_x
    assert win.engine.y == float(win.engine.max_y)
    assert win.engine.state == State.IDLE
    assert win.is_running_to_kiss is False
    assert win.run_timeout == 0.0

    win.quit_application()
