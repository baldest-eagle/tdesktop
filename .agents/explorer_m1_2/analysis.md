# Technical Analysis: Dynamic Grid Layout Solver & 50/50 Split Condition

## 1. Overview
This report provides a deep architectural and algorithmic analysis of the dynamic grid layout solver in Telegram Desktop's group call viewport (`Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`), specifically focusing on the 50/50 split condition for 2 active feeds.

---

## 2. Codebase Investigation & Observation

### 2.1 File & Function Context
- **Target File**: `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
- **Target Function**: `Viewport::Layout Viewport::countWide(int outerWidth, int outerHeight) const` (Lines 510–673)
- **Target Structs & Variables**:
  - `_slotCount` (`rpl::variable<int>`): Set to 0 in dynamic mode, or 1, 4, 9 in fixed grid mode.
  - `_pinnedEndpoints` (`std::vector<VideoEndpoint>`): Pinned video feeds placed in leading slots.
  - `_tiles` (`std::vector<std::unique_ptr<VideoTile>>`): Active video tiles in the viewport.
  - `skip` (`st::groupCallVideoLargeSkip`): Spacing between adjacent video tiles.

### 2.2 Direct Code Observation (Lines 554–605)
```cpp
554: 
555: 	auto columnsBlack = uint64();
556: 	auto rowsBlack = uint64();
557: 	const auto count = int(sizes.size());
558: 	const auto skip = st::groupCallVideoLargeSkip;
559: 
560: 	const auto slotConstraint = _slotCount.current();
561: 	const auto fixedGridDim = (slotConstraint == 1)
562: 		? 1
563: 		: (slotConstraint == 4)
564: 		? 2
565: 		: (slotConstraint == 9)
566: 		? 3
567: 		: 0;
568: 
569: 	if (fixedGridDim > 0) {
570: 		const auto cols = fixedGridDim;
571: 		const auto rows = fixedGridDim;
572: 		const auto maxVisible = cols * rows;
573: 		const auto visibleCount = std::min(count, maxVisible);
574: 		const auto cellW = (outerWidth - (cols - 1) * skip) / float64(cols);
575: 		const auto cellH = (outerHeight - (rows - 1) * skip) / float64(rows);
576: 
577: 		// Special case: 2 feeds -> 50/50 split across the screen
578: 		if (count == 2 && slotConstraint == 0) {
579: 			const auto halfW = (outerWidth - skip) / 2;
580: 			sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
581: 			sizes[1].columns = sizes[1].rows = { halfW + skip, 0, halfW, outerHeight };
582: 			result.useColumns = true;
583: 			return result;
584: 		}
585: 
586: 		for (auto i = 0; i != count; ++i) {
...
```

---

## 3. Root Cause Analysis

### 3.1 The Dead Code Flaw
1. **Logical Contradiction**:
   - `fixedGridDim` is derived from `slotConstraint`:
     ```cpp
     fixedGridDim = (slotConstraint == 1) ? 1
                  : (slotConstraint == 4) ? 2
                  : (slotConstraint == 9) ? 3
                  : 0;
     ```
   - When dynamic layout mode is active, `slotConstraint == 0`, which results in `fixedGridDim == 0`.
   - Therefore, when `slotConstraint == 0`, `if (fixedGridDim > 0)` at line 569 evaluates to **`false`**.
   - The special-case branch at line 578:
     ```cpp
     if (count == 2 && slotConstraint == 0)
     ```
     is nested **inside** the `if (fixedGridDim > 0)` block.
   - For this inner branch to execute, we would need:
     $$\text{fixedGridDim} > 0 \implies \text{slotConstraint} \in \{1, 4, 9\}$$
     AND simultaneously:
     $$\text{slotConstraint} == 0$$
   - Since $\{1, 4, 9\} \cap \{0\} = \emptyset$, this condition is an absolute mathematical impossibility. Lines 578–584 are **100% dead, unreachable code**.

### 3.2 Dynamic Solver Fallthrough Behavior
Because the 50/50 special case is skipped, execution falls through to the dynamic aspect-ratio layout solver (lines 606–672):
```cpp
const auto slices = int(std::ceil(std::sqrt(float64(count))));
```
For `count == 2`:
- `slices = std::ceil(std::sqrt(2.0)) = 2`.
- The solver computes two alternative layouts:
  1. **Columns layout**: 2 columns $\times$ 1 row. Each feed gets width `(outerWidth - skip)/2` and height `outerHeight`.
  2. **Rows layout**: 1 column $\times$ 2 rows. Each feed gets width `outerWidth` and height `(outerHeight - skip)/2`.
- The solver computes the letterboxing black area for each layout:
  - `columnsBlack`: Black pixel area if placing aspect-ratio scaled video inside tall column cells.
  - `rowsBlack`: Black pixel area if placing aspect-ratio scaled video inside wide row cells.
- The layout with fewer black pixels is chosen: `result.useColumns = (columnsBlack < rowsBlack);`.

**Why 2 active feeds fail to split 50/50 width:**
- Standard desktop screens are landscape (e.g. 16:9, 1920x1080) and typical video feeds are landscape (16:9 or 4:3).
- Splitting a 16:9 screen into 2 columns creates two tall portrait-like cells ($8:9$ aspect ratio), requiring severe letterboxing (top and bottom black bars).
- Splitting into 2 rows creates two wide panoramic cells ($32:9$ aspect ratio).
- Depending on the video track resolutions and window aspect ratio, `rowsBlack` is often $\le$ `columnsBlack`, causing `result.useColumns` to become `false`.
- When `useColumns == false`, the viewport stacks the two feeds vertically (one on top, one on bottom) with large black side pillars, completely failing to provide the intended side-by-side 50/50 split.

### 3.3 Rounding & Pixel Loss Flaw in Original Code
In line 579–581 of the original snippet:
```cpp
const auto halfW = (outerWidth - skip) / 2;
sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
sizes[1].columns = sizes[1].rows = { halfW + skip, 0, halfW, outerHeight };
```
When `outerWidth - skip` is odd:
- Integer division truncates the remainder (e.g., $(1920 - 3) / 2 = 1917 / 2 = 958$).
- Left feed width: $958\text{px}$.
- Skip gap: $3\text{px}$ (from $x=958$ to $x=961$).
- Right feed width: $958\text{px}$ (from $x=961$ to $x=1919$).
- Total width consumed: $958 + 3 + 958 = 1919\text{px}$.
- Viewport width is $1920\text{px}$, leaving a $1\text{px}$ unpainted column at the right edge.
- **Fix**: The second feed's width must be calculated as `outerWidth - halfW - skip` to guarantee pixel-perfect coverage across all window resolutions.

---

## 4. Fix Recommendation & Solution

### 4.1 Placement in Control Flow
The 50/50 split condition must be moved to the top-level layout evaluation, placed immediately after single-tile handling (`sizes.size() == 1`) and before fixed grid evaluation (`if (fixedGridDim > 0)`).

### 4.2 Comprehensive Grid Count Matrix
| Active Feed Count (`count`) | Mode / `slotConstraint` | Active Branch | Resulting Layout |
|:---|:---|:---|:---|
| 0 | Any | `sizes.empty()` | Empty layout (0 tiles) |
| 1 | Any | `sizes.size() == 1` | 1 Full-screen tile (`0, 0, outerWidth, outerHeight`) |
| 2 | Dynamic (`slotConstraint == 0`) | `count == 2 && slotConstraint == 0` | Exact 50/50 side-by-side split (full height) |
| 2 | Fixed 2x2 (`slotConstraint == 4`) | `fixedGridDim > 0` (`fixedGridDim == 2`) | Top 2 quadrants in 2x2 grid (bottom slots empty) |
| 2 | Fixed 1x1 (`slotConstraint == 1`) | `fixedGridDim > 0` (`fixedGridDim == 1`) | 1 Full-screen tile in Slot 0, Feed 1 hidden |
| 3 | Dynamic (`slotConstraint == 0`) | Dynamic Solver (lines 606+) | 2x2 dynamic packing (1 full column/row + 2 split) |
| 3 | Fixed 2x2 (`slotConstraint == 4`) | `fixedGridDim > 0` (`fixedGridDim == 2`) | 3 quadrants filled in 2x2 grid |
| 4 | Dynamic (`slotConstraint == 0`) | Dynamic Solver (lines 606+) | Balanced 2x2 grid |
| 4 | Fixed 2x2 (`slotConstraint == 4`) | `fixedGridDim > 0` (`fixedGridDim == 2`) | Complete 2x2 grid |
| 5+ | Dynamic (`slotConstraint == 0`) | Dynamic Solver (lines 606+) | Dynamic packing with $N$ slices ($3\times3$ etc.) |
| 5+ | Fixed Grid (`slotConstraint == 4/9`) | `fixedGridDim > 0` | First $4$ or $9$ visible, rest hidden |

### 4.3 Proposed Code Diff
```diff
--- a/Telegram/SourceFiles/calls/group/calls_group_viewport.cpp
+++ b/Telegram/SourceFiles/calls/group/calls_group_viewport.cpp
@@ -557,6 +557,18 @@ Viewport::Layout Viewport::countWide(int outerWidth, int outerHeight) const {
 	const auto count = int(sizes.size());
 	const auto skip = st::groupCallVideoLargeSkip;
 	const auto slotConstraint = _slotCount.current();
+
+	if (count == 2 && slotConstraint == 0) {
+		const auto halfW = (outerWidth - skip) / 2;
+		sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
+		sizes[1].columns = sizes[1].rows = {
+			halfW + skip,
+			0,
+			outerWidth - halfW - skip,
+			outerHeight,
+		};
+		result.useColumns = true;
+		return result;
+	}
+
 	const auto fixedGridDim = (slotConstraint == 1)
 		? 1
 		: (slotConstraint == 4)
@@ -574,15 +586,6 @@ Viewport::Layout Viewport::countWide(int outerWidth, int outerHeight) const {
 		const auto cellW = (outerWidth - (cols - 1) * skip) / float64(cols);
 		const auto cellH = (outerHeight - (rows - 1) * skip) / float64(rows);
 
-		// Special case: 2 feeds -> 50/50 split across the screen
-		if (count == 2 && slotConstraint == 0) {
-			const auto halfW = (outerWidth - skip) / 2;
-			sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
-			sizes[1].columns = sizes[1].rows = { halfW + skip, 0, halfW, outerHeight };
-			result.useColumns = true;
-			return result;
-		}
-
 		for (auto i = 0; i != count; ++i) {
 			auto &geometry = sizes[i];
 			if (i < visibleCount) {
```
