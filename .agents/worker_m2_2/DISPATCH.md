## 2026-08-20T20:40:22Z

You are Worker 2 (replacement for worker_m2_1) for Milestone M2 (Navigation & Calls Menu Integration).

Your working directory is: c:\Users\kyleh\tdesktop\.agents\worker_m2_2\
The original user request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
The M2 scope document is at: c:\Users\kyleh\tdesktop\.agents\sub_orch_m2\SCOPE.md

Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md`, `AGENTS.md`, and `REVIEW.md` before starting.
Also read the reports produced by the explorers:
- `c:\Users\kyleh\tdesktop\.agents\explorer_m2_1\handoff.md`
- `c:\Users\kyleh\tdesktop\.agents\explorer_m2_2\handoff.md`
- `c:\Users\kyleh\tdesktop\.agents\explorer_m2_3\handoff.md`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
You own and may edit the following files:
- `Telegram/SourceFiles/window/window_main_menu.cpp`
- `Telegram/SourceFiles/calls/calls_box_controller.h`
- `Telegram/SourceFiles/calls/calls_box_controller.cpp`
- `Telegram/SourceFiles/core/core_settings.cpp`
- `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
- `Telegram/SourceFiles/data/data_histories.cpp`
- `Telegram/SourceFiles/api/api_rich_tasks.cpp`
- `Telegram/SourceFiles/api/api_rich_tasks.h`

TASKS:
1. **Wire Calls Popup Menu in `Telegram/SourceFiles/window/window_main_menu.cpp`**:
   - At lines ~703–708, replace the direct modal `::Calls::ShowCallsBox(controller);` call with:
     ```cpp
     		const auto calls = addAction(
     			tr::lng_menu_calls(),
     			{ &st::menuIconPhone }
     		);
     		calls->setClickedCallback([=] {
     			_contextMenu = base::make_unique_q<Ui::PopupMenu>(
     				calls,
     				st::popupMenuWithIcons);
     			::Calls::ShowCallsMenu(_contextMenu.get(), controller);
     			_contextMenu->popup(QCursor::pos());
     		});
     ```
   - Verify Wallet entry placement below "My Profile" with green `NEW` badge.
   - Clean up include ordering around line 30 if needed.

2. **Fix Ghost Mode Settings & Binary Serialization**:
   - In `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp:1089`:
     Change `const auto settings = Core::App().settings();` to `const auto settings = &Core::App().settings();` so member accesses via `->` compile correctly and modify the singleton instance.
   - In `Telegram/SourceFiles/core/core_settings.cpp`:
     Relocate `_ghostMode` serialization to the end of the stream after `_chatFiltersTabsMode` (size calculation, `serialize()` stream write, and `addFromSerialized()` stream read with `if (!stream.atEnd())`), removing it from the middle to preserve binary backward compatibility per `AGENTS.md`.
   - In `Telegram/SourceFiles/data/data_histories.cpp:716`:
     Remove the single-line descriptive comment (`// Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers`).

3. **Fix Rich Tasks Iterator Safety & Includes**:
   - In `Telegram/SourceFiles/api/api_rich_tasks.h`:
     Sort includes (`#include "base/flat_map.h"` before `#include "base/timer.h"`).
   - In `Telegram/SourceFiles/api/api_rich_tasks.cpp:84–88`:
     Remove `_entries.remove(itemId);` from `RichTasks::send` to prevent iterator invalidation during range-for loop in `sendAccumulated()`.

4. **Code Conventions & Cleanups in `calls_box_controller`**:
   - In `Telegram/SourceFiles/calls/calls_box_controller.h`:
     Sort includes (`#include "mtproto/sender.h"` before `#include "ui/layers/generic_box.h"`).
     Use C++17 `namespace Calls::GroupCalls {`.
     Remove single-line comment at line 75 (`// Not a real mtpRequestId.`).
   - In `Telegram/SourceFiles/calls/calls_box_controller.cpp`:
     Format `ShowCallsMenu` parameter continuations with 2 tabs (`\t\t`).
     Remove trailing comments on include lines 37, 48, 49.

5. **Build & Verify**:
   - Run compilation command:
     `cmake --build out --config Debug --target Telegram`
     (or check through WSL if appropriate per `AGENTS.md`).
   - Verify that all modified files compile and link cleanly without errors or warnings.
