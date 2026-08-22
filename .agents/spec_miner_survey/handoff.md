# Handoff Report — Spec Miner Survey Phase

**Agent**: Spec Miner (`.agents/spec_miner_survey/`)  
**Parent Agent**: `5278ca9a-12ca-434c-963d-a5a03310dd33`  
**Date**: 2026-08-20T19:15:00Z  
**Type**: Hard Handoff

---

## 1. Observation

1. **Authoritative Request & Fork Features Documentation**:
   - `docs/fork_features.md` contains 57 distinct feature items across 13 functional categories (Privacy & Ghost Mode E3, Multi-Connection MTProto B1, Call UI & Controls, Multi-Display & Routing DisplayCoordinator, Grid Layout & Pin System, Floating Overlay, Participant Sidebar & Search, Audio/Microphone Zero-Mic, Main Menu & Navigation, UI Tweaks & Polish, Context Menus & Cross-UI, Backend Engine C1/A1, Build & Toolchain).
   - `ORIGINAL_REQUEST.md` (lines 10-12) requires auditing the repository against `docs/fork_features.md` on branch `nightly`, implementing or finalizing all partially completed or missing features (including `calls_box_controller.cpp/.h`, SQLite PRAGMA tuning C1, WebRTC jitter clamping A1), and strictly adhering to `REVIEW.md` and `AGENTS.md`.

2. **Codebase State Probed**:
   - **Ghost Mode (E3)**: Implemented in `core/core_settings.h` (lines 785-794), `core/core_settings.cpp` (lines 464, 634, 870), `data/data_histories.cpp` (lines 717-721), and `settings/sections/settings_privacy_security.cpp` (lines 1093-1117).
   - **Multi-Connection MTProto (B1)**: Configured in `storage/download_manager_mtproto.h` and `storage/download_manager_mtproto.cpp` with `kDownloadPartSize = 128 KB`, `kMaxSessionsCount = 16`, and `kMaxWaitedInSession = 4 MB`.
   - **Call UI & Controls / Style**: `calls.style` has `CallButton` struct defined (line 17); `Telegram/lib_ui/ui/colors.palette` has `callCancelRipple: #c04646` (line 571).
   - **DisplayCoordinator**: `calls/group/calls_group_display_coordinator.h` and `.cpp` implement `DisplayCoordinator`, `DisplayRole`, and multi-display routing with `updateAudioLevels` guarding against 2nd screen hijacking.
   - **Floating Overlay**: `calls/group/calls_group_floating_overlay.h` and `.cpp` implement frameless transparent window with `Ctrl+Shift+T` shortcut and mouse wheel opacity control, with chat placeholder in `setupChatContent`.
   - **Calls Box Controller & Main Menu**: `calls/calls_box_controller.h` and `.cpp` contain `ShowCallsMenu` (line 930) and `ListController`. In `window/window_main_menu.cpp` (line 707), the Calls button currently calls `ShowCallsBox` directly instead of `ShowCallsMenu` or a submenu, and Wallet item is listed under My Profile in `docs/fork_features.md`.
   - **Rich Tasks**: `api/api_rich_tasks.h` and `api/api_rich_tasks.cpp` implement `Api::RichTasks` with debounced `EditRichMessage`.
   - **Backend Performance C1 / A1**:
     - C1 (SQLite PRAGMA tuning): `docs/fork_features.md` specifies WAL journaling (`PRAGMA journal_mode = WAL;`) and memory-mapped I/O (`PRAGMA mmap_size = 268435456;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA cache_size = -64000;`).
     - A1 (WebRTC Jitter Clamping): `ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp` (lines 1565-1566) and `MediaManager.cpp` (line 364) configure `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50`.
   - **Build & Language Keys**: `Telegram/CMakeLists.txt` registers all fork source files (lines 456-459); `Telegram/Resources/langs/lang.strings` defines `lng_group_call_context_pin_to_grid` (line 6463) and `lng_group_call_open_chat` (line 6464).

---

## 2. Logic Chain

1. Starting from `ORIGINAL_REQUEST.md` and `docs/fork_features.md`, every single feature requirement was mapped against the codebase.
2. Direct source code examination revealed which features are fully implemented, which have existing stubs or placeholders (e.g. `calls_box_controller.cpp` vs `window_main_menu.cpp` wiring; `calls_group_floating_overlay.cpp` chat binding), and what constants/settings govern each subsystem.
3. Every feature was categorized and documented with inputs, outputs, error behaviors, exact constant values, and acceptance criteria in `.agents/spec_miner_survey/report.md`.
4. Style guidelines from `REVIEW.md` (no single-line comments, empty line before closing brace in classes, operators on continuation lines, `tr::` projections, `base::take`, no `Q_OS_LINUX`) were cross-referenced to identify potential style violations in fork files.

---

## 3. Caveats

- `run_command` was not used to execute interactive build or git commands due to subagent environment permissions. All source inspection was performed directly via file system tools (`view_file`, `grep_search`, `find_by_name`).
- No source code or build files were modified in this phase, preserving strict read-only compliance for the Spec Miner archetype.

---

## 4. Conclusion

The specification survey is complete. All 57 features across all 13 categories described in `docs/fork_features.md` and referenced in `ORIGINAL_REQUEST.md` have been cataloged in `report.md`. The orchestrator and implementation subagents have complete, unambiguous acceptance criteria, file references, constants, and edge case behaviors to proceed with the implementation, audit, and verification phases.

---

## 5. Verification Method

To independently verify the survey findings:
1. Inspect `c:\Users\kyleh\tdesktop\.agents\spec_miner_survey\report.md` for complete feature coverage.
2. Cross-reference entries with `c:\Users\kyleh\tdesktop\docs\fork_features.md` and `c:\Users\kyleh\tdesktop\README-WINDOWS-BUILD.md`.
3. Inspect source files referenced in Section 1 using `view_file` or `grep_search` to verify line numbers and symbol names.
