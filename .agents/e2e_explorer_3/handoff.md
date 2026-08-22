# Handoff Report: Tier 1 E2E Test Suite (Features 38–57) & Test Harness Architecture

**Author**: Explorer 3 (`e2e_explorer_3`)  
**Scope**: Categories 9 to 13 (Features 38–57) + `tests/e2e/run_all.py` Test Harness Architecture  
**Target Recipient**: E2E Testing Orchestrator / Implementation Subagents  
**Date**: August 20, 2026  

---

## 1. Observation

Direct observations from the repository codebase, documentation, and build definitions:

1. **Category 9 (Main Menu & Navigation)**:
   - `Telegram/SourceFiles/window/window_main_menu.cpp:707`: Invokes `::Calls::ShowCallsBox(controller);` which in fork enhancements bridges to `Calls::ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window)`.
   - `Telegram/SourceFiles/calls/calls_box_controller.cpp:930-994`: Implements `ShowCallsMenu`, adding active group calls rows from `state->groupCallsDelegate.peerListRowAt(i)`, separator, "Start Call" (`tr::lng_confcall_create_call`), and "Calls" history (`tr::lng_call_box_title`).
   - `Telegram/SourceFiles/window/window_main_menu.cpp:662-675`: Places "My Profile" at index 0, followed by the TON Wallet entry with green `NEW` badge (`st::mainMenuButton`, `&st::menuIconProfile`).
2. **Category 10 (UI Tweaks & Polish)**:
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:2865-2880`: In Wide mode, explicitly hides obstructing buttons: `toggle(_screenShare, false); toggle(_message, false); toggle(_wideMenu, false); toggle(_settings, false); toggle(_video, false); toggle(_gridModeButton, false); toggle(_chatToggle, false); toggle(_mute, false); toggle(_hangup, false); if (_controlsBackgroundWide) _controlsBackgroundWide->hide();`.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:427-436`: Event filter intercepts `QKeyEvent` with `Qt::Key_T && Qt::ControlModifier && Qt::ShiftModifier`, executing `if (_floatingOverlay) _floatingOverlay->toggle();` and returning `base::EventFilterResult::Cancel`.
   - `Telegram/SourceFiles/calls/calls.style:18, 921-956`: Defines `groupCallShareInner: IconButton(groupCallSettingsInner)`, `groupCallVideoInnerActive`, and `groupCallMessageInnerActive` inheriting `IconButton(callButton)`.
3. **Category 11 (Context Menus & Cross-UI)**:
   - `Telegram/SourceFiles/api/api_rich_tasks.h:30-58` and `api/api_rich_tasks.cpp:23, 40-135`: `kSendDelay = crl::time(1000)`. `RichTasks::toggle` validates `togglingAllowed`, clones `Iv::RichPage`, calls `state.toggleTaskState(source)`, applies locally via `item->applyLocalRichPage`, sets `entry.dirty = true`, and calls `_sendTimer.callOnce(kSendDelay)`. On RPC failure, rolls back via `item->applyLocalRichPage(original)`.
   - `Telegram/Resources/langs/lang.strings:6463-6464`: `"lng_group_call_context_pin_to_grid" = "Pin to grid";` and `"lng_group_call_open_chat" = "Open Chat";`.
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:1037-1048`: `Viewport::togglePin(const VideoEndpoint &endpoint, bool pinned)` mutates `_pinnedEndpoints` and `_pinnedSlots`, then invokes `updateTilesGeometry()`.
4. **Category 12 (Backend / Engine)**:
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:916-940`: `setTileGeometry` uses `kMedium = style::ConvertScale(540)` and `kSmall = style::ConvertScale(240)`. Fires `_qualityRequests.fire(VideoQualityRequest{ endpoint, quality })` when `tile->updateRequestedQuality(quality)` is true.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h:116-118`: Active speaker tracking variables `_speakerThreshold = 0.05`, `_speakerHoldFrames = 0`.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:318`: `updateAudioLevels` is a no-op: `// Active speaker auto-stealing disabled to ensure only explicitly pinned feeds appear on secondary displays`.
   - `PROJECT.md:87`: SQLite engine PRAGMAs: `PRAGMA journal_mode = WAL;`, `PRAGMA mmap_size = 268435456;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA cache_size = -64000;`, `PRAGMA temp_store = MEMORY;`.
   - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`: `audioOptions.audio_jitter_buffer_fast_accelerate = true;` and `audioOptions.audio_jitter_buffer_min_delay_ms = 50;`.
5. **Category 13 (Build & Toolchain)**:
   - `README-WINDOWS-BUILD.md:1-151`: Documents MSVC 2022 prerequisites, `prepare.py` tweaks, `-j1` memory safety flag for PCH memory exhaustion prevention, and `CallButton` codegen struct.
   - `Telegram/CMakeLists.txt:199-200, 456-465`: Registers `api/api_rich_tasks.cpp`, `calls/calls_box_controller.cpp`, `calls/group/calls_group_display_coordinator.cpp`, `calls/group/calls_group_floating_overlay.cpp`, `calls/group/calls_group_viewport_tile.cpp`.

---

## 2. Logic Chain

1. **Full Feature Partitioning**:
   - The fork feature inventory spans 57 features across 13 categories.
   - Explorer 1 defined Tier 1 tests for Features 1–15 (Categories 1–4, 75 tests).
   - Explorer 2 defined Tier 1 tests for Features 16–37 (Categories 5–8, 110 tests).
   - Explorer 3 (this report) defines Tier 1 tests for Features 38–57 (Categories 9–13, 100 tests) plus the comprehensive `run_all.py` test harness architecture.
   - Total Tier 1 test cases: 75 + 110 + 100 = 285 tests (exact match to `TEST_INFRA.md:152`).

2. **Grounded Test Design**:
   - Every single test case (`TEST-T1-F38-01` to `TEST-T1-F57-05`) specifies exact Preconditions, Actions, Expected Outputs, State Verifications, and Mock Requirements.
   - State mutations (such as Rich Tasks debounce timers, SQLite PRAGMA execution, WebRTC AudioOptions, and Viewport quality thresholds) are mapped to explicit programmatic assertions.

3. **Oracles & Simulators**:
   - `SQLitePragmaOracle` validates all 5 PRAGMA statements and fallback mechanics.
   - `WebRTCJitterOracle` verifies fast accelerate and 50ms min delay clamping.
   - `RichTasksStateOracle` tracks in-flight request IDs, dirty bit scheduling, and error rollback.
   - `UiSimulator` & `GridSolverOracle` provide opaque-box behavioral validation of GUI widgets and layout geometry.

4. **Framework Architecture**:
   - `tests/e2e/run_all.py` is architected as an autonomous test runner that loads all 4 tiers, supports flexible filtering (`--tier`, `--category`, `--feature`, `--filter`), outputs structured terminal and JUnit/JSON reports, and yields strict exit codes (`0` on pass, `1` on fail).

---

## 3. Caveats

1. **GUI Rendering in Headless CI**: Virtual UI testing relies on Qt offscreen platform plugin (`QT_QPA_PLATFORM=offscreen` or `UiSimulator` abstraction) to avoid requiring a physical GPU display during automated headless test runs.
2. **WebRTC Media Hardware**: WebRTC playout delay testing simulates NetEq buffer depths and audio packet arrival rather than capturing physical sound card waveforms.
3. **Multi-Monitor Physical Hardware**: Virtual `QScreen` instances are emulated by `DisplayCoordinatorMock` / `QtScreenMock` rather than requiring multiple physical display panels connected to the test runner machine.

---

## 4. Conclusion

- Explorer 3 has successfully produced a 100% complete, fully grounded technical specification for Tier 1 tests covering Features 38 through 57 (100 distinct test cases).
- The complete test runner framework architecture (`tests/e2e/run_all.py`) has been fully designed and specified with all supporting mock modules, CLI flags, discovery mechanisms, and reporting formats.
- All specifications are documented in `c:\Users\kyleh\tdesktop\.agents\e2e_explorer_3\report.md` and are ready for implementation in Tier 1 test scripts.

---

## 5. Verification Method

To independently verify the findings and specifications in this report:

1. **Verify Report and Documentation Artifacts**:
   - View `c:\Users\kyleh\tdesktop\.agents\e2e_explorer_3\report.md` to confirm all 100 test specifications (Features 38–57) and framework architecture.
   - Verify feature count: `grep -c "#### TEST-T1-F" c:\Users\kyleh\tdesktop\.agents\e2e_explorer_3\report.md` (should return exactly 100).
2. **Verify Codebase Grounding**:
   - Inspect `calls_box_controller.cpp:930` for `ShowCallsMenu`.
   - Inspect `calls_group_panel.cpp:2865` for wide mode button cleanup.
   - Inspect `calls_group_panel.cpp:429` for `Ctrl+Shift+T` event filter.
   - Inspect `api_rich_tasks.cpp:23, 40-60` for `kSendDelay = 1000` and debounce logic.
   - Inspect `GroupInstanceCustomImpl.cpp:1565` for `audio_jitter_buffer_fast_accelerate` and `50` ms delay.
   - Inspect `Telegram/CMakeLists.txt:199, 456` and `lang.strings:6463-6464`.
3. **Execution Command for Test Runner**:
   - Once implemented, the test suite is executed via:
     ```powershell
     py tests/e2e/run_all.py --tier 1
     ```
   - Successful run returns exit code `0`.
