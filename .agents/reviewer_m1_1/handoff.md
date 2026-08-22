# Handoff Report: Milestone M1 — Reviewer 1 Audit & Review

**Agent**: Reviewer 1 (Milestone M1)  
**Roles**: Reviewer & Critic  
**Parent**: Sub-Orchestrator M1 (`e26ac6b6-cadb-4cf1-a64f-cacfbc8879fa`)  
**Date**: 2026-08-20  
**Verdict**: **APPROVE**

---

## 1. Observation

Direct code verification across target files and related project sources:

1. **`calls_group_floating_overlay.h:60-68` & `calls_group_floating_overlay.cpp:125-167`**:
   - `FloatingOverlay::setupChatContent()` instantiates `std::make_unique<MessagesUi>` passing `this`, `_panel->uiShow()`, `MessagesMode::GroupCall`, `call->messages()->listValue()`, `nullptr`, `call->messages()->idUpdates()`, `call->canManageValue()`, `call->messagesEnabledValue()`, and `[=](QPoint) { return false; }`.
   - `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` correctly sets `left = 4`, `bottom = height() - 4`, `width = width() - 8`, and `availableHeight = height() - 40`.
   - `resizeEvent()` dynamically recalculates geometries for `_messagesUi`, `_closeBtn` (`width() - 30, 5`), and `_passthroughBtn` (`width() - 55, 5`).
   - String literals use `u"..."_q` (`u"Ctrl+Shift+T"_q`, `u"Chat"_q`), `!isHidden()` is used in place of `isVisible()`, `QPainter` is constructed with `auto p = QPainter(this)`, and class declarations maintain an empty line before the closing brace (`calls_group_floating_overlay.h:68`). No single-line comments exist.

2. **`calls_group_viewport.cpp:560-572`**:
   - The 50/50 split condition `if (count == 2 && slotConstraint == 0)` is positioned ahead of `if (fixedGridDim > 0)`.
   - Geometry calculation for tile 0 is `{ 0, 0, halfW, outerHeight }` and for tile 1 is `{ halfW + skip, 0, outerWidth - halfW - skip, outerHeight }`.
   - `result.useColumns = true;` is set before returning `result`.

3. **`calls_group_members.cpp:1445-1466, 1530-1538`**:
   - `tr::lng_group_call_context_pin_to_grid(tr::now)` is wired for unpinned camera streams in `createRowContextMenu`, calling `_call->pinVideoEndpoint(camera)`.
   - `tr::lng_group_call_open_chat(tr::now)` is wired in the `else` branch of `if (participantPeer->isUser())` for non-user participants (channels and groups), calling `showHistory`.
   - Both `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` exist in `Telegram/Resources/langs/lang.strings:6463-6464`.

---

## 2. Logic Chain

1. **Floating Overlay Coordinate Calculation**:
   - In `calls_group_messages_ui.cpp:1885-1893`, `MessagesUi::updateGeometries()` sets `_scroll` geometry to `_left, bottom - min, _width, min`, where `min = std::min(height, _availableHeight)`.
   - When `bottom = height() - 4` and `_availableHeight = height() - 40`, `bottom - min >= (height() - 4) - (height() - 40) = 36`.
   - This keeps message scrolling strictly within `y >= 36` and `y <= height() - 4`, protecting the header buttons and title at `y = 5..10`.
   - Dynamic button repositioning in `resizeEvent` ensures window resizing maintains proper header button positioning.

2. **50/50 Viewport Grid Layout**:
   - Placing `if (count == 2 && slotConstraint == 0)` outside of `if (fixedGridDim > 0)` fixes the unreachable dead code branch that occurred when `slotConstraint == 0` (where `fixedGridDim` evaluates to `0`).
   - Using `outerWidth - halfW - skip` for the second tile ensures exact pixel coverage without 1px rounding gaps on odd-width viewports.

3. **Context Action Wiring**:
   - Camera feeds correctly toggle between `lng_group_call_context_unpin_camera` when pinned and `lng_group_call_context_pin_to_grid` when unpinned.
   - Non-user call participants (channels/groups) now receive a valid context menu action `lng_group_call_open_chat` mapping to `showHistory`, resolving the missing navigation action for non-user participants.

4. **Integrity & Code Quality**:
   - No dummy implementations, fake data, hardcoded test hooks, or style deviations are present. All `REVIEW.md` and `AGENTS.md` guidelines are satisfied.

---

## 3. Caveats

- Fixed grid mode constraints (`slotConstraint` 1, 4, 9) continue to use their dedicated grid solver branches and are unconstrained by the dynamic 50/50 condition.
- Screen endpoints continue to use `lng_group_call_context_pin_screen` and `lng_group_call_context_unpin_screen`.
- No caveats regarding memory safety or lifetimes: `MessagesUi` is owned via `std::unique_ptr`, UI widgets use `object_ptr`, and context menus are transient Qt objects with safe captures.

---

## 4. Conclusion

The implementation produced by Worker 1 satisfies all requirements for Milestone M1 with zero integrity violations and strict compliance with `REVIEW.md` and `AGENTS.md`.

**Verdict**: **APPROVE**

---

## 5. Verification Method

### Files to Inspect
1. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
2. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
3. `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
4. `Telegram/SourceFiles/calls/group/calls_group_members.cpp`
5. `c:\Users\kyleh\tdesktop\.agents\reviewer_m1_1\review.md`

### Invalidation Conditions
- Any occurrence of `_messagesUi->move(4, 36, ...)` which would misplace the scroll view at negative coordinates.
- Any nesting of `if (count == 2 && slotConstraint == 0)` inside `if (fixedGridDim > 0)` which would disable dynamic 50/50 split.
- Missing `lng_group_call_open_chat` in `calls_group_members.cpp:1536`.
