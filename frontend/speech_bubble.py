"""Modern, sleek floating dialogue box widget for Display Buddy.
Features:
- True dynamic sizing: expands or contracts naturally based on the text inside.
- Zero geometry / SetWindowPos warnings on Windows (eliminates Unable to set geometry on high-DPI displays).
- Full screen boundary clamping (never goes off-screen on left, right, top, or taskbar).
- Auto-flip below companion if near top of the monitor.
- Dynamic pointer tail tracking companion anchor even when clamped.
- Dark glassmorphism acrylic styling with smooth multi-layer drop shadow painted directly.
- Circular sticker avatar badge with glowing accent border.
- Configurable 1-2 letter person initials badge located directly beneath the avatar photo.
- Clean text presentation with high-legibility Segoe UI typography.
"""

import os
from typing import Optional
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, QRect
from PyQt6.QtGui import (
    QFont, QFontMetrics, QPixmap, QPainter, QPainterPath, QColor, QPen, 
    QGuiApplication
)
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame
)


class ModernBubbleCard(QFrame):
    """Custom-painted speech bubble card with smooth acrylic glass, multi-layer shadow, and dynamic tail."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1, 1)
        self.accent_color = QColor(244, 63, 94)  # Rose default
        self.tail_x = 100.0
        self.tail_pointing_down = True
        self.tail_w = 14.0
        self.tail_h = 9.0

    def set_tail(self, tail_x: float, tail_pointing_down: bool, accent_hex: str) -> None:
        self.tail_x = tail_x
        self.tail_pointing_down = tail_pointing_down
        self.accent_color = QColor(accent_hex)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        w = self.width()
        h = self.height()

        # Margins inside the card to allow room for shadow and tail
        shadow_pad = 5.0
        top_offset = shadow_pad + (self.tail_h if not self.tail_pointing_down else 0.0)
        bottom_offset = shadow_pad + (self.tail_h if self.tail_pointing_down else 0.0)

        card_x = shadow_pad
        card_y = top_offset
        card_w = w - (shadow_pad * 2.0)
        card_h = h - top_offset - bottom_offset

        # 1. Main Card Path
        path = QPainterPath()
        path.addRoundedRect(float(card_x), float(card_y), float(card_w), float(card_h), 12.0, 12.0)

        # 2. Dynamic Tail Pointer Path
        tail_path = QPainterPath()
        clamped_tail_x = max(card_x + 16.0, min(card_x + card_w - 16.0, self.tail_x))

        if self.tail_pointing_down:
            tip_y = card_y + card_h + self.tail_h
            base_y = card_y + card_h
            tail_path.moveTo(clamped_tail_x - self.tail_w / 2.0, base_y - 1.0)
            tail_path.lineTo(clamped_tail_x, tip_y)
            tail_path.lineTo(clamped_tail_x + self.tail_w / 2.0, base_y - 1.0)
            tail_path.closeSubpath()
        else:
            tip_y = card_y - self.tail_h
            base_y = card_y
            tail_path.moveTo(clamped_tail_x - self.tail_w / 2.0, base_y + 1.0)
            tail_path.lineTo(clamped_tail_x, tip_y)
            tail_path.lineTo(clamped_tail_x + self.tail_w / 2.0, base_y + 1.0)
            tail_path.closeSubpath()

        full_bubble = path.united(tail_path)

        # 3. Native Dual-Pass Soft Drop Shadow
        p.setPen(Qt.PenStyle.NoPen)
        for offset_y, alpha in [(3.0, 30), (1.5, 55)]:
            shadow_p = QPainterPath(full_bubble)
            shadow_p.translate(0.0, offset_y)
            p.fillPath(shadow_p, QColor(0, 0, 0, alpha))

        # 4. Deep Dark Acrylic Background (Obsidian Slate)
        p.fillPath(full_bubble, QColor(15, 23, 42, 246))

        # 5. Sleek Glowing Accent Border
        p.setPen(QPen(self.accent_color, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(full_bubble)

        p.end()


class SpeechBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMinimumSize(1, 1)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # Custom-painted modern card
        self.card = ModernBubbleCard(self)
        self.card.setMinimumSize(1, 1)
        self.card_layout = QHBoxLayout(self.card)
        self.card_layout.setContentsMargins(12, 10, 14, 18)
        self.card_layout.setSpacing(10)

        # Avatar Column (Circular avatar + 1-2 letter person initials badge directly below)
        self.avatar_col = QWidget(self.card)
        self.avatar_col_layout = QVBoxLayout(self.avatar_col)
        self.avatar_col_layout.setContentsMargins(0, 0, 0, 0)
        self.avatar_col_layout.setSpacing(3)
        self.avatar_col_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.avatar_label = QLabel(self.avatar_col)
        self.avatar_label.setFixedSize(36, 36)
        self.avatar_label.setScaledContents(True)
        self.avatar_col_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Small initials badge below photo (1 or 2 letters showing the person's name)
        self.initials_badge = QLabel(self.avatar_col)
        self.initials_badge.setFixedSize(26, 16)
        self.initials_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.initials_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.initials_badge.hide()
        self.avatar_col_layout.addWidget(self.initials_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        self.card_layout.addWidget(self.avatar_col, alignment=Qt.AlignmentFlag.AlignTop)

        # Text label (clean, word-wrapped, no extra containers needed!)
        self.label = QLabel(self.card)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.label.setStyleSheet("color: #f8fafc; background: transparent;")
        self.card_layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.root_layout.addWidget(self.card)

        # Dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.hide)

        # Dynamic size caches
        self.current_bubble_w: int = 150
        self.current_bubble_h: int = 68

    def _make_circular_avatar(self, pixmap: QPixmap, accent_hex: str, size: int = 36) -> QPixmap:
        """Renders avatar inside a circular ring with glowing accent border and comfortable framing."""
        target = QPixmap(size, size)
        target.fill(Qt.GlobalColor.transparent)
        p = QPainter(target)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        center = QPointF(size / 2.0, size / 2.0)
        radius = (size - 3.0) / 2.0

        # 1. Dark circular backdrop matching obsidian card
        bg_clip = QPainterPath()
        bg_clip.addEllipse(center, radius, radius)
        p.fillPath(bg_clip, QColor(15, 23, 42, 245))

        # 2. Scale avatar with breathing room (~78% of size) so head, hair and chin fit completely
        inner_size = int(size * 0.78)
        scaled = pixmap.scaled(
            inner_size, inner_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # 3. Clip to circular frame and draw centered
        p.setClipPath(bg_clip)
        draw_x = int((size - scaled.width()) / 2.0)
        draw_y = int((size - scaled.height()) / 2.0)
        p.drawPixmap(draw_x, draw_y, scaled)

        # 4. Draw glowing circular border ring on top
        p.setClipping(False)
        accent = QColor(accent_hex)
        p.setPen(QPen(accent, 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(center, radius, radius)
        p.end()
        return target

    def show_speech(
        self,
        text: str,
        anchor_x: int,
        anchor_y: int,
        duration_ms: int = 4500,
        avatar_path: Optional[str] = None,
        border_color: str = "#f43f5e",
        companion_height: int = 112,
        initials: Optional[str] = None
    ) -> None:
        """Displays text with dynamic sizing, boundary clamping, and dynamic pointer tail."""
        clean_text = text.strip()
        self.label.setText(clean_text)

        # Configurable 1-2 letter initials badge below photo
        if initials is None:
            if "girl" in str(avatar_path).lower() or border_color in ("#ec4899", "#db2777"):
                initials = "G"
            else:
                initials = "B"

        display_initials = str(initials).strip()[:2].upper()
        if display_initials:
            self.initials_badge.setText(display_initials)
            if "girl" in str(avatar_path).lower() or border_color in ("#ec4899", "#db2777"):
                self.initials_badge.setStyleSheet("""
                    QLabel {
                        background-color: rgba(236, 72, 153, 0.25);
                        color: #f472b6;
                        border: 1px solid rgba(236, 72, 153, 0.65);
                        border-radius: 4px;
                        font-size: 9px;
                        font-weight: 700;
                    }
                """)
            else:
                self.initials_badge.setStyleSheet("""
                    QLabel {
                        background-color: rgba(244, 63, 94, 0.25);
                        color: #fda4af;
                        border: 1px solid rgba(244, 63, 94, 0.65);
                        border-radius: 4px;
                        font-size: 9px;
                        font-weight: 700;
                    }
                """)
            self.initials_badge.show()
        else:
            self.initials_badge.hide()

        # Avatar Icon
        has_avatar = False
        if avatar_path and os.path.exists(avatar_path):
            pix = QPixmap(avatar_path)
            if not pix.isNull():
                circ = self._make_circular_avatar(pix, border_color, 36)
                self.avatar_label.setPixmap(circ)
                self.avatar_label.show()
                has_avatar = True
            else:
                self.avatar_label.hide()
        else:
            self.avatar_label.hide()

        self.avatar_col.setVisible(has_avatar or bool(display_initials))

        # --- Dynamic Text Bounding Measurement ---
        fm = QFontMetrics(self.label.font())
        raw_adv = fm.horizontalAdvance(clean_text)

        max_text_w = 210
        if "\n" not in clean_text and raw_adv <= max_text_w:
            target_text_w = raw_adv + 8
            target_text_h = fm.height() + 2
        else:
            if raw_adv < 340 and "\n" not in clean_text:
                wrap_w = min(max_text_w, int(raw_adv / 2) + 24)
            else:
                wrap_w = max_text_w
            rect = fm.boundingRect(QRect(0, 0, wrap_w, 2000), Qt.TextFlag.TextWordWrap, clean_text)
            target_text_w = rect.width() + 10
            target_text_h = rect.height() + 4

        self.label.setFixedSize(target_text_w, target_text_h)

        # Bubble Card Dimensions
        avatar_w = 36 if (has_avatar or display_initials) else 0
        spacing = 10 if avatar_w > 0 else 0
        h_padding = 12 + 14  # left + right
        bubble_w = max(110, h_padding + avatar_w + spacing + target_text_w)

        avatar_col_h = (36 + 3 + 16) if (has_avatar and display_initials) else (36 if has_avatar else 0)
        content_h = max(avatar_col_h, target_text_h)
        v_padding = 10 + 18  # top + bottom including tail and shadow
        bubble_h = max(58, content_h + v_padding)

        self.current_bubble_w = bubble_w
        self.current_bubble_h = bubble_h
        self.current_border_color = border_color

        self.setFixedSize(bubble_w, bubble_h)
        self.reposition(anchor_x, anchor_y, companion_height)

        self.show()
        self.raise_()

        # Windows Kernel Topmost
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
        except Exception:
            pass

        self.dismiss_timer.start(duration_ms)

    def reposition(self, anchor_x: int, anchor_y: int, companion_height: int = 112) -> None:
        """Dynamically tracks companion movement in real time with boundary clamping."""
        actual_w = getattr(self, "current_bubble_w", max(self.width(), 110))
        actual_h = getattr(self, "current_bubble_h", max(self.height(), 58))

        screen = QGuiApplication.screenAt(QPoint(anchor_x, anchor_y))
        if not screen:
            screen = QGuiApplication.primaryScreen()

        geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        margin = 12
        screen_left = geo.x()
        screen_top = geo.y()
        screen_right = geo.x() + geo.width()
        screen_bottom = geo.y() + geo.height()

        # 1. Horizontal Clamping
        min_x = screen_left + margin
        max_x = max(min_x, screen_right - actual_w - margin)
        desired_x = int(anchor_x - (actual_w / 2))
        pos_x = max(min_x, min(max_x, desired_x))

        # 2. Vertical Positioning & Auto-Flipping
        tail_pointing_down = True
        # Character hair top is located ~18px below the window top anchor_y.
        # Desired bubble Y places the tail pointer tip just 4-5px directly above the hair!
        desired_y = int(anchor_y - actual_h + 18)

        if desired_y < screen_top + margin:
            desired_y = int(anchor_y + companion_height)
            tail_pointing_down = False

        min_y = screen_top + margin
        max_y = max(min_y, screen_bottom - actual_h - margin)
        pos_y = max(min_y, min(max_y, desired_y))

        # 3. Dynamic Tail Pointer Offset
        rel_anchor_x = float(anchor_x - pos_x)
        accent = getattr(self, "current_border_color", "#f43f5e")
        self.card.set_tail(rel_anchor_x, tail_pointing_down, accent)

        # Update card layout margins to give room for tail above vs below
        if tail_pointing_down:
            self.card_layout.setContentsMargins(12, 10, 14, 18)
        else:
            self.card_layout.setContentsMargins(12, 18, 14, 10)

        self.setGeometry(pos_x, pos_y, actual_w, actual_h)
