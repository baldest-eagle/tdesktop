## 2026-08-20T20:46:00Z

You are Reviewer 1 for Milestone M2 (Navigation & Calls Menu Integration).

Your working directory is: c:\Users\kyleh\tdesktop\.agents\reviewer_m2_1\
The original user request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
The M2 scope document is at: c:\Users\kyleh\tdesktop\.agents\sub_orch_m2\SCOPE.md
The worker handoff report is at: c:\Users\kyleh\tdesktop\.agents\worker_m2_2\handoff.md

Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md`, `AGENTS.md`, and `REVIEW.md` before starting.

TASK:
Perform an objective, thorough code review of all M2 files modified:
1. `Telegram/SourceFiles/window/window_main_menu.cpp`: Verify Calls popup menu wiring via `Ui::PopupMenu` and `::Calls::ShowCallsMenu`. Verify Wallet entry placement under "My Profile" with green `NEW` badge (`docs/fork_features.md:62`).
2. `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`: Verify pointer fix (`&Core::App().settings()`) and Ghost Mode UI toggle.
3. `Telegram/SourceFiles/core/core_settings.cpp`: Verify `_ghostMode` is appended strictly to the end of the binary serialization stream (size, write, and read guarded by `!stream.atEnd()`).
4. `Telegram/SourceFiles/data/data_histories.cpp`: Verify read receipt suppression when `ghostMode()` is true, and absence of descriptive single-line comments.
5. `Telegram/SourceFiles/api/api_rich_tasks.h` & `api_rich_tasks.cpp`: Verify include sorting and iterator safety fix in `RichTasks::send`.
6. `Telegram/SourceFiles/calls/calls_box_controller.h` & `calls_box_controller.cpp`: Verify sorted includes, C++17 nested namespaces, 2-tab parameter indentation, and absence of comments.

Write your report in `c:\Users\kyleh\tdesktop\.agents\reviewer_m2_1\handoff.md` with:
- Observation
- Logic Chain
- Caveats
- Conclusion (MUST state explicit verdict: `APPROVE` or `REQUEST_CHANGES`)
- Verification Method

Send a completion message back to parent when done.
