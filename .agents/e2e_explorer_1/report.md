# Technical Specification: Tier 1 E2E Test Suite (Features 1–15)
**Scope**: Categories 1 to 4 (Privacy & Ghost Mode, Network & Download, Call UI & Controls, Multi-Display & Routing)  
**Author**: Explorer 1 (`e2e_explorer_1`)  
**Target Milestone**: M5 E2E Integration & Verification  
**Authoritative References**: `PROJECT.md`, `docs/fork_features.md`, `TEST_INFRA.md`  

---

## Executive Summary & Test Framework Overview

This technical specification details the complete Tier 1 end-to-end (E2E) test catalog for Features 1 through 15 of the Telegram Desktop fork. Following the Opaque-Box, Requirement-Driven, and Category-Partition methodology established in `TEST_INFRA.md`, every feature is covered by exactly five (5) distinct, deterministic Tier 1 test cases (total 75 test cases).

### Execution Harness & Architecture
- **Runner**: `py tests/e2e/run_all.py --tier 1`
- **Module Mapping**:
  - `tests/e2e/tier1_features/test_t1_privacy_network.py` (Features 1, 2, 3)
  - `tests/e2e/tier1_features/test_t1_calls_ui.py` (Features 4, 5, 6, 7, 8, 9, 10)
  - `tests/e2e/tier1_features/test_t1_multi_display.py` (Features 11, 12, 13, 14, 15)
- **Framework Support Components**:
  - `MtprotoMock`: In-memory protocol simulator capturing RPC invocations (`MTPmessages_readHistory`, `MTPchannels_readHistory`, chunk download requests `MTPupload_getFile`).
  - `StorageMock`: Manages fake `tdata` settings binary streams and SQLite instances.
  - `CallSimulator`: Injects fake group call descriptors, audio levels, WebRTC tracks, and video frames.
  - `DisplayCoordinatorMock` / `QtScreenMock`: Simulates virtual `QScreen` topologies, geometries, and window hierarchies.

---

## Category 1: Privacy & Ghost Mode (E3)

### Feature 1: Ghost Mode (Decoupled Read Receipts)
*Source*: `docs/fork_features.md:8`, `PROJECT.md:14` (`data_histories.cpp`, `core_settings.h`)

#### TEST-T1-F01-01: Default Disabled State & Normal Read Receipt Transmission
- **Objective**: Verify that when Ghost Mode is disabled (`ghostMode == false`), viewing incoming messages dispatches standard outgoing `MTPmessages_readHistory` RPC requests to the server.
- **Inputs & Preconditions**:
  - Account: Logged-in session with User A.
  - Peer: Private chat with User B (PeerID: `1002`).
  - Message Inbox: 3 unread messages (IDs: `101`, `102`, `103`).
  - Setting: `Core::App().settings().ghostMode() == false`.
- **Actions**:
  1. Open chat history for PeerID `1002`.
  2. Scroll viewport to render message ID `103`.
  3. Trigger history read evaluation timer expiration (`_readRequestsTimer`).
- **Expected Outputs**:
  - `Histories::sendReadRequest` is invoked.
  - An MTProto RPC request `messages.readHistory` with `peer = inputPeerUser(1002)` and `max_id = 103` is sent upstream.
  - `state.sentReadTill` updates to `103`.
- **State Verification**:
  - `MtprotoMock`: Exactly 1 `messages.readHistory` RPC logged.
  - Local UI: Unread badge for Peer `1002` clears to `0`.
- **Mock Requirements**: `MtprotoMock` recording outgoing RPCs; `CallSimulator` inactive.

#### TEST-T1-F01-02: Ghost Mode Enabled - Suppression of Outgoing Read Inbox Receipts
- **Objective**: Verify that enabling Ghost Mode (`ghostMode == true`) intercepts `Histories::sendReadRequest`, resetting pending read state and completely suppressing `messages.readHistory` upstream transmission.
- **Inputs & Preconditions**:
  - Peer: Private chat with User B (PeerID: `1002`).
  - Message Inbox: 5 unread messages (IDs: `201` to `205`).
  - Setting: `Core::App().settings().setGhostMode(true)`.
- **Actions**:
  1. Navigate to chat with PeerID `1002`.
  2. View messages `201` through `205` in the active viewport.
  3. Fire `Histories::sendReadRequest(history, state)`.
- **Expected Outputs**:
  - `state.willReadTill` is reset to `0`.
  - `state.willReadWhen` is reset to `0`.
  - Function returns early before `sendRequest(history, RequestType::ReadInbox, ...)`.
  - Zero outgoing MTProto read requests dispatched.
- **State Verification**:
  - `MtprotoMock`: `messages.readHistory` call count remains `0`.
  - `state.sentReadTill` remains `0`.
- **Mock Requirements**: `MtprotoMock` with assertion on empty RPC log for `ReadInbox`.

#### TEST-T1-F01-03: Local Unread Badge Integrity Under Ghost Mode
- **Objective**: Verify that under Ghost Mode, local scroll tracking and UI display function smoothly while decoupling server state from client view.
- **Inputs & Preconditions**:
  - Peer: Private chat with User C (PeerID: `1003`).
  - Unread Count: `4`.
  - Setting: `ghostMode == true`.
- **Actions**:
  1. Open dialog `1003`.
  2. Read all messages.
  3. Inspect history local state and server-side simulated inbox state.
- **Expected Outputs**:
  - Local message list renders messages with read styling locally.
  - Server-side inbox pointer remains unadvanced.
- **State Verification**:
  - `history->unreadCount()` locally is reconciled for active session display.
  - No `messages.readHistory` packet emitted over MTProto transport.
- **Mock Requirements**: `MtprotoMock` verifying zero network traffic.

#### TEST-T1-F01-04: Channel / Megagroup Read Receipts Suppression
- **Objective**: Verify that Ghost Mode suppresses `channels.readHistory` for broadcast channels and supergroups when reading messages.
- **Inputs & Preconditions**:
  - Channel: Supergroup channel (ChannelID: `2001`).
  - Unread Messages: IDs `501` to `520`.
  - Setting: `ghostMode == true`.
- **Actions**:
  1. Open supergroup `2001`.
  2. Scroll down to bottom message `520`.
  3. Trigger read request dispatch cycle.
- **Expected Outputs**:
  - Outgoing `channels.readHistory` RPC is completely suppressed.
  - `channel->unreadCount()` remains unmutated upstream.
- **State Verification**:
  - `MtprotoMock`: Zero calls to `channels.readHistory` with `channel = inputChannel(2001)`.
- **Mock Requirements**: `MtprotoMock` configured with channel entity fixtures.

#### TEST-T1-F01-05: Dynamic Ghost Mode Toggle Mid-Session
- **Objective**: Verify that toggling Ghost Mode from false to true while unread requests are queued immediately aborts outbound read requests.
- **Inputs & Preconditions**:
  - Peer: Dialog `1004` with 2 unread messages.
  - Setting: Initial `ghostMode == false`.
- **Actions**:
  1. View message in dialog `1004` (queuing read timer).
  2. Before timer fires, invoke `Core::App().settings().setGhostMode(true)`.
  3. Advance event loop to process timer expiration.
- **Expected Outputs**:
  - Timer callback evaluates `ghostMode() == true` in `sendReadRequest`.
  - Request is dropped; `state.willReadTill` reset to `0`.
- **State Verification**:
  - `MtprotoMock`: Zero read RPCs sent.
- **Mock Requirements**: `MtprotoMock` with simulated event loop timer control.

---

### Feature 2: Ghost Mode Settings UI & Persistence
*Source*: `docs/fork_features.md:9`, `PROJECT.md:15` (`core_settings.cpp/.h`, `settings_privacy_security.cpp`)

#### TEST-T1-F02-01: Privacy & Security Settings UI Element Presence
- **Objective**: Verify that the Ghost Mode checkbox/toggle is properly registered and visible in the Privacy and Security settings section.
- **Inputs & Preconditions**:
  - Open Telegram Settings -> Privacy and Security.
- **Actions**:
  1. Construct `Settings::PrivacySecurity` widget.
  2. Inspect child controls for Ghost Mode entry.
- **Expected Outputs**:
  - A checkbox/toggle row titled "Ghost Mode" (or localized equivalent) is instantiated.
  - Initial toggle state reflects `Core::App().settings().ghostMode()`.
- **State Verification**:
  - Toggle widget pointer is non-null and visible in the layout.
- **Mock Requirements**: Qt Widget environment; `StorageMock`.

#### TEST-T1-F02-02: Settings UI Toggle User Interaction & Reactive Update
- **Objective**: Verify that clicking the Ghost Mode toggle in UI immediately mutates `Core::Settings::_ghostMode` and fires `ghostModeChanges()` reactive stream.
- **Inputs & Preconditions**:
  - Settings UI displayed; `ghostMode == false`.
  - Reactive observer subscribed to `Core::App().settings().ghostModeChanges()`.
- **Actions**:
  1. Simulate user click on the Ghost Mode toggle.
- **Expected Outputs**:
  - Toggle UI state changes to checked.
  - `Core::App().settings().ghostMode()` returns `true`.
  - Reactive observer receives `true`.
- **State Verification**:
  - `_ghostMode.current() == true`.
  - UI checkbox state is checked.
- **Mock Requirements**: `rpl::variable` listener harness.

#### TEST-T1-F02-03: Binary Serialization to `tdata` Stream End
- **Objective**: Verify that the Ghost Mode setting is sequentially serialized at the end of the `Core::Settings` binary stream via `QDataStream`.
- **Inputs & Preconditions**:
  - `Core::Settings` initialized with `ghostMode = true`.
  - Binary buffer and `QDataStream` opened for writing.
- **Actions**:
  1. Execute `Core::Settings::writeSettings(stream)`.
  2. Inspect byte output and stream size calculation (`sizeof(qint32)` for `_ghostMode`).
- **Expected Outputs**:
  - Stream writes `qint32(1)` at the designated terminal position.
- **State Verification**:
  - Binary serialization format complies with append-at-end rule in `AGENTS.md`.
- **Mock Requirements**: In-memory `QByteArray` / `QDataStream`.

#### TEST-T1-F02-04: Cold Restart Deserialization and State Recovery
- **Objective**: Verify that restarting the application deserializes the Ghost Mode state from `tdata` accurately.
- **Inputs & Preconditions**:
  - Encoded settings payload containing `ghostMode = 1`.
- **Actions**:
  1. Initialize a new `Core::Settings` instance.
  2. Execute `Core::Settings::readSettings(stream)`.
- **Expected Outputs**:
  - `_ghostMode` field is populated with `true`.
  - `Core::App().settings().ghostMode()` returns `true`.
- **State Verification**:
  - Post-initialization state matches serialized value.
- **Mock Requirements**: `StorageMock` loading serialized binary buffer.

#### TEST-T1-F02-05: Backward Compatibility & atEnd Stream Guard
- **Objective**: Verify that reading a legacy `settings` stream (lacking the `ghostMode` field) does not trigger deserialization errors and defaults `ghostMode` safely to `false`.
- **Inputs & Preconditions**:
  - Legacy serialized binary stream terminating before the `ghostMode` offset (`stream.atEnd() == true`).
- **Actions**:
  1. Instantiate `Core::Settings` and invoke `readSettings(stream)`.
- **Expected Outputs**:
  - `stream.atEnd()` guard prevents read overrun.
  - `_ghostMode` defaults safely to `false`.
- **State Verification**:
  - No crash, assertion failure, or data corruption occurs.
  - `ghostMode() == false`.
- **Mock Requirements**: Truncated legacy binary payload fixture.

---

## Category 2: Network & Download (B1)

### Feature 3: Multi-Connection MTProto Chunk Downloading (16 parallel sessions)
*Source*: `docs/fork_features.md:12`, `PROJECT.md:16` (`download_manager_mtproto.cpp/.h`)

#### TEST-T1-F03-01: Initial Session Pool Allocation
- **Objective**: Verify that `DownloadManagerMtproto` initializes with exactly `kStartSessionsCount = 4` parallel download sessions for a target DC.
- **Inputs & Preconditions**:
  - `DownloadManagerMtproto` instance initialized with `ApiWrap`.
  - Target DC: `MTP::DcId(2)`.
- **Actions**:
  1. Query balance data / session pool for DC 2 upon initial download request.
- **Expected Outputs**:
  - `sessions.size() == 4` (`kStartSessionsCount`).
  - All 4 initial sessions have `requested = 0`, `successes = 0`, `maxWaitedAmount = 8 * 128KB`.
- **State Verification**:
  - Initial session pool size is exactly 4.
- **Mock Requirements**: `MtprotoMock` with simulated DC 2 endpoint.

#### TEST-T1-F03-02: Dynamic Session Pool Scaling to Max Capacity (16 Sessions)
- **Objective**: Verify that sustained successful chunk downloads scale the session pool up to `kMaxSessionsCount = 16`.
- **Inputs & Preconditions**:
  - DC 2 session pool with 4 initial sessions.
  - Large document download enqueued (e.g. 50 MB file, 400 chunks of 128 KB).
- **Actions**:
  1. Simulate consecutive successful chunk completions across all active sessions (`requestSucceeded`).
  2. Advance time past `kRetryAddSessionTimeout` intervals.
- **Expected Outputs**:
  - Sessions vector incrementally expands via `sessions.emplace_back()`.
  - Session expansion halts exactly when `sessions.size() == 16` (`kMaxSessionsCount`).
- **State Verification**:
  - `dc.sessions.size() == 16`.
  - High download parallelism achieved.
- **Mock Requirements**: Fast-forwarded async timer and `MtprotoMock` chunk delivery.

#### TEST-T1-F03-03: Load-Balancing & Chunk Dispatch (`chooseSessionIndex`)
- **Objective**: Verify that `chooseSessionIndex(dcId)` selects the session index with the minimum pending `requested` bytes.
- **Inputs & Preconditions**:
  - DC 2 with 4 sessions having pending loads:
    - Session 0: `256 KB`
    - Session 1: `128 KB`
    - Session 2: `512 KB`
    - Session 3: `0 KB`
- **Actions**:
  1. Call `chooseSessionIndex(MTP::DcId(2))`.
- **Expected Outputs**:
  - Returns session index `3` (least loaded).
- **State Verification**:
  - `changeRequestedAmount(2, 3, 128 * 1024)` updates Session 3 load to `128 KB`.
- **Mock Requirements**: Direct unit harness for `DownloadManagerMtproto`.

#### TEST-T1-F03-04: Timeout & Failure Backoff
- **Objective**: Verify that network timeouts trigger session removal / backoff when errors exceed `kRemoveSessionAfterTimeouts`.
- **Inputs & Preconditions**:
  - DC 2 with 8 active sessions.
- **Actions**:
  1. Inject repeated network timeout errors on session requests.
  2. Trigger timeout threshold logic.
- **Expected Outputs**:
  - `dc.timeouts` incremented.
  - Excess sessions trimmed back down towards `kStartSessionsCount`.
- **State Verification**:
  - Session count decreases; session remove count tracked in `sessionRemoveTimes`.
- **Mock Requirements**: Fault-injecting `MtprotoMock` returning `RPC_CALL_TIMEOUT`.

#### TEST-T1-F03-05: Multi-DC Independent Session Isolation
- **Objective**: Verify that session pools and scaling metrics are managed independently for different DC IDs (e.g. DC 2 vs DC 4).
- **Inputs & Preconditions**:
  - Concurrent downloads from DC 2 (Media) and DC 4 (CDN Document).
- **Actions**:
  1. Scale DC 2 session pool to 12 sessions via successful transfers.
  2. Maintain DC 4 at 4 sessions with low activity.
- **Expected Outputs**:
  - `_balanceData[DcId(2)].sessions.size() == 12`.
  - `_balanceData[DcId(4)].sessions.size() == 4`.
- **State Verification**:
  - No cross-DC session pool pollution or shared state interference.
- **Mock Requirements**: Multi-DC `MtprotoMock`.

---

## Category 3: Call UI & Controls

### Feature 4: Grid Mode Toggle
*Source*: `docs/fork_features.md:15`, `PROJECT.md:17` (`calls_group_panel.cpp`, `calls_group_viewport.cpp`)

#### TEST-T1-F04-01: Grid Mode Button Instantiation & Initial State
- **Objective**: Verify that `_gridModeButton` is instantiated in `Group::Panel`, displayed with `st::groupCallScreenShareSmall`, and initialized to accessible title "Grid View (1x1, 2x2, 3x3)".
- **Inputs & Preconditions**:
  - Active group call with 4 video participants.
- **Actions**:
  1. Initialize `Calls::Group::Panel`.
  2. Inspect `_gridModeButton` properties.
- **Expected Outputs**:
  - `_gridModeButton` is non-null and visible.
  - `accessibleName()` is "Grid View (1x1, 2x2, 3x3)".
  - `_viewport->gridModeValue().current() == false`.
- **State Verification**:
  - Default layout mode is presentation / speaker view.
- **Mock Requirements**: `CallSimulator` hosting 4 video participants.

#### TEST-T1-F04-02: Toggle from Presentation to Grid Mode
- **Objective**: Verify clicking `_gridModeButton` switches viewport to `PanelMode::Grid` and updates `gridModeValue` to `true`.
- **Inputs & Preconditions**:
  - `Group::Panel` in presentation mode (`gridMode == false`).
- **Actions**:
  1. Trigger click on `_gridModeButton`.
- **Expected Outputs**:
  - `_viewport->gridModeValue().current()` transitions to `true`.
  - `_viewport` layout re-solves to symmetrical grid tiles.
- **State Verification**:
  - `_viewport->gridModeValue().current() == true`.
- **Mock Requirements**: `CallSimulator` UI harness.

#### TEST-T1-F04-03: Toggle from Grid Mode to Presentation Mode
- **Objective**: Verify clicking `_gridModeButton` while in grid mode reverts viewport back to presentation mode.
- **Inputs & Preconditions**:
  - `Group::Panel` in grid mode (`gridMode == true`).
- **Actions**:
  1. Trigger click on `_gridModeButton`.
- **Expected Outputs**:
  - `_viewport->gridModeValue().current()` transitions to `false`.
  - Presentation layout with featured speaker restored.
- **State Verification**:
  - `_viewport->gridModeValue().current() == false`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F04-04: Reactive Button Progress State
- **Objective**: Verify `_gridModeButton->setProgress(gridOn ? 1. : 0.)` reacts to `_viewport->gridModeValue().value()`.
- **Inputs & Preconditions**:
  - `Group::Panel` active.
- **Actions**:
  1. Mutate `_viewport->gridModeValue()` programmatically or via shortcut.
- **Expected Outputs**:
  - Button progress property updates to `1.0` when active, `0.0` when inactive.
  - Button color overrides reflect active/inactive palette state.
- **State Verification**:
  - Visual toggle state matches underlying reactive variable.
- **Mock Requirements**: Qt widget test fixture.

#### TEST-T1-F04-05: Multi-Participant Grid Mode Persistence Across Member Join/Leave
- **Objective**: Verify Grid Mode remains active when participants join or leave the group call.
- **Inputs & Preconditions**:
  - Call in Grid Mode with 3 participants.
- **Actions**:
  1. Simulate Participant 4 joining.
  2. Simulate Participant 1 leaving.
- **Expected Outputs**:
  - `gridModeValue()` remains `true` throughout mutations.
  - Viewport recalculates grid layout without resetting to presentation mode.
- **State Verification**:
  - `_viewport->gridModeValue().current() == true`.
- **Mock Requirements**: `CallSimulator` emitting participant join/leave events.

---

### Feature 5: In-Call Chat Panel Slide-Out
*Source*: `docs/fork_features.md:16`, `PROJECT.md:18` (`calls_group_panel.cpp`, `calls_group_messages.cpp`)

#### TEST-T1-F05-01: Chat Panel Toggle Button Creation & Click Event Handling
- **Objective**: Verify chat toggle button in call controls instantiates `_chatPanel` and toggles `_chatPanelShown`.
- **Inputs & Preconditions**:
  - Active group call window. `_chatPanelShown.current() == false`.
- **Actions**:
  1. Click message/chat toggle control button (`_message`).
- **Expected Outputs**:
  - `_chatPanelShown.current()` toggles to `true`.
  - `_chatPanel` is created as a child widget of the call window.
- **State Verification**:
  - `_chatPanel != nullptr` and `_chatPanel->isVisible() == true`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F05-02: Slide-Out Geometry & Rounded Corners Translucent Background
- **Objective**: Verify `_chatPanel` configures `Qt::WA_TranslucentBackground` and paints `Ui::RoundRect` corners with 0.9 opacity.
- **Inputs & Preconditions**:
  - Call window geometry: `1280x720`.
- **Actions**:
  1. Open chat panel slide-out.
  2. Inspect `_chatPanel` attributes and geometry.
- **Expected Outputs**:
  - `testAttribute(Qt::WA_TranslucentBackground)` is `true`.
  - Panel geometry occupies right slide-out region (width ~380px, height matching call window).
- **State Verification**:
  - Translucent background and rounded corner painter invoked.
- **Mock Requirements**: Qt paint event harness.

#### TEST-T1-F05-03: Embedded `MessagesUi` Instantiation and Message Feed Rendering
- **Objective**: Verify `MessagesUi` is instantiated inside `_chatPanel` and binds to `_call->messages()->listValue()`.
- **Inputs & Preconditions**:
  - Group call associated with chat history containing 10 text messages.
- **Actions**:
  1. Open in-call chat slide-out panel.
- **Expected Outputs**:
  - `MessagesUi` instance renders message list inside `_chatPanel`.
  - Input field `_messageField` is visible at the bottom of the panel.
- **State Verification**:
  - Child message items are non-empty and correctly parented.
- **Mock Requirements**: `CallSimulator` with mock message history.

#### TEST-T1-F05-04: Top-Left Close Button (`_chatPanelClose`) Dismissal Action
- **Objective**: Verify clicking `_chatPanelClose` (positioned at `(4, 4)`) hides `_chatPanel` and updates `_chatPanelShown` to `false`.
- **Inputs & Preconditions**:
  - `_chatPanelShown == true`; `_chatPanel` visible.
- **Actions**:
  1. Simulate click on `_chatPanelClose`.
- **Expected Outputs**:
  - `_chatPanelShown.current()` updates to `false`.
  - `_chatPanel->hide()` is invoked.
- **State Verification**:
  - `_chatPanel->isVisible() == false`.
- **Mock Requirements**: Qt mouse click simulation.

#### TEST-T1-F05-05: Concurrent Video Stream Playback During Active Chat Slide-Out
- **Objective**: Verify video feed rendering and audio playback remain uninterrupted while opening and interacting with `_chatPanel`.
- **Inputs & Preconditions**:
  - 2 active video streams rendering in viewport.
- **Actions**:
  1. Toggle chat panel open.
  2. Type and send a chat message.
  3. Verify video viewport frame updates.
- **Expected Outputs**:
  - Video tracks continue receiving and rendering frames.
  - Video viewport geometry adjusts smoothly without dropping WebRTC frames.
- **State Verification**:
  - Frame delivery counter increments continuously.
- **Mock Requirements**: `CallSimulator` with active video track frame pump.

---

### Feature 6: End Call Button & Hover Controls
*Source*: `docs/fork_features.md:17`, `PROJECT.md:19` (`calls_group_panel.cpp`, `calls.style`)

#### TEST-T1-F06-01: Hangup Button Appearance & Discrete Placement
- **Objective**: Verify `_hangup` button is initialized with `st::groupCallHangup` and correctly positioned in the call controls bar.
- **Inputs & Preconditions**:
  - Group call window opened.
- **Actions**:
  1. Inspect `_hangup` widget properties in `Calls::Group::Panel`.
- **Expected Outputs**:
  - `_hangup` is visible, styled with red hangup palette accents, and accessible label set to `lng_group_call_leave`.
- **State Verification**:
  - `_hangup` geometry placed in standard controls container.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F06-02: Hover Detection & Nice Tooltip Activation
- **Objective**: Verify hovering over `_hangup` displays tooltip with `tr::lng_group_call_leave()`.
- **Inputs & Preconditions**:
  - Call window active; controls shown.
- **Actions**:
  1. Simulate mouse enter event on `_hangup`.
- **Expected Outputs**:
  - `showNiceTooltip(_hangup.data(), NiceTooltipType::Normal)` is triggered.
  - Tooltip label text matches `tr::lng_group_call_leave(tr::now)`.
- **State Verification**:
  - Tooltip widget is instantiated and visible.
- **Mock Requirements**: Qt event dispatcher for `QEvent::Enter`.

#### TEST-T1-F06-03: Auto-Hiding Controls Timer on Idle & Hover Re-appearance
- **Objective**: Verify that call controls auto-hide after inactivity timeout (`_hideControlsTimer`) and reappear upon mouse motion.
- **Inputs & Preconditions**:
  - Fullscreen / Wide call panel with mouse stationary.
- **Actions**:
  1. Advance timer to trigger `_hideControlsTimer`.
  2. Verify controls fade out.
  3. Simulate mouse move event over call window.
- **Expected Outputs**:
  - Step 2: `_wideControlsShown` becomes `false`; controls hidden.
  - Step 3: `toggleWideControls(true)` invoked; controls restore visibility.
- **State Verification**:
  - `_hangup->isVisible()` toggles false then true.
- **Mock Requirements**: Qt timer and mouse event simulation.

#### TEST-T1-F06-04: Hangup Click Triggering Complete Call Termination Pipeline
- **Objective**: Verify clicking `_hangup` triggers `endCall()`, disconnecting WebRTC transport and closing the call panel.
- **Inputs & Preconditions**:
  - Active call connected.
- **Actions**:
  1. Simulate click on `_hangup`.
- **Expected Outputs**:
  - `_call->hangup()` or `_call->leave()` invoked.
  - Call window closes cleanly without memory leaks.
- **State Verification**:
  - Call state transitions to `Discarded` / `Destroyed`.
- **Mock Requirements**: `CallSimulator` observing `leave` invocation.

#### TEST-T1-F06-05: Titlebar Close Event Wired to Hangup Logic
- **Objective**: Verify closing the call window via titlebar close button (`QCloseEvent`) maps directly to call hangup.
- **Inputs & Preconditions**:
  - Active call session.
- **Actions**:
  1. Send `QCloseEvent` to `Calls::Group::Panel::widget()`.
- **Expected Outputs**:
  - Close event intercepted to trigger `endCall()`.
  - Window closes and resources are freed.
- **State Verification**:
  - Call termination confirmed in controller.
- **Mock Requirements**: `CallSimulator`.

---

### Feature 7: Camera & Participant Bar Controls
*Source*: `docs/fork_features.md:18`, `PROJECT.md:20` (`calls_group_panel.cpp`, `calls_group_members.cpp`)

#### TEST-T1-F07-01: Camera Toggle Button Presence & State Reflection
- **Objective**: Verify `_video` control button reflects active camera broadcast state.
- **Inputs & Preconditions**:
  - Group call connected. Camera initially off (`isSharingCamera == false`).
- **Actions**:
  1. Click `_video` toggle button to enable camera.
  2. Click `_video` toggle button again to disable camera.
- **Expected Outputs**:
  - Step 1: `_call->toggleShareCamera()` called; camera track starts; button indicates active state.
  - Step 2: Camera track stops; button reverts to inactive state.
- **State Verification**:
  - `_call->isSharingCameraValue()` matches toggle actions.
- **Mock Requirements**: `CallSimulator` with mock WebRTC video capture device.

#### TEST-T1-F07-02: Camera Tooltip Dynamic Text Updating
- **Objective**: Verify tooltip text changes dynamically between "Share Camera" and "Stop Camera" based on state.
- **Inputs & Preconditions**:
  - Mouse hovering on `_video` button.
- **Actions**:
  1. Inspect tooltip text when camera is off.
  2. Turn camera on and inspect tooltip text.
- **Expected Outputs**:
  - Camera off: Tooltip displays `tr::lng_group_call_tooltip_camera()`.
  - Camera on: Tooltip displays `tr::lng_group_call_tooltip_camera_off()`.
- **State Verification**:
  - `showNiceTooltip` producer emits updated text string.
- **Mock Requirements**: `rpl::producer` inspection harness.

#### TEST-T1-F07-03: Muted by Admin Participant Enforcement
- **Objective**: Verify that if a participant is muted by admin (`_call->mutedByAdmin() == true`), video and screen share tooltips return nullptr and activation is blocked.
- **Inputs & Preconditions**:
  - User muted by admin in group call permissions.
- **Actions**:
  1. Hover on `_video` and `_screenShare` buttons.
  2. Attempt click on `_video`.
- **Expected Outputs**:
  - Tooltips return `nullptr` (suppressed).
  - Video broadcast request is ignored.
- **State Verification**:
  - Camera sharing remains `false`.
- **Mock Requirements**: `CallSimulator` with `mutedByAdmin = true`.

#### TEST-T1-F07-04: Participant Sidebar Open/Close Control
- **Objective**: Verify participant list toggle button displays/hides `Calls::Group::MembersWidget`.
- **Inputs & Preconditions**:
  - Call window in Wide mode.
- **Actions**:
  1. Click members bar toggle button.
- **Expected Outputs**:
  - `_members` widget toggles visibility.
  - Window layout resizes main viewport to accommodate sidebar.
- **State Verification**:
  - `_members->isVisible()` is `true`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F07-05: Participant List Dynamic Counter Updating
- **Objective**: Verify the participant count label in the bar updates reactively as members join and leave.
- **Inputs & Preconditions**:
  - Call initially with 5 members.
- **Actions**:
  1. Simulate 3 new members joining.
  2. Simulate 1 member leaving.
- **Expected Outputs**:
  - Label updates from "5 participants" -> "8 participants" -> "7 participants".
- **State Verification**:
  - Member count label string matches `_call->participants().size()`.
- **Mock Requirements**: `CallSimulator` participant stream.

---

### Feature 8: CallButton to IconButton Migration
*Source*: `docs/fork_features.md:19`, `PROJECT.md:21` (`calls.style`, `calls_box_controller.cpp`, `lib_ui`)

#### TEST-T1-F08-01: Unified `IconButton` Primitive Geometry & Icon Sizing in `calls.style`
- **Objective**: Verify `CallButton` definition embeds `IconButton` (`button: IconButton;`) with unified styling dimensions.
- **Inputs & Preconditions**:
  - Parsed `calls.style` stylesheet.
- **Actions**:
  1. Inspect `CallButton` struct fields in compiled style definitions.
- **Expected Outputs**:
  - `CallButton` struct defines `button: IconButton`, `bg: color`, `bgSize: pixels`, `outerRadius: pixels`.
- **State Verification**:
  - Style struct alignment matches `lib_ui` `IconButton` interface.
- **Mock Requirements**: Style compiler validator.

#### TEST-T1-F08-02: Call Button Color Overrides & Palette Color Binding
- **Objective**: Verify call buttons properly apply color overrides (e.g. `toggleableOverrides`, `groupCallIconFg`).
- **Inputs & Preconditions**:
  - Instantiated `Ui::CallButton` or `Ui::IconButton` in call controls.
- **Actions**:
  1. Apply active state color override palette.
- **Expected Outputs**:
  - Foreground and background colors transition according to palette override rules.
- **State Verification**:
  - Custom painter applies overridden `QColor` values.
- **Mock Requirements**: Qt paint fixture.

#### TEST-T1-F08-03: Ripple & Click Animation Rendering Conformance
- **Objective**: Verify click ripple effects render accurately on migrated icon buttons without visual artifacts.
- **Inputs & Preconditions**:
  - Button displayed.
- **Actions**:
  1. Simulate mouse press and release on button.
- **Expected Outputs**:
  - Ripple animation triggers from click origin coordinate.
  - Ripple radius expands smoothly to button bounds.
- **State Verification**:
  - Ripple painter completes animation lifecycle without crash.
- **Mock Requirements**: Qt animation step simulator.

#### TEST-T1-F08-04: Keyboard Focus and Accessible Name Binding
- **Objective**: Verify all migrated call buttons support keyboard focus traversal (Tab key) and expose accessible names.
- **Inputs & Preconditions**:
  - Call controls bar containing Hangup, Mic, Camera, ScreenShare, GridMode buttons.
- **Actions**:
  1. Tab through controls sequentially.
- **Expected Outputs**:
  - Each button gains focus; `hasFocus()` becomes `true`.
  - `accessibleName()` returns valid descriptive string for each button.
- **State Verification**:
  - Accessible name is non-empty for every control.
- **Mock Requirements**: Accessible event listener.

#### TEST-T1-F08-05: Performance Benchmark: Button Creation & Render Overhead
- **Objective**: Verify that lightweight `IconButton` primitives instantiate and paint in < 1ms per widget.
- **Inputs & Preconditions**:
  - Benchmark harness creating 100 button instances.
- **Actions**:
  1. Measure total initialization and initial paint time.
- **Expected Outputs**:
  - Average instantiation + paint time is < 0.5ms per button.
- **State Verification**:
  - Zero memory leaks across rapid creation/destruction cycles.
- **Mock Requirements**: High-resolution performance timer.

---

### Feature 9: callCancelRipple Palette Color
*Source*: `docs/fork_features.md:20`, `PROJECT.md:22` (`lib_ui/ui/colors.palette`)

#### TEST-T1-F09-01: Color Value Integrity (`callCancelRipple: #c04646`)
- **Objective**: Verify `callCancelRipple` palette entry resolves to exact hex `#c04646` in `colors.palette`.
- **Inputs & Preconditions**:
  - Loaded `ui/colors.palette`.
- **Actions**:
  1. Query `st::callCancelRipple` color definition.
- **Expected Outputs**:
  - `st::callCancelRipple->c` has RGB values `R: 192 (0xc0), G: 70 (0x46), B: 70 (0x46)`.
- **State Verification**:
  - `st::callCancelRipple->c.name().toLower() == "#c04646"`.
- **Mock Requirements**: Palette loader test harness.

#### TEST-T1-F09-02: Palette Generator Output Verification
- **Objective**: Verify code generator creates valid C++ symbol `st::callCancelRipple` during build.
- **Inputs & Preconditions**:
  - Generated style headers (`styles/style_calls.h`, `ui/colors.palette`).
- **Actions**:
  1. Inspect symbol existence and type.
- **Expected Outputs**:
  - `style::color callCancelRipple` is declared as an `extern` / `constexpr` style color.
- **State Verification**:
  - Header compilation passes without missing symbol errors.
- **Mock Requirements**: Code inspection / unit test assertion.

#### TEST-T1-F09-03: Ripple Animation Paint on Cancel / Hangup Button
- **Objective**: Verify ripple animation on call cancel button uses `st::callCancelRipple` for wave fill.
- **Inputs & Preconditions**:
  - Cancel / Hangup button pressed in call popup.
- **Actions**:
  1. Trigger ripple animation step.
  2. Inspect painter brush color.
- **Expected Outputs**:
  - Ripple paint routine uses `st::callCancelRipple->c` with appropriate alpha fade.
- **State Verification**:
  - Painted pixel colors match `#c04646` hue.
- **Mock Requirements**: Mock QPainter verifying brush colors.

#### TEST-T1-F09-04: Theme Switching & Palette Cache Invalidation
- **Objective**: Verify switching between Day, Tinted, and Night themes preserves or overrides `callCancelRipple` properly.
- **Inputs & Preconditions**:
  - Application running with Day theme.
- **Actions**:
  1. Switch theme to Night mode.
  2. Re-query `st::callCancelRipple`.
- **Expected Outputs**:
  - Palette cache updates cleanly; color remains valid `#c04646` (or night override if specified).
- **State Verification**:
  - No stale color pointer references remain.
- **Mock Requirements**: Theme manager mock.

#### TEST-T1-F09-05: Custom Theme File Palette Fallback
- **Objective**: Verify that loading a custom theme `.tdesktop-theme` that omits `callCancelRipple` falls back to `#c04646` default.
- **Inputs & Preconditions**:
  - Custom theme missing `callCancelRipple` key.
- **Actions**:
  1. Load and parse custom theme palette.
- **Expected Outputs**:
  - `st::callCancelRipple` retains default value `#c04646`.
- **State Verification**:
  - Fallback mechanism prevents uninitialized color crash.
- **Mock Requirements**: Custom palette parser mock.

---

### Feature 10: Hidden Floating PiP Camera Preview
*Source*: `docs/fork_features.md:21`, `PROJECT.md:23` (`calls_group_panel.cpp`, `calls_group_viewport.cpp`)

#### TEST-T1-F10-01: Verification of Removed Floating PiP Webcam Overlay
- **Objective**: Verify that starting local camera does not spawn a floating, obstructing Picture-in-Picture window over the call.
- **Inputs & Preconditions**:
  - Group call active with multiple remote video feeds.
- **Actions**:
  1. Enable local camera (`toggleShareCamera`).
  2. Inspect top-level and floating child widgets of call panel.
- **Expected Outputs**:
  - No detached or floating PiP camera preview widget exists.
- **State Verification**:
  - Floating PiP widget count is `0`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F10-02: Local Camera Feed Integration into Main Grid as Standard Tile
- **Objective**: Verify self-camera feed is embedded directly into `Calls::Group::Viewport` as a standard participant tile (`self = true`).
- **Inputs & Preconditions**:
  - Group call in Grid mode.
- **Actions**:
  1. Enable local camera.
- **Expected Outputs**:
  - Viewport calls `add(endpoint, track, trackSize, pinned, true /* self */)`.
  - Self-tile is laid out alongside remote participant tiles in the grid.
- **State Verification**:
  - `_viewport` contains tile matching local user endpoint.
- **Mock Requirements**: `CallSimulator` with self video track.

#### TEST-T1-F10-03: Self-Video Tile Pin / Unpin Capability Without PiP Duplication
- **Objective**: Verify self-video tile can be pinned/unpinned within the grid without creating redundant preview duplicates.
- **Inputs & Preconditions**:
  - Self video active in grid.
- **Actions**:
  1. Pin self-video tile.
  2. Unpin self-video tile.
- **Expected Outputs**:
  - Tile moves between pinned stage and secondary grid slots cleanly.
  - Exactly 1 video sink instance exists for self-camera.
- **State Verification**:
  - Self video tile count remains exactly `1`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F10-04: Layout Recomputation When Local Camera Is Toggled
- **Objective**: Verify viewport grid geometry recomputes smoothly when local camera starts or stops.
- **Inputs & Preconditions**:
  - 3 remote video participants. Grid layout 2x2.
- **Actions**:
  1. Enable local camera (total 4 feeds).
  2. Verify 2x2 layout is filled.
  3. Disable local camera (total 3 feeds).
- **Expected Outputs**:
  - Grid solver re-evaluates optimal tile dimensions upon camera state changes.
- **State Verification**:
  - Viewport geometry covers available panel area without overlapping tiles.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F10-05: Zero Floating Widget Obstruction During Screen Share
- **Objective**: Verify that when a remote participant shares their screen, no local camera preview overlays or obstructs the presentation canvas.
- **Inputs & Preconditions**:
  - Remote screen share active in presentation mode.
  - Local camera enabled.
- **Actions**:
  1. Inspect screen share canvas bounding box and overlapping children.
- **Expected Outputs**:
  - Screen share canvas is 100% unobstructed by any floating PiP preview.
- **State Verification**:
  - Local video is restricted to sidebar thumbnail strip.
- **Mock Requirements**: `CallSimulator` with screen share track.

---

## Category 4: Multi-Display & Routing (DisplayCoordinator)

### Feature 11: Multi-Monitor Stage Window Support
*Source*: `docs/fork_features.md:24`, `PROJECT.md:24` (`calls_group_display_coordinator.cpp/.h`)

#### TEST-T1-F11-01: Multi-Monitor Detection via `QGuiApplication::screens()`
- **Objective**: Verify `DisplayCoordinator` enumerates connected monitors and identifies secondary displays.
- **Inputs & Preconditions**:
  - System with 2 connected virtual screens:
    - Screen 0 (Primary): `1920x1080` at `(0, 0)`
    - Screen 1 (Secondary): `1920x1080` at `(1920, 0)`
- **Actions**:
  1. Instantiate `DisplayCoordinator`.
  2. Call `updateScreens()`.
- **Expected Outputs**:
  - `_displays` map contains an entry for Screen 1 (`displayIndex = 1`).
  - `displayCount()` returns `1` auxiliary display.
- **State Verification**:
  - `displayCount() == 1`.
- **Mock Requirements**: `QtScreenMock` managing virtual screen list.

#### TEST-T1-F11-02: Dynamic Auxiliary Stage Window Instantiation on Screen 2
- **Objective**: Verify `ensureStageWindow(1)` creates a top-level `QWidget` positioned on Screen 1 with a dedicated `Viewport`.
- **Inputs & Preconditions**:
  - 2 screens connected.
- **Actions**:
  1. Call `_displayCoordinator->ensureStageWindow(1)`.
- **Expected Outputs**:
  - `DisplayWindow` created with `widget` and `viewport`.
  - `widget->geometry()` matches Screen 1 `availableGeometry()` `(1920, 0, 1920, 1080)`.
  - Window flags include `Qt::Window | Qt::FramelessWindowHint`.
- **State Verification**:
  - `_displays[1].widget != nullptr` and `_displays[1].viewport != nullptr`.
- **Mock Requirements**: `QtScreenMock`.

#### TEST-T1-F11-03: Auxiliary Window Frameless & Opaque Geometry Configuration
- **Objective**: Verify auxiliary display window sets `Qt::WA_OpaquePaintEvent` and fills the entire available screen bounds.
- **Inputs & Preconditions**:
  - Auxiliary display window created.
- **Actions**:
  1. Inspect window flags and attributes.
- **Expected Outputs**:
  - `testAttribute(Qt::WA_OpaquePaintEvent)` is `true`.
  - Viewport geometry set to `QRect(0, 0, 1920, 1080)`.
- **State Verification**:
  - Viewport widget is shown and raised on secondary screen.
- **Mock Requirements**: `QtScreenMock`.

#### TEST-T1-F11-04: Screen Addition and Removal Event Handling
- **Objective**: Verify `QGuiApplication::screenAdded` and `screenRemoved` signals dynamically create and destroy auxiliary display windows.
- **Inputs & Preconditions**:
  - System starts with 1 screen.
- **Actions**:
  1. Fire `screenAdded` with Screen 1 (`1920x1080`).
  2. Verify `_displayCountChanged` emits `1`.
  3. Fire `screenRemoved` with Screen 1.
  4. Verify `_displayCountChanged` emits `0`.
- **Expected Outputs**:
  - Auxiliary window is created on addition and destroyed/cleaned up on removal.
- **State Verification**:
  - `_displays.find(1) == _displays.end()` after removal.
- **Mock Requirements**: `QtScreenMock` emitting addition/removal signals.

#### TEST-T1-F11-05: Window Close & Graceful Teardown of Auxiliary Viewports
- **Objective**: Verify tearing down `DisplayCoordinator` closes all auxiliary windows and destroys their viewports without leaks.
- **Inputs & Preconditions**:
  - 2 auxiliary display windows active.
- **Actions**:
  1. Destroy `DisplayCoordinator` instance.
- **Expected Outputs**:
  - All auxiliary widgets are hidden, reset, and memory freed.
- **State Verification**:
  - No orphaned windows or WebRTC video sinks left open.
- **Mock Requirements**: Memory leak and lifecycle assertion harness.

---

### Feature 12: Dual Initial Windows Prompt
*Source*: `docs/fork_features.md:25`, `PROJECT.md:25` (`calls_group_display_coordinator.cpp`, `calls_group_panel.cpp`)

#### TEST-T1-F12-01: Target Display Prompt Trigger on Multi-Monitor Pin Action
- **Objective**: Verify that pinning a participant when multiple monitors are detected opens the target display selection dialog ("Screen 1 vs Screen 2").
- **Inputs & Preconditions**:
  - 2 monitors connected.
  - Video feed for User X in call.
- **Actions**:
  1. Click "Pin to Screen..." in participant context menu.
- **Expected Outputs**:
  - Display selection dialog is prompted to the user.
- **State Verification**:
  - Dialog is modal and active.
- **Mock Requirements**: `QtScreenMock` (2 screens), `CallSimulator`.

#### TEST-T1-F12-02: Screen Enumeration & Display Naming in Selection Dialog
- **Objective**: Verify the prompt enumerates all connected screens with human-readable labels (e.g. "Monitor 1: Primary (1920x1080)", "Monitor 2: Auxiliary (1920x1080)").
- **Inputs & Preconditions**:
  - 2 screens configured in test environment.
- **Actions**:
  1. Open display target selection prompt.
  2. Read list options in dialog.
- **Expected Outputs**:
  - Exactly 2 options displayed matching screen indices 0 and 1.
- **State Verification**:
  - Screen geometry and device names match mock screen list.
- **Mock Requirements**: `QtScreenMock`.

#### TEST-T1-F12-03: Selection Confirmation Routing Feed to Chosen Display
- **Objective**: Verify selecting "Screen 2" from the prompt invokes `pinToScreen(1, endpoint, track, trackSize, self)` on `DisplayCoordinator`.
- **Inputs & Preconditions**:
  - Display selection prompt open for User X.
- **Actions**:
  1. Select Screen 2 option and confirm.
- **Expected Outputs**:
  - `_displayCoordinator->pinToScreen(1, ...)` is called.
  - Feed appears pinned on Screen 2 stage window.
- **State Verification**:
  - `_displayCoordinator->isPinnedOnScreen(1, endpoint) == true`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F12-04: Single-Monitor Graceful Degradation (Bypass Prompt)
- **Objective**: Verify that if only 1 screen is detected, pinning bypasses the multi-monitor prompt and pins directly to primary viewport.
- **Inputs & Preconditions**:
  - 1 screen connected (`screens().size() == 1`).
- **Actions**:
  1. Click "Pin to Grid" for User X.
- **Expected Outputs**:
  - No dialog is prompted.
  - Feed is pinned directly to primary `_viewport`.
- **State Verification**:
  - `_viewport->togglePin(endpoint, true)` invoked.
- **Mock Requirements**: `QtScreenMock` with 1 screen.

#### TEST-T1-F12-05: User Cancellation of Target Display Prompt
- **Objective**: Verify cancelling the target display prompt dismisses dialog and leaves existing stage layouts unmutated.
- **Inputs & Preconditions**:
  - Prompt opened.
- **Actions**:
  1. Click Cancel / press Escape.
- **Expected Outputs**:
  - Dialog closes.
  - No new feeds are routed or pinned to any screen.
- **State Verification**:
  - `_displayCoordinator->pinnedCount(1)` remains unchanged.
- **Mock Requirements**: Qt dialog test harness.

---

### Feature 13: Display Role Router
*Source*: `docs/fork_features.md:26`, `PROJECT.md:26` (`calls_group_display_coordinator.cpp/.h`)

#### TEST-T1-F13-01: Role Assignment (`ActiveSpeaker`, `GridViewport`, `ChatStation`)
- **Objective**: Verify `DisplayCoordinator::setRole` assigns roles to display indices.
- **Inputs & Preconditions**:
  - Auxiliary display 1 active.
- **Actions**:
  1. Call `_displayCoordinator->setRole(1, DisplayRole::ActiveSpeaker)`.
  2. Call `_displayCoordinator->setRole(1, DisplayRole::ChatStation)`.
  3. Call `_displayCoordinator->setRole(1, DisplayRole::GridViewport)`.
- **Expected Outputs**:
  - Step 1: `role(1)` returns `DisplayRole::ActiveSpeaker`.
  - Step 2: `role(1)` returns `DisplayRole::ChatStation`.
  - Step 3: `role(1)` returns `DisplayRole::GridViewport`.
- **State Verification**:
  - `_displays[1].role` matches assigned enum.
- **Mock Requirements**: `DisplayCoordinator` test harness.

#### TEST-T1-F13-02: Window Title Updating Matching Assigned Role
- **Objective**: Verify changing display role updates the auxiliary window title via `RoleText(role)`.
- **Inputs & Preconditions**:
  - Auxiliary window for Screen 1 open.
- **Actions**:
  1. Set role to `DisplayRole::ActiveSpeaker`.
  2. Set role to `DisplayRole::ChatStation`.
  3. Set role to `DisplayRole::GridViewport`.
- **Expected Outputs**:
  - Window title becomes "Active Speaker", "Chat Station", and "Grid View" respectively.
- **State Verification**:
  - `_displays[1].widget->windowTitle()` matches expected string.
- **Mock Requirements**: Qt window mock.

#### TEST-T1-F13-03: Role State Query & Default Role Initialization
- **Objective**: Verify newly created auxiliary displays initialize with default role `DisplayRole::GridViewport` and query on non-existent display returns `DisplayRole::None`.
- **Inputs & Preconditions**:
  - Screen 1 attached.
- **Actions**:
  1. Query `role(1)`.
  2. Query `role(99)`.
- **Expected Outputs**:
  - `role(1) == DisplayRole::GridViewport`.
  - `role(99) == DisplayRole::None`.
- **State Verification**:
  - Return values match specification.
- **Mock Requirements**: Unit test harness.

#### TEST-T1-F13-04: ChatStation Role Viewport & Chat Content Setup
- **Objective**: Verify assigning `ChatStation` role configures the display window to host full-screen chat and search components.
- **Inputs & Preconditions**:
  - Screen 1 assigned `DisplayRole::ChatStation`.
- **Actions**:
  1. Trigger layout update for display 1.
- **Expected Outputs**:
  - Window initializes chat layout controller.
- **State Verification**:
  - Chat station widget hierarchy is instantiated on Screen 1.
- **Mock Requirements**: `QtScreenMock`.

#### TEST-T1-F13-05: Multi-Role Configuration Across 3+ Displays
- **Objective**: Verify independent role assignment across 3 monitors (Screen 0: Primary Call UI, Screen 1: Active Speaker Stage, Screen 2: Grid Viewport).
- **Inputs & Preconditions**:
  - 3 screens connected.
- **Actions**:
  1. Set Screen 1 role to `ActiveSpeaker`.
  2. Set Screen 2 role to `GridViewport`.
- **Expected Outputs**:
  - `role(1) == DisplayRole::ActiveSpeaker`.
  - `role(2) == DisplayRole::GridViewport`.
- **State Verification**:
  - Both secondary windows operate concurrently under distinct roles.
- **Mock Requirements**: 3-screen `QtScreenMock`.

---

### Feature 14: Async Video Stream Routing
*Source*: `docs/fork_features.md:27`, `PROJECT.md:27` (`calls_group_display_coordinator.cpp`, `calls_group_viewport.cpp`)

#### TEST-T1-F14-01: Non-Blocking Dispatch of Video Frame Consumer to Secondary Viewport
- **Objective**: Verify video frames dispatched to secondary display viewport render asynchronously without blocking the main UI thread.
- **Inputs & Preconditions**:
  - Secondary stage window open on Screen 1.
  - Video track streaming 1080p 60fps frames.
- **Actions**:
  1. Route video track to Screen 1 via `pinToScreen`.
  2. Pump 60 video frames through the track.
- **Expected Outputs**:
  - Secondary viewport consumes frames via its render backend (OpenGL / RHI / Raster).
  - Main thread event loop latency remains < 5ms.
- **State Verification**:
  - Zero frame drops or main-thread hitching.
- **Mock Requirements**: `CallSimulator` frame generator with latency probe.

#### TEST-T1-F14-02: Video Track Pinning to Specific Screen (`pinToScreen`)
- **Objective**: Verify `pinToScreen(screenIndex, endpoint, track, trackSize, self)` registers endpoint in `_routedEndpoints` and calls `viewport->add` with pinned status.
- **Inputs & Preconditions**:
  - Video endpoint `EP_Alice`.
- **Actions**:
  1. Call `pinToScreen(1, EP_Alice, track, trackSize, false)`.
- **Expected Outputs**:
  - `_routedEndpoints[1]` contains `EP_Alice`.
  - `isPinnedOnScreen(1, EP_Alice)` returns `true`.
  - `pinnedCount(1)` returns `1`.
  - `showDisplay(1)` is invoked to raise window.
- **State Verification**:
  - Endpoint is active on Screen 1 viewport.
- **Mock Requirements**: `DisplayCoordinator` test harness.

#### TEST-T1-F14-03: Unpinning and Video Track Teardown from Secondary Screen (`unpinFromScreen`)
- **Objective**: Verify `unpinFromScreen(1, EP_Alice)` unpins and removes endpoint from Screen 1 viewport.
- **Inputs & Preconditions**:
  - `EP_Alice` pinned on Screen 1.
- **Actions**:
  1. Call `unpinFromScreen(1, EP_Alice)`.
- **Expected Outputs**:
  - `_routedEndpoints[1]` does not contain `EP_Alice`.
  - `isPinnedOnScreen(1, EP_Alice)` returns `false`.
  - `pinnedCount(1)` drops to `0`.
  - Secondary viewport removes video tile.
- **State Verification**:
  - Video track unhooked cleanly.
- **Mock Requirements**: `DisplayCoordinator`.

#### TEST-T1-F14-04: Quality Request Event Propagation from Secondary Viewport
- **Objective**: Verify `VideoQualityRequest` events emitted by secondary viewport propagate through `DisplayCoordinator::qualityRequests()` to trigger simulcast upscaling.
- **Inputs & Preconditions**:
  - Secondary display viewport with full-screen pinned tile.
- **Actions**:
  1. Secondary viewport fires quality request for `EP_Alice` (demanding HD stream).
- **Expected Outputs**:
  - `_qualityRequests` producer on `DisplayCoordinator` fires `EP_Alice`.
- **State Verification**:
  - WebRTC engine receives upscaling signal for `EP_Alice`.
- **Mock Requirements**: `rpl::producer` listener harness.

#### TEST-T1-F14-05: Multiple Video Streams Concurrently Routed to Different Screens
- **Objective**: Verify routing `EP_Alice` to Screen 1 and `EP_Bob` to Screen 2 concurrently.
- **Inputs & Preconditions**:
  - 3 monitors total.
- **Actions**:
  1. Pin `EP_Alice` to Screen 1.
  2. Pin `EP_Bob` to Screen 2.
- **Expected Outputs**:
  - `isPinnedOnScreen(1, EP_Alice) == true` and `isPinnedOnScreen(1, EP_Bob) == false`.
  - `isPinnedOnScreen(2, EP_Bob) == true` and `isPinnedOnScreen(2, EP_Alice) == false`.
- **State Verification**:
  - Both video streams render on their respective displays without cross-talk.
- **Mock Requirements**: 3-screen `QtScreenMock`.

---

### Feature 15: Secondary Display Active-Speaker Isolation
*Source*: `docs/fork_features.md:28`, `PROJECT.md:28` (`calls_group_display_coordinator.cpp`)

#### TEST-T1-F15-01: Guarded `updateAudioLevels` on Auxiliary Display (No Auto-Stealing)
- **Objective**: Verify that `DisplayCoordinator::updateAudioLevels` is guarded/no-op'd so active speaker changes never hijack or auto-fill video slots on secondary displays.
- **Inputs & Preconditions**:
  - Feed `EP_Alice` explicitly pinned on Screen 1.
  - Remote participant `User_Charlie` starts shouting (audio level = `1.0`).
- **Actions**:
  1. Call `_displayCoordinator->updateAudioLevels({ { peerCharlie, 1.0 }, { peerAlice, 0.0 } })`.
- **Expected Outputs**:
  - Feed on Screen 1 remains `EP_Alice`.
  - `User_Charlie` is NOT routed to Screen 1.
- **State Verification**:
  - `isPinnedOnScreen(1, EP_Alice) == true`.
  - `isPinnedOnScreen(1, EP_Charlie) == false`.
- **Mock Requirements**: `CallSimulator` injecting rapid audio level fluctuations.

#### TEST-T1-F15-02: Explicitly Pinned Feeds Maintain Persistent Focus
- **Objective**: Verify pinned feeds on secondary displays maintain persistent visual focus regardless of who is speaking in the call.
- **Inputs & Preconditions**:
  - 2 feeds (`EP_Alice`, `EP_Bob`) pinned on Screen 1.
  - 10 other participants speaking sequentially.
- **Actions**:
  1. Simulate 10 audio level update bursts for unpinned participants.
- **Expected Outputs**:
  - Pinned stage on Screen 1 retains exactly `EP_Alice` and `EP_Bob`.
  - Tile order and dimensions on Screen 1 remain steady.
- **State Verification**:
  - `pinnedCount(1) == 2`.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F15-03: Secondary Display Feed Count Invariance During Rapid Speaker Flapping
- **Objective**: Verify rapid active speaker alternation (speaker flapping) causes zero mutations to secondary screen slot allocator.
- **Inputs & Preconditions**:
  - Screen 1 active with 1 pinned stream.
- **Actions**:
  1. Alternate active speaker between 5 participants every 50ms for 2 seconds.
- **Expected Outputs**:
  - Secondary screen viewport executes 0 layout recalculations or tile re-parenting operations.
- **State Verification**:
  - `pinnedCount(1) == 1` continuously.
- **Mock Requirements**: High-frequency audio generator harness.

#### TEST-T1-F15-04: Audio Level Visual Indicators Confined to Primary Display
- **Objective**: Verify speaker audio ring/waveform animations are confined to primary window tiles and do not clutter secondary display stage feeds.
- **Inputs & Preconditions**:
  - Secondary display stage rendering `EP_Alice`.
- **Actions**:
  1. Alice speaks (audio level = `0.8`).
  2. Inspect secondary viewport tile rendering flags.
- **Expected Outputs**:
  - Clean video render on secondary display without distracting audio ring overlays.
- **State Verification**:
  - Stage viewport operates in clean presentation mode.
- **Mock Requirements**: `CallSimulator`.

#### TEST-T1-F15-05: Re-enabling Active Speaker Role Explicitly vs Default Isolation Invariant
- **Objective**: Verify that if a display is explicitly assigned `DisplayRole::ActiveSpeaker`, it routes the loudest speaker, whereas default auxiliary displays strictly enforce isolation.
- **Inputs & Preconditions**:
  - Screen 1: Default `DisplayRole::GridViewport` (Isolated).
  - Screen 2: Configured to `DisplayRole::ActiveSpeaker`.
- **Actions**:
  1. Trigger audio level spike for `User_Dave`.
- **Expected Outputs**:
  - Screen 1 remains unchanged (isolation preserved).
  - Screen 2 updates to show `User_Dave`.
- **State Verification**:
  - Isolated display unchanged; dedicated active-speaker display routes `User_Dave`.
- **Mock Requirements**: `DisplayCoordinator` dual-display test fixture.

---

## Test Implementation Matrix & Traceability

| Category | Feature # | Feature Name | Test ID Range | Target Test File | Status |
|---|---|---|---|---|---|
| **Cat 1: Privacy & Ghost Mode** | 1 | Ghost Mode (Decoupled Read Receipts) | `TEST-T1-F01-01` .. `05` | `test_t1_privacy_network.py` | Complete |
| | 2 | Ghost Mode Settings UI & Persistence | `TEST-T1-F02-01` .. `05` | `test_t1_privacy_network.py` | Complete |
| **Cat 2: Network & Download** | 3 | Multi-Connection MTProto Chunk Downloading | `TEST-T1-F03-01` .. `05` | `test_t1_privacy_network.py` | Complete |
| **Cat 3: Call UI & Controls** | 4 | Grid Mode Toggle | `TEST-T1-F04-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| | 5 | In-Call Chat Panel Slide-Out | `TEST-T1-F05-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| | 6 | End Call Button & Hover Controls | `TEST-T1-F06-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| | 7 | Camera & Participant Bar Controls | `TEST-T1-F07-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| | 8 | CallButton to IconButton Migration | `TEST-T1-F08-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| | 9 | callCancelRipple Palette Color | `TEST-T1-F09-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| | 10 | Hidden Floating PiP Camera Preview | `TEST-T1-F10-01` .. `05` | `test_t1_calls_ui.py` | Complete |
| **Cat 4: Multi-Display & Routing** | 11 | Multi-Monitor Stage Window Support | `TEST-T1-F11-01` .. `05` | `test_t1_multi_display.py` | Complete |
| | 12 | Dual Initial Windows Prompt | `TEST-T1-F12-01` .. `05` | `test_t1_multi_display.py` | Complete |
| | 13 | Display Role Router | `TEST-T1-F13-01` .. `05` | `test_t1_multi_display.py` | Complete |
| | 14 | Async Video Stream Routing | `TEST-T1-F14-01` .. `05` | `test_t1_multi_display.py` | Complete |
| | 15 | Secondary Display Active-Speaker Isolation | `TEST-T1-F15-01` .. `05` | `test_t1_multi_display.py` | Complete |

**Total Tier 1 Test Cases in Scope**: **75 / 75**
