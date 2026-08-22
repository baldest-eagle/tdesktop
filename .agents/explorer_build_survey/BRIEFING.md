# BRIEFING — 2026-08-20T19:12:50Z

## Mission
Perform comprehensive Build & Architecture Survey for Telegram Desktop codebase on Windows Native/WSL environment.

## 🔒 My Identity
- Archetype: explorer
- Roles: Explorer, Build & Architecture Survey
- Working directory: c:\Users\kyleh\tdesktop\.agents\explorer_build_survey
- Original parent: 5278ca9a-12ca-434c-963d-a5a03310dd33
- Milestone: Build & Architecture Survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Produce structured report in c:\Users\kyleh\tdesktop\.agents\explorer_build_survey\report.md
- Self-contained handoff.md

## Current Parent
- Conversation ID: 5278ca9a-12ca-434c-963d-a5a03310dd33
- Updated: 2026-08-20T19:12:50Z

## Investigation State
- **Explored paths**:
  - `CMakeLists.txt`, `Telegram/CMakeLists.txt`, `cmake/options.cmake`, `cmake/options_win.cmake`, `cmake/init_target.cmake`, `cmake/variables.cmake`, `cmake/nice_target_sources.cmake`, `cmake/lib_tgcalls.cmake`, `cmake/external/qt/package.cmake`
  - `out/CMakeCache.txt`, `out/Telegram/Telegram.vcxproj`, `out/Debug/Telegram.exe`, `out/Telegram/Telegram.dir/Debug/*.obj`
  - `Telegram/SourceFiles/calls/calls_box_controller.cpp/.h`
  - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp/.h`, `calls_group_floating_overlay.cpp/.h`
  - `Telegram/SourceFiles/api/api_rich_tasks.cpp/.h`, `chat_helpers/rich_paste_toast.cpp/.h`
  - `Telegram/lib_storage/`, `Telegram/ThirdParty/tgcalls/`
  - `README-WINDOWS-BUILD.md`, `docs/fork_features.md`, `ARCHITECTURE.md`, `AGENTS.md`
- **Key findings**:
  - Target `Telegram` is configured for MSVC v143 (VS 2022 BuildTools 14.44.35207, x64, Windows SDK 10.0.26100.0) in C++20.
  - Existing Debug executable `out/Debug/Telegram.exe` (492 MB) and PDB (2.98 GB) exist and link all sub-libraries cleanly.
  - `calls_box_controller.cpp/.h` and all related fork sources are fully registered in `Telegram/CMakeLists.txt` and have valid object files compiled.
  - WebRTC jitter clamping (`A1`) is configured in `tgcalls` (`GroupInstanceCustomImpl.cpp` / `InstanceV2Impl.cpp`) with `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50`.
  - Single-threaded build (`-j1`) or bounded parallelism is required on Windows native rebuilds to avoid MSVC PCH heap limits on huge Qt resource translation units.
- **Unexplored areas**: None remaining for build and architecture survey scope.

## Key Decisions Made
- Confirmed full build target and source registration integrity.
- Detailed the difference between Windows Native MSVC build flow and WSL Docker build flow.

## Artifact Index
- c:\Users\kyleh\tdesktop\.agents\explorer_build_survey\report.md — Detailed build and architecture survey report
- c:\Users\kyleh\tdesktop\.agents\explorer_build_survey\handoff.md — Handoff report
- c:\Users\kyleh\tdesktop\.agents\explorer_build_survey\progress.md — Liveness and progress tracking
