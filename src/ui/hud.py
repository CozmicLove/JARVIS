import sys
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QApplication, QWidget


class NovaHUD(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NOVA HUD")
        self.setFixedSize(420, 420)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.angle = 0
        self.status = "ONLINE"

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()

    def animate(self):
        self.angle = (self.angle + 3) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter()

        if not painter.begin(self):
            return

        try:
            painter.setRenderHint(QPainter.Antialiasing)

            center_x = self.width() // 2
            center_y = self.height() // 2

            for i in range(5):
                alpha = 45 - i * 7
                radius = 105 + i * 14
                painter.setPen(QPen(QColor(0, 180, 255, alpha), 2))
                painter.drawEllipse(
                    center_x - radius,
                    center_y - radius,
                    radius * 2,
                    radius * 2
                )

            painter.setPen(QPen(QColor(0, 220, 255, 230), 5))
            painter.drawArc(
                center_x - 125,
                center_y - 125,
                250,
                250,
                self.angle * 16,
                120 * 16
            )

            painter.setBrush(QColor(0, 120, 200, 90))
            painter.setPen(QPen(QColor(0, 220, 255, 220), 3))
            painter.drawEllipse(center_x - 70, center_y - 70, 140, 140)

            for i in range(12):
                angle = math.radians(i * 30 + self.angle)
                x = center_x + math.cos(angle) * 155
                y = center_y + math.sin(angle) * 155

                painter.setBrush(QColor(0, 220, 255, 180))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

            painter.setPen(QColor(180, 240, 255))
            painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "NOVA")

            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                0,
                center_y + 95,
                self.width(),
                30,
                Qt.AlignCenter,
                self.status
            )

        finally:
            painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = NovaHUD()
    hud.show()
    sys.exit(app.exec())
