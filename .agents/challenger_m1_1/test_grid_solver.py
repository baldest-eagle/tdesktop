"""
Empirical and Mathematical Test Oracle for Dynamic Grid Layout Solver in calls_group_viewport.cpp
"""
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

def safe_round(val: float) -> int:
    # std::round in C++ rounds half-way cases away from zero
    if val >= 0:
        return int(math.floor(val + 0.5))
    else:
        return int(math.ceil(val - 0.5))

@dataclass
class QRect:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    def is_empty(self) -> bool:
        return self.w <= 0 or self.h <= 0

    def right(self) -> int:
        return self.x + self.w

    def bottom(self) -> int:
        return self.y + self.h

@dataclass
class QSize:
    w: int = 0
    h: int = 0

    def scaled(self, width: int, height: int, keep_aspect: bool = True) -> 'QSize':
        if self.w <= 0 or self.h <= 0 or width <= 0 or height <= 0:
            return QSize(0, 0)
        # Qt::KeepAspectRatio: scale to fit within width x height
        factor = min(width / self.w, height / self.h)
        return QSize(safe_round(self.w * factor), safe_round(self.h * factor))

@dataclass
class Geometry:
    size: QSize
    rows: QRect
    columns: QRect

@dataclass
class Layout:
    outer: QSize
    list: List[Geometry]
    use_columns: bool = False

def count_wide(outer_width: int, outer_height: int, tile_sizes: List[QSize], slot_constraint: int, skip: int = 6) -> Layout:
    result = Layout(outer=QSize(outer_width, outer_height), list=[])
    
    # Filter empty sizes
    active_sizes = [s for s in tile_sizes if s.w > 0 and s.h > 0]
    result.list = [Geometry(size=s, rows=QRect(), columns=QRect()) for s in active_sizes]
    
    if len(result.list) == 0:
        return result
    elif len(result.list) == 1:
        result.list[0].rows = QRect(0, 0, outer_width, outer_height)
        result.list[0].columns = QRect(0, 0, outer_width, outer_height)
        return result

    count = len(result.list)
    sizes = result.list

    if count == 2 and slot_constraint == 0:
        half_w = (outer_width - skip) // 2
        sizes[0].columns = sizes[0].rows = QRect(0, 0, half_w, outer_height)
        sizes[1].columns = sizes[1].rows = QRect(
            half_w + skip,
            0,
            outer_width - half_w - skip,
            outer_height
        )
        result.use_columns = True
        return result

    fixed_grid_dim = 1 if slot_constraint == 1 else (2 if slot_constraint == 4 else (3 if slot_constraint == 9 else 0))

    if fixed_grid_dim > 0:
        cols = fixed_grid_dim
        rows = fixed_grid_dim
        max_visible = cols * rows
        visible_count = min(count, max_visible)
        cell_w = (outer_width - (cols - 1) * skip) / float(cols)
        cell_h = (outer_height - (rows - 1) * skip) / float(rows)

        for i in range(count):
            if i < visible_count:
                c = i % cols
                r = i // cols
                left = safe_round(c * (cell_w + skip))
                top = safe_round(r * (cell_h + skip))
                w = safe_round((c + 1) * cell_w + c * skip) - left
                h = safe_round((r + 1) * cell_h + r * skip) - top
                sizes[i].columns = QRect(left, top, w, h)
                sizes[i].rows = QRect(left, top, w, h)
            else:
                sizes[i].columns = QRect()
                sizes[i].rows = QRect()
        result.use_columns = True
        return result

    slices = int(math.ceil(math.sqrt(float(count))))
    columns_black = 0
    rows_black = 0

    # Columns pass
    index = 0
    columns = slices
    sizew = (outer_width + skip) / float(columns)
    for column in range(columns):
        left = safe_round(column * sizew)
        width = safe_round(column * sizew + sizew - skip) - left
        num_rows = safe_round((count - index) / float(columns - column))
        sizeh = (outer_height + skip) / float(num_rows)
        for row in range(num_rows):
            top = safe_round(row * sizeh)
            height = safe_round(row * sizeh + sizeh - skip) - top
            geom = sizes[index]
            geom.columns = QRect(left, top, width, height)
            scaled = geom.size.scaled(width, height, True)
            if scaled.w < width:
                columns_black += (width - scaled.w) * height
            else:
                columns_black += (height - scaled.h) * width
            index += 1

    # Rows pass
    index = 0
    num_rows_pass = slices
    sizeh = (outer_height + skip) / float(num_rows_pass)
    for row in range(num_rows_pass):
        top = safe_round(row * sizeh)
        height = safe_round(row * sizeh + sizeh - skip) - top
        num_cols = safe_round((count - index) / float(num_rows_pass - row))
        sizew = (outer_width + skip) / float(num_cols)
        for column in range(num_cols):
            left = safe_round(column * sizew)
            width = safe_round(column * sizew + sizew - skip) - left
            geom = sizes[index]
            geom.rows = QRect(left, top, width, height)
            scaled = geom.size.scaled(width, height, True)
            if scaled.w < width:
                rows_black += (width - scaled.w) * height
            else:
                rows_black += (height - scaled.h) * width
            index += 1

    result.use_columns = (columns_black < rows_black)
    return result

def verify_all_test_cases():
    test_counts = [1, 2, 3, 4, 5, 6, 9, 12, 16]
    test_constraints = [0, 1, 4, 9]
    test_dims = [
        (1920, 1080),
        (1921, 1080),
        (1921, 1079),
        (1366, 768),
        (800, 600),
        (320, 240),
        (100, 100)
    ]
    test_skips = [4, 6, 8]
    
    results = []
    
    # 1. Test N=2, slotConstraint=0 exact 50/50 and gap/overlap
    for W, H in test_dims:
        for skip in test_skips:
            sizes = [QSize(1280, 720), QSize(1280, 720)]
            layout = count_wide(W, H, sizes, slot_constraint=0, skip=skip)
            
            rect0 = layout.list[0].columns
            rect1 = layout.list[1].columns
            
            # Check left tile starts at 0
            assert rect0.x == 0, f"Failed: rect0.x != 0 for W={W}, skip={skip}"
            # Check gap is exactly skip
            gap = rect1.x - rect0.right()
            assert gap == skip, f"Failed: gap={gap} != skip={skip} for W={W}"
            # Check right tile lands at outerWidth
            assert rect1.right() == W, f"Failed: rect1.right()={rect1.right()} != W={W}"
            # Check heights
            assert rect0.h == H and rect1.h == H, f"Height mismatch"
            # Check 50/50 width difference is at most 1px (due to integer parity)
            assert abs(rect0.w - rect1.w) <= 1, f"Width asymmetry > 1px: {rect0.w} vs {rect1.w}"

    # 2. Test N=2, slotConstraint=4 is 2x2 grid not 50/50
    for W, H in test_dims:
        for skip in test_skips:
            sizes = [QSize(1280, 720), QSize(1280, 720)]
            layout = count_wide(W, H, sizes, slot_constraint=4, skip=skip)
            
            # In 2x2 grid, tile height is approximately (H - skip) / 2
            rect0 = layout.list[0].columns
            rect1 = layout.list[1].columns
            expected_cell_h = safe_round((H - skip) / 2.0)
            assert abs(rect0.h - expected_cell_h) <= 1, f"slotConstraint=4 intercepted: rect0.h={rect0.h} != {expected_cell_h}"
            assert rect0.y == 0 and rect1.y == 0
            assert rect0.x == 0
            assert rect1.x == rect0.right() + skip
            assert rect1.right() == W

    # 3. Exhaustive test across all N, constraints, dimensions, skips
    passed_cases = 0
    total_cases = 0
    
    for N in test_counts:
        for constraint in test_constraints:
            for W, H in test_dims:
                for skip in test_skips:
                    total_cases += 1
                    tile_sizes = [QSize(1280, 720) for _ in range(N)]
                    layout = count_wide(W, H, tile_sizes, slot_constraint=constraint, skip=skip)
                    
                    geoms = layout.list
                    assert len(geoms) == N, f"Mismatch in returned geometries: {len(geoms)} vs {N}"
                    
                    chosen_rects = [g.columns if layout.use_columns else g.rows for g in geoms]
                    
                    if constraint == 1:
                        # Only 1 visible tile (first one), others empty
                        assert not chosen_rects[0].is_empty()
                        assert chosen_rects[0].x == 0 and chosen_rects[0].y == 0
                        assert chosen_rects[0].w == W and chosen_rects[0].h == H
                        for idx in range(1, N):
                            assert chosen_rects[idx].is_empty(), f"Tile {idx} should be empty for 1x1 slot constraint"
                    elif constraint == 4:
                        # 2x2 grid: up to 4 visible
                        visible = min(N, 4)
                        for idx in range(visible):
                            r = chosen_rects[idx]
                            assert not r.is_empty(), f"Visible tile {idx} empty in 2x2 grid"
                            assert r.x >= 0 and r.y >= 0
                            assert r.right() <= W and r.bottom() <= H
                        for idx in range(visible, N):
                            assert chosen_rects[idx].is_empty(), f"Tile {idx} should be empty in 2x2 grid"
                    elif constraint == 9:
                        # 3x3 grid: up to 9 visible
                        visible = min(N, 9)
                        for idx in range(visible):
                            r = chosen_rects[idx]
                            assert not r.is_empty(), f"Visible tile {idx} empty in 3x3 grid"
                            assert r.x >= 0 and r.y >= 0
                            assert r.right() <= W and r.bottom() <= H
                        for idx in range(visible, N):
                            assert chosen_rects[idx].is_empty(), f"Tile {idx} should be empty in 3x3 grid"
                    elif constraint == 0:
                        # Dynamic layout: all N tiles visible
                        for idx in range(N):
                            r = chosen_rects[idx]
                            assert not r.is_empty(), f"Dynamic tile {idx} is empty for N={N}"
                            assert r.x >= 0 and r.y >= 0
                            assert r.right() <= W and r.bottom() <= H
                    
                    passed_cases += 1
                    
    return total_cases, passed_cases

if __name__ == "__main__":
    total, passed = verify_all_test_cases()
    print(f"ALL TESTS PASSED: {passed} / {total} cases verified successfully.")
