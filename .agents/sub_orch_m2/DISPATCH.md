# Dispatch History

## 2026-08-20T19:16:08Z

You are the Sub-Orchestrator for Milestone M2 (Navigation & Calls Menu Integration) on the Telegram Desktop fork.

Your working directory is: c:\Users\kyleh\tdesktop\.agents\sub_orch_m2\
The original request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
Your scope document is at: c:\Users\kyleh\tdesktop\.agents\sub_orch_m2\SCOPE.md

Your Assigned Scope & Tasks:
1. In `Telegram/SourceFiles/window/window_main_menu.cpp:707`, replace the direct modal `Calls::ShowCallsBox` call with `Calls::ShowCallsMenu` (declared and implemented in `Telegram/SourceFiles/calls/calls_box_controller.h/.cpp`), so clicking Calls opens the dynamic structured popup menu with active calls, Start Call, and Call History.
2. Verify the Wallet menu entry in `window/window_main_menu.cpp` is positioned below "My Profile" with the green `NEW` badge per `docs/fork_features.md:62`.
3. Verify Ghost Mode read receipt suppression in `data_histories.cpp`, settings UI in `settings_privacy_security.cpp`, and trailing binary serialization in `core_settings.cpp/.h`.
4. Verify Rich Tasks markdown checklists in `api_rich_tasks.cpp/.h`.
5. Adhere strictly to project conventions in `REVIEW.md` and `AGENTS.md` (no single-line comments, `tr::` projections, `crl::guard`, `MTP::Sender`, etc.).

Workflow:
- Execute the Project Pattern iteration loop: Explorer -> Worker -> Reviewer -> Challenger -> Forensic Auditor (`teamwork_preview_auditor`).
- Record gate verdicts in `GATE_STATUS.md`.
- Enforce the Forensic Auditor BINARY VETO.
- When the gate passes, write `handoff.md` in your working directory and notify the parent orchestrator via `send_message`.
