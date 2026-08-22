## 2026-08-20T19:16:08Z

<USER_REQUEST>
You are the Sub-Orchestrator for Milestone M1 (Calls UI, Floating Overlay & Viewport Grid) on the Telegram Desktop fork.

Your working directory is: c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\
The original request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
Your scope document is at: c:\Users\kyleh\tdesktop\.agents\sub_orch_m1\SCOPE.md

Your Assigned Scope & Tasks:
1. Complete `FloatingOverlay::setupChatContent()` in `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp` by creating and parenting `MessagesUi` / chat content correctly using `_panel` and window controllers. Clean up formatting and style per `REVIEW.md`.
2. In `calls_group_viewport.cpp:577` (and dynamic grid layout solver), fix the 50/50 split condition so that 2 active feeds correctly split half-width on screen when `slotConstraint == 0` (or dynamic mode) instead of hitting dead code in `if (fixedGridDim > 0)`.
3. In `calls_group_members.cpp` / group calls menus, wire `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` so participants have direct "Pin to Grid" and "Open Chat" actions in context menus.
4. Adhere strictly to project conventions in `REVIEW.md` and `AGENTS.md` (e.g. no single-line comments in code, `crl::guard`, `_q` string literals, LF/CRLF consistency).

Workflow:
- Execute the Project Pattern iteration loop: Explorer -> Worker -> Reviewer -> Challenger -> Forensic Auditor (`teamwork_preview_auditor`).
- Require workers to write clean code and run validation.
- Record gate verdicts in `GATE_STATUS.md`.
- Enforce the Forensic Auditor BINARY VETO (any integrity violation fails the milestone).
- When the gate passes, write `handoff.md` in your working directory and notify the parent orchestrator via `send_message`.
</USER_REQUEST>
