# Handoff Report: Reviewer 2 — Milestone M2 (Navigation & Calls Menu Integration)

## 1. Observation

A full independent audit was conducted on all Milestone M2 deliverables and touched files:
1. `Telegram/SourceFiles/window/window_main_menu.cpp`
2. `Telegram/SourceFiles/calls/calls_box_controller.h`
3. `Telegram/SourceFiles/calls/calls_box_controller.cpp`
4. `Telegram/SourceFiles/core/core_settings.h`
5. `Telegram/SourceFiles/core/core_settings.cpp`
6. `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
7. `Telegram/SourceFiles/data/data_histories.cpp`
8. `Telegram/SourceFiles/api/api_rich_tasks.h`
9. `Telegram/SourceFiles/api/api_rich_tasks.cpp`

### 1.1 Calls Menu & Main Menu Integration (`window_main_menu.cpp`)
- **Lines 704–714**:
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
  Direct modal `Calls::ShowCallsBox` was replaced with a dynamic `Ui::PopupMenu` attached to `_contextMenu`, populated via `Calls::ShowCallsMenu`, matching `PROJECT.md § Calls::ShowCallsMenu ↔ Window::MainMenu` and `docs/fork_features.md:61`.
- **Lines 662–678**:
  `SetupMenuBots(_menu, controller)` is positioned immediately beneath "My Profile" (`tr::lng_menu_my_profile()`) prior to channel/group creation actions. In `window_main_menu_helpers.cpp:355–357`, TON Wallet is rendered with `Ui::NewBadge::AddToRight(button)` using `st::windowBgActive`, fulfilling `docs/fork_features.md:62`.
- **Lines 69–75**:
  Header includes are alphabetized with nested directories first, style includes (`styles/style_*.h`) segregated with a blank line, and trailing comments removed.

### 1.2 Calls Box Controller Interface & Lifetime (`calls_box_controller.h/.cpp`)
- **Header (`calls_box_controller.h:89–92`)**:
  `void ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window);` exported cleanly with C++17 nested namespace `Calls::GroupCalls`.
- **Implementation (`calls_box_controller.cpp:931–995`)**:
  - `ShowCallsMenu` allocates `State` on `menu->lifetime().make_state<State>(window)`, encapsulating `GroupCalls::ListController` and `BoxController` delegates.
  - Dynamically populates active group calls via `state->groupCallsDelegate.peerListRowAt(i)` and connects history navigation guarded by `crl::guard(menu, ...)`.
  - Appends Start Conference Call (`Calls::Group::PrepareCreateCallBox`) and Call History (`Calls::ShowCallsBox`) actions with icon descriptors and separators.
  - All action callbacks are guarded against menu lifetime with `crl::guard`.
  - Include order (lines 10–54) complies with folder-first sorting; parameter indentation on `ShowCallsMenu` uses two tabs.

### 1.3 Core Settings Binary Serialization (`core_settings.h/.cpp`)
- **Header (`core_settings.h:784–795, 1153`)**:
  `rpl::variable<bool> _ghostMode = false;` initialized with default `false`. Accessors `ghostMode()`, `ghostModeValue()`, `ghostModeChanges()`, and `setGhostMode(bool)` provide reactive streams.
- **Serialization Size Calculation (`core_settings.cpp:345–350`)**:
  `_ghostMode` (+`sizeof(qint32)`) is added strictly at the end of stream calculations following `_chatFiltersTabsMode`.
- **Serialization Stream Writing (`core_settings.cpp:523–528`)**:
  ```cpp
		stream << qint32(SerializePlaybackSpeed(_audioPlaybackSpeed.current()));
		stream << qint32(_mediaGridZoomStep);
		stream << qint32(_pullToNextChannel.current() ? 1 : 0);
		stream << qint32(_chatFiltersTabsMode.current());
		stream << qint32(_ghostMode.current() ? 1 : 0);
  ```
  Guarantees `Ensures(result.size() == size)` passes without size mismatch.
- **Deserialization Stream Reading (`core_settings.cpp:634, 1058–1060, 1246`)**:
  `ghostMode` is defaulted to `_ghostMode.current() ? 1 : 0;` and deserialized conditionally via `if (!stream.atEnd()) { stream >> ghostMode; }` at the tail of the stream.
  Legacy storage buffers lacking the 4-byte ghostMode flag remain valid without offset corruption or deserialization failure, strictly adhering to `AGENTS.md § Local Storage Serialization`.

### 1.4 Reactive Settings UI & Read Mark Suppression (`settings_privacy_security.cpp`, `data_histories.cpp`)
- **Privacy Settings Section (`settings_privacy_security.cpp:1088–1118`)**:
  - Bound via `const auto settings = &Core::App().settings();`.
  - `toggle->toggledChanges() | rpl::filter(...) | rpl::on_next(...)` eliminates redundant set calls and persists changes through `Core::App().saveSettingsDelayed()` with `toggle->lifetime()`.
  - Wired into `PrivacySecurity::setupContent` at line 1203 between Top Peers and Account Self-Destruction.
- **MTProto Suppression (`data_histories.cpp:713–721`)**:
  ```cpp
void Histories::sendReadRequest(not_null<History*> history, State &state) {
	Expects(state.willReadTill > state.sentReadTill);

	if (Core::App().settings().ghostMode()) {
		state.willReadTill = 0;
		state.willReadWhen = 0;
		return;
	}
  ```
  When `ghostMode()` is true, resets `willReadTill` and `willReadWhen` to 0 and returns immediately. Outgoing `MTPmessages_ReadHistory` and `MTPchannels_ReadHistory` requests are completely suppressed at the network boundary.
  Single-line comments removed per `REVIEW.md`.

### 1.5 Rich Tasks Reactive Debounce, Optimistic UI & Iterator Safety (`api_rich_tasks.h/.cpp`)
- **Includes (`api_rich_tasks.h:10–11`)**:
  `base/flat_map.h` and `base/timer.h` ordered alphabetically.
- **Optimistic State & Debouncing (`api_rich_tasks.cpp:39–62, 64–81`)**:
  - `toggle()` clones `Iv::RichPage`, updates task checkbox state, snapshots `entry.original`, sets `entry.dirty = true`, applies local page optimistically to `HistoryItem`, and triggers `_sendTimer.callOnce(kSendDelay)` (1000ms debounce).
  - `sendAccumulated()` filters for non-busy, dirty entries and batches requests.
- **Iterator Safety Fix (`api_rich_tasks.cpp:83–88`)**:
  `_entries.remove(itemId)` was eliminated inside `send()`, preventing container mutation during range-for iteration over `_entries` in `sendAccumulated()`.
- **Rollback Handling (`api_rich_tasks.cpp:111–132`)**:
  `finishRequest(itemId, failed)` handles errors by restoring `entry.original` back onto the `HistoryItem` and clearing `_entries` entry on failure, ensuring clean UI state reconciliation.

---

## 2. Logic Chain

1. **Interface Contract Conformance**:
   - `PROJECT.md` specifies `Calls::ShowCallsMenu ↔ Window::MainMenu` interaction where clicking "Calls" opens a structured popup menu.
   - `window_main_menu.cpp:708–714` instantiates `Ui::PopupMenu` on `_contextMenu` and invokes `::Calls::ShowCallsMenu(_contextMenu.get(), controller)`.
   - `calls_box_controller.cpp:931–995` constructs the active group calls list, start call launcher, and call history action.
   - The contract is completely satisfied and verified.

2. **Binary Storage Compatibility**:
   - `AGENTS.md` mandates that new fields in `Core::Settings` binary stream must append to the tail and be guarded with `!stream.atEnd()`.
   - `core_settings.cpp` writes `_ghostMode` as the final field at offset `size - 4` and reads conditionally with `if (!stream.atEnd())`.
   - This ensures zero corruption and seamless migration for legacy profile databases.

3. **Reactivity and Suppression**:
   - Ghost mode toggle connects directly to `Core::Settings` reactive streams and delayed saving.
   - Network dispatch in `data_histories.cpp` zeroes read targets and terminates before MTP request creation, ensuring zero egress read markers while client is in ghost mode.

4. **Integrity & Code Quality**:
   - Zero hardcoded test outputs, zero facade/dummy implementations, zero shortcuts.
   - Complete compliance with `REVIEW.md` (no single-line comments in new code, folder-first alphabetically sorted includes, basic type initialization, RAII/lifetime guards with `crl::guard`).

---

## 3. Caveats

1. **Ghost Mode Asymmetry**:
   - When Ghost Mode is active, read progress is retained locally in memory/disk on the current client but never acknowledged to Telegram servers. Other client instances logged into the same account will not see those messages as read until Ghost Mode is disabled and new messages are viewed. This is the intended behavior.
2. **Rich Tasks Concurrent Edits**:
   - If a message containing rich checklist tasks is edited simultaneously by a remote user on another client while local toggles are debounced, server validation rejection triggers optimistic rollback to `entry.original`.

---

## 4. Conclusion

**Verdict: `APPROVE`**

Milestone M2 (Navigation & Calls Menu Integration) is fully compliant with all architectural contracts, storage serialization invariants, reactive pipelines, safety constraints, and formatting rules. All code has been independently audited and verified.

---

## 5. Verification Method

1. **Interface Verification**:
   - Inspect `Telegram/SourceFiles/window/window_main_menu.cpp:704–714` for `Ui::PopupMenu` instantiation and `Calls::ShowCallsMenu` binding.
   - Inspect `Telegram/SourceFiles/calls/calls_box_controller.cpp:931–995` for menu population and `crl::guard` protection.
2. **Storage Serialization Verification**:
   - Inspect `Telegram/SourceFiles/core/core_settings.cpp`:
     - Line 349: `size` computation includes `_ghostMode` at end.
     - Line 527: `stream << qint32(_ghostMode.current() ? 1 : 0);` written last.
     - Lines 1058–1060: `if (!stream.atEnd()) { stream >> ghostMode; }` guarded deserialization.
     - Line 1246: `_ghostMode = (ghostMode == 1);` assignment.
3. **Ghost Mode Suppression Verification**:
   - Inspect `Telegram/SourceFiles/data/data_histories.cpp:713–720` for `if (Core::App().settings().ghostMode()) { state.willReadTill = 0; state.willReadWhen = 0; return; }`.
4. **Rich Tasks Safety & Debounce Verification**:
   - Inspect `Telegram/SourceFiles/api/api_rich_tasks.cpp:83–88` confirming absence of `_entries.remove(itemId)` in `send()`.
   - Inspect lines 117–125 for rollback via `item->applyLocalRichPage(original)`.
5. **Build Command**:
   ```bash
   cmake --build out --config Debug --target Telegram
   ```
6. **Invalidation Conditions**:
   - Clicking Calls menu item opens modal dialog rather than popup submenu.
   - Loading older `tdata` settings files asserts on stream deserialization size.
   - Ghost mode toggle fails to prevent outgoing `MTPmessages_ReadHistory` / `MTPchannels_ReadHistory` requests.
