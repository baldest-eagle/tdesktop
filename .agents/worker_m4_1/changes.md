# Changes Made by Worker M4.1 (Milestone M4)

## Summary of Completed Tasks
1. **CMake Source Synchronization (Feature 56)**:
   - Registered `storage/storage_sqlite_pragmas.h` in `Telegram/CMakeLists.txt` alphabetically in the `storage/` section between `storage/storage_sparse_ids_list.h` and `storage/storage_user_photos.cpp`.

2. **Include Directive Reordering**:
   - `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`: Moved `styles/style_calls.h` to the end of include directives, separated by an empty line following Qt includes.
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.h`: Reordered includes so nested directory `ui/effects/animations.h` precedes `ui/rp_widget.h`.
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`: Reordered includes alphabetically, ensured nested directories precede local files, moved `styles/style_calls.h` to the bottom following Qt includes.
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp`: Correctly placed `ui/widgets/fields/input_field.h` in alphabetical hierarchy under `ui/widgets/fields/`, sorted all includes alphabetically, and placed `styles/style_calls.h` at the end.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h`: Sorted project includes alphabetically (`base/`, `calls/group/`, `ui/`).
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp`: Placed `styles/style_calls.h` last separated by an empty line after Qt/QtWidgets includes.
   - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`: Sorted include directives strictly alphabetically (`apiwrap.h`, `base/`, `data/`, `main/`, `mtproto/`).

3. **Bloat Comments & Dead Code Removal**:
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`:
     - Removed trailing comment on `#include "data/data_group_call.h"`.
     - Removed bloat comments at lines 515 and 529-530 in `Viewport::countWide`.
     - Replaced explicit vector declaration with `auto unpinnedTiles = std::vector<not_null<VideoTile*>>();`.
     - Removed 46 lines of dead commented-out code in `MuteButtonTooltip` (lines 1175-1221) and adjusted return indentation.
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp`:
     - Removed bloat comment at line 1982 (`// In-call username search bar...`).
     - Added `const` to `searchWrap` and `searchField` variable declarations.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp`:
     - Removed single-line bloat comments at lines 52, 101, 113, 124, 131, 137, 154, 171.
     - Modernized loop index in `updateScreens` (`auto i = 0; i != screens.size(); ++i`, `const auto idx : toRemove`).
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp`:
     - Removed bloat comments at lines 1493, 1519, 1535.

4. **Literal Modernization (`QStringLiteral` / raw literals -> `u"..."_q`)**:
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp`:
     - Line 1994: Changed `QStringLiteral("Search username...")` to `u"Search username..."_q`.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp`:
     - Lines 23-26: Modernized `RoleText` returns from raw strings to `u"Active Speaker"_q`, `u"Grid View"_q`, `u"Chat Station"_q`, and `QString()`.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp`:
     - Line 862: `u"Grid View (1x1, 2x2, 3x3)"_q`.
     - Line 882: `u"Toggle Floating Chat"_q`.
     - Lines 1478-1479: `u"Manage Pinned Screen"_q`, `u"Pin Camera to Screen"_q`.
     - Line 1483: `u"Choose target screen for "_q`, `u":"_q`.
     - Line 1487: `u"Unpin (Return to Main Grid)"_q`.
     - Line 1509: `u"Screen 1 (Stage Window)"_q`.
     - Line 1525: `u"Screen 2 (2nd Monitor)"_q`.

5. **Namespace Comments**:
   - `Telegram/SourceFiles/calls/group/calls_group_members.h`:
     - Line 133: Fixed closing namespace comment from `} // namespace Calls` to `} // namespace Calls::Group`.

## Modified Files
1. `Telegram/CMakeLists.txt`
2. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
3. `Telegram/SourceFiles/calls/group/calls_group_viewport.h`
4. `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
5. `Telegram/SourceFiles/calls/group/calls_group_members.h`
6. `Telegram/SourceFiles/calls/group/calls_group_members.cpp`
7. `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h`
8. `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp`
9. `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`
10. `Telegram/SourceFiles/calls/group/calls_group_panel.cpp`
