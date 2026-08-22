## 2026-08-20T19:16:51Z
You are Explorer 1 for Milestone M2 (Navigation & Calls Menu Integration).

Your working directory is: c:\Users\kyleh\tdesktop\.agents\explorer_m2_1\
The original user request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
The M2 scope document is at: c:\Users\kyleh\tdesktop\.agents\sub_orch_m2\SCOPE.md

READ `ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md`, `AGENTS.md`, and `REVIEW.md` before starting.

TASK:
1. Examine `Telegram/SourceFiles/window/window_main_menu.cpp:707` (and surrounding lines).
   - Check how the "Calls" menu item is currently implemented.
   - Check how `Calls::ShowCallsBox` is called vs what `Calls::ShowCallsMenu` requires.
   - Inspect `Telegram/SourceFiles/calls/calls_box_controller.h` and `Telegram/SourceFiles/calls/calls_box_controller.cpp` to verify the declaration, parameters, and behavior of `Calls::ShowCallsMenu`.
   - Formulate the exact code change needed to replace `Calls::ShowCallsBox` with `Calls::ShowCallsMenu` so clicking Calls opens the dynamic structured popup menu (active calls, Start Call, Call History).
2. Examine the Wallet menu entry in `Telegram/SourceFiles/window/window_main_menu.cpp`.
   - Verify if it is positioned directly below "My Profile".
   - Verify if it displays the green `NEW` badge per `docs/fork_features.md:62`.
   - Note exact line numbers, logic, and whether any adjustments are needed.

Produce a detailed report in `c:\Users\kyleh\tdesktop\.agents\explorer_m2_1\handoff.md` with:
- Observation (findings with exact file paths and line numbers)
- Logic Chain (exact recommended modifications for the Worker)
- Caveats & Risks
- Conclusion & Implementation Instructions for Worker

Send a completion message back to parent when done.
