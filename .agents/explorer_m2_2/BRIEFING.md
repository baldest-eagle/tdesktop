# BRIEFING — 2026-08-20T19:21:45Z

## Mission
Investigate Ghost Mode (Decoupled Read Receipts) implementation, serialization safety, settings UI toggle, and read receipt suppression across data_histories, core_settings, and settings_privacy_security for M2.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, synthesizer
- Working directory: c:\Users\kyleh\tdesktop\.agents\explorer_m2_2
- Original parent: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Milestone: M2 (Navigation & Calls Menu Integration)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement / modify source code directly
- Must check data_histories.cpp, core_settings.h/cpp, settings_privacy_security.cpp, and fork docs
- Ensure strict compliance with binary serialization rules (append at end of stream, !stream.atEnd() guard)
- Output handoff report in .agents/explorer_m2_2/handoff.md

## Current Parent
- Conversation ID: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Updated: 2026-08-20T19:21:45Z

## Investigation State
- **Explored paths**:
  - `Telegram/SourceFiles/data/data_histories.cpp` (lines 713-722, 173-320, 686-711, 749-764)
  - `Telegram/SourceFiles/core/core_settings.h` (lines 784-795, 1153)
  - `Telegram/SourceFiles/core/core_settings.cpp` (lines 295, 464, 634, 870, 1246, 346-349, 524-528, 1055-1060)
  - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp` (lines 1088-1118, 1190-1205)
  - `Telegram/Resources/langs/lang.strings` (lines 902-903)
- **Key findings**:
  1. `data_histories.cpp:717-721`: Read receipts suppression is correctly hooked in `Histories::sendReadRequest`. When `ghostMode()` is true, `state.willReadTill = 0; state.willReadWhen = 0; return;` suppresses sending `MTPchannels_ReadHistory` and `MTPmessages_ReadHistory`. Line 716 has a prohibited single-line comment.
  2. `core_settings.cpp`: Serialization bug identified. `_ghostMode` was inserted into the middle of the sequential stream (lines 295, 464, 870) between `_cornerReaction` and `_translateButtonEnabled`, violating `AGENTS.md` binary serialization append-at-end rule. It must be moved to the end of the stream after `_chatFiltersTabsMode`.
  3. `settings_privacy_security.cpp:1089`: Bug identified. `const auto settings = Core::App().settings();` decays reference and creates a value copy, causing member access `settings->` to fail compilation and mutations to be lost. Must be `const auto settings = &Core::App().settings();`.
  4. `lang.strings:902-903`: Keys `lng_settings_ghost_mode` and `lng_settings_ghost_mode_about` exist and are correctly defined.
- **Unexplored areas**: None within M2 Ghost Mode scope.

## Key Decisions Made
- Prepared detailed evidence chain and exact proposed diffs for Worker.

## Artifact Index
- DISPATCH.md — Dispatch log
- BRIEFING.md — Persistent context & memory
- progress.md — Liveness & progress heartbeat
- handoff.md — Comprehensive handoff report
