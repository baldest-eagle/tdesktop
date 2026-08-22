# BRIEFING — 2026-08-20T19:24:00Z

## Mission
Execute Milestone M2 code modifications: Navigation & Calls Menu Integration, Ghost Mode settings & serialization fixes, Rich Tasks safety & include fixes, CallsBoxController code conventions, and compile/verify cleanly.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: c:\Users\kyleh\tdesktop\.agents\worker_m2_1\
- Original parent: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Milestone: M2 (Navigation & Calls Menu Integration)

## 🔒 Key Constraints
- Integrity Mandate: No cheating, no fake outputs, genuine implementations only.
- Exclusive write ownership files:
  - `Telegram/SourceFiles/window/window_main_menu.cpp`
  - `Telegram/SourceFiles/calls/calls_box_controller.h`
  - `Telegram/SourceFiles/calls/calls_box_controller.cpp`
  - `Telegram/SourceFiles/core/core_settings.cpp`
  - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
  - `Telegram/SourceFiles/data/data_histories.cpp`
  - `Telegram/SourceFiles/api/api_rich_tasks.cpp`
  - `Telegram/SourceFiles/api/api_rich_tasks.h`
- Strict compliance with `AGENTS.md` and `REVIEW.md` (no single-line bloat comments, binary serialization at stream end with atEnd guard, etc.).
- Build and verify via CMake / WSL as appropriate.

## Current Parent
- Conversation ID: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Updated: 2026-08-20T19:24:00Z

## Task Summary
- **What to build**:
  1. Wire Calls Popup Menu in `window_main_menu.cpp` using `_contextMenu = base::make_unique_q<Ui::PopupMenu>(calls, st::popupMenuWithIcons); ::Calls::ShowCallsMenu(_contextMenu.get(), controller); _contextMenu->popup(QCursor::pos());`. Verify Wallet below "My Profile" with green badge. Clean includes.
  2. Fix Ghost Mode settings in `settings_privacy_security.cpp` (change `const auto settings = Core::App().settings();` to `const auto settings = &Core::App().settings();`). Relocate `_ghostMode` serialization in `core_settings.cpp` to the end of the binary stream after `_chatFiltersTabsMode` with `!stream.atEnd()` guard. Remove single-line comment in `data_histories.cpp:716`.
  3. Fix Rich Tasks in `api_rich_tasks.h` (sort includes) and `api_rich_tasks.cpp` (remove `_entries.remove(itemId)` in `send` to avoid iterator invalidation during range-for loop).
  4. Fix `calls_box_controller.h` (sort includes, C++17 nested namespace `Calls::GroupCalls`, remove comment) and `calls_box_controller.cpp` (2-tab parameter indentation for `ShowCallsMenu`, remove trailing comments).
  5. Build & verify.
- **Success criteria**: All 8 files modified cleanly, no compiler or linker errors/warnings, strict style compliance.
- **Interface contracts**: `PROJECT.md`, `SCOPE.md`
- **Code layout**: `PROJECT.md`

## Key Decisions Made
- Following recommendations from explorer handoff reports (`explorer_m2_1`, `explorer_m2_2`, `explorer_m2_3`).

## Artifact Index
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_1\DISPATCH.md` — Assignment instructions
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_1\progress.md` — Liveness and progress tracking
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_1\handoff.md` — Final handoff report

## Change Tracker
- **Files modified**: [TBD]
- **Build status**: [TBD]
- **Pending issues**: None

## Quality Status
- **Build/test result**: [TBD]
- **Lint status**: [TBD]
- **Tests added/modified**: [TBD]

## Loaded Skills
- None
