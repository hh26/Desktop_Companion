# Display Buddy 🐾

An autonomous, customizable, lightweight virtual desktop companion (screenmate) built with Python and PyQt6.

Display Buddy lives transparently on your Windows desktop, idles, wanders, sits above your taskbar, responds to mouse clicks and drag-and-drop with physics, speaks cartoon dialogues, and supports custom skins.

---

## 🌟 Key Features

- **Transparent Canvas:** Frameless, borderless, always-on-top window that renders pixel art smoothly on top of open Windows applications.
- **Per-Pixel Click-Through:** Transparent margins allow mouse clicks to pass through to the apps behind the companion; only opaque pixels register clicks and drags.
- **Finite State Machine (FSM):** Complete autonomous lifecycle (`Idle`, `Walking`, `Sitting`, `Sleeping`, `Dragged`, `Falling`).
- **Windows Taskbar Awareness:** Queries `SPI_GETWORKAREA` to clamp movement directly on top of the Windows taskbar without clipping or falling behind.
- **Per-Monitor DPI Awareness:** Crisp, unblurred nearest-neighbor scaled pixel art on high-DPI displays (100%, 125%, 150%+).
- **Cartoon Speech Bubbles:** Displays periodic idle remarks, encouragement, or witty responses when clicked.
- **Sound Effects:** Cheerful pitch-swept pop and chime sounds on actions.
- **System Tray Management:** Easily pause/resume movement, mute audio, trigger speech, or exit cleanly from the Windows tray.
- **Customizable Skin System:** Decoupled folder structure allows adding custom skins without touching any core engine code.

---

## 📁 Project Architecture

```text
Display Buddy/
├── architecture.md               # System architecture and API contracts
├── main.py                       # Application entry point
├── run_tests.py                  # Test runner (pytest / unittest)
├── requirements.txt              # Project dependencies (PyQt6, pytest)
├── backend/                      # Engine & Operating System Integration
│   ├── state_machine.py          # FSM, physics, boundaries, and drag mechanics
│   ├── skin_loader.py            # Skin parser and validator
│   ├── dialogue_manager.py       # Speech bubble text and quote triggers
│   ├── sound_manager.py          # Asynchronous audio playback and mute controls
│   ├── asset_generator.py        # Procedural sprite & sound generator
│   └── win32_utils.py            # DPI awareness and SPI_GETWORKAREA integration
├── frontend/                     # UI & Presentation Layer
│   ├── companion_window.py       # Frameless transparent QWidget & event handling
│   ├── sprite_renderer.py        # Sprite loading, nearest-neighbor scaling & alpha hit-testing
│   ├── speech_bubble.py          # Rounded cartoon speech bubble widget
│   └── tray_icon.py              # System tray icon and context menu
├── skins/                        # Skin Packs
│   └── default_companion/
│       ├── config.json           # Movement, render scaling, and behavior weights
│       ├── dialogues.json        # Speech quotes
│       ├── sprites/              # Animation frames (.png)
│       └── sounds/               # Audio effects (.wav)
└── tests/                        # Comprehensive automated test suite
    ├── test_state_machine.py     # FSM transitions and gravity physics tests
    ├── test_skin_loader.py       # Config loading and asset validation tests
    ├── test_dialogue_manager.py  # Dialogue interval and quote tests
    └── test_sound_manager.py     # Sound manager and mute toggle tests
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Display Buddy
```bash
python main.py
```
*Note: Default sprites and sounds will be automatically generated if not already present on disk.*

### 3. Run Test Suite
```bash
python run_tests.py
# or
pytest -v
```

---

## 🎨 Creating a Custom Skin

To add your own desktop pet:
1. Create a new folder under `skins/<your_pet_name>/`.
2. Add a `config.json` defining frame sizes, scales, and speeds:
```json
{
  "name": "My Custom Pet",
  "render": {
    "scale": 2.5,
    "fps": 10,
    "frame_width": 32,
    "frame_height": 32
  },
  "movement": {
    "walk_speed_px_per_tick": 4,
    "wander_interval_min_seconds": 10,
    "wander_interval_max_seconds": 25,
    "gravity_px_per_tick": 8
  }
}
```
3. Place your sprite PNGs (`idle.png`, `walk_left.png`, `walk_right.png`, `sit.png`, `sleep.png`, `dragged.png`, `fall.png`) in `skins/<your_pet_name>/sprites/`.
4. Place your audio WAV files (`click.wav`, `wake.wav`) in `skins/<your_pet_name>/sounds/`.
5. Add your custom dialogue quotes in `skins/<your_pet_name>/dialogues.json`.

---

## 🖱️ Controls & Interactions

- **Left Click & Drag:** Pick up your companion and move it anywhere on your screen. Releasing it mid-air lets it fall with gravity back to the floor.
- **Left Click:** Tickle/pat your companion to trigger speech and playful sounds.
- **Transparent Areas:** Clicks through the transparent empty space directly reach whatever window is behind it.
- **System Tray Icon:** Right-click the companion icon in the Windows taskbar tray to Pause/Resume, Mute/Unmute, or Exit.
