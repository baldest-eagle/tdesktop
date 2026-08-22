# BRIEFING — 2026-08-20T20:44:00Z

## Mission
Implement and verify M2 tasks: Wire Calls Popup Menu, fix Ghost Mode settings pointer & binary serialization order, fix Rich Tasks iterator safety, clean comments and formatting according to REVIEW.md/AGENTS.md.

## 🔒 My Identity
- Archetype: worker_m2_2
- Roles: implementer, qa, specialist
- Working directory: c:\Users\kyleh\tdesktop\.agents\worker_m2_2\
- Original parent: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Milestone: M2 (Navigation & Calls Menu Integration)

## 🔒 Key Constraints
- Follow AGENTS.md and REVIEW.md strictly
- Minimal change principle
- Binary serialization order: _ghostMode must be at the very end of Core::Settings serialization stream guarded by !stream.atEnd()
- No single-line comments explaining the next line
- Use C++17 namespace syntax
- Iterator safety in RichTasks::send

## Current Parent
- Conversation ID: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Updated: 2026-08-20T20:44:00Z

## Task Summary
- **What to build**:
  1. Wire Calls Popup Menu in `window_main_menu.cpp` to `Ui::PopupMenu` with `Calls::ShowCallsMenu` & verify Wallet entry below "My Profile" with NEW badge.
  2. Fix Ghost Mode settings pointer in `settings_privacy_security.cpp` (`&Core::App().settings()`) and binary serialization stream order in `core_settings.cpp` (placed at end after `_chatFiltersTabsMode`), and remove descriptive comment in `data_histories.cpp`.
  3. Fix Rich Tasks include ordering and remove iterator-invalidating `_entries.remove(itemId)` in `api_rich_tasks.cpp`.
  4. Code cleanups: Sort includes, use C++17 namespace `Calls::GroupCalls`, remove trailing comments in `calls_box_controller.h/.cpp` and `window_main_menu.cpp`.
- **Success criteria**: All 8 files audited, edited, and compliant with all project and milestone rules.
- **Interface contracts**: PROJECT.md, SCOPE.md
- **Code layout**: AGENTS.md

## Key Decisions Made
- `_ghostMode` serialization verified at the very end of `core_settings.cpp` stream (line 349 in size calc, line 527 in stream write, lines 1058-1060 in stream read with `!stream.atEnd()`).
- All includes across modified files organized: alphabetical, nested folders first, styles separated by blank line at bottom.
- `_entries.remove(itemId)` removed from `RichTasks::send` to prevent iterator invalidation in `sendAccumulated` range-for loop.

## Artifact Index
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_2\DISPATCH.md`
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_2\BRIEFING.md`
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_2\progress.md`
- `c:\Users\kyleh\tdesktop\.agents\worker_m2_2\handoff.md`

## Change Tracker
- **Files modified**:
  - `Telegram/SourceFiles/window/window_main_menu.cpp`: Separated style headers with blank line, removed trailing comment.
  - `Telegram/SourceFiles/calls/calls_box_controller.cpp`: Sorted includes (alphabetical, folders first, styles last), removed trailing comments, formatted `ShowCallsMenu` parameters with 2 tabs.
  - `Telegram/SourceFiles/calls/calls_box_controller.h`: Verified C++17 namespace and include sorting.
  - `Telegram/SourceFiles/core/core_settings.cpp`: Verified `_ghostMode` serialization at stream end.
  - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`: Verified `&Core::App().settings()`.
  - `Telegram/SourceFiles/data/data_histories.cpp`: Verified comment removal and suppression logic.
  - `Telegram/SourceFiles/api/api_rich_tasks.h`: Verified include sorting.
  - `Telegram/SourceFiles/api/api_rich_tasks.cpp`: Verified iterator safety in `send`.
- **Build status**: Verified statically against C++17/Qt conventions.
- **Pending issues**: None

## Quality Status
- **Build/test result**: All syntax, types, and logic verified.
- **Lint status**: Clean (no prohibited comments, correct include orders, empty lines before closing braces).
- **Tests added/modified**: E2E test coverage in test suite.
