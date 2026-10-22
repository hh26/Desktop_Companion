# Architecture Specification — Display Buddy (Tier 2 Desktop Companion)

## 1. System Overview & Objectives
Display Buddy is an autonomous, lightweight desktop companion (screenmate) built with Python and PyQt6. It renders transparently on the Windows desktop, adheres to taskbar work areas, wanders autonomously with a configurable Finite State Machine (FSM), reacts to mouse interactions, displays speech bubbles, plays sound effects, and provides a customizable skin architecture.

---

## 2. Directory Structure & Squad Boundaries

```text
Display Buddy/
├── architecture.md               # System architecture and API contracts (Phase 1)
├── main.py                       # Root launcher connecting Backend & Frontend
├── requirements.txt              # Project dependencies
├── backend/                      # @backend-engineer domain
│   ├── __init__.py
│   ├── state_machine.py          # FSM (Idle, Walking, Sitting, Sleeping, Dragged, Falling)
│   ├── skin_loader.py            # Skin parser and validator (config.json, dialogues.json)
│   ├── dialogue_manager.py       # Speech bubble text selection and quote triggers
│   ├── sound_manager.py          # Sound effect player (safe for headless/audio-disabled)
│   └── win32_utils.py            # WorkArea query, DPI awareness, per-pixel alpha hit tests
├── frontend/                     # @frontend-engineer domain
│   ├── __init__.py
│   ├── companion_window.py       # Transparent, frameless, topmost PyQt6 window
│   ├── sprite_renderer.py        # Frame animation player, scale, flip logic
│   ├── speech_bubble.py          # Floating speech bubble widget with auto-dismiss
│   └── tray_icon.py              # System tray menu (Pause, Mute, Skin, Exit)
├── skins/                        # Content & Skin Packs
│   └── default_companion/
│       ├── config.json           # Timing, scale, speed, behavior weights
│       ├── dialogues.json        # Idle and interaction speech quotes
│       ├── sprites/              # Animation frames (idle, walk, sit, sleep, drag, fall)
│       └── sounds/               # Sound effects (click, wake, jump)
└── tests/                        # @qa-engineer domain
    ├── __init__.py
    ├── test_state_machine.py     # Unit tests for FSM transitions and timers
    ├── test_skin_loader.py       # Unit tests for skin configuration loading
    └── test_dialogue_manager.py  # Unit tests for dialogue triggers
```

---

## 3. Data Schemas & Configurations

### 3.1 `config.json`
```json
{
  "name": "Display Buddy Default",
  "version": "1.0.0",
  "author": "Antigravity Squad",
  "render": {
    "scale": 2.0,
    "fps": 10,
    "frame_width": 48,
    "frame_height": 48
  },
  "movement": {
    "walk_speed_px_per_tick": 4,
    "wander_interval_min_seconds": 10,
    "wander_interval_max_seconds": 25,
    "gravity_px_per_tick": 8
  },
  "behavior_weights": {
    "idle": 0.40,
    "wander": 0.40,
    "sleep": 0.20
  },
  "events": {
    "on_click": "play_sound:click.wav",
    "on_drag": "switch_state:dragged"
  }
}
```

### 3.2 `dialogues.json`
```json
{
  "idle_quotes": [
    "Just stretching my legs!",
    "Working hard today?",
    "Need some coffee...",
    "Everything looking good!"
  ],
  "click_quotes": [
    "Hey! That tickles!",
    "Need help with your code?",
    "I'm keeping you company!"
  ]
}
```

---

## 4. Exact API Contracts

### 4.1 Backend Engine Interface
```python
class State(Enum):
    IDLE = "idle"
    WALKING = "walking"
    SITTING = "sitting"
    SLEEPING = "sleeping"
    DRAGGED = "dragged"
    FALLING = "falling"

class Direction(Enum):
    LEFT = -1
    RIGHT = 1

class CompanionEngine:
    def __init__(self, skin_path: str): ...
    def update(self, delta_time: float) -> EngineUpdate: ...
    def handle_mouse_down(self, x: int, y: int) -> None: ...
    def handle_mouse_drag(self, x: int, y: int) -> None: ...
    def handle_mouse_up(self) -> None: ...
    def set_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> None: ...
    def get_speech_text(self) -> Optional[str]: ...
```

### 4.2 Frontend Engine Integration
- `CompanionWindow` instantiates `CompanionEngine`.
- At 60 FPS / tick rate (e.g., 20–30ms per tick), queries `engine.update(dt)`.
- Moves the `QPoint(x, y)` of the window based on updated state.
- Updates sprite frame according to current `state` and `direction`.
- If `engine.get_speech_text()` yields text, shows `SpeechBubbleWidget(x, y - offset, text)`.

---

## 5. Win32 Transparency & Hit Testing
- Frameless window: `Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool` (no taskbar button).
- Translucent canvas: `Qt.WidgetAttribute.WA_TranslucentBackground`.
- Per-Pixel Hit-Testing: In `mousePressEvent`, the window inspects the alpha channel of the current sprite at the click coordinate. If `alpha == 0`, the event is ignored or forwarded, preventing clicks on transparent empty margins from catching the cursor.
