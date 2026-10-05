import os
import sys
import math
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QRadialGradient, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QFrame,
    QPushButton,
)

from src.system.monitor import SystemMonitor
from core.runtime import NovaRuntime
from src.ui.control_center_v2_bridge import NovaPresentationBridge


MAX_CONVERSATION_ENTRIES = 45
STREAM_RENDER_INTERVAL = 0.18
FLOATING_ORB_PRESETS = {
    "SMALL": (195, 210, 150),
    "NORMAL": (230, 250, 180),
    "LARGE": (275, 300, 220),
}
FLOATING_ORB_SIZE = os.environ.get("NOVA_FLOATING_ORB_SIZE", "NORMAL").upper()
FLOATING_ORB_WINDOW_WIDTH, FLOATING_ORB_WINDOW_HEIGHT, FLOATING_ORB_DIAMETER = (
    FLOATING_ORB_PRESETS.get(FLOATING_ORB_SIZE, FLOATING_ORB_PRESETS["NORMAL"])
)


class VoiceWorker(QThread):

    status_changed = Signal(str)
    heard = Signal(str)
    answered = Signal(str)
    answer_started = Signal(str)
    answer_delta = Signal(str)
    quit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.runtime = None

    def run(self):
        self.status_changed.emit("LOADING")
        self.runtime = NovaRuntime()
        self.status_changed.emit("READY")
        self.runtime.run(
            callbacks={
                "status": self.status_changed.emit,
                "heard": self.heard.emit,
                "answer": self.answered.emit,
                "answer_start": self.answer_started.emit,
                "answer_delta": self.answer_delta.emit,
                "quit": lambda _: self.quit_requested.emit(),
            },
            announce=True
        )

    def stop(self):
        if self.runtime:
            self.runtime.stop()


class NovaOrb(QWidget):

    def __init__(self):
        super().__init__()
        self.angle = 0
        self.status = "ONLINE"
        self.activity = 0.25
        self.target_activity = 0.25
        self.rotation_speed = 0.35
        self.compact = False
        self.frame_tick = 0
        self.hovered = False
        self.mascot_columns = 8
        self.mascot_rows = 6
        self.mascot_sheet = QPixmap(
            os.path.join(PROJECT_ROOT, "assets", "mascot", "captain_nova_sheet.png")
        )
        self.setMouseTracking(True)
        self.setMinimumSize(520, 520)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def set_compact(self, compact):
        self.compact = compact

        if compact:
            self.setFixedSize(220, 220)
        else:
            self.setMinimumSize(520, 520)
            self.setMaximumSize(16777215, 16777215)

    def set_status(self, status):
        self.status = status
        profile = {
            "STARTING": (0.08, 0.08),
            "LOADING": (0.12, 0.12),
            "READY": (0.22, 0.22),
            "SLEEPING": (0.06, 0.08),
            "STANDBY": (0.18, 0.22),
            "LISTENING": (0.38, 0.45),
            "THINKING": (0.68, 0.95),
            "SPEAKING": (0.88, 1.25),
            "OFFLINE": (0.03, 0.03),
        }.get(status, (0.25, 0.35))
        self.target_activity = profile[0]
        self.rotation_speed = profile[1]

    def animate(self):
        self.activity += (self.target_activity - self.activity) * 0.14
        breathing = 0.04 * math.sin(math.radians(self.angle * 3))

        if self.status == "SPEAKING":
            speed = self.rotation_speed + 1.35 + abs(math.sin(math.radians(self.angle * 5))) * 0.65
        elif self.status == "THINKING":
            speed = self.rotation_speed + 0.75
        else:
            speed = self.rotation_speed + max(0, self.activity + breathing) * 0.45

        self.angle = (self.angle + speed) % 360
        self.frame_tick = (self.frame_tick + 1) % 100000
        self.update()

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def mascot_profile(self):
        status = self.status.upper()
        if self.hovered and status not in {"SPEAKING", "THINKING", "SLEEPING", "OFFLINE"}:
            return 5, 4, 0, 8

        profiles = {
            "STARTING": (2, 5, 0, 8),
            "LOADING": (2, 5, 0, 8),
            "READY": (0, 5, 0, 8),
            "STANDBY": (0, 5, 0, 8),
            "LISTENING": (1, 3, 0, 8),
            "THINKING": (2, 4, 0, 8),
            "SPEAKING": (3, 2, 0, 8),
            "SLEEPING": (4, 7, 0, 8),
            "OFFLINE": (4, 7, 0, 8),
        }
        return profiles.get(status, (0, 5, 0, 8))

    def paint_captain_nova(self, painter, cx, cy, scale):
        if self.mascot_sheet.isNull():
            return False

        sheet_width = self.mascot_sheet.width()
        sheet_height = self.mascot_sheet.height()
        cell_w = sheet_width // self.mascot_columns
        cell_h = sheet_height // self.mascot_rows
        if cell_w <= 0 or cell_h <= 0:
            return False

        row, delay, start, count = self.mascot_profile()
        frame = start + ((self.frame_tick // max(1, delay)) % max(1, count))
        frame = max(0, min(self.mascot_columns - 1, frame))
        row = max(0, min(self.mascot_rows - 1, row))
        source = QRect(frame * cell_w, row * cell_h, cell_w, cell_h)

        status = self.status.upper()
        compact_boost = 0.74 if self.compact else 1.0
        speak_pulse = 0.04 * math.sin(math.radians(self.angle * 8)) if status == "SPEAKING" else 0
        think_pulse = 0.025 * math.sin(math.radians(self.angle * 5)) if status == "THINKING" else 0
        pulse = 1 + speak_pulse + think_pulse

        halo_radius = int(190 * scale * compact_boost * (1 + self.activity * 0.12))
        gradient = QRadialGradient(cx, cy, halo_radius)
        gradient.setColorAt(0.0, QColor(80, 235, 255, 120))
        gradient.setColorAt(0.34, QColor(18, 152, 210, 62))
        gradient.setColorAt(0.76, QColor(8, 48, 86, 28))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(cx - halo_radius, cy - halo_radius, halo_radius * 2, halo_radius * 2)

        ring_color = QColor(56, 218, 245, 118 if status != "SLEEPING" else 58)
        for i, radius in enumerate([122, 154, 186]):
            r = int(radius * scale * compact_boost * pulse)
            painter.setPen(QPen(ring_color, max(1, int((2 - i * 0.25) * scale))))
            painter.setBrush(Qt.NoBrush)
            start_angle = int((self.angle * (1 + i * 0.18) + i * 60) * 16)
            span = int((100 + self.activity * 38 - i * 10) * 16)
            painter.drawArc(cx - r, cy - r, r * 2, r * 2, start_angle, span)
            painter.drawArc(cx - r, cy - r, r * 2, r * 2, start_angle + int(180 * 16), int(span * 0.55))

        target_size = int(min(self.width(), self.height()) * (0.62 if not self.compact else 0.72) * pulse)
        y_shift = int((18 if not self.compact else 10) * scale)
        target = QRect(cx - target_size // 2, cy - target_size // 2 - y_shift, target_size, target_size)
        painter.drawPixmap(target, self.mascot_sheet, source)

        painter.setPen(QColor(140, 238, 255, 190))
        painter.setFont(QFont("Consolas", max(9, int(20 * scale)), QFont.Bold))
        text_y = cy + int((178 if not self.compact else 92) * scale)
        painter.drawText(0, text_y, self.width(), int(34 * scale), Qt.AlignCenter, status)
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx = self.width() // 2
        cy = self.height() // 2
        scale = min(self.width(), self.height()) / 520

        if self.paint_captain_nova(painter, cx, cy, scale):
            return

        self.paint_energy_core_v2(painter, cx, cy, scale)
        return

        if self.compact:
            self.paint_energy_orb(painter, cx, cy)
            return

        activity = self.activity
        glow_boost = int(55 * activity)
        pulse = 1 + 0.035 * math.sin(math.radians(self.angle * (2 + activity * 3)))

        for i in range(7):
            radius = (95 + i * 18) * scale * pulse
            alpha = 45 + glow_boost - i * 6
            painter.setPen(QPen(QColor(0, 200, 255, alpha), 2))
            painter.drawEllipse(
                int(cx - radius),
                int(cy - radius),
                int(radius * 2),
                int(radius * 2)
            )

        painter.setPen(QPen(QColor(0, 230, 255, 145 + int(90 * activity)), 5 + int(3 * activity)))
        outer = int(170 * scale * (1 + activity * 0.03))
        painter.drawArc(cx - outer, cy - outer, outer * 2, outer * 2, self.angle * 16, 115 * 16)

        painter.setPen(QPen(QColor(0, 150, 210, 90 + int(85 * activity)), 2 + int(2 * activity)))
        mid = int(130 * scale)
        painter.drawArc(cx - mid, cy - mid, mid * 2, mid * 2, -self.angle * 16, 80 * 16)

        painter.setBrush(QColor(0, 115, 190, 80 + int(70 * activity)))
        painter.setPen(QPen(QColor(0, 230, 255, 130 + int(95 * activity)), 3 + int(2 * activity)))
        core = int(90 * scale * (1 + activity * 0.05))
        painter.drawEllipse(cx - core, cy - core, core * 2, core * 2)

        painter.setPen(QPen(QColor(0, 230, 255, 140), 2))
        inner = int(65 * scale)
        painter.drawEllipse(cx - inner, cy - inner, inner * 2, inner * 2)

        dot_count = 10 + int(14 * activity)
        for i in range(dot_count):
            a = math.radians(i * (360 / dot_count) + self.angle)
            x = cx + math.cos(a) * 205 * scale
            y = cy + math.sin(a) * 205 * scale
            dot = max(2, int(4 * scale))
            painter.setBrush(QColor(0, 220, 255, 90 + int(120 * activity)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - dot, int(y) - dot, dot * 2, dot * 2)

        painter.setPen(QColor(210, 248, 255))
        painter.setFont(QFont("Segoe UI", max(14, int(34 * scale)), QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, "NOVA")

        painter.setFont(QFont("Segoe UI", max(8, int(12 * scale))))
        painter.drawText(
            0,
            int(cy + 125 * scale),
            self.width(),
            int(30 * scale),
            Qt.AlignCenter,
                self.status
            )

    def paint_pixel_companion(self, painter, cx, cy, scale):
        activity = self.activity
        heartbeat = 0.5 + 0.5 * math.sin(math.radians(self.angle * 5))
        if self.status == "SPEAKING":
            pulse = 1 + 0.055 * heartbeat
        elif self.status == "THINKING":
            pulse = 1 + 0.028 * math.sin(math.radians(self.angle * 3))
        else:
            pulse = 1 + 0.018 * math.sin(math.radians(self.angle))

        aura_radius = int(168 * scale * (1 + activity * 0.12) * pulse)
        glow = QRadialGradient(cx, cy - int(12 * scale), aura_radius)
        glow.setColorAt(0.0, QColor(235, 255, 255, 135 + int(60 * activity)))
        glow.setColorAt(0.20, QColor(69, 232, 255, 95 + int(70 * activity)))
        glow.setColorAt(0.52, QColor(0, 118, 255, 34 + int(50 * activity)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - aura_radius, cy - aura_radius, aura_radius * 2, aura_radius * 2)

        painter.setBrush(Qt.NoBrush)
        ring_alpha = 72 if self.status == "SLEEPING" else 105 + int(55 * activity)
        for i, radius_mul in enumerate((0.86, 1.08, 1.30)):
            radius = int(126 * radius_mul * scale * pulse)
            alpha = max(22, ring_alpha - i * 24)
            width = max(1, int((2 + activity * 2) * scale))
            painter.setPen(QPen(QColor(76, 228, 255, alpha), width))
            if self.status in ("SPEAKING", "THINKING"):
                painter.drawArc(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2,
                    int((self.angle * (1.2 + i * 0.4) + i * 80) * 16),
                    int((82 + activity * 38) * 16),
                )
                painter.drawArc(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2,
                    int((-self.angle * (0.8 + i * 0.25) + 190 + i * 40) * 16),
                    int((46 + activity * 24) * 16),
                )
            else:
                painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        unit = max(3, int(6 * scale))
        grid_w = 46
        grid_h = 58
        ox = int(cx - (grid_w * unit) / 2)
        oy = int(cy - (grid_h * unit) / 2 - 4 * unit)

        def block(gx, gy, gw, gh, color, pen=None):
            painter.setBrush(color)
            painter.setPen(pen if pen is not None else Qt.NoPen)
            painter.drawRect(ox + gx * unit, oy + gy * unit, gw * unit, gh * unit)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        outline = QColor(28, 41, 45, 245)
        cream = QColor(246, 232, 190, 255)
        cream_shadow = QColor(219, 198, 151, 255)
        suit = QColor(238, 245, 221, 255)
        suit_shadow = QColor(202, 217, 190, 255)
        cyan = QColor(48, 227, 255, 255)
        cyan_dark = QColor(0, 119, 190, 255)
        leaf = QColor(149, 228, 75, 255)
        leaf_shadow = QColor(75, 154, 65, 255)

        # Head outline and pixel-soft corners.
        block(9, 15, 28, 22, outline)
        block(7, 18, 32, 16, outline)
        block(11, 13, 24, 2, outline)
        block(11, 37, 24, 2, outline)
        block(10, 16, 26, 20, cream)
        block(8, 19, 30, 14, cream)
        block(11, 14, 24, 2, cream)
        block(11, 36, 24, 2, cream_shadow)
        block(34, 19, 3, 14, cream_shadow)

        # Face.
        eye_color = QColor(38, 48, 58, 255)
        eye_glow = QColor(75, 235, 255, 165 if self.status in ("LISTENING", "SPEAKING") else 85)
        block(16, 25, 3, 3, eye_glow)
        block(17, 25, 2, 3, eye_color)
        block(28, 25, 3, 3, eye_glow)
        block(28, 25, 2, 3, eye_color)
        if self.status == "SPEAKING":
            block(22, 32, 5, 1, QColor(72, 74, 70, 255))
            block(23, 33, 3, 1, QColor(72, 74, 70, 255))
        else:
            block(23, 32, 3, 1, QColor(72, 74, 70, 220))

        # Body, arms, legs.
        block(15, 40, 16, 12, outline)
        block(17, 39, 12, 2, outline)
        block(16, 40, 14, 11, suit)
        block(27, 42, 3, 8, suit_shadow)
        block(11, 42, 5, 8, outline)
        block(30, 42, 5, 8, outline)
        block(12, 43, 3, 6, suit)
        block(31, 43, 3, 6, suit)
        block(17, 52, 5, 4, outline)
        block(25, 52, 5, 4, outline)
        block(18, 52, 3, 3, suit_shadow)
        block(26, 52, 3, 3, suit_shadow)

        # Chest mark.
        block(22, 44, 4, 1, cyan)
        block(21, 45, 6, 3, cyan_dark)
        block(23, 44, 2, 5, cyan)
        block(23, 45, 2, 2, QColor(220, 255, 255, 230))

        # Small NOVA sprout, rebranded as an energy antenna.
        block(22, 8, 2, 6, outline)
        block(23, 7, 2, 7, leaf_shadow)
        block(13, 5, 10, 5, outline)
        block(14, 4, 9, 4, leaf)
        block(15, 6, 8, 4, leaf_shadow)
        block(24, 4, 10, 5, outline)
        block(24, 3, 9, 4, leaf)
        block(24, 5, 8, 4, leaf_shadow)
        block(17, 5, 4, 1, QColor(226, 255, 128, 255))
        block(27, 4, 4, 1, QColor(226, 255, 128, 255))

        painter.restore()

        if self.status == "SPEAKING":
            painter.setPen(QPen(QColor(65, 231, 255, 125 + int(95 * heartbeat)), max(1, int(3 * scale))))
            wave_y = cy - int(8 * scale)
            for side in (-1, 1):
                x = cx + side * int(110 * scale)
                painter.drawLine(x, wave_y - int(22 * scale), x, wave_y + int(22 * scale))
                painter.drawLine(x + side * int(12 * scale), wave_y - int(32 * scale), x + side * int(12 * scale), wave_y + int(32 * scale))

        painter.setPen(QColor(219, 250, 255, 235))
        painter.setFont(QFont("Segoe UI", max(10, int(28 * scale)), QFont.Bold))
        painter.drawText(0, int(cy - 8 * scale), self.width(), int(36 * scale), Qt.AlignCenter, "NOVA")
        painter.setPen(QColor(143, 235, 246, 205))
        painter.setFont(QFont("Segoe UI", max(8, int(12 * scale))))
        painter.drawText(0, int(cy + 128 * scale), self.width(), int(26 * scale), Qt.AlignCenter, self.status)

    def paint_blue_aura_sphere(self, painter, cx, cy, scale):
        activity = self.activity
        compact_boost = 1.18 if self.compact else 1.0
        base = 126 * scale * compact_boost
        pulse = 1 + (0.01 + activity * 0.015) * math.sin(
            math.radians(self.angle * (0.9 + activity * 0.7))
        )

        core_radius = int(base * 0.48 * pulse)
        sphere_radius = int(base * 0.7 * pulse)
        aura_radius = int(base * (1.08 + activity * 0.18))

        glow = QRadialGradient(cx, cy, aura_radius)
        glow.setColorAt(0.0, QColor(250, 255, 255, 70 + int(activity * 90)))
        glow.setColorAt(0.16, QColor(130, 245, 255, 58 + int(activity * 80)))
        glow.setColorAt(0.38, QColor(0, 142, 255, 34 + int(activity * 60)))
        glow.setColorAt(0.68, QColor(0, 60, 190, 12 + int(activity * 34)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - aura_radius,
            cy - aura_radius,
            aura_radius * 2,
            aura_radius * 2
        )

        haze_count = 18 + int(activity * 10)
        for i in range(haze_count):
            phase = math.radians(self.angle * (0.12 + activity * 0.12) + i * 29)
            radius = sphere_radius * (0.48 + (i % 8) * 0.07)
            lift = math.sin(phase * 1.55) * 24 * scale
            drift = math.cos(phase * 1.2) * 24 * scale

            start_x = cx + math.cos(phase) * radius * 0.68
            start_y = cy + math.sin(phase) * radius * 0.42
            end_x = cx + math.cos(phase + 1.12) * (radius + 42 * scale)
            end_y = cy + math.sin(phase + 1.12) * (radius * 0.72 + 18 * scale)

            path = QPainterPath()
            path.moveTo(start_x, start_y)
            path.cubicTo(
                cx + math.cos(phase + 0.22) * (radius + drift),
                cy + math.sin(phase + 0.22) * (radius * 0.4 - lift),
                cx + math.cos(phase + 0.68) * (radius - 34 * scale),
                cy + math.sin(phase + 0.68) * (radius * 0.78 + lift),
                end_x,
                end_y
            )
            alpha = 12 + int(activity * 58) + (i % 4) * 7
            painter.setPen(QPen(QColor(80, 226, 255, alpha), max(1, int(1.0 * scale))))
            painter.drawPath(path)

        sphere = QRadialGradient(
            cx - int(18 * scale),
            cy - int(24 * scale),
            sphere_radius
        )
        sphere.setColorAt(0.0, QColor(255, 255, 255, 182 + int(activity * 48)))
        sphere.setColorAt(0.17, QColor(150, 248, 255, 128 + int(activity * 50)))
        sphere.setColorAt(0.42, QColor(18, 166, 255, 74 + int(activity * 48)))
        sphere.setColorAt(0.72, QColor(0, 64, 172, 42 + int(activity * 34)))
        sphere.setColorAt(1.0, QColor(0, 4, 28, 6 + int(activity * 18)))
        painter.setBrush(sphere)
        painter.setPen(QPen(QColor(165, 248, 255, 40 + int(activity * 70)), max(1, int(1.2 * scale))))
        painter.drawEllipse(
            cx - sphere_radius,
            cy - sphere_radius,
            sphere_radius * 2,
            sphere_radius * 2
        )

        core = QRadialGradient(
            cx - int(8 * scale),
            cy - int(12 * scale),
            core_radius
        )
        core.setColorAt(0.0, QColor(255, 255, 255, 210 + int(activity * 32)))
        core.setColorAt(0.26, QColor(155, 250, 255, 142 + int(activity * 48)))
        core.setColorAt(0.6, QColor(0, 152, 255, 62 + int(activity * 44)))
        core.setColorAt(1.0, QColor(0, 42, 130, 0 + int(activity * 24)))
        painter.setBrush(core)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - core_radius,
            cy - core_radius,
            core_radius * 2,
            core_radius * 2
        )

        painter.setBrush(Qt.NoBrush)
        inner_wisp_count = 12 + int(activity * 10)
        for i in range(inner_wisp_count):
            phase = math.radians(self.angle * (0.2 + activity * 0.2) + i * 43)
            radius = sphere_radius * (0.26 + (i % 6) * 0.08)
            wobble = math.sin(phase * 2.05) * 24 * scale

            path = QPainterPath()
            path.moveTo(
                cx + math.cos(phase) * radius,
                cy + math.sin(phase) * radius * 0.46
            )
            path.cubicTo(
                cx + math.cos(phase + 0.3) * (radius + 32 * scale),
                cy + math.sin(phase + 0.3) * (radius * 0.44 + wobble),
                cx + math.cos(phase + 0.74) * (radius - 26 * scale),
                cy + math.sin(phase + 0.74) * (radius * 0.7 - wobble),
                cx + math.cos(phase + 1.12) * (radius + 10 * scale),
                cy + math.sin(phase + 1.12) * radius * 0.62
            )
            painter.setPen(QPen(QColor(190, 252, 255, 18 + int(activity * 68)), max(1, int(0.9 * scale))))
            painter.drawPath(path)

        particle_count = 10 + int(activity * 16)
        for i in range(particle_count):
            phase = math.radians(i * 137.5 + self.angle * (0.22 + activity * 0.38))
            radius = aura_radius * (0.32 + (i % 8) * 0.07)
            x = cx + math.cos(phase) * radius
            y = cy + math.sin(phase * 0.95) * radius * 0.72
            dot = max(1, int((0.9 + (i % 3) * 0.45) * scale))
            painter.setBrush(QColor(165, 248, 255, 18 + int(activity * 80)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - dot, int(y) - dot, dot * 2, dot * 2)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(230, 254, 255, 28 + int(activity * 82)), max(1, int(1.4 * scale))))
        painter.drawEllipse(
            cx - sphere_radius,
            cy - sphere_radius,
            sphere_radius * 2,
            sphere_radius * 2
        )

        if not self.compact:
            painter.setPen(QColor(146, 236, 248, 180))
            painter.setFont(QFont("Segoe UI", max(8, int(12 * scale))))
            painter.drawText(
                0,
                int(cy + 118 * scale),
                self.width(),
                int(30 * scale),
                Qt.AlignCenter,
                self.status
            )

    def paint_breathing_plasma_orb(self, painter, cx, cy, scale):
        activity = self.activity
        compact_boost = 1.12 if self.compact else 1.0

        slow_breath = math.sin(math.radians(self.angle * 1.8))
        heartbeat = 0

        if self.status == "SPEAKING":
            beat = abs(math.sin(math.radians(self.angle * 7.5)))
            heartbeat = beat ** 5
        elif self.status == "THINKING":
            heartbeat = abs(math.sin(math.radians(self.angle * 3))) ** 3 * 0.45

        base = 118 * scale * compact_boost
        sphere_radius = int(base * (0.72 + slow_breath * 0.018 + heartbeat * 0.06))
        core_radius = int(base * (0.36 + activity * 0.03 + heartbeat * 0.04))
        aura_radius = int(base * (1.18 + activity * 0.14 + heartbeat * 0.14))

        glow = QRadialGradient(cx, cy, aura_radius)
        glow.setColorAt(0.0, QColor(250, 255, 255, 55 + int(activity * 74) + int(heartbeat * 35)))
        glow.setColorAt(0.2, QColor(90, 230, 255, 48 + int(activity * 62) + int(heartbeat * 45)))
        glow.setColorAt(0.48, QColor(0, 110, 255, 24 + int(activity * 42) + int(heartbeat * 24)))
        glow.setColorAt(0.82, QColor(0, 28, 110, 6 + int(activity * 18)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - aura_radius,
            cy - aura_radius,
            aura_radius * 2,
            aura_radius * 2
        )

        sphere = QRadialGradient(
            cx - int(18 * scale),
            cy - int(22 * scale),
            sphere_radius
        )
        sphere.setColorAt(0.0, QColor(255, 255, 255, 145 + int(activity * 45)))
        sphere.setColorAt(0.2, QColor(100, 236, 255, 96 + int(activity * 42)))
        sphere.setColorAt(0.5, QColor(0, 126, 238, 54 + int(activity * 38)))
        sphere.setColorAt(0.76, QColor(0, 40, 138, 25 + int(activity * 22)))
        sphere.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(sphere)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - sphere_radius,
            cy - sphere_radius,
            sphere_radius * 2,
            sphere_radius * 2
        )

        core = QRadialGradient(
            cx - int(6 * scale),
            cy - int(10 * scale),
            core_radius
        )
        core.setColorAt(0.0, QColor(255, 255, 255, 205 + int(heartbeat * 40)))
        core.setColorAt(0.28, QColor(120, 245, 255, 130 + int(activity * 55)))
        core.setColorAt(0.65, QColor(0, 135, 255, 52 + int(activity * 42)))
        core.setColorAt(1.0, QColor(0, 55, 155, 0 + int(activity * 18)))
        painter.setBrush(core)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - core_radius,
            cy - core_radius,
            core_radius * 2,
            core_radius * 2
        )

        painter.setBrush(Qt.NoBrush)

        swirl_count = 12 + int(activity * 8)
        for i in range(swirl_count):
            phase = math.radians(self.angle * (0.34 + activity * 0.22) + i * (360 / swirl_count))
            radius = sphere_radius * (0.22 + (i % 6) * 0.085)
            span = 36 + int(activity * 45) + (i % 3) * 10
            start = int(math.degrees(phase)) % 360
            alpha = 18 + int(activity * 82) + int(heartbeat * 65) - (i % 4) * 8
            width = max(1, int((1.2 + activity * 1.8 + heartbeat * 2.2) * scale))
            painter.setPen(QPen(QColor(150, 248, 255, max(12, alpha)), width))
            painter.drawArc(
                int(cx - radius),
                int(cy - radius * 0.72),
                int(radius * 2),
                int(radius * 1.44),
                start * 16,
                span * 16
            )

        wave_count = 7 + int(activity * 7)
        for i in range(wave_count):
            phase = math.radians(self.angle * (0.22 + activity * 0.18) + i * (360 / wave_count))
            radius = sphere_radius * (0.34 + (i % 5) * 0.095)
            drift = math.sin(phase * 1.9) * 22 * scale

            path = QPainterPath()
            path.moveTo(
                cx + math.cos(phase) * radius,
                cy + math.sin(phase) * radius * 0.52
            )
            path.cubicTo(
                cx + math.cos(phase + 0.28) * (radius + 28 * scale),
                cy + math.sin(phase + 0.28) * (radius * 0.46 + drift),
                cx + math.cos(phase + 0.72) * (radius - 24 * scale),
                cy + math.sin(phase + 0.72) * (radius * 0.72 - drift),
                cx + math.cos(phase + 1.16) * (radius + 12 * scale),
                cy + math.sin(phase + 1.16) * radius * 0.62
            )

            alpha = 18 + int(activity * 72) + int(heartbeat * 42)
            painter.setPen(QPen(QColor(160, 248, 255, alpha), max(1, int(0.9 * scale))))
            painter.drawPath(path)

        particle_count = 7 + int(activity * 12)
        for i in range(particle_count):
            phase = math.radians(i * 137.5 + self.angle * (0.25 + activity * 0.4))
            radius = sphere_radius * (0.28 + (i % 7) * 0.075)
            x = cx + math.cos(phase) * radius
            y = cy + math.sin(phase * 0.92) * radius * 0.72
            dot = max(1, int((0.9 + (i % 3) * 0.5) * scale))
            painter.setBrush(QColor(160, 248, 255, 24 + int(activity * 90) + int(heartbeat * 55)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - dot, int(y) - dot, dot * 2, dot * 2)

        painter.setPen(QColor(232, 253, 255, 230))
        font_size = 26 if self.compact else max(14, int(34 * scale))
        painter.setFont(QFont("Segoe UI", font_size, QFont.Bold))
        painter.drawText(0, cy - int(18 * scale), self.width(), int(40 * scale), Qt.AlignCenter, "NOVA")

        painter.setPen(QColor(145, 235, 248, 190))
        status_size = 8 if self.compact else max(8, int(12 * scale))
        painter.setFont(QFont("Segoe UI", status_size, QFont.Normal))
        painter.drawText(
            0,
            cy + int((46 if self.compact else 118) * scale),
            self.width(),
            int(24 * scale),
            Qt.AlignCenter,
            self.status
        )

    def paint_energy_core_v2(self, painter, cx, cy, scale):
        activity = self.activity
        compact_boost = 1.25 if self.compact else 1.0
        heartbeat = 0

        if self.status == "SPEAKING":
            beat = abs(math.sin(math.radians(self.angle * 7)))
            heartbeat = beat ** 5

        pulse = 1 + (0.018 + activity * 0.025) * math.sin(
            math.radians(self.angle * (1.5 + activity * 1.8))
        ) + heartbeat * 0.09

        base = 112 * scale * compact_boost
        core_radius = int(base * (0.55 + activity * 0.035) * pulse)
        glass_radius = int(base * (0.78 + activity * 0.04) * pulse)
        glow_radius = int(base * (1.12 + activity * 0.18))

        glow = QRadialGradient(cx, cy, glow_radius)
        glow.setColorAt(0.0, QColor(235, 255, 255, 55 + int(75 * activity)))
        glow.setColorAt(0.22, QColor(70, 232, 255, 48 + int(75 * activity)))
        glow.setColorAt(0.55, QColor(0, 118, 255, 24 + int(55 * activity)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - glow_radius,
            cy - glow_radius,
            glow_radius * 2,
            glow_radius * 2
        )

        glass = QRadialGradient(cx - int(18 * scale), cy - int(22 * scale), glass_radius)
        glass.setColorAt(0.0, QColor(255, 255, 255, 120 + int(55 * activity)))
        glass.setColorAt(0.25, QColor(105, 238, 255, 82 + int(55 * activity)))
        glass.setColorAt(0.58, QColor(0, 132, 235, 48 + int(55 * activity)))
        glass.setColorAt(1.0, QColor(0, 18, 45, 16 + int(30 * activity)))
        painter.setBrush(glass)
        painter.setPen(QPen(QColor(130, 242, 255, 72 + int(85 * activity)), max(1, int(2 * scale))))
        painter.drawEllipse(
            cx - glass_radius,
            cy - glass_radius,
            glass_radius * 2,
            glass_radius * 2
        )

        core = QRadialGradient(cx - int(10 * scale), cy - int(12 * scale), core_radius)
        core.setColorAt(0.0, QColor(245, 255, 255, 165 + int(55 * activity)))
        core.setColorAt(0.36, QColor(42, 224, 255, 105 + int(65 * activity)))
        core.setColorAt(0.74, QColor(0, 95, 210, 45 + int(55 * activity)))
        core.setColorAt(1.0, QColor(0, 20, 55, 12 + int(30 * activity)))
        painter.setBrush(core)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            cx - core_radius,
            cy - core_radius,
            core_radius * 2,
            core_radius * 2
        )

        painter.setBrush(Qt.NoBrush)

        if self.status == "SLEEPING":
            ring_alpha = 42
            ripple_count = 1
        elif self.status == "OFFLINE":
            ring_alpha = 24
            ripple_count = 0
        elif self.status == "LOADING":
            ring_alpha = 62
            ripple_count = 1
        elif self.status == "THINKING":
            ring_alpha = 110
            ripple_count = 3
        elif self.status == "SPEAKING":
            ring_alpha = 135
            ripple_count = 4
        else:
            ring_alpha = 95
            ripple_count = 2

        for i in range(ripple_count):
            radius = int(base * (0.92 + i * 0.18 + activity * 0.05))
            alpha = max(18, ring_alpha - i * 26)
            painter.setPen(QPen(QColor(54, 226, 255, alpha), max(1, int((1.5 + activity) * scale))))
            painter.drawEllipse(
                cx - radius,
                cy - radius,
                radius * 2,
                radius * 2
            )

        if self.status in ("SPEAKING", "THINKING"):
            scan_layers = [
                (1.27, 88, 1.55, 0),
                (1.27, 42, 1.55, 146),
                (1.03, 78, -1.2, 52),
                (1.03, 34, -1.2, 228),
            ]

            for radius_scale, span, direction, offset in scan_layers:
                radius = int(base * (radius_scale + heartbeat * 0.035))
                start = int((self.angle * direction + offset) % 360)
                alpha = 48 + int(88 * activity) + int(45 * heartbeat)
                width = max(1, int((1.35 + activity * 1.7 + heartbeat * 1.2) * scale))
                pen = QPen(QColor(112, 244, 255, min(210, alpha)), width)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawArc(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2,
                    start * 16,
                    span * 16
                )

        arc_sets = [
            (0.72, 62, 0.52),
            (0.95, 48, -0.38),
            (1.16, 34, 0.26),
        ]

        for index, (radius_scale, span, direction) in enumerate(arc_sets):
            radius = int(base * radius_scale)
            start = int((self.angle * direction + index * 128) % 360)
            alpha = 58 + int(95 * activity) - index * 22
            width = max(1, int((2.2 - index * 0.25 + activity * 1.6) * scale))
            painter.setPen(QPen(QColor(70, 235, 255, alpha), width))
            painter.drawArc(
                cx - radius,
                cy - radius,
                radius * 2,
                radius * 2,
                start * 16,
                span * 16
            )

        if self.status == "SPEAKING":
            reactor_arcs = [
                (1.43, 18, 2.15, 0),
                (1.43, 18, 2.15, 72),
                (1.43, 18, 2.15, 144),
                (1.43, 18, 2.15, 216),
                (1.43, 18, 2.15, 288),
                (0.64, 42, -2.35, 35),
                (0.64, 42, -2.35, 155),
                (0.64, 42, -2.35, 275),
            ]

            for radius_scale, span, direction, offset in reactor_arcs:
                radius = int(base * radius_scale)
                start = int((self.angle * direction + offset) % 360)
                alpha = 82 + int(92 * heartbeat)
                width = max(1, int((1.65 + heartbeat * 2.1) * scale))
                pen = QPen(QColor(115, 245, 255, alpha), width)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawArc(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2,
                    start * 16,
                    span * 16
                )

            scan_radius = int(base * (1.48 + heartbeat * 0.08))
            painter.setPen(QPen(QColor(35, 210, 255, 38 + int(heartbeat * 55)), max(1, int(1.1 * scale))))
            painter.drawEllipse(
                cx - scan_radius,
                cy - scan_radius,
                scan_radius * 2,
                scan_radius * 2
            )

        particle_count = 4 + int(activity * 12)
        for i in range(particle_count):
            phase = math.radians(i * 137.5 + self.angle * (0.48 + activity * 0.65))
            radius = base * (0.9 + (i % 5) * 0.06)
            x = cx + math.cos(phase) * radius
            y = cy + math.sin(phase) * radius
            dot = max(1, int((1.5 + (i % 2)) * scale))
            painter.setBrush(QColor(155, 247, 255, 28 + int(105 * activity)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - dot, int(y) - dot, dot * 2, dot * 2)

        if not self.compact:
            painter.setPen(QColor(228, 253, 255, 225))
            painter.setFont(QFont("Segoe UI", max(14, int(34 * scale)), QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "NOVA")

            painter.setPen(QColor(145, 235, 248, 175))
            painter.setFont(QFont("Segoe UI", max(8, int(12 * scale))))
            painter.drawText(
                0,
                int(cy + 118 * scale),
                self.width(),
                int(30 * scale),
                Qt.AlignCenter,
                self.status
            )
        else:
            painter.setPen(QColor(235, 253, 255, 220))
            painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
            painter.drawText(0, cy - 12, self.width(), 24, Qt.AlignCenter, "NOVA")

            painter.setPen(QColor(145, 235, 248, 185))
            painter.setFont(QFont("Segoe UI", 8, QFont.Normal))
            painter.drawText(0, cy + 32, self.width(), 18, Qt.AlignCenter, self.status)

    def paint_energy_orb(self, painter, cx, cy):
        activity = self.activity
        pulse = 1 + (0.01 + activity * 0.035) * math.sin(math.radians(self.angle * (2 + activity * 3)))
        core_radius = int((43 + activity * 5) * pulse)
        glass_radius = int(58 + activity * 5)
        outer_radius = int(76 + activity * 8)
        glow_radius = int(82 + activity * 26)

        glow = QRadialGradient(cx, cy, glow_radius)
        glow.setColorAt(0.0, QColor(210, 252, 255, 55 + int(85 * activity)))
        glow.setColorAt(0.3, QColor(55, 220, 255, 42 + int(65 * activity)))
        glow.setColorAt(0.68, QColor(0, 95, 210, 20 + int(45 * activity)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - glow_radius, cy - glow_radius, glow_radius * 2, glow_radius * 2)

        glass = QRadialGradient(cx - 12, cy - 16, glass_radius)
        glass.setColorAt(0.0, QColor(245, 255, 255, 120 + int(70 * activity)))
        glass.setColorAt(0.28, QColor(95, 230, 255, 78 + int(70 * activity)))
        glass.setColorAt(0.62, QColor(0, 115, 225, 50 + int(65 * activity)))
        glass.setColorAt(1.0, QColor(0, 28, 76, 18 + int(30 * activity)))
        painter.setBrush(glass)
        painter.setPen(QPen(QColor(130, 244, 255, 85 + int(110 * activity)), 1))
        painter.drawEllipse(cx - glass_radius, cy - glass_radius, glass_radius * 2, glass_radius * 2)

        core = QRadialGradient(cx - 8, cy - 10, core_radius)
        core.setColorAt(0.0, QColor(235, 255, 255, 160 + int(70 * activity)))
        core.setColorAt(0.4, QColor(35, 215, 255, 80 + int(80 * activity)))
        core.setColorAt(1.0, QColor(0, 90, 210, 10 + int(40 * activity)))
        painter.setBrush(core)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - core_radius, cy - core_radius, core_radius * 2, core_radius * 2)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(160, 248, 255, 80 + int(115 * activity)), 1))
        painter.drawEllipse(cx - glass_radius, cy - glass_radius, glass_radius * 2, glass_radius * 2)

        painter.setPen(QPen(QColor(0, 215, 255, 45 + int(125 * activity)), 2))
        painter.drawEllipse(cx - outer_radius, cy - outer_radius, outer_radius * 2, outer_radius * 2)

        painter.setPen(QPen(QColor(0, 95, 210, 22 + int(58 * activity)), 1))
        painter.drawEllipse(cx - 94, cy - 94, 188, 188)

        for i, radius in enumerate([69, 82, 93]):
            start = (self.angle * (0.65 + activity * 1.7) + i * 122) % 360
            span = 34 + int(activity * 36) + i * 8
            alpha = 55 + int(105 * activity) - i * 16
            painter.setPen(QPen(QColor(65, 235, 255, alpha), 2))
            painter.drawArc(
                cx - radius,
                cy - radius,
                radius * 2,
                radius * 2,
                start * 16,
                span * 16
            )

        for i in range(4):
            phase = math.radians(self.angle * (0.7 + activity) + i * 90)
            radius = 62 + activity * 11
            x1 = cx + math.cos(phase) * radius
            y1 = cy + math.sin(phase) * radius
            x2 = cx + math.cos(phase + 0.24) * (radius + 20)
            y2 = cy + math.sin(phase + 0.24) * (radius + 20)

            wisp = QPainterPath()
            wisp.moveTo(x1, y1)
            wisp.cubicTo(
                cx + math.cos(phase + 0.1) * (radius + 14),
                cy + math.sin(phase + 0.1) * (radius + 14),
                cx + math.cos(phase + 0.18) * (radius - 11),
                cy + math.sin(phase + 0.18) * (radius - 11),
                x2,
                y2
            )
            painter.setPen(QPen(QColor(0, 195, 255, 20 + int(70 * activity)), 1))
            painter.drawPath(wisp)

        painter.setPen(QPen(QColor(210, 250, 255, 40 + int(85 * activity)), 1))
        painter.drawLine(cx - 34, cy, cx + 34, cy)
        painter.drawLine(cx, cy - 34, cx, cy + 34)

        particle_count = 4 + int(activity * 10)
        for i in range(particle_count):
            phase = math.radians(i * 137 + self.angle * (0.7 + activity * 1.4))
            radius = 86 + (i % 4) * 4
            x = cx + math.cos(phase) * radius
            y = cy + math.sin(phase) * radius
            dot = 1 + (i % 2)
            painter.setBrush(QColor(120, 245, 255, 30 + int(105 * activity)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - dot, int(y) - dot, dot * 2, dot * 2)

        painter.setPen(QColor(235, 253, 255))
        painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
        painter.drawText(0, cy - 12, self.width(), 24, Qt.AlignCenter, "NOVA")

        painter.setPen(QColor(140, 230, 245, 115))
        painter.setFont(QFont("Segoe UI", 7, QFont.Normal))
        painter.drawText(0, cy + 30, self.width(), 18, Qt.AlignCenter, self.status)


class OrbWindow(QWidget):

    def __init__(self, restore_callback):
        super().__init__()
        self.restore_callback = restore_callback
        self.drag_position = None
        self.hud_text = ""

        self.setWindowTitle("NOVA Orb")
        self.setFixedSize(220, 220)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.NoDropShadowWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent; border: 0px;")

        self.orb = NovaOrb()
        self.orb.set_compact(True)
        self.orb.setStyleSheet("background: transparent; border: 0px;")

        self.hud = QFrame()
        self.hud.setObjectName("OrbHud")
        self.hud.setStyleSheet("""
            QFrame#OrbHud {
                background-color: rgba(3, 18, 30, 178);
                border: 1px solid rgba(0, 220, 255, 170);
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: 0px;
                color: #dffaff;
                font-size: 13px;
                line-height: 1.35;
            }
        """)
        self.hud.hide()

        self.hud_label = QLabel("")
        self.hud_label.setWordWrap(True)
        self.hud_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        hud_layout = QVBoxLayout(self.hud)
        hud_layout.setContentsMargins(14, 12, 14, 12)
        hud_layout.setSpacing(0)
        hud_layout.addWidget(self.hud_label)

        self.hide_hud_timer = QTimer(self)
        self.hide_hud_timer.setSingleShot(True)
        self.hide_hud_timer.timeout.connect(self.hide_answer_hud)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.orb)
        layout.addWidget(self.hud)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.restore_callback()
        elif event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() -
                self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None

    def compact_answer_text(self, text):
        text = " ".join(str(text).split())

        if len(text) <= 520:
            return text

        return text[:517].rstrip() + "..."

    def resize_answer_hud(self):
        text = self.compact_answer_text(self.hud_text)
        length = len(text)

        if length <= 80:
            width = 300
            height = 82
        elif length <= 180:
            width = 390
            height = 112
        elif length <= 320:
            width = 470
            height = 152
        else:
            width = 540
            height = 196

        self.hud.setFixedSize(width, height)
        self.setFixedSize(220 + 8 + width, max(220, height))

    def show_answer_hud(self, text=""):
        self.hide_hud_timer.stop()
        self.hud_text = str(text or "")
        self.hud_label.setText(self.compact_answer_text(self.hud_text))
        self.resize_answer_hud()

        if not self.hud.isVisible():
            self.hud.show()

    def append_answer_hud(self, delta):
        if not self.hud.isVisible():
            self.show_answer_hud("")

        self.hud_text += str(delta or "")
        self.hud_label.setText(self.compact_answer_text(self.hud_text))
        self.resize_answer_hud()

    def finish_answer_hud(self):
        if self.hud.isVisible():
            self.hide_hud_timer.start(3500)

    def hide_answer_hud(self):
        self.hud.hide()
        self.hud_text = ""
        self.hud_label.setText("")
        self.setFixedSize(220, 220)

    def closeEvent(self, event):
        self.orb.timer.stop()
        event.accept()


class StatusRow(QWidget):

    def __init__(self, title):
        super().__init__()

        self.title = QLabel(title)
        self.title.setFixedWidth(90)

        self.detail = QLabel("")
        self.detail.setStyleSheet("color: #7fa8b5; font-size: 12px;")

        self.value = QLabel("0%")
        self.value.setFixedWidth(55)
        self.value.setAlignment(Qt.AlignRight)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        top = QHBoxLayout()
        top.addWidget(self.title)
        top.addWidget(self.detail)
        top.addStretch()
        top.addWidget(self.value)

        layout.addLayout(top)
        layout.addWidget(self.bar)

    def update_value(self, percent, detail="", value_text=None):
        self.bar.setValue(percent)
        self.value.setText(value_text or f"{percent}%")
        self.detail.setText(detail)


class ControlCenter(QWidget):

    def __init__(self):
        super().__init__()

        self.monitor = SystemMonitor()
        self.started_at = time.monotonic()
        self.latest_telemetry = None
        self.orb_mode = False
        self._compact_position = None
        self.drag_position = None
        self.orb_window = None
        self.voice_worker = None
        self.nova_status = "LOADING"
        self.floating_orb_diameter = FLOATING_ORB_DIAMETER
        self.conversation_entries = []
        self.streaming_nova_index = None
        self.last_stream_render = 0

        self.setWindowTitle("NOVA Control Center")
        self.setMinimumSize(1350, 760)

        self.base_stylesheet = """
            QWidget {
                background-color: #030810;
                color: #d7f7ff;
                font-family: Segoe UI;
            }

            QLabel#Title {
                font-size: 36px;
                font-weight: bold;
                color: #42dfff;
            }

            QLabel#Section {
                font-size: 16px;
                font-weight: bold;
                color: #00e5ff;
            }

            QLabel#SubTitle {
                font-size: 19px;
                font-weight: bold;
                color: #00e5ff;
            }

            QTextEdit {
                background-color: #06111d;
                border: 1px solid #0098c8;
                border-radius: 14px;
                padding: 16px;
                color: #d7f7ff;
                font-size: 14px;
            }

            QLabel {
                font-size: 14px;
            }

            QProgressBar {
                background-color: #0a1b28;
                border: 1px solid #06394f;
                border-radius: 5px;
            }

            QProgressBar::chunk {
                background-color: #00e5ff;
                border-radius: 5px;
            }

            QFrame#Panel {
                background-color: #06111d;
                border: 1px solid #0098c8;
                border-radius: 14px;
            }

            QPushButton {
                background-color: #06111d;
                border: 1px solid #0098c8;
                border-radius: 8px;
                color: #8eeaff;
                font-weight: bold;
                padding: 9px 14px;
            }

            QPushButton:hover {
                background-color: #092033;
                color: #ffffff;
            }
        """
        self.setStyleSheet(self.base_stylesheet)

        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        self.seed_conversation()

        web_index = os.path.join(
            os.path.dirname(__file__), "control_center_v2_web", "dist", "index.html"
        )
        if not os.path.isfile(web_index):
            raise FileNotFoundError(
                f"NOVA Control Center V2 bundle is missing: {web_index}"
            )
        self._v2_web_index = web_index
        # The mascot renderer belongs only to the legacy UI. Never construct it
        # on the V2 startup path, even as an off-screen placeholder.
        self.orb = None

        self.cpu = StatusRow("CPU")
        self.gpu = StatusRow("GPU")
        self.gpu_temp = StatusRow("GPU TEMP")
        self.vram = StatusRow("VRAM")
        self.ram = StatusRow("RAM")
        self.disk = StatusRow("DISK")

        self.info = QLabel()
        self.info.setObjectName("Panel")
        self.info.setStyleSheet("""
            QLabel {
                background-color: #06111d;
                border: 1px solid #0098c8;
                border-radius: 14px;
                padding: 14px;
                font-size: 14px;
                font-family: Consolas;
            }
        """)

        self.footer = QLabel()
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setStyleSheet("""
            QLabel {
                background-color: #06111d;
                border: 1px solid #0098c8;
                border-radius: 12px;
                padding: 10px;
                color: #8eeaff;
            }
        """)

        self.build_layout()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_realtime)
        self.timer.start(1000)

        self.update_realtime()
        self.start_voice_runtime()

    def start_voice_runtime(self):
        self.voice_worker = VoiceWorker()
        self.voice_worker.status_changed.connect(self.set_nova_status)
        self.voice_worker.heard.connect(self.add_user_message)
        self.voice_worker.answered.connect(self.add_nova_message)
        self.voice_worker.answer_started.connect(self.start_nova_stream)
        self.voice_worker.answer_delta.connect(self.add_nova_stream_delta)
        self.voice_worker.quit_requested.connect(self.close_from_voice)
        self.voice_worker.start()

    def close_from_voice(self):
        QTimer.singleShot(500, self.close)

    def seed_conversation(self):
        now = time.strftime("%H:%M:%S")
        self.conversation_entries = [
            (now, "SYSTEM", "NOVA Control Center initialized."),
            (now, "NOVA", "Loading voice command engine..."),
        ]
        self.render_conversation()

    def render_conversation(self):
        if len(self.conversation_entries) > MAX_CONVERSATION_ENTRIES:
            self.conversation_entries = self.conversation_entries[
                -MAX_CONVERSATION_ENTRIES:
            ]
            if self.streaming_nova_index is not None:
                self.streaming_nova_index = len(self.conversation_entries) - 1

        scrollbar = self.conversation.verticalScrollBar()
        old_scroll_value = scrollbar.value()
        was_at_bottom = old_scroll_value >= scrollbar.maximum() - 20

        blocks = [
            f"{timestamp}   {role}\n{message}"
            for timestamp, role, message in self.conversation_entries
            if str(message).strip()
        ]
        self.conversation.setPlainText("\n\n".join(blocks))

        scrollbar = self.conversation.verticalScrollBar()
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(min(old_scroll_value, scrollbar.maximum()))
        if hasattr(self, "v2_bridge"):
            self.v2_bridge.publish()

    def append_conversation(self, role, message):
        if not str(message).strip():
            return

        now = time.strftime("%H:%M:%S")
        self.conversation_entries.append((now, role, message))
        self.streaming_nova_index = None
        self.render_conversation()

    def add_user_message(self, message):
        self.append_conversation("USER", message)

    def add_nova_message(self, message):
        self.append_conversation("NOVA", message)

        if self.orb_window is not None and self.orb_mode:
            self.orb_window.show_answer_hud(message)

    def start_nova_stream(self, message):
        now = time.strftime("%H:%M:%S")
        self.conversation_entries.append((now, "NOVA", message))
        self.streaming_nova_index = len(self.conversation_entries) - 1
        self.last_stream_render = 0
        self.render_conversation()

        if self.orb_window is not None and self.orb_mode:
            self.orb_window.show_answer_hud(message)

    def add_nova_stream_delta(self, delta):
        if self.streaming_nova_index is None:
            self.start_nova_stream("")

        timestamp, role, message = self.conversation_entries[
            self.streaming_nova_index
        ]
        self.conversation_entries[self.streaming_nova_index] = (
            timestamp,
            role,
            message + delta
        )

        now = time.monotonic()
        if delta.endswith("\n") or now - self.last_stream_render >= STREAM_RENDER_INTERVAL:
            self.last_stream_render = now
            self.render_conversation()

        if self.orb_window is not None and self.orb_mode:
            self.orb_window.append_answer_hud(delta)

    def set_nova_status(self, status):
        self.nova_status = status
        status_text = {
            "STANDBY": "Listening for command...",
            "LOADING": "Loading voice command engine...",
            "READY": "Voice command engine ready.",
            "LISTENING": "Listening...",
            "THINKING": "Thinking...",
            "SPEAKING": "Speaking...",
            "SLEEPING": "Sleeping. Waiting for wake up.",
            "OFFLINE": "Offline",
        }.get(status, status.title())

        if self.orb is not None:
            self.orb.set_status(status)

        if self.orb_window is not None:
            self.orb_window.orb.set_status(status)

            if status == "SPEAKING" and self.orb_window.hud_text.strip():
                self.orb_window.show_answer_hud(self.orb_window.hud_text)
            elif status in ("LISTENING", "SLEEPING", "STANDBY", "OFFLINE"):
                self.orb_window.finish_answer_hud()

        self.status_text.setText(f"STATUS : {status}\n{status_text}")
        self.update_realtime()

    def build_layout(self):
        if self._v2_web_index:
            self.build_v2_layout(self._v2_web_index)
            return

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 18, 24, 18)
        self.main_layout.setSpacing(10)

        self.title = QLabel("NOVA CONTROL CENTER")
        self.title.setObjectName("Title")
        self.title.setAlignment(Qt.AlignCenter)

        self.mode_button = QPushButton("ORB MODE")
        self.mode_button.setFixedWidth(120)
        self.mode_button.clicked.connect(self.toggle_orb_mode)

        header = QHBoxLayout()
        header.addStretch()
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.mode_button)

        body = QHBoxLayout()
        body.setSpacing(28)

        self.left_panel = QFrame()
        left = QVBoxLayout(self.left_panel)
        left_title = QLabel("CONVERSATION")
        left_title.setObjectName("Section")
        left.addWidget(left_title)
        left.addWidget(self.conversation)

        self.center_panel = QFrame()
        center = QVBoxLayout(self.center_panel)
        center.setSpacing(0)

        self.subtitle = QLabel("ALFRED'S PERSONAL ASSISTANT")
        self.subtitle.setObjectName("SubTitle")
        self.subtitle.setAlignment(Qt.AlignCenter)

        center.addWidget(self.subtitle)
        center.addWidget(self.orb, alignment=Qt.AlignCenter)
        center.addStretch()

        self.status_box = QFrame()
        self.status_box.setObjectName("Panel")
        status_box_layout = QVBoxLayout(self.status_box)

        self.status_text = QLabel("STATUS : STARTING\nStarting voice runtime...")
        self.status_text.setAlignment(Qt.AlignCenter)
        status_box_layout.addWidget(self.status_text)

        center.addWidget(self.status_box)

        self.right_panel = QFrame()
        self.right_panel.setObjectName("Panel")

        right = QVBoxLayout(self.right_panel)
        right.setContentsMargins(18, 14, 18, 14)
        right.setSpacing(8)

        right_title = QLabel("SYSTEM STATUS")
        right_title.setObjectName("Section")

        right.addWidget(right_title)
        right.addWidget(self.cpu)
        right.addWidget(self.gpu)
        right.addWidget(self.gpu_temp)
        right.addWidget(self.vram)
        right.addWidget(self.ram)
        right.addWidget(self.disk)
        right.addWidget(self.info)
        right.addStretch()

        body.addWidget(self.left_panel, 3)
        body.addWidget(self.center_panel, 5)
        body.addWidget(self.right_panel, 3)

        self.main_layout.addLayout(header)
        self.main_layout.addLayout(body)
        self.main_layout.addWidget(self.footer)

    def build_v2_layout(self, web_index):
        self.status_text = QLabel("STATUS : STARTING", self)
        # Retained for the legacy status setter, never a second visible label.
        self.status_text.hide()
        self.setObjectName("novaControlCenter")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet(self.base_stylesheet + "\nQWidget#novaControlCenter { background: transparent; }\n")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.v2_bridge = NovaPresentationBridge(self)
        self.v2_channel = QWebChannel(self)
        self.v2_channel.registerObject("nova", self.v2_bridge)
        self.v2_view = QWebEngineView(self)
        self.v2_view.setAttribute(Qt.WA_TranslucentBackground, True)
        self.v2_view.setAutoFillBackground(False)
        self.v2_view.setStyleSheet("background: transparent;")
        self.v2_view.page().setBackgroundColor(QColor("#03070f"))
        self.v2_view.page().setWebChannel(self.v2_channel)
        self.v2_view.setContextMenuPolicy(Qt.NoContextMenu)
        self._v2_frontend_ready = False
        self._v2_frame_ready = False
        self.v2_bridge.frontendReady.connect(self._show_v2_when_ready)
        self.v2_bridge.frameReady.connect(self._reveal_v2_when_ready)
        self.v2_view.load(QUrl.fromLocalFile(web_index))
        self.main_layout.addWidget(self.v2_view)

    def _show_v2_when_ready(self):
        if self._v2_frontend_ready:
            return
        self._v2_frontend_ready = True
        # A near-transparent visible surface keeps WebEngine's compositor
        # active; fully transparent windows can suspend animation frames.
        self.setWindowOpacity(0.01)
        self.show()

    def _reveal_v2_when_ready(self):
        if self._v2_frame_ready or not self._v2_frontend_ready:
            return
        self._v2_frame_ready = True
        self.setWindowOpacity(1)

    def toggle_orb_mode(self):
        if self.orb_mode:
            self.show_control_center()
        else:
            self.show_orb_mode()

    def show_orb_mode(self):
        if hasattr(self, "v2_view"):
            self.enter_compact_orb_mode()
            return
        self.orb_mode = True

        if self.orb_window is None:
            self.orb_window = OrbWindow(self.show_control_center)

        self.orb_window.orb.set_status(self.orb.status)
        self.hide()
        self.orb_window.show()

    def show_control_center(self):
        if hasattr(self, "v2_view") and self.orb_mode:
            self.exit_compact_orb_mode()
            return
        self.orb_mode = False

        if self.orb_window is not None:
            self.orb_window.hide()

        self.show()

    def enter_compact_orb_mode(self):
        if not hasattr(self, "v2_view") or self.orb_mode:
            return

        self._control_rect = self.geometry()
        self._control_minimum_size = self.minimumSize()
        self._control_was_maximized = self.isMaximized()
        self._control_window_flags = self.windowFlags()
        self.setWindowState(Qt.WindowNoState)
        self.setMinimumSize(1, 1)
        self.setWindowFlags(self._control_window_flags | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.resize(FLOATING_ORB_WINDOW_WIDTH, FLOATING_ORB_WINDOW_HEIGHT)
        if self._compact_position is None:
            screen = self.screen() or QApplication.primaryScreen()
            available = screen.availableGeometry()
            self.move(available.center() - self.rect().center())
        else:
            self.move(self._compact_position)
        self.orb_mode = True
        # Keep the native compositor's opacity in sync with the document.
        # CSS-only opaque -> transparent changes can leave stale pixels in
        # Qt WebEngine's surface (rings and old labels accumulate).
        self.v2_view.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self.show()
        self._set_floating_window_chrome(True)
        self.v2_bridge.modeChanged.emit("orb")

    def exit_compact_orb_mode(self):
        if not hasattr(self, "v2_view") or not self.orb_mode:
            return

        self._compact_position = self.pos()
        self.setWindowFlags(self._control_window_flags)
        self.setGeometry(self._control_rect)
        self.setMinimumSize(self._control_minimum_size)
        self.orb_mode = False
        self.v2_view.page().setBackgroundColor(QColor("#03070f"))
        if self._control_was_maximized:
            self.showMaximized()
        else:
            self.show()
            self.setGeometry(self._control_rect)
        self._set_floating_window_chrome(False)
        self.v2_bridge.modeChanged.emit("control")

    def _set_floating_window_chrome(self, floating):
        if sys.platform != "win32":
            return
        try:
            import ctypes

            hwnd = ctypes.c_void_p(int(self.winId()))
            border = ctypes.c_uint(0xFFFFFFFE if floating else 0xFFFFFFFF)
            corner = ctypes.c_int(1 if floating else 0)
            dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute
            dwm(hwnd, 34, ctypes.byref(border), ctypes.sizeof(border))
            dwm(hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner))
        except (AttributeError, OSError):
            pass

    def shutdown_windows(self):
        self.timer.stop()
        if self.orb is not None:
            self.orb.timer.stop()

        if self.voice_worker is not None:
            self.voice_worker.stop()
            self.voice_worker.wait(7000)
            self.voice_worker = None

        if self.orb_window is not None:
            self.orb_window.orb.timer.stop()
            self.orb_window.close()
            self.orb_window = None

    def update_realtime(self):
        data = self.monitor.get_status()
        self.latest_telemetry = data
        now = time.strftime("%H:%M:%S")

        self.cpu.update_value(data["cpu"], data["cpu_name"])
        self.gpu.update_value(data["gpu"], data["gpu_name"])
        self.gpu_temp.update_value(
            min(data["gpu_temp"] or 0, 100),
            "",
            data["gpu_temp_text"]
        )
        self.vram.update_value(data["vram"], data["vram_text"])
        self.ram.update_value(data["ram"], data["ram_text"])
        self.disk.update_value(data["disk"], data["disk_text"])

        self.info.setText(
            f"{'TIME':<12}: {now}\n"
            f"{'BATTERY':<12}: {data['battery']}\n"
            f"{'POWER':<12}: {data['charging']}\n"
            f"{'GPU TEMP':<12}: {data['gpu_temp_text']}\n"
            f"{'INTERNET':<12}: ONLINE\n"
            f"{'MICROPHONE':<12}: READY\n"
            f"{'SPEAKER':<12}: READY\n"
            f"{'MODE':<12}: {self.nova_status}"
        )

        self.footer.setText(
            f"STATUS : {self.nova_status}     |     CPU {data['cpu']}%     GPU {data['gpu']}%     RAM {data['ram']}%     TIME {now}"
        )
        if hasattr(self, "v2_bridge"):
            self.v2_bridge.publish()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.orb_mode:
                self.show_control_center()
            else:
                self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()

    def closeEvent(self, event):
        self.shutdown_windows()
        event.accept()
        QApplication.quit()


def _install_clean_captain_nova_renderer():
    import math
    import time
    from pathlib import Path

    def _clean_captain_nova_paint(self, event):
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        width = max(1, self.width())
        height = max(1, self.height())
        center_x = width / 2
        center_y = height / 2

        if not hasattr(self, "_captain_nova_clean_pixmap"):
            project_root = Path(__file__).resolve().parents[2]
            asset_path = project_root / "assets" / "ui" / "captain_nova_clean.png"
            self._captain_nova_clean_pixmap = QPixmap(str(asset_path))

        raw_status = str(
            getattr(self, "mode", getattr(self, "status", getattr(self, "state", "LISTENING")))
        ).upper()
        if "SPEAK" in raw_status:
            status = "SPEAKING"
            pulse = 0.025
        elif "THINK" in raw_status:
            status = "THINKING"
            pulse = 0.012
        elif "SLEEP" in raw_status:
            status = "SLEEPING"
            pulse = 0.0
        elif "LOAD" in raw_status:
            status = "LOADING"
            pulse = 0.01
        elif "OFF" in raw_status:
            status = "OFFLINE"
            pulse = 0.0
        else:
            status = "LISTENING"
            pulse = 0.008

        tick = time.monotonic()
        base_size = min(width, height) * 0.78
        size = base_size * (1.0 + math.sin(tick * 2.2) * pulse)
        bob = math.sin(tick * 1.2) * min(width, height) * 0.012
        top = center_y - size * 0.52 + bob
        mascot_rect = QRectF(center_x - size / 2, top, size, size)

        # Soft glow only; no old HUD rings/orb background.
        glow_alpha = 26 if status in {"SPEAKING", "THINKING", "LISTENING", "LOADING"} else 10
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 220, 255, glow_alpha)))
        painter.drawEllipse(QRectF(center_x - size * 0.30, top + size * 0.08, size * 0.60, size * 0.62))

        pixmap = self._captain_nova_clean_pixmap
        if not pixmap.isNull():
            painter.drawPixmap(mascot_rect, pixmap, QRectF(pixmap.rect()))
        else:
            painter.setPen(QColor("#8EEBFF"))
            painter.setFont(QFont("Segoe UI", max(18, int(size * 0.10)), QFont.Bold))
            painter.drawText(mascot_rect, Qt.AlignCenter, "NOVA")

        painter.setPen(QColor(130, 235, 255, 230))
        painter.setFont(QFont("Consolas", max(14, int(min(width, height) * 0.055)), QFont.Bold))
        painter.drawText(QRectF(0, top + size * 0.89, width, 48), Qt.AlignCenter, status)

    for class_name in ("CaptainNovaOrb", "NovaOrb", "JarvisOrb"):
        orb_class = globals().get(class_name)
        if orb_class is not None:
            orb_class.paintEvent = _clean_captain_nova_paint


_install_clean_captain_nova_renderer()


def _install_final_captain_nova_renderer():
    """Force the runtime avatar to use the clean Captain Nova asset only."""
    from math import sin
    from pathlib import Path

    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

    asset_path = Path(__file__).resolve().parents[2] / "assets" / "mascot" / "captain_nova_clean.png"
    cache = {"pixmap": None}

    def _paint(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        status = str(
            getattr(self, "state", getattr(self, "status", getattr(self, "mode", "LISTENING")))
        ).upper()
        w, h = self.width(), self.height()
        cx, cy = w * 0.5, h * 0.46
        tick = float(getattr(self, "angle", 0.0))

        is_speaking = "SPEAK" in status
        is_thinking = "THINK" in status
        base = min(w * 0.82, h * 0.76)
        pulse = 1.0 + (0.014 * sin(tick * 0.026) if is_speaking else 0.005 * sin(tick * 0.014))
        bob = 2.5 * sin(tick * (0.010 if is_thinking else 0.012))
        size = base * pulse

        pixmap = cache["pixmap"]
        if pixmap.isNull():
            pixmap = QPixmap(str(asset_path))
            cache["pixmap"] = pixmap

        if not pixmap.isNull():
            target = QRectF(cx - size / 2, cy - size / 2 + bob, size, size)
            painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        else:
            painter.setPen(QColor(90, 230, 255, 230))
            painter.setFont(QFont("Arial", max(18, int(base * 0.13)), QFont.Bold))
            painter.drawText(QRectF(0, cy - 30, w, 70), Qt.AlignCenter, "NOVA")

        painter.setPen(QColor(110, 225, 255, 230 if is_speaking else 175))
        painter.setFont(QFont("Consolas", max(13, int(min(w, h) * 0.052)), QFont.Bold))
        painter.drawText(QRectF(0, h - max(68, h * 0.16), w, 44), Qt.AlignCenter, status)
        painter.end()

    for class_name in ("CaptainNovaOrb", "NovaOrb", "JarvisOrb"):
        orb_class = globals().get(class_name)
        if orb_class is not None:
            orb_class.paintEvent = _paint


_install_final_captain_nova_renderer()


def _install_captain_nova_clean_runtime_renderer_v2():
    """Final clean mascot renderer: Captain Nova only, no legacy orb background."""
    from math import sin
    from pathlib import Path

    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

    asset_path = Path(__file__).resolve().parents[2] / "assets" / "mascot" / "captain_nova_clean.png"
    cache = {"pixmap": None}

    def _paint(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        width = self.width()
        height = self.height()
        side = min(width, height)
        phase = float(getattr(self, "phase", 0.0))
        state = str(getattr(self, "state", "idle")).lower()

        if state == "speaking":
            pulse = 1.0 + 0.018 * sin(phase * 0.9)
        elif state == "thinking":
            pulse = 1.0 + 0.012 * sin(phase * 0.7)
        else:
            pulse = 1.0 + 0.006 * sin(phase * 0.45)

        pixmap = cache["pixmap"]
        if pixmap is None or pixmap.isNull():
            pixmap = QPixmap(str(asset_path))
            cache["pixmap"] = pixmap

        if not pixmap.isNull():
            draw_size = side * 0.68 * pulse
            target = QRectF(
                (width - draw_size) / 2,
                (height - draw_size) / 2 - side * 0.04,
                draw_size,
                draw_size,
            )
            painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        else:
            painter.setPen(QColor("#7ee8ff"))
            painter.drawText(self.rect(), Qt.AlignCenter, "NOVA")

        painter.setPen(QColor("#7ee8ff"))
        painter.setFont(QFont("Consolas", max(12, int(side * 0.05))))
        painter.drawText(
            QRectF(0, height - max(44, int(side * 0.16)), width, 34),
            Qt.AlignCenter,
            state.upper(),
        )
        painter.end()

    patched = False
    for class_name, klass in list(globals().items()):
        if isinstance(klass, type) and (
            "Orb" in class_name or "Mascot" in class_name or "Avatar" in class_name
        ):
            if hasattr(klass, "paintEvent"):
                klass.paintEvent = _paint
                patched = True

    if not patched:
        for class_name in ("CaptainNovaOrb", "NovaOrb", "JarvisOrb"):
            klass = globals().get(class_name)
            if klass is not None:
                klass.paintEvent = _paint


_install_captain_nova_clean_runtime_renderer_v2()


def _install_captain_nova_clean_renderer_final():
    """Use the clean Captain NOVA mascot renderer for every orb/avatar widget."""
    import math
    from pathlib import Path

    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

    asset_path = (
        Path(__file__).resolve().parents[2]
        / "assets"
        / "mascot"
        / "captain_nova_clean.png"
    )
    cache = {"pixmap": None}

    def _read_state(widget):
        for attr in ("state", "status", "mode", "_state", "_status", "current_state"):
            value = getattr(widget, attr, None)
            if value:
                return str(value).replace(".", "").strip().lower()
        return "idle"

    def _paint(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), Qt.transparent)

        width = self.width()
        height = self.height()
        side = max(1, min(width, height))
        phase = float(getattr(self, "phase", getattr(self, "_phase", 0.0)))
        state = _read_state(self)

        if "speak" in state:
            pulse = 1.0 + 0.018 * math.sin(phase * 0.18)
            label = "SPEAKING"
        elif "think" in state:
            pulse = 1.0 + 0.012 * math.sin(phase * 0.14)
            label = "THINKING"
        elif "sleep" in state:
            pulse = 0.96 + 0.004 * math.sin(phase * 0.06)
            label = "SLEEPING"
        elif "listen" in state:
            pulse = 1.0 + 0.008 * math.sin(phase * 0.10)
            label = "LISTENING"
        else:
            pulse = 1.0 + 0.005 * math.sin(phase * 0.08)
            label = state.upper() if state else "READY"

        pixmap = cache["pixmap"]
        if pixmap is None or pixmap.isNull():
            pixmap = QPixmap(str(asset_path))
            cache["pixmap"] = pixmap

        if pixmap and not pixmap.isNull():
            draw_size = min(width * 0.88, height * 0.78) * pulse
            target = QRectF(
                (width - draw_size) / 2,
                (height - draw_size) / 2 - side * 0.025,
                draw_size,
                draw_size,
            )
            painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        else:
            painter.setPen(QColor("#7ee8ff"))
            painter.setFont(QFont("Consolas", max(18, int(side * 0.10)), QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "NOVA")

        painter.setPen(QColor("#7ee8ff"))
        painter.setFont(QFont("Consolas", max(11, int(side * 0.052)), QFont.Bold))
        painter.drawText(
            QRectF(0, height - max(40, int(side * 0.13)), width, 34),
            Qt.AlignCenter,
            label,
        )
        painter.end()

    for name, klass in list(globals().items()):
        if isinstance(klass, type) and (
            "Orb" in name or "Mascot" in name or "Avatar" in name
        ):
            if hasattr(klass, "paintEvent"):
                klass.paintEvent = _paint


_install_captain_nova_clean_renderer_final()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = ControlCenter()
    if not window._v2_web_index:
        window.show()
    sys.exit(app.exec())
