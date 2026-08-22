# Handoff Report: Milestone M1 — Worker 1 Implementation

**Worker**: Worker 1 (Milestone M1)  
**Parent**: Sub-Orchestrator M1 (`e26ac6b6-cadb-4cf1-a64f-cacfbc8879fa`)  
**Date**: 2026-08-20  

---

## 1. Observation

Direct code observations from the pre-existing codebase:

1. **`calls_group_floating_overlay.cpp:149-159`**:
   `FloatingOverlay::setupChatContent()` was an uninstantiated stub:
   ```cpp
   void FloatingOverlay::setupChatContent() {
       if (!_panel) {
           return;
       }
   }
   ```
   Furthermore, `_messagesUi->move(4, 36, width() - 8, height() - 40)` in `resizeEvent` erroneously passed `36` as `bottom`, which positioned the internal message scroll viewport at negative y-coordinates `36 - minHeight`. Header buttons `_closeBtn` and `_passthroughBtn` were local variables not repositioned upon resize.

2. **`calls_group_viewport.cpp:569-584`**:
   The 50/50 split condition was nested inside `if (fixedGridDim > 0)`:
   ```cpp
   const auto slotConstraint = _slotCount.current();
   const auto fixedGridDim = (slotConstraint == 1) ? 1 : (slotConstraint == 4) ? 2 : (slotConstraint == 9) ? 3 : 0;
   if (fixedGridDim > 0) {
       ...
       if (count == 2 && slotConstraint == 0) {
           ...
       }
   }
   ```
   When `slotConstraint == 0`, `fixedGridDim` evaluates to `0`, making `if (fixedGridDim > 0)` false and rendering lines 578-584 completely unreachable.

3. **`calls_group_members.cpp:1445-1466, 1523-1535`**:
   `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` were present in `lang.strings` but unwired in `createRowContextMenu`:
   ```cpp
   if (participantPeer->isUser()) {
       result->addAction(tr::lng_context_send_message(tr::now), showHistory);
   }
   // Non-user peers had no chat history entry
   ```

---

## 2. Logic Chain

1. **Floating Overlay Chat Rendering & UI Lifetime**:
   - `MessagesUi` requires `QWidget* parent`, `std::shared_ptr<ChatHelpers::Show>`, `MessagesMode`, and producers for messages, top donors, id updates, manage rights, and enabled state (`calls_group_messages_ui.h:53-62`).
   - By constructing `_messagesUi` in `setupChatContent()` with `this`, `_panel->uiShow()`, `MessagesMode::GroupCall`, `_panel->call()->messages()->listValue()`, `nullptr`, `_panel->call()->messages()->idUpdates()`, `_panel->call()->canManageValue()`, `_panel->call()->messagesEnabledValue()`, and `[=](QPoint) { return false; }`, the overlay receives live message streams.
   - Calling `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` correctly sets `left = 4`, `bottom = height() - 4`, `width = width() - 8`, and `availableHeight = height() - 40` (reserving header space from y = 0 to 36).
   - Storing `_title`, `_closeBtn`, and `_passthroughBtn` as `object_ptr` members allows `resizeEvent()` to reposition `_closeBtn` to `(width() - 30, 5)` and `_passthroughBtn` to `(width() - 55, 5)`.

2. **Dynamic 50/50 Viewport Grid Layout**:
   - Moving `if (count == 2 && slotConstraint == 0)` outside and before `if (fixedGridDim > 0)` restores the branch for 2 active feeds in dynamic layout mode.
   - Calculating `sizes[1].columns = sizes[1].rows = { halfW + skip, 0, outerWidth - halfW - skip, outerHeight }` ensures no pixel gaps occur on odd outer widths.
   - Returning `result` immediately with `result.useColumns = true` bypasses the dynamic solver fallback which was erroneously stacking feeds vertically or letterboxing them.

3. **Participant Context Actions**:
   - Using `tr::lng_group_call_context_pin_to_grid(tr::now)` for unpinned camera endpoints aligns the UI with group call grid pinning behavior.
   - Adding `result->addAction(tr::lng_group_call_open_chat(tr::now), showHistory);` under `else` of `if (participantPeer->isUser())` enables users to open chat history for channels and groups participating in the call.

---

## 3. Caveats

- Fixed grid modes (1x1, 2x2, 3x3) maintain their respective `fixedGridDim` constraints and are unaffected by the dynamic 50/50 split condition.
- Screen sharing feeds continue to use `lng_group_call_context_pin_screen` / `lng_group_call_context_unpin_screen`.
- No caveats regarding ownership or lifetimes: `FloatingOverlay` is parented to `Panel`, child widgets use `object_ptr`, and Qt shortcut handlers capture safely by value.

---

## 4. Conclusion

All three Milestone M1 worker tasks have been genuinely and fully implemented:
1. `FloatingOverlay::setupChatContent()` instantiated with live `MessagesUi`, accurate geometry anchoring, dynamic button repositioning on resize, and strict compliance with `REVIEW.md`.
2. 50/50 viewport grid layout restored for 2-feed dynamic mode without dead code or pixel-rounding gaps.
3. `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` successfully wired into participant context menus.

---

## 5. Verification Method

### Files to Inspect
1. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
2. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
3. `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
4. `Telegram/SourceFiles/calls/group/calls_group_members.cpp`

### Verification Invalidation Conditions
- If `_messagesUi->move(...)` bottom parameter is passed as `36` instead of `height() - 4`, chat scroll will be placed off-screen.
- If `count == 2 && slotConstraint == 0` is inside `if (fixedGridDim > 0)`, dynamic 50/50 layout will never execute.
- If `lng_group_call_open_chat` is missing in `createRowContextMenu`, channel/group participants will lack an open chat option.
