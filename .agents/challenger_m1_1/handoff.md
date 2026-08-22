# Handoff Report — Milestone M1 Grid Layout Solver Challenge

## 1. Observation
- **Inspected File**: `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp` lines 555-677 (`Viewport::countWide`).
- **Dynamic 50/50 Split Logic (lines 561-572)**:
  ```cpp
  const auto slotConstraint = _slotCount.current();
  if (count == 2 && slotConstraint == 0) {
      const auto halfW = (outerWidth - skip) / 2;
      sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
      sizes[1].columns = sizes[1].rows = {
          halfW + skip,
          0,
          outerWidth - halfW - skip,
          outerHeight,
      };
      result.useColumns = true;
      return result;
  }
  ```
- **Fixed Grid Dimension Dispatch (lines 574-580)**:
  ```cpp
  const auto fixedGridDim = (slotConstraint == 1)
      ? 1
      : (slotConstraint == 4)
      ? 2
      : (slotConstraint == 9)
      ? 3
      : 0;
  ```
- **Fixed Grid Solver (lines 582-608)**:
  ```cpp
  if (fixedGridDim > 0) {
      const auto cols = fixedGridDim;
      const auto rows = fixedGridDim;
      const auto maxVisible = cols * rows;
      const auto visibleCount = std::min(count, maxVisible);
      const auto cellW = (outerWidth - (cols - 1) * skip) / float64(cols);
      const auto cellH = (outerHeight - (rows - 1) * skip) / float64(rows);

      for (auto i = 0; i != count; ++i) {
          auto &geometry = sizes[i];
          if (i < visibleCount) {
              const auto c = i % cols;
              const auto r = i / cols;
              const auto left = int(base::SafeRound(c * (cellW + skip)));
              const auto top = int(base::SafeRound(r * (cellH + skip)));
              const auto w = int(base::SafeRound((c + 1) * cellW + c * skip)) - left;
              const auto h = int(base::SafeRound((r + 1) * cellH + r * skip)) - top;
              geometry.columns = { left, top, w, h };
              geometry.rows = { left, top, w, h };
          } else {
              geometry.columns = QRect();
              geometry.rows = QRect();
          }
      }
      result.useColumns = true;
      return result;
  }
  ```
- **Dynamic Partitioning Loop (lines 610-677)**:
  Uses $\text{slices} = \lceil \sqrt{\text{count}} \rceil$ to partition columns and rows, evaluating both orientations (`columns` vs `rows`) and selecting the one with minimized letterbox black bars (`columnsBlack < rowsBlack`).

## 2. Logic Chain
1. **From Observation (lines 561-572)**:
   - For $N=2, \text{slotConstraint}=0$:
     $\text{left}_0 = 0$, $\text{width}_0 = \lfloor (W - S) / 2 \rfloor$, $\text{right}_0 = \lfloor (W - S) / 2 \rfloor$.
     $\text{left}_1 = \lfloor (W - S) / 2 \rfloor + S$, $\text{width}_1 = W - \lfloor (W - S) / 2 \rfloor - S$, $\text{right}_1 = W$.
   - The gap between tiles is $\text{left}_1 - \text{right}_0 = S \equiv \text{skip}$.
   - The total width is $\text{right}_1 - \text{left}_0 = W \equiv \text{outerWidth}$.
   - This holds identically for any $W \ge S$, whether $W$ and $S$ are even or odd. No 1px gap or overlap occurs.

2. **From Observation (lines 561, 574-580)**:
   - For $N=2, \text{slotConstraint}=4$, the predicate `count == 2 && slotConstraint == 0` evaluates to `false` because `slotConstraint == 4 != 0`.
   - Control passes directly to `fixedGridDim = 2`, triggering the 2x2 grid calculation with $\text{cellH} \approx (H - S)/2$, which places the two feeds in the top-left and top-right quadrants without interception by the 50/50 split branch.

3. **From Observation (lines 582-608)**:
   - For any fixed grid dimension $D \in \{1, 2, 3\}$, adjacent columns satisfy:
     $\text{left}(c+1) - \text{right}(c) = \text{round}((c+1)(\text{cellW}+S)) - \text{round}((c+1)\text{cellW}+cS) = S$.
   - The rightmost column boundary is $\text{round}(D \cdot \text{cellW} + (D-1)S) = \text{round}(W) = W$.
   - Invisible tiles ($i \ge D^2$) receive empty `QRect()`.

4. **From Observation (lines 610-677)**:
   - For dynamic mode with $N \in \{3, 4, 5, 6, 9, 12, 16\}$, `slices` correctly computes grid bounds, cleanly partitioning all $N$ feeds with 0 lost tiles, 0 overlaps, and exact $S$-pixel gutters.

## 3. Caveats
- The solver assumes $W \ge S$ and $H \ge S$, which is guaranteed by the UI minimum viewport constraints ($W \ge 280\text{px}$).
- Aspect ratio selection optimizes for visual black-bar area; different video source aspect ratios are letterboxed/pillarboxed within their assigned tiles using `Qt::KeepAspectRatio`.

## 4. Conclusion
- **Verdict**: **APPROVE**
- The solver implementation in `calls_group_viewport.cpp` fulfills all functional and boundary requirements:
  - Exact 50/50 horizontal split for $N=2, \text{slotConstraint}=0$ without 1px gap/overlap.
  - Zero false-interception for $N=2, \text{slotConstraint}=4$.
  - Complete mathematical consistency for all $N \in [1..16]$ and slot constraints $S_c \in \{0, 1, 4, 9\}$ across odd and even viewport dimensions.

## 5. Verification Method
- Execute the Python oracle script:
  `py c:\Users\kyleh\tdesktop\.agents\challenger_m1_1\test_grid_solver.py`
  (756 parameterized test cases covering all dimensions, skips, counts, and constraints).
- Inspect `c:\Users\kyleh\tdesktop\.agents\challenger_m1_1\challenge.md` for full test proof and results matrix.
