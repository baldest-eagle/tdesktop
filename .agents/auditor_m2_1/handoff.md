# Forensic Audit Report: Milestone M2 — Navigation & Calls Menu Integration

**Work Product**: Milestone M2 Implementation across 8 files  
**Profile**: General Project (Development / Demo / Benchmark Modes)  
**Auditor**: Forensic Auditor (`auditor_m2_1`)  
**Target Parent**: Sub-Orchestrator M2 (`cc351ddd-67a8-4da7-b053-fdba88cdf5ba`)  
**Date**: 2026-08-20  
**Verdict**: **CLEAN**

---

## 1. Observation

Direct forensic code inspections across all 8 owned files for Milestone M2:

### 1.1 Main Menu & Calls Popup (`Telegram/SourceFiles/window/window_main_menu.cpp`)
- **Calls Popup Menu Integration (lines 704–714)**:
  ```cpp
  const auto calls = addAction(
      tr::lng_menu_calls(),
      { &st::menuIconPhone }
  );
  calls->setClickedCallback([=] {
      _contextMenu = base::make_unique_q<Ui::PopupMenu>(
          calls,
          st::popupMenuWithIcons);
      ::Calls::ShowCallsMenu(_contextMenu.get(), controller);
      _contextMenu->popup(QCursor::pos());
  });
  ```
  - Replaces modal dialog with dynamic popup instantiation using `st::popupMenuWithIcons` and populates entries through `::Calls::ShowCallsMenu`.
- **Wallet Entry Placement & NEW Badge (lines 663–678)**:
  - `SetupMenuBots(_menu, controller)` is called immediately below "My Profile" (`tr::lng_menu_my_profile()`) and before the separator shadow (`object_ptr<Ui::PlainShadow>(_menu)`), rendering TON Wallet with the green `NEW` badge (`Ui::NewBadge::AddToRight(button)`) via `window_main_menu_helpers.cpp:355–357`.
- **Style Includes**:
  - Alphabetical includes with style headers segregated at lines 71–75: `style_chat.h`, `style_menu_icons.h`, `style_settings.h`, `style_window.h`, `style_window_main_menu.h`.

### 1.2 Calls Menu Controller (`Telegram/SourceFiles/calls/calls_box_controller.h` & `calls_box_controller.cpp`)
- **Header (`calls_box_controller.h`)**:
  - Folder-first alphabetical includes (lines 10–12): `boxes/peer_list_box.h`, `mtproto/sender.h`, `ui/layers/generic_box.h`.
  - C++17 nested namespace `namespace Calls::GroupCalls {` (line 18).
  - Empty line before closing braces for `ListController` (line 36) and `BoxController` (line 79).
  - Function declaration `void ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window);` (lines 89–91).
- **Implementation (`calls_box_controller.cpp:931–995`)**:
  - `ShowCallsMenu` allocates `State` containing `groupCallsController`, `groupCallsDelegate`, `callsController`, `callsDelegate`, and `dummy` widget on `menu->lifetime()`.
  - Binds live group calls rows to `window->showPeerHistory(peer, SectionShow::Way::ClearStack)`.
  - Adds "Start Group Call" action to `Calls::Group::PrepareCreateCallBox`.
  - Adds "Call History" action to `Calls::ShowCallsBox(window)`.
  - All action callbacks are safely guarded with `crl::guard(menu, [=] { ... })`.
  - Zero single-line comments; parameter indentation properly formatted.

### 1.3 Ghost Mode Settings & Binary Serialization (`core_settings.h`, `core_settings.cpp`, `settings_privacy_security.cpp`)
- **Core Settings Header (`core_settings.h:784–795, 1153`)**:
  - Member `rpl::variable<bool> _ghostMode = false;`.
  - Accessors: `setGhostMode(bool)`, `ghostMode() const`, `ghostModeValue() const`, `ghostModeChanges() const`.
- **Binary Stream Ordering & Backward Compatibility (`core_settings.cpp`)**:
  - Positioned strictly at stream end after `_chatFiltersTabsMode`:
    1. Size reservation (line 349): `+ sizeof(qint32); // _ghostMode`
    2. Write serialization (line 527): `stream << qint32(_ghostMode.current() ? 1 : 0);`
    3. Deserialization local initialization (line 634): `qint32 ghostMode = _ghostMode.current() ? 1 : 0;`
    4. Guarded read (lines 1058–1060): `if (!stream.atEnd()) { stream >> ghostMode; }`
    5. Field assignment (line 1246): `_ghostMode = (ghostMode == 1);`
  - Fully conforms to `AGENTS.md` local storage serialization rules.
- **Privacy & Security Settings UI (`settings_privacy_security.cpp:1088–1118`)**:
  - `BuildGhostModeSection` captures `const auto settings = &Core::App().settings();` ensuring proper singleton reference.
  - Reactive toggle filter `toggled != settings->ghostMode()` avoids redundant events and triggers `Core::App().saveSettingsDelayed()`.
  - Registered inside `PrivacySecurity::setupContent()` (line 1203).

### 1.4 Ghost Mode Read Receipt Suppression (`Telegram/SourceFiles/data/data_histories.cpp`)
- **`Histories::sendReadRequest` (lines 713–720)**:
  ```cpp
  void Histories::sendReadRequest(not_null<History*> history, State &state) {
      Expects(state.willReadTill > state.sentReadTill);

      if (Core::App().settings().ghostMode()) {
          state.willReadTill = 0;
          state.willReadWhen = 0;
          return;
      }

      const auto tillId = state.sentReadTill = base::take(state.willReadTill);
  ```
  - When `ghostMode()` is enabled, zeros `willReadTill`/`willReadWhen` and immediately returns, preventing any `MTPchannels_ReadHistory` or `MTPmessages_ReadHistory` requests from being constructed or dispatched.
  - Zero single-line comments in modified logic.

### 1.5 Rich Tasks MTProto Integration & Iterator Safety (`api_rich_tasks.h` & `api_rich_tasks.cpp`)
- **Header (`api_rich_tasks.h`)**:
  - Alphabetical includes (`base/flat_map.h`, `base/timer.h`).
  - C++17 nested namespace `namespace Iv::Markdown {`.
  - Initialized struct members in `Accumulated`.
- **Implementation (`api_rich_tasks.cpp`)**:
  - `togglingAllowed`: checks `item->richPage()`, `!page->part`, and `item->allowsEdit(...)`.
  - `toggle`: creates modified `Iv::RichPage` via `Iv::Editor::State::toggleTaskState`, applies local optimistic update `item->applyLocalRichPage`, and debounces with `base::Timer _sendTimer` at 1000ms.
  - `sendAccumulated` (lines 64–81): iterates `for (auto &[itemId, entry] : _entries)` without in-loop container removal, calling `send(itemId, entry)`.
  - `send` (lines 83–109): triggers `EditRichMessage` with serialized `Iv::SerializeInputRichMessage` (mode `FinalSubmit`).
  - `finishRequest` (lines 111–132): handles rollback to `entry.original` upon request failure, and reschedules if dirtied during flight.

---

## 2. Logic Chain

1. **Popup Menu & Window Session Integration**:
   - `window_main_menu.cpp` properly instantiates `Ui::PopupMenu` on `_contextMenu`, populated via `Calls::ShowCallsMenu`. All click handlers are protected by `crl::guard(menu, ...)`, eliminating use-after-free risks if the menu is dismissed during asynchronous events.
2. **Backward-Compatible Persistent Storage**:
   - Appending `_ghostMode` strictly to the tail of `Core::Settings` binary stream and guarding read operations with `!stream.atEnd()` guarantees that legacy config files load cleanly without size mismatch errors or deserialization corruption.
3. **Ghost Mode Integrity**:
   - Read receipt suppression intercepting `sendReadRequest` in `data_histories.cpp` effectively suppresses outbound MTProto read calls at the root history dispatcher while resetting pending read timers.
4. **Memory and Iterator Safety**:
   - Removing in-loop `_entries.remove` in `RichTasks::send` prevents iterator invalidation during `sendAccumulated()` traversal.
5. **Code Style & Guidelines**:
   - Zero single-line descriptive comments in new/modified code.
   - Proper folder-first alphabetical include ordering.
   - C++17 nested namespaces used across all modified headers.
   - Clean variable initialization and RAII guard patterns throughout.

---

## 3. Caveats

- **Decoupled Read Receipts**:
  - Ghost Mode decouples read marks exclusively on the local client without marking messages as read on the Telegram cloud or remote peers, in strict compliance with the fork specification in `docs/fork_features.md:8`.
- **Build Verification**:
  - Full end-to-end multi-target linking is scheduled for verification in Milestone M4 per the orchestrator dependency graph.

---

## 4. Conclusion

**Verdict: CLEAN**

No integrity violations, facade implementations, hardcoded test strings, fake stubs, unauthorized files, or hidden bypasses were detected. Milestone M2 implementation satisfies all architectural, security, and coding requirements.

---

## 5. Verification Method

1. **Main Menu Verification**:
   - Inspect `Telegram/SourceFiles/window/window_main_menu.cpp:704–714` to confirm `Ui::PopupMenu` and `::Calls::ShowCallsMenu` invocation.
   - Inspect `Telegram/SourceFiles/window/window_main_menu.cpp:674` for `SetupMenuBots` below "My Profile".
2. **Calls Controller Verification**:
   - Inspect `Telegram/SourceFiles/calls/calls_box_controller.h:18, 89–91` and `calls_box_controller.cpp:931–995`.
3. **Serialization Verification**:
   - Inspect `Telegram/SourceFiles/core/core_settings.cpp:349, 527, 1058–1060, 1246` to confirm stream tail positioning and `!stream.atEnd()` guards.
4. **Ghost Mode Verification**:
   - Inspect `Telegram/SourceFiles/data/data_histories.cpp:716–720` to verify early return and state zeroing.
   - Inspect `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp:1088–1118` for `const auto settings = &Core::App().settings();`.
5. **Rich Tasks Verification**:
   - Inspect `Telegram/SourceFiles/api/api_rich_tasks.cpp:64–88` to confirm iterator safety during container iteration.
