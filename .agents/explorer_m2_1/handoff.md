# Handoff Report: Milestone M2 — Navigation & Calls Menu Integration (Explorer 1)

## 1. Observation

### 1.1 Calls Menu Item in Main Menu
- **File**: `Telegram/SourceFiles/window/window_main_menu.cpp`
- **Lines 703–708**:
  ```cpp
  		addAction(
  			tr::lng_menu_calls(),
  			{ &st::menuIconPhone }
  		)->setClickedCallback([=] {
  			::Calls::ShowCallsBox(controller);
  		});
  ```
- **Finding**: Currently, clicking the "Calls" entry in the main menu directly opens the modal `Calls::ShowCallsBox(controller)` dialog instead of displaying a popup menu.

### 1.2 Declaration and Implementation of `Calls::ShowCallsMenu`
- **Header Declaration**: `Telegram/SourceFiles/calls/calls_box_controller.h:88–90`
  ```cpp
  void ShowCallsMenu(
  	not_null<Ui::PopupMenu*> menu,
  	not_null<::Window::SessionController*> window);
  ```
- **Definition**: `Telegram/SourceFiles/calls/calls_box_controller.cpp:930–994`
  ```cpp
  void ShowCallsMenu(
  	not_null<Ui::PopupMenu*> menu,
  	not_null<::Window::SessionController*> window) {
  	struct State {
  		base::unique_qptr<QWidget> dummy;
  		GroupCalls::ListController groupCallsController;
  		PeerListContentDelegateSimple groupCallsDelegate;
  		BoxController callsController;
  		PeerListContentDelegateSimple callsDelegate;

  		State(not_null<::Window::SessionController*> window)
  		: groupCallsController(window)
  		, callsController(window) {
  		}
  	};

  	const auto state = menu->lifetime().make_state<State>(window);

  	state->dummy = base::make_unique_q<QWidget>();

  	const auto groupCallsContent = base::make_unique_q<PeerListContent>(
  		state->dummy.get(),
  		&state->groupCallsController);
  	state->groupCallsDelegate.setContent(groupCallsContent);
  	state->groupCallsController.setDelegate(&state->groupCallsDelegate);

  	menu->addAction(
  		tr::lng_call_box_groupcalls_subtitle(tr::now),
  		nullptr,
  		&st::menuIconGroups);

  	const auto groupCount = state->groupCallsDelegate.peerListFullRowsCount();
  	for (auto i = 0; i < groupCount; ++i) {
  		const auto row = state->groupCallsDelegate.peerListRowAt(i);
  		if (!row) continue;
  		const auto peer = row->peer();
  		if (!peer) continue;
  		menu->addAction(
  			peer->name(),
  			crl::guard(menu, [=] {
  				window->showPeerHistory(
  					peer,
  					::Window::SectionShow::Way::ClearStack);
  			}),
  			&st::menuIconGroups);
  	}

  	menu->addSeparator();

  	menu->addAction(
  		tr::lng_confcall_create_call(tr::now),
  		crl::guard(menu, [=] {
  			window->show(Calls::Group::PrepareCreateCallBox(window, nullptr));
  		}),
  		&st::menuIconGroups);

  	menu->addSeparator();

  	menu->addAction(
  		tr::lng_call_box_title(tr::now),
  		crl::guard(menu, [=] {
  			Calls::ShowCallsBox(window);
  		}),
  		&st::menuIconPhone);
  }
  ```
- **Included Headers in `window_main_menu.cpp`**:
  - `calls/calls_box_controller.h` is already included at line 17.
  - `ui/widgets/popup_menu.h` is already included at line 61.
  - `styles/style_chat.h` (and `styles/style_window.h`) providing `st::popupMenuWithIcons` is already included.
  - `_contextMenu` (`base::unique_qptr<Ui::PopupMenu>`) is an existing member of `Window::MainMenu` (`window_main_menu.h:111`).

### 1.3 Wallet Entry Verification
- **Placement in `window_main_menu.cpp`**:
  - Lines 662–678:
    ```cpp
    	if (!_controller->session().supportMode()) {
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
  - `SetupMenuBots(_menu, controller);` (line 673) is positioned directly below "My Profile" (`tr::lng_menu_my_profile()`) and above the shadow separator / chat creation buttons.
- **Implementation in `window_main_menu_helpers.cpp`**:
  - Lines 278–361:
    ```cpp
    void SetupMenuBots(
    		not_null<Ui::VerticalLayout*> container,
    		not_null<Window::SessionController*> controller) {
    	...
    	for (const auto &bot : bots->attachBots()) {
    		...
    		if (bots->showMainMenuNewBadge(bot)) {
    			Ui::NewBadge::AddToRight(button);
    		}
    	}
    }
    ```
- **Badge Logic in `inline_bots/bot_attach_web_view.cpp:2635–2640`**:
  ```cpp
  bool AttachWebView::showMainMenuNewBadge(
  		const AttachWebViewBot &bot) const {
  	return bot.inMainMenu
  		&& bot.disclaimerRequired
  		&& !disclaimerAccepted(bot);
  }
  ```
- **Badge Rendering in `ui/new_badges.cpp:18–51`**:
  - `AddToRight` creates a badge with string `tr::lng_bot_side_menu_new()` ("NEW") and paints a rounded pill using brush `st::windowBgActive` (the theme's active accent color / green in standard theme) anchored to the right edge of the button.
- **Finding on Wallet Entry**: The Wallet entry (and attach bots in main menu) is already positioned directly below "My Profile" with the green `NEW` badge conforming precisely to `docs/fork_features.md:62`. No code adjustments are needed for the Wallet entry.

---

## 2. Logic Chain

1. **Problem Requirement**:
   `docs/fork_features.md:61` requires: "Replace 'Calls' button with folder/submenu — show calls groups inline instead of opening popup box".
   `PROJECT.md:84–85` and `SCOPE.md:18–19` define the contract: `Calls::ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window)` dynamically populates active calls, start call, and call history entries when the user clicks the Calls menu action.

2. **Analysis of Current State**:
   - `window_main_menu.cpp:707` directly calls `::Calls::ShowCallsBox(controller);` inside the button click callback.
   - `calls_box_controller.h:88` and `calls_box_controller.cpp:930` provide the full implementation of `Calls::ShowCallsMenu`.
   - `window_main_menu.cpp` already has `MainMenu::_contextMenu` (`base::unique_qptr<Ui::PopupMenu>`) to manage menu popups on the main menu, and `st::popupMenuWithIcons` is available.

3. **Proposed Modification**:
   In `Telegram/SourceFiles/window/window_main_menu.cpp`:
   Capture the `calls` button pointer returned from `addAction(...)`, and inside `setClickedCallback`:
   - Construct a new `Ui::PopupMenu` assigned to `_contextMenu` with `calls` as parent and `st::popupMenuWithIcons` style.
   - Call `::Calls::ShowCallsMenu(_contextMenu.get(), controller);`.
   - Call `_contextMenu->popup(QCursor::pos());` to display the menu at the cursor position.

4. **Style Conformance Check**:
   - No single-line comments in code (per `REVIEW.md` and `AGENTS.md`).
   - Use `auto` for type deduction (`const auto calls = ...`).
   - Clean RAII / `unique_qptr` ownership via `_contextMenu`.

---

## 3. Caveats & Risks

1. **Popup Menu Lifetime & Re-clicks**:
   Using `_contextMenu` ensures that if a user clicks the button while an existing menu is active, `_contextMenu = base::make_unique_q<...>` will automatically destroy the previous instance and construct a fresh one, preventing orphaned or duplicate menus.
2. **Empty Calls State**:
   `ShowCallsMenu` handles the case where there are 0 active group calls: `groupCount` will be 0, skipping the loop and cleanly presenting the subtitle, separator, "Create Call", separator, and "Call History" / "Calls".
3. **No Unresolved Symbols**:
   `Calls::ShowCallsMenu` is already defined in `calls_box_controller.cpp` which is built as part of the core Telegram target.

---

## 4. Conclusion & Implementation Instructions for Worker

### Exact Code Change Required

**File**: `Telegram/SourceFiles/window/window_main_menu.cpp`
**Lines**: 703–708

#### Before:
```cpp
		addAction(
			tr::lng_menu_calls(),
			{ &st::menuIconPhone }
		)->setClickedCallback([=] {
			::Calls::ShowCallsBox(controller);
		});
```

#### After:
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

### Wallet Entry Summary
- Located at `window_main_menu.cpp:673` via `SetupMenuBots(_menu, controller);`.
- Positioned directly below "My Profile" (`tr::lng_menu_my_profile()`) and above `Ui::PlainShadow`.
- Green `NEW` badge is rendered via `Ui::NewBadge::AddToRight(button)` using `st::windowBgActive`.
- **Status**: Verified and fully compliant with `docs/fork_features.md:62`. No changes needed.

---

## 5. Verification Method

1. **Source Inspection**:
   - Inspect `Telegram/SourceFiles/window/window_main_menu.cpp` to confirm lines 703–712 instantiate `Ui::PopupMenu` with `st::popupMenuWithIcons`, populate via `::Calls::ShowCallsMenu`, and popup at `QCursor::pos()`.
   - Confirm no single-line comments are added.
2. **Build Verification**:
   - Run compilation command:
     `cmake --build out --config Debug --target Telegram`
   - Verify that `window_main_menu.cpp` compiles without warnings or unresolved symbol errors.
3. **Behavioral Invalidation Conditions**:
   - If clicking "Calls" in the main menu still opens the `ShowCallsBox` dialog instead of the popup menu, the wiring was not applied.
   - If the popup menu fails to show "Start Call" (`lng_confcall_create_call`) and "Calls" history (`lng_call_box_title`), verify `ShowCallsMenu` execution.
