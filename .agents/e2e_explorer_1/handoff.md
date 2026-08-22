# Handoff Report: E2E Testing Track (Categories 1–4, Features 1–15)

**Agent**: Explorer 1 (`e2e_explorer_1`)  
**Parent Agent**: `1df83d47-a9a4-4674-a88d-a8a51c46a12a`  
**Working Directory**: `c:\Users\kyleh\tdesktop\.agents\e2e_explorer_1\`  
**Report Artifact**: `c:\Users\kyleh\tdesktop\.agents\e2e_explorer_1\report.md`  

---

## 1. Observation

Direct observations from codebase inspection across Features 1 through 15:

1. **Feature 1 & 2 (Ghost Mode & Settings Persistence)**:
   - `Telegram/SourceFiles/data/data_histories.cpp:717-721`:
     ```cpp
     // Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers
     if (Core::App().settings().ghostMode()) {
         state.willReadTill = 0;
         state.willReadWhen = 0;
         return;
     }
     ```
   - `Telegram/SourceFiles/core/core_settings.h:785-794, 1153`: `rpl::variable<bool> _ghostMode = false;`, `ghostMode()`, `ghostModeValue()`, `ghostModeChanges()`.
   - `Telegram/SourceFiles/core/core_settings.cpp:295, 464, 634, 870, 1246`: Serialized via `QDataStream` at the end of the settings stream: `stream >> ghostMode; _ghostMode = (ghostMode == 1);`.

2. **Feature 3 (Multi-Connection MTProto Chunk Downloading)**:
   - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:25-26`:
     ```cpp
     constexpr auto kStartSessionsCount = 4;
     constexpr auto kMaxSessionsCount = 16;
     ```
   - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:286-298`: Increments sessions up to `kMaxSessionsCount` on consecutive chunk transfer successes.
   - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:301-310`: `chooseSessionIndex(dcId)` chooses the session with minimum `requested` bytes via `ranges::min_element`.

3. **Feature 4 to 10 (Call UI & Controls)**:
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:859-877`: `_gridModeButton` created with `st::groupCallScreenShareSmall`, accessible label `"Grid View (1x1, 2x2, 3x3)"`, and reactive progress binding.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:558-614`: `_chatPanel` slide-out configured with `Qt::WA_TranslucentBackground`, `_chatPanelClose` at `(4, 4)`, and `MessagesUi` parenting.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:243, 689, 2597`: `_hangup` button wired to `endCall()` with `tr::lng_group_call_leave()`.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:2583-2592`: Camera toggle tooltip switches dynamically between `lng_group_call_tooltip_camera` and `lng_group_call_tooltip_camera_off`.
   - `Telegram/SourceFiles/calls/calls.style:17-28`: `CallButton { button: IconButton; ... }` defines the unified button primitive.
   - `Telegram/lib_ui/ui/colors.palette:571`: `callCancelRipple: #c04646; // phone call popup cancel button ripple effect`.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:272-275`: Floating PiP webcam overlay removed; local camera feeds integrate directly into `_viewport` as standard tiles (`self = true`).

4. **Feature 11 to 15 (Multi-Display & DisplayCoordinator Routing)**:
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h:37-49`:
     ```cpp
     enum class DisplayRole { ActiveSpeaker, GridViewport, ChatStation, None };
     struct DisplayWindow { base::unique_qptr<QWidget> widget; std::unique_ptr<Viewport> viewport; DisplayRole role; QScreen *screen; };
     ```
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:92-139`: `createDisplayWindow` instantiates frameless top-level `QWidget` on auxiliary `QScreen` with a dedicated `Viewport`.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:232-263`: `pinToScreen` and `unpinFromScreen` manage per-screen routed endpoints and stage viewports.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:317-319`: `updateAudioLevels` explicitly disables active-speaker slot hijacking on auxiliary displays.

---

## 2. Logic Chain

1. **Test Derivation Grounding**: The 75 test cases were derived directly from the code definitions observed in `PROJECT.md`, `docs/fork_features.md`, and the actual C++ implementations in `Telegram/SourceFiles/`.
2. **Category Partitioning**:
   - Features 1–2 map to `tests/e2e/tier1_features/test_t1_privacy_network.py` (Ghost Mode suppression & persistence).
   - Feature 3 maps to `tests/e2e/tier1_features/test_t1_privacy_network.py` (MTProto multi-session chunk downloading).
   - Features 4–10 map to `tests/e2e/tier1_features/test_t1_calls_ui.py` (Grid toggle, chat slide-out, hangup, camera controls, IconButton, palette colors, PiP removal).
   - Features 11–15 map to `tests/e2e/tier1_features/test_t1_multi_display.py` (Multi-monitor stage windows, display prompts, role routing, async video frame dispatch, active-speaker isolation).
3. **Completeness & Determinism**: Each test case specifies inputs, execution steps, expected outcomes, state checks, and mock harness requirements, ensuring 100% reproducibility and test independence.

---

## 3. Caveats

- **WebRTC Network Simulation**: Frame consumption and video track tests rely on mock video sinks/renderers (`CallSimulator`) rather than hardware camera/GPU encoders to maintain headless CI determinism.
- **Display Topology**: Multi-monitor tests assume `QGuiApplication::screens()` virtual screen injection or Qt headless platform plugin screen mocking (`-platform offscreen` or mock `QScreen` list).

---

## 4. Conclusion

A comprehensive technical specification comprising exactly 75 distinct Tier 1 E2E tests across Categories 1 to 4 (Features 1 to 15) has been successfully created and documented in `c:\Users\kyleh\tdesktop\.agents\e2e_explorer_1\report.md`. All test cases strictly adhere to opaque-box testing guidelines and fully map to the fork's architectural requirements.

---

## 5. Verification Method

To independently verify the test specifications and codebase references:

1. **Verify Report Artifact**:
   - Inspect `c:\Users\kyleh\tdesktop\.agents\e2e_explorer_1\report.md` for the full 75-test catalog across Features 1–15.
2. **Codebase Symbol Check**:
   - Verify Ghost Mode: grep `ghostMode` in `Telegram/SourceFiles/data/data_histories.cpp` and `Telegram/SourceFiles/core/core_settings.cpp`.
   - Verify MTProto 16 Sessions: grep `kMaxSessionsCount` in `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`.
   - Verify Display Coordinator: grep `DisplayCoordinator` and `DisplayRole` in `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h`.
   - Verify Palette Color: grep `callCancelRipple` in `Telegram/lib_ui/ui/colors.palette`.
3. **Execution Command (once test implementation track completes)**:
   ```bash
   py tests/e2e/run_all.py --tier 1
   ```
