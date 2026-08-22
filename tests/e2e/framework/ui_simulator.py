"""
UI Simulator, Floating Overlay State Machine, and Main Menu / Context Controller.
"""

from typing import List, Dict, Any, Optional, Tuple
from .assertions import GeometryRect


class FloatingOverlaySimulator:
    """Simulates the transparent top-most companion overlay (Features 25-30, 44)."""

    def __init__(self, x: int = 100, y: int = 100, width: int = 400, height: int = 600):
        self.geometry = GeometryRect(x, y, width, height)
        self.visible: bool = False
        self.opacity: float = 0.70  # Default initial opacity
        self.frameless: bool = True
        self.stays_on_top: bool = True
        self.translucent_background: bool = True
        self.mouse_passthrough: bool = False
        self.search_query: str = ""
        self.chat_messages: List[Dict[str, Any]] = []

    def toggle_visibility(self) -> bool:
        """Toggled by Ctrl+Shift+T."""
        self.visible = not self.visible
        return self.visible

    def dismiss(self) -> None:
        """Dismissed by Escape key."""
        self.visible = False

    def adjust_opacity(self, delta_wheel: int) -> float:
        """Adjusts opacity via Ctrl + Wheel up/down (step 0.05 clamped to [0.20, 1.00])."""
        step = 0.05 if delta_wheel > 0 else -0.05
        self.opacity = max(0.20, min(1.00, round(self.opacity + step, 2)))
        return self.opacity

    def drag_move(self, dx: int, dy: int) -> GeometryRect:
        """Moves overlay canvas by delta coordinates."""
        self.geometry.x += dx
        self.geometry.y += dy
        return self.geometry

    def resize(self, new_width: int, new_height: int) -> GeometryRect:
        self.geometry.width = max(100, new_width)
        self.geometry.height = max(100, new_height)
        return self.geometry

    def set_search_query(self, query: str) -> List[Dict[str, Any]]:
        self.search_query = query.strip().lower()
        if not self.search_query:
            return self.chat_messages
        return [
            m
            for m in self.chat_messages
            if self.search_query in m.get("text", "").lower()
        ]


class MenuControllerSimulator:
    """Simulates Main Menu, Context Menus, and Calls Submenu."""

    def __init__(self, support_mode: bool = False):
        self.support_mode = support_mode
        self.menu_items: List[Dict[str, Any]] = []
        self._build_main_menu()

    def _build_main_menu(self) -> None:
        self.menu_items = [
            {"id": "my_profile", "text": "My Profile", "icon": "profile"},
        ]
        if not self.support_mode:
            self.menu_items.append(
                {
                    "id": "wallet",
                    "text": "Wallet",
                    "icon": "wallet",
                    "badge": "NEW",
                    "badge_color": "#28a745",
                }
            )
        self.menu_items.extend(
            [
                {"id": "bots", "text": "Bots", "icon": "bots"},
                {"id": "separator_1", "type": "separator"},
                {"id": "new_group", "text": "New Group", "icon": "group"},
                {"id": "new_channel", "text": "New Channel", "icon": "channel"},
                {"id": "contacts", "text": "Contacts", "icon": "contacts"},
                {"id": "calls", "text": "Calls", "icon": "calls", "has_submenu": True},
                {"id": "saved_messages", "text": "Saved Messages", "icon": "saved"},
            ]
        )

    def get_calls_submenu(self, active_group_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generates the Calls submenu structure with dynamic active group calls."""
        submenu = [
            {"id": "header_groupcalls", "type": "header", "text": "Group Calls"},
        ]
        for gc in active_group_calls:
            submenu.append(
                {
                    "id": f"gc_{gc.get('peer_id')}",
                    "text": gc.get("title", ""),
                    "peer_id": gc.get("peer_id"),
                    "icon": "group",
                }
            )
        submenu.extend(
            [
                {"id": "sep_gc", "type": "separator"},
                {"id": "start_call", "text": "Start Call", "icon": "create_call"},
                {"id": "sep_hist", "type": "separator"},
                {"id": "call_history", "text": "Calls", "icon": "history"},
            ]
        )
        return submenu


class CallWindowControlsSimulator:
    """Simulates Call window UI controls, hover states, and wide-mode cleanups."""

    def __init__(self):
        self.panel_mode: str = "Narrow"  # "Narrow" or "Wide" or "Grid"
        self.grid_mode_enabled: bool = False
        self.chat_panel_visible: bool = False
        self.hover_controls_visible: bool = False
        self.pip_preview_hidden: bool = True
        self.floating_center_controls_visible: bool = True
        self.call_cancel_ripple_color: str = "#c04646"

    def set_panel_mode(self, mode: str) -> None:
        self.panel_mode = mode
        if mode in ("Wide", "Grid"):
            # Wide/grid mode cleans up obstructing buttons in center
            self.floating_center_controls_visible = False
        else:
            self.floating_center_controls_visible = True

    def toggle_chat_panel(self) -> bool:
        self.chat_panel_visible = not self.chat_panel_visible
        return self.chat_panel_visible

    def toggle_grid_mode(self) -> bool:
        self.grid_mode_enabled = not self.grid_mode_enabled
        if self.grid_mode_enabled:
            self.set_panel_mode("Grid")
        else:
            self.set_panel_mode("Narrow")
        return self.grid_mode_enabled

    def on_titlebar_close_clicked(self) -> str:
        """Wires titlebar close event directly to hangup."""
        return "HANGUP_CALL"
