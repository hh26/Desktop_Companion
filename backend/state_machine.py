"""Finite State Machine and Physics Engine for Display Buddy."""

from dataclasses import dataclass
from enum import Enum
import random
from typing import Optional, Callable


class State(Enum):
    IDLE = "idle"
    WALKING = "walking"
    SITTING = "sitting"
    SLEEPING = "sleeping"
    DRAGGED = "dragged"
    FALLING = "falling"
    WAITING_HUG = "waiting_hug"
    HUGGING = "hugging"
    WAITING_KISS = "waiting_kiss"
    KISSING = "kissing"
    HANGING = "hanging"


class Direction(Enum):
    LEFT = -1
    RIGHT = 1


@dataclass
class EngineUpdate:
    state: State
    direction: Direction
    x: float
    y: float
    event_sound: Optional[str] = None
    event_speech: Optional[str] = None


class CompanionEngine:
    def __init__(self, config: dict):
        self.config = config
        self.state = State.IDLE
        self.direction = Direction.RIGHT

        # Movement parameters
        movement_cfg = config.get("movement", {})
        self.walk_speed = float(movement_cfg.get("walk_speed_px_per_tick", 3.0))
        self.wander_min = float(movement_cfg.get("wander_interval_min_seconds", 10.0))
        self.wander_max = float(movement_cfg.get("wander_interval_max_seconds", 25.0))
        self.gravity = float(movement_cfg.get("gravity_px_per_tick", 8.0))

        # Behavior weights
        self.behavior_weights = config.get(
            "behavior_weights",
            {"idle": 0.40, "wander": 0.40, "sleep": 0.20}
        )

        # Coordinate & bounds management
        self.x: float = 300.0
        self.y: float = 500.0
        self.vy: float = 0.0

        render_cfg = config.get("render", {})
        scale = float(render_cfg.get("scale", 2.0))
        self.width = int(render_cfg.get("frame_width", 48) * scale)
        self.height = int(render_cfg.get("frame_height", 48) * scale)

        # Floor offset to eliminate taskbar gap (compensates for transparent margin below shoes)
        self.floor_offset = int(movement_cfg.get("floor_offset", 15))

        # Work area boundaries (default fallback values)
        self.min_x: int = 0
        self.min_y: int = 0
        self.max_x: int = 1920 - self.width
        self.max_y: int = 1080 - self.height + self.floor_offset

        # State Timers
        self.state_time: float = 0.0
        self.target_duration: float = self._pick_idle_duration()

        # Drag tracking
        self.drag_offset_x: float = 0.0
        self.drag_offset_y: float = 0.0

        # Event callbacks
        self.sound_event_callback: Optional[Callable[[str], None]] = None
        self.speech_event_callback: Optional[Callable[[str], None]] = None

    def set_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> None:
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max(min_x, max_x - self.width)
        self.max_y = max(min_y, max_y - self.height + self.floor_offset)
        self.x = max(float(self.min_x), min(float(self.max_x), self.x))
        self.y = max(float(self.min_y), min(float(self.max_y), self.y))

    def _pick_idle_duration(self) -> float:
        return random.uniform(1.5, 3.5)

    def _pick_walk_duration(self) -> float:
        return random.uniform(4.0, 8.0)

    def _pick_sit_duration(self) -> float:
        return random.uniform(2.5, 5.0)

    def _pick_sleep_duration(self) -> float:
        return random.uniform(8.0, 16.0)

    def handle_mouse_down(self, mouse_screen_x: int, mouse_screen_y: int) -> None:
        self.drag_offset_x = mouse_screen_x - self.x
        self.drag_offset_y = mouse_screen_y - self.y
        self.state = State.DRAGGED
        self.vy = 0.0
        self.state_time = 0.0

    def handle_mouse_drag(self, mouse_screen_x: int, mouse_screen_y: int) -> None:
        if self.state == State.DRAGGED:
            new_x = mouse_screen_x - self.drag_offset_x
            new_y = mouse_screen_y - self.drag_offset_y
            self.x = max(float(self.min_x), min(float(self.max_x), float(new_x)))
            self.y = max(float(self.min_y), min(float(self.max_y), float(new_y)))

    def handle_mouse_up(self, allow_hang: bool = False, hang_chance: float = 0.22) -> bool:
        if self.state == State.DRAGGED:
            if self.y < self.max_y - 2.0:
                if allow_hang and random.random() < hang_chance:
                    self.state = State.HANGING
                    self.vy = 0.0
                    self.state_time = 0.0
                    self.target_duration = random.uniform(3.5, 6.0)
                    return True
                else:
                    self.state = State.FALLING
                    self.vy = 0.0
                    return False
            else:
                self.state = State.SITTING
                self.state_time = 0.0
                self.target_duration = self._pick_sit_duration()
                return False
        return False

    def update(self, delta_time: float) -> EngineUpdate:
        self.state_time += delta_time
        sound_trigger = None
        speech_trigger = None

        if self.state == State.IDLE:
            if self.state_time >= self.target_duration:
                w_wander = float(self.behavior_weights.get("wander", 0.70))
                w_idle = float(self.behavior_weights.get("idle", 0.10))
                w_sleep = float(self.behavior_weights.get("sleep", 0.20))
                total_w = w_wander + w_idle + w_sleep
                
                wander_thresh = (w_wander / total_w) if total_w > 0 else 0.70
                sleep_thresh = wander_thresh + ((w_sleep / total_w) if total_w > 0 else 0.20)
                
                r = random.random()
                if r < wander_thresh:
                    self.state = State.WALKING
                    self.target_duration = self._pick_walk_duration()
                    self.state_time = 0.0
                    self.direction = random.choice([Direction.LEFT, Direction.RIGHT])
                elif r < sleep_thresh:
                    self.state = State.SITTING
                    self.target_duration = self._pick_sit_duration()
                    self.state_time = 0.0
                else:
                    self.target_duration = self._pick_idle_duration()
                    self.state_time = 0.0

        elif self.state == State.WALKING:
            # Move horizontally
            step = self.walk_speed * self.direction.value
            self.x += step

            hit_edge = False
            if self.x <= self.min_x:
                self.x = float(self.min_x)
                self.direction = Direction.RIGHT
                hit_edge = True
            elif self.x >= self.max_x:
                self.x = float(self.max_x)
                self.direction = Direction.LEFT
                hit_edge = True

            if hit_edge or self.state_time >= self.target_duration:
                # Transition to sitting when reached screen border or target duration reached
                self.state = State.SITTING
                self.target_duration = self._pick_sit_duration()
                self.state_time = 0.0

        elif self.state == State.SITTING:
            if self.state_time >= self.target_duration:
                # Sit -> Sleeping or back to Idle
                if random.random() < 0.5:
                    self.state = State.SLEEPING
                    self.target_duration = self._pick_sleep_duration()
                else:
                    self.state = State.IDLE
                    self.target_duration = self._pick_idle_duration()
                self.state_time = 0.0

        elif self.state == State.SLEEPING:
            if self.state_time >= self.target_duration:
                self.state = State.IDLE
                self.target_duration = self._pick_idle_duration()
                self.state_time = 0.0

        elif self.state == State.FALLING:
            # Apply gravity physics
            self.vy += self.gravity * (delta_time * 10.0)
            self.y += self.vy
            if self.y >= self.max_y:
                self.y = float(self.max_y)
                self.vy = 0.0
                self.state = State.SITTING
                self.target_duration = self._pick_sit_duration()
                self.state_time = 0.0
                sound_trigger = "click.wav"

        elif self.state == State.DRAGGED:
            # Position updated directly by mouse
            pass

        elif self.state in (State.WAITING_HUG, State.WAITING_KISS):
            # Waits in place facing incoming friend
            pass

        elif self.state in (State.HUGGING, State.KISSING):
            # Holds warm embrace or showering cheek kisses
            if self.state_time >= self.target_duration:
                self.state = State.IDLE
                self.state_time = 0.0
                self.target_duration = self._pick_idle_duration()

        elif self.state == State.HANGING:
            # Companion hangs suspended in mid-air until duration expires, then falls
            if self.state_time >= self.target_duration:
                self.state = State.FALLING
                self.vy = 0.0
                self.state_time = 0.0
                sound_trigger = "wake.wav"

        return EngineUpdate(
            state=self.state,
            direction=self.direction,
            x=self.x,
            y=self.y,
            event_sound=sound_trigger,
            event_speech=speech_trigger
        )
