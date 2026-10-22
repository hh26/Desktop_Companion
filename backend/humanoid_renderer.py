"""Procedural Humanoid Character Rigging & Animation Engine for Display Buddy.
Features custom character models tailored directly to user reference photos:
- 'boy_main': Primary companion (quiff hairstyle, smiling eyes, beard stubble, burgundy button-up, sunglasses).
- 'girl_friend': Hugging friend (voluminous curly hair, black glasses, anime star eyes, black t-shirt, camo backpack).
"""

import os
import math
from typing import Dict, Tuple, Optional, Any
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QFont, QPainterPath
)
from backend.state_machine import State, Direction
from backend.path_utils import get_skins_dir


# Character Outfit Color Palettes
BOY_PALETTES = {
    "default": {
        "hair": QColor(38, 28, 24),           # Dark espresso brown/black
        "hair_dark": QColor(22, 16, 14),
        "hair_highlight": QColor(72, 54, 46),
        "skin": QColor(255, 224, 196),        # Peach skin
        "skin_shadow": QColor(238, 198, 168),
        "shirt": QColor(146, 30, 48),         # Rich burgundy / maroon
        "shirt_collar": QColor(112, 18, 32),
        "pants": QColor(42, 52, 68),          # Slate denim
        "shoes": QColor(250, 250, 252),       # White sneakers
        "shoe_sole": QColor(24, 28, 36),
        "sunglasses": QColor(18, 18, 22),
        "stubble": QColor(64, 46, 38, 180)
    },
    "emerald": {
        "hair": QColor(38, 28, 24),
        "hair_dark": QColor(22, 16, 14),
        "hair_highlight": QColor(72, 54, 46),
        "skin": QColor(255, 224, 196),
        "skin_shadow": QColor(238, 198, 168),
        "shirt": QColor(16, 185, 129),        # Emerald green
        "shirt_collar": QColor(5, 150, 105),
        "pants": QColor(30, 41, 59),
        "shoes": QColor(250, 250, 252),
        "shoe_sole": QColor(15, 23, 42),
        "sunglasses": QColor(18, 18, 22),
        "stubble": QColor(64, 46, 38, 180)
    },
    "midnight": {
        "hair": QColor(38, 28, 24),
        "hair_dark": QColor(22, 16, 14),
        "hair_highlight": QColor(72, 54, 46),
        "skin": QColor(255, 224, 196),
        "skin_shadow": QColor(238, 198, 168),
        "shirt": QColor(37, 99, 235),         # Royal blue
        "shirt_collar": QColor(29, 78, 216),
        "pants": QColor(15, 23, 42),
        "shoes": QColor(250, 250, 252),
        "shoe_sole": QColor(30, 41, 59),
        "sunglasses": QColor(18, 18, 22),
        "stubble": QColor(64, 46, 38, 180)
    },
    "sunset": {
        "hair": QColor(38, 28, 24),
        "hair_dark": QColor(22, 16, 14),
        "hair_highlight": QColor(72, 54, 46),
        "skin": QColor(255, 224, 196),
        "skin_shadow": QColor(238, 198, 168),
        "shirt": QColor(249, 115, 22),        # Coral orange
        "shirt_collar": QColor(217, 70, 239),
        "pants": QColor(30, 41, 59),
        "shoes": QColor(250, 250, 252),
        "shoe_sole": QColor(234, 88, 12),
        "sunglasses": QColor(18, 18, 22),
        "stubble": QColor(64, 46, 38, 180)
    }
}

GIRL_PALETTES = {
    "default": {
        "hair": QColor(36, 26, 24),           # Dark curly brown/black
        "hair_dark": QColor(22, 16, 14),
        "hair_highlight": QColor(68, 50, 44),
        "skin": QColor(224, 172, 134),        # Warm caramel / tan
        "skin_shadow": QColor(200, 150, 114),
        "shirt": QColor(24, 24, 27),          # Black t-shirt
        "pants": QColor(48, 58, 74),          # Denim
        "shoes": QColor(248, 248, 250),       # White sneakers
        "shoe_sole": QColor(20, 20, 24),
        "glasses": QColor(20, 20, 20),        # Black spectacles
        "backpack": QColor(118, 114, 92),     # Camo backpack
        "camo_spot": QColor(72, 78, 60),
        "earring": QColor(255, 255, 255)
    },
    "lavender": {
        "hair": QColor(36, 26, 24),
        "hair_dark": QColor(22, 16, 14),
        "hair_highlight": QColor(68, 50, 44),
        "skin": QColor(224, 172, 134),
        "skin_shadow": QColor(200, 150, 114),
        "shirt": QColor(168, 85, 247),        # Purple t-shirt
        "pants": QColor(55, 65, 81),
        "shoes": QColor(255, 255, 255),
        "shoe_sole": QColor(219, 39, 119),
        "glasses": QColor(20, 20, 20),
        "backpack": QColor(118, 114, 92),
        "camo_spot": QColor(72, 78, 60),
        "earring": QColor(255, 255, 255)
    }
}


class HumanoidRenderer:
    def __init__(self, character_type: str = "boy_main", palette_name: str = "default"):
        self.hd_size = 256
        self.target_width = 112
        self.target_height = 112

        self.character_type = character_type
        self.palette_name = palette_name

        if self.character_type == "girl_friend":
            self.palettes = GIRL_PALETTES
        else:
            self.palettes = BOY_PALETTES

        self.palette = self.palettes.get(palette_name, self.palettes["default"])
        self.render_mode: str = "unified"

        # Load authentic sticker photo face cutouts
        skins_dir = get_skins_dir()
        self.boy_head_path = os.path.join(skins_dir, "boy_head.png")
        if not os.path.exists(self.boy_head_path):
            self.boy_head_path = os.path.join(skins_dir, "avatar_boy.png")
        self.girl_head_path = os.path.join(skins_dir, "girl_head.png")
        if not os.path.exists(self.girl_head_path):
            self.girl_head_path = os.path.join(skins_dir, "avatar_girl.png")

        self.boy_head: Optional[QPixmap] = QPixmap(self.boy_head_path) if os.path.exists(self.boy_head_path) else None
        self.girl_head: Optional[QPixmap] = QPixmap(self.girl_head_path) if os.path.exists(self.girl_head_path) else None

        # Cache of pre-rendered frames by state and direction
        self._pixmaps: Dict[Tuple[str, Direction], QPixmap] = {}
        self._images: Dict[Tuple[str, Direction], QImage] = {}

        self.load_all_sprites()

    def toggle_render_mode(self) -> str:
        """Unified rendering mode combining vector limbs with photo faces."""
        return self.render_mode

    def set_palette(self, palette_name: str) -> None:
        """Switches the character outfit palette and re-renders all frames."""
        if palette_name in self.palettes:
            self.palette_name = palette_name
            self.palette = self.palettes[palette_name]
            self.load_all_sprites()

    def cycle_palette(self) -> str:
        """Cycles to the next available outfit palette."""
        names = list(self.palettes.keys())
        idx = names.index(self.palette_name) if self.palette_name in names else 0
        next_name = names[(idx + 1) % len(names)]
        self.set_palette(next_name)
        return next_name

    def draw_boy(
        self,
        p: QPainter,
        state_name: str,
        direction: Direction,
        walk_phase: float = 0.0,
        is_blinking: bool = False
    ) -> None:
        """Draws the Boy companion (left image: maroon shirt, quiff, sunglasses, smile)."""
        pal = self.palette
        cx = self.hd_size / 2.0
        cy = 138.0

        p.save()
        if direction == Direction.LEFT:
            p.translate(self.hd_size, 0)
            p.scale(-1, 1)

        body_y = cy
        left_leg_angle = 0.0
        right_leg_angle = 0.0
        left_arm_angle = 0.0
        right_arm_angle = 0.0
        head_tilt = 0.0

        body_tilt = 0.0
        if state_name in ("walk_left", "walk_right", "walking"):
            bounce = abs(math.sin(walk_phase * 2.0)) * 6.0
            body_y -= bounce
            left_leg_angle = math.sin(walk_phase) * 32.0
            right_leg_angle = -math.sin(walk_phase) * 32.0
            left_arm_angle = -math.sin(walk_phase) * 35.0
            right_arm_angle = math.sin(walk_phase) * 35.0
            head_tilt = math.sin(walk_phase) * 2.0
        elif state_name in ("sit", "sitting"):
            body_y += 18.0
            left_leg_angle = 75.0
            right_leg_angle = 75.0
            left_arm_angle = 35.0
            right_arm_angle = 35.0
        elif state_name in ("sleep", "sleeping"):
            body_y += 24.0
            left_leg_angle = 85.0
            right_leg_angle = 85.0
            left_arm_angle = 60.0
            right_arm_angle = 60.0
            head_tilt = 12.0
        elif state_name in ("dragged", "drag"):
            body_y -= 10.0
            left_leg_angle = 15.0
            right_leg_angle = -15.0
            left_arm_angle = -135.0
            right_arm_angle = -135.0
        elif state_name in ("fall", "falling"):
            left_arm_angle = -140.0
            right_arm_angle = -140.0
            left_leg_angle = 20.0
            right_leg_angle = -20.0
        elif state_name in ("hanging", "hang"):
            # Dangling suspended in mid-air! Arms grasping upward, legs kicking/swinging gently
            hang_sway = math.sin(walk_phase) * 7.0
            body_tilt = hang_sway
            head_tilt = hang_sway * 0.4
            body_y -= 8.0
            left_arm_angle = -155.0 + hang_sway * 0.8
            right_arm_angle = -150.0 - hang_sway * 0.8
            left_leg_angle = 14.0 + hang_sway * 1.6
            right_leg_angle = -12.0 - hang_sway * 1.6
        elif state_name in ("kissing", "kiss"):
            # Smooth, gentle cheek kiss cadence
            kiss_cycle = math.sin(walk_phase * 5.5)
            peck = max(0.0, kiss_cycle)
            body_tilt = 7.0 + peck * 1.5
            head_tilt = 12.0 + peck * 2.5
            left_leg_angle = -2.0
            right_leg_angle = 4.0
        elif state_name in ("waiting_kiss",):
            body_tilt = 4.0
            head_tilt = 6.0
            left_leg_angle = -2.0
            right_leg_angle = 3.0
        elif state_name in ("hugging", "hug", "waiting_hug"):
            hug_sway = math.sin(walk_phase * 2.5) * 2.0
            body_tilt = 7.0 + hug_sway
            head_tilt = 11.0 + hug_sway
            left_leg_angle = -4.0
            right_leg_angle = 6.0

        head_cy = body_y - 25.0

        # 1. Ground Shadow (faint and small when hanging high in the air)
        shadow_p = QPainterPath()
        if state_name in ("hanging", "hang"):
            shadow_p.addEllipse(QPointF(cx, 236.0), 20.0, 4.0)
            p.fillPath(shadow_p, QColor(0, 0, 0, 15))
        else:
            shadow_w = 42.0 if state_name not in ("sit", "sitting", "sleep", "sleeping") else 54.0
            shadow_p.addEllipse(QPointF(cx, 236.0), shadow_w, 8.5)
            p.fillPath(shadow_p, QColor(0, 0, 0, 40))

        # Body tilt transform for hug or leaning actions
        if body_tilt != 0.0:
            p.save()
            p.translate(cx, body_y + 36.0)
            p.rotate(body_tilt)
            p.translate(-cx, -(body_y + 36.0))

        # 2. Back Hair (base shadow)
        if not self.boy_head or self.boy_head.isNull():
            back_hair = QPainterPath()
            back_hair.addEllipse(QPointF(cx, head_cy - 12.0), 38.0, 36.0)
            p.fillPath(back_hair, pal["hair_dark"])

        # 3. Legs & Shoes
        hip_y = body_y + 36.0
        leg_len = 34.0
        for is_right, angle in [(False, left_leg_angle), (True, right_leg_angle)]:
            rad = math.radians(angle)
            lx = cx + (9.5 if is_right else -9.5)
            foot_x = lx + math.sin(rad) * leg_len
            foot_y = hip_y + math.cos(rad) * leg_len

            p.setPen(QPen(pal["pants"], 12.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(lx, hip_y), QPointF(foot_x, foot_y))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["shoes"])
            p.drawRoundedRect(int(foot_x - 7.5), int(foot_y - 2.0), 17, 10, 4, 4)
            p.setBrush(pal["shoe_sole"])
            p.drawRoundedRect(int(foot_x - 7.5), int(foot_y + 6.0), 17, 3, 1, 1)

        # 4. Torso (Burgundy Button-Down Shirt)
        torso_w = 40.0
        torso_h = 36.0
        p.setPen(QPen(pal["shirt_collar"], 1.5))
        p.setBrush(pal["shirt"])
        p.drawRoundedRect(int(cx - torso_w / 2.0), int(body_y + 6.0), int(torso_w), int(torso_h), 8, 8)

        # Shirt Placket & Buttons
        p.setPen(QPen(pal["shirt_collar"], 2.0))
        p.drawLine(QPointF(cx, body_y + 14.0), QPointF(cx, body_y + 40.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(250, 250, 250))
        for by in [body_y + 24.0, body_y + 32.0, body_y + 38.0]:
            p.drawEllipse(QPointF(cx, by), 1.6, 1.6)

        # Folded Shirt Collar
        collar_p = QPainterPath()
        collar_p.moveTo(cx - 16.0, body_y + 6.0)
        collar_p.lineTo(cx - 5.0, body_y + 16.0)
        collar_p.lineTo(cx, body_y + 10.0)
        collar_p.lineTo(cx + 5.0, body_y + 16.0)
        collar_p.lineTo(cx + 16.0, body_y + 6.0)
        collar_p.closeSubpath()
        p.fillPath(collar_p, pal["shirt_collar"])

        # Hanging Folded Sunglasses on Collar
        p.setPen(QPen(pal["sunglasses"], 2.0))
        p.setBrush(QColor(16, 16, 20, 240))
        p.drawRoundedRect(int(cx - 5.0), int(body_y + 13.0), 10, 15, 4, 4)
        p.setPen(QPen(QColor(60, 60, 65), 1.8))
        p.drawLine(QPointF(cx - 4.0, body_y + 13.0), QPointF(cx + 4.0, body_y + 13.0))

        # 5. Arms & Hands
        shoulder_y = body_y + 12.0
        arm_len = 26.0

        if state_name in ("kissing", "kiss"):
            # Back Arm (Left): Tenderly rests supporting her lower cheek/shoulder (stable, not shaking!)
            sx_l = cx - 18.0
            elbow_x_l = cx + 8.0
            elbow_y_l = shoulder_y + 12.0
            hand_x_l = cx + 26.0
            hand_y_l = shoulder_y + 8.0
            p.setPen(QPen(pal["shirt"], 9.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_l, shoulder_y), QPointF(elbow_x_l, elbow_y_l))
            p.drawLine(QPointF(elbow_x_l, elbow_y_l), QPointF(hand_x_l, hand_y_l))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            # Gentle open palm
            p.drawEllipse(QPointF(hand_x_l, hand_y_l), 5.5, 5.0)

            # Front Arm (Right): Wrapped gently around her waist / back
            sx_r = cx + 18.0
            elbow_x_r = sx_r + 14.0
            elbow_y_r = shoulder_y + 11.0
            hand_x_r = elbow_x_r + 16.0
            hand_y_r = elbow_y_r + 4.0
            p.setPen(QPen(pal["shirt"], 10.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_r, shoulder_y), QPointF(elbow_x_r, elbow_y_r))
            p.drawLine(QPointF(elbow_x_r, elbow_y_r), QPointF(hand_x_r, hand_y_r))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_r, hand_y_r), 6.0, 6.0)
        elif state_name in ("hugging", "hug", "waiting_hug"):
            # Back Arm (Left): wraps around partner's back/shoulder
            sx_l = cx - 18.0
            elbow_x_l = cx + 8.0
            elbow_y_l = shoulder_y + 4.0
            hand_x_l = cx + 34.0
            hand_y_l = shoulder_y + 8.0
            p.setPen(QPen(pal["shirt"], 10.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_l, shoulder_y), QPointF(elbow_x_l, elbow_y_l))
            p.drawLine(QPointF(elbow_x_l, elbow_y_l), QPointF(hand_x_l, hand_y_l))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_l, hand_y_l), 5.5, 5.5)

            # Front Arm (Right): wraps around partner's waist
            sx_r = cx + 18.0
            elbow_x_r = sx_r + 14.0
            elbow_y_r = shoulder_y + 12.0
            hand_x_r = elbow_x_r + 16.0
            hand_y_r = elbow_y_r + 4.0
            p.setPen(QPen(pal["shirt"], 10.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_r, shoulder_y), QPointF(elbow_x_r, elbow_y_r))
            p.drawLine(QPointF(elbow_x_r, elbow_y_r), QPointF(hand_x_r, hand_y_r))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_r, hand_y_r), 6.0, 6.0)
        else:
            # Left Arm
            rad_l = math.radians(left_arm_angle)
            sx_l = cx - 20.0
            hand_x_l = sx_l + math.sin(rad_l) * arm_len
            hand_y_l = shoulder_y + math.cos(rad_l) * arm_len
            p.setPen(QPen(pal["shirt"], 9.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_l, shoulder_y), QPointF(hand_x_l, hand_y_l))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_l, hand_y_l), 5.5, 5.5)

            # Right Arm (Thumbs-up in idle!)
            sx_r = cx + 20.0
            if state_name in ("idle",) and not is_blinking:
                hand_x_r = sx_r + 10.0
                hand_y_r = shoulder_y + 8.0
                p.setPen(QPen(pal["shirt"], 9.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(sx_r, shoulder_y), QPointF(hand_x_r - 2.0, hand_y_r + 5.0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(pal["skin"])
                p.drawEllipse(QPointF(hand_x_r, hand_y_r), 6.0, 6.0)
                p.setPen(QPen(pal["skin"], 4.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(hand_x_r - 1.0, hand_y_r + 1.0), QPointF(hand_x_r - 1.0, hand_y_r - 9.0))
            else:
                rad_r = math.radians(right_arm_angle)
                hand_x_r = sx_r + math.sin(rad_r) * arm_len
                hand_y_r = shoulder_y + math.cos(rad_r) * arm_len
                p.setPen(QPen(pal["shirt"], 9.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(sx_r, shoulder_y), QPointF(hand_x_r, hand_y_r))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(pal["skin"])
                p.drawEllipse(QPointF(hand_x_r, hand_y_r), 5.5, 5.5)

        # 6. Head, Face & Hair
        head_off_x = 0.0
        if state_name in ("kissing", "kiss"):
            kiss_cycle = math.sin(walk_phase * 5.5)
            head_off_x = max(0.0, kiss_cycle) * 3.5

        p.save()
        p.translate(cx + head_off_x, head_cy)
        p.rotate(head_tilt)

        # Neck
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal["skin_shadow"])
        p.drawRect(-7, 20, 14, 10)

        # Authentic Photo Face Rendering
        if self.boy_head and not self.boy_head.isNull():
            hw = 88.0
            hh = hw * (self.boy_head.height() / float(self.boy_head.width()))
            head_rect = QRectF(-hw / 2.0, 31.0 - hh, hw, hh)
            p.drawPixmap(head_rect.toRect(), self.boy_head)
        else:
            # Procedural Vector Head Fallback
            # Ears
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(-33.0, 3), 6.5, 8.5)
            p.drawEllipse(QPointF(33.0, 3), 6.5, 8.5)
            p.setPen(QPen(pal["skin_shadow"], 1.5))
            p.drawArc(-34, 0, 5, 6, 40 * 16, 180 * 16)
            p.drawArc(29, 0, 5, 6, -40 * 16, -180 * 16)

            # Face Skin Base
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(0, 0), 33.0, 31.0)

            # Eyebrows
            p.setPen(QPen(pal["hair"], 3.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            brow_l = QPainterPath()
            brow_l.moveTo(-24, -13)
            brow_l.quadTo(-16, -18, -8, -14)
            p.drawPath(brow_l)

            brow_r = QPainterPath()
            brow_r.moveTo(8, -14)
            brow_r.quadTo(16, -18, 24, -13)
            p.drawPath(brow_r)

            # Eyes
            eye_y = -3.0
            if state_name in ("sleep", "sleeping"):
                p.setPen(QPen(QColor(32, 24, 20), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(-23, int(eye_y - 4), 16, 12, 20 * 16, 140 * 16)
                p.drawArc(7, int(eye_y - 4), 16, 12, 20 * 16, 140 * 16)
            elif is_blinking:
                p.setPen(QPen(QColor(32, 24, 20), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(-22, eye_y), QPointF(-8, eye_y))
                p.drawLine(QPointF(8, eye_y), QPointF(22, eye_y))
            elif state_name in ("dragged", "drag", "fall", "falling"):
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(30, 24, 20))
                p.drawEllipse(QPointF(-14, eye_y), 7.0, 9.5)
                p.drawEllipse(QPointF(14, eye_y), 7.0, 9.5)
                p.setBrush(QColor(255, 255, 255))
                p.drawEllipse(QPointF(-15, eye_y - 3), 3.0, 3.5)
                p.drawEllipse(QPointF(13, eye_y - 3), 3.0, 3.5)
            else:
                p.setPen(QPen(QColor(32, 24, 20), 3.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(-24, int(eye_y - 8), 18, 14, 25 * 16, 130 * 16)
                p.drawArc(6, int(eye_y - 8), 18, 14, 25 * 16, 130 * 16)

            # Pink Cheek Blush
            p.setPen(QPen(QColor(248, 113, 113, 220), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ox in [-22, -18, -14]:
                p.drawLine(QPointF(ox - 2, eye_y + 8), QPointF(ox + 3, eye_y + 13))
            for ox in [14, 18, 22]:
                p.drawLine(QPointF(ox - 2, eye_y + 8), QPointF(ox + 3, eye_y + 13))

            # Stubble & Mustache
            p.setPen(QPen(pal["stubble"], 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(-5, eye_y + 7.5), QPointF(5, eye_y + 7.5))
            for sx, sy in [(-4, 24), (0, 26), (4, 24), (-2, 22), (2, 22)]:
                p.drawPoint(QPointF(sx, sy))

            # Joyful Wide Smile with Teeth
            mouth_p = QPainterPath()
            mouth_p.moveTo(-11, eye_y + 11)
            mouth_p.quadTo(0, eye_y + 25, 11, eye_y + 11)
            mouth_p.closeSubpath()
            p.setPen(QPen(QColor(40, 24, 20), 2.5))
            p.setBrush(QColor(255, 255, 255))
            p.fillPath(mouth_p, QColor(255, 255, 255))
            p.drawPath(mouth_p)

            # Styled Swept Quiff Hair
            sideburn_l = QPainterPath()
            sideburn_l.moveTo(-33, -8)
            sideburn_l.lineTo(-27, -8)
            sideburn_l.lineTo(-28, 6)
            sideburn_l.lineTo(-33, 4)
            sideburn_l.closeSubpath()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["hair"])
            p.fillPath(sideburn_l, pal["hair"])

            sideburn_r = QPainterPath()
            sideburn_r.moveTo(33, -8)
            sideburn_r.lineTo(27, -8)
            sideburn_r.lineTo(28, 6)
            sideburn_r.lineTo(33, 4)
            sideburn_r.closeSubpath()
            p.fillPath(sideburn_r, pal["hair"])

            quiff_p = QPainterPath()
            quiff_p.moveTo(-34, -12)
            quiff_p.cubicTo(-38, -36, -14, -50, 10, -46)
            quiff_p.cubicTo(30, -42, 42, -26, 36, -10)
            quiff_p.cubicTo(32, 2, 25, -4, 22, -12)
            quiff_p.cubicTo(16, -20, 4, -25, -6, -16)
            quiff_p.cubicTo(-16, -7, -26, -3, -34, -12)
            quiff_p.closeSubpath()
            p.fillPath(quiff_p, pal["hair"])

            p.setPen(QPen(pal["hair_highlight"], 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(-20, -30), QPointF(-4, -38))
            p.drawLine(QPointF(-8, -26), QPointF(10, -32))
            p.drawLine(QPointF(6, -22), QPointF(22, -28))

        # Floating hearts during hug
        if state_name in ("hugging", "hug"):
            p.setFont(QFont("Segoe UI Emoji", 16))
            p.setPen(QColor(239, 68, 68))
            p.drawText(-10, -48, "❤️")
            p.setFont(QFont("Segoe UI Emoji", 11))
            p.drawText(16, -42, "✨")

        p.restore()
        if body_tilt != 0.0:
            p.restore()

        # Flying affection particles (drifting smoothly up and away into the air)
        if state_name in ("kissing", "kiss"):
            t_anim = walk_phase * 0.35
            particles = [
                ("💋", 16, QColor(244, 63, 94)),
                ("❤️", 13, QColor(239, 68, 68)),
                ("✨", 11, QColor(251, 191, 36)),
                ("💕", 14, QColor(236, 72, 153))
            ]
            for k, (sym, base_size, col) in enumerate(particles):
                prog = (t_anim + k * 0.25) % 1.0
                fly_y = (head_cy - 12.0) - (prog * 60.0) - (prog * prog * 18.0)
                drift_x = math.sin(prog * 3.0 + k * 1.5) * 10.0 + (prog * 18.0)
                fly_x = (cx + 32.0) + drift_x

                alpha = min(1.0, prog / 0.15) if prog < 0.15 else max(0.0, (1.0 - prog) / 0.35)
                scale_size = int(base_size * (0.8 + 0.4 * (1.0 - abs(prog - 0.4))))

                p.save()
                p.setOpacity(alpha)
                p.setFont(QFont("Segoe UI Emoji", scale_size))
                p.setPen(col)
                p.drawText(QPointF(fly_x, fly_y), sym)
                p.restore()

        p.restore()

    def draw_girl(
        self,
        p: QPainter,
        state_name: str,
        direction: Direction,
        walk_phase: float = 0.0,
        is_blinking: bool = False
    ) -> None:
        """Draws the Girl companion (right image: curly hair, black glasses, anime eyes, black tee, backpack)."""
        pal = self.palette
        cx = self.hd_size / 2.0
        cy = 138.0

        p.save()
        if direction == Direction.LEFT:
            p.translate(self.hd_size, 0)
            p.scale(-1, 1)

        body_y = cy
        left_leg_angle = 0.0
        right_leg_angle = 0.0
        left_arm_angle = 0.0
        right_arm_angle = 0.0
        head_tilt = 0.0

        body_tilt = 0.0
        if state_name in ("walk_left", "walk_right", "walking"):
            bounce = abs(math.sin(walk_phase * 2.0)) * 6.0
            body_y -= bounce
            left_leg_angle = math.sin(walk_phase) * 32.0
            right_leg_angle = -math.sin(walk_phase) * 32.0
            left_arm_angle = -math.sin(walk_phase) * 35.0
            right_arm_angle = math.sin(walk_phase) * 35.0
            head_tilt = math.sin(walk_phase) * 2.0
        elif state_name in ("sit", "sitting"):
            body_y += 18.0
            left_leg_angle = 75.0
            right_leg_angle = 75.0
            left_arm_angle = 35.0
            right_arm_angle = 35.0
        elif state_name in ("sleep", "sleeping"):
            body_y += 24.0
            left_leg_angle = 85.0
            right_leg_angle = 85.0
            left_arm_angle = 60.0
            right_arm_angle = 60.0
            head_tilt = 12.0
        elif state_name in ("dragged", "drag"):
            body_y -= 10.0
            left_leg_angle = 15.0
            right_leg_angle = -15.0
            left_arm_angle = -135.0
            right_arm_angle = -135.0
        elif state_name in ("fall", "falling"):
            left_arm_angle = -140.0
            right_arm_angle = -140.0
            left_leg_angle = 20.0
            right_leg_angle = -20.0
        elif state_name in ("hanging", "hang"):
            hang_sway = math.sin(walk_phase) * 7.0
            body_tilt = -hang_sway
            head_tilt = -hang_sway * 0.4
            body_y -= 8.0
            left_arm_angle = -155.0 + hang_sway * 0.8
            right_arm_angle = -150.0 - hang_sway * 0.8
            left_leg_angle = 14.0 + hang_sway * 1.6
            right_leg_angle = -12.0 - hang_sway * 1.6
        elif state_name in ("kissing", "kiss"):
            # Girl stays peaceful, steady, and smiling (no shaking!)
            body_tilt = -5.0
            head_tilt = -8.0
            left_leg_angle = 4.0
            right_leg_angle = -3.0
        elif state_name in ("waiting_kiss",):
            body_tilt = -3.0
            head_tilt = -5.0
            left_leg_angle = 2.0
            right_leg_angle = -2.0
        elif state_name in ("hugging", "hug", "waiting_hug"):
            hug_sway = math.sin(walk_phase * 2.5) * 2.0
            body_tilt = -7.0 - hug_sway
            head_tilt = -11.0 - hug_sway
            left_leg_angle = 6.0
            right_leg_angle = -4.0

        head_cy = body_y - 25.0

        # 1. Ground Shadow (faint and small when hanging high in the air)
        shadow_p = QPainterPath()
        if state_name in ("hanging", "hang"):
            shadow_p.addEllipse(QPointF(cx, 236.0), 20.0, 4.0)
            p.fillPath(shadow_p, QColor(0, 0, 0, 15))
        else:
            shadow_w = 42.0 if state_name not in ("sit", "sitting", "sleep", "sleeping") else 54.0
            shadow_p.addEllipse(QPointF(cx, 236.0), shadow_w, 8.5)
            p.fillPath(shadow_p, QColor(0, 0, 0, 40))

        # Body tilt transform for hug or leaning actions
        if body_tilt != 0.0:
            p.save()
            p.translate(cx, body_y + 36.0)
            p.rotate(body_tilt)
            p.translate(-cx, -(body_y + 36.0))

        # 2. Back Curly Hair (only needed if photo head not loaded)
        if not self.girl_head or self.girl_head.isNull():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["hair_dark"])
            back_curls = [
                (-34, head_cy - 8, 18), (-40, head_cy + 8, 19), (-36, head_cy + 24, 18),
                (34, head_cy - 8, 18), (40, head_cy + 8, 19), (36, head_cy + 24, 18),
                (0, head_cy - 16, 36)
            ]
            for rx, ry, rad in back_curls:
                p.drawEllipse(QPointF(cx + rx, ry), rad, rad)

        # 3. Camo Backpack
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal["backpack"])
        p.drawRoundedRect(int(cx - 20.0), int(body_y + 4.0), 40, 36, 10, 10)
        p.setBrush(pal["camo_spot"])
        p.drawEllipse(QPointF(cx - 8.0, body_y + 14.0), 6.0, 5.0)
        p.drawEllipse(QPointF(cx + 8.0, body_y + 24.0), 7.0, 5.0)

        # 4. Legs & Shoes
        hip_y = body_y + 36.0
        leg_len = 34.0
        for is_right, angle in [(False, left_leg_angle), (True, right_leg_angle)]:
            rad = math.radians(angle)
            lx = cx + (9.0 if is_right else -9.0)
            foot_x = lx + math.sin(rad) * leg_len
            foot_y = hip_y + math.cos(rad) * leg_len

            p.setPen(QPen(pal["pants"], 11.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(lx, hip_y), QPointF(foot_x, foot_y))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["shoes"])
            p.drawRoundedRect(int(foot_x - 7.0), int(foot_y - 2.0), 16, 10, 4, 4)
            p.setBrush(pal["shoe_sole"])
            p.drawRoundedRect(int(foot_x - 7.0), int(foot_y + 6.0), 16, 3, 1, 1)

        # 5. Torso (Fitted Black T-Shirt)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal["shirt"])
        p.drawRoundedRect(int(cx - 17.0), int(body_y + 8.0), 34, 32, 8, 8)

        # Camo Backpack Straps
        p.setPen(QPen(pal["camo_spot"], 3.0))
        p.drawLine(QPointF(cx - 12.0, body_y + 8.0), QPointF(cx - 14.0, body_y + 36.0))
        p.drawLine(QPointF(cx + 12.0, body_y + 8.0), QPointF(cx + 14.0, body_y + 36.0))

        # 6. Arms & Hands
        shoulder_y = body_y + 12.0
        arm_len = 26.0

        if state_name in ("kissing", "kiss"):
            # Front Arm (Left): resting affectionately against boy's chest/shoulder
            sx_l = cx - 18.0
            elbow_x_l = cx - 4.0
            elbow_y_l = shoulder_y + 1.0
            hand_x_l = cx + 18.0
            hand_y_l = shoulder_y + 4.0
            p.setPen(QPen(pal["shirt"], 9.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_l, shoulder_y), QPointF(elbow_x_l, elbow_y_l))
            p.setPen(QPen(pal["skin"], 7.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(elbow_x_l, elbow_y_l), QPointF(hand_x_l, hand_y_l))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_l, hand_y_l), 5.5, 5.5)

            # Back Arm (Right): Wrapped behind boy's back
            sx_r = cx + 18.0
            elbow_x_r = cx - 4.0
            elbow_y_r = shoulder_y + 8.0
            hand_x_r = cx - 26.0
            hand_y_r = shoulder_y + 10.0
            p.setPen(QPen(pal["shirt"], 9.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_r, shoulder_y), QPointF(elbow_x_r, elbow_y_r))
            p.setPen(QPen(pal["skin"], 7.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(elbow_x_r, elbow_y_r), QPointF(hand_x_r, hand_y_r))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_r, hand_y_r), 5.5, 5.5)
        elif state_name in ("hugging", "hug", "waiting_hug"):
            # Front Arm (Left): wraps around boy's neck/shoulder
            sx_l = cx - 18.0
            elbow_x_l = cx - 2.0
            elbow_y_l = shoulder_y - 2.0
            hand_x_l = cx + 22.0
            hand_y_l = shoulder_y - 1.0
            p.setPen(QPen(pal["shirt"], 9.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_l, shoulder_y), QPointF(elbow_x_l, elbow_y_l))
            p.setPen(QPen(pal["skin"], 7.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(elbow_x_l, elbow_y_l), QPointF(hand_x_l, hand_y_l))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_l, hand_y_l), 5.5, 5.5)

            # Back Arm (Right): wraps around boy's back/waist
            sx_r = cx + 18.0
            elbow_x_r = cx - 4.0
            elbow_y_r = shoulder_y + 8.0
            hand_x_r = cx - 26.0
            hand_y_r = shoulder_y + 10.0
            p.setPen(QPen(pal["shirt"], 9.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(sx_r, shoulder_y), QPointF(elbow_x_r, elbow_y_r))
            p.setPen(QPen(pal["skin"], 7.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(elbow_x_r, elbow_y_r), QPointF(hand_x_r, hand_y_r))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(hand_x_r, hand_y_r), 5.5, 5.5)
        else:
            for is_right, angle in [(False, left_arm_angle), (True, right_arm_angle)]:
                rad = math.radians(angle)
                sx = cx + (18.0 if is_right else -18.0)
                hand_x = sx + math.sin(rad) * arm_len
                hand_y = shoulder_y + math.cos(rad) * arm_len

                sleeve_x = sx + math.sin(rad) * 9.0
                sleeve_y = shoulder_y + math.cos(rad) * 9.0
                p.setPen(QPen(pal["shirt"], 9.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(sx, shoulder_y), QPointF(sleeve_x, sleeve_y))

                p.setPen(QPen(pal["skin"], 7.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(sleeve_x, sleeve_y), QPointF(hand_x, hand_y))

                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(pal["skin"])
                p.drawEllipse(QPointF(hand_x, hand_y), 5.5, 5.5)

        # 7. Head, Face & Glasses
        p.save()
        p.translate(cx, head_cy)
        p.rotate(head_tilt)

        # Neck
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal["skin_shadow"])
        p.drawRect(-6, 20, 12, 10)

        # Authentic Photo Face Rendering
        if self.girl_head and not self.girl_head.isNull():
            hw = 116.0
            hh = hw * (self.girl_head.height() / float(self.girl_head.width()))
            head_rect = QRectF(-hw / 2.0, 34.0 - hh, hw, hh)
            p.drawPixmap(head_rect.toRect(), self.girl_head)
        else:
            # Procedural Vector Head Fallback
            # Ears & Pearl Studs
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(-32.0, 3), 6.0, 8.0)
            p.drawEllipse(QPointF(32.0, 3), 6.0, 8.0)
            p.setBrush(pal["earring"])
            p.drawEllipse(QPointF(-32.0, 6), 2.5, 2.5)
            p.drawEllipse(QPointF(32.0, 6), 2.5, 2.5)

            # Face Skin Base (Tan Skin)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["skin"])
            p.drawEllipse(QPointF(0, 0), 32.5, 30.5)

            # Eyebrows
            p.setPen(QPen(pal["hair"], 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(-22, -16, 16, 8, 20 * 16, 140 * 16)
            p.drawArc(6, -16, 16, 8, 20 * 16, 140 * 16)

            # Big Sparkling Anime Eyes
            eye_y = -1.0
            if state_name in ("sleep", "sleeping"):
                p.setPen(QPen(QColor(32, 24, 20), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(-23, int(eye_y - 4), 16, 10, 20 * 16, 140 * 16)
                p.drawArc(7, int(eye_y - 4), 16, 10, 20 * 16, 140 * 16)
            elif is_blinking:
                p.setPen(QPen(QColor(32, 24, 20), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(-22, eye_y), QPointF(-8, eye_y))
                p.drawLine(QPointF(8, eye_y), QPointF(22, eye_y))
            else:
                for ex in [-14.0, 14.0]:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(38, 26, 20))
                    p.drawEllipse(QPointF(ex, eye_y), 8.5, 11.0)
                    p.setBrush(QColor(16, 12, 10))
                    p.drawEllipse(QPointF(ex, eye_y + 1), 5.0, 6.5)
                    # Diamond Star Highlights
                    p.setBrush(QColor(255, 255, 255))
                    p.drawEllipse(QPointF(ex - 2.5, eye_y - 3), 3.8, 4.5)
                    p.drawEllipse(QPointF(ex + 3.0, eye_y + 3), 2.2, 2.2)

            # Black Glasses Frames
            p.setPen(QPen(pal["glasses"], 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(-25, int(eye_y - 10), 21, 21, 6, 6)
            p.drawRoundedRect(4, int(eye_y - 10), 21, 21, 6, 6)
            p.drawLine(QPointF(-4, eye_y - 1), QPointF(4, eye_y - 1))
            p.drawLine(QPointF(-25, eye_y - 2), QPointF(-32, eye_y - 1))
            p.drawLine(QPointF(25, eye_y - 2), QPointF(32, eye_y - 1))

            # Smile & Blush
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(244, 114, 182, 160))
            p.drawEllipse(QPointF(-21, eye_y + 13), 7.5, 4.0)
            p.drawEllipse(QPointF(21, eye_y + 13), 7.5, 4.0)

            p.setPen(QPen(QColor(52, 32, 26), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(-6, int(eye_y + 10), 12, 7, -20 * 16, -140 * 16)

            # Front Curly Hair Ringlets
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal["hair"])
            curls_front = [
                (-26, -26, 13), (-14, -30, 14), (0, -31, 14), (14, -30, 14), (26, -26, 13),
                (-34, -14, 14), (-38, -2, 15), (-36, 12, 14),
                (34, -14, 14), (38, -2, 15), (36, 12, 14),
                (-22, -20, 10), (22, -20, 10)
            ]
            for hx, hy, hrad in curls_front:
                p.drawEllipse(QPointF(hx, hy), float(hrad), float(hrad))

            p.setPen(QPen(pal["hair_highlight"], 1.6))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(-30, -10, 10, 10, 30 * 16, 120 * 16)
            p.drawArc(20, -10, 10, 10, 30 * 16, 120 * 16)

        # Extra cheek blush glow during kiss
        if state_name in ("kissing", "kiss"):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(251, 113, 133, 180))
            p.drawEllipse(QPointF(-18, 14), 10, 6)
            p.drawEllipse(QPointF(18, 14), 10, 6)
        elif state_name in ("hugging", "hug"):
            p.setFont(QFont("Segoe UI Emoji", 16))
            p.setPen(QColor(239, 68, 68))
            p.drawText(6, -48, "❤️")
            p.setFont(QFont("Segoe UI Emoji", 11))
            p.drawText(-18, -42, "✨")

        p.restore()
        if body_tilt != 0.0:
            p.restore()
        p.restore()

    def draw_humanoid(
        self,
        p: QPainter,
        state_name: str,
        direction: Direction,
        walk_phase: float = 0.0,
        is_blinking: bool = False
    ) -> None:
        """Dispatches drawing to the active character model with unified photo-face vector rigging."""
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if self.character_type == "girl_friend":
            self.draw_girl(p, state_name, direction, walk_phase=walk_phase, is_blinking=is_blinking)
        else:
            self.draw_boy(p, state_name, direction, walk_phase=walk_phase, is_blinking=is_blinking)

    def create_sprite(self, state_name: str, direction: Direction, walk_phase: float = 0.0, is_blinking: bool = False) -> QPixmap:
        """Renders and returns a high-resolution pixmap."""
        pixmap = QPixmap(self.hd_size, self.hd_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        self.draw_humanoid(p, state_name, direction, walk_phase=walk_phase, is_blinking=is_blinking)
        p.end()
        return pixmap

    def load_all_sprites(self) -> None:
        """Pre-renders default states."""
        states = [
            "idle", "walk_left", "walk_right", "walking",
            "sit", "sitting", "sleep", "sleeping",
            "dragged", "fall", "falling",
            "hanging",
            "hugging", "waiting_hug",
            "kissing", "kiss", "waiting_kiss"
        ]
        for s in states:
            phase = 0.8 if s in ("walk_left", "walk_right", "walking") else 0.0
            pix_r = self.create_sprite(s, Direction.RIGHT, walk_phase=phase)
            self._pixmaps[(s, Direction.RIGHT)] = pix_r
            self._images[(s, Direction.RIGHT)] = pix_r.toImage()

            pix_l = self.create_sprite(s, Direction.LEFT, walk_phase=phase)
            self._pixmaps[(s, Direction.LEFT)] = pix_l
            self._images[(s, Direction.LEFT)] = pix_l.toImage()

    def get_pixmap(self, state: Any, direction: Direction) -> QPixmap:
        """Retrieves pixmap for given state and direction."""
        state_str = state.value if hasattr(state, "value") else str(state)
        key = (state_str, direction)
        if key in self._pixmaps:
            return self._pixmaps[key]

        fallback_key = (state_str, Direction.RIGHT)
        if fallback_key in self._pixmaps:
            return self._pixmaps[fallback_key]

        return self._pixmaps.get(("idle", Direction.RIGHT), QPixmap())

    def is_opaque_at(self, state: Any, direction: Direction, x: int, y: int) -> bool:
        """Samples alpha channel for per-pixel click transparency."""
        state_str = state.value if hasattr(state, "value") else str(state)
        key = (state_str, direction)
        img = self._images.get(key) or self._images.get((state_str, Direction.RIGHT))
        if not img or x < 0 or y < 0:
            return False

        scale_factor = self.hd_size / float(self.target_width)
        sample_x = int(x * scale_factor)
        sample_y = int(y * scale_factor)

        if 0 <= sample_x < img.width() and 0 <= sample_y < img.height():
            return img.pixelColor(sample_x, sample_y).alpha() > 30

        return False
