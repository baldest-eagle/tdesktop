# Handoff Report — Codebase Survey Phase

**Agent**: `explorer_codebase_survey`  
**Working Directory**: `c:\Users\kyleh\tdesktop\.agents\explorer_codebase_survey\`  
**Target File**: `report.md`  

---

## 1. Observation

1. **Ghost Mode (E3)**:
   - `Telegram/SourceFiles/data/data_histories.cpp:716-721`:
     ```cpp
     // Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers
     if (Core::App().settings().ghostMode()) {
         state.willReadTill = 0;
         state.willReadWhen = 0;
         return;
     }
     ```
   - `Telegram/SourceFiles/core/core_settings.h:784-795` and `core_settings.cpp:295,464,634,870,1246` provide binary QDataStream serialization.
   - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp:1088-1117,1203`: `BuildGhostModeSection` adds the toggle to privacy settings.

2. **Network Multi-Connection (B1)**:
   - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:25-26`:
     ```cpp
     constexpr auto kStartSessionsCount = 4;
     constexpr auto kMaxSessionsCount = 16;
     ```

3. **Floating Overlay Incomplete Stub**:
   - `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp:149-158`:
     ```cpp
     void FloatingOverlay::setupChatContent() {
         // Note: MessagesUi requires a proper parent with session/show
         // This is a placeholder - full implementation needs access to
         // the Panel's uiShow() and _call->messages() data
         if (!_panel) {
             return;
         }
         // Get messages data from panel
         // _messagesUi = std::make_unique<MessagesUi>(...);
     }
     ```

4. **Dynamic Grid Solver 50/50 Dead Code**:
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:560-584`:
     ```cpp
     const auto slotConstraint = _slotCount.current();
     const auto fixedGridDim = (slotConstraint == 1)
         ? 1
         : (slotConstraint == 4)
         ? 2
         : (slotConstraint == 9)
         ? 3
         : 0;

     if (fixedGridDim > 0) {
         const auto cols = fixedGridDim;
         const auto rows = fixedGridDim;
         const auto maxVisible = cols * rows;
         const auto visibleCount = std::min(count, maxVisible);
         const auto cellW = (outerWidth - (cols - 1) * skip) / float64(cols);
         const auto cellH = (outerHeight - (rows - 1) * skip) / float64(rows);

         // Special case: 2 feeds -> 50/50 split across the screen
         if (count == 2 && slotConstraint == 0) {
             const auto halfW = (outerWidth - skip) / 2;
             sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
             sizes[1].columns = sizes[1].rows = { halfW + skip, 0, halfW, outerHeight };
             result.useColumns = true;
             return result;
         }
     ```

5. **Calls Menu Disconnect**:
   - `Telegram/SourceFiles/calls/calls_box_controller.cpp:930-994` declares and implements `ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window)`.
   - `Telegram/SourceFiles/window/window_main_menu.cpp:707`:
     ```cpp
     addAction(
         tr::lng_menu_calls(),
         { &st::menuIconPhone }
     )->setClickedCallback([=] {
         ::Calls::ShowCallsBox(controller);
     });
     ```

6. **WebRTC Jitter Clamping (A1)**:
   - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`:
     ```cpp
     audioOptions.audio_jitter_buffer_fast_accelerate = true;
     audioOptions.audio_jitter_buffer_min_delay_ms = 50;
     ```
   - `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp:364`:
     ```cpp
     audioOptions.audio_jitter_buffer_fast_accelerate = true;
     ```

7. **Missing Language Key Usages**:
   - `Telegram/Resources/langs/lang.strings:6463-6464`: `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` exist in `lang.strings` but are not referenced in `Telegram/SourceFiles/`.

---

## 2. Logic Chain

1. **Ghost Mode (E3)** and **MTProto Multi-Connection (B1)** are fully integrated and functional in `data_histories.cpp` and `download_manager_mtproto.cpp`.
2. **DisplayCoordinator**, **In-Call Search**, **Alphabetical Sorting**, **Rich Tasks**, and **Listen-Only Mode** are operational in their respective modules (`calls_group_display_coordinator.cpp`, `calls_group_members.cpp`, `api_rich_tasks.cpp`, `calls_group_panel.cpp`).
3. Based on Observation 3, `FloatingOverlay` cannot display messages because `_messagesUi` is never instantiated in `setupChatContent()`.
4. Based on Observation 4, when `slotConstraint == 0`, `fixedGridDim` evaluates to 0, causing the entire `if (fixedGridDim > 0)` block to be skipped. Consequently, `count == 2` will never execute the 50/50 split and always falls through to the sqrt solver.
5. Based on Observation 5, `ShowCallsMenu` is written but disconnected; the main menu continues to invoke the modal `ShowCallsBox`.
6. Based on Observation 7, the UI context menus in `calls_group_members.cpp` only expose standard single-track camera/screen pin actions rather than "Pin to Grid" or in-meeting chat actions.

---

## 3. Caveats

- SQLite PRAGMA tuning (C1) is listed as a feature in `docs/fork_features.md`, but Telegram Desktop's architecture relies on `lib_storage` binary caching, not SQLite. Unless SQLite integration is being introduced as a separate storage subsystem, no SQLite PRAGMA calls exist in the tdesktop engine.
- Build commands through WSL/Docker were not run during this read-only exploration phase.

---

## 4. Conclusion

The fork has a strong foundation with the majority of custom features already implemented. The primary pending items and fixes required for complete readiness are:
1. Complete `FloatingOverlay::setupChatContent()` with `MessagesUi` parenting and clean up style/formatting in `calls_group_floating_overlay.cpp`.
2. Fix the 50/50 dynamic grid solver logic bug in `calls_group_viewport.cpp:577`.
3. Wire `Calls::ShowCallsMenu` into `window_main_menu.cpp`.
4. Wire `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` in `calls_group_members.cpp`.
5. Remove single-line descriptive comments across modified files per `REVIEW.md`.

---

## 5. Verification Method

- Inspect `c:\Users\kyleh\tdesktop\.agents\explorer_codebase_survey\report.md` for full breakdown.
- Inspect the specific code lines cited in Observations 1-7 via `view_file`.
- Compile via Windows Native Debug build:
  ```cmd
  cmake --build out --config Debug --target Telegram
  ```
