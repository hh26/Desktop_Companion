"""Friend companion window: Girl character from reference photo who enters to hug the primary companion and leaves."""

import os
from typing import Callable, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QGuiApplication
from PyQt6.QtWidgets import QWidget

from backend.state_machine import State, Direction
from backend.humanoid_renderer import HumanoidRenderer
from backend.path_utils import get_asset_path
from frontend.speech_bubble import SpeechBubble


class FriendCompanionWindow(QWidget):
    def __init__(
        self,
        target_x: float,
        floor_y: float,
        on_visitor_ready: Optional[Callable[[float], None]] = None,
        on_interaction_end: Optional[Callable[[], None]] = None,
        on_visitor_finished: Optional[Callable[[], None]] = None,
        on_hug_end: Optional[Callable[[], None]] = None,
        on_hug_start: Optional[Callable[[], None]] = None,
        visitor_initials: str = "G",
        interaction_mode: str = "hug",
        dialogues: Optional[dict] = None,
        parent=None
    ):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Girl companion model (curls, black glasses, anime eyes, black tee)
        self.renderer = HumanoidRenderer(character_type="girl_friend", palette_name="default")
        self.setFixedSize(self.renderer.target_width, self.renderer.target_height)

        self.target_x = float(target_x)
        self.floor_y = float(floor_y)
        self.on_visitor_ready = on_visitor_ready
        self.on_interaction_end = on_interaction_end or on_hug_end
        self.on_visitor_finished = on_visitor_finished
        self.on_hug_end = on_hug_end
        self.on_hug_start = on_hug_start
        self.interaction_mode = interaction_mode
        self.dialogues = dialogues or {}
        self.interactions = self.dialogues.get("interaction_dialogues", {})

        d_init = self.dialogues.get("initials", {})
        if isinstance(d_init, dict) and d_init.get("visitor"):
            self.visitor_initials = str(d_init.get("visitor")).strip()[:2].upper()
        elif self.dialogues.get("visitor_initials"):
            self.visitor_initials = str(self.dialogues.get("visitor_initials")).strip()[:2].upper()
        else:
            self.visitor_initials = str(visitor_initials)[:2].upper()

        # Speech bubble for the visiting friend
        self.speech_bubble = SpeechBubble()
        self.avatar_path = get_asset_path("skins", "avatar_girl.png")

        # Determine screen and available geometry (multi-monitor aware)
        from PyQt6.QtCore import QPoint
        screen = QGuiApplication.screenAt(QPoint(int(self.target_x), int(self.floor_y)))
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry() if screen else None
        self.screen_left = screen_geo.x() if screen_geo else 0
        self.screen_width = screen_geo.width() if screen_geo else 1920

        # Visitor walks in only for a small distance from the screen edge, waits for the boy, and walks back out
        if self.target_x > (self.screen_left + self.screen_width / 2):
            self.x = float(self.screen_left - 85.0)
            self.direction = Direction.RIGHT
            # Walk in a small distance (~130px onto screen from left border)
            self.stand_x = float(self.screen_left + 130.0)
            self.exit_direction = Direction.LEFT
            self.exit_target_x = float(self.screen_left - 150.0)
        else:
            self.x = float(self.screen_left + self.screen_width + 65.0)
            self.direction = Direction.LEFT
            # Walk in a small distance (~190px from right border onto screen)
            self.stand_x = float(self.screen_left + self.screen_width - 190.0)
            self.exit_direction = Direction.RIGHT
            self.exit_target_x = float(self.screen_left + self.screen_width + 150.0)

        self.y = self.floor_y
        self.state = State.WALKING
        self.walk_speed = 4.2
        self.walk_phase = 0.0

        self.is_waiting_for_companion = False
        self.hug_timer = 0.0
        self.is_exiting = False

        self.move(int(self.x), int(self.y))
        self.show()

        # Update loop (30 FPS -> 33ms)
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._on_tick)
        self.tick_timer.start(33)

    def get_girl_interaction_dialogue(self, mode: str) -> Optional[str]:
        """Gets dialogue line for girl during hug or kiss."""
        line = self.interactions.get(mode, {}).get("girl")
        if not line:
            line = "Hehe, tickles! You're so sweet! 🥰❤️" if mode == "kiss" else "Chellam! 💖"
        return line

    def trigger_speech(self, text: str, duration_ms: int = 3500, initials: Optional[str] = None) -> None:
        anchor_x = int(self.x + self.width() / 2)
        anchor_y = int(self.y)
        self.speech_bubble.show_speech(
            text, anchor_x, anchor_y,
            duration_ms=duration_ms,
            avatar_path=self.avatar_path,
            border_color="#ec4899",
            companion_height=self.height(),
            initials=initials or self.visitor_initials
        )

    def start_embrace(self) -> None:
        """Called by primary companion when he finishes running over and initiates the mutual hug."""
        self.state = State.HUGGING
        self.hug_timer = 0.0
        txt = self.get_girl_interaction_dialogue("hug")
        if txt:
            # Stagger by 2300ms so boy's 2200ms speech finishes completely first (zero overlap)
            QTimer.singleShot(2300, lambda: self.trigger_speech(txt, duration_ms=2200))
        if self.on_hug_start:
            self.on_hug_start()

    def start_kiss(self) -> None:
        """Called by primary companion when he finishes running over and showers her with cheek kisses."""
        self.state = State.KISSING
        self.hug_timer = 0.0
        txt = self.get_girl_interaction_dialogue("kiss")
        if txt:
            # Stagger by 2300ms so boy's 2200ms speech finishes completely first (zero overlap)
            QTimer.singleShot(2300, lambda: self.trigger_speech(txt, duration_ms=2200))
        if self.on_hug_start:
            self.on_hug_start()

    def _notify_visitor_finished(self) -> None:
        if not getattr(self, "_finished_notified", False):
            self._finished_notified = True
            if self.on_visitor_finished:
                self.on_visitor_finished()

    def _on_tick(self) -> None:
        dt = 0.033
        self.walk_phase += dt * 10.0

        if self.state == State.WALKING and not self.is_waiting_for_companion and not self.is_exiting:
            # Step onto the screen towards stand_x
            step = self.walk_speed * self.direction.value
            self.x += step

            reached = (self.direction == Direction.RIGHT and self.x >= self.stand_x) or \
                      (self.direction == Direction.LEFT and self.x <= self.stand_x)
            if reached:
                self.x = self.stand_x
                if self.interaction_mode == "kiss":
                    self.state = State.WAITING_KISS
                    self.is_waiting_for_companion = True
                else:
                    self.state = State.WAITING_HUG
                    self.is_waiting_for_companion = True

                if self.on_visitor_ready:
                    self.on_visitor_ready(self.x)

        elif self.state in (State.WAITING_HUG, State.WAITING_KISS):
            # Waiting for the companion to run over
            pass

        elif self.state == State.HUGGING:
            self.hug_timer += dt
            if self.hug_timer >= 4.8:
                # Hug finished! Primary companion returns to idle, visitor begins walk off-screen
                if self.on_interaction_end:
                    self.on_interaction_end()
                self.is_exiting = True
                self.state = State.WALKING
                # Turn back toward the screen border she entered from to walk back the same distance out
                self.direction = self.exit_direction

        elif self.state == State.KISSING:
            self.hug_timer += dt
            if self.hug_timer >= 4.8:
                # Kiss sequence finished! Primary companion returns to idle, visitor begins walk off-screen
                if self.on_interaction_end:
                    self.on_interaction_end()
                self.is_exiting = True
                self.state = State.WALKING
                # Turn back toward the screen border she entered from to walk back the same distance out
                self.direction = self.exit_direction

        elif self.is_exiting:
            step = (self.walk_speed * 1.3) * self.direction.value
            self.x += step

            # If reached screen edge, close window and trigger cleanup callback
            if (self.direction == Direction.LEFT and self.x < self.screen_left - 130) or \
               (self.direction == Direction.RIGHT and self.x > self.screen_left + self.screen_width + 120):
                self.tick_timer.stop()
                self.speech_bubble.hide()
                self._notify_visitor_finished()
                self.close()
                return

        self.move(int(self.x), int(self.y))

        # Dynamic repositioning of speech bubble during walk / run / hug
        if self.speech_bubble.isVisible():
            anchor_x = int(self.x + self.width() / 2)
            anchor_y = int(self.y)
            self.speech_bubble.reposition(anchor_x, anchor_y, companion_height=self.height())

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        phase = self.walk_phase if self.state in (State.WALKING, State.KISSING) else 0.0
        pixmap = self.renderer.create_sprite(self.state.value, self.direction, walk_phase=phase)
        if not pixmap.isNull():
            painter.drawPixmap(self.rect(), pixmap)
        painter.end()

    def closeEvent(self, event) -> None:
        try:
            if hasattr(self, "tick_timer") and self.tick_timer.isActive():
                self.tick_timer.stop()
            self._notify_visitor_finished()
        except Exception:
            pass
        self.speech_bubble.close()
        super().closeEvent(event)
