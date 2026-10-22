"""Automated packaging script for Display Buddy.
Creates two ready-to-share distributions:
1. 'DisplayBuddy_Portable.zip': Standalone executable bundle (Zero Python required by recipient).
2. 'DisplayBuddy_Source_OneClick.zip': Clean source zip with double-clickable Start_DisplayBuddy.bat.
"""

import os
import sys
import shutil
import subprocess
import zipfile

# Ensure UTF-8 output on Windows terminal
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def ensure_pyinstaller() -> bool:
    """Verifies PyInstaller is available, or installs it automatically."""
    try:
        import PyInstaller
        print("[Build] PyInstaller is already installed.")
        return True
    except ImportError:
        print("[Build] Installing PyInstaller...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)
        return res.returncode == 0


def create_portable_exe() -> str:
    """Builds the standalone onedir portable executable using PyInstaller."""
    print("\n" + "=" * 60)
    print("[*] Building Standalone Portable Executable (Option A)...")
    print("=" * 60)

    if not ensure_pyinstaller():
        print("[ERROR] Could not install PyInstaller.")
        return ""

    app_dist = os.path.join(DIST_DIR, "DisplayBuddy")
    if os.path.exists(app_dist):
        shutil.rmtree(app_dist, ignore_errors=True)

    # PyInstaller command: windowed (no console window), onedir
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "DisplayBuddy",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "main.py"
    ]

    print("[Build] Running PyInstaller:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=BASE_DIR, check=False)
    if res.returncode != 0:
        print("[ERROR] PyInstaller compilation failed!")
        return ""

    # Copy external asset dependencies to dist/DisplayBuddy
    dst_skins = os.path.join(app_dist, "skins")
    if os.path.exists(dst_skins):
        shutil.rmtree(dst_skins, ignore_errors=True)

    print("[Build] Copying skins and documentation...")
    shutil.copytree(
        os.path.join(BASE_DIR, "skins"),
        dst_skins,
        ignore=shutil.ignore_patterns("backup", "*.tmp", "*neck*.png")
    )

    # Copy user documentation and stop helper
    shutil.copyfile(
        os.path.join(BASE_DIR, "README_FOR_FRIEND.txt"),
        os.path.join(app_dist, "README_FOR_FRIEND.txt")
    )
    shutil.copyfile(
        os.path.join(BASE_DIR, "Stop_DisplayBuddy.bat"),
        os.path.join(app_dist, "Stop_DisplayBuddy.bat")
    )

    # Zip the portable distribution
    zip_path = os.path.join(BASE_DIR, "DisplayBuddy_Portable.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"[Build] Compressing standalone bundle into {os.path.basename(zip_path)}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dist):
            for file in files:
                abs_f = os.path.join(root, file)
                rel_f = os.path.relpath(abs_f, DIST_DIR)
                zf.write(abs_f, rel_f)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[SUCCESS] Portable bundle created: {zip_path} ({size_mb:.1f} MB)")
    return zip_path


def create_source_zip() -> str:
    """Packages the lightweight clean source distribution with Start_DisplayBuddy.bat."""
    print("\n" + "=" * 60)
    print("[*] Building One-Click Source Package (Option B)...")
    print("=" * 60)

    zip_path = os.path.join(BASE_DIR, "DisplayBuddy_Source_OneClick.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    include_files = [
        "main.py",
        "requirements.txt",
        "Start_DisplayBuddy.bat",
        "Stop_DisplayBuddy.bat",
        "README_FOR_FRIEND.txt",
    ]

    include_dirs = [
        "backend",
        "frontend",
        "skins",
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add root files
        for f in include_files:
            p = os.path.join(BASE_DIR, f)
            if os.path.exists(p):
                zf.write(p, os.path.join("DisplayBuddy", f))

        # Add directories
        for d in include_dirs:
            p = os.path.join(BASE_DIR, d)
            for root, dirs, files in os.walk(p):
                # Ignore backup directories and pycache
                dirs[:] = [d for d in dirs if d not in ("__pycache__", "backup", ".pytest_cache")]
                for file in files:
                    if file.endswith((".pyc", ".pyo", ".tmp")):
                        continue
                    abs_f = os.path.join(root, file)
                    rel_f = os.path.relpath(abs_f, BASE_DIR)
                    zf.write(abs_f, os.path.join("DisplayBuddy", rel_f))

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[SUCCESS] Source package created: {zip_path} ({size_mb:.1f} MB)")
    return zip_path


def main():
    print("--- Display Buddy Packaging Suite ---")
    # 1. Option B: Source zip (Fast, lightweight)
    src_zip = create_source_zip()

    # 2. Option A: Standalone portable executable (Zero-install)
    exe_zip = create_portable_exe()

    print("\n" + "=" * 60)
    print("[*] ALL PACKAGES READY TO SHARE!")
    print("=" * 60)
    if exe_zip:
        print(f"  * Standalone Portable (Zero setup for friend) : {os.path.basename(exe_zip)}")
    if src_zip:
        print(f"  * One-Click Source Launcher (Lightweight ~10MB): {os.path.basename(src_zip)}")
    print("=" * 60)
    if exe_zip:
        print(f"• Standalone Portable (Zero setup for friend) : {os.path.basename(exe_zip)}")
    if src_zip:
        print(f"• One-Click Source Launcher (Lightweight ~10MB): {os.path.basename(src_zip)}")


if __name__ == "__main__":
    main()
