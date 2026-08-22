"""
Rich Tasks Checklist Tracker, Debounce Batcher, and Optimistic UI Oracle (Feature 45).
"""

import re
from typing import List, Dict, Any, Optional, Tuple


class ChecklistItem:
    """Represents a single task item in a markdown checklist."""

    def __init__(self, index: int, text: str, completed: bool):
        self.index = index
        self.text = text
        self.completed = completed


class RichTasksOracle:
    """Simulates Rich Tasks interactive checklist parsing, debounce timer, optimistic updates, and rollback."""

    def __init__(self, message_id: int, initial_markdown: str):
        self.message_id = message_id
        self.current_markdown = initial_markdown
        self.server_markdown = initial_markdown
        self.items: List[ChecklistItem] = []
        self._parse_markdown(initial_markdown)

        self.debounce_timer_active: bool = False
        self.debounce_duration_ms: int = 1000  # 1000ms debounce window
        self.timer_remaining_ms: int = 0
        self.pending_save_dispatches: int = 0
        self.history_snapshots: List[str] = [initial_markdown]

    def _parse_markdown(self, text: str) -> None:
        self.items.clear()
        lines = text.split("\n")
        idx = 0
        for line in lines:
            m = re.match(r"^\s*-\s*\[([ xX])\]\s*(.*)$", line)
            if m:
                is_checked = m.group(1).lower() == "x"
                item_text = m.group(2).strip()
                self.items.append(ChecklistItem(idx, item_text, is_checked))
                idx += 1

    def render_markdown(self) -> str:
        """Generates markdown string from current checklist items."""
        lines = []
        for item in self.items:
            box = "[x]" if item.completed else "[ ]"
            lines.append(f"- {box} {item.text}")
        return "\n".join(lines)

    def toggle_item(self, item_index: int) -> bool:
        """Toggles an item state immediately (optimistic local update) and starts/resets 1000ms debounce timer."""
        if 0 <= item_index < len(self.items):
            # Record snapshot for rollback
            self.history_snapshots.append(self.current_markdown)

            self.items[item_index].completed = not self.items[item_index].completed
            self.current_markdown = self.render_markdown()

            # Start or reschedule debounce timer (dirty rescheduling)
            self.debounce_timer_active = True
            self.timer_remaining_ms = self.debounce_duration_ms
            return True
        return False

    def advance_time(self, delta_ms: int) -> Optional[str]:
        """Advances simulated timer; if timer expires, commits changes via EditRichMessage RPC."""
        if not self.debounce_timer_active:
            return None

        self.timer_remaining_ms -= delta_ms
        if self.timer_remaining_ms <= 0:
            self.debounce_timer_active = False
            self.timer_remaining_ms = 0
            self.pending_save_dispatches += 1
            self.server_markdown = self.current_markdown
            return self.current_markdown
        return None

    def rollback_on_error(self) -> None:
        """Reverts local state to last known server-confirmed markdown upon RPC failure."""
        self.current_markdown = self.server_markdown
        self._parse_markdown(self.server_markdown)
        self.debounce_timer_active = False
        self.timer_remaining_ms = 0
