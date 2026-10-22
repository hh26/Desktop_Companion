"""High-Definition vector sprite renderer with anti-aliasing and crystal clarity."""

from typing import Dict, Tuple
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QRadialGradient, 
    QPen, QBrush, QFont, QPainterPath
)
from backend.skin_loader import Skin
from backend.state_machine import State, Direction


class SpriteRenderer:
    def __init__(self, skin: Skin):
        self.skin = skin
        # Native HD resolution (256x256 internal buffer for super-sharp retina display)
        self.hd_size = 256
        self.target_width = 112
        self.target_height = 112

        self._pixmaps: Dict[Tuple[str, Direction], QPixmap] = {}
        self._images: Dict[Tuple[str, Direction], QImage] = {}

        self.load_all_sprites()

    def create_hd_sprite(self, state_name: str, direction: Direction) -> QPixmap:
        """Procedurally draws a gorgeous, crisp, vector-grade companion slime."""
        pixmap = QPixmap(self.hd_size, self.hd_size)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        cx = self.hd_size / 2.0
        cy = self.hd_size * 0.58
        rx = self.hd_size * 0.38
        ry = self.hd_size * 0.32

        # State-based squish and stretch
        if state_name in ("walk_left", "walk_right", "walking"):
            cy -= 8.0
            rx *= 0.95
            ry *= 1.05
        elif state_name in ("sit", "sitting"):
            cy += 10.0
            rx *= 1.15
            ry *= 0.85
        elif state_name in ("sleep", "sleeping"):
            cy += 12.0
            rx *= 1.18
            ry *= 0.80
        elif state_name in ("dragged", "drag"):
            cy -= 10.0
            rx *= 0.80
            ry *= 1.25
        elif state_name in ("fall", "falling"):
            rx *= 0.90
            ry *= 1.10

        # 1. Soft Ambient Drop Shadow under body
        shadow_path = QPainterPath()
        shadow_path.addEllipse(QPointF(cx, cy + ry * 0.85), rx * 0.8, ry * 0.25)
        p.fillPath(shadow_path, QColor(0, 0, 0, 40))

        # 2. Main Slime Body with Vibrant Lush Radial Gradient
        body_grad = QRadialGradient(cx - rx * 0.25, cy - ry * 0.35, rx * 1.3)
        body_grad.setColorAt(0.0, QColor(140, 245, 120))  # Bright lime highlight
        body_grad.setColorAt(0.4, QColor(76, 209, 55))    # Vivid emerald body
        body_grad.setColorAt(0.85, QColor(40, 160, 45))   # Deep shade
        body_grad.setColorAt(1.0, QColor(25, 95, 30))     # Dark rim

        body_path = QPainterPath()
        body_path.addEllipse(QPointF(cx, cy), rx, ry)
        p.setPen(QPen(QColor(18, 65, 25), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(body_grad)
        p.drawPath(body_path)

        # 3. Glossy Glass Highlights
        highlight_grad = QRadialGradient(cx - rx * 0.35, cy - ry * 0.45, rx * 0.5)
        highlight_grad.setColorAt(0.0, QColor(255, 255, 255, 220))
        highlight_grad.setColorAt(0.5, QColor(180, 255, 160, 140))
        highlight_grad.setColorAt(1.0, QColor(140, 245, 120, 0))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(highlight_grad)
        p.drawEllipse(QPointF(cx - rx * 0.32, cy - ry * 0.42), rx * 0.38, ry * 0.24)

        # Bottom Sub-surface Glow
        glow_grad = QRadialGradient(cx + rx * 0.2, cy + ry * 0.45, rx * 0.6)
        glow_grad.setColorAt(0.0, QColor(120, 255, 150, 100))
        glow_grad.setColorAt(1.0, QColor(76, 209, 55, 0))
        p.setBrush(glow_grad)
        p.drawEllipse(QPointF(cx + rx * 0.15, cy + ry * 0.35), rx * 0.45, ry * 0.25)

        # 4. Expressions & Eyes
        eye_dir_offset = -8.0 if direction == Direction.LEFT else 8.0
        eye_y = cy - ry * 0.10

        if state_name in ("sleep", "sleeping"):
            # Happy closed sleeping arches
            p.setPen(QPen(QColor(20, 30, 20), 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(int(cx - 38 + eye_dir_offset), int(eye_y - 8), 22, 16, 20 * 16, 140 * 16)
            p.drawArc(int(cx + 16 + eye_dir_offset), int(eye_y - 8), 22, 16, 20 * 16, 140 * 16)

            # Floating Zzz
            p.setPen(QColor(56, 189, 248))
            p.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            p.drawText(int(cx + 40), int(cy - 40), "Z")
            p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            p.drawText(int(cx + 56), int(cy - 56), "z")
        elif state_name in ("dragged", "drag"):
            # Wide surprised eyes
            p.setPen(QPen(QColor(18, 65, 25), 2.0))
            p.setBrush(QColor(20, 25, 20))
            p.drawEllipse(QPointF(cx - 24, eye_y), 10.0, 14.0)
            p.drawEllipse(QPointF(cx + 24, eye_y), 10.0, 14.0)

            # White reflections
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QPointF(cx - 26, eye_y - 4), 4.0, 5.0)
            p.drawEllipse(QPointF(cx + 22, eye_y - 4), 4.0, 5.0)

            # Open surprised mouth 'o'
            p.setPen(QPen(QColor(20, 30, 20), 3.0))
            p.setBrush(QColor(180, 50, 60))
            p.drawEllipse(QPointF(cx, cy + ry * 0.25), 6.0, 8.0)
        elif state_name in ("fall", "falling"):
            # Panicked eyes
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(20, 25, 20))
            p.drawEllipse(QPointF(cx - 24, eye_y), 9.0, 13.0)
            p.drawEllipse(QPointF(cx + 24, eye_y), 9.0, 13.0)
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QPointF(cx - 24, eye_y - 4), 3.5, 4.5)
            p.drawEllipse(QPointF(cx + 24, eye_y - 4), 3.5, 4.5)

            # Wind streaks
            p.setPen(QPen(QColor(200, 240, 255, 180), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(int(cx - 30), 20, int(cx - 30), 45)
            p.drawLine(int(cx + 30), 15, int(cx + 30), 40)
        else:
            # Cheerful sparkling Anime Eyes
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(20, 25, 20))
            p.drawEllipse(QPointF(cx - 26 + eye_dir_offset, eye_y), 9.0, 13.0)
            p.drawEllipse(QPointF(cx + 26 + eye_dir_offset, eye_y), 9.0, 13.0)

            # Primary White Glint
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QPointF(cx - 28 + eye_dir_offset, eye_y - 4), 4.0, 5.5)
            p.drawEllipse(QPointF(cx + 24 + eye_dir_offset, eye_y - 4), 4.0, 5.5)

            # Secondary Small Glint
            p.drawEllipse(QPointF(cx - 23 + eye_dir_offset, eye_y + 4), 2.2, 2.2)
            p.drawEllipse(QPointF(cx + 29 + eye_dir_offset, eye_y + 4), 2.2, 2.2)

            # Smiling mouth
            p.setPen(QPen(QColor(20, 30, 20), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(int(cx - 8 + eye_dir_offset), int(cy + 2), 16, 12, -30 * 16, -120 * 16)

        # Rosy Cute Blush
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 120, 150, 160))
        p.drawEllipse(QPointF(cx - 42 + eye_dir_offset, eye_y + 12), 11.0, 6.5)
        p.drawEllipse(QPointF(cx + 42 + eye_dir_offset, eye_y + 12), 11.0, 6.5)

        p.end()
        return pixmap

    def load_all_sprites(self) -> None:
        """Pre-renders HD vector sprites for all states and directions."""
        states = ["idle", "walk_left", "walk_right", "walking", "sit", "sitting", "sleep", "sleeping", "dragged", "fall", "falling"]
        for s in states:
            # Generate sharp HD pixmap
            pixmap_right = self.create_hd_sprite(s, Direction.RIGHT)
            self._pixmaps[(s, Direction.RIGHT)] = pixmap_right
            self._images[(s, Direction.RIGHT)] = pixmap_right.toImage()

            pixmap_left = self.create_hd_sprite(s, Direction.LEFT)
            self._pixmaps[(s, Direction.LEFT)] = pixmap_left
            self._images[(s, Direction.LEFT)] = pixmap_left.toImage()

    def get_pixmap(self, state: State, direction: Direction) -> QPixmap:
        """Retrieves high-resolution vector QPixmap for current state and direction."""
        key = (state.value, direction)
        if key in self._pixmaps:
            return self._pixmaps[key]

        fallback_key = (state.value, Direction.RIGHT)
        if fallback_key in self._pixmaps:
            return self._pixmaps[fallback_key]

        return self._pixmaps.get(("idle", Direction.RIGHT), QPixmap())

    def is_opaque_at(self, state: State, direction: Direction, x: int, y: int) -> bool:
        """Samples alpha channel for per-pixel click-through hit testing."""
        key = (state.value, direction)
        img = self._images.get(key) or self._images.get((state.value, Direction.RIGHT))
        if not img or x < 0 or y < 0:
            return False

        # Scale coordinates from window size (112) to HD buffer (256)
        scale_factor = self.hd_size / float(self.target_width)
        sample_x = int(x * scale_factor)
        sample_y = int(y * scale_factor)

        if 0 <= sample_x < img.width() and 0 <= sample_y < img.height():
            return img.pixelColor(sample_x, sample_y).alpha() > 25

        return False
