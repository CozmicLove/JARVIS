"""Launch the standalone, offline NOVA WebGL visual prototype."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow


PAGE = Path(__file__).resolve().parent / "orb_webgl" / "index.html"


class PreviewPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f"[WebGL {level.name}] {source}:{line}: {message}", file=sys.stderr)


class OfflineInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if info.requestUrl().scheme() not in {"file", "data", "blob"}:
            info.block(True)


class OrbPreview(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVA Orb — WebGL Prototype")
        self.resize(1000, 760)
        self.view = QWebEngineView(self)
        self._profile = QWebEngineProfile(self)
        self._offline_interceptor = OfflineInterceptor(self)
        self._profile.setUrlRequestInterceptor(self._offline_interceptor)
        self.view.setPage(PreviewPage(self._profile, self.view))
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        self.setCentralWidget(self.view)
        self.view.load(QUrl.fromLocalFile(str(PAGE)))
        reload_shortcut = QShortcut(QKeySequence("F5"), self)
        reload_shortcut.activated.connect(self.view.reload)
        self._reload_shortcut = reload_shortcut

    def set_state(self, state: str):
        """Python entry point for future host integration."""
        import json
        self.view.page().runJavaScript(f"window.setState({json.dumps(state)})")

    def set_view_mode(self, mode: str):
        """Switch between the two standalone preview camera compositions."""
        import json
        self.view.page().runJavaScript(f"window.setViewMode({json.dumps(mode)})")


def main():
    app = QApplication(sys.argv)
    window = OrbPreview()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
