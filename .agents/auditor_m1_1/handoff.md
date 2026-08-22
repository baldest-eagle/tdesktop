# Handoff Report: Forensic Audit of Milestone M1

**Agent**: Forensic Auditor (`auditor_m1_1`)  
**Target**: Milestone M1 (Calls UI, Floating Overlay & Viewport Grid)  
**Parent**: Sub-Orchestrator M1 (`e26ac6b6-cadb-4cf1-a64f-cacfbc8879fa`)  
**Date**: 2026-08-20  
**Verdict**: **CLEAN**

---

## 1. Observation

Direct code inspections of Worker 1's modifications across all 4 target files:

1. **`calls_group_floating_overlay.h:62-66` & `calls_group_floating_overlay.cpp:154-167`**:
   `setupChatContent()` instantiates `MessagesUi` using live rpl producers from `_panel->call()` (`listValue()`, `idUpdates()`, `canManageValue()`, `messagesEnabledValue()`) and passes `_panel->uiShow()`, parent `this`, and `MessagesMode::GroupCall`. Geometry is positioned using `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` and dynamically re-anchored on `resizeEvent()`. Header buttons `_closeBtn` and `_passthroughBtn` are maintained as `object_ptr` members and moved to `(width() - 30, 5)` and `(width() - 55, 5)` respectively upon resize.

2. **`calls_group_viewport.cpp:560-573`**:
   The 50/50 split condition `if (count == 2 && slotConstraint == 0)` is placed before `if (fixedGridDim > 0)`. The layout calculates `halfW = (outerWidth - skip) / 2`, assigning `sizes[0] = { 0, 0, halfW, outerHeight }` and `sizes[1] = { halfW + skip, 0, outerWidth - halfW - skip, outerHeight }`, and returns `result` with `result.useColumns = true`.

3. **`calls_group_members.cpp:1451-1454, 1530-1538`**:
   - Camera video endpoint context menu wires `tr::lng_group_call_context_pin_to_grid(tr::now)` invoking `[=] { _call->pinVideoEndpoint(camera); }`.
   - Non-user participant rows (channels/groups) wire `tr::lng_group_call_open_chat(tr::now)` invoking `showHistory`, which navigates the active primary window session controller to `showPeerHistory(participantPeer, ::Window::SectionShow::Way::Forward)`.

4. **Style and Forensic Indicators**:
   - Zero hardcoded outputs, fake mock responses, or stubbed return values.
   - Zero single-line comments in newly introduced or modified logic.
   - Project literal `_q` used for QStrings (`u"Ctrl+Shift+T"_q`, `u"Chat"_q`).
   - Proper spacing, `auto` type deduction, and clean formatting throughout.

---

## 2. Logic Chain

1. **Floating Overlay Genuineness**:
   - The constructor of `MessagesUi` requires active stream bindings and valid UI show context. Passing live streams from `_panel->call()` connects the overlay directly to Telegram's group call message delivery pipeline.
   - `move(4, height() - 4, width() - 8, height() - 40)` accurately specifies `(left, bottom, width, availableHeight)`. Positioning at `height() - 4` reserves 4px bottom padding and 36px top header area (`height() - 40`), preventing the negative y-coordinate clipping previously observed when `36` was passed as `bottom`.
   - Updating child button geometries in `resizeEvent()` ensures interactive elements remain reachable upon window resizing.

2. **50/50 Split Geometry Validity**:
   - In dynamic layout mode, `slotConstraint == 0`, meaning `fixedGridDim` is 0. Moving the 50/50 split check above `if (fixedGridDim > 0)` removes the dead-code defect.
   - The tile dimensions `halfW` and `outerWidth - halfW - skip` add up with `skip` to exactly `outerWidth`, proving mathematical correctness and preventing 1px seam gaps or edge overflows.

3. **Context Action Completeness**:
   - Localizations `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` are genuinely bound to the respective call and window session actions without dummy intermediaries or dead callbacks.

---

## 3. Caveats

- Fixed grid modes (`slotConstraint` in `{1, 4, 9}`) continue to be processed by the subsequent `fixedGridDim > 0` branch as intended by the grid architecture.
- Screen sharing unpin/pin actions continue to use `lng_group_call_context_unpin_screen` / `lng_group_call_context_pin_screen`.
- No caveats regarding code integrity or compliance.

---

## 4. Conclusion

**Verdict: CLEAN**

Milestone M1 changes implemented by Worker 1 are genuine, correct, free of any facades or cheating shortcuts, and adhere strictly to project conventions. The work product is approved for Milestone M1 completion.

---

## 5. Verification Method

To independently inspect and verify:
1. Inspect `calls_group_floating_overlay.cpp:154-167`: Verify `MessagesUi` constructor arguments and `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)`.
2. Inspect `calls_group_viewport.cpp:560-573`: Verify `count == 2 && slotConstraint == 0` is positioned before `if (fixedGridDim > 0)` and computes complementary tile widths.
3. Inspect `calls_group_members.cpp:1451-1454, 1530-1538`: Verify context menu action lambdas for pin to grid and open chat.
4. Verify absence of single-line comments in modified blocks per `REVIEW.md`.
