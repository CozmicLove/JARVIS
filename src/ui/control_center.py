import os
import sys
import math
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QFrame,
)

from src.system.monitor import SystemMonitor


class JarvisOrb(QWidget):

    def __init__(self):
        super().__init__()
        self.angle = 0
        self.setMinimumSize(520, 520)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(25)

    def animate(self):
        self.angle = (self.angle + 3) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx = self.width() // 2
        cy = self.height() // 2 - 35

        for i in range(7):
            radius = 90 + i * 18
            alpha = 70 - i * 8
            painter.setPen(QPen(QColor(0, 200, 255, alpha), 2))
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        painter.setPen(QPen(QColor(0, 230, 255), 7))
        painter.drawArc(cx - 170, cy - 170, 340, 340, self.angle * 16, 115 * 16)

        painter.setPen(QPen(QColor(0, 120, 180, 140), 2))
        painter.drawEllipse(cx - 130, cy - 130, 260, 260)
        painter.drawEllipse(cx - 105, cy - 105, 210, 210)

        painter.setBrush(QColor(0, 115, 190, 120))
        painter.setPen(QPen(QColor(0, 230, 255), 4))
        painter.drawEllipse(cx - 90, cy - 90, 180, 180)

        for i in range(20):
            a = math.radians(i * 18 + self.angle)
            x = cx + math.cos(a) * 205
            y = cy + math.sin(a) * 205
            painter.setBrush(QColor(0, 220, 255, 190))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)

        painter.setPen(QColor(220, 250, 255))
        painter.setFont(QFont("Segoe UI", 36, QFont.Bold))
        painter.drawText(
            0,
            cy - 45,
            self.width(),
            90,
            Qt.AlignCenter,
            "JARVIS"
        )


class StatusRow(QWidget):

    def __init__(self, title):
        super().__init__()

        self.title = QLabel(title)
        self.title.setFixedWidth(70)

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

    def update_value(self, percent, detail=""):
        self.bar.setValue(percent)
        self.value.setText(f"{percent}%")
        self.detail.setText(detail)


class ControlCenter(QWidget):

    def __init__(self):
        super().__init__()

        self.monitor = SystemMonitor()

        self.setWindowTitle("JARVIS Control Center")
        self.setMinimumSize(1350, 760)

        self.setStyleSheet("""
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
        """)

        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setText(
            "13:37:01   SYSTEM\n"
            "JARVIS Control Center initialized.\n\n"
            "13:37:05   USER\n"
            "Say Jarvis to activate voice assistant.\n\n"
            "13:37:07   JARVIS\n"
            "Standing by, Sir."
        )

        self.orb = JarvisOrb()

        self.cpu = StatusRow("CPU")
        self.gpu = StatusRow("GPU")
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

    def build_layout(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 18, 24, 18)
        main.setSpacing(10)

        title = QLabel("JARVIS CONTROL CENTER")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)

        body = QHBoxLayout()
        body.setSpacing(28)

        left = QVBoxLayout()
        left_title = QLabel("CONVERSATION")
        left_title.setObjectName("Section")
        left.addWidget(left_title)
        left.addWidget(self.conversation)

        center = QVBoxLayout()
        center.setSpacing(0)

        subtitle = QLabel("ALFRED'S PERSONAL ASSISTANT")
        subtitle.setObjectName("SubTitle")
        subtitle.setAlignment(Qt.AlignCenter)

        center.addWidget(subtitle)
        center.addWidget(self.orb, alignment=Qt.AlignCenter)
        center.addStretch()

        status_box = QFrame()
        status_box.setObjectName("Panel")
        status_box_layout = QVBoxLayout(status_box)

        status_text = QLabel("STATUS : ONLINE\nListening for wake word...")
        status_text.setAlignment(Qt.AlignCenter)
        status_box_layout.addWidget(status_text)

        center.addWidget(status_box)

        right_panel = QFrame()
        right_panel.setObjectName("Panel")

        right = QVBoxLayout(right_panel)
        right.setContentsMargins(18, 14, 18, 14)
        right.setSpacing(8)

        right_title = QLabel("SYSTEM STATUS")
        right_title.setObjectName("Section")

        right.addWidget(right_title)
        right.addWidget(self.cpu)
        right.addWidget(self.gpu)
        right.addWidget(self.vram)
        right.addWidget(self.ram)
        right.addWidget(self.disk)
        right.addWidget(self.info)
        right.addStretch()

        body.addLayout(left, 3)
        body.addLayout(center, 5)
        body.addWidget(right_panel, 3)

        main.addWidget(title)
        main.addLayout(body)
        main.addWidget(self.footer)

    def update_realtime(self):
        data = self.monitor.get_status()
        now = time.strftime("%H:%M:%S")

        self.cpu.update_value(data["cpu"])
        self.gpu.update_value(data["gpu"], data["gpu_name"])
        self.vram.update_value(data["vram"], data["vram_text"])
        self.ram.update_value(data["ram"], data["ram_text"])
        self.disk.update_value(data["disk"], data["disk_text"])

        self.info.setText(
            f"{'TIME':<12}: {now}\n"
            f"{'BATTERY':<12}: {data['battery']}\n"
            f"{'POWER':<12}: {data['charging']}\n"
            f"{'INTERNET':<12}: ONLINE\n"
            f"{'MICROPHONE':<12}: READY\n"
            f"{'SPEAKER':<12}: READY\n"
            f"{'MODE':<12}: STANDBY"
        )

        self.footer.setText(
            f"STATUS : ONLINE     |     CPU {data['cpu']}%     GPU {data['gpu']}%     RAM {data['ram']}%     TIME {now}"
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlCenter()
    window.show()
    sys.exit(app.exec())