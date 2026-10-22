"""Display Buddy — Desktop Companion Application Entry Point."""

import datetime
import os
import sys
import traceback

# Ensure UTF-8 streams on Windows to prevent UnicodeEncodeError with emojis
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication

from frontend.companion_window import CompanionWindow
from frontend.tray_icon import TrayIcon
from backend.path_utils import get_base_dir


def install_crash_handler(base_dir: str) -> None:
    """Installs a global uncaught exception hook that records crash traces to crash.log."""
    log_path = os.path.join(base_dir, "crash.log")

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"CRASH OCCURRED: {timestamp}\n")
                f.write(f"{'=' * 60}\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        except Exception:
            pass

        try:
            print(f"\n[Crash Handler] Uncaught Exception occurred at {timestamp}! Details logged to {log_path}", file=sys.stderr)
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        except Exception:
            pass

    sys.excepthook = handle_exception


def main() -> None:
    base_dir = get_base_dir()
    install_crash_handler(base_dir)

    print("=" * 50)
    print("🐾 Starting Display Buddy Desktop Companion...")
    print("=" * 50)

    # 1. Initialize Qt Application (Qt 6 natively sets DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # 2. Resolve default skin path
    default_skin = os.path.join(base_dir, "skins", "default_companion")

    # 3. Initialize Companion Window
    window = CompanionWindow(default_skin)
    app.aboutToQuit.connect(window.quit_application)

    # 4. Initialize System Tray Icon
    icon_pixmap = window.renderer.get_pixmap(
        window.engine.state,
        window.engine.direction
    )
    tray_icon = TrayIcon(
        icon=QIcon(icon_pixmap),
        on_toggle_pause=window.toggle_pause,
        on_toggle_mute=window.toggle_mute,
        on_trigger_speech=lambda: window.trigger_speech(
            window.dialogue_mgr.get_random_idle_quote() or "Hello!"
        ),
        on_exit=window.quit_application,
        on_reset_position=window.reset_position
    )
    tray_icon.show()

    # 5. Show companion window & force kernel-level HWND_TOPMOST over full-screen IDEs
    window.show()
    window.raise_()
    window.activateWindow()

    # Enforce native Win32 HWND_TOPMOST (-1)
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = int(window.winId())
            # HWND_TOPMOST (-1), SWP_NOMOVE (0x2) | SWP_NOSIZE (0x1) | SWP_NOACTIVATE (0x10) | SWP_SHOWWINDOW (0x40)
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0040)
        except Exception:
            pass

    print(f"✨ Companion is live at desktop coordinates: X={int(window.engine.x)}, Y={int(window.engine.y)}")
    print(f"📐 Size: {window.width()}x{window.height()} px")
    print("👀 Look near the bottom of your screen (above the taskbar) or system tray.")
    print("💡 Left-click to pet, click & drag to move. To exit, right-click the tray icon or press Ctrl+C.")
    print("📍 Lost your companion? Click the system tray icon or right-click > Bring to Front to summon him anytime!")
    print("=" * 50)

    # 6. Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        try:
            print(f"\n[Error] Failed to start Display Buddy: {exc}")
        except Exception:
            pass
        traceback.print_exc()
        sys.exit(1)
