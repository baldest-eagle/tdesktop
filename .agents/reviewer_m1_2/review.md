# Review Report: Milestone M1 — Calls UI, Floating Overlay & Viewport Grid

**Reviewer**: Reviewer 2 (Milestone M1)  
**Parent**: Sub-Orchestrator M1 (`e26ac6b6-cadb-4cf1-a64f-cacfbc8879fa`)  
**Target Files**:
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_members.cpp`

---

## Review Summary

**Verdict**: **APPROVE**

Worker 1 has correctly, cleanly, and comprehensively implemented all requirements assigned in Milestone M1:
1. `FloatingOverlay::setupChatContent()` instantiated with live `MessagesUi` data streams, proper bottom-anchoring geometry, and header button repositioning in `resizeEvent()`.
2. The 50/50 viewport grid layout split condition for 2 active feeds in dynamic mode (`slotConstraint == 0`) was moved out of unreachable dead code and properly handles odd/even boundary widths without rounding gaps.
3. Group call context actions `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` were correctly wired for camera tiles and non-user participants (channels/groups).
4. Full compliance with `REVIEW.md` and `AGENTS.md` (no single-line comments in new code, trailing return types, proper `auto` usage, `!isHidden()` checks, `_q` literals, alphabetical header ordering, RAII/lifecycle safety). No integrity violations found.

---

## Detailed Findings & Verification

### 1. Floating Overlay Chat Content & Lifecycle
- **Instantiation**: `MessagesUi` is constructed in `FloatingOverlay::setupChatContent()` using `this` as parent, `_panel->uiShow()`, `MessagesMode::GroupCall`, and live producers from `_panel->call()` (`listValue()`, `idUpdates()`, `canManageValue()`, `messagesEnabledValue()`).
- **Geometry Anchoring**: `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` correctly bottom-anchors message scrolling at `y = height() - 4`, with total available scroll height `height() - 40`, reserving 36px at the top (y = 0 to 36) for header label and controls.
- **Resize Handling**: `resizeEvent` updates geometry for `_messagesUi`, `_closeBtn` (`width() - 30, 5`), and `_passthroughBtn` (`width() - 55, 5`).
- **Ownership & Memory Safety**: `FloatingOverlay` is owned via `std::unique_ptr<FloatingOverlay>` by `Panel`. All child UI components use `object_ptr` or `std::unique_ptr` and are safely destroyed when `Panel` / `FloatingOverlay` teardown occurs.

### 2. Viewport 50/50 Grid Split Math & Dead-Code Fix
- **Dead Code Removal**: Relocated `if (count == 2 && slotConstraint == 0)` outside `if (fixedGridDim > 0)`. When `slotConstraint == 0` (dynamic mode), `fixedGridDim` is 0, which previously caused the 50/50 branch to be entirely unreachable.
- **Layout Math & Boundary Verification**:
  - `halfW = (outerWidth - skip) / 2`
  - Tile 0: `{ 0, 0, halfW, outerHeight }`
  - Tile 1: `{ halfW + skip, 0, outerWidth - halfW - skip, outerHeight }`
  - Verified for odd and even `outerWidth` (e.g. `outerWidth = 1921, skip = 10` -> `halfW = 955`, Tile 0 width = 955, Tile 1 width = 956, total span = 955 + 10 + 956 = 1921). Zero pixel rounding gap.
  - Sets both `sizes[i].columns` and `sizes[i].rows`, along with `result.useColumns = true`, ensuring safety across all rendering paths.

### 3. Participant Context Actions
- **Pin to Grid**: Unpinned camera feeds in `calls_group_members.cpp` display `tr::lng_group_call_context_pin_to_grid(tr::now)` invoking `_call->pinVideoEndpoint(camera)`.
- **Open Chat for Channels & Groups**: Added `tr::lng_group_call_open_chat(tr::now)` under the `else` branch of `if (participantPeer->isUser())` which triggers `showHistory` via `window->showPeerHistory(participantPeer, ...)`.
- Profile viewing differentiates between users (`lng_context_view_profile`), channels (`lng_context_view_channel`), and groups (`lng_context_view_group`).

### 4. Style & Mechanical Conformance (`REVIEW.md`)
- **Empty line before class closing brace**: Present in `FloatingOverlay`.
- **No single-line comments**: Checked and clean.
- **Use `!isHidden()`**: Replaced `isVisible()` with `!isHidden()` in `FloatingOverlay::toggle()` and `FloatingOverlay::isVisible()`.
- **Literal syntax**: Uses `u"..."_q` for QString literals.
- **Include ordering**: Correctly sorted alphabetically, nested folders first, `styles/style_calls.h` separated before Qt headers.

---

## Adversarial Review & Attack Surface Analysis

| Challenge Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| **Odd Viewport Dimensions** (`outerWidth = 1921`, `skip = 10`) | Equal tiling without 1px gap or overflow | Tile 0 width 955, Tile 1 width 956, total span 1921 | PASS |
| **Fixed vs Dynamic Grid Modes** (`slotConstraint` in `{1, 4, 9}`) | Fixed grid takes precedence over 50/50 dynamic split | `slotConstraint == 0` condition guards dynamic split; fixed modes fall through to `fixedGridDim > 0` | PASS |
| **Overlay Destruction on Call Termination** | Clean teardown without dangling pointers | Owned as `std::unique_ptr` by `Panel`; all sub-widgets use `object_ptr`/`std::unique_ptr` parented to overlay | PASS |
| **Non-User Participant History Navigation** | Safely routes to channel/group history | `showHistory` delegates to `SessionController::showPeerHistory`, supporting all `PeerData` types | PASS |
| **Integrity Audit** | Genuine implementation without stubs, hardcoded test results, or bypasses | Fully implemented production logic matching codebase conventions | PASS |

---

## Verdict
**APPROVE**
