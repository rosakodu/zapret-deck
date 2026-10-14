#!/usr/bin/env python3
"""
Zapret-Deck Desktop Tray Companion.
Provides a native StatusNotifierItem system tray popup for managing
Zapret DPI bypass, strategies, autotune, and WARP VPN without opening Steam Big Picture.
Fully compatible with KDE Plasma Wayland (Steam Deck Desktop Mode), supporting
identical native context menus on BOTH Left-Click and Right-Click.
"""

import sys
import os
import time
import threading
from typing import Optional, Dict, List, Any, Callable

# Ensure plugin root directory is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)
PY_MODULES_DIR = os.path.join(PLUGIN_DIR, "py_modules")
if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_DIR)
if PY_MODULES_DIR not in sys.path:
    sys.path.insert(0, PY_MODULES_DIR)

try:
    from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
    from PyQt6.QtGui import (
        QPixmap, QPainter, QColor, QBrush, QPen, QPainterPath, QImage
    )
    from PyQt6.QtWidgets import QApplication
except ImportError:
    try:
        from PySide6.QtCore import Qt, QTimer, QPoint, Signal as pyqtSignal, QObject
        from PySide6.QtGui import (
            QPixmap, QPainter, QColor, QBrush, QPen, QPainterPath, QImage
        )
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("Error: Neither PyQt6 nor PySide6 is installed.")
        sys.exit(1)

import dbus
import dbus.service
import dbus.mainloop.pyqt6

from tray.api_client import ZapretDeckApiClient


# ─────────────────────────────────────────────────────────────
# Localization
# ─────────────────────────────────────────────────────────────

STRINGS = {
    "ru": {
        "app_title": "Zapret Deck",
        "status_offline": "Демон не отвечает",
        "status_active": "Активен",
        "status_inactive": "Выключен",
        "zapret_label": "Zapret",
        "warp_label": "WARP VPN",
        "action_enable_zapret": "🛡️ Включить Zapret",
        "action_disable_zapret": "🛡️ Выключить Zapret",
        "menu_strategies": "Стратегии обхода",
        "action_autotune": "⚡ Автоподбор стратегии",
        "autotune_in_progress": "Автоподбор в процессе...",
        "action_enable_warp": "🌐 Включить WARP",
        "action_disable_warp": "🌐 Выключить WARP",
        "action_generate_warp": "🔑 Сгенерировать WARP аккаунт",
        "menu_autostart": "Автозапуск в трее",
        "action_exit": "❌ Закрыть трей",
        "notify_zapret_on": "Zapret включен ({strategy})",
        "notify_zapret_off": "Zapret выключен",
        "notify_warp_on": "WARP VPN подключен",
        "notify_warp_off": "WARP VPN отключен",
        "notify_autotune_started": "Автоподбор стратегии запущен...",
        "notify_autotune_done": "Автоподбор завершен: {strategy}",
        "notify_autotune_failed": "Автоподбор не нашел рабочей стратегии",
        "notify_warp_gen_done": "Аккаунт WARP успешно сгенерирован!",
        "notify_warp_gen_fail": "Ошибка генерации аккаунта WARP",
        "strategy_user_suffix": "[Пользовательская]",
    },
    "en": {
        "app_title": "Zapret Deck",
        "status_offline": "Daemon Offline",
        "status_active": "Active",
        "status_inactive": "Inactive",
        "zapret_label": "Zapret",
        "warp_label": "WARP VPN",
        "action_enable_zapret": "🛡️ Enable Zapret",
        "action_disable_zapret": "🛡️ Disable Zapret",
        "menu_strategies": "Bypass Strategies",
        "action_autotune": "⚡ Auto-detect Strategy",
        "autotune_in_progress": "Auto-detecting strategy...",
        "action_enable_warp": "🌐 Enable WARP",
        "action_disable_warp": "🌐 Disable WARP",
        "action_generate_warp": "🔑 Generate WARP Account",
        "menu_autostart": "Autostart Companion",
        "action_exit": "❌ Exit Tray",
        "notify_zapret_on": "Zapret enabled ({strategy})",
        "notify_zapret_off": "Zapret disabled",
        "notify_warp_on": "WARP VPN connected",
        "notify_warp_off": "WARP VPN disconnected",
        "notify_autotune_started": "Auto-detection started...",
        "notify_autotune_done": "Auto-detection complete: {strategy}",
        "notify_autotune_failed": "No working strategy found",
        "notify_warp_gen_done": "WARP account successfully generated!",
        "notify_warp_gen_fail": "Failed to generate WARP account",
        "strategy_user_suffix": "[User]",
    },
}


def get_lang() -> str:
    lang = os.environ.get("LANG", "").lower()
    return "ru" if lang.startswith("ru") else "en"


def tr(key: str, **kwargs) -> str:
    lang = get_lang()
    text = STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text


# ─────────────────────────────────────────────────────────────
# Dynamic Tray Icon Generator
# ─────────────────────────────────────────────────────────────

def create_tray_pixmap(status: str = "inactive", size: int = 64) -> QPixmap:
    """Generates crisp vector-like tray icon with status indicator."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Base shield
    shield_color = QColor(225, 230, 240)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(shield_color))

    margin = size * 0.12
    w = size - 2 * margin
    h = size - 2 * margin

    path = QPainterPath()
    path.moveTo(size / 2, margin)
    path.lineTo(size - margin, margin + h * 0.25)
    path.lineTo(size - margin, margin + h * 0.6)
    path.quadTo(size / 2, size - margin, size / 2, size - margin)
    path.quadTo(margin, margin + h * 0.6, margin, margin + h * 0.6)
    path.lineTo(margin, margin + h * 0.25)
    path.closeSubpath()
    painter.drawPath(path)

    # Inner cutout for shield accent
    inner_color = QColor(26, 32, 44)
    painter.setBrush(QBrush(inner_color))
    inner_path = QPainterPath()
    in_m = size * 0.22
    in_h = size - 2 * in_m
    inner_path.moveTo(size / 2, in_m)
    inner_path.lineTo(size - in_m, in_m + in_h * 0.25)
    inner_path.lineTo(size - in_m, in_m + in_h * 0.55)
    inner_path.quadTo(size / 2, size - in_m, size / 2, size - in_m)
    inner_path.quadTo(in_m, in_m + in_h * 0.55, in_m, in_m + in_h * 0.55)
    inner_path.lineTo(in_m, in_m + in_h * 0.25)
    inner_path.closeSubpath()
    painter.drawPath(inner_path)

    # Status Dot (bottom-right)
    dot_radius = size * 0.20
    dot_cx = size - dot_radius - 2
    dot_cy = size - dot_radius - 2

    if status == "zapret":
        dot_color = QColor(26, 159, 255)  # Steam Blue
    elif status == "warp":
        dot_color = QColor(16, 185, 129)  # Green
    elif status == "both":
        dot_color = QColor(6, 182, 212)   # Cyan / Teal
    elif status == "autotune":
        dot_color = QColor(245, 158, 11)  # Amber / Busy
    elif status == "offline":
        dot_color = QColor(239, 68, 68)   # Red
    else:
        dot_color = QColor(148, 163, 184) # Slate gray

    painter.setPen(QPen(QColor(26, 31, 41), 3))
    painter.setBrush(QBrush(dot_color))
    painter.drawEllipse(QPoint(int(dot_cx), int(dot_cy)), int(dot_radius), int(dot_radius))

    painter.end()
    return pixmap


def pixmap_to_sni_pixmap(pixmap: QPixmap) -> dbus.Struct:
    """Converts a QPixmap to org.kde.StatusNotifierItem IconPixmap ARGB32 network struct."""
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    w, h = image.width(), image.height()
    raw = bytearray()
    for y in range(h):
        for x in range(w):
            p = image.pixel(x, y)
            raw.extend([(p >> 24) & 0xFF, (p >> 16) & 0xFF, (p >> 8) & 0xFF, p & 0xFF])
    return dbus.Struct((dbus.Int32(w), dbus.Int32(h), dbus.ByteArray(raw)))


# ─────────────────────────────────────────────────────────────
# StatusNotifierItem & DBusMenu Adaptors
# ─────────────────────────────────────────────────────────────

class ZapretDeckSNI(dbus.service.Object):
    """
    Standard org.kde.StatusNotifierItem implementation.
    Exports 'ItemIsMenu: True' which forces KDE Plasma to trigger the context
    menu on BOTH Left-Click (ЛКМ) and Right-Click (ПКМ).
    """

    def __init__(self, conn, path, tray_app):
        super().__init__(conn, path)
        self.tray_app = tray_app

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ss', out_signature='v')
    def Get(self, iface, prop):
        return self.GetAll(iface).get(prop, '')

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface):
        if iface == 'org.kde.StatusNotifierItem':
            icon_struct = pixmap_to_sni_pixmap(self.tray_app.current_icon_pixmap)
            return {
                'Category': dbus.String('ApplicationStatus'),
                'Id': dbus.String('zapret-deck'),
                'Title': dbus.String(self.tray_app.current_title),
                'Status': dbus.String('Active'),
                'ItemIsMenu': dbus.Boolean(True),
                'IconName': dbus.String(''),
                'IconPixmap': dbus.Array([icon_struct], signature='(iiay)'),
                'OverlayIconPixmap': dbus.Array([], signature='(iiay)'),
                'AttentionIconPixmap': dbus.Array([], signature='(iiay)'),
                'AttentionIconName': dbus.String(''),
                'AttentionMovieName': dbus.String(''),
                'OverlayIconName': dbus.String(''),
                'IconThemePath': dbus.String(''),
                'WindowId': dbus.Int32(0),
                'Menu': dbus.ObjectPath('/MenuBar'),
                'ToolTip': dbus.Struct((
                    dbus.String(''),
                    dbus.Array([], signature='(iiay)'),
                    dbus.String(self.tray_app.current_tooltip),
                    dbus.String('')
                )),
            }
        return {}

    @dbus.service.method('org.kde.StatusNotifierItem', in_signature='ii')
    def Activate(self, x, y):
        pass

    @dbus.service.method('org.kde.StatusNotifierItem', in_signature='ii')
    def ContextMenu(self, x, y):
        pass

    @dbus.service.method('org.kde.StatusNotifierItem', in_signature='ii')
    def SecondaryActivate(self, x, y):
        pass

    @dbus.service.method('org.kde.StatusNotifierItem', in_signature='is')
    def Scroll(self, delta, dir):
        pass

    @dbus.service.method('org.kde.StatusNotifierItem', in_signature='s')
    def ProvideXdgActivationToken(self, token):
        pass

    @dbus.service.signal('org.kde.StatusNotifierItem')
    def NewTitle(self):
        pass

    @dbus.service.signal('org.kde.StatusNotifierItem')
    def NewIcon(self):
        pass

    @dbus.service.signal('org.kde.StatusNotifierItem')
    def NewToolTip(self):
        pass

    @dbus.service.signal('org.kde.StatusNotifierItem')
    def NewStatus(self, status):
        pass

    @dbus.service.signal('org.kde.StatusNotifierItem')
    def NewMenu(self):
        pass


class ZapretDeckDBusMenu(dbus.service.Object):
    """
    Standard com.canonical.dbusmenu implementation.
    Delivers dynamic menu hierarchies and click events directly to KDE Plasma.
    """

    def __init__(self, conn, path, tray_app):
        super().__init__(conn, path)
        self.tray_app = tray_app
        self.revision = dbus.UInt32(1)

    @dbus.service.method('com.canonical.dbusmenu', in_signature='i', out_signature='b')
    def AboutToShow(self, id):
        return True

    @dbus.service.method('com.canonical.dbusmenu', in_signature='iias', out_signature='u(ia{sv}av)')
    def GetLayout(self, parent_id, recursion_depth, property_names):
        return self.tray_app.get_menu_layout(parent_id, recursion_depth)

    @dbus.service.method('com.canonical.dbusmenu', in_signature='isvu', out_signature='')
    def Event(self, id, eventId, data, timestamp):
        if eventId == 'clicked':
            self.tray_app.trigger_menu_action(id)

    @dbus.service.method('com.canonical.dbusmenu', in_signature='aias', out_signature='a(ia{sv})')
    def GetGroupProperties(self, ids, propertyNames):
        return dbus.Array([], signature=dbus.Signature('(ia{sv})'))

    @dbus.service.method('com.canonical.dbusmenu', in_signature='is', out_signature='v')
    def GetProperty(self, id, property):
        return dbus.String('')

    @dbus.service.signal('com.canonical.dbusmenu', signature='ui')
    def LayoutUpdated(self, revision, parentId):
        pass

    def bump_layout(self):
        self.revision = dbus.UInt32(int(self.revision) + 1)
        self.LayoutUpdated(self.revision, dbus.Int32(0))


# ─────────────────────────────────────────────────────────────
# Background State Signaler
# ─────────────────────────────────────────────────────────────

class StateBridge(QObject):
    state_updated = pyqtSignal(object, object, object)
    show_notification = pyqtSignal(str, str)


# ─────────────────────────────────────────────────────────────
# Tray Application
# ─────────────────────────────────────────────────────────────

class ZapretDeckTrayApp(QObject):
    """Main System Tray controller managing SNI, DBusMenu, state and polling."""

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.client = ZapretDeckApiClient()
        self.bridge = StateBridge()

        # State cache
        self.last_zapret_active: Optional[bool] = None
        self.last_warp_active: Optional[bool] = None
        self.last_autotune_state: Optional[bool] = None
        self.status: Optional[Dict[str, Any]] = None
        self.strategies: List[Dict[str, Any]] = []
        self.desktop_status: Dict[str, Any] = {}

        # Display properties
        self.current_title = tr("app_title")
        self.current_tooltip = f"{tr('app_title')} - {tr('status_inactive')}"
        self.current_icon_pixmap = create_tray_pixmap("inactive", 48)

        # Action registry: ID -> callback
        self.action_callbacks: Dict[int, Callable[[], None]] = {}
        self.next_action_id = 100

        # Submenu mapping: parent_id -> list of child Structs
        self.menu_children_map: Dict[int, List[dbus.Struct]] = {}
        self.root_items: List[dbus.Struct] = []

        # Connect signals
        self.bridge.state_updated.connect(self._apply_state)
        self.bridge.show_notification.connect(self._send_desktop_notification)

        # Setup DBus
        self.session_bus = dbus.SessionBus()
        self.sni = ZapretDeckSNI(self.session_bus, '/StatusNotifierItem', self)
        self.dbusmenu = ZapretDeckDBusMenu(self.session_bus, '/MenuBar', self)

        # Register with KDE Plasma StatusNotifierWatcher
        try:
            watcher = self.session_bus.get_object(
                'org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher'
            )
            watcher_iface = dbus.Interface(watcher, 'org.kde.StatusNotifierWatcher')
            watcher_iface.RegisterStatusNotifierItem(self.session_bus.get_unique_name())
        except Exception as e:
            print(f"[ZapretDeckTray] StatusNotifierWatcher warning: {e}")

        # Background polling timer (every 2.5s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_status_background)
        self.timer.start(2500)

        # Initial poll
        self._poll_status_background()

    def _send_desktop_notification(self, title: str, message: str, timeout_ms: int = 4000):
        """Sends native desktop notification via org.freedesktop.Notifications."""
        try:
            notify_obj = self.session_bus.get_object(
                'org.freedesktop.Notifications', '/org/freedesktop/Notifications'
            )
            notify_iface = dbus.Interface(notify_obj, 'org.freedesktop.Notifications')
            notify_iface.Notify('Zapret Deck', 0, '', title, message, [], {}, timeout_ms)
        except Exception:
            pass

    def _poll_status_background(self):
        """Runs in background thread and emits result via Qt Signal."""
        def _worker():
            status = self.client.get_status()
            strategies = self.client.get_strategies() if status else []
            desktop_status = self.client.get_desktop_status() if status else {}
            self.bridge.state_updated.emit(status, strategies, desktop_status)

        threading.Thread(target=_worker, daemon=True).start()

    def _register_action(self, callback: Callable[[], None]) -> int:
        aid = self.next_action_id
        self.next_action_id += 1
        self.action_callbacks[aid] = callback
        return aid

    def trigger_menu_action(self, action_id: int):
        cb = self.action_callbacks.get(action_id)
        if cb:
            cb()

    def get_menu_layout(self, parent_id: int, recursion_depth: int) -> tuple:
        """Returns the DBusMenu hierarchy according to com.canonical.dbusmenu spec."""
        parent_id_int = int(parent_id)
        if parent_id_int == 0:
            root_props = dbus.Dictionary({
                dbus.String('children-display'): dbus.String('submenu')
            }, signature=dbus.Signature('sv'))
            children = dbus.Array(self.root_items, signature=dbus.Signature('v'))
            root = dbus.Struct((dbus.Int32(0), root_props, children))
            return (self.dbusmenu.revision, root)

        sub_children = self.menu_children_map.get(parent_id_int, [])
        sub_props = dbus.Dictionary({
            dbus.String('children-display'): dbus.String('submenu')
        }, signature=dbus.Signature('sv'))
        sub_root = dbus.Struct((
            dbus.Int32(parent_id_int),
            sub_props,
            dbus.Array(sub_children, signature=dbus.Signature('v'))
        ))
        return (self.dbusmenu.revision, sub_root)

    def _apply_state(
        self,
        status: Optional[Dict[str, Any]],
        strategies: List[Dict[str, Any]],
        desktop_status: Dict[str, Any],
    ):
        """Slot executed strictly on GUI thread. Builds menu and updates icon."""
        self.status = status
        self.strategies = strategies
        self.desktop_status = desktop_status

        self.action_callbacks.clear()
        self.menu_children_map.clear()
        self.next_action_id = 100

        if not status:
            self.current_icon_pixmap = create_tray_pixmap("offline", 48)
            self.current_tooltip = f"{tr('app_title')} - {tr('status_offline')}"
            self.sni.NewIcon()
            self.sni.NewToolTip()

            status_item = dbus.Struct((
                dbus.Int32(1),
                dbus.Dictionary({
                    dbus.String('label'): dbus.String(f"🔴 {tr('status_offline')}"),
                    dbus.String('enabled'): dbus.Boolean(False),
                    dbus.String('visible'): dbus.Boolean(True),
                }, signature=dbus.Signature('sv')),
                dbus.Array([], signature=dbus.Signature('v'))
            ))
            self.root_items = [status_item]
            self.dbusmenu.bump_layout()
            return

        zapret_active = bool(status.get("zapret_active") or status.get("zapret_enabled"))
        warp_active = bool(status.get("warp_active") or status.get("warp_enabled"))
        autotune_in_progress = bool(status.get("autotune_in_progress"))
        current_strategy = status.get("current_strategy", "")
        current_strategy_name = status.get("current_strategy_name", "")

        # Notifications on state transitions
        if self.last_zapret_active is not None and self.last_zapret_active != zapret_active:
            if zapret_active:
                self._send_desktop_notification(
                    tr("app_title"),
                    tr("notify_zapret_on", strategy=current_strategy_name or "Active"),
                    2500,
                )
            else:
                self._send_desktop_notification(
                    tr("app_title"), tr("notify_zapret_off"), 2000
                )
        self.last_zapret_active = zapret_active

        if self.last_warp_active is not None and self.last_warp_active != warp_active:
            if warp_active:
                self._send_desktop_notification(
                    tr("app_title"), tr("notify_warp_on"), 2500
                )
            else:
                self._send_desktop_notification(
                    tr("app_title"), tr("notify_warp_off"), 2000
                )
        self.last_warp_active = warp_active

        if self.last_autotune_state is not None and self.last_autotune_state != autotune_in_progress:
            if not autotune_in_progress and zapret_active:
                self._send_desktop_notification(
                    tr("app_title"),
                    tr("notify_autotune_done", strategy=current_strategy_name or "OK"),
                    4000,
                )
        self.last_autotune_state = autotune_in_progress

        # Icon and Tooltip
        if autotune_in_progress:
            icon_kind = "autotune"
            self.current_tooltip = f"{tr('app_title')} - {tr('autotune_in_progress')}"
        elif zapret_active and warp_active:
            icon_kind = "both"
            self.current_tooltip = f"{tr('app_title')} - Zapret & WARP: {tr('status_active')}"
        elif zapret_active:
            icon_kind = "zapret"
            self.current_tooltip = f"{tr('app_title')} - Zapret: {current_strategy_name or tr('status_active')}"
        elif warp_active:
            icon_kind = "warp"
            self.current_tooltip = f"{tr('app_title')} - WARP: {tr('status_active')}"
        else:
            icon_kind = "inactive"
            self.current_tooltip = f"{tr('app_title')} - {tr('status_inactive')}"

        self.current_icon_pixmap = create_tray_pixmap(icon_kind, 48)
        self.sni.NewIcon()
        self.sni.NewToolTip()

        new_root_items: List[dbus.Struct] = []

        # ── 1. Status Summary Headers ──
        zapret_status_text = (
            f"🔵 Zapret: {tr('status_active')}"
            + (f" ({current_strategy_name[:24]})" if current_strategy_name else "")
            if zapret_active
            else f"⚪ Zapret: {tr('status_inactive')}"
        )
        new_root_items.append(dbus.Struct((
            dbus.Int32(1),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(zapret_status_text),
                dbus.String('enabled'): dbus.Boolean(False),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        warp_status_text = (
            f"🟢 WARP: {tr('status_active')}"
            if warp_active
            else f"⚪ WARP: {tr('status_inactive')}"
        )
        new_root_items.append(dbus.Struct((
            dbus.Int32(2),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(warp_status_text),
                dbus.String('enabled'): dbus.Boolean(False),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # Separator
        new_root_items.append(dbus.Struct((
            dbus.Int32(3),
            dbus.Dictionary({
                dbus.String('type'): dbus.String('separator'),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # ── 2. Zapret Toggle & Strategies ──
        zapret_toggle_label = (
            tr("action_disable_zapret") if zapret_active else tr("action_enable_zapret")
        )
        zapret_toggle_id = self._register_action(
            lambda: self._set_service("zapret", not zapret_active)
        )
        new_root_items.append(dbus.Struct((
            dbus.Int32(zapret_toggle_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(zapret_toggle_label),
                dbus.String('enabled'): dbus.Boolean(not autotune_in_progress),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # Strategies Submenu
        strat_menu_id = 10
        strat_children: List[dbus.Struct] = []
        if strategies:
            for s in strategies:
                s_name = s.get("name", "")
                s_args = s.get("args", "")
                is_current = (s_args == current_strategy)
                prefix = "✔ " if is_current else ""
                label = f"{prefix}{s_name}"

                act_id = self._register_action(lambda a=s_args: self._apply_strategy(a))
                strat_children.append(dbus.Struct((
                    dbus.Int32(act_id),
                    dbus.Dictionary({
                        dbus.String('label'): dbus.String(label),
                        dbus.String('enabled'): dbus.Boolean(not autotune_in_progress),
                        dbus.String('visible'): dbus.Boolean(True),
                    }, signature=dbus.Signature('sv')),
                    dbus.Array([], signature=dbus.Signature('v'))
                )))

        self.menu_children_map[strat_menu_id] = strat_children
        new_root_items.append(dbus.Struct((
            dbus.Int32(strat_menu_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(f"🎯 {tr('menu_strategies')}"),
                dbus.String('children-display'): dbus.String('submenu'),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array(strat_children, signature=dbus.Signature('v'))
        )))

        # Autotune Action
        autotune_label = (
            f"⏳ {tr('autotune_in_progress')}"
            if autotune_in_progress
            else tr("action_autotune")
        )
        autotune_id = self._register_action(self._run_autotune)
        new_root_items.append(dbus.Struct((
            dbus.Int32(autotune_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(autotune_label),
                dbus.String('enabled'): dbus.Boolean(not autotune_in_progress),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # Separator
        new_root_items.append(dbus.Struct((
            dbus.Int32(4),
            dbus.Dictionary({
                dbus.String('type'): dbus.String('separator'),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # ── 3. WARP Controls ──
        warp_toggle_label = (
            tr("action_disable_warp") if warp_active else tr("action_enable_warp")
        )
        warp_toggle_id = self._register_action(
            lambda: self._set_service("warp", not warp_active)
        )
        new_root_items.append(dbus.Struct((
            dbus.Int32(warp_toggle_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(warp_toggle_label),
                dbus.String('enabled'): dbus.Boolean(True),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        gen_warp_id = self._register_action(self._generate_warp)
        new_root_items.append(dbus.Struct((
            dbus.Int32(gen_warp_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(tr("action_generate_warp")),
                dbus.String('enabled'): dbus.Boolean(True),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # Separator
        new_root_items.append(dbus.Struct((
            dbus.Int32(5),
            dbus.Dictionary({
                dbus.String('type'): dbus.String('separator'),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # ── 4. Autostart Toggle ──
        is_autostart = bool(desktop_status.get("autostart"))
        autostart_prefix = "✔ " if is_autostart else "☐ "
        autostart_id = self._register_action(
            lambda: self._toggle_autostart(not is_autostart)
        )
        new_root_items.append(dbus.Struct((
            dbus.Int32(autostart_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(f"{autostart_prefix}{tr('menu_autostart')}"),
                dbus.String('enabled'): dbus.Boolean(True),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # Separator
        new_root_items.append(dbus.Struct((
            dbus.Int32(6),
            dbus.Dictionary({
                dbus.String('type'): dbus.String('separator'),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        # ── 5. Exit Action ──
        exit_id = self._register_action(self._exit_tray)
        new_root_items.append(dbus.Struct((
            dbus.Int32(exit_id),
            dbus.Dictionary({
                dbus.String('label'): dbus.String(tr("action_exit")),
                dbus.String('enabled'): dbus.Boolean(True),
                dbus.String('visible'): dbus.Boolean(True),
            }, signature=dbus.Signature('sv')),
            dbus.Array([], signature=dbus.Signature('v'))
        )))

        self.root_items = new_root_items
        self.dbusmenu.bump_layout()

    def _set_service(self, service: str, enabled: bool):
        def _worker():
            self.client.set_service_state(service, enabled)
            time.sleep(0.4)
            self._poll_status_background()
        threading.Thread(target=_worker, daemon=True).start()

    def _apply_strategy(self, strategy: str):
        def _worker():
            self.client.apply_strategy(strategy)
            self.client.set_service_state("zapret", True)
            time.sleep(0.4)
            self._poll_status_background()
        threading.Thread(target=_worker, daemon=True).start()

    def _run_autotune(self):
        self._send_desktop_notification(
            tr("app_title"), tr("notify_autotune_started"), 3000
        )
        def _worker():
            self.client.start_autotune()
            time.sleep(0.5)
            self._poll_status_background()
        threading.Thread(target=_worker, daemon=True).start()

    def _generate_warp(self):
        def _worker():
            success = self.client.generate_warp()
            if success:
                self.bridge.show_notification.emit(
                    tr("app_title"), tr("notify_warp_gen_done")
                )
            else:
                self.bridge.show_notification.emit(
                    tr("app_title"), tr("notify_warp_gen_fail")
                )
            time.sleep(0.4)
            self._poll_status_background()
        threading.Thread(target=_worker, daemon=True).start()

    def _toggle_autostart(self, enable: bool):
        def _worker():
            self.client.set_autostart(enable)
            time.sleep(0.3)
            self._poll_status_background()
        threading.Thread(target=_worker, daemon=True).start()

    def _exit_tray(self):
        self.app.quit()


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    try:
        dbus.mainloop.pyqt6.DBusQtMainLoop(set_as_default=True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ZapretDeckTray")

    tray = ZapretDeckTrayApp(app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
