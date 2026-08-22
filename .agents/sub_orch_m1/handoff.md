# Milestone M1 Completion Handoff Report

**Sub-Orchestrator**: Milestone M1 (Calls UI, Floating Overlay & Viewport Grid)  
**Parent**: Top-Level Orchestrator (`5278ca9a-12ca-434c-963d-a5a03310dd33`)  
**Date**: 2026-08-20  
**Status**: **COMPLETED / PASSED**

---

## 1. Observation

1. **Floating Overlay Chat Content (`FloatingOverlay::setupChatContent()`)**:
   - In `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp:154-167` (and `calls_group_floating_overlay.h:62-66`), `_messagesUi` is instantiated with `this`, `_panel->uiShow()`, `MessagesMode::GroupCall`, `call->messages()->listValue()`, `nullptr` (topDonors), `call->messages()->idUpdates()`, `call->canManageValue()`, `call->messagesEnabledValue()`, and `[=](QPoint) { return false; }`.
   - Layout geometry is initialized and dynamically maintained upon `resizeEvent()` via `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)`.
   - Header control buttons `_closeBtn` and `_passthroughBtn` are preserved as `object_ptr` members and dynamically repositioned to `(width() - 30, 5)` and `(width() - 55, 5)`.
   - All single-line comments were removed, standard tab indentation and `_q` string literals (`u"Chat"_q`, `u"Ctrl+Shift+T"_q`) were applied, and `!isHidden()` is used for visibility checks per `REVIEW.md`.

2. **Dynamic 50/50 Viewport Grid Split**:
   - In `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:560-573`, the 50/50 split condition `if (count == 2 && slotConstraint == 0)` was relocated before `if (fixedGridDim > 0)`.
   - Horizontal tiles are calculated as:
     `sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };`
     `sizes[1].columns = sizes[1].rows = { halfW + skip, 0, outerWidth - halfW - skip, outerHeight };`
     `result.useColumns = true; return result;`
   - Odd-width integer divisions are absorbed cleanly without 1px seam gaps or edge overflow.

3. **Participant Context Actions ("Pin to Grid" & "Open Chat")**:
   - In `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1451-1454, 1530-1538`:
     - `tr::lng_group_call_context_pin_to_grid(tr::now)` is wired for unpinned video camera endpoints to invoke `[=] { _call->pinVideoEndpoint(camera); }`.
     - `tr::lng_group_call_open_chat(tr::now)` is added in the `else` branch of `if (participantPeer->isUser())` to route channel/group participants to `showHistory` via `window->showPeerHistory(participantPeer, ::Window::SectionShow::Way::Forward)`.

---

## 2. Logic Chain

1. **Overlay Geometry & Lifecycle**:
   - `MessagesUi::move` expects `bottom` to represent the bottom edge of the widget. Setting `bottom = height() - 4` and `availableHeight = height() - 40` ensures the scroll container top $y_{\text{top}} \ge 36\text{px}$ unconditionally, avoiding collision with top header buttons at $y = 5..10\text{px}$ and resolving the previous off-screen clipping bug.
2. **Dynamic 50/50 Grid Partitioning**:
   - When `slotConstraint == 0` (dynamic mode), `fixedGridDim` evaluates to `0`. Moving the 50/50 check before `if (fixedGridDim > 0)` restores the dynamic 2-feed branch from dead code.
   - Complementary tile width `outerWidth - halfW - skip` guarantees exact horizontal pixel coverage $\sum w_i + \text{skip} = \text{outerWidth}$ across all odd and even widths.
3. **Context Action Completeness**:
   - All participant types (users, channels, megagroups) now have valid navigation options in calls, and video streams provide explicit pin-to-grid controls.

---

## 3. Caveats

- Fixed grid modes (`slotConstraint` $\in \{1, 4, 9\}$) bypass the dynamic 2-feed check as designed and execute their respective $N \times N$ cell calculations.
- Screen sharing streams continue to utilize `lng_group_call_context_pin_screen` and `lng_group_call_context_unpin_screen`.
- No architectural caveats or regressions identified.

---

## 4. Conclusion & Gate Evaluation

| Verification Stage | Verdict |
|-------------------|---------|
| Worker 1 Implementation | **DONE** |
| Reviewer 1 (`8567a023-95c1-4acf-b35d-fd9ee2b9e45f`) | **APPROVE** |
| Reviewer 2 (`22cecae0-99c6-4e73-98e0-10210c0d68dd`) | **APPROVE** |
| Challenger 1 (`4a432e62-f4e2-4774-ae78-33181147dd9c`) | **APPROVE** |
| Challenger 2 (`8c789bae-0a60-409c-8541-3d4cf06c3330`) | **APPROVE** |
| Forensic Auditor (`d71258dd-5659-4237-8e2d-31ab4bafdacd`) | **CLEAN** |
| **Milestone M1 Gate** | **PASS** |

---

## 5. Milestone State & Key Artifacts

- **Milestone M1**: **DONE**
- **Active Subagents**: None (all subagents completed and retired)
- **Pending Decisions**: None
- **Remaining Work**: Hand off to top-level orchestrator for subsequent milestones.
- **Key Artifacts**:
  - `c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\SCOPE.md`
  - `c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\GATE_STATUS.md`
  - `c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\progress.md`
  - `c:\Users\kyleh\tdesktop\.agents\worker_m1_1\changes.md`
  - `c:\Users\kyleh\tdesktop\.agents\auditor_m1_1\audit.md`
