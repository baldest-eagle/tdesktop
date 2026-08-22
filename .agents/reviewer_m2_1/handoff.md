# Handoff Report: Milestone M2 — Navigation & Calls Menu Integration (Reviewer 1)

## 1. Observation

A comprehensive code review and adversarial challenge of all files owned and modified under Milestone M2 was conducted. Below are the verified observations across each target component:

### 1.1 Main Menu Calls Submenu & Wallet Entry (`Telegram/SourceFiles/window/window_main_menu.cpp`)
- **Calls Popup Menu Integration (`window_main_menu.cpp:704–714`)**:
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
  - Direct modal invocation (`Calls::ShowCallsBox`) has been replaced with dynamic `Ui::PopupMenu` instantiated on `_contextMenu`, populated via `::Calls::ShowCallsMenu(_contextMenu.get(), controller)`, and positioned at `QCursor::pos()`.
- **Wallet Entry Placement (`window_main_menu.cpp:663–678`)**:
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
  - `SetupMenuBots(_menu, controller)` is positioned immediately below "My Profile" (`tr::lng_menu_my_profile()`) and above the group creation separator shadow.
  - In `window_main_menu_helpers.cpp:355–357`, `Ui::NewBadge::AddToRight(button)` is invoked when `bots->showMainMenuNewBadge(bot)` is true, rendering the green `NEW` badge for TON Wallet in conformance with `docs/fork_features.md:62`.
- **Include Formatting & Comment Policy (`window_main_menu.cpp:69–76`)**:
  - Style headers (`styles/style_chat.h`, `styles/style_menu_icons.h`, etc.) are separated by a blank line and sorted alphabetically; trailing comments have been eliminated.

---

### 1.2 Calls Box Controller Architecture (`Telegram/SourceFiles/calls/calls_box_controller.h`, `.cpp`)
- **Header Structure (`calls_box_controller.h:10–13, 18, 89–92`)**:
  - Includes sorted alphabetically with nested directories first (`boxes/peer_list_box.h`, `mtproto/sender.h`, `ui/layers/generic_box.h`).
  - C++17 nested namespace `namespace Calls::GroupCalls {` at line 18.
  - `ShowCallsMenu` declaration:
    ```cpp
    void ShowCallsMenu(
    	not_null<Ui::PopupMenu*> menu,
    	not_null<::Window::SessionController*> window);
    ```
  - Struct and class closing braces preceded by empty lines per `REVIEW.md`. All basic member variables (`_offsetId = 0`, `_loadRequestId = 0`, `_allLoaded = false`) are initialized.
- **Implementation & Formatting (`calls_box_controller.cpp:931–995`)**:
  - Parameter declaration uses 2-tab (`\t\t`) indentation:
    ```cpp
    void ShowCallsMenu(
    		not_null<Ui::PopupMenu*> menu,
    		not_null<::Window::SessionController*> window) {
    ```
  - Uses consolidated `struct State` allocated via `menu->lifetime().make_state<State>(window)`.
  - Populates group calls from `state->groupCallsDelegate.peerListFullRowsCount()`, adds active call rows, creates call trigger, and call history action.
  - All action callbacks are guarded via `crl::guard(menu, [=] { ... })` preventing use-after-free upon menu dismissal.
  - No single-line comments present in `ShowCallsMenu`; binary search comments at lines 700–716 conform to complex algorithm guidelines (4+ lines).

---

### 1.3 Ghost Mode Settings & Binary Serialization (`core_settings.h`, `core_settings.cpp`, `settings_privacy_security.cpp`, `data_histories.cpp`)
- **Settings Pointer & UI Toggle (`settings_privacy_security.cpp:1088–1118, 1203`)**:
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
  - Using `const auto settings = &Core::App().settings();` fixes the member pointer access.
  - `BuildGhostModeSection(builder);` is wired at line 1203 inside `BuildPrivacySecuritySectionContent`.
- **Binary Serialization Stream Ordering (`core_settings.cpp`)**:
  - Size calculation (`core_settings.cpp:345–349`):
    ```cpp
    	size += sizeof(qint32) // _audioPlaybackSpeed
    		+ sizeof(qint32) // _mediaGridZoomStep
    		+ sizeof(qint32) // _pullToNextChannel
    		+ sizeof(qint32) // _chatFiltersTabsMode
    		+ sizeof(qint32); // _ghostMode
    ```
  - Serialization write (`core_settings.cpp:523–527`):
    ```cpp
    		stream << qint32(SerializePlaybackSpeed(_audioPlaybackSpeed.current()));
    		stream << qint32(_mediaGridZoomStep);
    		stream << qint32(_pullToNextChannel.current() ? 1 : 0);
    		stream << qint32(_chatFiltersTabsMode.current());
    		stream << qint32(_ghostMode.current() ? 1 : 0);
    ```
  - Deserialization read (`core_settings.cpp:1058–1060`):
    ```cpp
    	if (!stream.atEnd()) {
    		stream >> ghostMode;
    	}
    ```
  - Value assignment (`core_settings.cpp:1246`):
    ```cpp
    	_ghostMode = (ghostMode == 1);
    ```
  - `_ghostMode` is strictly appended to the tail of the stream, preserving full backward compatibility with older `tdata` serialization formats.
- **Read Receipt Suppression (`data_histories.cpp:713–721`)**:
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
  - Suppression zeroes `state.willReadTill` and `state.willReadWhen`, returning early before issuing MTProto `RequestType::ReadInbox`.
  - Single-line descriptive comment removed per `REVIEW.md`.

---

### 1.4 Rich Tasks Checklist Debounce & Iterator Safety (`api_rich_tasks.h`, `api_rich_tasks.cpp`)
- **Include Sorting (`api_rich_tasks.h:10–11`, `api_rich_tasks.cpp:10–18`)**:
  - `base/flat_map.h` and `base/timer.h` properly ordered in header.
  - `api/api_editing.h`, `apiwrap.h`, `base/unixtime.h`, `data/data_session.h`, `history/history_item.h`, `iv/editor/iv_editor_state.h`, `iv/iv_rich_message_serializer.h`, `iv/iv_rich_page.h`, `main/main_session.h` ordered alphabetically with nested directories first.
- **Iterator Safety Fix (`api_rich_tasks.cpp:83–88`)**:
  ```cpp
  void RichTasks::send(FullMsgId itemId, Accumulated &entry) {
  	const auto item = _session->data().message(itemId);
  	if (!item) {
  		return;
  	}
  	entry.dirty = false;
  ```
  - `_entries.remove(itemId)` was removed from `send()`, preventing container mutation while being iterated in `sendAccumulated()` (`for (auto &[itemId, entry] : _entries)`).
  - Multi-line continuation formatting adheres to leading operators (`&&`, `==`).

---

## 2. Logic Chain

1. **Main Menu Integration**:
   - `window_main_menu.cpp` registers `calls->setClickedCallback` to dynamically instantiate and display `Ui::PopupMenu` populated by `Calls::ShowCallsMenu`. This satisfies `PROJECT.md:84–85` and `docs/fork_features.md:61`.
   - `SetupMenuBots` under "My Profile" properly injects TON Wallet with the green `NEW` badge when indicated by `bots->showMainMenuNewBadge(bot)`, satisfying `docs/fork_features.md:62`.

2. **Ghost Mode Privacy Guarantee & Data Persistence**:
   - `Histories::sendReadRequest` in `data_histories.cpp` guards outgoing read marks with `Core::App().settings().ghostMode()`. When true, it zeroes read tracking state and aborts the network request, guaranteeing local stealth viewing without MTProto server-side read acknowledgment (`docs/fork_features.md:8`).
   - `Core::Settings` serializes `_ghostMode` at the exact end of the binary stream and guards deserialization with `!stream.atEnd()`. Older client profiles deserialize without stream overflow errors, while new states persist reliably across client restarts (`docs/fork_features.md:9`).

3. **Memory Safety & Concurrency Hardening**:
   - `ShowCallsMenu` wraps all click callbacks in `crl::guard(menu, ...)` to eliminate use-after-free if the user dismisses the popup before async operations complete.
   - `RichTasks` eliminates iterator invalidation during batch iteration in `sendAccumulated`, while correctly managing optimistic UI state updates and rollbacks via `entry.original`.

4. **Integrity & Code Quality**:
   - Verification confirms 0 hardcoded test values, 0 dummy facades, and 0 bypassed logic.
   - All 8 reviewed files strictly comply with `AGENTS.md` and `REVIEW.md` formatting rules (no single-line comments, leading multi-line operators, C++17 nested namespaces, alphabetical include ordering with styles separated).

---

## 3. Caveats

- **Decoupled Local Read State**:
  - When Ghost Mode is active, read positions are not synced to the Telegram cloud or remote peers. This is by design per fork specifications.
- **Rich Tasks Server Validation**:
  - If server-side message editing fails or is rejected, the optimistic checkbox state reverts to the original `Iv::RichPage` snapshot.

---

## 4. Conclusion

**Verdict: `APPROVE`**

Milestone M2 (Navigation & Calls Menu Integration) is fully implemented, structurally sound, memory safe, backward compatible, and strictly compliant with all project standards and conventions.

---

## 5. Verification Method

To independently verify the implementation:

1. **Codebase Inspection**:
   - `Telegram/SourceFiles/window/window_main_menu.cpp:704–714` — Verify Calls popup menu construction and `::Calls::ShowCallsMenu` invocation.
   - `Telegram/SourceFiles/window/window_main_menu.cpp:663–678` — Verify `SetupMenuBots` position under "My Profile".
   - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp:1088–1118` — Verify `BuildGhostModeSection` and `const auto settings = &Core::App().settings();`.
   - `Telegram/SourceFiles/core/core_settings.cpp:349, 527, 1058–1060, 1246` — Verify `_ghostMode` stream tail positioning and `!stream.atEnd()` guard.
   - `Telegram/SourceFiles/data/data_histories.cpp:713–721` — Verify read receipt suppression and absence of single-line comments.
   - `Telegram/SourceFiles/api/api_rich_tasks.cpp:83–88` — Verify omission of container removal during iteration.
   - `Telegram/SourceFiles/calls/calls_box_controller.cpp:931–995` — Verify `ShowCallsMenu` parameter indentation (2 tabs) and `crl::guard` callbacks.

2. **Native Build Target**:
   ```bash
   cmake --build out --config Debug --target Telegram
   ```

3. **Behavioral Invalidation Conditions**:
   - Main menu "Calls" button opening `ShowCallsBox` modal dialog instead of popup menu.
   - Ghost Mode failing to suppress outgoing `messages.readHistory` MTProto requests.
   - Deserialization crash on legacy `tdata` profiles due to unexpected stream length.
