## 2026-08-20T19:23:26Z

You are Worker 1 for Milestone M1 (Calls UI, Floating Overlay & Viewport Grid).
Your working directory is: c:\Users\kyleh\tdesktop\.agents\worker_m1_1\
Parent: Sub-Orchestrator M1 (Conv ID: e26ac6b6-cadb-4cf1-a64f-cacfbc8879fa)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Mandatory reading:
- Scope: c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\SCOPE.md
- Dispatch / User Request: c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\DISPATCH.md
- Code Guidelines: c:\Users\kyleh\tdesktop\REVIEW.md and c:\Users\kyleh\tdesktop\AGENTS.md
- Explorer 1 Analysis: c:\Users\kyleh\tdesktop\.agents\explorer_m1_1\analysis.md
- Explorer 2 Analysis: c:\Users\kyleh\tdesktop\.agents\explorer_m1_2\analysis.md
- Explorer 3 Analysis: c:\Users\kyleh\tdesktop\.agents\explorer_m1_3\analysis.md

Your Exclusive Write Ownership:
- Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h
- Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp
- Telegram/SourceFiles/calls/group/calls_group_viewport.cpp
- Telegram/SourceFiles/calls/group/calls_group_members.cpp

Your Tasks:
1. Implement `FloatingOverlay::setupChatContent()` in `calls_group_floating_overlay.cpp` (and adjust `calls_group_floating_overlay.h` as detailed in Explorer 1's analysis):
   - Instantiate `_messagesUi` passing parent `this`, `_panel->uiShow()`, `MessagesMode::GroupCall`, `_panel->call()->messages()->listValue()`, `nullptr` (topDonors), `_panel->call()->messages()->idUpdates()`, `_panel->call()->canManageValue()`, `_panel->call()->messagesEnabledValue()`, and `[=](QPoint) { return false; }`.
   - In `setupChatContent()` and `resizeEvent()`, position correctly with `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)`.
   - Update `_closeBtn` and `_passthroughBtn` to be member pointers repositioned on `resizeEvent()`.
   - Clean up code style per `REVIEW.md`: strictly NO single-line comments in code, use `_q` literals (e.g. `u"Chat"_q`, `u"Ctrl+Shift+T"_q`), use `!isHidden()`, ensure proper tab indentation and empty line before closing braces.

2. In `calls_group_viewport.cpp:577`:
   - Fix the 50/50 split condition so that 2 active feeds correctly split half-width on screen when `count == 2 && slotConstraint == 0`.
   - Move the check from inside `if (fixedGridDim > 0)` to before `if (fixedGridDim > 0)`.
   - Use:
     `sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };`
     `sizes[1].columns = sizes[1].rows = { halfW + skip, 0, outerWidth - halfW - skip, outerHeight };`
     `result.useColumns = true; return result;`

3. In `calls_group_members.cpp`:
   - In `createRowContextMenu`, wire `lng_group_call_context_pin_to_grid` for pinning camera endpoint (and screencast as appropriate).
   - In `if (participantPeer->isUser())` block: maintain `tr::lng_context_send_message(tr::now)` for user, and in the `else` branch add `result->addAction(tr::lng_group_call_open_chat(tr::now), showHistory);` so non-user participants have "Open Chat".
   - Adhere to `REVIEW.md` (no single-line comments).

Validation:
- Perform validation checks and run any verification / build checks.
- Document all changes and verification results in `c:\Users\kyleh\tdesktop\.agents\worker_m1_1\changes.md` and `handoff.md`.
- Send a completion message to parent with summary and path to handoff.
