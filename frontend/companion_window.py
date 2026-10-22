"""Main transparent companion window with human-like animation, context menu, and hug mechanics."""

import os
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent, QGuiApplication, QPainter
from PyQt6.QtWidgets import QWidget, QMenu, QApplication

from backend.state_machine import CompanionEngine, State, Direction
from backend.skin_loader import Skin
from backend.dialogue_manager import DialogueManager
from backend.sound_manager import SoundManager
from backend.win32_utils import get_desktop_work_area
from backend.humanoid_renderer import HumanoidRenderer
from frontend.speech_bubble import SpeechBubble
from frontend.friend_window import FriendCompanionWindow
from backend.path_utils import get_asset_path


class CompanionWindow(QWidget):
    def __init__(self, skin_path: str):
        super().__init__()

        # Window styling: Frameless, Topmost, Tool (no taskbar clutter), Translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Core subsystems
        self.skin = Skin(skin_path)
        self.engine = CompanionEngine(self.skin.config)
        # Main companion: Boy character from user reference photo
        self.renderer = HumanoidRenderer(character_type="boy_main", palette_name="default")
        self.dialogue_mgr = DialogueManager(self.skin.dialogues)
        self.sound_mgr = SoundManager()

        # Speech bubble & Avatar
        self.speech_bubble = SpeechBubble()
        self.avatar_path = get_asset_path("skins", "avatar_boy.png")

        # Configurable companion identity / initials (1-2 letters below avatar)
        d_initials = self.skin.dialogues.get("initials", {})
        if isinstance(d_initials, dict):
            comp_init = d_initials.get("companion") or self.skin.dialogues.get("companion_initials")
        else:
            comp_init = self.skin.dialogues.get("companion_initials")

        comp_cfg = self.skin.config.get("companion", {})
        self.companion_name = comp_cfg.get("name", "Buddy")
        raw_initials = comp_init or comp_cfg.get("initials", "B")
        self.companion_initials = str(raw_initials).strip()[:2].upper()
        self.interactions = self.skin.dialogues.get("interaction_dialogues", {})

        # Runtime controls
        self.is_paused: bool = False
        self.is_dragging: bool = False
        self.is_mouse_pressed: bool = False
        self.press_pos = None
        self.has_dragged: bool = False
        self.last_click_time: float = 0.0
        self.friend_window = None

        # Safeguards and state tracking
        self.is_quitting: bool = False
        self.run_timeout: float = 0.0
        self._tick_counter: int = 0

        # Walking, Hug & Kiss running tracker
        self.walk_phase: float = 0.0
        self.is_running_to_hug: bool = False
        self.hug_target_x: float = 0.0
        self.is_running_to_kiss: bool = False
        self.kiss_target_x: float = 0.0

        # Apply sizing
        self.setFixedSize(self.renderer.target_width, self.renderer.target_height)

        # Initialize screen bounds excluding taskbar & place on floor
        self._sync_screen_bounds(preserve_position=False)

        # Dynamic screen geometry changes (e.g. resolution change, monitor connect/disconnect)
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen.availableGeometryChanged.connect(self._on_screen_geometry_changed)
            screen.geometryChanged.connect(self._on_screen_geometry_changed)

        # Update loop (30 FPS -> 33ms interval)
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._on_tick)
        self.tick_interval_ms = 33
        self.tick_timer.start(self.tick_interval_ms)

        # Move to initial position on screen
        self.move(int(self.engine.x), int(self.engine.y))

        # Greet user shortly after spawn
        QTimer.singleShot(600, lambda: self.trigger_speech("Hello! I'm your desktop buddy! ✨\n(Right-click me for actions!)"))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._ensure_topmost()

    def _ensure_topmost(self) -> None:
        """Reinforces HWND_TOPMOST without stealing keyboard/input focus."""
        try:
            import sys
            if sys.platform == "win32":
                import ctypes
                hwnd = int(self.winId())
                # HWND_TOPMOST (-1)
                # SWP_NOSIZE (0x0001) | SWP_NOMOVE (0x0002) | SWP_NOACTIVATE (0x0010) | SWP_SHOWWINDOW (0x0040)
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0040)
        except Exception:
            pass

    def _sync_screen_bounds(self, preserve_position: bool = False) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            left = geo.x()
            top = geo.y()
            right = geo.x() + geo.width()
            bottom = geo.y() + geo.height()
            self.engine.set_bounds(left, top, right, bottom)

            if not preserve_position:
                # Spawn on floor, slightly indented
                self.engine.x = float(left + 240)
                self.engine.y = float(self.engine.max_y)
                self.engine.state = State.IDLE
                self.engine.target_duration = 1.0  # Starts walking after 1 second
            else:
                self.engine.x = max(float(self.engine.min_x), min(float(self.engine.max_x), self.engine.x))
                self.engine.y = max(float(self.engine.min_y), min(float(self.engine.max_y), self.engine.y))
        else:
            left, top, right, bottom = get_desktop_work_area()
            self.engine.set_bounds(left, top, right, bottom)
            if not preserve_position:
                self.engine.y = float(self.engine.max_y)
            else:
                self.engine.x = max(float(self.engine.min_x), min(float(self.engine.max_x), self.engine.x))
                self.engine.y = max(float(self.engine.min_y), min(float(self.engine.max_y), self.engine.y))

    def _on_screen_geometry_changed(self, _geo=None) -> None:
        self._sync_screen_bounds(preserve_position=True)
        self.move(int(self.engine.x), int(self.engine.y))

    def reset_position(self) -> None:
        """Emergency recovery: Resets companion to visible center-floor and brings window to topmost."""
        self._sync_screen_bounds(preserve_position=False)
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.engine.x = float(geo.x() + (geo.width() - self.width()) / 2)
            self.engine.y = float(self.engine.max_y)
        else:
            self.engine.x = 400.0
            self.engine.y = float(self.engine.max_y)

        self.engine.state = State.IDLE
        self.engine.vy = 0.0
        self.engine.state_time = 0.0
        self.is_running_to_hug = False
        self.is_running_to_kiss = False
        self.run_timeout = 0.0
        self.is_paused = False

        self.move(int(self.engine.x), int(self.engine.y))
        self.show()
        self.raise_()
        self.activateWindow()
        self._ensure_topmost()
        self.trigger_speech("Here I am! ✨ Ready to hang out!")

    def _on_tick(self) -> None:
        try:
            dt = self.tick_interval_ms / 1000.0

            # Periodic topmost reassertion (every 60 ticks = ~2 seconds) to prevent sliding behind full-screen windows
            self._tick_counter += 1
            if self._tick_counter % 60 == 0:
                self._ensure_topmost()

            if not self.is_paused:
                if self.is_running_to_hug:
                    self.run_timeout += dt
                    dist = abs(self.engine.x - self.hug_target_x)

                    # Dynamic athletic sprint velocity: fast dash across desktop, smooth deceleration into embrace
                    if dist > 140.0:
                        run_speed = max(260.0, min(500.0, dist / 1.5))
                    else:
                        t = max(0.0, min(1.0, dist / 140.0))
                        run_speed = 150.0 + t * 150.0

                    step_size = min(run_speed * dt, dist)
                    step = step_size * self.engine.direction.value
                    self.engine.x += step

                    # Leg animation frequency proportional to running speed
                    phase_rate = 10.0 + min(8.0, (run_speed / 500.0) * 8.0)
                    self.walk_phase += dt * phase_rate

                    # Check if reached hug embrace point
                    reached = False
                    if dist <= 4.0:
                        reached = True
                    elif self.engine.direction == Direction.LEFT and self.engine.x <= self.hug_target_x:
                        reached = True
                    elif self.engine.direction == Direction.RIGHT and self.engine.x >= self.hug_target_x:
                        reached = True
                    elif self.run_timeout > 15.0:
                        reached = True

                    if reached:
                        self.engine.x = self.hug_target_x
                        self.is_running_to_hug = False
                        self.run_timeout = 0.0
                        self.engine.state = State.HUGGING
                        self.engine.state_time = 0.0
                        self.engine.target_duration = 5.0  # Synchronized with visitor duration
                        if self.friend_window:
                            self.friend_window.start_embrace()
                        snd_path = self.skin.get_sound_path("wake.wav")
                        self.sound_mgr.play(snd_path)
                        hug_text = self.get_boy_interaction_dialogue("hug")
                        if hug_text:
                            self.trigger_speech(hug_text, duration_ms=2200)

                    # Clamp inside screen bounds
                    self.engine.x = max(float(self.engine.min_x), min(float(self.engine.max_x), self.engine.x))
                    self.move(int(self.engine.x), int(self.engine.y))

                elif self.is_running_to_kiss:
                    self.run_timeout += dt
                    dist = abs(self.engine.x - self.kiss_target_x)

                    # Dynamic athletic sprint velocity: fast dash across desktop, smooth deceleration into kiss
                    if dist > 140.0:
                        run_speed = max(260.0, min(520.0, dist / 1.5))
                    else:
                        t = max(0.0, min(1.0, dist / 140.0))
                        run_speed = 150.0 + t * 150.0

                    step_size = min(run_speed * dt, dist)
                    step = step_size * self.engine.direction.value
                    self.engine.x += step

                    phase_rate = 10.0 + min(8.0, (run_speed / 500.0) * 8.0)
                    self.walk_phase += dt * phase_rate

                    # Check if reached kiss proximity
                    reached = False
                    if dist <= 4.0:
                        reached = True
                    elif self.engine.direction == Direction.LEFT and self.engine.x <= self.kiss_target_x:
                        reached = True
                    elif self.engine.direction == Direction.RIGHT and self.engine.x >= self.kiss_target_x:
                        reached = True
                    elif self.run_timeout > 15.0:
                        reached = True

                    if reached:
                        self.engine.x = self.kiss_target_x
                        self.is_running_to_kiss = False
                        self.run_timeout = 0.0
                        self.engine.state = State.KISSING
                        self.engine.state_time = 0.0
                        self.engine.target_duration = 5.0  # Synchronized with visitor duration
                        if self.friend_window:
                            self.friend_window.start_kiss()
                        snd_path = self.skin.get_sound_path("wake.wav")
                        self.sound_mgr.play(snd_path)
                        kiss_text = self.get_boy_interaction_dialogue("kiss")
                        if kiss_text:
                            self.trigger_speech(kiss_text, duration_ms=2200)

                    # Clamp inside screen bounds
                    self.engine.x = max(float(self.engine.min_x), min(float(self.engine.max_x), self.engine.x))
                    self.move(int(self.engine.x), int(self.engine.y))

                else:
                    prev_state = self.engine.state
                    update = self.engine.update(dt)

                    # Transition from hanging to falling: trigger realization drop dialogue
                    if prev_state == State.HANGING and self.engine.state == State.FALLING:
                        drop_quote = self.dialogue_mgr.get_random_hanging_drop_quote()
                        if drop_quote:
                            self.trigger_speech(drop_quote, duration_ms=2500)

                    # Animate walk cycle with limb swinging
                    if self.engine.state == State.WALKING:
                        self.walk_phase += dt * 9.5
                    elif self.engine.state == State.HUGGING:
                        self.walk_phase += dt * 3.0  # Gentle rhythmic swaying during embrace
                    elif self.engine.state == State.KISSING:
                        self.walk_phase += dt * 5.5  # Smooth, gentle kissing cadence
                    elif self.engine.state == State.HANGING:
                        self.walk_phase += dt * 4.0  # Gentle swinging while suspended mid-air
                    else:
                        self.walk_phase = 0.0

                    # Clamp inside screen bounds and move
                    self.engine.x = max(float(self.engine.min_x), min(float(self.engine.max_x), self.engine.x))
                    self.engine.y = max(float(self.engine.min_y), min(float(self.engine.max_y), self.engine.y))
                    self.move(int(self.engine.x), int(self.engine.y))

                    # Sound effects
                    if update.event_sound:
                        snd_path = self.skin.get_sound_path(update.event_sound)
                        self.sound_mgr.play(snd_path)

                    # Check dialogue periodic triggers
                    quote = self.dialogue_mgr.update(dt)
                    if quote and self.engine.state not in (State.HUGGING, State.WAITING_HUG, State.KISSING, State.WAITING_KISS):
                        self.trigger_speech(quote)

            # Dynamic repositioning of speech bubble during walk, drag, or hug run
            if self.speech_bubble.isVisible():
                anchor_x = int(self.x() + self.width() / 2)
                anchor_y = self.y()
                self.speech_bubble.reposition(anchor_x, anchor_y, companion_height=self.height())

            # Trigger redraw
            self.update()
        except Exception as exc:
            import sys
            print(f"[CompanionWindow] Warning in tick loop: {exc}", file=sys.stderr)

    def trigger_speech(self, text: str, duration_ms: int = 4500, initials: Optional[str] = None) -> None:
        anchor_x = int(self.x() + self.width() / 2)
        anchor_y = self.y()
        self.speech_bubble.show_speech(
            text, anchor_x, anchor_y,
            duration_ms=duration_ms,
            avatar_path=self.avatar_path,
            border_color="#f43f5e",
            companion_height=self.height(),
            initials=initials or self.companion_initials
        )

    def get_boy_interaction_dialogue(self, mode: str) -> Optional[str]:
        """Gets dialogue line for boy during hug or kiss."""
        line = self.interactions.get(mode, {}).get("boy")
        if not line:
            line = "*mwah!* *mwah!* *mwah!* 💕💋" if mode == "kiss" else "Aww, you sweetheart! 🥰❤️"
        return line

    def get_visitor_initials(self) -> str:
        """Retrieves visitor initials from dialogues.json or config.json."""
        d_init = self.skin.dialogues.get("initials", {})
        if isinstance(d_init, dict) and d_init.get("visitor"):
            return str(d_init.get("visitor")).strip()[:2].upper()
        if self.skin.dialogues.get("visitor_initials"):
            return str(self.skin.dialogues.get("visitor_initials")).strip()[:2].upper()
        return str(self.skin.config.get("visitor", {}).get("initials", "G")).strip()[:2].upper()

    # --- Right-Click Actions & Custom Menu ---
    def trigger_kiss(self) -> None:
        """Launches visitor to enter, and companion runs over to kiss her cheek multiple times like in Kiss_Gif!"""
        if self.friend_window is not None:
            return  # Sequence already active

        self.is_paused = False
        self.is_running_to_hug = False
        self.is_running_to_kiss = False
        self.engine.y = float(self.engine.max_y)

        # Multi-monitor aware check: face towards incoming visitor side
        screen = QGuiApplication.screenAt(QPoint(int(self.engine.x), int(self.engine.y)))
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry() if screen else None
        s_left = screen_geo.x() if screen_geo else 0
        s_width = screen_geo.width() if screen_geo else 1920

        if self.engine.x > (s_left + s_width / 2):
            self.engine.direction = Direction.LEFT
        else:
            self.engine.direction = Direction.RIGHT

        self.move(int(self.engine.x), int(self.engine.y))
        self.engine.state = State.WAITING_KISS

        def on_visitor_ready(visitor_x: float):
            # Friend has entered the screen and is waiting with a smile
            if self.engine.x > visitor_x:
                self.engine.direction = Direction.LEFT
                self.kiss_target_x = visitor_x + 30.0
            else:
                self.engine.direction = Direction.RIGHT
                self.kiss_target_x = visitor_x - 30.0

            self.is_running_to_kiss = True
            self.run_timeout = 0.0
            self.engine.state = State.WALKING

        def on_kiss_interaction_end():
            self.is_running_to_kiss = False
            self.engine.state = State.IDLE
            self.engine.state_time = 0.0
            self.engine.target_duration = self.engine._pick_idle_duration()
            if self.friend_window:
                self.engine.direction = self.friend_window.direction

        def on_visitor_finished():
            self.friend_window = None

        vis_initials = self.get_visitor_initials()
        self.friend_window = FriendCompanionWindow(
            target_x=self.engine.x,
            floor_y=float(self.engine.max_y),
            on_visitor_ready=on_visitor_ready,
            on_interaction_end=on_kiss_interaction_end,
            on_visitor_finished=on_visitor_finished,
            visitor_initials=vis_initials,
            interaction_mode="kiss",
            dialogues=self.skin.dialogues
        )

    def trigger_hug(self) -> None:
        """Launches a visitor to enter the screen, and primary companion runs over to hug her!"""
        if self.friend_window is not None:
            return  # Hug sequence already active

        self.is_paused = False
        self.is_running_to_hug = False
        self.is_running_to_kiss = False
        self.engine.y = float(self.engine.max_y)

        # Multi-monitor aware check: face towards incoming visitor side
        screen = QGuiApplication.screenAt(QPoint(int(self.engine.x), int(self.engine.y)))
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry() if screen else None
        s_left = screen_geo.x() if screen_geo else 0
        s_width = screen_geo.width() if screen_geo else 1920

        if self.engine.x > (s_left + s_width / 2):
            self.engine.direction = Direction.LEFT
        else:
            self.engine.direction = Direction.RIGHT

        self.move(int(self.engine.x), int(self.engine.y))
        self.engine.state = State.WAITING_HUG

        def on_visitor_ready(visitor_x: float):
            # Friend has entered the screen and is waiting with open arms
            if self.engine.x > visitor_x:
                self.engine.direction = Direction.LEFT
                self.hug_target_x = visitor_x + 36.0
            else:
                self.engine.direction = Direction.RIGHT
                self.hug_target_x = visitor_x - 36.0

            self.is_running_to_hug = True
            self.run_timeout = 0.0
            self.engine.state = State.WALKING

        def on_hug_interaction_end():
            self.is_running_to_hug = False
            self.engine.state = State.IDLE
            self.engine.state_time = 0.0
            self.engine.target_duration = self.engine._pick_idle_duration()
            if self.friend_window:
                self.engine.direction = self.friend_window.direction

        def on_visitor_finished():
            self.friend_window = None

        vis_initials = self.get_visitor_initials()
        self.friend_window = FriendCompanionWindow(
            target_x=self.engine.x,
            floor_y=float(self.engine.max_y),
            on_visitor_ready=on_visitor_ready,
            on_interaction_end=on_hug_interaction_end,
            on_visitor_finished=on_visitor_finished,
            visitor_initials=vis_initials,
            interaction_mode="hug",
            dialogues=self.skin.dialogues
        )

    def action_start_walking(self) -> None:
        self.engine.state = State.WALKING
        self.engine.state_time = 0.0
        self.engine.target_duration = 6.0
        self.trigger_speech("Time to stretch my legs! 🚶")

    def action_sit(self) -> None:
        self.engine.state = State.SITTING
        self.engine.state_time = 0.0
        self.engine.target_duration = 10.0
        self.trigger_speech("Taking a cozy seat on the taskbar. ☕")

    def action_sleep(self) -> None:
        self.engine.state = State.SLEEPING
        self.engine.state_time = 0.0
        self.engine.target_duration = 18.0
        self.trigger_speech("Power nap mode activated... Zzz 💤")

    def action_cycle_outfit(self) -> None:
        new_palette = self.renderer.cycle_palette()
        snd_path = self.skin.get_sound_path("click.wav")
        self.sound_mgr.play(snd_path)
        self.trigger_speech(f"Check out my {new_palette.title()} outfit! 🎨✨")

    def toggle_pause(self) -> bool:
        self.is_paused = not self.is_paused
        status = "Paused" if self.is_paused else "Resumed"
        self.trigger_speech(f"Movement {status}! ⏸️" if self.is_paused else f"Movement {status}! ▶️")
        return self.is_paused

    def toggle_mute(self) -> bool:
        muted = self.sound_mgr.toggle_mute()
        status = "Muted 🔇" if muted else "Unmuted 🔊"
        self.trigger_speech(f"Sounds {status}!")
        return muted

    def action_im_bored(self) -> None:
        """Responds to 'I'm bored.' with 'Hi bored, I'm [name]' dad joke or quirky suggestions."""
        quote = self.dialogue_mgr.get_bored_quote(companion_name=self.companion_name)
        self.trigger_speech(quote, duration_ms=4500)

    def action_say_something(self) -> None:
        """Responds to 'Say something' by saying 'something' or providing an interesting fact."""
        quote = self.dialogue_mgr.get_say_something_quote()
        self.trigger_speech(quote, duration_ms=4500)

    # --- Mouse & Context Menu Events ---
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        local_x = int(event.pos().x())
        local_y = int(event.pos().y())

        # Alpha hit testing: right clicks on empty margins pass through
        if not self.renderer.is_opaque_at(self.engine.state, self.engine.direction, local_x, local_y):
            event.ignore()
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #f8fafc;
                border: 2px solid #10b981;
                border-radius: 12px;
                padding: 6px;
                font-family: 'Segoe UI', system-ui;
                font-size: 13px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 8px;
                margin: 2px 0px;
            }
            QMenu::item:selected {
                background-color: #10b981;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #334155;
                margin: 4px 6px;
            }
        """)

        # Menu labels configurable via dialogues.json (under "menu_labels") or config.json
        labels = self.skin.dialogues.get("menu_labels", {})

        # 1. Partner Interactions
        kiss_label = labels.get("kiss", "😘 Kiss Visitor (Cheek Peck)")
        kiss_act = menu.addAction(kiss_label)
        kiss_act.triggered.connect(self.trigger_kiss)

        hug_label = labels.get("hug", "🤗 Hug Companion")
        hug_act = menu.addAction(hug_label)
        hug_act.triggered.connect(self.trigger_hug)

        # 2. Dialogue & Conversation Triggers
        bored_label = labels.get("bored", "🥱 I'm bored.")
        bored_act = menu.addAction(bored_label)
        bored_act.triggered.connect(self.action_im_bored)

        talk_label = labels.get("talk", "💬 Say Something")
        talk_act = menu.addAction(talk_label)
        talk_act.triggered.connect(self.action_say_something)

        menu.addSeparator()

        # 3. Actions & Poses
        walk_label = labels.get("walk", "🚶 Start Walking")
        walk_act = menu.addAction(walk_label)
        walk_act.triggered.connect(self.action_start_walking)

        sit_label = labels.get("sit", "☕ Sit Down")
        sit_act = menu.addAction(sit_label)
        sit_act.triggered.connect(self.action_sit)

        sleep_label = labels.get("sleep", "💤 Take a Nap")
        sleep_act = menu.addAction(sleep_label)
        sleep_act.triggered.connect(self.action_sleep)

        menu.addSeparator()

        # 4. Outfits & Customization
        palette_cap = self.renderer.palette_name.title()
        outfit_template = labels.get("outfit", f"🎨 Change Outfit ({palette_cap})")
        if "{palette}" in outfit_template:
            outfit_label = outfit_template.replace("{palette}", palette_cap)
        elif "(" not in outfit_template:
            outfit_label = f"{outfit_template} ({palette_cap})"
        else:
            outfit_label = outfit_template
        outfit_act = menu.addAction(outfit_label)
        outfit_act.triggered.connect(self.action_cycle_outfit)

        # 5. Pause & Sound
        if self.is_paused:
            pause_txt = labels.get("resume", "▶️ Resume Movement")
        else:
            pause_txt = labels.get("pause", "⏸️ Pause Movement")
        pause_act = menu.addAction(pause_txt)
        pause_act.triggered.connect(self.toggle_pause)

        if self.sound_mgr.is_muted:
            mute_txt = labels.get("unmute", "🔊 Unmute Sounds")
        else:
            mute_txt = labels.get("mute", "🔇 Mute Sounds")
        mute_act = menu.addAction(mute_txt)
        mute_act.triggered.connect(self.toggle_mute)

        menu.addSeparator()

        reset_label = labels.get("reset_pos", "📍 Reset Position (Bring to Front)")
        reset_act = menu.addAction(reset_label)
        reset_act.triggered.connect(self.reset_position)

        menu.addSeparator()

        # 6. Exit
        exit_label = labels.get("exit", "❌ Exit Display Buddy")
        exit_act = menu.addAction(exit_label)
        exit_act.triggered.connect(self.quit_application)

        menu.exec(event.globalPos())
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            local_x = int(event.position().x())
            local_y = int(event.position().y())

            # Alpha hit test
            if not self.renderer.is_opaque_at(self.engine.state, self.engine.direction, local_x, local_y):
                event.ignore()
                return

            event.accept()
            self.is_mouse_pressed = True
            self.is_dragging = False
            self.has_dragged = False
            self.press_pos = event.globalPosition().toPoint()
            self.engine.handle_mouse_down(int(event.globalPosition().x()), int(event.globalPosition().y()))
            # Note: No dialogue or sound is triggered here!
            # We defer until mouseReleaseEvent to distinguish between stationary clicks and dragging.

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_mouse_pressed and self.press_pos:
            curr_pos = event.globalPosition().toPoint()
            dist = (curr_pos - self.press_pos).manhattanLength()

            # Start dragging once movement exceeds threshold
            if dist >= 6 or self.is_dragging:
                self.is_dragging = True
                self.has_dragged = True

                # Hide speech bubble while dragging to prevent annoying visual clutter
                if self.speech_bubble.isVisible():
                    self.speech_bubble.hide()

                self.engine.handle_mouse_drag(int(curr_pos.x()), int(curr_pos.y()))
                self.move(int(self.engine.x), int(self.engine.y))
                event.accept()
                return

        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.is_mouse_pressed:
            self.is_mouse_pressed = False

            if self.has_dragged:
                # User was dragging the companion across the screen
                self.is_dragging = False
                hung = self.engine.handle_mouse_up(allow_hang=True)
                if hung:
                    hang_quote = self.dialogue_mgr.get_random_hanging_quote()
                    if hang_quote:
                        self.trigger_speech(hang_quote, duration_ms=4000)
            else:
                # User performed a stationary tap/click without dragging
                self.engine.handle_mouse_up(allow_hang=False)

                import time
                now = time.time()
                # Cooldown debounce: 0.8s between click quotes
                if now - self.last_click_time > 0.8:
                    self.last_click_time = now
                    snd_path = self.skin.get_sound_path("click.wav")
                    self.sound_mgr.play(snd_path)

                    click_quote = self.dialogue_mgr.get_random_click_quote()
                    if click_quote and self.engine.state not in (State.HUGGING, State.WAITING_HUG, State.KISSING, State.WAITING_KISS):
                        self.trigger_speech(click_quote)

            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        phase = self.walk_phase if (self.engine.state in (State.WALKING, State.HUGGING, State.KISSING, State.HANGING) or self.is_running_to_hug or self.is_running_to_kiss) else 0.0
        is_blinking = (int(self.engine.state_time * 2.5) % 8 == 0) and (self.engine.state == State.IDLE)
        pixmap = self.renderer.create_sprite(
            self.engine.state.value,
            self.engine.direction,
            walk_phase=phase,
            is_blinking=is_blinking
        )
        if pixmap and not pixmap.isNull():
            painter.drawPixmap(self.rect(), pixmap)
        painter.end()

    def quit_application(self) -> None:
        """Gracefully tears down friend window and speech bubble before quitting application."""
        self.is_quitting = True
        if self.friend_window:
            self.friend_window.close()
        self.speech_bubble.close()
        self.close()
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:
        if not self.is_quitting:
            # Protect against accidental close events (e.g. Alt+F4 or system close)
            event.ignore()
            return
        if self.friend_window:
            self.friend_window.close()
        self.speech_bubble.close()
        super().closeEvent(event)
