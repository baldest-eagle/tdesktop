"""
Exact mathematical grid solver oracle for discrete presets, 50/50 splits, and uncapped dynamic grids.
"""

import math
from typing import List, Dict, Tuple, Optional, Any
from .assertions import GeometryRect


class GridSolverOracle:
    """Mathematical reference implementation of Telegram Desktop Group Call Grid Layouts."""

    def __init__(self, skip: int = 4):
        self.skip = skip

    def solve_preset_grid(
        self, width: int, height: int, slot_count: int, participant_count: int
    ) -> List[GeometryRect]:
        """Computes tile bounding boxes for discrete presets (1x1, 2x2, 3x3)."""
        if slot_count not in (1, 4, 9):
            raise ValueError(f"Invalid preset slot count: {slot_count}")

        d = int(math.isqrt(slot_count))
        w_cell = (width - (d - 1) * self.skip) / d
        h_cell = (height - (d - 1) * self.skip) / d

        rects: List[GeometryRect] = []
        for i in range(participant_count):
            if i < slot_count:
                r = i // d
                c = i % d
                x = round(c * (w_cell + self.skip))
                y = round(r * (h_cell + self.skip))
                w = round((c + 1) * w_cell + c * self.skip) - x
                h = round((r + 1) * h_cell + r * self.skip) - y
                rects.append(GeometryRect(x, y, w, h))
            else:
                # Overflow tiles receive empty geometry
                rects.append(GeometryRect(0, 0, 0, 0))
        return rects

    def solve_50_50_split(self, width: int, height: int) -> List[GeometryRect]:
        """Computes side-by-side 50/50 split for exactly 2 participants in dynamic mode."""
        w_half = (width - self.skip) // 2
        r0 = GeometryRect(0, 0, w_half, height)
        r1 = GeometryRect(w_half + self.skip, 0, w_half, height)
        return [r0, r1]

    def solve_dynamic_grid(
        self,
        width: int,
        height: int,
        count: int,
        aspect_ratio: float = 16.0 / 9.0,
    ) -> List[GeometryRect]:
        """Computes optimal dynamic grid layout for N participants."""
        if count <= 0:
            return []
        if count == 1:
            return [GeometryRect(0, 0, width, height)]
        if count == 2:
            return self.solve_50_50_split(width, height)

        # Dynamic uncapped solver: find optimal (cols, rows) minimizing wasted area / letterboxing
        best_cols = 1
        best_rows = count
        best_score = float("inf")

        for cols in range(1, count + 1):
            rows = math.ceil(count / cols)
            w_avail = (width - (cols - 1) * self.skip) / cols
            h_avail = (height - (rows - 1) * self.skip) / rows
            if w_avail <= 0 or h_avail <= 0:
                continue

            current_ratio = w_avail / h_avail
            score = abs(current_ratio - aspect_ratio)
            # Prefer squarer grid layout
            if score < best_score:
                best_score = score
                best_cols = cols
                best_rows = rows

        rects: List[GeometryRect] = []
        w_cell = (width - (best_cols - 1) * self.skip) / best_cols
        h_cell = (height - (best_rows - 1) * self.skip) / best_rows

        for i in range(count):
            r = i // best_cols
            c = i % best_cols
            x = round(c * (w_cell + self.skip))
            y = round(r * (h_cell + self.skip))
            w = round((c + 1) * w_cell + c * self.skip) - x
            h = round((r + 1) * h_cell + r * self.skip) - y
            rects.append(GeometryRect(x, y, w, h))

        return rects


class PinSlotAllocator:
    """Manages persistent pinned participants across layout changes."""

    def __init__(self):
        self.pinned_endpoints: List[str] = []
        self.splitter_ratio: float = 0.50

    def pin(self, endpoint_id: str) -> None:
        if endpoint_id not in self.pinned_endpoints:
            self.pinned_endpoints.append(endpoint_id)

    def unpin(self, endpoint_id: str) -> None:
        if endpoint_id in self.pinned_endpoints:
            self.pinned_endpoints.remove(endpoint_id)

    def toggle_pin(self, endpoint_id: str) -> bool:
        if endpoint_id in self.pinned_endpoints:
            self.pinned_endpoints.remove(endpoint_id)
            return False
        else:
            self.pinned_endpoints.append(endpoint_id)
            return True

    def is_pinned(self, endpoint_id: str) -> bool:
        return endpoint_id in self.pinned_endpoints

    def get_ordered_endpoints(
        self, all_endpoints: List[str]
    ) -> List[Tuple[str, bool]]:
        """Returns endpoints ordered with pinned first, followed by unpinned in original order."""
        res: List[Tuple[str, bool]] = []
        # Pinned first
        for ep in self.pinned_endpoints:
            if ep in all_endpoints:
                res.append((ep, True))
        # Unpinned remaining
        for ep in all_endpoints:
            if ep not in self.pinned_endpoints:
                res.append((ep, False))
        return res

    def set_splitter_ratio(self, ratio: float) -> None:
        self.splitter_ratio = max(0.10, min(0.90, ratio))
