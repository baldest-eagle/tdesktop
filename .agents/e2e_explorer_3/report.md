# Technical Specification: Tier 1 E2E Test Suite (Features 38–57) & Test Runner Harness Architecture

**Scope**: Categories 9 to 13 (Main Menu & Navigation, UI Tweaks & Polish, Context Menus & Cross-UI, Backend / Engine, Build & Toolchain) + Complete Test Runner Framework Architecture  
**Author**: Explorer 3 (`e2e_explorer_3`)  
**Target Milestone**: M5 E2E Integration & Verification  
**Authoritative References**: `PROJECT.md`, `docs/fork_features.md`, `TEST_INFRA.md`, `README-WINDOWS-BUILD.md`, `Telegram/CMakeLists.txt`, `Telegram/Resources/langs/lang.strings`

---

## 1. Executive Summary

This document specifies the complete technical and operational design for Tier 1 End-to-End (E2E) testing covering Features 38 through 57 (Categories 9–13) of the Telegram Desktop (`tdesktop`) fork, alongside the full architectural specification for the `tests/e2e/run_all.py` test harness framework.

Following the Opaque-Box, Requirement-Driven methodology established in `TEST_INFRA.md`:
1. **Tier 1 Feature Coverage**: Exactly five (5) distinct, deterministic test cases per feature across 20 features = **100 Tier 1 test cases**. Combined with Explorer 1 (Features 1–15, 75 tests) and Explorer 2 (Features 16–37, 110 tests), the entire 57-feature inventory achieves 100% Tier 1 coverage (**285 test cases**).
2. **Specialized Engine Oracles**: Rigorous state tracking and invariant verification for:
   - **Rich Tasks (Feature 45)**: 1000ms debounce batching, immediate local page application, `EditRichMessage` dispatch, dirty rescheduling, and failure rollback.
   - **SQLite PRAGMA Tuning C1 (Feature 53)**: WAL journaling, 256 MB memory-mapped I/O (`mmap_size`), synchronous NORMAL, 64 MB cache, and fallback handling.
   - **WebRTC Playout Delay & Jitter Clamping A1 (Feature 54)**: Fast accelerate audio draining and 50ms minimum jitter delay in `tgcalls`.
3. **Test Runner Architecture**: A standalone, zero-external-dependency Python test execution harness (`tests/e2e/run_all.py`) supporting modular tier selection, filtering, parallel simulation, structured reporting, and strict exit code semantics (`0` = pass, `1` = fail).

---

## 2. Category 9: Main Menu & Navigation (Features 38–39)

### Feature 38: Calls Submenu in Main Menu
*Source*: `docs/fork_features.md:61`, `PROJECT.md:51`, `window/window_main_menu.cpp:707`, `calls/calls_box_controller.cpp:930`, `calls/calls_box_controller.h:88`

#### TEST-T1-F38-01: Main Menu Calls Action Replaced with Submenu Popup
- **Objective**: Verify that clicking the "Calls" entry in the main menu invokes `Calls::ShowCallsMenu` to display a structured popup submenu instead of immediately opening a plain dialog box.
- **Inputs & Preconditions**:
  - Main menu opened via hamburger button.
  - Active Telegram session running.
  - Zero active group calls in progress.
- **Actions**:
  1. Locate the "Calls" action item in `Window::MainMenu`.
  2. Simulate user click on the Calls action item.
- **Expected Outputs**:
  - `Calls::ShowCallsMenu` is called with the current `Window::SessionController`.
  - A `Ui::PopupMenu` is instantiated and positioned at the menu action origin.
  - Submenu contains header "Group Calls" (`lng_call_box_groupcalls_subtitle`), separator, "Start Call" (`lng_confcall_create_call`), separator, and "Calls" / "Call History" (`lng_call_box_title`).
- **State Verification**:
  - `PopupMenu` child count == 3 items + 2 separators.
  - Main menu remains responsive and closes gracefully upon selection.
- **Mock Requirements**: `UiSimulator` for menu event generation.

#### TEST-T1-F38-02: Dynamic Population of Active Group Calls in Submenu
- **Objective**: Verify that active ongoing group calls are dynamically queried and rendered as actionable rows at the top of the Calls submenu.
- **Inputs & Preconditions**:
  - User is a member of 2 chats with active group calls: Chat A ("Engineering Standup", PeerID: `3001`) and Chat B ("Design Review", PeerID: `3002`).
  - Main menu opened.
- **Actions**:
  1. Click "Calls" item in main menu.
  2. Inspect generated items in the `Calls::ShowCallsMenu` popup.
- **Expected Outputs**:
  - Submenu queries `GroupCalls::ListController` via `state->groupCallsDelegate`.
  - Exactly 2 group call entries appear under the group calls section labeled "Engineering Standup" and "Design Review".
  - Icon for both entries is `&st::menuIconGroups`.
- **State Verification**:
  - Item 0: Header `lng_call_box_groupcalls_subtitle`.
  - Item 1: Peer 3001 ("Engineering Standup").
  - Item 2: Peer 3002 ("Design Review").
  - Item 3: Separator.
  - Item 4: Start Call.
- **Mock Requirements**: `CallSimulator` providing active group call peer list.

#### TEST-T1-F38-03: Active Group Call Item Click Navigation
- **Objective**: Verify that clicking an active group call item from the Calls submenu immediately opens the corresponding chat history.
- **Inputs & Preconditions**:
  - Calls submenu open with active group call for Peer `3001`.
- **Actions**:
  1. Click the submenu action for Peer `3001`.
- **Expected Outputs**:
  - Submenu dismisses.
  - `window->showPeerHistory(peer, Window::SectionShow::Way::ClearStack)` is invoked with Peer `3001`.
  - Active window changes view to Chat A history.
- **State Verification**:
  - Active navigation stack is cleared; current open history item matches Peer `3001`.
- **Mock Requirements**: `UiSimulator` tracking navigation controller history.

#### TEST-T1-F38-04: "Start Call" Action Launches Create Call Dialog
- **Objective**: Verify that selecting the "Start Call" item from the Calls submenu launches the `PrepareCreateCallBox` dialog.
- **Inputs & Preconditions**:
  - Calls submenu open.
- **Actions**:
  1. Click the "Start Call" action (`lng_confcall_create_call`).
- **Expected Outputs**:
  - Submenu closes.
  - `window->show(Calls::Group::PrepareCreateCallBox(window, nullptr))` is invoked.
  - Modal dialog for starting a group call is displayed on screen.
- **State Verification**:
  - Active box on `Window::SessionController` is an instance of `PrepareCreateCallBox`.
- **Mock Requirements**: `UiSimulator` verifying modal box creation.

#### TEST-T1-F38-05: "Call History" Action Opens Standard Calls Box
- **Objective**: Verify that clicking the "Calls" (Call History) entry at the bottom of the submenu opens the complete call history box (`ShowCallsBox`).
- **Inputs & Preconditions**:
  - Calls submenu open.
- **Actions**:
  1. Click the "Calls" history action (`lng_call_box_title`).
- **Expected Outputs**:
  - Submenu closes.
  - `Calls::ShowCallsBox(window)` is invoked.
  - A `Ui::GenericBox` displaying past incoming/outgoing call records is shown.
- **State Verification**:
  - Active layer box contains `Calls::BoxController` list.
- **Mock Requirements**: `UiSimulator` verifying call history box activation.

---

### Feature 39: Wallet Entry with NEW Badge
*Source*: `docs/fork_features.md:62`, `PROJECT.md:52`, `window/window_main_menu.cpp:662-675`

#### TEST-T1-F39-01: Wallet Menu Item Position & Presence Under My Profile
- **Objective**: Verify that the Wallet entry is inserted into the main menu immediately below the "My Profile" button.
- **Inputs & Preconditions**:
  - Standard user account (`supportMode == false`).
  - Open Telegram Main Menu.
- **Actions**:
  1. Enumerate main menu button child widgets in order.
- **Expected Outputs**:
  - First button: "My Profile" (`tr::lng_menu_my_profile()`).
  - Second button: "Wallet" entry with icon `&st::menuIconWallet` and NEW badge.
  - Followed by Bots section, separator, Create Group, Create Channel, etc.
- **State Verification**:
  - Wallet button index == 1 in the non-support main menu action list.
- **Mock Requirements**: `UiSimulator` menu layout inspector.

#### TEST-T1-F39-02: Visual Styling & Green "NEW" Badge Rendering
- **Objective**: Verify that the Wallet menu entry renders a distinct green accent badge containing the text "NEW".
- **Inputs & Preconditions**:
  - Main menu rendered on screen.
- **Actions**:
  1. Inspect the right accessory widget of the Wallet menu button.
  2. Inspect badge background color, text color, and border radius.
- **Expected Outputs**:
  - Badge text equals `"NEW"`.
  - Badge styling uses accent green background with white bold text.
  - Badge does not overlap button text or icon.
- **State Verification**:
  - Badge widget geometry is positioned within the right margin of the `st::mainMenuButton`.
- **Mock Requirements**: `UiSimulator` widget hierarchy validator.

#### TEST-T1-F39-03: Wallet Item Click Navigation
- **Objective**: Verify that clicking the Wallet menu item triggers navigation to the TON Wallet interface / mini-app.
- **Inputs & Preconditions**:
  - Main menu open.
- **Actions**:
  1. Simulate mouse click on the Wallet button.
- **Expected Outputs**:
  - Main menu closes.
  - Wallet navigation handler executes (invoking `controller->showSection(...)` or launching wallet bot/mini-app).
- **State Verification**:
  - Navigation event dispatched; active view switches to Wallet.
- **Mock Requirements**: `UiSimulator` verifying navigation event dispatch.

#### TEST-T1-F39-04: Support Mode Isolation (Wallet Hidden for Support Accounts)
- **Objective**: Verify that when the client is running in support mode (`session().supportMode() == true`), the Wallet menu entry is strictly omitted.
- **Inputs & Preconditions**:
  - Client initialized with a support account (`supportMode = true`).
  - Open Main Menu.
- **Actions**:
  1. Enumerate all actions in `Window::MainMenu`.
- **Expected Outputs**:
  - Support mode branch executes (`_menu` contains Add Contact, Fix chats order, etc.).
  - Wallet menu button is NOT added to `_menu`.
- **State Verification**:
  - No button with icon `&st::menuIconWallet` exists in the widget tree.
- **Mock Requirements**: `UiSimulator` with `supportMode` enabled session.

#### TEST-T1-F39-05: Main Menu Item Order & Separator Integrity
- **Objective**: Verify that the presence of the Wallet entry does not disrupt subsequent standard menu items or separator line positions.
- **Inputs & Preconditions**:
  - Standard user account. Main menu open.
- **Actions**:
  1. Verify the sequential list of action titles: My Profile, Wallet, Bots, [Separator], New Group, New Channel, Contacts, Calls, Saved Messages.
- **Expected Outputs**:
  - All standard buttons exist with valid icons and non-empty click callbacks.
  - Separators have height `st::mainMenuSkip`.
- **State Verification**:
  - Action list matches exact expected sequence without duplicate or missing items.
- **Mock Requirements**: `UiSimulator` sequential action validator.

---

## 3. Category 10: UI Tweaks & Polish (Features 40–44)

### Feature 40: Wide/Grid Obstructing Button Cleanup
*Source*: `docs/fork_features.md:65`, `PROJECT.md:53`, `calls/group/calls_group_panel.cpp:2865-2880`

#### TEST-T1-F40-01: Wide Mode Floating Control Dismissal
- **Objective**: Verify that switching to `PanelMode::Wide` toggles off floating center controls (`_screenShare`, `_message`, `_wideMenu`, `_settings`, `_video`, `_gridModeButton`, `_chatToggle`, `_mute`, `_hangup`, `_controlsBackgroundWide`) to provide an unobstructed video feed.
- **Inputs & Preconditions**:
  - Active group call with 1 video stream in `PanelMode::Narrow`.
- **Actions**:
  1. Trigger layout switch to `PanelMode::Wide`.
  2. Call `updateControlsGeometry()`.
- **Expected Outputs**:
  - `toggle(_screenShare, false)`, `toggle(_message, false)`, `toggle(_wideMenu, false)`, `toggle(_settings, false)`, `toggle(_video, false)`, `toggle(_gridModeButton, false)`, `toggle(_chatToggle, false)`, `toggle(_mute, false)`, `toggle(_hangup, false)` are executed.
  - `_controlsBackgroundWide` is hidden.
- **State Verification**:
  - All 9 floating button widgets have `isVisible() == false`.
- **Mock Requirements**: `CallSimulator` with `calls_group_panel` state inspector.

#### TEST-T1-F40-02: Grid Mode Obstruction-Free Video Tiles
- **Objective**: Verify that in `PanelMode::Grid`, floating center controls remain hidden and do not overlay the multi-tile video canvas.
- **Inputs & Preconditions**:
  - Active group call with 4 video feeds in `PanelMode::Grid`.
- **Actions**:
  1. Inspect visible overlay elements on top of `calls_group_viewport`.
- **Expected Outputs**:
  - Video grid viewport occupies full usable area.
  - No floating on-screen buttons obstruct the video tiles.
- **State Verification**:
  - Video viewport bounding box intersects zero floating control widgets.
- **Mock Requirements**: `CallSimulator` and `GridSolverOracle`.

#### TEST-T1-F40-03: Restoration of Controls on Returning to Narrow Mode
- **Objective**: Verify that transitioning back from Wide/Grid mode to Narrow mode re-enables and correctly positions the standard bottom toolbar buttons.
- **Inputs & Preconditions**:
  - Call panel in `PanelMode::Wide`.
- **Actions**:
  1. Switch mode back to `PanelMode::Narrow`.
  2. Run `updateControlsGeometry()`.
- **Expected Outputs**:
  - Bottom toolbar recalculates layout (e.g. `muteSize`, `buttonSkip`, `fullWidth`).
  - Buttons (`_mute`, `_settings`, `_hangup`, `_video`, etc.) become visible and properly spaced.
- **State Verification**:
  - `_mute->isVisible() == true`, `_hangup->isVisible() == true`.
- **Mock Requirements**: `CallSimulator` geometry calculator.

#### TEST-T1-F40-04: RTMP / Full Stream Title Geometry Refresh
- **Objective**: Verify that when in Wide/Grid mode with RTMP live stream active (`_rtmpFull == true`), `refreshTitleGeometry()` is called to adjust title overlay cleanly.
- **Inputs & Preconditions**:
  - RTMP live stream active; `_rtmpFull = true`.
- **Actions**:
  1. Trigger geometry update in Wide mode.
- **Expected Outputs**:
  - `refreshTitleGeometry()` is invoked.
  - Stream title bar aligns to top margin without overlapping video stream header.
- **State Verification**:
  - Title widget Y position == `0` with standard title margins.
- **Mock Requirements**: `CallSimulator` with RTMP stream fixture.

#### TEST-T1-F40-05: Transient Hover Controls Auto-Hide Behavior
- **Objective**: Verify that hovering over the video area in Wide/Grid mode reveals minimal transient controls which automatically fade out after mouse inactivity.
- **Inputs & Preconditions**:
  - Wide mode active; controls hidden.
- **Actions**:
  1. Move mouse into call panel window.
  2. Wait for hover display duration.
  3. Cease mouse movement for 3000ms.
- **Expected Outputs**:
  - Mouse movement reveals discreet header/corner controls.
  - Inactivity timer fires, fading out controls smoothly to opacity `0.0`.
- **State Verification**:
  - Controls opacity == `0.0` after inactivity timeout.
- **Mock Requirements**: `UiSimulator` virtual timer and mouse mover.

---

### Feature 41: Titlebar Close Wired to Hangup
*Source*: `docs/fork_features.md:66`, `PROJECT.md:54`, `calls/group/calls_group_panel.cpp:690`, `calls/calls_panel.cpp`

#### TEST-T1-F41-01: Participant Window Close Button [X] Hangup
- **Objective**: Verify that clicking the titlebar close [X] button as a standard group call participant immediately terminates the call, sends a leave request, and closes the window.
- **Inputs & Preconditions**:
  - Active group call window open; user is regular participant (non-host).
- **Actions**:
  1. Simulate click on the titlebar close button (`_title->closeButton()`).
- **Expected Outputs**:
  - Window close event is accepted.
  - Outgoing `phone.leaveGroupCall` MTProto request is dispatched.
  - WebRTC media session is stopped.
  - Group call panel widget is scheduled for deletion (`deleteLater()`).
- **State Verification**:
  - `CallSimulator`: `leaveCall` invoked; window is closed.
- **Mock Requirements**: `CallSimulator` and `MtprotoMock`.

#### TEST-T1-F41-02: Host/Admin Close [X] Prompts Confirmation Dialog
- **Objective**: Verify that when the group call owner/admin clicks the close [X] button, a confirmation dialog is presented with options to "End call for everyone" vs "Leave call".
- **Inputs & Preconditions**:
  - Active group call; user is group call owner/admin.
- **Actions**:
  1. Click titlebar close [X] button.
- **Expected Outputs**:
  - Window does NOT immediately close.
  - Confirmation box `lng_group_call_end_sure` is presented with buttons: "End" (destructive), "Leave", and "Cancel".
- **State Verification**:
  - Active box is confirmation dialog; call remains active until user chooses an option.
- **Mock Requirements**: `UiSimulator` dialog inspector.

#### TEST-T1-F41-03: Keyboard Alt+F4 / Window Close Event Interception
- **Objective**: Verify that native OS close triggers (such as `Alt+F4` or OS window manager close) route through the same hangup sequence.
- **Inputs & Preconditions**:
  - Active call panel in focus.
- **Actions**:
  1. Send `QCloseEvent` to the call panel window.
- **Expected Outputs**:
  - `closeEvent(QCloseEvent *e)` intercepts the event.
  - Initiates hangup / leave pipeline.
- **State Verification**:
  - Call state transitions to `CallState::Ended`.
- **Mock Requirements**: `UiSimulator` dispatching `QCloseEvent`.

#### TEST-T1-F41-04: Multi-Monitor Stage Window Close Isolation
- **Objective**: Verify that closing an auxiliary secondary display stage window does NOT hang up the group call, but only tears down the secondary display viewport.
- **Inputs & Preconditions**:
  - Group call running with secondary stage window on Display 2 (`displayIndex = 1`).
- **Actions**:
  1. Click close [X] on the secondary stage window.
- **Expected Outputs**:
  - Secondary stage window closes and is destroyed.
  - Main group call panel remains OPEN and ACTIVE.
  - Pinned feeds on the secondary display are unrouted or migrated to primary grid.
- **State Verification**:
  - `DisplayCoordinator::displayCount()` decrements to 1.
  - Main call status remains `CallStatus::Active`.
- **Mock Requirements**: `DisplayCoordinatorMock`.

#### TEST-T1-F41-05: Fast Close During Connection Handshake
- **Objective**: Verify that closing the window while the call is still in the `Connecting` state safely aborts the handshake without crashing or leaking WebRTC threads.
- **Inputs & Preconditions**:
  - Call initiated; state is `CallState::Connecting`.
- **Actions**:
  1. Immediately click close [X] button.
- **Expected Outputs**:
  - Handshake canceled; WebRTC initialization aborted.
  - Window closes cleanly with zero assertion failures.
- **State Verification**:
  - WebRTC threads joined; resources destroyed safely.
- **Mock Requirements**: `CallSimulator` in connecting state.

---

### Feature 42: Screen Share & Message Toggle Icons
*Source*: `docs/fork_features.md:67`, `PROJECT.md:55`, `calls/calls.style:921-956`, `lib_ui/ui/colors.palette`

#### TEST-T1-F42-01: Screen Share Inactive Icon Style Conformance
- **Objective**: Verify that the screen share toggle button in its inactive state renders the `groupCallShareInner` style with standard call button palette color.
- **Inputs & Preconditions**:
  - Group call active; screen sharing is inactive (`sharing == false`).
- **Actions**:
  1. Inspect `_screenShare` button style descriptor and icon.
- **Expected Outputs**:
  - Style inherits from `groupCallSettingsInner` which inherits from `callButton: IconButton`.
  - Icon resolves to screen share vector graphic with default neutral/white tint.
- **State Verification**:
  - Button state is unchecked; icon matches `calls.style:921`.
- **Mock Requirements**: `UiSimulator` style oracle.

#### TEST-T1-F42-02: Screen Share Active Icon & Accent Color
- **Objective**: Verify that when screen sharing is activated, the button switches to active icon styling with accent background and animated ripple.
- **Inputs & Preconditions**:
  - User starts screen sharing.
- **Actions**:
  1. Observe `_screenShare` button visual state mutation.
- **Expected Outputs**:
  - Button switches to active style (`groupCallVideoInnerActive` or active share descriptor).
  - Background renders active accent color.
- **State Verification**:
  - Button `isChecked() == true`; active icon rendered.
- **Mock Requirements**: `UiSimulator` style inspector.

#### TEST-T1-F42-03: Message Panel Toggle Icon States (Inactive vs Active)
- **Objective**: Verify that the in-call message panel toggle button toggles cleanly between `groupCallMessageInner` and `groupCallMessageInnerActive`.
- **Inputs & Preconditions**:
  - Group call with text chat enabled.
- **Actions**:
  1. Inspect icon when chat panel is hidden (`_chatPanelShown == false`).
  2. Click button to show chat panel (`_chatPanelShown == true`).
- **Expected Outputs**:
  - Inactive state: renders `groupCallMessageInner` icon.
  - Active state: renders `groupCallMessageInnerActive` with filled/highlighted vector icon.
- **State Verification**:
  - Button style updates reactively based on `_chatPanelShown` observable.
- **Mock Requirements**: `UiSimulator` observable style validator.

#### TEST-T1-F42-04: IconButton Base Inheritance & Dimensions
- **Objective**: Verify that `groupCallShareInner`, `groupCallVideoInner`, and `groupCallMessageInner` inherit unified `IconButton` dimensions and padding.
- **Inputs & Preconditions**:
  - Codegen style structs loaded from `calls.style`.
- **Actions**:
  1. Query width, height, and icon center offsets for all call control button style instances.
- **Expected Outputs**:
  - All three button styles share uniform outer bounding dimensions (`st::groupCallButtonSize`).
  - Hitbox and ripple center coordinates are identical.
- **State Verification**:
  - Dimensions match `calls.style` specification exactly.
- **Mock Requirements**: Style parser oracle.

#### TEST-T1-F42-05: Dark/Light Palette Adaptation for Call Control Icons
- **Objective**: Verify that all call control vector icons re-rasterize properly when switching between Dark and Light palette themes without color bleeding.
- **Inputs & Preconditions**:
  - Active call panel rendered.
- **Actions**:
  1. Switch application palette from Light (`palette: day`) to Dark (`palette: night`).
- **Expected Outputs**:
  - Icon colors recalculate using night palette tints.
  - Vectors render crisp edges without halo artifacts.
- **State Verification**:
  - Palette change signal triggers repaint; contrast ratio >= 4.5:1.
- **Mock Requirements**: Palette switch simulator.

---

### Feature 43: Multi-Pin Hover Controls
*Source*: `docs/fork_features.md:68`, `PROJECT.md:56`, `calls/group/calls_group_viewport.cpp:758, 1037-1048`, `calls/group/calls_group_viewport.h:94`

#### TEST-T1-F43-01: Hover Pin Button Reveal on Unpinned Video Tile
- **Objective**: Verify that hovering the mouse cursor over an unpinned video tile reveals a pin button in the tile's header area.
- **Inputs & Preconditions**:
  - Multi-participant call; participant Peer `4001` has active unpinned video tile.
- **Actions**:
  1. Move mouse cursor over the bounding box of Peer `4001`'s video tile.
- **Expected Outputs**:
  - Tile detects hover event (`_selected` or `_mouseInside`).
  - Pin icon button fades in at the top corner of the tile.
- **State Verification**:
  - Hover pin button is visible and clickable.
- **Mock Requirements**: `UiSimulator` mouse hover dispatcher.

#### TEST-T1-F43-02: Clicking Hover Pin Icon Pins Video Tile
- **Objective**: Verify that clicking the hover pin icon on an unpinned video tile immediately adds the endpoint to `_pinnedEndpoints` and assigns a pinned slot.
- **Inputs & Preconditions**:
  - Hover pin icon visible on Peer `4001`'s tile (`endpoint = { 4001, Video }`).
- **Actions**:
  1. Click the pin icon button.
- **Expected Outputs**:
  - `Viewport::togglePin(endpoint, true)` is invoked.
  - `endpoint` is appended to `_pinnedEndpoints`.
  - `_pinnedSlots[endpoint]` is set to the new pin index.
  - `updateTilesGeometry()` recalculates layout with the tile in the featured pinned section.
- **State Verification**:
  - `Viewport::isPinned(endpoint) == true`.
- **Mock Requirements**: `GridSolverOracle` verifying pinned slot allocation.

#### TEST-T1-F43-03: Hover State on Already-Pinned Video Tile
- **Objective**: Verify that hovering over an already-pinned video tile displays an "unpin" icon state.
- **Inputs & Preconditions**:
  - Participant Peer `4001` is pinned (`isPinned == true`).
- **Actions**:
  1. Hover over Peer `4001`'s pinned video tile.
- **Expected Outputs**:
  - Hover icon renders in the "unpin / active pin" visual state.
- **State Verification**:
  - Icon indicates unpin action.
- **Mock Requirements**: `UiSimulator` tile inspector.

#### TEST-T1-F43-04: Clicking Hover Icon on Pinned Tile Unpins Feed
- **Objective**: Verify that clicking the hover icon on a pinned tile removes it from pinned feeds and re-flows remaining tiles.
- **Inputs & Preconditions**:
  - Peer `4001` is pinned; hover icon clicked.
- **Actions**:
  1. Simulate click on the unpin hover button.
- **Expected Outputs**:
  - `Viewport::togglePin(endpoint, false)` is invoked.
  - `endpoint` is erased from `_pinnedEndpoints` and `_pinnedSlots`.
  - Tile re-enters the standard auto-flowing grid.
- **State Verification**:
  - `Viewport::isPinned(endpoint) == false`.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F43-05: Mouse Leave Cleanly Hides Hover Controls
- **Objective**: Verify that moving the mouse cursor outside the tile bounding box immediately hides the pin controls to avoid video obstruction.
- **Inputs & Preconditions**:
  - Mouse currently hovering over tile with pin icon visible.
- **Actions**:
  1. Move mouse outside tile bounding box.
- **Expected Outputs**:
  - Tile receives `leaveEvent`.
  - Hover pin button fades out to hidden.
- **State Verification**:
  - Pin icon visibility == `false`.
- **Mock Requirements**: `UiSimulator` event dispatcher.

---

### Feature 44: Window-Level Ctrl+Shift+T Key Handler
*Source*: `docs/fork_features.md:69`, `PROJECT.md:57`, `calls/group/calls_group_panel.cpp:427-436`, `calls/group/calls_group_floating_overlay.h`

#### TEST-T1-F44-01: Ctrl+Shift+T Keypress Opens Floating Overlay
- **Objective**: Verify that pressing `Ctrl+Shift+T` within the call panel window when the floating overlay is hidden calls `_floatingOverlay->toggle()` and shows the overlay.
- **Inputs & Preconditions**:
  - Active call panel window has keyboard focus.
  - `_floatingOverlay` is instantiated and currently hidden.
- **Actions**:
  1. Dispatch `QKeyEvent(QEvent::KeyPress, Qt::Key_T, Qt::ControlModifier | Qt::ShiftModifier)`.
- **Expected Outputs**:
  - Event filter in `calls_group_panel.cpp:427-436` catches the event.
  - `_floatingOverlay->toggle()` is called.
  - Overlay becomes visible on screen.
- **State Verification**:
  - `_floatingOverlay->isHidden() == false`.
- **Mock Requirements**: `UiSimulator` key event dispatcher.

#### TEST-T1-F44-02: Ctrl+Shift+T Keypress Hides Visible Floating Overlay
- **Objective**: Verify that pressing `Ctrl+Shift+T` when the floating overlay is visible toggles it off.
- **Inputs & Preconditions**:
  - Floating overlay is currently visible.
  - Call panel window in focus.
- **Actions**:
  1. Press `Ctrl+Shift+T`.
- **Expected Outputs**:
  - `_floatingOverlay->toggle()` hides the overlay window.
- **State Verification**:
  - `_floatingOverlay->isHidden() == true`.
- **Mock Requirements**: `UiSimulator`.

#### TEST-T1-F44-03: Event Filter Cancellation (No Key Bleed)
- **Objective**: Verify that the window event filter returns `base::EventFilterResult::Cancel` upon handling `Ctrl+Shift+T`, preventing child widgets from receiving the raw key events.
- **Inputs & Preconditions**:
  - Call panel with active child widgets.
- **Actions**:
  1. Dispatch `Ctrl+Shift+T` key event.
- **Expected Outputs**:
  - Result of event filter is `base::EventFilterResult::Cancel`.
  - Event is marked as accepted and does NOT propagate to child widgets or insert text.
- **State Verification**:
  - No text entered into any input field.
- **Mock Requirements**: `UiSimulator` event filter tester.

#### TEST-T1-F44-04: Null Floating Overlay Safe No-Op
- **Objective**: Verify that pressing `Ctrl+Shift+T` when `_floatingOverlay` is null (e.g. before full initialization) executes safely without crashing.
- **Inputs & Preconditions**:
  - Call panel initialized with `_floatingOverlay = nullptr`.
- **Actions**:
  1. Send `Ctrl+Shift+T` key press.
- **Expected Outputs**:
  - Null check `if (_floatingOverlay)` evaluates to false.
  - Function returns `Cancel` without dereferencing a null pointer.
- **State Verification**:
  - Zero crashes; system stable.
- **Mock Requirements**: `UiSimulator`.

#### TEST-T1-F44-05: Focus Isolation (Plain Typing Does Not Trigger Toggle)
- **Objective**: Verify that typing standard letters (e.g. 'T', 'Shift+T', 'Ctrl+T') without the exact `Ctrl+Shift+T` modifier combination does NOT toggle the overlay.
- **Inputs & Preconditions**:
  - Chat input field focused in call panel.
- **Actions**:
  1. Type 'T' (`Key_T`, no modifiers).
  2. Type 'Shift+T' (`Key_T`, `ShiftModifier`).
  3. Type 'Ctrl+T' (`Key_T`, `ControlModifier`).
- **Expected Outputs**:
  - None of these key events trigger `_floatingOverlay->toggle()`.
  - Characters are passed through to the text editor.
- **State Verification**:
  - Overlay visibility state remains unchanged throughout.
- **Mock Requirements**: `UiSimulator` text input test.

---

## 4. Category 11: Context Menus & Cross-UI (Features 45–48)

### Feature 45: Rich Tasks (Checklist Items)
*Source*: `docs/fork_features.md:72`, `PROJECT.md:58`, `api/api_rich_tasks.h:30-58`, `api/api_rich_tasks.cpp:20-136`

#### TEST-T1-F45-01: Immediate Local Checklist State Mutation
- **Objective**: Verify that toggling a rich task checklist item via `Api::RichTasks::toggle` immediately updates local `Iv::RichPage` representation and renders the checkbox state change in UI.
- **Inputs & Preconditions**:
  - Message `FullMsgId(10, 501)` contains a rich markdown checklist with item `[ ] Buy domain`.
  - Message edit is allowed (`togglingAllowed` == true).
- **Actions**:
  1. User clicks the checkbox for item 0 (`source`).
  2. `Api::RichTasks::toggle(item, source)` is invoked.
- **Expected Outputs**:
  - `state.toggleTaskState(source)` flips item state to checked (`[x]`).
  - `item->applyLocalRichPage(std::move(page))` applies the mutated page locally.
  - UI repaints checkbox with checkmark immediately.
- **State Verification**:
  - Local `item->richPage()` reflects checked state.
  - `_entries[itemId].dirty == true`.
- **Mock Requirements**: `MtprotoMock` and Rich Tasks state oracle.

#### TEST-T1-F45-02: 1000ms Debounce Timer Batching
- **Objective**: Verify that multiple rapid task toggles on the same message within the 1000ms window (`kSendDelay = 1000ms`) coalesce into a single upstream `EditRichMessage` RPC call.
- **Inputs & Preconditions**:
  - Message `501` has 3 checklist items.
- **Actions**:
  1. At t=0ms, toggle item 0.
  2. At t=300ms, toggle item 1.
  3. At t=600ms, toggle item 2.
  4. Advance virtual time past t=1600ms.
- **Expected Outputs**:
  - `_sendTimer` triggers `sendAccumulated()` once at t=1600ms.
  - Exactly ONE `EditRichMessage` RPC is dispatched containing all 3 modified checkbox states.
- **State Verification**:
  - `MtprotoMock`: `messages.editMessage` call count == 1.
  - Serialized rich page in RPC payload matches final 3-item state.
- **Mock Requirements**: `MtprotoMock` with virtual clock control.

#### TEST-T1-F45-03: Network RPC Failure Rollback to Original State
- **Objective**: Verify that if the server rejects `EditRichMessage` with an RPC error (e.g. `MESSAGE_NOT_MODIFIED` or network disconnect), `RichTasks::finishRequest` rolls back the local page to `entry.original`.
- **Inputs & Preconditions**:
  - Message `501` initially had item 0 unchecked.
  - User toggled item 0 to checked; `EditRichMessage` dispatched.
- **Actions**:
  1. `MtprotoMock` returns RPC error `RPC_CALL_FAIL`.
  2. `finishRequest(itemId, true /* failed */)` is triggered.
- **Expected Outputs**:
  - `entry.original` is retrieved from `_entries`.
  - `item->applyLocalRichPage(original)` restores the original unchecked rich page.
  - Entry is erased from `_entries`.
  - UI reverts checkbox to unchecked.
- **State Verification**:
  - `item->richPage()` matches pre-toggle state.
- **Mock Requirements**: `MtprotoMock` injecting RPC failure response.

#### TEST-T1-F45-04: Edit Permission Enforcement (`togglingAllowed`)
- **Objective**: Verify that `togglingAllowed` returns `false` and suppresses toggle attempts if the message edit window has expired or the rich page is a partial preview.
- **Inputs & Preconditions**:
  - Case A: Message sent > 48 hours ago (outside edit allowance window).
  - Case B: Message has `richPage->part == true`.
- **Actions**:
  1. Invoke `Api::RichTasks::toggle` for Case A.
  2. Invoke `Api::RichTasks::toggle` for Case B.
- **Expected Outputs**:
  - `togglingAllowed(item)` returns `false` in both cases.
  - No local state mutation occurs; no debounce timer is scheduled.
- **State Verification**:
  - `_entries` map remains empty.
- **Mock Requirements**: Rich Tasks oracle with mocked timestamps.

#### TEST-T1-F45-05: Concurrent Edit Dirty Rescheduling
- **Objective**: Verify that if a user toggles an item while a previous `EditRichMessage` request is already in-flight (`requestId != 0`), the entry is marked `dirty` and a new edit is dispatched upon request completion.
- **Inputs & Preconditions**:
  - Item toggled; `requestId = 1001` in flight.
- **Actions**:
  1. User toggles a second checkbox on the same message while `requestId = 1001` is pending.
  2. Complete `requestId = 1001` successfully.
- **Expected Outputs**:
  - Second toggle sets `entry.dirty = true` and updates local page.
  - `finishRequest(itemId, false)` sees `entry.dirty == true`.
  - Reschedules `sendAccumulated()` to flush the latest state.
- **State Verification**:
  - Total RPCs dispatched == 2; final server state reflects all toggles.
- **Mock Requirements**: `MtprotoMock` in-flight RPC coordinator.

---

### Feature 46: Cross-UI Pin to Grid Actions
*Source*: `docs/fork_features.md:73`, `PROJECT.md:59`, `history/view/history_view_context_menu.cpp`, `calls/group/calls_group_menu.cpp`, `lang.strings:6463`

#### TEST-T1-F46-01: Context Menu "Pin to grid" Action Presence on Active Video Stream
- **Objective**: Verify that right-clicking any participant or video thumbnail across history view or call sidebars injects the `lng_group_call_context_pin_to_grid` ("Pin to grid") menu action.
- **Inputs & Preconditions**:
  - Group call active; participant Peer `4002` is transmitting video.
- **Actions**:
  1. Right click on Peer `4002`'s video stream or participant row.
  2. Inspect popup context menu actions.
- **Expected Outputs**:
  - Context menu contains item labeled "Pin to grid" (`lng_group_call_context_pin_to_grid`).
  - Item icon is pin icon.
- **State Verification**:
  - Action is enabled and visible.
- **Mock Requirements**: `UiSimulator` context menu inspector.

#### TEST-T1-F46-02: Executing "Pin to grid" Updates Viewport Pinned Feeds
- **Objective**: Verify that clicking "Pin to grid" from a context menu invokes the pin allocator and adds the endpoint to the active viewport.
- **Inputs & Preconditions**:
  - Context menu open with "Pin to grid" action for Peer `4002`.
- **Actions**:
  1. Click "Pin to grid".
- **Expected Outputs**:
  - Context menu dismisses.
  - `Viewport::togglePin({ 4002, Video }, true)` is called.
  - Viewport layout updates, placing Peer `4002` in a featured pinned slot.
- **State Verification**:
  - `Viewport::isPinned({ 4002, Video }) == true`.
- **Mock Requirements**: `CallSimulator` and `GridSolverOracle`.

#### TEST-T1-F46-03: Context Menu Suppression for Audio-Only Participants
- **Objective**: Verify that right-clicking a participant who is not transmitting video or screencast does NOT display "Pin to grid".
- **Inputs & Preconditions**:
  - Participant Peer `4003` is audio-only (no video tracks).
- **Actions**:
  1. Right click Peer `4003` row.
- **Expected Outputs**:
  - Context menu contains standard audio actions (Mute, Change Volume, etc.).
  - "Pin to grid" action is omitted.
- **State Verification**:
  - No action with key `lng_group_call_context_pin_to_grid` present.
- **Mock Requirements**: `UiSimulator`.

#### TEST-T1-F46-04: Context Menu Dynamic Toggle to "Unpin from grid"
- **Objective**: Verify that for an already-pinned participant, the context menu displays "Unpin from grid" (or `lng_group_call_context_unpin_camera` / unpin action).
- **Inputs & Preconditions**:
  - Peer `4002` is currently pinned.
- **Actions**:
  1. Right click on Peer `4002`'s tile.
- **Expected Outputs**:
  - Context menu displays "Unpin from grid" instead of "Pin to grid".
  - Clicking it unpins the participant.
- **State Verification**:
  - Pinned state toggled to `false`.
- **Mock Requirements**: `UiSimulator`.

#### TEST-T1-F46-05: In-Chat Video Message Attachment Pin to Grid
- **Objective**: Verify that right-clicking a live stream message or active call banner in the text chat history provides the "Pin to grid" option.
- **Inputs & Preconditions**:
  - Group call active in background; user viewing group chat history.
- **Actions**:
  1. Right click the group call status bar in chat history.
- **Expected Outputs**:
  - Context menu presents direct call actions including Pin to Grid for active streams.
- **State Verification**:
  - Pin action routes properly to background call controller.
- **Mock Requirements**: `UiSimulator` history context menu tester.

---

### Feature 47: Screen Target Pinning Prompt
*Source*: `docs/fork_features.md:74`, `PROJECT.md:60`, `calls/group/calls_group_display_coordinator.cpp:216`, `calls/group/calls_group_menu.cpp`

#### TEST-T1-F47-01: Single-Monitor Environment Bypasses Target Selection
- **Objective**: Verify that on systems with only 1 display (`displayCount() == 1`), triggering a pin action bypasses the screen target dialog and pins directly to the primary window.
- **Inputs & Preconditions**:
  - `QGuiApplication::screens().size() == 1`.
  - Group call active.
- **Actions**:
  1. User selects "Pin to Screen" for participant video.
- **Expected Outputs**:
  - No screen prompt dialog is displayed.
  - Video feed is pinned immediately to primary viewport (`displayIndex = 0`).
- **State Verification**:
  - Pin applied to Display 0; zero modal prompts spawned.
- **Mock Requirements**: `DisplayCoordinatorMock` with 1 virtual screen.

#### TEST-T1-F47-02: Multi-Monitor Pin Triggers Target Selection Dialog
- **Objective**: Verify that when 2 or more monitors are connected (`displayCount() >= 2`), triggering a pin action launches the Screen Target Pinning Prompt modal dialog.
- **Inputs & Preconditions**:
  - System configured with 2 displays: Primary Screen (Display 0) and Stage Screen (Display 1).
- **Actions**:
  1. Select "Pin to Screen" on a video feed.
- **Expected Outputs**:
  - Modal prompt appears with choices: "Screen 1 (Primary)" and "Screen 2 (Stage Window)".
- **State Verification**:
  - Modal dialog active on screen; awaits user selection.
- **Mock Requirements**: `DisplayCoordinatorMock` with 2 virtual screens.

#### TEST-T1-F47-03: Routing Feed to Screen 1 (Primary Display)
- **Objective**: Verify that selecting "Screen 1" routes the pinned feed to the primary window viewport and leaves secondary screens unaffected.
- **Inputs & Preconditions**:
  - Screen target prompt displayed.
- **Actions**:
  1. Click "Screen 1".
- **Expected Outputs**:
  - Dialog dismisses.
  - `DisplayCoordinator::addVideoTrack` routes feed to `displayIndex = 0`.
  - Primary viewport pins the tile.
- **State Verification**:
  - `DisplayCoordinator::isPinned(0, endpoint) == true`.
  - `DisplayCoordinator::isPinned(1, endpoint) == false`.
- **Mock Requirements**: `DisplayCoordinatorMock`.

#### TEST-T1-F47-04: Routing Feed to Screen 2 (Secondary Stage Window)
- **Objective**: Verify that selecting "Screen 2" routes the pinned feed to the secondary stage window and instantiates the auxiliary viewport if not already created.
- **Inputs & Preconditions**:
  - Screen target prompt displayed.
- **Actions**:
  1. Click "Screen 2".
- **Expected Outputs**:
  - Dialog dismisses.
  - `DisplayCoordinator::createDisplayWindow(1, screen2)` is called.
  - Video feed is dispatched to Stage Window viewport on Display 1.
- **State Verification**:
  - `DisplayCoordinator::isPinned(1, endpoint) == true`.
  - Stage window geometry matches Screen 2 bounds.
- **Mock Requirements**: `DisplayCoordinatorMock`.

#### TEST-T1-F47-05: Dialog Cancellation Aborts Pin Without State Mutation
- **Objective**: Verify that clicking Cancel or pressing Escape on the Screen Target prompt dismisses the dialog without pinning the feed to any display.
- **Inputs & Preconditions**:
  - Screen target prompt active.
- **Actions**:
  1. Press Escape.
- **Expected Outputs**:
  - Dialog closes.
  - Feed remains unpinned across all displays.
- **State Verification**:
  - Pinned lists for Display 0 and Display 1 remain unmodified.
- **Mock Requirements**: `DisplayCoordinatorMock`.

---

### Feature 48: Stream Thumbnail Unpin Action Dialog
*Source*: `docs/fork_features.md:75`, `PROJECT.md:61`, `calls/group/calls_group_viewport.cpp:1043`, `calls/group/calls_group_menu.cpp`

#### TEST-T1-F48-01: Thumbnail Context Menu Unpin Action Presence
- **Objective**: Verify that right-clicking any pinned stream thumbnail opens a context menu with an explicit "Unpin / Remove from Screen" action.
- **Inputs & Preconditions**:
  - Stream thumbnail for Peer `4005` is currently pinned.
- **Actions**:
  1. Right click the pinned stream thumbnail.
- **Expected Outputs**:
  - Context menu appears with "Unpin from screen" option.
- **State Verification**:
  - Action item is active and bound to unpin handler.
- **Mock Requirements**: `UiSimulator`.

#### TEST-T1-F48-02: Executing Thumbnail Unpin Updates Layout
- **Objective**: Verify that selecting "Unpin from screen" invokes `togglePin(endpoint, false)` and removes the feed from the featured pinned stage.
- **Inputs & Preconditions**:
  - Peer `4005` is pinned. Context menu open.
- **Actions**:
  1. Click "Unpin from screen".
- **Expected Outputs**:
  - `Viewport::togglePin({ 4005, Video }, false)` executes.
  - Pinned slot map removes entry.
  - Tile moves back into standard auto-scaling grid.
- **State Verification**:
  - `Viewport::isPinned({ 4005, Video }) == false`.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F48-03: Multi-Pin Auto-Scaling Upon Single Feed Removal
- **Objective**: Verify that when 1 of 3 pinned feeds is unpinned via the thumbnail dialog, the remaining 2 pinned feeds smoothly re-scale to a 50/50 split layout.
- **Inputs & Preconditions**:
  - 3 feeds pinned (Peer A, Peer B, Peer C).
- **Actions**:
  1. Unpin Peer C via thumbnail context action.
- **Expected Outputs**:
  - Pinned count reduces from 3 to 2.
  - Viewport auto-scales Peer A and Peer B to occupy equal halves (50/50) of the featured stage.
- **State Verification**:
  - Geometric widths of Peer A and Peer B tiles match within 1 pixel tolerance.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F48-04: Unpinning Last Pinned Feed Restores Active-Speaker Mode
- **Objective**: Verify that unpinning the sole remaining pinned feed cleanly transitions the viewport back to dynamic active-speaker presentation mode.
- **Inputs & Preconditions**:
  - Exactly 1 feed pinned.
- **Actions**:
  1. Unpin the feed.
- **Expected Outputs**:
  - Pinned count becomes 0.
  - Viewport switches auto-flow to track dynamic active speaker audio energy.
- **State Verification**:
  - `_pinnedEndpoints.empty() == true`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F48-05: Secondary Display Thumbnail Unpin Isolation
- **Objective**: Verify that triggering unpin on a secondary stage window thumbnail unpins the feed from the secondary display without affecting primary display pin assignments.
- **Inputs & Preconditions**:
  - Primary display has Peer A pinned; Secondary display has Peer B pinned.
- **Actions**:
  1. Right click Peer B thumbnail on secondary screen and select "Unpin".
- **Expected Outputs**:
  - Peer B is unpinned from secondary display.
  - Peer A remains pinned on primary display.
- **State Verification**:
  - Display 0: Peer A pinned. Display 1: 0 feeds pinned.
- **Mock Requirements**: `DisplayCoordinatorMock`.

---

## 5. Category 12: Backend / Engine (Features 49–54)

### Feature 49: Central Call & State Controller
*Source*: `docs/fork_features.md:78`, `PROJECT.md:62`, `calls/group/calls_group_call.h`, `calls/calls_instance.h`

#### TEST-T1-F49-01: Participant Cache Lifecycle & Event Synchronization
- **Objective**: Verify that the Central Call Controller maintains a consistent internal participant cache as members join, leave, mute, or update video descriptors.
- **Inputs & Preconditions**:
  - Group call active. Central Controller initialized.
- **Actions**:
  1. Dispatch `MTPGroupCallParticipant` join event for Peer `5001`.
  2. Dispatch mute update event for Peer `5001`.
  3. Dispatch leave event for Peer `5001`.
- **Expected Outputs**:
  - On join: Peer `5001` added to controller participant cache; UI notified.
  - On mute: Participant state updated to muted; audio energy meter disabled.
  - On leave: Peer `5001` pruned from cache; any associated video tiles removed.
- **State Verification**:
  - Participant cache size matches active member count at each step.
- **Mock Requirements**: `CallSimulator` event generator.

#### TEST-T1-F49-02: WebRTC Subscription State Reconciliation
- **Objective**: Verify that the controller synchronizes WebRTC media stream subscriptions with active viewport requests, subscribing only to visible feeds.
- **Inputs & Preconditions**:
  - 10 participants streaming video; viewport displays 4 visible tiles.
- **Actions**:
  1. Viewport requests video tracks for visible endpoints (Peers 1–4).
  2. Scroll viewport to reveal Peers 5–8 and hide Peers 1–4.
- **Expected Outputs**:
  - Controller dispatches WebRTC subscription requests for visible feeds.
  - Pauses/unsubscribes video streams for hidden feeds to conserve network bandwidth.
- **State Verification**:
  - Active WebRTC incoming video subscriptions == 4.
- **Mock Requirements**: `CallSimulator` WebRTC layer mock.

#### TEST-T1-F49-03: Network Reconnection & State Recovery
- **Objective**: Verify that upon temporary network disconnection and reconnection, the Central Controller re-establishes WebRTC signaling and restores all pinned slots and UI state.
- **Inputs & Preconditions**:
  - Active call with 2 pinned participants.
- **Actions**:
  1. Simulate network drop (`ConnectionState::Connecting`).
  2. Simulate network recovery (`ConnectionState::Connected`).
- **Expected Outputs**:
  - Controller reconciles call generation ID with server.
  - Re-subscribes to video tracks.
  - Pinned participants remain locked in their assigned slots.
- **State Verification**:
  - Pinned assignments and video renderers resume without user intervention.
- **Mock Requirements**: `CallSimulator` connection drop injector.

#### TEST-T1-F49-04: Permanent Zero-Mic Invariant Enforcement
- **Objective**: Verify that in Listen-Only mode, the Central Controller drops all outgoing audio descriptors and asserts zero microphone capture pipeline initialization.
- **Inputs & Preconditions**:
  - Call started in Listen-Only mode (`audioLockout == true`).
- **Actions**:
  1. Attempt to invoke `unmute()` or trigger spacebar push-to-talk.
- **Expected Outputs**:
  - Controller blocks audio capture initiation.
  - Outgoing audio stream descriptor is null.
  - Zero audio RTP packets dispatched.
- **State Verification**:
  - Outgoing audio packet count == 0.
- **Mock Requirements**: `CallSimulator` audio capture inspector.

#### TEST-T1-F49-05: Clean Call Teardown & Resource Disposal
- **Objective**: Verify that ending a call flushes all subscriptions, resets pin allocators, tears down auxiliary display windows, and safely deallocates media pipelines.
- **Inputs & Preconditions**:
  - Multi-participant call with secondary stage window and multiple pinned feeds.
- **Actions**:
  1. Terminate call via `Controller::finish()`.
- **Expected Outputs**:
  - All WebRTC audio/video channels closed.
  - Secondary windows destroyed.
  - Allocator and cache cleared to empty.
- **State Verification**:
  - Zero dangling pointers; memory footprint returns to baseline.
- **Mock Requirements**: `CallSimulator` teardown verifier.

---

### Feature 50: Simulcast Upscaling Signaling
*Source*: `docs/fork_features.md:79`, `PROJECT.md:63`, `calls/group/calls_group_viewport.cpp:916-940`, `calls/group/calls_group_common.h`

#### TEST-T1-F50-01: Small Video Tile Emits Thumbnail Quality Request
- **Objective**: Verify that when a video tile is rendered at dimensions where `min(width, height) < 240px`, the viewport fires a `VideoQualityRequest` requesting `VideoQuality::Thumbnail`.
- **Inputs & Preconditions**:
  - Video tile for endpoint `{ 6001, Video }`.
- **Actions**:
  1. Call `Viewport::setTileGeometry(tile, QRect(0, 0, 200, 150))`.
- **Expected Outputs**:
  - `min = 150 < kSmall (240)`.
  - `quality` resolved to `VideoQuality::Thumbnail`.
  - `_qualityRequests.fire` emits `VideoQualityRequest{ endpoint, VideoQuality::Thumbnail }`.
- **State Verification**:
  - Emitted request quality == `VideoQuality::Thumbnail`.
- **Mock Requirements**: `GridSolverOracle` and `CallSimulator`.

#### TEST-T1-F50-02: Medium Video Tile Emits Medium Quality Request
- **Objective**: Verify that when a video tile is resized so that `240px <= min(width, height) < 540px`, a `VideoQualityRequest` for `VideoQuality::Medium` is fired.
- **Inputs & Preconditions**:
  - Tile geometry resized.
- **Actions**:
  1. Call `Viewport::setTileGeometry(tile, QRect(0, 0, 480, 360))`.
- **Expected Outputs**:
  - `min = 360 >= kSmall (240)` and `< kMedium (540)`.
  - `quality` resolved to `VideoQuality::Medium`.
  - `_qualityRequests` emits `VideoQualityRequest{ endpoint, VideoQuality::Medium }`.
- **State Verification**:
  - Emitted quality == `VideoQuality::Medium`.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F50-03: Large Tile / Pinned Hero Emits Full Quality Request
- **Objective**: Verify that when a tile is enlarged so that `min(width, height) >= 540px` or is featured in `wide()` presentation mode (`tile == _large`), a request for `VideoQuality::Full` is dispatched.
- **Inputs & Preconditions**:
  - Tile expanded to large dimensions.
- **Actions**:
  1. Call `Viewport::setTileGeometry(tile, QRect(0, 0, 1280, 720))`.
- **Expected Outputs**:
  - `min = 720 >= kMedium (540)`.
  - `quality` resolved to `VideoQuality::Full`.
  - `_qualityRequests` emits `VideoQualityRequest{ endpoint, VideoQuality::Full }`.
- **State Verification**:
  - Emitted quality == `VideoQuality::Full`.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F50-04: Dynamic Viewport Resize Upscaling / Downscaling Lifecycle
- **Objective**: Verify that dynamically resizing the application window across thresholds triggers the appropriate sequence of quality change requests.
- **Inputs & Preconditions**:
  - Viewport with single active video stream.
- **Actions**:
  1. Window size 300x200 (Thumbnail requested).
  2. Resize window to 600x400 (Medium requested).
  3. Resize window to 1920x1080 (Full requested).
  4. Shrink window back to 300x200 (Thumbnail requested).
- **Expected Outputs**:
  - Stream quality transitions: Thumbnail -> Medium -> Full -> Thumbnail.
- **State Verification**:
  - Exactly 4 quality change events logged in sequence.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F50-05: Request Deduplication on Redundant Geometry Updates
- **Objective**: Verify that consecutive calls to `setTileGeometry` with geometries that fall within the same quality tier do NOT emit redundant quality requests (`tile->updateRequestedQuality` returns false).
- **Inputs & Preconditions**:
  - Tile currently requesting `VideoQuality::Medium` (size 400x300).
- **Actions**:
  1. Update tile geometry to 420x320 (`min = 320`, still Medium).
- **Expected Outputs**:
  - `tile->updateRequestedQuality(VideoQuality::Medium)` returns `false`.
  - No new `VideoQualityRequest` is emitted to the event stream.
- **State Verification**:
  - `_qualityRequests` event count remains 0 for this update.
- **Mock Requirements**: `GridSolverOracle`.

---

### Feature 51: Active-Speaker Hysteresis
*Source*: `docs/fork_features.md:80`, `PROJECT.md:64`, `calls/group/calls_group_display_coordinator.h:116-118`, `calls/group/calls_group_display_coordinator.cpp:318`

#### TEST-T1-F51-01: Energy Threshold Gate for Active Speaker Switch
- **Objective**: Verify that a participant must produce audio energy exceeding `_speakerThreshold = 0.05` before being considered for an active speaker promotion.
- **Inputs & Preconditions**:
  - Current active speaker is Peer `5001`.
  - Peer `5002` produces low background noise (energy = `0.02`).
- **Actions**:
  1. Feed audio level updates: `[{ Peer 5001, 0.0 }, { Peer 5002, 0.02 }]`.
- **Expected Outputs**:
  - Peer 5002 energy `0.02 < 0.05` threshold; ignored.
  - Active speaker does NOT switch to Peer 5002.
- **State Verification**:
  - `_activeSpeaker` remains Peer 5001 or transitions to neutral.
- **Mock Requirements**: `CallSimulator` audio energy generator.

#### TEST-T1-F51-02: Transient Energy Dip Hold (Hold Frames Damping)
- **Objective**: Verify that when the current active speaker briefly pauses speech (energy drops to 0.0 for < `_speakerHoldFrames`), the active speaker assignment is held to avoid tile flickering.
- **Inputs & Preconditions**:
  - Peer `5001` speaking (energy = 0.8).
- **Actions**:
  1. Drop Peer `5001` energy to 0.0 for 3 consecutive audio frames (within hold window).
  2. Resume Peer `5001` energy to 0.7.
- **Expected Outputs**:
  - Speaker hold damping maintains Peer `5001` as active speaker throughout the brief pause.
  - Viewport layout remains stable without re-sorting tiles.
- **State Verification**:
  - Zero layout re-sort operations triggered during the pause.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F51-03: Rapid Speaker Alternation Hysteresis
- **Objective**: Verify that rapid alternating speech between two participants (debate scenario) applies damping delay before switching focus, preventing visual flapping.
- **Inputs & Preconditions**:
  - Peer A and Peer B alternating speech every 100ms.
- **Actions**:
  1. Stream alternating energy spikes for 2000ms.
- **Expected Outputs**:
  - Speaker switches occur smoothly with damped transitions rather than every 100ms frame.
- **State Verification**:
  - Speaker switch frequency <= 1 switch per hold interval (>= 500ms).
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F51-04: Secondary Display Active-Speaker Isolation
- **Objective**: Verify that `DisplayCoordinator::updateAudioLevels` is a guarded no-op for secondary display windows, preventing active-speaker auto-stealing on stage screens.
- **Inputs & Preconditions**:
  - Secondary stage window open on Display 1 with explicitly pinned video feeds.
- **Actions**:
  1. Feed high audio energy spikes for non-pinned participant Peer `5003`.
  2. Execute `DisplayCoordinator::updateAudioLevels(levels)`.
- **Expected Outputs**:
  - Secondary display viewport does NOT switch to Peer `5003`.
  - Pinned stage feeds remain completely isolated from audio activity.
- **State Verification**:
  - Display 1 video feeds match explicit pins; zero audio auto-stealing.
- **Mock Requirements**: `DisplayCoordinatorMock`.

#### TEST-T1-F51-05: Complete Silence / Floor Open State
- **Objective**: Verify that when all participants fall silent (energy = 0.0 across all peers) exceeding the hold duration, the active speaker state decays gracefully to a floor-open neutral state without errors.
- **Inputs & Preconditions**:
  - Active speaker active; all audio levels drop to 0.0.
- **Actions**:
  1. Stream 50 consecutive silent audio frames.
- **Expected Outputs**:
  - Hold frames expire.
  - Active speaker indicator clears smoothly.
- **State Verification**:
  - `_activeSpeaker == nullptr` or retains last speaker passively without layout disruption.
- **Mock Requirements**: `CallSimulator`.

---

### Feature 52: TrackPeer & Endpoint Routing Cleanup
*Source*: `docs/fork_features.md:81`, `PROJECT.md:65`, `calls/group/calls_group_common.h`, `calls/group/calls_group_display_coordinator.cpp:295`, commit `0b263e0608`

#### TEST-T1-F52-01: Clean Endpoint-to-Peer Mapping
- **Objective**: Verify that incoming WebRTC video tracks bind uniquely and deterministically to `VideoEndpoint` structures combining `PeerId` and `VideoType` (Camera vs Screen).
- **Inputs & Preconditions**:
  - Participant Peer `5005` starts camera video.
- **Actions**:
  1. Call `addVideoTrack(displayIndex, { 5005, VideoType::Camera }, track, ...)`.
- **Expected Outputs**:
  - `VideoEndpoint` created with `peerId = 5005`, `type = VideoType::Camera`.
  - Track stored in `_tiles` and mapped in `_routedEndpoints[displayIndex]`.
- **State Verification**:
  - `_routedEndpoints[displayIndex].count({ 5005, VideoType::Camera }) == 1`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F52-02: Simultaneous Camera and Screen Share Disambiguation
- **Objective**: Verify that when a participant streams both webcam video and desktop screen sharing simultaneously, two distinct `VideoEndpoint` entities are maintained without collision.
- **Inputs & Preconditions**:
  - Peer `5005` starts camera and screen share.
- **Actions**:
  1. Register `endpointCamera = { 5005, VideoType::Camera }`.
  2. Register `endpointScreen = { 5005, VideoType::Screen }`.
- **Expected Outputs**:
  - Two separate `VideoTile` instances created.
  - Pinning one feed does not inadvertently pin or displace the other feed.
- **State Verification**:
  - Viewport contains 2 distinct endpoints for Peer `5005`.
- **Mock Requirements**: `GridSolverOracle`.

#### TEST-T1-F52-03: Track Removal & Texture Deallocation
- **Objective**: Verify that calling `removeVideoTrack` cleans up the OpenGL texture backing, unbinds the render pipeline, and erases the endpoint from active routing sets (`0b263e0608`).
- **Inputs & Preconditions**:
  - Endpoint `{ 5005, VideoType::Camera }` active with allocated textures.
- **Actions**:
  1. Participant stops camera.
  2. Invoke `removeVideoTrack(displayIndex, endpoint)`.
- **Expected Outputs**:
  - OpenGL texture resources freed.
  - Endpoint erased from `_routedEndpoints[displayIndex]`.
  - Tile removed from `_tiles`.
- **State Verification**:
  - Zero dangling track references; GPU memory freed.
- **Mock Requirements**: `CallSimulator` texture tracker.

#### TEST-T1-F52-04: Multi-Display Track Migration Cleanliness
- **Objective**: Verify that moving a video feed from Primary Screen to Secondary Screen removes the track from Display 0 and registers it on Display 1 without creating duplicate render loops.
- **Inputs & Preconditions**:
  - Endpoint active on Display 0.
- **Actions**:
  1. Migrate endpoint to Display 1.
- **Expected Outputs**:
  - `removeVideoTrack(0, endpoint)` executed on Display 0.
  - `addVideoTrack(1, endpoint, ...)` executed on Display 1.
- **State Verification**:
  - Endpoint exists exclusively in `_routedEndpoints[1]`.
- **Mock Requirements**: `DisplayCoordinatorMock`.

#### TEST-T1-F52-05: Sudden Peer Disconnect Teardown
- **Objective**: Verify that when a participant abruptly disconnects or drops from the call, all associated camera and screen share endpoints across all displays are immediately purged.
- **Inputs & Preconditions**:
  - Peer `5005` streaming camera on Display 0 and screen on Display 1.
- **Actions**:
  1. Peer `5005` drops connection.
  2. Central controller triggers cleanup for Peer `5005`.
- **Expected Outputs**:
  - All endpoints matching `peerId == 5005` are removed across all active displays.
  - Viewports recalculate layout cleanly.
- **State Verification**:
  - Total endpoints for Peer `5005` across all displays == 0.
- **Mock Requirements**: `DisplayCoordinatorMock`.

---

### Feature 53: SQLite PRAGMA Optimizations (C1)
*Source*: `docs/fork_features.md:82`, `PROJECT.md:66, 87`, `ORIGINAL_REQUEST.md:11`, `storage/localstorage.cpp`

#### TEST-T1-F53-01: SQLite Connection Initialization PRAGMA Sequence
- **Objective**: Verify that upon opening the local SQLite storage database, the application executes the complete C1 tuning PRAGMA sequence: WAL mode, 256MB mmap size, synchronous NORMAL, 64MB cache, and MEMORY temp store.
- **Inputs & Preconditions**:
  - Local database open requested on client startup.
- **Actions**:
  1. Initialize storage database connection via storage backend.
  2. Intercept and record all executed PRAGMA SQL statements.
- **Expected Outputs**:
  - The following statements are executed in order:
    1. `PRAGMA journal_mode = WAL;`
    2. `PRAGMA mmap_size = 268435456;` (256 MB)
    3. `PRAGMA synchronous = NORMAL;`
    4. `PRAGMA cache_size = -64000;` (64 MB page cache)
    5. `PRAGMA temp_store = MEMORY;`
- **State Verification**:
  - All 5 PRAGMA statements logged in connection startup sequence.
- **Mock Requirements**: `StorageMock` SQLite PRAGMA interceptor.

#### TEST-T1-F53-02: WAL Journal Mode Verification
- **Objective**: Verify that querying `PRAGMA journal_mode;` after database initialization returns `wal`.
- **Inputs & Preconditions**:
  - Database opened and initialized.
- **Actions**:
  1. Execute query `PRAGMA journal_mode;`.
- **Expected Outputs**:
  - Result row equals `"wal"`.
  - Database supports concurrent non-blocking readers and writer.
- **State Verification**:
  - Journal mode string == `"wal"`.
- **Mock Requirements**: `StorageMock` database engine.

#### TEST-T1-F53-03: Memory-Mapped I/O Size Verification
- **Objective**: Verify that querying `PRAGMA mmap_size;` returns `268435456` bytes (256 MB).
- **Inputs & Preconditions**:
  - Database open.
- **Actions**:
  1. Execute query `PRAGMA mmap_size;`.
- **Expected Outputs**:
  - Result integer equals `268435456`.
- **State Verification**:
  - `mmap_size` value == 268435456.
- **Mock Requirements**: `StorageMock`.

#### TEST-T1-F53-04: Cache Size & Synchronous Mode Settings
- **Objective**: Verify that querying `PRAGMA cache_size;` returns `-64000` and `PRAGMA synchronous;` returns `1` (NORMAL).
- **Inputs & Preconditions**:
  - Database open.
- **Actions**:
  1. Execute query `PRAGMA cache_size;`.
  2. Execute query `PRAGMA synchronous;`.
- **Expected Outputs**:
  - `cache_size` == `-64000` (representing 64,000 KiB).
  - `synchronous` == `1` (representing NORMAL mode).
- **State Verification**:
  - Both PRAGMA values match exact fork specifications.
- **Mock Requirements**: `StorageMock`.

#### TEST-T1-F53-05: Fallback Handling on Unsupported Filesystems
- **Objective**: Verify that if the underlying filesystem does not support WAL mode (e.g. read-only volume or network share lacking shared memory locks), the database open gracefully falls back to `TRUNCATE` or `DELETE` mode without failing startup.
- **Inputs & Preconditions**:
  - SQLite backend configured to simulate WAL initialization failure (`SQLITE_CANTOPEN` / locked `.shm`).
- **Actions**:
  1. Open database connection.
- **Expected Outputs**:
  - WAL attempt fails gracefully; fallback handler executes `PRAGMA journal_mode = TRUNCATE;`.
  - Database connection completes successfully.
- **State Verification**:
  - Database initialized and operational in fallback mode; zero crashes.
- **Mock Requirements**: `StorageMock` with simulated WAL error.

---

### Feature 54: WebRTC Playout Delay & Jitter Clamping (A1)
*Source*: `docs/fork_features.md:83`, `PROJECT.md:67`, `ORIGINAL_REQUEST.md:11`, `tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`, `tgcalls/v2/InstanceV2Impl.cpp:344-345`, `MediaManager.cpp:364`

#### TEST-T1-F54-01: Group Call Audio Channel Fast Accelerate Configuration
- **Objective**: Verify that when creating a voice channel in group calls (`GroupInstanceCustomImpl`), `cricket::AudioOptions::audio_jitter_buffer_fast_accelerate` is set to `true`.
- **Inputs & Preconditions**:
  - Group call initialization in `tgcalls`.
- **Actions**:
  1. Create voice channel via `CreateVoiceChannel`.
  2. Inspect passed `cricket::AudioOptions` struct.
- **Expected Outputs**:
  - `audioOptions.audio_jitter_buffer_fast_accelerate == true`.
- **State Verification**:
  - Boolean flag is explicitly true.
- **Mock Requirements**: `CallSimulator` inspecting `AudioOptions`.

#### TEST-T1-F54-02: Group Call Audio Channel 50ms Minimum Jitter Buffer Delay
- **Objective**: Verify that `cricket::AudioOptions::audio_jitter_buffer_min_delay_ms` is clamped to `50` ms for group call voice channels.
- **Inputs & Preconditions**:
  - Group call voice channel creation.
- **Actions**:
  1. Inspect `audioOptions.audio_jitter_buffer_min_delay_ms` parameter.
- **Expected Outputs**:
  - Value equals `50`.
- **State Verification**:
  - Playout jitter buffer floor is clamped at 50ms.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F54-03: 1-on-1 Call (InstanceV2) Jitter Clamping Parity
- **Objective**: Verify that 1-on-1 calls (`InstanceV2Impl`) configure identical `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50` parameters.
- **Inputs & Preconditions**:
  - 1-on-1 voice call initiated.
- **Actions**:
  1. Inspect `audioOptions` passed to 1-on-1 WebRTC peer connection.
- **Expected Outputs**:
  - `audio_jitter_buffer_fast_accelerate == true`.
  - `audio_jitter_buffer_min_delay_ms == 50`.
- **State Verification**:
  - 1-on-1 and Group calls share identical low-latency jitter buffer configuration.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F54-04: Burst Latency Playout Acceleration (NetEq Fast Drain)
- **Objective**: Verify that when a network latency burst causes audio packets to queue up (simulated 200ms burst), NetEq fast accelerate engages to drain the accumulated buffer back to 50ms.
- **Inputs & Preconditions**:
  - Active audio receive stream with 50ms baseline delay.
- **Actions**:
  1. Inject 200ms burst of delayed audio packets into WebRTC audio receiver.
  2. Observe audio playout clock rate and buffer depth over the next 500ms.
- **Expected Outputs**:
  - Fast acceleration accelerates audio playout rate smoothly without pitch distortion.
  - Playout buffer depth drains back down to ~50ms within 400ms.
- **State Verification**:
  - Steady-state playout latency restored to 50ms.
- **Mock Requirements**: `CallSimulator` NetEq buffer depth simulator.

#### TEST-T1-F54-05: Packet Loss Concealment (PLC) Stability Under Clamped Delay
- **Objective**: Verify that with minimum delay clamped at 50ms, simulated 10% random packet loss engages WebRTC Packet Loss Concealment (PLC) cleanly without buffer underrun clicks.
- **Inputs & Preconditions**:
  - Active voice stream with 10% packet loss injected.
- **Actions**:
  1. Stream 100 audio packets with 10 dropped frames.
- **Expected Outputs**:
  - NetEq PLC synthesizes missing audio frames smoothly.
  - Playout buffer does not crash or underflow catastrophically.
- **State Verification**:
  - Continuous audio output delivered to audio device.
- **Mock Requirements**: `CallSimulator` packet loss injector.

---

## 6. Category 13: Build & Toolchain (Features 55–57)

### Feature 55: Windows Native Build Guide
*Source*: `docs/fork_features.md:86`, `PROJECT.md:68`, `README-WINDOWS-BUILD.md:1-151`

#### TEST-T1-F55-01: Build Guide Document Structure & Prerequisites
- **Objective**: Verify that `README-WINDOWS-BUILD.md` exists and documents all required build prerequisites: Visual Studio 2022, CMake, Ninja, Qt 5.15.2, Python 3.12+, and Git for Windows.
- **Inputs & Preconditions**:
  - Read `README-WINDOWS-BUILD.md`.
- **Actions**:
  1. Validate document sections: Prerequisites, Directory Layout, Build Steps, and Fork-Specific Fixes.
- **Expected Outputs**:
  - All prerequisite tools and version requirements are clearly listed.
- **State Verification**:
  - All 4 primary headings present.
- **Mock Requirements**: File system parser.

#### TEST-T1-F55-02: Single-Threaded Memory Constraint (-j1) Specification
- **Objective**: Verify that the build guide explicitly specifies `-j1` for `cmake --build out --config Debug --target Telegram -j1` and explains PCH memory exhaustion avoidance on Qt resource files (`qrc_telegram.cpp`, `qrc_models.cpp`, `qrc_animations.cpp`).
- **Inputs & Preconditions**:
  - Inspect `README-WINDOWS-BUILD.md` lines 55–61.
- **Actions**:
  1. Check for `-j1` flag in build command.
  2. Check for PCH memory explanation.
- **Expected Outputs**:
  - Command contains `-j1`.
  - Detailed explanation of MSVC compiler heap memory limits on giant `.qrc` source files is present.
- **State Verification**:
  - Text pattern matches exact requirement.
- **Mock Requirements**: Static documentation validator.

#### TEST-T1-F55-03: `prepare.py` Workarounds Documentation
- **Objective**: Verify that the document specifies the MSYS2 PATH prefix fix, `ARCH=x64` for libwebp nmake, and skipping breakpad ATL headers in `prepare.py`.
- **Inputs & Preconditions**:
  - Inspect `README-WINDOWS-BUILD.md` table at line 40.
- **Actions**:
  1. Validate table entries for MSYS2 `find.exe` conflict, libwebp architecture detection, and breakpad ATL requirement.
- **Expected Outputs**:
  - All 3 tweaks documented with clear descriptions.
- **State Verification**:
  - Table contains all 3 entries.
- **Mock Requirements**: Static parser.

#### TEST-T1-F55-04: `CallButton` Codegen Struct Definition Documentation
- **Objective**: Verify that the guide provides the exact `CallButton` struct syntax added to `calls.style` to satisfy `codegen_style.exe`.
- **Inputs & Preconditions**:
  - Inspect `README-WINDOWS-BUILD.md` lines 64–81.
- **Actions**:
  1. Compare documented `CallButton` struct fields with `Telegram/SourceFiles/calls/calls.style`.
- **Expected Outputs**:
  - Fields match: `button: IconButton`, `bg: color`, `bgSize: pixels`, `bgPosition: point`, `angle: double`, `outerRadius: pixels`, `outerBg: color`, `label: FlatLabel`, `cornerButtonPosition: point`, `cornerButtonBorder: pixels`.
- **State Verification**:
  - Field names and types match codebase 100%.
- **Mock Requirements**: Style struct comparison tool.

#### TEST-T1-F55-05: Include Paths & Palette Colors Verification
- **Objective**: Verify that the guide records the include path correction (`ui/controls/call_button.h`) and the `callCancelRipple: #c04646` palette definition.
- **Inputs & Preconditions**:
  - Inspect `README-WINDOWS-BUILD.md` lines 83–94.
- **Actions**:
  1. Check for `ui/controls/call_button.h`.
  2. Check for `#c04646` color code.
- **Expected Outputs**:
  - Both fixes clearly documented and matching repository sources.
- **State Verification**:
  - Accurate references confirmed.
- **Mock Requirements**: Static validator.

---

### Feature 56: CMakeLists.txt Source Synchronization
*Source*: `docs/fork_features.md:87`, `PROJECT.md:69`, `Telegram/CMakeLists.txt:199-200, 418-465`

#### TEST-T1-F56-01: Rich Tasks Source Files Registration
- **Objective**: Verify that `api/api_rich_tasks.cpp` and `api/api_rich_tasks.h` are explicitly listed in `Telegram/CMakeLists.txt`.
- **Inputs & Preconditions**:
  - Open `Telegram/CMakeLists.txt`.
- **Actions**:
  1. Search for `api/api_rich_tasks.cpp` and `api/api_rich_tasks.h`.
- **Expected Outputs**:
  - Both files found under the `api/` source list (lines 199–200).
- **State Verification**:
  - Both file paths are registered in CMake target sources.
- **Mock Requirements**: CMake target parser.

#### TEST-T1-F56-02: Calls Box Controller Source Files Registration
- **Objective**: Verify that `calls/calls_box_controller.cpp` and `calls/calls_box_controller.h` are registered in `Telegram/CMakeLists.txt`.
- **Inputs & Preconditions**:
  - Open `Telegram/CMakeLists.txt`.
- **Actions**:
  1. Search for `calls/calls_box_controller.cpp` and `.h`.
- **Expected Outputs**:
  - Both entries found under `calls/` source list (lines 464–465).
- **State Verification**:
  - Target includes calls box controller.
- **Mock Requirements**: CMake target parser.

#### TEST-T1-F56-03: Display Coordinator Source Files Registration
- **Objective**: Verify that `calls/group/calls_group_display_coordinator.cpp` and `calls_group_display_coordinator.h` are registered in `Telegram/CMakeLists.txt`.
- **Inputs & Preconditions**:
  - Open `Telegram/CMakeLists.txt`.
- **Actions**:
  1. Search for `calls/group/calls_group_display_coordinator.cpp` and `.h`.
- **Expected Outputs**:
  - Both entries present at lines 456–457.
- **State Verification**:
  - Target sources include display coordinator.
- **Mock Requirements**: CMake target parser.

#### TEST-T1-F56-04: Floating Overlay Source Files Registration
- **Objective**: Verify that `calls/group/calls_group_floating_overlay.cpp` and `calls_group_floating_overlay.h` are registered in `Telegram/CMakeLists.txt`.
- **Inputs & Preconditions**:
  - Open `Telegram/CMakeLists.txt`.
- **Actions**:
  1. Search for `calls/group/calls_group_floating_overlay.cpp` and `.h`.
- **Expected Outputs**:
  - Both entries present at lines 458–459.
- **State Verification**:
  - Target sources include floating overlay.
- **Mock Requirements**: CMake target parser.

#### TEST-T1-F56-05: Comprehensive Fork Source Registration Audit
- **Objective**: Verify that every newly added fork source file in `Telegram/SourceFiles/calls/group/` and `Telegram/SourceFiles/api/` exists on disk and is registered in `Telegram/CMakeLists.txt`.
- **Inputs & Preconditions**:
  - Enumerate all `.cpp` and `.h` files in `Telegram/SourceFiles/calls/group/` and `Telegram/SourceFiles/api/`.
- **Actions**:
  1. Match file list against sources listed in `Telegram/CMakeLists.txt`.
- **Expected Outputs**:
  - Zero missing source files; 100% registration parity.
- **State Verification**:
  - Registration discrepancy count == 0.
- **Mock Requirements**: Source-to-CMake audit validator.

---

### Feature 57: Fork Localization Language Keys
*Source*: `docs/fork_features.md:88`, `PROJECT.md:70`, `Telegram/Resources/langs/lang.strings:6463-6464`

#### TEST-T1-F57-01: `lng_group_call_context_pin_to_grid` Key Verification
- **Objective**: Verify that `lng_group_call_context_pin_to_grid` is defined in `Telegram/Resources/langs/lang.strings` with the exact string `"Pin to grid"`.
- **Inputs & Preconditions**:
  - Read `Telegram/Resources/langs/lang.strings`.
- **Actions**:
  1. Locate key `"lng_group_call_context_pin_to_grid"`.
- **Expected Outputs**:
  - Line 6463 contains: `"lng_group_call_context_pin_to_grid" = "Pin to grid";`.
- **State Verification**:
  - Key exists, is properly quoted, and terminates with semicolon.
- **Mock Requirements**: Language pack parser.

#### TEST-T1-F57-02: `lng_group_call_open_chat` Key Verification
- **Objective**: Verify that `lng_group_call_open_chat` is defined in `Telegram/Resources/langs/lang.strings` with the exact string `"Open Chat"`.
- **Inputs & Preconditions**:
  - Read `Telegram/Resources/langs/lang.strings`.
- **Actions**:
  1. Locate key `"lng_group_call_open_chat"`.
- **Expected Outputs**:
  - Line 6464 contains: `"lng_group_call_open_chat" = "Open Chat";`.
- **State Verification**:
  - Key exists and value is `"Open Chat"`.
- **Mock Requirements**: Language pack parser.

#### TEST-T1-F57-03: Ghost Mode Language Keys Consistency
- **Objective**: Verify that Ghost Mode UI localization keys (`lng_settings_ghost_mode`, `lng_settings_ghost_mode_about`) exist or have valid English fallback phrases in the settings UI.
- **Inputs & Preconditions**:
  - Query language provider for ghost mode strings.
- **Actions**:
  1. Request `tr::lng_settings_ghost_mode(tr::now)`.
  2. Request `tr::lng_settings_ghost_mode_about(tr::now)`.
- **Expected Outputs**:
  - Returns non-empty, localized or fallback descriptive strings ("Ghost Mode", "Do not send read receipts...").
- **State Verification**:
  - String lengths > 0; no crash on lookup.
- **Mock Requirements**: Localization oracle.

#### TEST-T1-F57-04: Language Pack Syntax & UTF-8 Encoding Integrity
- **Objective**: Verify that `lang.strings` contains valid UTF-8 without BOM, valid key-value quote pairing, and zero syntax errors across lines 6450–6500.
- **Inputs & Preconditions**:
  - Parse `Telegram/Resources/langs/lang.strings` around fork keys.
- **Actions**:
  1. Run syntax validator checking regex `^"([a-zA-Z0-9_]+)"\s*=\s*"([^"]*)";$`.
- **Expected Outputs**:
  - All keys conform to grammar rules without malformed escapes.
- **State Verification**:
  - Syntax error count == 0.
- **Mock Requirements**: Language pack syntax validator.

#### TEST-T1-F57-05: Missing Key Fallback Resilience
- **Objective**: Verify that if a non-English language pack is missing a fork-specific key, the client gracefully falls back to the default English string without rendering raw key IDs to the user.
- **Inputs & Preconditions**:
  - Active language set to German or Spanish (missing fork key).
- **Actions**:
  1. Request `lng_group_call_context_pin_to_grid`.
- **Expected Outputs**:
  - Fallback mechanism supplies `"Pin to grid"`.
- **State Verification**:
  - Returned string == `"Pin to grid"`.
- **Mock Requirements**: Localization fallback simulator.

---

## 7. Deep-Dive Specification: Rich Tasks State Machine (Feature 45)

```
                       User Clicks Checkbox
                                |
                                v
                   [ RichTasks::toggle() ]
                                |
                    Is togglingAllowed() true?
                   /                          \
                 No                            Yes
                /                                \
          [ Return ]                1. Clone RichPage
                                    2. state.toggleTaskState()
                                    3. item->applyLocalRichPage() (UI flips immediately)
                                    4. _entries[itemId].dirty = true
                                    5. _entries[itemId].scheduled = now
                                    6. _sendTimer.callOnce(1000ms)
                                                 |
                                                 v
                                   [ 1000ms Debounce Expires ]
                                                 |
                                                 v
                                    [ sendAccumulated() ]
                                                 |
                                       Is entry.requestId == 0?
                                      /                        \
                                    No                          Yes
                                   /                             \
                          [ Wait in flight ]            1. entry.dirty = false
                                                        2. EditRichMessage() RPC dispatched
                                                        3. entry.requestId = assigned
                                                                   |
                                                                   v
                                                    [ RPC Response Arrives ]
                                                   /                        \
                                              Success                      Failure
                                             /                              \
                                  Is entry.dirty == true?         1. item->applyLocalRichPage(entry.original)
                                 /                       \           (Rollback UI to original)
                               Yes                        No      2. _entries.erase(itemId)
                              /                            \
              1. entry.scheduled = now              [ _entries.erase(itemId) ]
              2. sendAccumulated() (reschedule)
```

---

## 8. Deep-Dive Specification: SQLite PRAGMA (C1) & WebRTC Jitter (A1) Oracles

### SQLite PRAGMA C1 Verification Oracle
The `StorageMock` or database verification harness intercepts the connection lifecycle and executes runtime validations:

```python
class SQLitePragmaOracle:
    EXPECTED_PRAGMAS = {
        "journal_mode": "wal",
        "mmap_size": 268435456,
        "synchronous": 1,         # NORMAL
        "cache_size": -64000,     # 64 MB
        "temp_store": 2           # MEMORY
    }

    def verify_connection(self, db_cursor):
        results = {}
        for pragma, expected in self.EXPECTED_PRAGMAS.items():
            db_cursor.execute(f"PRAGMA {pragma};")
            row = db_cursor.fetchone()
            actual = row[0] if row else None
            # Handle string case-insensitivity for journal_mode
            if isinstance(actual, str):
                actual = actual.lower()
            if actual != expected:
                raise AssertionError(
                    f"PRAGMA {pragma} mismatch: expected {expected}, got {actual}"
                )
            results[pragma] = actual
        return results
```

### WebRTC Jitter Clamping A1 Verification Oracle
The `CallSimulator` validates audio channel configuration and simulates NetEq buffer acceleration:

```python
class WebRTCJitterOracle:
    EXPECTED_FAST_ACCELERATE = True
    EXPECTED_MIN_DELAY_MS = 50

    def verify_audio_options(self, audio_options):
        assert audio_options.audio_jitter_buffer_fast_accelerate == self.EXPECTED_FAST_ACCELERATE, (
            "audio_jitter_buffer_fast_accelerate must be True"
        )
        assert audio_options.audio_jitter_buffer_min_delay_ms == self.EXPECTED_MIN_DELAY_MS, (
            f"audio_jitter_buffer_min_delay_ms must be {self.EXPECTED_MIN_DELAY_MS}"
        )

    def simulate_burst_drain(self, initial_buffer_ms, burst_ms, elapsed_ms):
        # With fast_accelerate enabled, drain rate is ~1.5x normal playout rate
        total_buffered = initial_buffer_ms + burst_ms
        drain_rate = 1.5  # acceleration factor
        drained = elapsed_ms * (drain_rate - 1.0)
        remaining = max(self.EXPECTED_MIN_DELAY_MS, total_buffered - drained)
        return remaining
```

---

## 9. Complete Architecture for `tests/e2e/run_all.py` Test Harness Framework

### 9.1 Directory Structure & File Inventory
The entire E2E test suite resides under `tests/e2e/` with strict modular separation:

```text
c:\Users\kyleh\tdesktop\tests\e2e\
├── framework/
│   ├── __init__.py                  # Framework exports
│   ├── assertions.py                # Custom assertion library (BBox, RPC, State)
│   ├── mtproto_mock.py              # MTProto RPC interceptor & session simulator
│   ├── storage_mock.py              # Fake tdata binary serializer & SQLite PRAGMA oracle
│   ├── call_simulator.py            # TgCalls WebRTC simulator & AudioOptions verifier
│   ├── grid_solver_oracle.py        # Group call viewport grid solver & layout oracle
│   ├── ui_simulator.py              # Qt event dispatcher, widget hierarchy & menu inspector
│   └── display_mock.py              # QScreen topology manager & multi-monitor router
├── tier1_features/
│   ├── __init__.py
│   ├── test_t1_privacy_network.py   # Features 1-3 (15 tests)
│   ├── test_t1_calls_ui.py          # Features 4-10 (35 tests)
│   ├── test_t1_multi_display.py     # Features 11-15 (25 tests)
│   ├── test_t1_grid_pin.py          # Features 16-24 (45 tests)
│   ├── test_t1_floating_overlay.py  # Features 25-30 (30 tests)
│   ├── test_t1_sidebar_audio.py     # Features 31-37 (35 tests)
│   ├── test_t1_menu_polish.py       # Features 38-44 (35 tests)
│   └── test_t1_context_engine_build.py # Features 45-57 (65 tests)
│                                    # Total Tier 1: 285 tests
├── tier2_boundaries/
│   ├── __init__.py
│   ├── test_t2_privacy_network_boundaries.py
│   ├── test_t2_calls_ui_boundaries.py
│   ├── test_t2_multi_display_boundaries.py
│   ├── test_t2_grid_pin_boundaries.py
│   ├── test_t2_floating_overlay_boundaries.py
│   ├── test_t2_sidebar_audio_boundaries.py
│   ├── test_t2_menu_polish_boundaries.py
│   └── test_t2_context_engine_build_boundaries.py # Total Tier 2: 285 tests
├── tier3_combinations/
│   ├── __init__.py
│   ├── test_t3_call_ui_grid_interactions.py
│   ├── test_t3_multi_display_overlay_interactions.py
│   ├── test_t3_ghost_mode_network_interactions.py
│   └── test_t3_audio_lockout_menu_interactions.py # Total Tier 3: ≥57 tests
├── tier4_scenarios/
│   ├── __init__.py
│   └── test_t4_real_world_scenarios.py             # Total Tier 4: 29 scenarios
└── run_all.py                       # Unified test runner CLI
```

---

### 9.2 `run_all.py` Execution Engine Specification

#### Command-Line Interface (CLI) Arguments
`run_all.py` supports rich flags for developer efficiency and CI automation:

```bash
# Run entire test suite (all 4 tiers: 656+ tests)
py tests/e2e/run_all.py

# Run specific tier
py tests/e2e/run_all.py --tier 1
py tests/e2e/run_all.py --tier 2
py tests/e2e/run_all.py --tier 3
py tests/e2e/run_all.py --tier 4

# Run specific category (1 to 13)
py tests/e2e/run_all.py --category 9
py tests/e2e/run_all.py --category 12

# Run specific feature (1 to 57)
py tests/e2e/run_all.py --feature 45
py tests/e2e/run_all.py --feature 53

# Filter by test name / regex
py tests/e2e/run_all.py --filter "TEST-T1-F45.*"

# Output formats
py tests/e2e/run_all.py --json report.json --junit junit_results.xml

# Execution controls
py tests/e2e/run_all.py --bail        # Stop on first failure
py tests/e2e/run_all.py --verbose     # Print detailed trace per test
py tests/e2e/run_all.py --timeout 30  # Per-test timeout in seconds
```

#### Exit Code Semantics
- **`0` (PASS)**: All discovered test cases executed and passed with zero assertion errors or unhandled exceptions.
- **`1` (FAIL)**: One or more test cases failed assertions, timed out, or encountered unhandled exceptions.

#### Core Runner Architecture (`run_all.py` Design)
```python
import sys
import os
import time
import argparse
import unittest
import importlib
import traceback

class E2ETestRunner:
    def __init__(self, tier=None, category=None, feature=None, filter_pattern=None, bail=False, verbose=False, timeout=30):
        self.tier = tier
        self.category = category
        self.feature = feature
        self.filter_pattern = filter_pattern
        self.bail = bail
        self.verbose = verbose
        self.timeout = timeout
        self.results = []

    def discover_tests(self):
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        
        # Determine test directories based on selected tier
        tiers_to_run = [self.tier] if self.tier else [1, 2, 3, 4]
        base_dir = os.path.dirname(os.path.abspath(__file__))

        tier_folders = {
            1: "tier1_features",
            2: "tier2_boundaries",
            3: "tier3_combinations",
            4: "tier4_scenarios"
        }

        for t in tiers_to_run:
            folder = os.path.join(base_dir, tier_folders[t])
            if os.path.exists(folder):
                tier_suite = loader.discover(folder, pattern="test_*.py")
                suite.addTests(self._filter_tests(tier_suite))
        return suite

    def _filter_tests(self, suite):
        filtered = unittest.TestSuite()
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                filtered.addTests(self._filter_tests(item))
            elif isinstance(item, unittest.TestCase):
                test_id = item.id()
                # Apply regex filter, feature filter, or category filter
                if self._matches_filters(test_id, item):
                    filtered.addTest(item)
        return filtered

    def _matches_filters(self, test_id, test_case):
        if self.feature:
            feature_tag = f"F{int(self.feature):02d}"
            if feature_tag not in test_id:
                return False
        if self.filter_pattern:
            import re
            if not re.search(self.filter_pattern, test_id):
                return False
        return True

    def run(self):
        suite = self.discover_tests()
        total_count = suite.countTestCases()
        print(f"============================================================")
        print(f" Telegram Desktop Fork E2E Test Suite")
        print(f" Discovered: {total_count} test cases")
        print(f"============================================================\n")

        start_time = time.time()
        passed, failed, errors, skipped = 0, 0, 0, 0

        for test in self._iterate_tests(suite):
            test_start = time.time()
            test_name = test.id().split('.')[-1]
            try:
                test.runBare()
                duration = time.time() - test_start
                passed += 1
                if self.verbose:
                    print(f"  [PASS] {test_name} ({duration*1000:.1f}ms)")
            except AssertionError as e:
                duration = time.time() - test_start
                failed += 1
                print(f"  [FAIL] {test_name} ({duration*1000:.1f}ms): {e}")
                if self.bail:
                    break
            except Exception as e:
                duration = time.time() - test_start
                errors += 1
                print(f"  [ERROR] {test_name} ({duration*1000:.1f}ms): {e}")
                if self.bail:
                    break

        total_time = time.time() - start_time
        print(f"\n============================================================")
        print(f" Results: {passed} passed, {failed} failed, {errors} errors, {skipped} skipped")
        print(f" Duration: {total_time:.2f}s")
        print(f"============================================================")

        return 0 if (failed == 0 and errors == 0) else 1

    def _iterate_tests(self, suite):
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                yield from self._iterate_tests(item)
            elif isinstance(item, unittest.TestCase):
                yield item

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram Desktop E2E Test Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Tier to execute")
    parser.add_argument("--category", type=int, help="Category number (1-13)")
    parser.add_argument("--feature", type=int, help="Feature number (1-57)")
    parser.add_argument("--filter", type=str, help="Filter test regex")
    parser.add_argument("--bail", action="store_true", help="Stop on first failure")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--timeout", type=int, default=30, help="Test timeout in seconds")
    args = parser.parse_args()

    runner = E2ETestRunner(
        tier=args.tier,
        category=args.category,
        feature=args.feature,
        filter_pattern=args.filter,
        bail=args.bail,
        verbose=args.verbose,
        timeout=args.timeout
    )
    sys.exit(runner.run())
```

---

## 10. Summary Matrix of Scope (Features 38–57)

| Feature # | Feature Name | Category | Test Count | Key Invariants Verified | Source File |
|---|---|---|:---:|---|---|
| **F38** | Calls Submenu in Main Menu | 9: Main Menu & Navigation | 5 | `ShowCallsMenu`, dynamic active group calls list, Start Call box, Call History box | `window_main_menu.cpp:707`, `calls_box_controller.cpp:930` |
| **F39** | Wallet Entry with NEW Badge | 9: Main Menu & Navigation | 5 | Position under My Profile, green `NEW` badge rendering, support mode suppression | `window_main_menu.cpp:662-675` |
| **F40** | Wide/Grid Obstructing Button Cleanup | 10: UI Tweaks & Polish | 5 | Floating buttons hidden in Wide/Grid mode, narrow mode restoration, transient hover | `calls_group_panel.cpp:2865-2880` |
| **F41** | Titlebar Close Wired to Hangup | 10: UI Tweaks & Polish | 5 | Participant [X] hangup, host confirmation prompt, Alt+F4 interception, stage window isolation | `calls_group_panel.cpp:690`, `calls_panel.cpp` |
| **F42** | Screen Share & Message Toggle Icons | 10: UI Tweaks & Polish | 5 | Inactive vs active vector icon styles, `IconButton` inheritance, dark/light palette tints | `calls.style:921-956`, `colors.palette` |
| **F43** | Multi-Pin Hover Controls | 10: UI Tweaks & Polish | 5 | Hover pin button reveal, click toggling, pin/unpin icon swap, mouse leave cleanup | `calls_group_viewport.cpp:758, 1037-1048` |
| **F44** | Window-Level Ctrl+Shift+T Key Handler | 10: UI Tweaks & Polish | 5 | KeyPress event filter, toggle overlay, event consumption (`Cancel`), input focus safety | `calls_group_panel.cpp:427-436` |
| **F45** | Rich Tasks (Checklist Items) | 11: Context Menus & Cross-UI | 5 | Immediate local rich page mutation, 1000ms debounce batching, RPC failure rollback, dirty reschedule | `api/api_rich_tasks.cpp:20-136` |
| **F46** | Cross-UI Pin to Grid Actions | 11: Context Menus & Cross-UI | 5 | `lng_group_call_context_pin_to_grid` in context menus, video track presence gate | `history_view_context_menu.cpp`, `lang.strings:6463` |
| **F47** | Screen Target Pinning Prompt | 11: Context Menus & Cross-UI | 5 | Single-monitor bypass, multi-monitor dialog prompt, Screen 1 vs Screen 2 routing, cancellation | `calls_group_display_coordinator.cpp:216` |
| **F48** | Stream Thumbnail Unpin Action Dialog | 11: Context Menus & Cross-UI | 5 | Thumbnail unpin context menu, dynamic tile auto-scaling, active-speaker fallback | `calls_group_viewport.cpp:1043` |
| **F49** | Central Call & State Controller | 12: Backend / Engine | 5 | Participant cache sync, WebRTC visible subscriptions, network recovery, zero-mic invariant | `calls_group_call.h`, `calls_instance.h` |
| **F50** | Simulcast Upscaling Signaling | 12: Backend / Engine | 5 | Geometric threshold triggers (240px -> Medium, 540px -> Full), deduplication | `calls_group_viewport.cpp:916-940` |
| **F51** | Active-Speaker Hysteresis | 12: Backend / Engine | 5 | `_speakerThreshold = 0.05`, hold frames pause damping, rapid debate damping, 2nd screen isolation | `calls_group_display_coordinator.h:116-118` |
| **F52** | TrackPeer & Endpoint Routing Cleanup | 12: Backend / Engine | 5 | `VideoEndpoint(PeerId, VideoType)` mapping, simultaneous camera+screen, texture cleanup | `calls_group_common.h`, commit `0b263e0608` |
| **F53** | SQLite PRAGMA Optimizations (C1) | 12: Backend / Engine (C1) | 5 | WAL journaling, `mmap_size = 268435456`, `synchronous = NORMAL`, `cache_size = -64000`, fallback | `PROJECT.md:87`, `storage/localstorage.cpp` |
| **F54** | WebRTC Playout Delay & Jitter Clamping (A1) | 12: Backend / Engine (A1) | 5 | `audio_jitter_buffer_fast_accelerate = true`, `audio_jitter_buffer_min_delay_ms = 50`, NetEq burst drain | `tgcalls/group/GroupInstanceCustomImpl.cpp:1565` |
| **F55** | Windows Native Build Guide | 13: Build & Toolchain | 5 | MSVC 2022 setup, `-j1` memory safety flag, `prepare.py` MSYS2 fix, `CallButton` codegen struct | `README-WINDOWS-BUILD.md:1-151` |
| **F56** | CMakeLists.txt Source Synchronization | 13: Build & Toolchain | 5 | `api_rich_tasks`, `calls_box_controller`, `display_coordinator`, `floating_overlay` registration | `Telegram/CMakeLists.txt:199, 418-465` |
| **F57** | Fork Localization Language Keys | 13: Build & Toolchain | 5 | `lng_group_call_context_pin_to_grid`, `lng_group_call_open_chat`, syntax & quote validation | `Telegram/Resources/langs/lang.strings:6463-6464` |
| **Total** | **20 Features** | **Categories 9–13** | **100 Tests** | **Comprehensive Tier 1 Specification Completed** | |

---

*End of Specification — Prepared by Explorer 3 (`e2e_explorer_3`)*
