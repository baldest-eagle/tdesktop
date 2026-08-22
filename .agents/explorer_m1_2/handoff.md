# Handoff Report: Dynamic Grid Layout Solver (50/50 Split Condition)

## 1. Observation
- **Target File**: `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
- **Target Function**: `Viewport::Layout Viewport::countWide(int outerWidth, int outerHeight) const` (Lines 510–673)
- **Observed Code Snippet (Lines 560–585)**:
  ```cpp
  const auto slotConstraint = _slotCount.current();
  const auto fixedGridDim = (slotConstraint == 1)
      ? 1
      : (slotConstraint == 4)
      ? 2
      : (slotConstraint == 9)
      ? 3
      : 0;

  if (fixedGridDim > 0) {
      const auto cols = fixedGridDim;
      const auto rows = fixedGridDim;
      const auto maxVisible = cols * rows;
      const auto visibleCount = std::min(count, maxVisible);
      const auto cellW = (outerWidth - (cols - 1) * skip) / float64(cols);
      const auto cellH = (outerHeight - (rows - 1) * skip) / float64(rows);

      // Special case: 2 feeds -> 50/50 split across the screen
      if (count == 2 && slotConstraint == 0) {
          const auto halfW = (outerWidth - skip) / 2;
          sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
          sizes[1].columns = sizes[1].rows = { halfW + skip, 0, halfW, outerHeight };
          result.useColumns = true;
          return result;
      }
  ```
- **Observed Behavior**:
  - In dynamic layout mode, `_slotCount` is `0` (`slotConstraint == 0`), which yields `fixedGridDim = 0`.
  - The branch `if (fixedGridDim > 0)` at line 569 evaluates to `false`.
  - Lines 578–584 containing `if (count == 2 && slotConstraint == 0)` are located inside `if (fixedGridDim > 0)` and cannot be reached.
  - Execution falls through to the dynamic aspect ratio solver at line 606 (`slices = int(std::ceil(std::sqrt(float64(count))))`), which computes `columnsBlack` vs `rowsBlack`.
  - For standard landscape aspect-ratio video feeds, `rowsBlack` often ends up lower than `columnsBlack`, setting `result.useColumns = false` and stacking the 2 feeds horizontally (top and bottom) instead of splitting them 50/50 side-by-side.
  - In addition, the right-side width calculation `sizes[1] = { halfW + skip, 0, halfW, outerHeight }` truncates when `(outerWidth - skip)` is odd, leaving a 1px gap on the right boundary.

---

## 2. Logic Chain
1. `_slotCount` is the reactive variable representing fixed slot grid modes (`0` = Dynamic, `1` = 1x1, `4` = 2x2, `9` = 3x3) as observed in `calls_group_viewport.h:240` and `calls_group_panel.cpp:867`.
2. `fixedGridDim` evaluates to `0` whenever `slotConstraint == 0` (Dynamic mode) per line 561–567.
3. The enclosing check `if (fixedGridDim > 0)` at line 569 is entered if and only if `slotConstraint > 0`.
4. The inner condition `if (count == 2 && slotConstraint == 0)` at line 578 requires `slotConstraint == 0`.
5. Since `slotConstraint > 0` and `slotConstraint == 0` cannot both be true simultaneously, lines 578–584 are unreachable dead code.
6. The unhandled 2-feed dynamic case falls through to the multi-feed solver (lines 606–672), which makes orientation decisions based on minimizing black letterboxing rather than enforcing the required 50/50 side-by-side split.
7. Relocating the 50/50 split check before `if (fixedGridDim > 0)` allows it to execute whenever `count == 2 && slotConstraint == 0`, returning the side-by-side geometry immediately.
8. Computing `sizes[1]` width as `outerWidth - halfW - skip` ensures the full viewport width is filled regardless of integer odd/even parity.
9. All other counts ($1$, $3$, $4+$, and any count with fixed slot constraints $1, 4, 9$) bypass this check and continue executing their respective layout paths without alteration.

---

## 3. Caveats
- **Animation Transitions**: The 50/50 split correctly sets both `columns` and `rows` and sets `result.useColumns = true`, which is compatible with `Viewport::applyLarge()` (lines 410–475) and `Viewport::updateTilesAnimated()` (lines 477–508) during large tile toggle animations.
- **Narrow Mode**: This change exclusively governs wide/grid mode (`Viewport::countWide`). Narrow viewports (below `st::groupCallNarrowMembersWidth`) use `Viewport::updateTilesGeometryNarrow` which stacks feeds in a vertical carousel list.
- **No other caveats**: The fix is self-contained and strictly improves layout determinism.

---

## 4. Conclusion
- The bug is caused by nesting the dynamic mode check (`slotConstraint == 0`) inside a guard that requires `slotConstraint > 0` (`if (fixedGridDim > 0)`).
- **Exact Fix**:
  Move the 50/50 split condition to top-level in `Viewport::countWide` (before `fixedGridDim` check) and adjust the second feed width calculation:
  ```cpp
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

---

## 5. Verification Method
1. **Source Inspection**:
   Inspect `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp` lines 555–605 to verify that `count == 2 && slotConstraint == 0` is reached before `fixedGridDim > 0`.
2. **Logic & Arithmetic Verification**:
   - For $N=1$: `sizes.size() == 1` branch returns `{ 0, 0, outerWidth, outerHeight }`.
   - For $N=2, \text{slotConstraint}=0$: Returns `{ 0, 0, halfW, outerHeight }` and `{ halfW + skip, 0, outerWidth - halfW - skip, outerHeight }`. Check sum: $halfW + skip + (outerWidth - halfW - skip) = outerWidth$.
   - For $N=2, \text{slotConstraint}=4$: Skips branch, enters `fixedGridDim == 2`, returns top 2 cells of 2x2 grid.
   - For $N=3, \text{slotConstraint}=0$: Skips branch, enters dynamic aspect solver.
   - For $N=4, \text{slotConstraint}=0$: Skips branch, enters dynamic aspect solver (2x2 grid).
3. **Build & Integration Test**:
   Run repository build command to verify compilation:
   ```bash
   cmake --build out --config Debug --target Telegram
   ```
