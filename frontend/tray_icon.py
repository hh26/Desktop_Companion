"""System tray integration for Display Buddy."""

from typing import Callable, Optional
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


class TrayIcon(QSystemTrayIcon):
    def __init__(
        self,
        icon: QIcon,
        on_toggle_pause: Callable[[], bool],
        on_toggle_mute: Callable[[], bool],
        on_trigger_speech: Callable[[], None],
        on_exit: Callable[[], None],
        on_reset_position: Optional[Callable[[], None]] = None,
        parent=None
    ):
        super().__init__(icon, parent)
        self.setToolTip("Display Buddy — Desktop Companion (Click to summon)")

        self.on_toggle_pause = on_toggle_pause
        self.on_toggle_mute = on_toggle_mute
        self.on_trigger_speech = on_trigger_speech
        self.on_exit = on_exit
        self.on_reset_position = on_reset_position

        self.menu = QMenu()
        self._init_menu()
        self.setContextMenu(self.menu)

        # Left-click or double-click system tray icon to summon companion immediately
        self.activated.connect(self._handle_activation)

    def _init_menu(self) -> None:
        title_action = QAction("Display Buddy v1.0", self.menu)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)
        self.menu.addSeparator()

        self.pause_action = QAction("Pause Movement", self.menu)
        self.pause_action.triggered.connect(self._handle_toggle_pause)
        self.menu.addAction(self.pause_action)

        self.mute_action = QAction("Mute Sounds", self.menu)
        self.mute_action.triggered.connect(self._handle_toggle_mute)
        self.menu.addAction(self.mute_action)

        self.speech_action = QAction("Say Something!", self.menu)
        self.speech_action.triggered.connect(self.on_trigger_speech)
        self.menu.addAction(self.speech_action)

        self.reset_action = QAction("📍 Bring to Front / Reset Position", self.menu)
        self.reset_action.triggered.connect(self._handle_reset_position)
        self.menu.addAction(self.reset_action)

        self.menu.addSeparator()

        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.on_exit)
        self.menu.addAction(exit_action)

    def _handle_reset_position(self) -> None:
        if self.on_reset_position:
            self.on_reset_position()

    def _handle_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        # Trigger on left-click or double-click on tray icon
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._handle_reset_position()

    def _handle_toggle_pause(self) -> None:
        is_paused = self.on_toggle_pause()
        self.pause_action.setText("Resume Movement" if is_paused else "Pause Movement")

    def _handle_toggle_mute(self) -> None:
        is_muted = self.on_toggle_mute()
        self.mute_action.setText("Unmute Sounds" if is_muted else "Mute Sounds")
