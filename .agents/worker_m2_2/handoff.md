# Handoff Report: Milestone M2 — Navigation & Calls Menu Integration (Worker 2)

## 1. Observation

### 1.1 Calls Popup Menu & Wallet Integration (`Telegram/SourceFiles/window/window_main_menu.cpp`)
- **Calls Popup Menu Wiring (lines 703–713)**:
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
  - Replaced direct modal `Calls::ShowCallsBox(controller);` call with dynamic `Ui::PopupMenu` instantiated with `st::popupMenuWithIcons` and populated via `::Calls::ShowCallsMenu(_contextMenu.get(), controller)`.
- **Wallet Entry Placement (lines 662–678)**:
  ```cpp
  		_menu->add(
  			CreateButtonWithIcon(
  				_menu,
  				tr::lng_menu_my_profile(),
  				st::mainMenuButton,
  				{ &st::menuIconProfile })
  		)->setClickedCallback([=] {
  			controller->showSection(
  				Info::Stories::Make(controller->session().user()));
  		});

  		SetupMenuBots(_menu, controller);

  		_menu->add(
  			object_ptr<Ui::PlainShadow>(_menu),
  			{ 0, st::mainMenuSkip, 0, st::mainMenuSkip });
  ```
  - `SetupMenuBots` is positioned directly below "My Profile" (`tr::lng_menu_my_profile()`) and attaches TON Wallet with the green `NEW` badge (`Ui::NewBadge::AddToRight(button)` using `st::windowBgActive`) matching `docs/fork_features.md:62`.
- **Include Formatting (lines 69–75)**:
  ```cpp
  #include "window/window_session_controller.h"

  #include "styles/style_chat.h"
  #include "styles/style_menu_icons.h"
  #include "styles/style_settings.h"
  #include "styles/style_window.h"
  #include "styles/style_window_main_menu.h"
  ```
  - Style headers separated by a blank line and trailing comment (`// popupMenuExpandedSeparator`) removed.

---

### 1.2 Ghost Mode Settings & Binary Serialization (`core_settings.cpp`, `settings_privacy_security.cpp`, `data_histories.cpp`)
- **Settings Pointer Fix (`Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp:1089`)**:
  ```cpp
  void BuildGhostModeSection(SectionBuilder &builder) {
  	const auto settings = &Core::App().settings();

  	builder.addSkip();
  	builder.addSubsectionTitle({
  		.id = u"privacy/ghost_mode"_q,
  		.title = tr::lng_settings_ghost_mode(),
  		.keywords = { u"ghost"_q, u"mode"_q, u"read"_q, u"receipts"_q },
  	});

  	const auto toggle = builder.addButton({
  		.id = u"privacy/ghost_mode_toggle"_q,
  		.title = tr::lng_settings_ghost_mode(),
  		.st = &st::settingsButtonNoIcon,
  		.toggled = settings->ghostModeValue(),
  		.keywords = { u"ghost"_q, u"mode"_q, u"read"_q, u"receipts"_q },
  	});

  	if (toggle) {
  		toggle->toggledChanges(
  		) | rpl::filter([=](bool toggled) {
  			return toggled != settings->ghostMode();
  		}) | rpl::on_next([=](bool toggled) {
  			settings->setGhostMode(toggled);
  			Core::App().saveSettingsDelayed();
  		}, toggle->lifetime());
  	}

  	builder.addSkip();
  	builder.addDividerText(tr::lng_settings_ghost_mode_about());
  }
  ```
  - Using `const auto settings = &Core::App().settings();` resolves compiler errors with `settings->` and ensures reactive toggles update the singleton application settings.

- **Binary Serialization Stream Ordering (`Telegram/SourceFiles/core/core_settings.cpp`)**:
  - `_ghostMode` is positioned strictly at the end of the serialization stream after `_chatFiltersTabsMode`:
    1. Size calculation (lines 345–350):
       ```cpp
       	size += sizeof(qint32) // _audioPlaybackSpeed
       		+ sizeof(qint32) // _mediaGridZoomStep
       		+ sizeof(qint32) // _pullToNextChannel
       		+ sizeof(qint32) // _chatFiltersTabsMode
       		+ sizeof(qint32); // _ghostMode
       ```
    2. Stream serialization (lines 523–528):
       ```cpp
       		stream << qint32(SerializePlaybackSpeed(_audioPlaybackSpeed.current()));
       		stream << qint32(_mediaGridZoomStep);
       		stream << qint32(_pullToNextChannel.current() ? 1 : 0);
       		stream << qint32(_chatFiltersTabsMode.current());
       		stream << qint32(_ghostMode.current() ? 1 : 0);
       ```
    3. Stream deserialization (lines 1052–1060):
       ```cpp
       	if (!stream.atEnd()) {
       		stream >> pullToNextChannel;
       	}
       	if (!stream.atEnd()) {
       		stream >> chatFiltersTabsMode;
       	}
       	if (!stream.atEnd()) {
       		stream >> ghostMode;
       	}
       ```
    4. Field assignment (line 1246):
       ```cpp
       	_ghostMode = (ghostMode == 1);
       ```
  - Backward compatibility with legacy `tdata` is fully preserved per `AGENTS.md` guidelines.

- **Read Receipt Suppression & Comment Removal (`Telegram/SourceFiles/data/data_histories.cpp:713–722`)**:
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
  - Descriptive single-line comment removed per `REVIEW.md`. Suppression zeroes `willReadTill`/`willReadWhen` and returns early without sending MTProto read marks.

---

### 1.3 Rich Tasks Iterator Safety & Includes (`api_rich_tasks.h` / `api_rich_tasks.cpp`)
- **Include Sorting (`Telegram/SourceFiles/api/api_rich_tasks.h:10–11`)**:
  ```cpp
  #include "base/flat_map.h"
  #include "base/timer.h"
  ```
- **Iterator Invalidation Bug Fix (`Telegram/SourceFiles/api/api_rich_tasks.cpp:83–88`)**:
  ```cpp
  void RichTasks::send(FullMsgId itemId, Accumulated &entry) {
  	const auto item = _session->data().message(itemId);
  	if (!item) {
  		return;
  	}
  	entry.dirty = false;
  ```
  - Removed `_entries.remove(itemId);` within `RichTasks::send` to prevent mutating `_entries` while being iterated by `for (auto &[itemId, entry] : _entries)` in `sendAccumulated()`.

---

### 1.4 Calls Box Controller Cleanups (`calls_box_controller.h` / `calls_box_controller.cpp`)
- **Header (`Telegram/SourceFiles/calls/calls_box_controller.h`)**:
  - Alphabetical includes (lines 10–12: `boxes/`, `mtproto/`, `ui/layers/`).
  - C++17 nested namespace `namespace Calls::GroupCalls {` (line 18).
  - Clean member declarations without single-line comments.
- **Implementation (`Telegram/SourceFiles/calls/calls_box_controller.cpp`)**:
  - Includes fully sorted alphabetically with nested folders first (lines 10–48) and styles separated by a blank line (lines 50–56).
  - Trailing comments removed.
  - `ShowCallsMenu` parameter indentation formatted with 2 tabs (`\t\t`) (lines 930–932).

---

## 2. Logic Chain

1. **Main Menu Calls Popup**:
   - `window_main_menu.cpp` binds `calls->setClickedCallback` to dynamically instantiate `Ui::PopupMenu` on `_contextMenu`, populated by `Calls::ShowCallsMenu(_contextMenu.get(), controller)`, and positioned at `QCursor::pos()`. This satisfies `PROJECT.md:84–85` and `docs/fork_features.md:61`.
2. **Settings Singleton & Serialization Integrity**:
   - `Core::App().settings()` returns a reference to the global `Settings` object. By taking its address `const auto settings = &Core::App().settings();`, member accesses compile and modify the shared singleton instance.
   - Moving `_ghostMode` serialization to the end of the `Core::Settings` binary stream prevents 4-byte stream offsets when loading legacy client configurations, guaranteeing backward compatibility.
3. **Iterator Invalidation Prevention**:
   - `RichTasks::sendAccumulated()` iterates through `_entries` with a range-for loop. Removing `_entries.remove(itemId)` from `send()` prevents container mutation during active iteration, eliminating undefined behavior and heap corruption risks.
4. **Code Quality & Review Conformance**:
   - All single-line descriptive comments banned by `REVIEW.md` were eliminated across all 8 owned files.
   - Include directives follow folder-first alphabetical ordering with style sheets segregated.
   - C++17 nested namespaces are used throughout.

---

## 3. Caveats

- **Ghost Mode Cross-Device State**:
  - When Ghost Mode is active, read states are decoupled locally; messages read on the desktop client will not show as read on mobile devices or to remote peers. This is the intended fork specification.
- **Rich Tasks Rollback**:
  - If a message containing rich tasks fails server validation upon edit, `RichTasks::finishRequest` restores `entry.original` snapshot to roll back the optimistic UI state cleanly.

---

## 4. Conclusion

All Milestone M2 requirements are fully satisfied across all 8 owned files:
1. Calls popup submenu is wired in `window_main_menu.cpp`.
2. TON Wallet entry with green `NEW` badge is verified below "My Profile".
3. Ghost Mode settings pointer is fixed and binary serialization is properly placed at the tail of the stream in `core_settings.cpp`.
4. Rich Tasks iterator safety bug is fixed and includes are sorted.
5. All code conventions in `REVIEW.md` and `AGENTS.md` are strictly met.

---

## 5. Verification Method

1. **Source Inspection**:
   - `Telegram/SourceFiles/window/window_main_menu.cpp`: Verify lines 703–713 for `Ui::PopupMenu` and `ShowCallsMenu`.
   - `Telegram/SourceFiles/calls/calls_box_controller.h`: Verify lines 10–12 includes and line 18 `namespace Calls::GroupCalls`.
   - `Telegram/SourceFiles/calls/calls_box_controller.cpp`: Verify lines 10–56 sorted includes and lines 930–932 two-tab parameter indentation.
   - `Telegram/SourceFiles/core/core_settings.cpp`: Verify lines 349, 527, 1058–1060 for `_ghostMode` at stream tail.
   - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`: Verify line 1089 `const auto settings = &Core::App().settings();`.
   - `Telegram/SourceFiles/data/data_histories.cpp`: Verify line 716 has no descriptive comment and zeroes `willReadTill`/`willReadWhen`.
   - `Telegram/SourceFiles/api/api_rich_tasks.h`: Verify line 10 `#include "base/flat_map.h"`.
   - `Telegram/SourceFiles/api/api_rich_tasks.cpp`: Verify lines 84–88 omit `_entries.remove(itemId)`.
2. **Build Command**:
   ```bash
   cmake --build out --config Debug --target Telegram
   ```
3. **Behavioral Invalidation Conditions**:
   - If clicking "Calls" in the main menu opens `ShowCallsBox` modal dialog instead of the popup menu.
   - If toggling Ghost Mode in Privacy & Security settings crashes or fails to suppress outgoing MTProto read requests.
   - If deserializing existing `tdata` settings causes assertion failure `Ensures(result.size() == size)`.
