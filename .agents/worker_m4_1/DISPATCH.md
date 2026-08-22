## 2026-08-20T21:03:28Z

You are Worker M4.1 for Milestone M4 on the Telegram Desktop fork.
Your working directory is: c:\Users\kyleh\tdesktop\.agents\worker_m4_1\
The authoritative user request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md (you MUST read this first).
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
The milestone scope is at: c:\Users\kyleh\tdesktop\sub_orch_m4\SCOPE.md
The style guidelines are in: c:\Users\kyleh\tdesktop\REVIEW.md and c:\Users\kyleh\tdesktop\AGENTS.md
Explorer reports are in:
- c:\Users\kyleh\tdesktop\.agents\explorer_m4_1\report.md
- c:\Users\kyleh\tdesktop\.agents\explorer_m4_2\report.md
- c:\Users\kyleh\tdesktop\.agents\explorer_m4_3\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Tasks:
1. CMake Source Synchronization (Feature 56):
   - Register `storage/storage_sqlite_pragmas.h` in `Telegram/CMakeLists.txt` alphabetically in the `storage/` section (around line 1884, between `storage/storage_sparse_ids_list.h` and `storage/storage_user_photos.cpp`).
2. Code Style & Review Polish per REVIEW.md and AGENTS.md:
   - Reorder `#include` directives in `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`, `Telegram/SourceFiles/calls/group/calls_group_viewport.h/.cpp`, `Telegram/SourceFiles/calls/group/calls_group_members.cpp`, `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h/.cpp`, and `Telegram/SourceFiles/storage/download_manager_mtproto.cpp` so that:
     * Nested folders come before files in the same directory.
     * Style includes (`styles/style_*.h`) always go last, separated from other includes by an empty line.
     * Standard alphabetical sorting.
   - Remove single-line bloat comments and dead commented-out code:
     * In `calls_group_viewport.cpp` (lines 515, 529-530, and the 46-line dead commented-out block around lines 1175-1221).
     * In `calls_group_members.cpp` (line 1982).
     * In `calls_group_display_coordinator.cpp` (lines 52, 101, 113, 124, 131, 137, 154, 171).
     * In `calls_group_panel.cpp` (lines 1493, 1519, 1535).
   - Convert `QStringLiteral` and raw string literals to `u"..."_q`:
     * `calls_group_members.cpp:1994`: `u"Search username..."_q`.
     * `calls_group_display_coordinator.cpp:23-26`: `return u"Active Speaker"_q;` etc.
     * `calls_group_panel.cpp`: convert `QStringLiteral(...)` to `u"..."_q` at the fork modification sites (e.g. lines 862, 882, 1478, 1479, 1483, 1487, 1509, 1525).
   - Fix namespace comment in `Telegram/SourceFiles/calls/group/calls_group_members.h:133` (`} // namespace Calls::Group`).
3. Verification:
   - Verify all modified files maintain UTF-8 without BOM and CRLF line endings on Windows.
   - Verify that all changes adhere strictly to REVIEW.md and AGENTS.md.
   - Document all changes in `c:\Users\kyleh\tdesktop\.agents\worker_m4_1\changes.md`.
   - Write a complete 5-section handoff report in `c:\Users\kyleh\tdesktop\.agents\worker_m4_1\handoff.md`.
4. When done, notify your parent with send_message.
