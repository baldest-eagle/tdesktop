# Technical Analysis: Group Call Context Menu Actions (Pin to Grid & Open Chat)

## Executive Summary
This investigation analyzes the wiring of context menu actions in group calls (`calls_group_members.cpp`), specifically focusing on `lng_group_call_context_pin_to_grid` ("Pin to grid") and `lng_group_call_open_chat` ("Open Chat"). Both language strings are already present in `Telegram/Resources/langs/lang.strings` but are currently unwired in C++ source code. This report details their definitions, call flows, connections to viewport grid pinning and window session controllers, edge case handling, and exact code modification recommendations adhering to `REVIEW.md` and `AGENTS.md`.

---

## 1. Codebase Findings & Observations

### 1.1 Language String Definitions
- **Location**: `Telegram/Resources/langs/lang.strings:6459-6468`
- **Context block**:
  ```strings
  "lng_group_call_context_pin_camera" = "Pin video";
  "lng_group_call_context_unpin_camera" = "Unpin video";
  "lng_group_call_context_pin_screen" = "Pin screencast";
  "lng_group_call_context_unpin_screen" = "Unpin screencast";
  "lng_group_call_context_pin_to_grid" = "Pin to grid";
  "lng_group_call_open_chat" = "Open Chat";
  "lng_group_call_context_remove" = "Remove";
  "lng_group_call_context_cancel_invite" = "Discard invite";
  "lng_group_call_context_stop_ringing" = "Stop calling";
  "lng_group_call_context_ban_from_call" = "Ban from call";
  ```
- **Observation**:
  - `lng_group_call_context_pin_to_grid` (line 6463) and `lng_group_call_open_chat` (line 6464) are placed in the group call participant context menu string cluster.
  - While `lng_group_call_context_pin_camera` and `lng_group_call_context_pin_screen` are used in `calls_group_members.cpp:1448-1464`, `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` were left unreferenced.

### 1.2 Context Menu Generation in `calls_group_members.cpp`
- **Location**: `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1339-1565`
- **Function**: `base::unique_qptr<Ui::PopupMenu> Members::Controller::createRowContextMenu(QWidget *parent, not_null<PeerListRow*> row)`
- **Current Behavior for Chat Opening** (lines 1523-1534):
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
  - For user participants (`participantPeer->isUser()`), the menu provides "Send Message" (`tr::lng_context_send_message`) which invokes `showHistory`.
  - For channel or group participants (`!participantPeer->isUser()`), "View Channel" or "View Group" is shown, but **no action** to open the chat exists.
- **Current Behavior for Video Pinning** (lines 1418-1467):
  ```cpp
  if (const auto real = _call->lookupReal()) {
      auto oneFound = false;
      auto hasTwoOrMore = false;
      const auto &shown = _call->shownVideoTracks();
      for (const auto &[endpoint, track] : _call->activeVideoTracks()) {
          if (shown.contains(endpoint)) {
              if (oneFound) {
                  hasTwoOrMore = true;
                  break;
              }
              oneFound = true;
          }
      }
      const auto participant = real->participantByPeer(participantPeer);
      if (participant && hasTwoOrMore) {
          const auto &large = _call->videoEndpointLarge();
          const auto pinned = _call->videoEndpointPinned();
          const auto camera = VideoEndpoint{
              VideoEndpointType::Camera,
              participantPeer,
              computeCameraEndpoint(participant),
          };
          const auto screen = VideoEndpoint{
              VideoEndpointType::Screen,
              participantPeer,
              computeScreenEndpoint(participant),
          };
          if (shown.contains(camera)) {
              if (pinned && large == camera) {
                  result->addAction(
                      tr::lng_group_call_context_unpin_camera(tr::now),
                      [=] { _call->pinVideoEndpoint({}); });
              } else {
                  result->addAction(
                      tr::lng_group_call_context_pin_camera(tr::now),
                      [=] { _call->pinVideoEndpoint(camera); });
              }
          }
          if (shown.contains(screen)) {
              if (pinned && large == screen) {
                  result->addAction(
                      tr::lng_group_call_context_unpin_screen(tr::now),
                      [=] { _call->pinVideoEndpoint({}); });
              } else {
                  result->addAction(
                      tr::lng_group_call_context_pin_screen(tr::now),
                      [=] { _call->pinVideoEndpoint(screen); });
                  }
          }
      }
      ...
  }
  ```

### 1.3 Trigger Points for the Context Menu
1. **Sidebar / Members List**: Right-clicking or long-pressing a participant row in the members panel delegates via `Members::Controller::rowContextMenu` -> `createRowContextMenu`.
2. **Viewport Video Tile**: Right-clicking a video tile in `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:220`:
   ```cpp
   if (button == Qt::RightButton) {
       tile->row()->showContextMenu();
   }
   ```
   `tile->row()` returns `MembersRow*`, invoking `_delegate->rowShowContextMenu(this)`, which calls `showRowMenu(row, false)` and displays `createRowContextMenu`.

---

## 2. Action Mechanics & Wiring Architecture

### 2.1 "Open Chat" Action
- **Intent**: Allow users in a call to directly open the chat history for a participant (user, channel, or group).
- **Mechanism**:
  - `showHistory` is already defined in `calls_group_members.cpp:1388-1394`:
    ```cpp
    const auto showHistory = [=] {
        withActiveWindow([=](not_null<::Window::SessionController*> window) {
            window->showPeerHistory(
                participantPeer,
                ::Window::SectionShow::Way::Forward);
        });
    };
    ```
  - `withActiveWindow` safely retrieves `Core::App().activePrimaryWindow()`, discards and deletes the popup menu to prevent focus reactivations, invokes `window->invokeForSessionController(account, participantPeer, ...)`, and activates the MainWindow.
- **Resolution**:
  - When `participantPeer->isUser()` is true: show `tr::lng_context_send_message(tr::now)` ("Send Message").
  - When `!participantPeer->isUser()` (channel or group): show `tr::lng_group_call_open_chat(tr::now)` ("Open Chat").
  - Both invoke `showHistory`.

### 2.2 "Pin to Grid" Action
- **Intent**: Provide participant/video feed pinning in the group call grid.
- **Mechanism**:
  - `GroupCall::pinVideoEndpoint(VideoEndpoint endpoint)` (`Telegram/SourceFiles/calls/group/calls_group_call.cpp:3959-3965`):
    - Sets `_videoEndpointLarge = endpoint` and `_videoEndpointPinned = true` (or unpins if empty).
  - `Viewport::togglePin(const VideoEndpoint &endpoint, bool pinned)` (`Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:1037-1048`):
    - Places pinned endpoints in `_pinnedEndpoints` which are assigned to leading slots (0, 1, ...) during layout calculation in `Viewport::countWide`.
- **Resolution**:
  - When a participant has an active camera or screen video feed:
    - If camera is shown: allow pinning to grid via `tr::lng_group_call_context_pin_to_grid(tr::now)` (or `tr::lng_group_call_context_pin_camera(tr::now)`), unpinning via `tr::lng_group_call_context_unpin_camera(tr::now)`.
    - If screen is shown: allow pinning to grid via `tr::lng_group_call_context_pin_to_grid(tr::now)` / `tr::lng_group_call_context_pin_screen(tr::now)`, unpinning via `tr::lng_group_call_context_unpin_screen(tr::now)`.

---

## 3. Edge Case Analysis

| Edge Case | Impact | Handling & Guard |
|---|---|---|
| **Server Admin Permissions** | User is not admin / moderator | Pinning to grid is a client-side layout preference and requires no server permissions. Muting/kicking actions remain strictly guarded by `_call->canManage()` and chat admin checks. |
| **Already Pinned State** | Feed is already pinned | Checked via `pinned && large == camera` (or `screen`). If pinned, menu dynamically displays the unpin string (`lng_group_call_context_unpin_camera` / `_unpin_screen`) with unpin callback `_call->pinVideoEndpoint({})`. |
| **Non-User Participants** | Participant is channel or group | `!participantPeer->isUser()` now receives `tr::lng_group_call_open_chat(tr::now)`, resolving the missing history action for non-user participants. |
| **Context Menu Lifetime & Focus** | MainWindow activated while menu open | `withActiveWindow` calls `menu->discardParentReActivate()` and deletes `weakMenu.get()` before activating MainWindow, preventing focus bounce-back to the call panel. |
| **Single Video Track** | Only 1 video track in call | If `hasTwoOrMore` is false, pinning in spotlight is redundant, but in grid layout, pinning ensures the feed remains locked to Slot 0. |

---

## 4. Proposed Implementation Snippet

In `Telegram/SourceFiles/calls/group/calls_group_members.cpp`:

```cpp
// In Members::Controller::createRowContextMenu
if (participantPeer->isUser()) {
	result->addAction(
		tr::lng_context_send_message(tr::now),
		showHistory);
} else {
	result->addAction(
		tr::lng_group_call_open_chat(tr::now),
		showHistory);
}
```

And for pinning feeds:
```cpp
if (shown.contains(camera)) {
	if (pinned && large == camera) {
		result->addAction(
			tr::lng_group_call_context_unpin_camera(tr::now),
			[=] { _call->pinVideoEndpoint({}); });
	} else {
		result->addAction(
			tr::lng_group_call_context_pin_to_grid(tr::now),
			[=] { _call->pinVideoEndpoint(camera); });
	}
}
if (shown.contains(screen)) {
	if (pinned && large == screen) {
		result->addAction(
			tr::lng_group_call_context_unpin_screen(tr::now),
			[=] { _call->pinVideoEndpoint({}); });
	} else {
		result->addAction(
			tr::lng_group_call_context_pin_screen(tr::now),
			[=] { _call->pinVideoEndpoint(screen); });
	}
}
```

---

## 5. Style Guidelines Compliance Checklist (REVIEW.md & AGENTS.md)
- [x] **No single-line comments in code**: No trivial comments describing obvious code lines.
- [x] **String literals**: Use `_q` literals where applicable (`u"..."_q`).
- [x] **Language strings**: Use `tr::lng_...` directly without `rpl::single`.
- [x] **Whitespace & Formatting**: No consecutive empty lines; proper indentation.
- [x] **Lifetime Guards**: Use `crl::guard` and weak pointers where closures outlive scope.
