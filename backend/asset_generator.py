"""Procedural asset generator for default companion sprites and sounds (pure standard library)."""

import math
import os
import struct
import wave
import zlib


def create_png_rgba(width: int, height: int, pixels: list) -> bytes:
    """
    Creates a valid RGBA PNG byte stream.
    pixels is a list of height rows, each row being a list of (r, g, b, a) tuples.
    """
    raw_bytes = bytearray()
    for y in range(height):
        raw_bytes.append(0)  # filter type 0 (None)
        for x in range(width):
            r, g, b, a = pixels[y][x]
            raw_bytes.extend((r, g, b, a))

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)
    idat = chunk(b"IDAT", zlib.compress(bytes(raw_bytes), 9))
    iend = chunk(b"IEND", b"")

    return header + ihdr + idat + iend


def generate_slime_pixels(state: str, width: int = 32, height: int = 32) -> list:
    """Draws cute pixel-art slime sprites for each state."""
    # Blank transparent background
    grid = [[(0, 0, 0, 0) for _ in range(width)] for _ in range(height)]

    # Colors
    C_OUTLINE = (28, 66, 42, 255)
    C_BASE = (76, 209, 55, 255)
    C_HIGHLIGHT = (140, 245, 120, 255)
    C_SHADOW = (40, 150, 45, 255)
    C_EYE = (20, 20, 20, 255)
    C_BLUSH = (255, 120, 150, 180)
    C_WHITE = (255, 255, 255, 255)
    C_ZZZ = (60, 140, 255, 230)

    center_x = 16
    center_y = 20

    if state == "idle":
        rx, ry = 11, 9
        center_y = 21
    elif state in ("walk_left", "walk_right"):
        rx, ry = 10, 10
        center_y = 19
    elif state == "sit":
        rx, ry = 13, 7
        center_y = 24
    elif state == "sleep":
        rx, ry = 13, 7
        center_y = 24
    elif state == "dragged":
        rx, ry = 7, 13
        center_y = 16
    elif state == "fall":
        rx, ry = 9, 11
        center_y = 15
    else:
        rx, ry = 11, 9

    # Draw body
    for y in range(height):
        for x in range(width):
            dx = (x - center_x) / rx
            dy = (y - center_y) / ry
            dist = dx * dx + dy * dy
            if dist <= 1.0:
                if dist > 0.80:
                    grid[y][x] = C_OUTLINE
                elif dy < -0.3 and dx < -0.1:
                    grid[y][x] = C_HIGHLIGHT
                elif dy > 0.3:
                    grid[y][x] = C_SHADOW
                else:
                    grid[y][x] = C_BASE

    # Eyes & Expressions
    if state == "sleep":
        # Closed smiling eyes
        for dx in (-4, -3, -2, 2, 3, 4):
            grid[center_y - 1][center_x + dx] = C_EYE
        grid[center_y - 2][center_x - 3] = C_EYE
        grid[center_y - 2][center_x + 3] = C_EYE
        # Zzz floating
        grid[6][23] = C_ZZZ
        grid[6][24] = C_ZZZ
        grid[7][23] = C_ZZZ
        grid[8][22] = C_ZZZ
        grid[9][22] = C_ZZZ
        grid[9][23] = C_ZZZ
    elif state == "dragged":
        # Wide surprised eyes
        for ey in (-3, -2, -1):
            grid[center_y + ey][center_x - 3] = C_EYE
            grid[center_y + ey][center_x + 3] = C_EYE
        # Open mouth 'o'
        grid[center_y + 2][center_x] = C_EYE
    elif state == "fall":
        # Panicked eyes
        grid[center_y - 2][center_x - 3] = C_EYE
        grid[center_y - 1][center_x - 3] = C_EYE
        grid[center_y - 2][center_x + 3] = C_EYE
        grid[center_y - 1][center_x + 3] = C_EYE
        # Wind lines above
        grid[3][center_x - 4] = (200, 230, 255, 180)
        grid[4][center_x - 4] = (200, 230, 255, 180)
        grid[2][center_x + 4] = (200, 230, 255, 180)
        grid[3][center_x + 4] = (200, 230, 255, 180)
    else:
        # Standard cute eyes & blush
        eye_y = center_y - 1
        eye_offset = -1 if state == "walk_left" else (1 if state == "walk_right" else 0)

        # Left eye
        grid[eye_y][center_x - 4 + eye_offset] = C_EYE
        grid[eye_y + 1][center_x - 4 + eye_offset] = C_EYE
        grid[eye_y][center_x - 4 + eye_offset] = C_WHITE

        # Right eye
        grid[eye_y][center_x + 3 + eye_offset] = C_EYE
        grid[eye_y + 1][center_x + 3 + eye_offset] = C_EYE
        grid[eye_y][center_x + 3 + eye_offset] = C_WHITE

        # Cute pink blush cheeks
        grid[eye_y + 2][center_x - 6 + eye_offset] = C_BLUSH
        grid[eye_y + 2][center_x + 5 + eye_offset] = C_BLUSH

    return grid


def create_wav_sound(filename: str, sound_type: str = "click") -> None:
    """Generates pure synthesis WAV sound effects."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    sample_rate = 44100

    if sound_type == "click":
        # Short cheerful pop (0.08 sec)
        duration = 0.08
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = float(i) / sample_rate
            freq = 600.0 + (1 - (t / duration)) * 400.0  # pitch sweep 1000 -> 600 Hz
            env = math.exp(-25.0 * t)
            val = int(32767.0 * 0.4 * env * math.sin(2.0 * math.pi * freq * t))
            samples.append(struct.pack("<h", max(-32768, min(32767, val))))
    else:
        # Wake / chime sound (0.15 sec)
        duration = 0.15
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = float(i) / sample_rate
            freq = 523.25 if t < 0.07 else 659.25  # C5 then E5 chime
            env = math.exp(-15.0 * (t % 0.075))
            val = int(32767.0 * 0.35 * env * math.sin(2.0 * math.pi * freq * t))
            samples.append(struct.pack("<h", max(-32768, min(32767, val))))

    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(samples))


def ensure_default_assets(skin_dir: str) -> None:
    """Verifies that all required sprite PNGs and audio WAVs exist, generating them if missing."""
    sprites_dir = os.path.join(skin_dir, "sprites")
    sounds_dir = os.path.join(skin_dir, "sounds")
    os.makedirs(sprites_dir, exist_ok=True)
    os.makedirs(sounds_dir, exist_ok=True)

    states = ["idle", "walk_left", "walk_right", "sit", "sleep", "dragged", "fall"]
    for state in states:
        sprite_path = os.path.join(sprites_dir, f"{state}.png")
        if not os.path.exists(sprite_path):
            pixels = generate_slime_pixels(state)
            png_bytes = create_png_rgba(32, 32, pixels)
            with open(sprite_path, "wb") as f:
                f.write(png_bytes)

    click_wav = os.path.join(sounds_dir, "click.wav")
    if not os.path.exists(click_wav):
        create_wav_sound(click_wav, "click")

    wake_wav = os.path.join(sounds_dir, "wake.wav")
    if not os.path.exists(wake_wav):
        create_wav_sound(wake_wav, "wake")
