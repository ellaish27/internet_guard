"""
InternetGuard - internet access gate
Blocks outbound internet access on this PC until a voucher code is entered.
Must be run as Administrator.

Single-instance behavior: if the app is launched again while already running
(e.g. the person double-clicks the taskbar/Start Menu icon), the existing
instance's voucher popup is brought to the front instead of a second copy
starting up and fighting over the firewall rule.
"""
import os
import sys
from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu

from common import db, network_controller
from common.gate_window import GateWindow
from common.overlay_widget import OverlayWidget
from common.session_manager import SessionManager
from common.admin_panel import open_admin_panel

SINGLE_INSTANCE_KEY = "InternetGuard-SingleInstance-MIS26"

# When bundled with Nuitka/PyInstaller, bundled data sits next to the
# executable; when run from source, it sits next to this file.
_BASE_DIR = os.path.dirname(os.path.abspath(getattr(sys, "frozen", False) and sys.executable or __file__))
ICON_ICO_PATH = os.path.join(_BASE_DIR, "icon.ico")
ICON_PNG_PATH = os.path.join(_BASE_DIR, "icon.png")


def _make_icon() -> QIcon:
    # Prefer the real branded icon (InternetGuard 2026 / Dain Corp shield
    # artwork). .ico is preferred on Windows since it carries multiple
    # resolutions for taskbar/tray/titlebar; .png is the fallback so this
    # still works if only one asset is present. Falls back to a plain
    # colored square if neither file is found, so the app never crashes
    # over a missing icon.
    for path in (ICON_ICO_PATH, ICON_PNG_PATH):
        if os.path.isfile(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("#4f8cff"))
    return QIcon(pixmap)


class InternetGuardApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setWindowIcon(_make_icon())
        db.init_db()
        self.gate = GateWindow()
        self.overlay = OverlayWidget()
        self.session = SessionManager()
        self.gate.unlocked.connect(self._on_unlocked)
        self.gate.admin_requested.connect(self._on_admin_requested)
        self.session.tick.connect(self.overlay.update_time)
        self.session.warning_triggered.connect(self._on_warning)
        self.session.session_expired.connect(self._on_expired)
        self._build_tray_icon()
        self._local_server: QLocalServer | None = None

    def _build_tray_icon(self):
        # The gate popup can be closed without unblocking the network
        # (see gate_window.closeEvent), so this tray icon is the only way
        # to bring the voucher prompt back once it's dismissed. There is
        # deliberately no Quit/Exit option here -- stopping the app is an
        # admin-authenticated action only (see admin_panel.py), not
        # something reachable from the plain tray menu.
        self.tray = QSystemTrayIcon(_make_icon(), self.app)
        self.tray.setToolTip("InternetGuard")

        menu = QMenu()
        show_action = menu.addAction("Enter voucher code")
        show_action.triggered.connect(self._show_gate_or_overlay)
        admin_action = menu.addAction("Admin")
        admin_action.triggered.connect(self._on_admin_requested)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _show_gate_or_overlay(self):
        if network_controller.is_blocked():
            self.gate.show()
        else:
            self.overlay.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_gate_or_overlay()

    def _on_admin_requested(self):
        open_admin_panel()

    def _on_unlocked(self, session_id: int, duration_minutes: int):
        self.gate.hide()
        network_controller.unblock_internet()
        self.session.start_session(session_id, duration_minutes)
        self.overlay.show()

    def _on_warning(self, seconds_remaining: int):
        minutes = seconds_remaining // 60
        QMessageBox.warning(
            None, "InternetGuard",
            f"Internet access will end in about {minutes} minute(s)."
        )

    def _on_expired(self):
        self.overlay.hide()
        network_controller.block_internet()
        self.gate.show()

    def _start_single_instance_listener(self):
        # A second launch connects to this socket and immediately
        # disconnects -- that alone is enough to trigger newConnection,
        # which we use as the signal to re-show the gate/overlay.
        self._local_server = QLocalServer()
        self._local_server.newConnection.connect(self._show_gate_or_overlay)
        QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
        self._local_server.listen(SINGLE_INSTANCE_KEY)

    def run(self):
        # If another instance is already listening, this is a re-launch
        # (e.g. the person clicked the taskbar/Start Menu icon again).
        # Signal it to show the popup, then exit this second process --
        # don't touch the firewall or spawn a second tray icon.
        probe = QLocalSocket()
        probe.connectToServer(SINGLE_INSTANCE_KEY)
        if probe.waitForConnected(200):
            probe.disconnectFromServer()
            sys.exit(0)

        if not network_controller.is_admin():
            QMessageBox.critical(
                None, "InternetGuard",
                "InternetGuard must be run as Administrator to control the firewall."
            )
            sys.exit(1)

        self._start_single_instance_listener()

        resumed = self.session.load_active_session()
        if resumed:
            network_controller.unblock_internet()
            self.overlay.show()
        else:
            network_controller.block_internet()
            self.gate.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    InternetGuardApp().run()
