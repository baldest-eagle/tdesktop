"""
Multi-Monitor Display Coordinator, Screen Enumerator, and Display Role Router.
"""

from typing import List, Dict, Any, Optional
from .assertions import GeometryRect


class VirtualScreen:
    """Represents a physical/virtual monitor (QScreen)."""

    def __init__(
        self,
        screen_id: int,
        name: str,
        geometry: GeometryRect,
        is_primary: bool = False,
    ):
        self.screen_id = screen_id
        self.name = name
        self.geometry = geometry
        self.is_primary = is_primary
        self.assigned_role: Optional[str] = None  # "Primary", "StageGrid", "ChatStation", "ActiveSpeakerStage"
        self.pinned_feed_id: Optional[str] = None


class DisplayCoordinatorMock:
    """Manages multi-monitor topology, stage windows, role routing, and screen disconnect fallback."""

    def __init__(self):
        self.screens: Dict[int, VirtualScreen] = {}
        self._init_default_topology()

    def _init_default_topology(self) -> None:
        """Initializes default 2-monitor topology."""
        self.add_screen(1, "Monitor 1 (Primary)", GeometryRect(0, 0, 1920, 1080), is_primary=True)
        self.add_screen(2, "Monitor 2 (Secondary)", GeometryRect(1920, 0, 1920, 1080), is_primary=False)
        self.assign_role(1, "Primary")
        self.assign_role(2, "StageGrid")

    def add_screen(
        self,
        screen_id: int,
        name: str,
        geometry: GeometryRect,
        is_primary: bool = False,
    ) -> VirtualScreen:
        screen = VirtualScreen(screen_id, name, geometry, is_primary)
        self.screens[screen_id] = screen
        return screen

    def remove_screen(self, screen_id: int) -> Optional[VirtualScreen]:
        """Simulates monitor unplug / disconnection."""
        if screen_id not in self.screens:
            return None
        scr = self.screens.pop(screen_id)
        # If removed screen had pinned feeds or stage role, fallback gracefully to primary
        primary = self.get_primary_screen()
        if primary and scr.pinned_feed_id:
            # Fallback pinned feed to primary
            if not primary.pinned_feed_id:
                primary.pinned_feed_id = scr.pinned_feed_id
        return scr

    def get_primary_screen(self) -> Optional[VirtualScreen]:
        for s in self.screens.values():
            if s.is_primary:
                return s
        return next(iter(self.screens.values())) if self.screens else None

    def assign_role(self, screen_id: int, role: str) -> bool:
        if screen_id in self.screens:
            self.screens[screen_id].assigned_role = role
            return True
        return False

    def pin_feed_to_screen(self, screen_id: int, feed_id: str) -> bool:
        if screen_id in self.screens:
            self.screens[screen_id].pinned_feed_id = feed_id
            return True
        return False

    def unpin_feed_from_screen(self, screen_id: int) -> bool:
        if screen_id in self.screens:
            self.screens[screen_id].pinned_feed_id = None
            return True
        return False

    def prompt_target_screen(self, feed_id: str, chosen_screen_id: int) -> bool:
        """Simulates Dual Initial Windows prompt (Screen 1 vs Screen 2)."""
        return self.pin_feed_to_screen(chosen_screen_id, feed_id)
