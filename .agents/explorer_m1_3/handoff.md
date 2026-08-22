# Handoff Report: Explorer M1-3 (Calls UI, Context Actions: Pin to Grid & Open Chat)

## 1. Observation
1. **Language Strings in `lang.strings`**:
   - `Telegram/Resources/langs/lang.strings:6463`: `"lng_group_call_context_pin_to_grid" = "Pin to grid";`
   - `Telegram/Resources/langs/lang.strings:6464`: `"lng_group_call_open_chat" = "Open Chat";`
   - Located in the exact same block with `lng_group_call_context_pin_camera` (line 6459), `lng_group_call_context_unpin_camera` (line 6460), `lng_group_call_context_pin_screen` (line 6461), `lng_group_call_context_unpin_screen` (line 6462).
2. **Context Menu Generation in `calls_group_members.cpp`**:
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1339-1565`: `Members::Controller::createRowContextMenu(QWidget *parent, not_null<PeerListRow*> row)` constructs the context popup menu for any call participant.
   - At lines 1523-1534:
     ```cpp
     result->addAction(
         (participantPeer->isUser()
             ? tr::lng_context_view_profile(tr::now)
             : participantPeer->isBroadcast()
             ? tr::lng_context_view_channel(tr::now)
             : tr::lng_context_view_group(tr::now)),
         showProfile);
     if (participantPeer->isUser()) {
         result->addAction(
             tr::lng_context_send_message(tr::now),
             showHistory);
     }
     ```
     When `participantPeer` is not a user (e.g. participant speaking as a channel or group), `showHistory` is completely omitted.
   - At lines 1445-1466:
     Video pinning uses `tr::lng_group_call_context_pin_camera` and `tr::lng_group_call_context_pin_screen`, but `tr::lng_group_call_context_pin_to_grid` is unreferenced.
3. **Viewport Context Menu Trigger**:
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:219-220`:
     ```cpp
     } else if (button == Qt::RightButton) {
         tile->row()->showContextMenu();
     }
     ```
     Right-clicking a video tile directly opens the participant's `createRowContextMenu`.
4. **Pinning Engine Mechanics**:
   - `Telegram/SourceFiles/calls/group/calls_group_call.cpp:3959-3965`: `GroupCall::pinVideoEndpoint(VideoEndpoint endpoint)` manages active endpoint pinning.
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:1037-1056`: `Viewport::togglePin(const VideoEndpoint &endpoint, bool pinned)` and `_pinnedEndpoints` manage leading slot assignments in `Viewport::countWide`.

---

## 2. Logic Chain
1. **Observation 1 & 2 -> Missing Non-User Chat Opening Action**:
   - `lng_group_call_open_chat` was defined in `lang.strings` specifically for group call participant menus.
   - For users, `tr::lng_context_send_message` opens private direct message history via `showHistory`.
   - For non-user participants (channels/groups), `showHistory` is the exact method to open that channel/group's history in `MainWindow`, but was missing from the `else` branch of `if (participantPeer->isUser())`.
   - Adding `result->addAction(tr::lng_group_call_open_chat(tr::now), showHistory)` in the `else` branch completes the chat opening action for all participants.
2. **Observation 1, 2, 3 & 4 -> Pin to Grid Wiring**:
   - `lng_group_call_context_pin_to_grid` is defined for pinning video feeds to the call grid.
   - When a video endpoint (camera or screencast) is available, offering `tr::lng_group_call_context_pin_to_grid(tr::now)` connects directly to `_call->pinVideoEndpoint(camera)` and toggles grid pinning.
   - When already pinned, dynamic toggle logic presents `tr::lng_group_call_context_unpin_camera(tr::now)` or `tr::lng_group_call_context_unpin_screen(tr::now)` with `_call->pinVideoEndpoint({})`.
3. **Observation 2 & 4 -> Safe Window and Menu Lifetime**:
   - `withActiveWindow` ensures the menu is destroyed via `delete weakMenu.get()` before activating `MainWindow`, eliminating focus re-activation race conditions.

---

## 3. Caveats
- `lng_group_call_context_pin_to_grid` applies when pinning video tracks to the viewport grid. If the call contains no active video tracks, video pinning actions are naturally hidden since there is no feed to pin.
- No server-side MTProto modifications or schema changes are needed; this is entirely client-side UI and session controller routing.

---

## 4. Conclusion
1. **Open Chat**: In `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1530-1534`, add the `else` branch to provide `tr::lng_group_call_open_chat(tr::now)` invoking `showHistory`.
2. **Pin to Grid**: In `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1445-1466`, wire `tr::lng_group_call_context_pin_to_grid(tr::now)` to `_call->pinVideoEndpoint(camera)` (and for screencast as appropriate).
3. **Quality & Guidelines**: Code adheres strictly to `REVIEW.md` (no single-line comments in code, `_q` literals, `crl::guard`, proper auto usage).

---

## 5. Verification Method
1. **Code Inspection**:
   - Verify `Telegram/SourceFiles/calls/group/calls_group_members.cpp` contains references to `tr::lng_group_call_open_chat` and `tr::lng_group_call_context_pin_to_grid`.
   - Verify both branches of `if (participantPeer->isUser())` populate an appropriate history action.
2. **Build and Test**:
   - Compile Debug target: `cmake --build out --config Debug --target Telegram`
   - Run tests if applicable.
3. **Functional Scenario**:
   - In a group call with participant joined as a channel: right click row -> "Open Chat" appears and opens the channel history in MainWindow.
   - In a group call with video feeds: right click tile/row -> "Pin to grid" appears and pins the feed to the leading grid slot; right-clicking pinned feed shows "Unpin video".
