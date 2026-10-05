"""Narrow, presentation-only bridge from the existing NOVA Control Center."""

import json
import time

from PySide6.QtCore import QObject, QPoint, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMenu


class NovaPresentationBridge(QObject):
    snapshotChanged = Signal(str)
    modeChanged = Signal(str)
    frontendReady = Signal()
    frameReady = Signal()

    def __init__(self, control_center):
        super().__init__(control_center)
        self.control_center = control_center

    @Slot(result=str)
    def requestSnapshot(self):
        return self._snapshot_json()

    @Slot()
    def enterCompactOrbMode(self):
        self.control_center.enter_compact_orb_mode()

    @Slot()
    def leaveCompactOrbMode(self):
        self.control_center.exit_compact_orb_mode()

    @Slot(result=str)
    def requestViewMode(self):
        return "orb" if self.control_center.orb_mode else "control"

    @Slot()
    def notifyFrontendReady(self):
        self.frontendReady.emit()

    @Slot()
    def notifyFrameReady(self):
        self.frameReady.emit()

    @Slot(int, int)
    def moveOrbWindow(self, dx, dy):
        center = self.control_center
        if center.orb_mode:
            center.move(center.pos() + QPoint(dx, dy))

    @Slot()
    def showOrbContextMenu(self):
        center = self.control_center
        if not center.orb_mode:
            return
        menu = QMenu(center)
        back = menu.addAction("Control Center")
        exit_action = menu.addAction("Exit NOVA")
        chosen = menu.exec(QCursor.pos())
        if chosen == back:
            center.exit_compact_orb_mode()
        elif chosen == exit_action:
            center.close()

    def publish(self):
        self.snapshotChanged.emit(self._snapshot_json())

    def _snapshot_json(self):
        center = self.control_center
        data = getattr(center, "latest_telemetry", None)
        telemetry = None
        if data is not None:
            telemetry = {
                "cpu": data.get("cpu"),
                "gpu": data.get("gpu"),
                "gpu_temp": data.get("gpu_temp"),
                "ram": data.get("ram"),
                "disk": data.get("disk"),
                "vram": data.get("vram"),
                "cpu_name": data.get("cpu_name") or "CPU",
                "gpu_name": data.get("gpu_name") or "GPU",
                "ram_text": data.get("ram_text") or "",
                "vram_text": data.get("vram_text") or "",
                "disk_text": data.get("disk_text") or "",
                "battery": data.get("battery") or "N/A",
            }
        snapshot = {
            "status": center.nova_status,
            "conversation": [
                {"time": timestamp, "role": role, "text": message}
                for timestamp, role, message in center.conversation_entries
            ],
            "telemetry": telemetry,
            "uptime_seconds": int(time.monotonic() - center.started_at),
            "current_task": None,
            "model": None,
            "agent": "NOVA",
            "voice": "READY" if center.nova_status not in {"LOADING", "OFFLINE"} else "—",
            "floating_orb_diameter": center.floating_orb_diameter,
        }
        return json.dumps(snapshot, ensure_ascii=False)
