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
                {"id": "saved_messages", "text": "Saved Messages", "icon": "saved"},
            ]
        )

    def get_calls_submenu(self, active_group_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deprecated: the main-menu Calls button was replaced by a chat folder.

        Retained only so legacy imports fail loudly with a clear message instead of
        an `AttributeError` on a missing method.
        """
        raise NotImplementedError(
            "The main-menu 'Calls' submenu no longer exists; use ChatFiltersSimulator "
            "and its local-only Calls filter (Data::kCallsFilterId) instead."
        )


class ChatFiltersSimulator:
    """Simulates the chat folder strip / folder menu with the local-only Calls filter.

    Mirrors `Data::ChatFilters` after the main-menu Calls button was removed and
    replaced by a pseudo-folder: the Calls filter is never part of the persisted
    folder list, it is synthesized into `displayList()` right after "All" and is
    pinned, so reordering can never move it.
    """

    ALL_FILTER_ID = 0
    CALLS_FILTER_ID = -2  # Data::kCallsFilterId

    def __init__(self, custom_folders: Optional[List[Dict[str, Any]]] = None):
        self._list: List[Dict[str, Any]] = [
            {"id": int(f["id"]), "title": f.get("title", "")}
            for f in (custom_folders or [])
        ]
        self.active_id: int = self.ALL_FILTER_ID
        self.calls_members: List[int] = []

    # --- folder list ---------------------------------------------------

    def list(self) -> List[Dict[str, Any]]:
        """User-created folders only; the Calls filter is never stored here."""
        return [dict(f) for f in self._list]

    def calls_filter(self) -> Dict[str, Any]:
        return {
            "id": self.CALLS_FILTER_ID,
            "title": "Calls",
            "local_only": True,
            "pinned": True,
        }

    def display_list(self) -> List[Dict[str, Any]]:
        """`_list` with the synthetic Calls filter inserted right after "All"."""
        result: List[Dict[str, Any]] = [{"id": self.ALL_FILTER_ID, "title": "All"}]
        result.extend(dict(f) for f in self._list)
        result.insert(1, self.calls_filter())
        return result

    def ids_of_tabs(self) -> List[int]:
        return [f["id"] for f in self.display_list()]

    def has(self) -> bool:
        """`ChatFilters::has()` — user folders only."""
        return len(self._list) > 1

    def has_tabs(self) -> bool:
        """`ChatFilters::hasTabs()` — tab strip / folder menu visibility.

        True even for a default account with no user folders, because the Calls
        filter always contributes a tab.
        """
        return len(self.display_list()) > 1

    def lookup_id(self, select: int) -> int:
        """Folder keyboard shortcuts operate in no-Calls space."""
        if 0 <= select < len(self._list):
            return int(self._list[select]["id"])
        return self.ALL_FILTER_ID

    # --- ordering ------------------------------------------------------

    def reorder(self, order: List[int]) -> List[int]:
        """Applies a persisted folder order (Calls id already stripped)."""
        stripped = [fid for fid in order if fid != self.CALLS_FILTER_ID]
        by_id = {int(f["id"]): f for f in self._list}
        ordered = [by_id[fid] for fid in stripped if fid in by_id]
        rest = [f for f in self._list if int(f["id"]) not in stripped]
        self._list = ordered + rest
        return self.ids_of_tabs()

    def save_order(self, display_order: List[int]) -> List[int]:
        """`Api::SaveOrder` must never persist the synthetic Calls id."""
        return [fid for fid in display_order if fid != self.CALLS_FILTER_ID]

    def calls_index(self) -> int:
        """The Calls filter is pinned at index 1, immediately after "All"."""
        return self.ids_of_tabs().index(self.CALLS_FILTER_ID)

    # --- membership ----------------------------------------------------

    def refresh_calls_membership(
        self,
        channels: List[Dict[str, Any]],
    ) -> List[int]:
        """Channels shown in the Calls folder.

        A channel qualifies only when its video chat is not empty, it is present in
        the chat list and it is not archived. Membership is set-backed in the client,
        so duplicates collapse and the original order is preserved.
        """
        members: List[int] = []
        for c in channels:
            if not c.get("call_not_empty"):
                continue
            if not c.get("in_chat_list", True):
                continue
            if c.get("archived", False):
                continue
            channel_id = int(c["id"])
            if channel_id not in members:
                members.append(channel_id)
        self.calls_members = members
        return list(self.calls_members)


class GroupCallFlagOracle:
    """Models peer-flag mutation ordering in `clearGroupCall()`.

    `ChannelData::clearGroupCall()` / `ChatData::clearGroupCall()` must clear
    `CallNotEmpty` *before* firing the `PeerUpdate::Flag::GroupCall` notification.
    With the historical ordering listeners observe a stale "call is still running"
    flag, so the Calls folder keeps the row after a joined call ends.
    """

    def __init__(self, call_not_empty: bool = True, call_active: bool = True):
        self.call_not_empty = call_not_empty
        self.call_active = call_active
        self.notifications = 0
        self.observed_during_notify: Optional[bool] = None

    def has_active_call(self) -> bool:
        """`Data::ChannelHasActiveCall()` / `Data::ChatHasActiveCall()`."""
        return self.call_not_empty

    def clear_group_call(self, notify_first: bool) -> bool:
        """`notify_first=True` reproduces the historical (buggy) ordering."""
        self.observed_during_notify = None
        if notify_first:
            self._notify()
            self._clear_flags()
        else:
            self._clear_flags()
            self._notify()
        return bool(self.observed_during_notify)

    def _clear_flags(self) -> None:
        self.call_active = False
        self.call_not_empty = False

    def _notify(self) -> None:
        self.notifications += 1
        self.observed_during_notify = self.has_active_call()


class ExportActionOracle:
    """Models the service-action mapping used by the export writers."""

    def wallpaper_json(
        self,
        paper_id: int,
        same: bool = False,
        for_both: bool = False,
    ) -> Dict[str, Any]:
        """`Export::JsonWriter` payload for `ActionSetChatWallPaper`."""
        return {
            "action": "set_same_chat_wallpaper" if same else "set_chat_wallpaper",
            "wallpaper_id": paper_id,
            "for_both": for_both,
        }

    def wallpaper_html(self, same: bool = False) -> str:
        """`HtmlWriter::Wrap` service text for `ActionSetChatWallPaper`."""
        return (
            "set the same background for this chat"
            if same
            else "set a new background for this chat"
        )


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
