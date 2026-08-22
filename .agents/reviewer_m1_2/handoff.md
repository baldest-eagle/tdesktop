# Handoff Report: Milestone M1 Reviewer 2

**Agent**: Reviewer 2 (Milestone M1)  
**Parent**: Sub-Orchestrator M1 (`e26ac6b6-cadb-4cf1-a64f-cacfbc8879fa`)  
**Date**: 2026-08-20  

---

## 1. Observation

Direct code inspections of Worker 1's implementation:

1. **`calls_group_floating_overlay.h:52,62-68` & `calls_group_floating_overlay.cpp:127-136, 154-167`**:
   - `setupChatContent()` instantiates `_messagesUi` using `this`, `_panel->uiShow()`, `MessagesMode::GroupCall`, `call->messages()->listValue()`, `nullptr`, `call->messages()->idUpdates()`, `call->canManageValue()`, `call->messagesEnabledValue()`, and `[=](QPoint) { return false; }`.
   - `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` correctly positions the scroll container anchored to `height() - 4` with 36px reserved for top controls.
   - `resizeEvent()` updates positions for `_messagesUi`, `_closeBtn` (`width() - 30, 5`), and `_passthroughBtn` (`width() - 55, 5`).
   - Style conformance: empty line before class closing brace, alphabetical include ordering with styles separated, `!isHidden()` used for visibility checks, `_q` string literals, and no single-line comments.

2. **`calls_group_viewport.cpp:560-572`**:
   - The 50/50 split condition `if (count == 2 && slotConstraint == 0)` was relocated before `if (fixedGridDim > 0)`.
   - Dynamic 50/50 layout calculates `halfW = (outerWidth - skip) / 2` and sets tile 1 width as `outerWidth - halfW - skip`, preventing 1px rounding discrepancies on odd outer widths.
   - Both `sizes[i].columns` and `sizes[i].rows` are assigned, and `result.useColumns = true; return result;` returns immediately.

3. **`calls_group_members.cpp:1451-1454, 1534-1538`**:
   - `tr::lng_group_call_context_pin_to_grid(tr::now)` is wired for unpinned camera tiles to call `_call->pinVideoEndpoint(camera)`.
   - `tr::lng_group_call_open_chat(tr::now)` is added in the `else` branch of `if (participantPeer->isUser())` to trigger `showHistory` (`window->showPeerHistory(participantPeer, ...)`) for channel and group participants.

---

## 2. Logic Chain

1. **Overlay Geometry & Lifecycle**:
   - `MessagesUi` coordinates in `move(left, bottom, width, availableHeight)` treat `bottom` as the bottom edge of the widget container. Passing `bottom = height() - 4` and `availableHeight = height() - 40` ensures the viewport spans `[y = 36, y = height() - 4]` without overlapping the title or buttons.
   - Memory management is clean: `FloatingOverlay` is parented to `Panel` via `std::unique_ptr<FloatingOverlay>`, ensuring deterministic destruction with no dangling callbacks or orphaned Qt widgets.

2. **Viewport Split Logic & Odd-Width Handling**:
   - In dynamic mode (`slotConstraint == 0`), `fixedGridDim` is 0. Moving the 50/50 check before `fixedGridDim > 0` resolves the unreachable code path.
   - Using `outerWidth - halfW - skip` for the right tile width ensures that when `outerWidth - skip` is odd, the 1 extra pixel is absorbed cleanly rather than leaving a blank column.

3. **Participant Chat Actions**:
   - Channels and megagroups participating in calls cannot receive 1-on-1 private messages (`lng_context_send_message`), but their history can be opened in Telegram Desktop. Providing `lng_group_call_open_chat` routing to `showPeerHistory` resolves this functionality gap.

---

## 3. Caveats

- Fixed grid modes (1x1, 2x2, 3x3) bypass the dynamic 50/50 split check by design as `slotConstraint != 0`.
- Screen share endpoint actions continue using their designated strings (`lng_group_call_context_pin_screen` / `lng_group_call_context_unpin_screen`).
- No caveats regarding safety, memory, or style rules.

---

## 4. Conclusion

**Verdict**: **APPROVE**  
Worker 1's implementation is verified to be logically complete, free of integrity violations or facade logic, and strictly compliant with `REVIEW.md` and repository guidelines.

---

## 5. Verification Method

### Files Inspected
1. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
2. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
3. `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
4. `Telegram/SourceFiles/calls/group/calls_group_members.cpp`

### Invalidation Conditions
- Any occurrence of dead code in `countWide` solver for dynamic layout.
- Any negative or misaligned y-coordinates in `MessagesUi` scroll container within `FloatingOverlay`.
- Inability to open chat history for non-user participants in group calls.
