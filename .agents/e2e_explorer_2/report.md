# E2E Test Specification: Telegram Desktop Fork (Categories 5–8 / Features 16–37)

**Document Version**: 1.0.0  
**Target Subsystems**: Grid & Pinned Layouts, Transparent Overlay Canvas, Embedded In-Meeting Chat & Search, Participant Sidebar & Listen-Only Controls  
**Author**: Explorer 2 (E2E Testing Track)  
**Date**: August 20, 2026  

---

## 1. Executive Summary & Scope Definition

This technical specification details the complete Tier 1 E2E Test Suite for **Categories 5 through 8 (Features 16 to 37)** of the Telegram Desktop fork repository. 

Across these 22 features, **110 distinct test specifications (5 tests per feature)** are rigorously designed with explicit preconditions, input/action sequences, expected outputs, layout oracle geometric assertions, overlay state models, mock engine requirements, and edge case resilience rules.

### Scope Inventory

| Category | Features | Feature IDs | Total Tier 1 Tests |
| :--- | :--- | :--- | :---: |
| **Category 5: Grid & Pinned Layouts** | Discrete Presets, 50/50 Split, Uncapped Dynamic Scaling, Pin Allocator, Dynamic Pinned Auto-Scaling, Multi-Pin, Resizable Panels, Grid Unpinning, Context Menu Pin | Features 16 – 24 | 45 |
| **Category 6: Transparent Overlay Canvas** | Frameless Window, Ctrl+Shift+T Shortcut, Opacity Ctrl+Wheel, Draggable Canvas & Esc Dismissal | Features 25 – 28 | 20 |
| **Category 7: Embedded In-Meeting Chat & Search** | Embedded Chat Resizing (`MessagesUi`), In-Meeting Chat Search | Features 29 – 30 | 10 |
| **Category 8: Participant List & Listen-Only Controls** | Chronological Grid Sort, Alphabetical Sidebar Sort, In-Call Search Bar, Search Quick Actions, Audio Lockout Mode, Mic Controls Removal, Permanent Zero-Mic Invariant | Features 31 – 37 | 35 |
| **Total** | **4 Categories / 22 Features** | **Features 16 – 37** | **110 Test Cases** |

---

## 2. Architectural Foundations & Layout Oracle Models

### 2.1 Grid Layout Solver & Geometry Oracle Models (Features 16, 17, 18)

The grid solver geometry in `calls_group_viewport.cpp` computes non-overlapping tile bounding boxes `(x, y, w, h)` within an outer viewport of dimension `(W, H)`.

#### 1. Discrete Preset Solver (Feature 16)
Given preset slot count $S \in \{1, 4, 9\}$ and tile spacing skip margin $g = \text{st::groupCallVideoLargeSkip}$ (default 4px):
- Dimension dimension $D = \sqrt{S} \in \{1, 2, 3\}$.
- Cell dimensions:
  $$w_{\text{cell}} = \frac{W - (D - 1)g}{D}, \quad h_{\text{cell}} = \frac{H - (D - 1)g}{D}$$
- Tile rectangle for index $i < \min(N, S)$ at row $r = \lfloor i / D \rfloor$, column $c = i \bmod D$:
  $$x_i = \text{round}(c \cdot (w_{\text{cell}} + g)), \quad y_i = \text{round}(r \cdot (h_{\text{cell}} + g))$$
  $$w_i = \text{round}((c + 1)w_{\text{cell}} + c \cdot g) - x_i, \quad h_i = \text{round}((r + 1)h_{\text{cell}} + r \cdot g) - y_i$$
- Overflow tiles ($i \ge S$) receive null geometry: $R_i = \text{QRect}(0, 0, 0, 0)$.

#### 2. Dynamic 50/50 Split Solver (Feature 17)
For $N = 2$ and dynamic mode ($S = 0$):
- $w_{\text{half}} = \lfloor (W - g) / 2 \rfloor$
- Tile 0 (Left): $R_0 = (0, 0, w_{\text{half}}, H)$
- Tile 1 (Right): $R_1 = (w_{\text{half}} + g, 0, w_{\text{half}}, H)$
- Invariant: $R_0 \cap R_1 = \emptyset$, $\text{Area}(R_0) + \text{Area}(R_1) = 2 \cdot w_{\text{half}} \cdot H$.

#### 3. Uncapped Dynamic Solver (Feature 18)
For arbitrary active participant count $N \ge 1$:
- Grid slice count: $K = \lceil \sqrt{N} \rceil$.
- Slices partitioned across columns vs rows to minimize letterbox/pillarbox padding:
  $$\text{useColumns} = (\text{columnsBlack} < \text{rowsBlack})$$
- Invariant: For all pairs $i \ne j$, $R_i \cap R_j = \emptyset$ and $\sum R_i \subseteq [0, W] \times [0, H]$.

---

### 2.2 Persistent Pin Allocator & State Transition System (Features 19, 20, 21, 22, 23, 24)

- **Data Structure**: `std::vector<VideoEndpoint> _pinnedEndpoints` maintaining insertion order, and `base::flat_map<VideoEndpoint, int> _pinnedSlots`.
- **Slot Allocation Rule**:
  - Pinned endpoints are allocated sequentially to leading slots $0, 1, \dots, K-1$.
  - Unpinned feeds are allocated to remaining slots $K, K+1, \dots, N-1$ ordered chronologically by `entryTime()`.
- **Pin Mutation Invariants**:
  - Adding unpinned participant $P_{\text{new}}$ NEVER shifts the slot index of any pinned peer $P \in \text{pinned}$.
  - Unpinning peer at index $j$ shifts subsequent pinned peers $j+1 \dots K-1$ to $j \dots K-2$; pinned peers $< j$ maintain identical indices.

---

### 2.3 Transparent Companion Overlay State Machine (Features 25, 26, 27, 28)

- **Window Model**: Top-level `QWidget` initialized with:
  $$\text{WindowFlags} = \text{Qt::Window} \mid \text{Qt::FramelessWindowHint} \mid \text{Qt::WindowStaysOnTopHint}$$
  $$\text{Attributes} = \text{Qt::WA\_TranslucentBackground} \mid \text{Qt::WA\_ShowWithoutActivating}$$
- **Opacity Range**: $\alpha \in [0.20, 1.00]$, initial $\alpha_0 = 0.70$, adjustment step $\Delta\alpha = \pm 0.05$ on `Ctrl + Wheel`.
- **Interaction Model**:
  - `Ctrl+Shift+T` toggles visibility: $V_{t+1} = \neg V_t$.
  - Dragging with `LeftButton` updates top-left coordinates: $(X_{t+1}, Y_{t+1}) = (X_0 + \Delta X, Y_0 + \Delta Y)$.
  - `Escape` dismisses overlay ($V \to \text{false}$).
  - Mouse-passthrough button sets `Qt::WA_TransparentForMouseEvents`.

---

### 2.4 Listen-Only & Zero-Mic Invariant Architecture (Features 35, 36, 37)

- **Media Engine Invariant (`tgcalls`)**:
  - Audio capture device is NEVER opened (`OpenAudioDevice()` skipped or returns dummy handle).
  - Outgoing RTP stream descriptor `m=audio` in SDP set to `recvonly` or omitted.
  - Outgoing audio packet transmission rate: $\frac{d(\text{AudioPackets})}{dt} \equiv 0$.
- **Call Panel UI Invariant**:
  - Microphone mute/unmute toggle actions are intercepted and discarded (`calls_group_panel.cpp:673`).
  - Sticked microphone onboarding tooltip is permanently suppressed (`calls_group_panel.cpp:245`).
- **Controller Invariant (`calls_group_call.cpp`)**:
  - Client state machine locks `isListenOnly() \equiv \text{true}` throughout call lifecycle.

---

## 3. Test Harness & Mock Architecture Requirements

The Tier 1 E2E test execution framework relies on five specialized mock components:

1. **`CallSimulator`**: Emulates WebRTC group call sessions, active participants, video track size streams (`trackSizeValue()`), participant join timestamps, and audio level streams.
2. **`GridSolverOracle`**: Reference mathematical implementation of `countWide()` and `countGrid()` that computes exact `QRect` matrices given $(W, H, N, S)$ for programmatic equality assertions.
3. **`OverlayStateProbe`**: Inspects top-level Qt window geometry, window flags, translucency attributes, opacity values, and event filter streams.
4. **`SidebarControllerMock`**: Emulates participant list mutations, search query inputs, and context menu action invocations.
5. **`ZeroMicNetworkSpy`**: Intercepts WebRTC SDP exchanges and RTP packet buffers to verify 0 outgoing audio packets.

---

## 4. Comprehensive Tier 1 Test Specifications (Features 16 – 37)

---

### Category 5: Grid & Pinned Layouts (Features 16 – 24)

#### Feature 16: Discrete Layout Presets (1x1, 2x2, 3x3)

##### `TEST-T1-F16-01`: Preset 1x1 Single Focus Tile Full-Viewport Geometry
- **Preconditions**: Active group call with 1 participant publishing 1280x720 video; viewport size = `1000 x 600`.
- **Inputs & Actions**: Call `setSlotCount(1)` on `Viewport` to select the 1x1 preset. Trigger `updateTilesGeometry()`.
- **Expected Outputs**: Viewport allocates exactly 1 visible slot.
- **Layout Oracle Assertions**:
  - Tile 0 geometry: `QRect(0, 0, 1000, 600)`.
  - `tile[0]->geometry() == QRect(0, 0, 1000, 600)`.
  - Zero margin/skip applied.
- **Mock Requirements**: `CallSimulator` with 1 active video endpoint `user_101`.
- **Edge Cases**: Verify aspect ratio preservation within tile bounds while tile container spans full viewport.

##### `TEST-T1-F16-02`: Preset 2x2 Symmetrical 4-Tile Quadrant Partitioning
- **Preconditions**: Group call with 4 active video feeds; viewport size = `1000 x 600`; skip margin = `4px`.
- **Inputs & Actions**: Call `setSlotCount(4)` on `Viewport`.
- **Expected Outputs**: Viewport creates 2 columns and 2 rows ($D=2$).
- **Layout Oracle Assertions**:
  - $w_{\text{cell}} = (1000 - 4)/2 = 498\text{px}$, $h_{\text{cell}} = (600 - 4)/2 = 298\text{px}$.
  - Slot (0,0): `QRect(0, 0, 498, 298)`
  - Slot (1,0): `QRect(502, 0, 498, 298)`
  - Slot (0,1): `QRect(0, 302, 498, 298)`
  - Slot (1,1): `QRect(502, 302, 498, 298)`
  - Overlap check: `Intersect(Slot_i, Slot_j) == QRect()` for all $i \ne j$.
- **Mock Requirements**: `CallSimulator` publishing 4 distinct endpoints `[ep_1, ep_2, ep_3, ep_4]`.
- **Edge Cases**: Verify integer rounding summation matches outer bounding width $498 + 4 + 498 = 1000$.

##### `TEST-T1-F16-03`: Preset 3x3 Symmetrical 9-Tile Matrix Partitioning
- **Preconditions**: Group call with 9 active video feeds; viewport size = `1200 x 900`; skip = `4px`.
- **Inputs & Actions**: Call `setSlotCount(9)`.
- **Expected Outputs**: 3x3 grid with 9 non-overlapping cells.
- **Layout Oracle Assertions**:
  - $w_{\text{cell}} = (1200 - 2 \times 4) / 3 = 397.333\text{px}$, $h_{\text{cell}} = (900 - 2 \times 4) / 3 = 297.333\text{px}$.
  - Tile 0 (0,0): `QRect(0, 0, 397, 297)`
  - Tile 1 (1,0): `QRect(401, 0, 398, 297)`
  - Tile 8 (2,2): `QRect(803, 603, 397, 297)`
  - All 9 tiles visible and active.
- **Mock Requirements**: `CallSimulator` with 9 distinct video streams.
- **Edge Cases**: Verify no sub-pixel drift causing total width/height to exceed viewport boundaries.

##### `TEST-T1-F16-04`: Preset 2x2 Under-Capacity Handling (3 Feeds in 4 Slots)
- **Preconditions**: Group call with 3 active video feeds; viewport size = `1000 x 600`; preset = `2x2` (`setSlotCount(4)`).
- **Inputs & Actions**: Trigger layout refresh.
- **Expected Outputs**: Slots 0, 1, 2 are populated with feeds; Slot 3 remains empty without stretching or distorting remaining tiles.
- **Layout Oracle Assertions**:
  - Tiles 0, 1, 2 receive standard quadrant rects identical to 4-feed layout.
  - Tile count in list = 3; no crash or invalid memory access when accessing slot index 3.
- **Mock Requirements**: `CallSimulator` configured with 3 video endpoints.
- **Edge Cases**: Add 4th feed dynamically and verify it fills slot 3 without moving tiles 0, 1, 2.

##### `TEST-T1-F16-05`: Preset 3x3 Overflow Handling (12 Feeds with 9 Slots)
- **Preconditions**: Group call with 12 active video feeds; preset = `3x3` (`setSlotCount(9)`).
- **Inputs & Actions**: Load 12 participant feeds into `Viewport`.
- **Expected Outputs**: Visible count clamped to $\min(12, 9) = 9$. Tiles 0..8 rendered in 3x3 grid; feeds 9..11 receive `QRect()`.
- **Layout Oracle Assertions**:
  - `tiles[0..8].geometry().isValid() == true`.
  - `tiles[9..11].geometry().isEmpty() == true`.
- **Mock Requirements**: `CallSimulator` with 12 mock endpoints.
- **Edge Cases**: Unpinning/removing tile 2 shifts tile 9 into visible slot 8.

---

#### Feature 17: Dynamic Grid Solver (50/50 Split)

##### `TEST-T1-F17-01`: 2-Feed 50/50 Horizontal Side-by-Side Split Verification
- **Preconditions**: Group call with 2 participants publishing video; dynamic mode (`_slotCount == 0`); viewport = `1200 x 800`; skip = `4px`.
- **Inputs & Actions**: Trigger `updateTilesGeometry()`.
- **Expected Outputs**: Viewport evaluates $N=2$ special case and splits width equally 50/50.
- **Layout Oracle Assertions**:
  - $w_{\text{half}} = (1200 - 4) / 2 = 598\text{px}$.
  - Tile 0: `QRect(0, 0, 598, 800)`.
  - Tile 1: `QRect(602, 0, 598, 800)`.
  - `result.useColumns == true`.
- **Mock Requirements**: `CallSimulator` with 2 video streams.
- **Edge Cases**: Unequal video native resolutions (e.g. 1920x1080 and 720x1280) both fit into equal 598x800 containers.

##### `TEST-T1-F17-02`: Dynamic 1-Feed Auto-Expansion to Full Screen
- **Preconditions**: Group call with 1 participant; dynamic mode.
- **Inputs & Actions**: Set viewport size = `1920 x 1080`.
- **Expected Outputs**: Single tile auto-scales to exact full viewport.
- **Layout Oracle Assertions**:
  - Tile 0: `QRect(0, 0, 1920, 1080)`.
  - Zero margins, zero pillarbox inside tile rect.
- **Mock Requirements**: `CallSimulator` with 1 feed.
- **Edge Cases**: Viewport resize from `1920x1080` to `800x600` immediately resizes Tile 0 to `(0, 0, 800, 600)`.

##### `TEST-T1-F17-03`: Dynamic 3-Feed Aspect-Ratio Optimal Packing
- **Preconditions**: 3 video feeds (16:9 widescreen); viewport = `1200 x 800`.
- **Inputs & Actions**: Execute dynamic grid solver.
- **Expected Outputs**: Solver computes `columnsBlack` vs `rowsBlack` and selects layout with minimal black area.
- **Layout Oracle Assertions**:
  - $K = \lceil \sqrt{3} \rceil = 2$ columns.
  - Column 0: 2 tiles stacked vertically. Column 1: 1 tile spanning full height (or balanced 2+1 rows).
  - All 3 tiles have non-zero geometry, $R_0 \cap R_1 \cap R_2 = \emptyset$.
- **Mock Requirements**: `CallSimulator` providing 3 16:9 video tracks.
- **Edge Cases**: Rotate one video stream to 9:16 portrait and verify solver recalculates optimal layout.

##### `TEST-T1-F17-04`: Dynamic Viewport Resize Reactive Recomputation
- **Preconditions**: 2 feeds in 50/50 split at `1000 x 600`.
- **Inputs & Actions**: Resize parent widget to `1400 x 900`.
- **Expected Outputs**: Geometry recomputes synchronously via `_content->sizeValue()`.
- **Layout Oracle Assertions**:
  - $w_{\text{half}} = (1400 - 4) / 2 = 698\text{px}$.
  - Tile 0: `QRect(0, 0, 698, 900)`.
  - Tile 1: `QRect(702, 0, 698, 900)`.
- **Mock Requirements**: Simulated Qt resize event on viewport widget.
- **Edge Cases**: Rapid continuous resize stream (60 events/sec) produces monotonic coordinate updates without glitching.

##### `TEST-T1-F17-05`: Transition from 1 to 2 to 3 Feeds Dynamic Re-solving
- **Preconditions**: Dynamic grid starting with 1 active feed.
- **Inputs & Actions**:
  1. Add feed 2 -> observe layout.
  2. Add feed 3 -> observe layout.
- **Expected Outputs**:
  - Step 1: Layout transitions from full-screen `(0, 0, W, H)` to 50/50 split.
  - Step 2: Layout transitions from 50/50 split to 3-tile balanced grid.
- **Layout Oracle Assertions**: Validate all intermediate rects against `GridSolverOracle` for $N=1, 2, 3$.
- **Mock Requirements**: `CallSimulator` dynamic stream addition.
- **Edge Cases**: Removing feed 3 immediately restores exact 50/50 split.

---

#### Feature 18: Uncapped Dynamic Main Grid Scaling

##### `TEST-T1-F18-01`: Uncapped Dynamic Scaling at N=16 (4x4 Grid Matrix)
- **Preconditions**: 16 active participants publishing video; viewport = `1600 x 1200`; dynamic mode.
- **Inputs & Actions**: Pass 16 feeds to `countWide()`.
- **Expected Outputs**: Solver generates $K = \lceil \sqrt{16} \rceil = 4$ columns and 4 rows.
- **Layout Oracle Assertions**:
  - 16 distinct non-empty `QRect` objects.
  - No tile overlap: $\forall i \ne j, R_i \cap R_j = \emptyset$.
  - Total covered bounding box equals `QRect(0, 0, 1600, 1200)`.
- **Mock Requirements**: `CallSimulator` with 16 feeds.
- **Edge Cases**: Verify CPU calculation time for $N=16$ is $< 2\text{ms}$.

##### `TEST-T1-F18-02`: Uncapped Dynamic Scaling at N=25 (5x5 Grid Matrix)
- **Preconditions**: 25 active video participants; viewport = `1500 x 1000`.
- **Inputs & Actions**: Trigger dynamic grid layout computation.
- **Expected Outputs**: Solver generates 5 columns x 5 rows ($K=5$).
- **Layout Oracle Assertions**:
  - $w_{\text{cell}} = (1500 - 4 \times 4) / 5 = 296.8\text{px}$, $h_{\text{cell}} = (1000 - 4 \times 4) / 5 = 196.8\text{px}$.
  - All 25 tiles assigned valid bounding rectangles.
- **Mock Requirements**: `CallSimulator` generating 25 video tracks.
- **Edge Cases**: Check memory stability and texture allocation across 25 tiles.

##### `TEST-T1-F18-03`: High-Density Stress Scaling at N=64 (8x8 Grid Matrix)
- **Preconditions**: 64 video participants; viewport = `1920 x 1080`.
- **Inputs & Actions**: Update grid layout with 64 feeds.
- **Expected Outputs**: Solver scales without artificial hard caps, generating $K=8$ columns x 8 rows.
- **Layout Oracle Assertions**:
  - 64 non-empty tile geometries.
  - Tile width $\approx (1920 - 7 \times 4)/8 = 236.5\text{px}$, height $\approx (1080 - 7 \times 4)/8 = 131.5\text{px}$.
  - Invariant: Zero crashing, zero integer overflow.
- **Mock Requirements**: `CallSimulator` with 64 endpoints.
- **Edge Cases**: Participant 64 leaves -> grid re-solves to 63 tiles seamlessly.

##### `TEST-T1-F18-04`: Prime and Irregular Participant Counts (N=7, N=11, N=17)
- **Preconditions**: Viewport = `1200 x 800`.
- **Inputs & Actions**: Test layouts for $N \in \{7, 11, 17\}$.
- **Expected Outputs**: Slices algorithm cleanly balances uneven rows across columns.
- **Layout Oracle Assertions**:
  - For $N=7$ ($K=3$ cols): Column distributions $(3, 2, 2)$ or $(2, 3, 2)$.
  - For $N=11$ ($K=4$ cols): Column distributions $(3, 3, 3, 2)$.
  - Sum of tiles in all columns equals $N$ exactly.
- **Mock Requirements**: `CallSimulator` parameterized by participant count.
- **Edge Cases**: Ensure no blank phantom column is created.

##### `TEST-T1-F18-05`: Minimum Dimension Guard on Constrained Viewport
- **Preconditions**: 16 participants in small viewport = `300 x 200`.
- **Inputs & Actions**: Calculate layout.
- **Expected Outputs**: Each tile maintains minimum non-zero geometry ($\ge 1\text{px}$).
- **Layout Oracle Assertions**:
  - $\forall i, w_i \ge 1 \land h_i \ge 1$.
  - Coordinates stay within $[0, 300] \times [0, 200]$.
- **Mock Requirements**: `CallSimulator` with 16 feeds.
- **Edge Cases**: Viewport resize to `0 x 0` sets `_fullHeight = 0` and exits gracefully.

---

#### Feature 19: Persistent Pin Slot Allocator

##### `TEST-T1-F19-01`: Single Pin Persistence Across New Participant Joins
- **Preconditions**: Group call with Peer A (pinned) and Peer B (unpinned). Viewport in 50/50 mode. Peer A is in Slot 0.
- **Inputs & Actions**: Join Peers C, D, E into the call. Trigger layout solve.
- **Expected Outputs**: Peer A remains locked in Slot 0 (top-left). Unpinned peers B, C, D, E are placed in Slots 1, 2, 3, 4.
- **Layout Oracle Assertions**:
  - `sizes[0].tile->endpoint() == PeerA.endpoint`.
  - `_pinnedEndpoints == { PeerA.endpoint }`.
- **Mock Requirements**: `CallSimulator` with dynamic participant joins.
- **Edge Cases**: Peer A stops video and restarts video -> re-attaches to pinned Slot 0.

##### `TEST-T1-F19-02`: Pin Slot Invariance on Unpinned Peer Leave
- **Preconditions**: Pinned Peer A (Slot 0), Unpinned Peer B (Slot 1), Unpinned Peer C (Slot 2).
- **Inputs & Actions**: Peer B leaves the call.
- **Expected Outputs**: Peer A stays in Slot 0. Peer C moves from Slot 2 to Slot 1.
- **Layout Oracle Assertions**:
  - Slot 0 endpoint remains `PeerA.endpoint`.
  - Slot 1 endpoint becomes `PeerC.endpoint`.
- **Mock Requirements**: `CallSimulator` participant leave event.
- **Edge Cases**: Unpinned peer leaves while layout animation is running.

##### `TEST-T1-F19-03`: Multi-Pin Sequential Slot Allocation
- **Preconditions**: Unpinned peers [A, B, C, D].
- **Inputs & Actions**:
  1. Call `togglePin(PeerB, true)`.
  2. Call `togglePin(PeerD, true)`.
- **Expected Outputs**:
  - `_pinnedEndpoints == { PeerB, PeerD }`.
  - Slot 0 = Peer B, Slot 1 = Peer D.
  - Slots 2, 3 = Peers A, C (sorted chronologically).
- **Layout Oracle Assertions**:
  - `sizes[0].tile == PeerB`, `sizes[1].tile == PeerD`.
- **Mock Requirements**: `CallSimulator` with endpoints A, B, C, D.
- **Edge Cases**: Pin order determines leading slot sequence deterministically.

##### `TEST-T1-F19-04`: Middle Pin Removal Re-indexing
- **Preconditions**: 3 pinned peers: Slot 0 = A, Slot 1 = B, Slot 2 = C.
- **Inputs & Actions**: Call `togglePin(PeerB, false)`.
- **Expected Outputs**: Peer B is unpinned. Peer C shifts to Slot 1. Peer A remains in Slot 0.
- **Layout Oracle Assertions**:
  - `_pinnedEndpoints == { PeerA, PeerC }`.
  - `_pinnedSlots[PeerA] == 0`, `_pinnedSlots[PeerC] == 1`.
- **Mock Requirements**: Viewport with 3 pinned feeds.
- **Edge Cases**: Re-pinning B appends B to the end of pinned slots (Slot 2).

##### `TEST-T1-F19-05`: Duplicate Pin Idempotency
- **Preconditions**: Peer A is already pinned at Slot 0.
- **Inputs & Actions**: Invoke `togglePin(PeerA, true)` again.
- **Expected Outputs**: No duplicate entries created in `_pinnedEndpoints` or `_pinnedSlots`.
- **Layout Oracle Assertions**:
  - `_pinnedEndpoints.size() == 1`.
  - `_pinnedSlots[PeerA] == 0`.
- **Mock Requirements**: Viewport pin state check.
- **Edge Cases**: Rapid double-click on pin button produces single pin state.

---

#### Feature 20: Per-Window Dynamic Pinned Auto-Scaling

##### `TEST-T1-F20-01`: 1 Pinned Feed Full-Stage Auto-Scaling
- **Preconditions**: Multi-feed call (1 pinned feed, 5 unpinned feeds). Secondary stage window opened (`800 x 600`).
- **Inputs & Actions**: Route pinned feed to secondary stage window.
- **Expected Outputs**: Pinned feed expands to fill 100% of stage window geometry.
- **Layout Oracle Assertions**:
  - Stage viewport geometry: `QRect(0, 0, 800, 600)`.
  - Tile 0 geometry: `QRect(0, 0, 800, 600)`.
- **Mock Requirements**: `DisplayCoordinator` with secondary window viewport.
- **Edge Cases**: Stage window minimized and restored -> geometry restored.

##### `TEST-T1-F20-02`: 2 Pinned Feeds Symmetrical Stage Partitioning
- **Preconditions**: Stage window (`1000 x 500`); 2 feeds pinned to stage window.
- **Inputs & Actions**: Update stage layout.
- **Expected Outputs**: 2 pinned feeds partition stage window 50/50.
- **Layout Oracle Assertions**:
  - Tile 0: `QRect(0, 0, 498, 500)`.
  - Tile 1: `QRect(502, 0, 498, 500)`.
- **Mock Requirements**: Stage window with 2 pinned feeds.
- **Edge Cases**: Rotate display orientation to portrait (`500 x 1000`) -> splits top/bottom.

##### `TEST-T1-F20-03`: 4 Pinned Feeds 2x2 Stage Matrix Auto-Scale
- **Preconditions**: Stage window (`1200 x 800`); 4 feeds pinned to stage window.
- **Inputs & Actions**: Trigger stage viewport update.
- **Expected Outputs**: 4 feeds automatically scaled in 2x2 grid.
- **Layout Oracle Assertions**:
  - 4 quadrants of size `598 x 398` with 4px gap.
- **Mock Requirements**: Stage window with 4 feeds.
- **Edge Cases**: Aspect ratio letterboxing computed independently per tile.

##### `TEST-T1-F20-04`: Dynamic Rescaling from 1 -> 3 -> 6 Pinned Feeds
- **Preconditions**: Active stage window.
- **Inputs & Actions**:
  1. Pin Feed 1 -> Stage has 1 feed.
  2. Pin Feeds 2, 3 -> Stage recomputes to 3 feeds.
  3. Pin Feeds 4, 5, 6 -> Stage recomputes to 6 feeds (3x2 matrix).
- **Expected Outputs**: Stage dynamic auto-scaling updates synchronously at each step.
- **Layout Oracle Assertions**: Verify stage tile count matches `pinnedCount(screenIndex)`.
- **Mock Requirements**: `DisplayCoordinator::pinToScreen()`.
- **Edge Cases**: Unpin all -> stage window displays placeholder or closes cleanly.

##### `TEST-T1-F20-05`: Independent Dual-Window Pinned Scaling
- **Preconditions**: Primary window (`1200 x 800`) with 1 pinned feed; Secondary window (`1920 x 1080`) with 4 pinned feeds.
- **Inputs & Actions**: Trigger concurrent resize of both windows.
- **Expected Outputs**: Primary window scales 1 feed to full; Secondary window scales 4 feeds to 2x2 matrix.
- **Layout Oracle Assertions**:
  - Primary Tile 0: `QRect(0, 0, 1200, 800)`.
  - Secondary Tiles 0..3: `QRect(x, y, 958, 538)`.
- **Mock Requirements**: Dual `Viewport` instances managed by `DisplayCoordinator`.
- **Edge Cases**: Dragging window between monitors with different DPI scales adjusts geometry without blur.

---

#### Feature 21: Multi-Pin Capability

##### `TEST-T1-F21-01`: Sequential Multi-Pin Registration (Feeds 1 to 5)
- **Preconditions**: Group call with 8 active video streams.
- **Inputs & Actions**: Sequentially pin endpoints `[ep_1, ep_2, ep_3, ep_4, ep_5]`.
- **Expected Outputs**: All 5 endpoints registered in `pinnedEndpoints()`.
- **Layout Oracle Assertions**:
  - `pinnedEndpoints().size() == 5`.
  - `isPinned(ep_k) == true` for $k \in \{1..5\}$.
- **Mock Requirements**: `Viewport::togglePin()`.
- **Edge Cases**: Check that previous pinned feeds are NOT auto-unpinned.

##### `TEST-T1-F21-02`: Multi-Pin Maximum Capacity Boundary (9 Pinned Feeds)
- **Preconditions**: 9 feeds pinned in viewport.
- **Inputs & Actions**: Attempt to pin 10th feed `ep_10`.
- **Expected Outputs**: System enforces maximum capacity rule (rejects 10th pin or prompts replacement).
- **Layout Oracle Assertions**:
  - `pinnedEndpoints().size() <= 9`.
- **Mock Requirements**: Viewport pin capacity limit.
- **Edge Cases**: Unpinning one feed allows pinning a new feed immediately.

##### `TEST-T1-F21-03`: Concurrent Multi-Pin from Video Grid and Sidebar
- **Preconditions**: 4 participants in call.
- **Inputs & Actions**:
  1. Click pin icon on Peer 1 video tile hover.
  2. Right-click Peer 2 in sidebar and select "Pin to Grid".
- **Expected Outputs**: Both Peer 1 and Peer 2 become pinned.
- **Layout Oracle Assertions**:
  - `isPinned(Peer1) == true && isPinned(Peer2) == true`.
- **Mock Requirements**: UI event dispatch from both tile and sidebar.
- **Edge Cases**: Pinning same peer from both sources simultaneously handled idempotently.

##### `TEST-T1-F21-04`: Mixed Screen-Share and Camera Multi-Pinning
- **Preconditions**: User A sharing screen (`ep_screen`) and camera (`ep_cam`); User B sharing camera (`ep_b`).
- **Inputs & Actions**: Pin `ep_screen`, `ep_cam`, and `ep_b`.
- **Expected Outputs**: All 3 distinct video tracks allocated leading pinned slots.
- **Layout Oracle Assertions**:
  - `pinnedEndpoints()` contains 3 unique endpoints with respective video tracks.
- **Mock Requirements**: `VideoEndpoint` differentiation (`track` vs `screen`).
- **Edge Cases**: User A stops screenshare -> `ep_screen` automatically unpinned while `ep_cam` remains pinned.

##### `TEST-T1-F21-05`: Multi-Pin State Reflection Across UI Surfaces
- **Preconditions**: Peers A and B pinned.
- **Inputs & Actions**: Inspect Video Tiles, Sidebar Rows, and Context Menus for Peers A, B, C.
- **Expected Outputs**:
  - Peers A and B show active pin badge on tile and "Unpin" context menu item.
  - Peer C shows unpinned icon on hover and "Pin" context menu item.
- **Layout Oracle Assertions**: UI state variables match `isPinned()` queries.
- **Mock Requirements**: `MembersRow` and `VideoTile` UI state validation.
- **Edge Cases**: Switching call modes (Wide -> Narrow -> Wide) preserves pin state badges.

---

#### Feature 22: Adjustable Pinned Panel Sizes

##### `TEST-T1-F22-01`: Splitter Drag Resizing of Pinned vs Unpinned Areas
- **Preconditions**: Viewport with pinned stage panel (left) and secondary grid (right); initial split = 50% (`500px / 500px`).
- **Inputs & Actions**: Simulate mouse drag on splitter handle by `+150px` to the right.
- **Expected Outputs**: Pinned stage panel expands to `650px`; secondary grid shrinks to `350px`.
- **Layout Oracle Assertions**:
  - Pinned stage geometry width == `650px`.
  - Secondary grid geometry width == `350px`.
  - Sum of widths + splitter == `1000px`.
- **Mock Requirements**: Mouse drag event simulator on splitter widget.
- **Edge Cases**: Dragging beyond bounds clamps at minimum width constraints.

##### `TEST-T1-F22-02`: Minimum Dimension Guardrails (120px Clamping)
- **Preconditions**: Splitter at 50%; viewport width = `1000px`.
- **Inputs & Actions**: Attempt to drag splitter to `x = 50px` (below minimum `120px`).
- **Expected Outputs**: Splitter clamps at `x = 120px`.
- **Layout Oracle Assertions**:
  - Pinned stage width $\ge 120\text{px}$.
  - Secondary grid width $\le 880\text{px}$.
- **Mock Requirements**: Splitter boundary validator.
- **Edge Cases**: Dragging to far right clamps secondary grid at minimum 120px as well.

##### `TEST-T1-F22-03`: Aspect Ratio Preservation During Splitter Drag
- **Preconditions**: 16:9 video in pinned panel being resized.
- **Inputs & Actions**: Resize pinned panel width from `600px` to `800px` at constant height `450px`.
- **Expected Outputs**: Video frame inside tile scales with `Qt::KeepAspectRatio`, adjusting pillarbox bars dynamically.
- **Layout Oracle Assertions**:
  - Video render rect aspect ratio $\equiv 16/9$.
  - Render rect centered within `800 x 450` tile container.
- **Mock Requirements**: `VideoTile::trackOrUserpicSize()`.
- **Edge Cases**: Video frame updates during active drag.

##### `TEST-T1-F22-04`: Splitter Reset to Default on Double-Click
- **Preconditions**: Splitter modified to custom ratio `70% / 30%`.
- **Inputs & Actions**: Double-click splitter bar.
- **Expected Outputs**: Splitter resets to default balanced 50% / 50% split.
- **Layout Oracle Assertions**:
  - Pinned stage width == `(W - splitterWidth) / 2`.
- **Mock Requirements**: Double-click mouse event on splitter.
- **Edge Cases**: Double-click while already at 50% maintains 50%.

##### `TEST-T1-F22-05`: Outer Window Resizing Proportional Scaling
- **Preconditions**: Pinned panel set to 60% of `1000px` (`600px`).
- **Inputs & Actions**: Resize outer window from `1000px` to `1500px`.
- **Expected Outputs**: Pinned panel scales proportionally to $60\% \times 1500 = 900\text{px}$.
- **Layout Oracle Assertions**:
  - Pinned panel width == `900px`.
  - Secondary area width == `600px`.
- **Mock Requirements**: Window resize event dispatcher.
- **Edge Cases**: Window shrunk to minimum size restores proportions when expanded again.

---

#### Feature 23: Grid Unpinning & Removal Actions

##### `TEST-T1-F23-01`: Direct Tile Hover Unpin Button Trigger
- **Preconditions**: Pinned Peer A in Slot 0. Mouse hovers over Tile 0.
- **Inputs & Actions**: Click Pin button in hover controls (`Selection::Element::PinButton`).
- **Expected Outputs**: `_pinToggles` fires `false`; Peer A is removed from `_pinnedEndpoints`.
- **Layout Oracle Assertions**:
  - `isPinned(PeerA) == false`.
  - Layout re-solves to dynamic chronological grid.
- **Mock Requirements**: Mouse release at `tile->pinOuter()` coordinates.
- **Edge Cases**: Unpinning only pinned feed resets viewport to standard presentation or grid mode.

##### `TEST-T1-F23-02`: Unpin via Member Sidebar Context Menu Action
- **Preconditions**: Peer A pinned with active camera feed.
- **Inputs & Actions**: Right-click Peer A row in sidebar; click `lng_group_call_context_unpin_camera`.
- **Expected Outputs**: Invokes `_call->pinVideoEndpoint({})` / `togglePin(PeerA, false)`.
- **Layout Oracle Assertions**:
  - `isPinned(PeerA) == false`.
  - Context menu for Peer A now displays `lng_group_call_context_pin_camera`.
- **Mock Requirements**: `Members::lookupRow(PeerA)` context menu event.
- **Edge Cases**: Unpinning screen-share feed specifically targets `screen` endpoint without affecting `camera` endpoint.

##### `TEST-T1-F23-03`: Batch Unpin All Feeds Action
- **Preconditions**: 4 feeds pinned in grid.
- **Inputs & Actions**: Invoke unpin-all command / action.
- **Expected Outputs**: All 4 endpoints cleared from `_pinnedEndpoints`.
- **Layout Oracle Assertions**:
  - `pinnedEndpoints().empty() == true`.
  - Grid displays all active feeds sorted by `entryTime()`.
- **Mock Requirements**: Viewport batch unpin handler.
- **Edge Cases**: Batch unpin during active video stream addition.

##### `TEST-T1-F23-04`: Secondary Screen Removal Action & Dialog
- **Preconditions**: Feed pinned to Secondary Screen 2.
- **Inputs & Actions**: Trigger "Remove from Screen 2" context menu action.
- **Expected Outputs**: `DisplayCoordinator::unpinFromScreen(2, endpoint)` is invoked; feed removed from Screen 2 stage.
- **Layout Oracle Assertions**:
  - `DisplayCoordinator::pinnedCount(2)` decrements by 1.
- **Mock Requirements**: `DisplayCoordinator` mock.
- **Edge Cases**: Removing last feed from secondary screen closes or clears secondary stage window.

##### `TEST-T1-F23-05`: Automatic Slot Cleanup on Remote Video Disconnect
- **Preconditions**: Remote Peer A is pinned in Slot 0.
- **Inputs & Actions**: Remote Peer A mutes camera / disconnects video track (`track->stateValue() -> false`).
- **Expected Outputs**: Viewport `remove(endpoint)` is called; Peer A removed from `_pinnedEndpoints` and `_pinnedSlots`.
- **Layout Oracle Assertions**:
  - `_pinnedSlots.find(PeerA) == _pinnedSlots.end()`.
  - Remaining feeds shift up into Slot 0 smoothly.
- **Mock Requirements**: `VideoTileTrack` state stream emitting inactive state.
- **Edge Cases**: Participant reconnects video 2 seconds later -> treated as new unpinned feed unless re-pinned.

---

#### Feature 24: Pin to Grid Context Menu Actions

##### `TEST-T1-F24-01`: Injection of `lng_group_call_context_pin_to_grid` in Sidebar Menu
- **Preconditions**: Unpinned participant with video in call sidebar.
- **Inputs & Actions**: Right-click participant row to open `PopupMenu`.
- **Expected Outputs**: Context menu contains item with localized string `tr::lng_group_call_context_pin_camera(tr::now)`.
- **Layout Oracle Assertions**:
  - Context menu item exists and is enabled.
- **Mock Requirements**: `calls_group_members.cpp:1452`.
- **Edge Cases**: Audio-only participant (no video published) does NOT display pin video action.

##### `TEST-T1-F24-02`: Video Tile Right-Click Menu Pin/Unpin Action Dynamic State
- **Preconditions**: Viewport with unpinned Tile 0.
- **Inputs & Actions**: Right-click on Tile 0. Inspect menu. Then pin Tile 0 and right-click again.
- **Expected Outputs**:
  - First right-click: menu displays "Pin to Grid".
  - Second right-click: menu displays "Unpin from Grid".
- **Layout Oracle Assertions**: Action text and callback toggle reactively based on `tile->pinned()`.
- **Mock Requirements**: `VideoTile::row()->showContextMenu()`.
- **Edge Cases**: Right-click during video stream freeze.

##### `TEST-T1-F24-03`: Pin to Grid from Search Result Rows
- **Preconditions**: Sidebar search query active; matching participant row displayed.
- **Inputs & Actions**: Right-click search result row; select "Pin to Grid".
- **Expected Outputs**: Target participant pinned to grid; search view maintained.
- **Layout Oracle Assertions**:
  - Target peer added to `_pinnedEndpoints`.
- **Mock Requirements**: Filtered `PeerListContent` row context menu.
- **Edge Cases**: Participant leaves call while search context menu is open -> menu action safely handles null peer.

##### `TEST-T1-F24-04`: Separate Pin Camera vs Pin Screen Menu Actions
- **Preconditions**: Participant sharing both webcam video and screen broadcast.
- **Inputs & Actions**: Right-click participant in member list.
- **Expected Outputs**: Context menu displays two distinct actions: `lng_group_call_context_pin_camera` AND `lng_group_call_context_pin_screen`.
- **Layout Oracle Assertions**:
  - Both actions present with distinct callbacks `_call->pinVideoEndpoint(camera)` and `_call->pinVideoEndpoint(screen)`.
- **Mock Requirements**: `calls_group_members.cpp:1445-1466`.
- **Edge Cases**: Participant stops screenshare while menu open -> selecting pin screen shows fallback toast.

##### `TEST-T1-F24-05`: Pin to Grid Action Execution and Viewport Focus
- **Preconditions**: Viewport in default presentation view.
- **Inputs & Actions**: Select "Pin to Grid" from context menu on Peer B.
- **Expected Outputs**: Viewport transitions to Grid mode if needed, allocates leading slot to Peer B, and triggers layout animation.
- **Layout Oracle Assertions**:
  - `_pinnedEndpoints.back() == PeerB.endpoint`.
  - `_largeChangeAnimation.animating() == true` or geometry updated immediately.
- **Mock Requirements**: `calls_group_viewport.cpp:1037`.
- **Edge Cases**: Pinning when call window is minimized updates geometry in background without rendering errors.

---

### Category 6: Transparent Overlay Canvas (Features 25 – 28)

#### Feature 25: Frameless Transparent Top-Most Overlay

##### `TEST-T1-F25-01`: Window Flags and Transparency Attributes Assertion
- **Preconditions**: `FloatingOverlay` instantiated with parent `Panel`.
- **Inputs & Actions**: Query window flags and attributes on `FloatingOverlay` widget.
- **Expected Outputs**:
  - `windowFlags() & Qt::Window == Qt::Window`.
  - `windowFlags() & Qt::FramelessWindowHint == Qt::FramelessWindowHint`.
  - `windowFlags() & Qt::WindowStaysOnTopHint == Qt::WindowStaysOnTopHint`.
  - `testAttribute(Qt::WA_TranslucentBackground) == true`.
  - `testAttribute(Qt::WA_ShowWithoutActivating) == true`.
- **Layout Oracle Assertions**: Exact bitmask matches on Qt window flags.
- **Mock Requirements**: `FloatingOverlay` constructor (`calls_group_floating_overlay.cpp:25-29`).
- **Edge Cases**: Platform window managers without compositor support fallback gracefully.

##### `TEST-T1-F25-02`: Initial Geometry and Screen Anchor Placement
- **Preconditions**: Primary screen available geometry = `1920 x 1080`.
- **Inputs & Actions**: Instantiate `FloatingOverlay`.
- **Expected Outputs**: Overlay positioned at top-right: `(screen.width() - 320, 100, 300, 400)`.
- **Layout Oracle Assertions**:
  - `overlay->geometry() == QRect(1600, 100, 300, 400)`.
  - `overlay->width() == 300`, `overlay->height() == 400`.
- **Mock Requirements**: `QApplication::primaryScreen()->availableGeometry()` mock returning `1920x1080`.
- **Edge Cases**: Screen with custom scaling (150% DPI) places overlay within visible working area.

##### `TEST-T1-F25-03`: Always-On-Top Layering Verification
- **Preconditions**: `FloatingOverlay` shown on desktop; secondary full-screen window created and focused.
- **Inputs & Actions**: Raise secondary window. Check overlay stacking order.
- **Expected Outputs**: `FloatingOverlay` remains above the newly activated window due to `Qt::WindowStaysOnTopHint`.
- **Layout Oracle Assertions**: Overlay widget receives paint events and is top-most in Z-order.
- **Mock Requirements**: Window layering probe.
- **Edge Cases**: Multiple always-on-top overlays maintain relative focus order.

##### `TEST-T1-F25-04`: Mouse Passthrough Mode Activation (`WA_TransparentForMouseEvents`)
- **Preconditions**: `FloatingOverlay` visible; `_passthrough == false`.
- **Inputs & Actions**: Click passthrough toggle button (`togglePassthrough()`).
- **Expected Outputs**:
  - `_passthrough == true`.
  - `testAttribute(Qt::WA_TransparentForMouseEvents) == true`.
  - Mouse clicks on overlay area pass through to underlying desktop windows.
- **Layout Oracle Assertions**: Attribute state matches boolean toggle.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:178-181`.
- **Edge Cases**: Toggle passthrough back to false restores interactive mouse events immediately.

##### `TEST-T1-F25-05`: Paint Event & Translucent Alpha Background Blending
- **Preconditions**: `FloatingOverlay` with `_opacity = 0.70`.
- **Inputs & Actions**: Trigger `paintEvent()`.
- **Expected Outputs**: `QPainter` paints background with `QColor(30, 30, 30, 200)` and border `QColor(255, 255, 255, 100)` at opacity `0.70`.
- **Layout Oracle Assertions**: Painter receives adjusted bounding rect `rect().adjusted(0, 0, -1, -1)`.
- **Mock Requirements**: Paint device interceptor.
- **Edge Cases**: Repaint on opacity change updates visual alpha cleanly.

---

#### Feature 26: Ctrl+Shift+T Keyboard Toggle

##### `TEST-T1-F26-01`: Toggle Hidden to Visible via `Ctrl+Shift+T` Shortcut
- **Preconditions**: Group call active; `FloatingOverlay` instantiated but hidden (`isVisible() == false`).
- **Inputs & Actions**: Emit shortcut activation event on `_toggleShortcut` (`QKeySequence("Ctrl+Shift+T")`).
- **Expected Outputs**:
  - `FloatingOverlay::toggle()` executes `show()`.
  - `isVisible() == true`.
  - Window raised and activated.
- **Layout Oracle Assertions**: `overlay->isVisible() == true`.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:38-40`.
- **Edge Cases**: Shortcut fires while full-screen presentation is active.

##### `TEST-T1-F26-02`: Toggle Visible to Hidden via `Ctrl+Shift+T` Shortcut
- **Preconditions**: `FloatingOverlay` currently visible on screen.
- **Inputs & Actions**: Trigger `Ctrl+Shift+T` shortcut.
- **Expected Outputs**:
  - `FloatingOverlay::toggle()` executes `hide()`.
  - `isVisible() == false`.
- **Layout Oracle Assertions**: `overlay->isVisible() == false`.
- **Mock Requirements**: Shortcut event dispatcher.
- **Edge Cases**: Hidden overlay stops consuming render/paint resources.

##### `TEST-T1-F26-03`: Panel-Level Window Shortcut Routing
- **Preconditions**: Focus is on Call `Panel` main window; overlay is hidden.
- **Inputs & Actions**: Send `QKeyEvent(QEvent::KeyPress, Qt::Key_T, Qt::ControlModifier | Qt::ShiftModifier)` to `Panel`.
- **Expected Outputs**: `Panel` routes shortcut to floating overlay controller; overlay is displayed.
- **Layout Oracle Assertions**: `overlay->isVisible() == true`.
- **Mock Requirements**: `calls_group_panel.cpp:1152`.
- **Edge Cases**: Key release event does not re-trigger toggle.

##### `TEST-T1-F26-04`: Rapid Repeated Toggle Debounce & Stability
- **Preconditions**: Overlay initialized.
- **Inputs & Actions**: Send 10 rapid `Ctrl+Shift+T` triggers within 100ms.
- **Expected Outputs**: Overlay state toggles deterministically 10 times, finishing in hidden state (`false`), without deadlocks or crashes.
- **Layout Oracle Assertions**: `overlay->isVisible() == false`.
- **Mock Requirements**: High-frequency key event generator.
- **Edge Cases**: Rapid toggling during window move or resize animation.

##### `TEST-T1-F26-05`: Call Teardown Lifecycle Cleanup
- **Preconditions**: Overlay visible during active call.
- **Inputs & Actions**: Terminate group call (`destroyPanel()`).
- **Expected Outputs**: `FloatingOverlay` is destroyed; shortcut unregistered from Qt event loop.
- **Layout Oracle Assertions**: Overlay pointer destroyed, no dangling shortcut bindings.
- **Mock Requirements**: Call teardown lifecycle simulator.
- **Edge Cases**: Closing call while overlay is dragging cleanly terminates drag.

---

#### Feature 27: Opacity Adjustment via Ctrl+Wheel

##### `TEST-T1-F27-01`: Opacity Increment on `Ctrl + WheelUp`
- **Preconditions**: Overlay visible; initial `_opacity = 0.70`.
- **Inputs & Actions**: Dispatch `QWheelEvent` with `angleDelta().y() = +120` and `modifiers() = Qt::ControlModifier`.
- **Expected Outputs**:
  - `_opacity` increases by `+0.05` to `0.75`.
  - `windowOpacity() == 0.75f`.
  - Widget repaints.
- **Layout Oracle Assertions**: `fabs(overlay->windowOpacity() - 0.75) < 1e-4`.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:100-114`.
- **Edge Cases**: High-precision trackpad wheel events with smaller deltas.

##### `TEST-T1-F27-02`: Opacity Decrement on `Ctrl + WheelDown`
- **Preconditions**: Overlay visible; initial `_opacity = 0.70`.
- **Inputs & Actions**: Dispatch `QWheelEvent` with `angleDelta().y() = -120` and `modifiers() = Qt::ControlModifier`.
- **Expected Outputs**:
  - `_opacity` decreases by `-0.05` to `0.65`.
  - `windowOpacity() == 0.65f`.
- **Layout Oracle Assertions**: `fabs(overlay->windowOpacity() - 0.65) < 1e-4`.
- **Mock Requirements**: `QWheelEvent` dispatcher.
- **Edge Cases**: Fast continuous scrolling down reaches lower clamp smoothly.

##### `TEST-T1-F27-03`: Upper Boundary Clamping at Maximum Opacity (1.00)
- **Preconditions**: Overlay visible; `_opacity = 0.95`.
- **Inputs & Actions**: Dispatch 5 consecutive `Ctrl + WheelUp` events.
- **Expected Outputs**: `_opacity` increases to `1.00` and clamps at `1.00` ($\max \le 1.00$).
- **Layout Oracle Assertions**: `overlay->windowOpacity() == 1.00f`.
- **Mock Requirements**: Multi-event wheel stream.
- **Edge Cases**: Floating-point accumulation rounding does not exceed `1.00`.

##### `TEST-T1-F27-04`: Lower Boundary Clamping at Minimum Opacity (0.20)
- **Preconditions**: Overlay visible; `_opacity = 0.30`.
- **Inputs & Actions**: Dispatch 5 consecutive `Ctrl + WheelDown` events.
- **Expected Outputs**: `_opacity` decreases to `0.20` and clamps at `0.20` ($\min \ge 0.20$).
- **Layout Oracle Assertions**: `overlay->windowOpacity() == 0.20f`.
- **Mock Requirements**: Lower-bound wheel stream.
- **Edge Cases**: Overlay remains visible and readable at minimum 20% opacity.

##### `TEST-T1-F27-05`: Standard Mouse Wheel Event Passthrough Without Ctrl
- **Preconditions**: Overlay visible; `_opacity = 0.70`.
- **Inputs & Actions**: Dispatch `QWheelEvent` with `angleDelta().y() = +120` and `modifiers() = Qt::NoModifier`.
- **Expected Outputs**:
  - `_opacity` remains unchanged at `0.70`.
  - Event passed to child `MessagesUi` scroll area for chat history scrolling.
- **Layout Oracle Assertions**: `overlay->windowOpacity() == 0.70f`.
- **Mock Requirements**: Unmodified wheel event.
- **Edge Cases**: Modifier key released mid-wheel scroll cleanly shifts from opacity to chat scroll.

---

#### Feature 28: Draggable Canvas & Escape to Dismiss

##### `TEST-T1-F28-01`: Left-Click Drag Repositioning Translation
- **Preconditions**: Overlay at `QRect(1000, 100, 300, 400)`; `_passthrough == false`.
- **Inputs & Actions**:
  1. `mousePressEvent` at local `(50, 50)` (global `(1050, 150)`) with `Qt::LeftButton`.
  2. `mouseMoveEvent` to global `(1150, 250)` ($\Delta = (+100, +100)$).
- **Expected Outputs**:
  - `_dragging == true`.
  - Overlay geometry translates by `(+100, +100)` to `QRect(1100, 200, 300, 400)`.
- **Layout Oracle Assertions**: `overlay->geometry() == QRect(1100, 200, 300, 400)`.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:76-92`.
- **Edge Cases**: Dragging across multi-monitor boundary translates seamlessly.

##### `TEST-T1-F28-02`: Mouse Release Drag State Termination
- **Preconditions**: Overlay currently in active drag state (`_dragging == true`).
- **Inputs & Actions**: Dispatch `mouseReleaseEvent` with `Qt::LeftButton`.
- **Expected Outputs**:
  - `_dragging` reset to `false`.
  - Overlay remains at new coordinates; subsequent mouse moves without press do not move window.
- **Layout Oracle Assertions**: `_dragging == false`.
- **Mock Requirements**: Mouse release dispatcher.
- **Edge Cases**: Mouse release outside window bounds still cancels drag state.

##### `TEST-T1-F28-03`: Escape Key Dismissal
- **Preconditions**: Overlay visible and focused.
- **Inputs & Actions**: Dispatch `QKeyEvent(QEvent::KeyPress, Qt::Key_Escape, Qt::NoModifier)`.
- **Expected Outputs**:
  - `FloatingOverlay::keyPressEvent` intercepts `Qt::Key_Escape`.
  - Calls `hide()`.
  - `isVisible() == false`.
- **Layout Oracle Assertions**: `overlay->isVisible() == false`.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:69-74`.
- **Edge Cases**: Pressing Escape while a child context menu is open dismisses the context menu first, subsequent Escape dismisses overlay.

##### `TEST-T1-F28-04`: Screen Boundary Snapping in `updateGeometry()`
- **Preconditions**: Screen available geometry = `[0, 0, 1920, 1080]`.
- **Inputs & Actions**: Drag overlay to position `(1800, 900)` with size `300 x 400` (exceeding screen right at 2100 and bottom at 1300). Call `updateGeometry()`.
- **Expected Outputs**: Overlay coordinates clamped inside screen:
  - `right() <= 1920` -> `x = 1920 - 300 = 1620`.
  - `bottom() <= 1080` -> `y = 1080 - 400 = 680`.
- **Layout Oracle Assertions**: `overlay->geometry() == QRect(1620, 680, 300, 400)`.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:160-176`.
- **Edge Cases**: Dragging past top/left bounds clamped at `x >= 0` and `y >= 0`.

##### `TEST-T1-F28-05`: Non-Left Mouse Button Drag Immunity
- **Preconditions**: Overlay visible at `(1000, 100, 300, 400)`.
- **Inputs & Actions**: Press and move mouse with `Qt::RightButton` or `Qt::MiddleButton`.
- **Expected Outputs**:
  - `_dragging` remains `false`.
  - Overlay geometry does NOT change.
- **Layout Oracle Assertions**: `overlay->geometry() == QRect(1000, 100, 300, 400)`.
- **Mock Requirements**: Right-click mouse event sequence.
- **Edge Cases**: Right-click displays context menu without shifting window position.

---

### Category 7: Embedded In-Meeting Chat & Search (Features 29 – 30)

#### Feature 29: Embedded Chat & Dynamic Resize

##### `TEST-T1-F29-01`: `MessagesUi` Attachment and Geometry Initialization
- **Preconditions**: `FloatingOverlay` initialized with size `300 x 400`.
- **Inputs & Actions**: Call `FloatingOverlay::setupChatContent()`.
- **Expected Outputs**: `MessagesUi` child widget is created and positioned with margins: `left = 4, top = 36, width = 300 - 8 = 292, height = 400 - 40 = 360`.
- **Layout Oracle Assertions**:
  - `_messagesUi->geometry() == QRect(4, 36, 292, 360)`.
- **Mock Requirements**: `calls_group_floating_overlay.cpp:125-130`, `calls_group_messages_ui.h`.
- **Edge Cases**: Initializing with null chat data handles gracefully without crash.

##### `TEST-T1-F29-02`: Overlay Resize Dynamic Child Content Scaling
- **Preconditions**: Overlay resized from `300 x 400` to `500 x 700`.
- **Inputs & Actions**: Trigger `FloatingOverlay::resizeEvent()`.
- **Expected Outputs**: `_messagesUi->move(4, 36, 500 - 8, 700 - 40)` is executed.
- **Layout Oracle Assertions**:
  - Child chat widget width == `492px`.
  - Child chat widget height == `660px`.
  - Message bubble items re-layout and re-wrap text to new width `492px`.
- **Mock Requirements**: `MessagesUi::move()` spy.
- **Edge Cases**: Rapid interactive window resize maintains continuous layout sync.

##### `TEST-T1-F29-03`: Real-Time Incoming Message Rendering in Overlay
- **Preconditions**: Overlay open with active `MessagesUi`.
- **Inputs & Actions**: Call simulator sends new chat message `Message{ id: 101, text: "Meeting notes updated" }`.
- **Expected Outputs**: Message appended to chat list; visible message item created; scroll area updates full height.
- **Layout Oracle Assertions**:
  - Message view count increments by 1.
  - New message rect visible in scroll viewport.
- **Mock Requirements**: `_call->messages()->listValue()` stream producer.
- **Edge Cases**: Rapid message bursts (20 messages/sec) append smoothly without dropped frames.

##### `TEST-T1-F29-04`: Message Field Input Focus vs Drag Reservation
- **Preconditions**: Overlay visible with chat text input field at bottom.
- **Inputs & Actions**: Click and drag inside message text input field.
- **Expected Outputs**: Text selection inside input field is performed; overlay window dragging is NOT triggered (`_dragging == false`).
- **Layout Oracle Assertions**: Overlay position remains static.
- **Mock Requirements**: Input widget event filter.
- **Edge Cases**: Dragging from header bar initiates window drag; dragging from input area edits text.

##### `TEST-T1-F29-05`: Elastic Scroll Offset Preservation on Resize
- **Preconditions**: User scrolled chat list up by `200px` (`scrollTop == 200`).
- **Inputs & Actions**: Resize overlay height by `+100px`.
- **Expected Outputs**: Scroll area preserves relative item anchor; scroll position does not jump to bottom unexpectedly.
- **Layout Oracle Assertions**: Target message remains in visible viewport after resize.
- **Mock Requirements**: `Ui::ElasticScroll` state probe.
- **Edge Cases**: Scroll at exact bottom stays pinned to bottom as new messages arrive during resize.

---

#### Feature 30: In-Meeting Chat Search

##### `TEST-T1-F30-01`: Substring Search Query Matching
- **Preconditions**: In-meeting chat history contains 5 messages: ["budget proposal", "team sync notes", "proposal review", "action items", "weekly budget"].
- **Inputs & Actions**: Enter search query `"proposal"` in chat search field.
- **Expected Outputs**: List filtered / matches highlighted for messages 1 and 3; match count = 2.
- **Layout Oracle Assertions**:
  - Match indices: `[0, 2]`.
  - Highlighted text matches `"proposal"`.
- **Mock Requirements**: `calls_group_messages.cpp` search filter.
- **Edge Cases**: Query with special regex characters (`"proposal (v2)"`) escaped and matched as literal.

##### `TEST-T1-F30-02`: Case-Insensitive Matching
- **Preconditions**: Messages contain `"URGENT ANNOUNCEMENT"` and `"urgent reminder"`.
- **Inputs & Actions**: Enter search query `"urgent"`.
- **Expected Outputs**: Both uppercase and lowercase messages matched.
- **Layout Oracle Assertions**: 2 matches returned.
- **Mock Requirements**: Case-insensitive substring matcher.
- **Edge Cases**: Mixed-case unicode characters match correctly.

##### `TEST-T1-F30-03`: Empty Search Query Reset
- **Preconditions**: Active search filter showing 1 match.
- **Inputs & Actions**: Clear search query text (`""`).
- **Expected Outputs**: Full chat message stream restored; all 5 original messages visible.
- **Layout Oracle Assertions**: Total visible item count == 5.
- **Mock Requirements**: Search query change listener.
- **Edge Cases**: Pressing ESC in search input clears query and restores list in 1 action.

##### `TEST-T1-F30-04`: Non-Matching Query Zero Results State
- **Preconditions**: Chat history active.
- **Inputs & Actions**: Search query `"nonexistent_token_xyz"`.
- **Expected Outputs**: Zero matches found; empty state label / icon displayed.
- **Layout Oracle Assertions**: Visible message items count == 0.
- **Mock Requirements**: Empty state widget probe.
- **Edge Cases**: Clearing non-matching query instantly recovers chat view.

##### `TEST-T1-F30-05`: Dynamic Match Evaluation on New Incoming Message
- **Preconditions**: Search active for query `"deploy"`; 1 existing match.
- **Inputs & Actions**: Incoming new message arrives: `"ready to deploy to production"`.
- **Expected Outputs**: Match count increments from 1 to 2; new message immediately appears in search results.
- **Layout Oracle Assertions**: Match count == 2.
- **Mock Requirements**: Reactive search stream over dynamic message updates.
- **Edge Cases**: Non-matching incoming message does not disrupt current search view.

---

### Category 8: Participant List & Listen-Only Controls (Features 31 – 37)

#### Feature 31: Chronological Entry-Time Grid Sorting

##### `TEST-T1-F31-01`: Chronological Ordering of 3 Sequential Joins
- **Preconditions**: Group call starting. Viewport in dynamic grid mode.
- **Inputs & Actions**:
  - Peer A joins at $t_1 = 1000\text{ms}$.
  - Peer B joins at $t_2 = 2000\text{ms}$.
  - Peer C joins at $t_3 = 3000\text{ms}$.
- **Expected Outputs**: Unpinned tiles sorted by `entryTime()`: Slot 0 = Peer A, Slot 1 = Peer B, Slot 2 = Peer C.
- **Layout Oracle Assertions**:
  - `unpinnedTiles[0]->endpoint() == PeerA`.
  - `unpinnedTiles[1]->endpoint() == PeerB`.
  - `unpinnedTiles[2]->endpoint() == PeerC`.
- **Mock Requirements**: `VideoTile::entryTime()` timestamping.
- **Edge Cases**: Verify oldest participant is always in top-left position (Slot 0).

##### `TEST-T1-F31-02`: Out-of-Order Join Timestamp Reconciliation
- **Preconditions**: Active call.
- **Inputs & Actions**: Feeds added in network arrival order: Peer B ($t=2000$), Peer A ($t=1000$), Peer C ($t=3000$).
- **Expected Outputs**: Solver sorts by `entryTime()`: Peer A placed in Slot 0, Peer B in Slot 1, Peer C in Slot 2.
- **Layout Oracle Assertions**:
  - Output slot order: `[PeerA, PeerB, PeerC]`.
- **Mock Requirements**: `std::sort` comparator in `calls_group_viewport.cpp:542-544`.
- **Edge Cases**: Re-ordering occurs deterministically regardless of insertion sequence.

##### `TEST-T1-F31-03`: Chronological Sort Partitioning with Pinned Feeds
- **Preconditions**: Peer B ($t=2000$) is pinned. Unpinned peers: Peer A ($t=1000$), Peer C ($t=3000$), Peer D ($t=4000$).
- **Inputs & Actions**: Compute layout.
- **Expected Outputs**:
  - Pinned Peer B occupies Slot 0.
  - Remaining unpinned peers sorted chronologically: Slot 1 = Peer A ($t=1000$), Slot 2 = Peer C ($t=3000$), Slot 3 = Peer D ($t=4000$).
- **Layout Oracle Assertions**:
  - Slot 0 == Peer B (pinned).
  - Slot 1 == Peer A, Slot 2 == Peer C, Slot 3 == Peer D.
- **Mock Requirements**: `calls_group_viewport.cpp:516-547`.
- **Edge Cases**: Unpinning Peer B shifts Peer A into Slot 0, Peer B into Slot 1.

##### `TEST-T1-F31-04`: Reconnecting Participant Timestamp Behavior
- **Preconditions**: Peer A joined at $t=1000$. Temporary network drop.
- **Inputs & Actions**: Peer A reconnects with original session entry timestamp preserved.
- **Expected Outputs**: Peer A retains chronological position based on session entry time.
- **Layout Oracle Assertions**: Slot position matches original $t=1000$ index.
- **Mock Requirements**: Session-level entry time tracker.
- **Edge Cases**: Complete leave & re-join assigns new timestamp $t_{\text{new}}$.

##### `TEST-T1-F31-05`: Simultaneous Entry-Time Tie-Breaking
- **Preconditions**: Peer A and Peer B have identical timestamps ($t_A = t_B = 5000\text{ms}$).
- **Inputs & Actions**: Execute grid sort.
- **Expected Outputs**: Deterministic tie-breaking by PeerId / endpoint name prevents slot oscillation.
- **Layout Oracle Assertions**: Slot ordering is stable across multiple layout solves.
- **Mock Requirements**: Stable sort comparator.
- **Edge Cases**: Layout refresh without participant changes produces identical coordinate assignments.

---

#### Feature 32: Alphabetical Sidebar Sorting

##### `TEST-T1-F32-01`: Case-Insensitive A-Z Alphabetical Order Verification
- **Preconditions**: Participants list with names: `["Charlie", "alice", "Bob", "david"]`.
- **Inputs & Actions**: Populate member list; trigger `peerListSortRows()`.
- **Expected Outputs**: Sidebar rows sorted case-insensitively: `["alice", "Bob", "Charlie", "david"]`.
- **Layout Oracle Assertions**:
  - Row 0 == "alice"
  - Row 1 == "Bob"
  - Row 2 == "Charlie"
  - Row 3 == "david"
- **Mock Requirements**: `calls_group_members.cpp:635-646`.
- **Edge Cases**: Names starting with numbers or symbols sort before letters predictably.

##### `TEST-T1-F32-02`: Dynamic Alphabetical Insertion of New Participant
- **Preconditions**: Sorted sidebar list: `["Alice", "David", "Frank"]`.
- **Inputs & Actions**: New participant "Charlie" joins call.
- **Expected Outputs**: "Charlie" inserted at index 1: `["Alice", "Charlie", "David", "Frank"]`.
- **Layout Oracle Assertions**: Row index for "Charlie" == 1.
- **Mock Requirements**: Dynamic row insertion in `PeerListContent`.
- **Edge Cases**: List scrolling position maintained during insertion.

##### `TEST-T1-F32-03`: Participant Name Update Dynamic Re-sorting
- **Preconditions**: User "Zachary" at bottom of list (index 10).
- **Inputs & Actions**: User updates profile name to "Aaron".
- **Expected Outputs**: Row for user moves from index 10 to index 0.
- **Layout Oracle Assertions**: Row at index 0 peer name == "Aaron".
- **Mock Requirements**: Peer update signal.
- **Edge Cases**: Fast consecutive name updates handle re-sorting cleanly.

##### `TEST-T1-F32-04`: Unicode and Accented Character Sorting
- **Preconditions**: Names: `["Åke", "Zoe", "Émile", "Adam"]`.
- **Inputs & Actions**: Execute alphabetical sort.
- **Expected Outputs**: Sorted via `QString::compare(..., Qt::CaseInsensitive)` standard unicode collation.
- **Layout Oracle Assertions**: Standard unicode alphabetical ordering verified.
- **Mock Requirements**: Unicode locale collation mock.
- **Edge Cases**: Emoji prefixes in user names handled gracefully.

##### `TEST-T1-F32-05`: State-Based Partitioning (Active vs Invited/Calling)
- **Preconditions**: Active members `["Charlie", "Alice"]`; Invited members `["David", "Bob"]`.
- **Inputs & Actions**: Execute sorting in `calls_group_members.cpp`.
- **Expected Outputs**:
  - Active members sorted alphabetically in top section: `["Alice", "Charlie"]`.
  - Invited members sorted alphabetically in bottom section: `["Bob", "David"]`.
- **Layout Oracle Assertions**:
  - Rows 0, 1 == Active members.
  - Rows 2, 3 == Invited members.
- **Mock Requirements**: `calls_group_members.cpp:638-646` (`groupA` vs `groupB`).
- **Edge Cases**: Invited member answers call -> transitions from bottom group to top active group alphabetically.

---

#### Feature 33: In-Call Sidebar Search Bar

##### `TEST-T1-F33-01`: Search Bar Geometry and Layout Anchoring
- **Preconditions**: Sidebar opened in Call Panel; sidebar width = `280px`.
- **Inputs & Actions**: Inspect search bar widget (`searchWrap`) in `_layout`.
- **Expected Outputs**:
  - `searchWrap` positioned at top of sidebar layout.
  - Height == `st::defaultInputField.heightMin + st::groupCallMembersTopSkip`.
  - Background filled with `st::groupCallMembersBg`.
- **Layout Oracle Assertions**: `searchWrap->y() == 0`, `searchWrap->width() == 280`.
- **Mock Requirements**: `calls_group_members.cpp:1978-1996`.
- **Edge Cases**: Sidebar resized -> search field width updates reactively.

##### `TEST-T1-F33-02`: Real-Time Member Filtering on Text Entry
- **Preconditions**: Sidebar contains 10 participants including "Alice Johnson", "Bob Smith", "Alicia Keys".
- **Inputs & Actions**: Type `"ali"` into search input field.
- **Expected Outputs**: `peerListSearchQueryChanged("ali")` executes; sidebar filters to 2 rows: "Alice Johnson" and "Alicia Keys".
- **Layout Oracle Assertions**: Visible row count == 2.
- **Mock Requirements**: `calls_group_members.cpp:1789-1791`.
- **Edge Cases**: Matching against both first name, last name, and @username.

##### `TEST-T1-F33-03`: Search Reset on Text Clearing
- **Preconditions**: Sidebar currently filtered by `"ali"` (2 rows visible).
- **Inputs & Actions**: Clear search input field (`searchField->setText("")`).
- **Expected Outputs**: All 10 participants restored in alphabetical order.
- **Layout Oracle Assertions**: Visible row count == 10.
- **Mock Requirements**: Empty string query event.
- **Edge Cases**: Clearing text via Backspace vs programmatic clear.

##### `TEST-T1-F33-04`: Keyboard ESC Shortcut Clearing in Search Bar
- **Preconditions**: Search field focused with text `"test"`.
- **Inputs & Actions**: Dispatch `Qt::Key_Escape` key event to search field.
- **Expected Outputs**: Search text is cleared, focus released, full list restored.
- **Layout Oracle Assertions**: Search input text == `""`, full list visible.
- **Mock Requirements**: Input field key handler.
- **Edge Cases**: Escape on already empty search field closes sidebar or keeps focus.

##### `TEST-T1-F33-05`: Case-Insensitive Substring Filtering
- **Preconditions**: Participant "Dr. Alexander Smith".
- **Inputs & Actions**: Search query `"ALEX"`, then `"smith"`, then `"dr."`.
- **Expected Outputs**: All 3 queries match "Dr. Alexander Smith".
- **Layout Oracle Assertions**: Target row remains visible across all 3 queries.
- **Mock Requirements**: Substring filter probe.
- **Edge Cases**: Queries with leading/trailing whitespace trimmed automatically.

---

#### Feature 34: Search Results Quick Actions

##### `TEST-T1-F34-01`: Direct Quick Pin Action on Search Row Click
- **Preconditions**: Sidebar filtered; matching row for Peer B displayed. Peer B has active video.
- **Inputs & Actions**: Click quick "Pin to Screen" action button on Peer B search row.
- **Expected Outputs**: Peer B video feed is pinned to grid without opening context menu.
- **Layout Oracle Assertions**:
  - `_call->pinVideoEndpoint(PeerB.videoEndpoint)` executed.
  - `isPinned(PeerB) == true`.
- **Mock Requirements**: `calls_group_members_row.cpp` quick action button click.
- **Edge Cases**: Quick pin on peer already pinned triggers unpin.

##### `TEST-T1-F34-02`: Direct Quick Chat Action on Search Row Click
- **Preconditions**: Sidebar search active; matching row for Peer B displayed.
- **Inputs & Actions**: Click quick "Open Chat" action button on Peer B row.
- **Expected Outputs**: Direct chat / in-meeting mention panel for Peer B is opened.
- **Layout Oracle Assertions**: Chat station or slide-out chat displays conversation with Peer B.
- **Mock Requirements**: `lng_group_call_open_chat` action trigger.
- **Edge Cases**: Participant with privacy restrictions for direct messaging displays group mention instead.

##### `TEST-T1-F34-03`: Quick Action Buttons Hover Animation & Highlight
- **Preconditions**: Mouse cursor moves over quick action button on search row.
- **Inputs & Actions**: Dispatch `QEvent::Enter` to quick action button.
- **Expected Outputs**: Button triggers ripple / highlight animation matching `calls.style`.
- **Layout Oracle Assertions**: Button opacity / background color updates to hover state.
- **Mock Requirements**: `Ui::IconButton` hover animation probe.
- **Edge Cases**: Fast mouse movement across multiple search rows updates hover states cleanly.

##### `TEST-T1-F34-04`: Quick Action State Sync with External Layout Mutations
- **Preconditions**: Search row visible for Peer A (currently unpinned).
- **Inputs & Actions**: Peer A is pinned via keyboard shortcut or tile click.
- **Expected Outputs**: Search row quick pin icon updates icon asset to active "Unpin" state.
- **Layout Oracle Assertions**: Button icon resource corresponds to pinned state.
- **Mock Requirements**: Reactive button state binding.
- **Edge Cases**: Unpinning from external source immediately reverts icon.

##### `TEST-T1-F34-05`: Coexistence of Quick Actions and Row Context Menu
- **Preconditions**: Search result row displayed.
- **Inputs & Actions**: Right-click on empty area of search row (outside quick action buttons).
- **Expected Outputs**: Full member context menu opens with all actions (Mute, Volume, Pin, Kick, Profile).
- **Layout Oracle Assertions**: Context menu popup opened at cursor location.
- **Mock Requirements**: Context menu event dispatch.
- **Edge Cases**: Right-clicking directly on quick action button still opens context menu.

---

#### Feature 35: Audio Lockout / Listen-Only Mode

##### `TEST-T1-F35-01`: Zero-Mic Device Initialization Invariant
- **Preconditions**: Group call launched in listen-only / audio lockout mode.
- **Inputs & Actions**: Start call session; observe `tgcalls` audio hardware initialization.
- **Expected Outputs**: `tgcalls` audio capture pipeline is NEVER initialized; microphone recording device is NOT opened.
- **Layout Oracle Assertions**: Zero OS audio capture handles allocated.
- **Mock Requirements**: `ZeroMicNetworkSpy` / WebRTC audio device module mock.
- **Edge Cases**: System with no physical microphone connected joins call without hardware error.

##### `TEST-T1-F35-02`: Outgoing Audio Packet Count Strict Zero Assertion
- **Preconditions**: Active call in listen-only mode for 10 seconds.
- **Inputs & Actions**: Simulate continuous loud ambient room noise / audio input.
- **Expected Outputs**: Zero outgoing RTP audio packets transmitted over network.
- **Layout Oracle Assertions**:
  - `total_outgoing_audio_packets == 0`.
  - `total_outgoing_audio_bytes == 0`.
- **Mock Requirements**: RTP network socket packet counter.
- **Edge Cases**: Spurt of audio input noise has zero effect on outgoing transmission.

##### `TEST-T1-F35-03`: Incoming Audio Playout & Reception Integrity
- **Preconditions**: Call in listen-only mode.
- **Inputs & Actions**: Remote speaker transmits audio stream.
- **Expected Outputs**: Incoming audio stream is received, decoded, and played through speakers/headphones with zero degradation.
- **Layout Oracle Assertions**: Audio output buffer renders incoming PCM frames smoothly.
- **Mock Requirements**: `tgcalls` audio playback pipeline.
- **Edge Cases**: Adjusting participant volume slider updates local playback volume correctly.

##### `TEST-T1-F35-04`: Mute/Unmute Action Immunity
- **Preconditions**: Call in listen-only mode.
- **Inputs & Actions**: Trigger programmatic unmute request or keypress.
- **Expected Outputs**: Unmute request is intercepted and discarded (`calls_group_panel.cpp:673`); audio capture remains inactive.
- **Layout Oracle Assertions**: Outgoing audio state remains `Muted / Disabled`.
- **Mock Requirements**: Call controller action handler.
- **Edge Cases**: Server admin sends unmute invite -> client displays notification but maintains zero-mic capture.

##### `TEST-T1-F35-05`: OS Microphone Permission Revocation Immunity
- **Preconditions**: Active listen-only call.
- **Inputs & Actions**: Revoke Windows OS microphone privacy permission for Telegram.
- **Expected Outputs**: Call continues uninterrupted; zero error dialogs or warnings displayed because client does not request mic access.
- **Layout Oracle Assertions**: Call state remains `Connected`.
- **Mock Requirements**: OS permission toggle simulation.
- **Edge Cases**: Re-granting OS permission has zero impact on listen-only operation.

---

#### Feature 36: Microphone Controls Removal

##### `TEST-T1-F36-01`: Microphone Tooltip Suppression Invariant
- **Preconditions**: Group call launched in listen-only mode.
- **Inputs & Actions**: Inspect `_stickedTooltipsShown` in `calls_group_panel.cpp:244-245`.
- **Expected Outputs**: `StickedTooltip::Microphone` flag is set by default, permanently suppressing microphone onboarding hints.
- **Layout Oracle Assertions**: `(_stickedTooltipsShown & StickedTooltip::Microphone) != 0`.
- **Mock Requirements**: `Panel` constructor probe.
- **Edge Cases**: Hovering over bottom controls bar never spawns microphone tooltip popup.

##### `TEST-T1-F36-02`: Bottom Bar Mic Toggle Handler No-Op Assertion
- **Preconditions**: Call panel active.
- **Inputs & Actions**: Invoke click callback on `_mute` button (`calls_group_panel.cpp:673`).
- **Expected Outputs**: Callback returns immediately without modifying call mute state or emitting audio toggle signal.
- **Layout Oracle Assertions**: Audio recording state is unchanged.
- **Mock Requirements**: Click event dispatcher on `_mute`.
- **Edge Cases**: Rapid clicking on bottom bar center produces zero side effects.

##### `TEST-T1-F36-03`: Push-to-Talk Spacebar Shortcut Invalidation
- **Preconditions**: Call panel focused.
- **Inputs & Actions**: Press and hold `Qt::Key_Space` (standard Push-to-Talk key).
- **Expected Outputs**: Key press event is ignored or passed through; Push-to-Talk audio broadcast is NOT initiated.
- **Layout Oracle Assertions**: Outgoing audio packet count == 0.
- **Mock Requirements**: Key event filter in `Panel`.
- **Edge Cases**: Spacebar press while typing in chat field inserts spaces normally.

##### `TEST-T1-F36-04`: Symmetric Sizing of Call Controls Bar Without Mic Button
- **Preconditions**: Call bottom bar with Camera, Screen Share, Chat, and Hangup buttons.
- **Inputs & Actions**: Layout bottom bar in listen-only mode.
- **Expected Outputs**: Remaining buttons centered symmetrically across bottom bar without awkward gaps or missing placeholder voids.
- **Layout Oracle Assertions**:
  - Center of controls container aligns with `width() / 2`.
  - Button spacing is uniform ($g = \text{st::groupCallButtonSkip}$).
- **Mock Requirements**: `calls_group_panel.cpp` bottom controls layout solver.
- **Edge Cases**: Resizing call panel horizontally retains symmetric centering.

##### `TEST-T1-F36-05`: Call Settings Audio Input Selector Disabled
- **Preconditions**: In-call settings dialog opened.
- **Inputs & Actions**: Inspect Audio Settings section.
- **Expected Outputs**: Microphone input device selector is disabled or marked with "Listen-Only Mode Active" status badge.
- **Layout Oracle Assertions**: Input device dropdown `isEnabled() == false`.
- **Mock Requirements**: `calls_group_settings.cpp` UI probe.
- **Edge Cases**: Output device selector (speakers/headphones) remains fully enabled and selectable.

---

#### Feature 37: Permanent Listen-Only Invariant

##### `TEST-T1-F37-01`: Server-Side Unmute Privilege Elevation Rejection
- **Preconditions**: User joins call as listen-only participant.
- **Inputs & Actions**: Server / Admin sends MTProto update `phone.groupCallParticipant` with `can_self_unmute = true` and `muted_by_you = false`.
- **Expected Outputs**: Client Central Controller enforces permanent invariant: drops outgoing audio descriptors and keeps capture pipeline closed.
- **Layout Oracle Assertions**: Client outgoing audio state remains disabled.
- **Mock Requirements**: MTProto RPC update injector.
- **Edge Cases**: Multiple consecutive admin unmute invitations all rejected automatically.

##### `TEST-T1-F37-02`: Outgoing WebRTC SDP Audio Descriptor Stripping
- **Preconditions**: WebRTC connection establishment / renegotiation.
- **Inputs & Actions**: Inspect generated SDP offer / answer.
- **Expected Outputs**: Outgoing SDP media section for audio contains `a=recvonly` or `m=audio 0` (zero port), stripping `sendrecv` capabilities.
- **Layout Oracle Assertions**: SDP contains `a=recvonly` and zero outgoing audio SSRCs.
- **Mock Requirements**: WebRTC SDP inspector spy.
- **Edge Cases**: Video stream renegotiation does not accidentally re-enable audio send channel.

##### `TEST-T1-F37-03`: Reconnection Invariant Preservation
- **Preconditions**: Active call loses network connection for 3 seconds.
- **Inputs & Actions**: WebRTC peer connection reconnects (`ICE state -> Connected`).
- **Expected Outputs**: Re-established WebRTC peer connection initializes only receive channels; zero-mic capture invariant preserved.
- **Layout Oracle Assertions**: Outgoing audio RTP packet count remains 0 after reconnection.
- **Mock Requirements**: Network disconnect/reconnect simulator.
- **Edge Cases**: Rapid network flapping (3 drops in 5 seconds) maintains invariant.

##### `TEST-T1-F37-04`: RPC Audio State Broadcast Suppression
- **Preconditions**: User in group call.
- **Inputs & Actions**: Simulate internal client audio toggle attempt.
- **Expected Outputs**: Client NEVER transmits MTProto RPC `phone.editGroupCallParticipant` requesting to un-mute or raise hand to speak.
- **Layout Oracle Assertions**: Sent RPC list contains zero audio modification requests.
- **Mock Requirements**: MTProto request interceptor.
- **Edge Cases**: Raising hand for text questions (if supported) does not request microphone access.

##### `TEST-T1-F37-05`: End-to-End Permanent Invariant Assertion Throughout Call Lifecycle
- **Preconditions**: Complete group call session from join to leave (duration: 30 simulated seconds) with mixed video, screen shares, and chat interactions.
- **Inputs & Actions**: Execute full call workflow.
- **Expected Outputs**: At every single millisecond $t \in [0, T_{\text{end}}]$, zero audio hardware capture was active and zero audio packets were sent.
- **Layout Oracle Assertions**:
  - $\max(\text{AudioCaptureDeviceHandles}) == 0$.
  - $\sum \text{OutgoingAudioPackets} == 0$.
- **Mock Requirements**: Full lifecycle state monitor.
- **Edge Cases**: Exiting call releases all media resources cleanly without audio subsystem hang.

---

## 5. Python Test Runner Mapping & Module Organization

The 110 Tier 1 test cases specified above map directly into the executable Python test architecture in `tests/e2e/`:

```text
tests/e2e/
├── framework/
│   ├── assertions.py                 # Custom geometry, rect intersection & floating point assertions
│   ├── call_simulator.py             # Emulates WebRTC video streams, endpoints, entry timestamps
│   ├── grid_solver_oracle.py         # Python reference math implementation of countWide / countGrid
│   ├── overlay_probe.py              # Qt window flag, geometry, and opacity inspectors
│   └── zero_mic_spy.py               # SDP inspection and zero-mic invariant verification
├── tier1_features/
│   ├── test_t1_grid_pin.py           # Features 16-24 (45 test cases)
│   ├── test_t1_floating_overlay.py   # Features 25-28 (20 test cases)
│   ├── test_t1_embedded_chat.py      # Features 29-30 (10 test cases)
│   └── test_t1_sidebar_audio.py      # Features 31-37 (35 test cases)
└── run_all.py                        # Standalone runner: py tests/e2e/run_all.py --tier 1
```

### Direct Feature-to-File Test Mapping

| Category | Features | Test File Path | Test Method Prefix | Tests |
| :--- | :--- | :--- | :--- | :---: |
| **Cat 5** | F16: Discrete Presets (1x1, 2x2, 3x3) | `tier1_features/test_t1_grid_pin.py` | `test_f16_presets_*` | 5 |
| **Cat 5** | F17: Dynamic 50/50 Split Solver | `tier1_features/test_t1_grid_pin.py` | `test_f17_dynamic_split_*` | 5 |
| **Cat 5** | F18: Uncapped Dynamic Grid Scaling | `tier1_features/test_t1_grid_pin.py` | `test_f18_uncapped_scale_*` | 5 |
| **Cat 5** | F19: Persistent Pin Slot Allocator | `tier1_features/test_t1_grid_pin.py` | `test_f19_pin_allocator_*` | 5 |
| **Cat 5** | F20: Dynamic Pinned Auto-Scaling | `tier1_features/test_t1_grid_pin.py` | `test_f20_pinned_autoscale_*` | 5 |
| **Cat 5** | F21: Multi-Pin Capability | `tier1_features/test_t1_grid_pin.py` | `test_f21_multipin_*` | 5 |
| **Cat 5** | F22: Adjustable Pinned Panel Sizes | `tier1_features/test_t1_grid_pin.py` | `test_f22_panel_resize_*` | 5 |
| **Cat 5** | F23: Grid Unpinning & Removal | `tier1_features/test_t1_grid_pin.py` | `test_f23_unpin_removal_*` | 5 |
| **Cat 5** | F24: Pin to Grid Context Menu | `tier1_features/test_t1_grid_pin.py` | `test_f24_context_menu_pin_*` | 5 |
| **Cat 6** | F25: Frameless Transparent Overlay | `tier1_features/test_t1_floating_overlay.py` | `test_f25_frameless_overlay_*` | 5 |
| **Cat 6** | F26: Ctrl+Shift+T Shortcut Toggle | `tier1_features/test_t1_floating_overlay.py` | `test_f26_shortcut_toggle_*` | 5 |
| **Cat 6** | F27: Opacity Adjustment Ctrl+Wheel | `tier1_features/test_t1_floating_overlay.py` | `test_f27_opacity_ctrl_wheel_*` | 5 |
| **Cat 6** | F28: Draggable Canvas & Esc Dismiss | `tier1_features/test_t1_floating_overlay.py` | `test_f28_drag_esc_dismiss_*` | 5 |
| **Cat 7** | F29: Embedded Chat & Dynamic Resize | `tier1_features/test_t1_embedded_chat.py` | `test_f29_chat_resize_*` | 5 |
| **Cat 7** | F30: In-Meeting Chat Search | `tier1_features/test_t1_embedded_chat.py` | `test_f30_chat_search_*` | 5 |
| **Cat 8** | F31: Chronological Grid Sorting | `tier1_features/test_t1_sidebar_audio.py` | `test_f31_chrono_grid_sort_*` | 5 |
| **Cat 8** | F32: Alphabetical Sidebar Sorting | `tier1_features/test_t1_sidebar_audio.py` | `test_f32_alpha_sidebar_sort_*` | 5 |
| **Cat 8** | F33: In-Call Sidebar Search Bar | `tier1_features/test_t1_sidebar_audio.py` | `test_f33_sidebar_searchbar_*` | 5 |
| **Cat 8** | F34: Search Results Quick Actions | `tier1_features/test_t1_sidebar_audio.py` | `test_f34_quick_actions_*` | 5 |
| **Cat 8** | F35: Audio Lockout / Listen-Only | `tier1_features/test_t1_sidebar_audio.py` | `test_f35_audio_lockout_*` | 5 |
| **Cat 8** | F36: Mic Controls Removal | `tier1_features/test_t1_sidebar_audio.py` | `test_f36_mic_controls_removal_*` | 5 |
| **Cat 8** | F37: Permanent Listen-Only Invariant | `tier1_features/test_t1_sidebar_audio.py` | `test_f37_permanent_listen_only_*` | 5 |
| **Total** | **22 Features** | **4 Test Suites** | **110 Unique Test Methods** | **110** |

---

## 6. Summary & Traceability Matrix

| Feature ID | Feature Name | Source File Target | Key Functions / Symbols | Tier 1 Tests |
| :---: | :--- | :--- | :--- | :---: |
| **16** | Discrete Layout Presets | `calls_group_viewport.cpp` | `setSlotCount()`, `countWide()` | 5 |
| **17** | Dynamic Grid Solver (50/50 Split) | `calls_group_viewport.cpp` | `countWide()`, `_slotCount == 0` | 5 |
| **18** | Uncapped Dynamic Main Grid Scaling | `calls_group_viewport.cpp` | `countWide()`, `slices = ceil(sqrt(N))` | 5 |
| **19** | Persistent Pin Slot Allocator | `calls_group_viewport.cpp` | `_pinnedEndpoints`, `_pinnedSlots` | 5 |
| **20** | Dynamic Pinned Auto-Scaling | `calls_group_display_coordinator.cpp` | `pinToScreen()`, `pinnedCount()` | 5 |
| **21** | Multi-Pin Capability | `calls_group_viewport.cpp` | `togglePin()`, `_pinnedEndpoints` | 5 |
| **22** | Adjustable Pinned Panel Sizes | `calls_group_viewport.cpp` | Splitter math, aspect ratio bounds | 5 |
| **23** | Grid Unpinning & Removal Actions | `calls_group_viewport.cpp` | `remove()`, `togglePin(..., false)` | 5 |
| **24** | Pin to Grid Context Menu Actions | `calls_group_members.cpp` | `lng_group_call_context_pin_to_grid` | 5 |
| **25** | Frameless Transparent Overlay | `calls_group_floating_overlay.cpp` | `FramelessWindowHint`, `WA_TranslucentBackground` | 5 |
| **26** | Ctrl+Shift+T Keyboard Toggle | `calls_group_floating_overlay.cpp` | `_toggleShortcut`, `toggle()` | 5 |
| **27** | Opacity Adjustment via Ctrl+Wheel | `calls_group_floating_overlay.cpp` | `wheelEvent()`, `_opacity` $[0.2, 1.0]$ | 5 |
| **28** | Draggable Canvas & Esc Dismiss | `calls_group_floating_overlay.cpp` | `mouseMoveEvent()`, `Key_Escape` | 5 |
| **29** | Embedded Chat & Dynamic Resize | `calls_group_floating_overlay.cpp` | `setupChatContent()`, `_messagesUi->move()` | 5 |
| **30** | In-Meeting Chat Search | `calls_group_messages.cpp` | Search query filter, match highlight | 5 |
| **31** | Chronological Entry-Time Sort | `calls_group_viewport.cpp` | `unpinnedTiles`, `entryTime()` | 5 |
| **32** | Alphabetical Sidebar Sorting | `calls_group_members.cpp` | `peerListSortRows()`, `QString::compare` | 5 |
| **33** | In-Call Sidebar Search Bar | `calls_group_members.cpp` | `searchWrap`, `searchByQuery()` | 5 |
| **34** | Search Results Quick Actions | `calls_group_members.cpp` | Direct pin/chat action buttons | 5 |
| **35** | Audio Lockout / Listen-Only Mode | `calls_group_panel.cpp` | Zero audio device capture in `tgcalls` | 5 |
| **36** | Microphone Controls Removal | `calls_group_panel.cpp` | `StickedTooltip::Microphone`, mic click no-op | 5 |
| **37** | Permanent Listen-Only Invariant | `calls_group_call.cpp` | Zero-mic invariant, SDP `recvonly` | 5 |
| **Total** | **Categories 5 – 8** | **All Modules Verified** | **Complete Coverage** | **110** |
