# Telegram Desktop Fork — Codebase Survey & Feature Audit Report

**Date**: 2026-08-20  
**Target Branch**: `nightly`  
**Working Directory**: `c:\Users\kyleh\tdesktop`  
**Investigator**: Explorer Agent (`explorer_codebase_survey`)  

---

## 1. Executive Summary

This survey provides a comprehensive audit of the Telegram Desktop (`tdesktop`) fork against `docs/fork_features.md`, `ARCHITECTURE.md`, `REVIEW.md`, and `AGENTS.md`.

The codebase contains substantial, working implementations of high-impact fork features including **Ghost Mode (E3)**, **Multi-Connection MTProto Streaming (B1)**, **DisplayCoordinator Multi-Monitor Routing**, **Dynamic Grid Solver & Persistent Pin Allocation**, **In-Call Sidebar Search**, **Alphabetical Participant Sorting**, and **Rich Tasks**.

However, several features are partially implemented, have broken logic branches, or remain stubbed:
1. **`calls_group_floating_overlay.cpp`**: `setupChatContent()` is an empty placeholder stub; `MessagesUi` is not instantiated or connected to the panel; multiple formatting/convention violations exist (zero indentation, `QStringLiteral`, single-line comments).
2. **`calls_group_viewport.cpp`**: Line 578 contains a dead-code logic bug (`if (count == 2 && slotConstraint == 0)` inside `if (fixedGridDim > 0)`), preventing 2-feed 50/50 grid layout from ever triggering.
3. **`calls_box_controller.cpp/.h` vs `window_main_menu.cpp`**: `ShowCallsMenu` is fully written to provide an inline calls menu with active group calls, but `window_main_menu.cpp:707` still calls `ShowCallsBox` directly.
4. **Main Menu Wallet**: Mentioned in `docs/fork_features.md`, not yet added to `window_main_menu.cpp`.
5. **Context Menu Actions ("Pin to Grid" & "Open Chat")**: Language keys exist in `lang.strings`, but the context menu action wiring in `calls_group_members.cpp` only supports standard single-camera/screen pinning and lacks grid pin / target screen selection.
6. **SQLite PRAGMA Tuning (C1)**: Mentioned in docs (`docs/fork_features.md`, `ARCHITECTURE.md`), but Telegram Desktop core does not use SQLite natively (it uses `lib_storage` binary cache database).
7. **WebRTC Jitter Clamping (A1)**: Audio fast acceleration (`audio_jitter_buffer_fast_accelerate = true`) and 50ms min delay (`audio_jitter_buffer_min_delay_ms = 50`) are wired in `GroupInstanceCustomImpl.cpp:1565-1566` and `MediaManager.cpp:364`. Further video playout clamping / jitter buffer tuning is documented as planned.

---

## 2. Feature Implementation Status Matrix

| Category | Feature | Status | Primary Locations | Notes & Blockers |
|---|---|---|---|---|
| **Privacy (E3)** | Ghost Mode (Decoupled Read Receipts) | **Complete** | `data/data_histories.cpp:716-721` | Intercepts `Histories::sendReadRequest` when `ghostMode()` is enabled. |
| **Privacy (E3)** | Settings UI & Persistence | **Complete** | `core/core_settings.h`, `core/core_settings.cpp:295,464,634,870,1246`, `settings/sections/settings_privacy_security.cpp:1088-1117,1203` | Serialized in sequential QDataStream at the end of the stream with fallback. |
| **Network (B1)** | Multi-Connection MTProto Chunk Downloading | **Complete** | `storage/download_manager_mtproto.cpp:25-26` | `kStartSessionsCount = 4`, `kMaxSessionsCount = 16`, parallel stream connections. |
| **Call UI & Controls** | Grid Mode Toggle | **Implemented** | `calls/group/calls_group_panel.cpp:859-877`, `calls/group/calls_group_viewport.cpp:1027` | Reactive button toggling `_viewport->setGridMode()`. |
| **Call UI & Controls** | Chat Panel Toggle | **Implemented** | `calls/group/calls_group_panel.cpp:557-615` | Translucent slide-out panel (`Ui::RoundRect`, opacity 0.9, close button, embeds `MessagesUi`). |
| **Call UI & Controls** | End Call Button & Hover Controls | **Implemented** | `calls/group/calls_group_panel.cpp:689` | Corner/bordering UI hangup button. |
| **Call UI & Controls** | CallButton → IconButton Refactor | **Partial** | `calls/group/calls_group_panel.h:263`, `calls/group/calls_group_panel.cpp:860` | `_gridModeButton` is still using `Ui::CallButton`. |
| **Call UI & Controls** | `callCancelRipple` Palette Color | **Complete** | `lib_ui/ui/colors.palette:571` | Added `callCancelRipple: #c04646;`. |
| **Call UI & Controls** | Hidden Floating PiP Camera Preview | **Complete** | `calls/group/calls_group_viewport.cpp` | Viewport suppresses unnecessary floating webcam PiP overlay. |
| **Multi-Display** | DisplayCoordinator Multi-Monitor Support | **Complete** | `calls/group/calls_group_display_coordinator.h/.cpp` | Monitors `QScreen` changes, creates secondary `QWidget` windows with dedicated `Viewport`. |
| **Multi-Display** | Display Role Router | **Complete** | `calls/group/calls_group_display_coordinator.cpp:21-28,175-192` | Assigns `ActiveSpeaker`, `GridViewport`, `ChatStation`. |
| **Multi-Display** | Async Video Routing (`pinToScreen`, `unpinFromScreen`) | **Complete** | `calls/group/calls_group_display_coordinator.cpp:232-263` | Explicit routing of video feeds to secondary screens. |
| **Multi-Display** | Secondary Display ActiveSpeaker Polish | **Complete** | `calls/group/calls_group_display_coordinator.cpp:317-319` | Auto-stealing disabled on 2nd screen to avoid slot hijacking. |
| **Grid Layout & Pin** | Discrete Layout Presets (1x1, 2x2, 3x3) | **Complete** | `calls/group/calls_group_viewport.cpp:560-604` | Handled via `slotConstraint` (1, 4, 9). |
| **Grid Layout & Pin** | Dynamic Grid Solver | **Bug / Partial** | `calls/group/calls_group_viewport.cpp:578-584` | **Dead code**: `count == 2 && slotConstraint == 0` placed inside `if (fixedGridDim > 0)`, so 50/50 split is unreachable. |
| **Grid Layout & Pin** | Persistent Pin Slot Allocator | **Complete** | `calls/group/calls_group_viewport.cpp:1037-1048` | `_pinnedEndpoints` and `_pinnedSlots` track multi-pin slots. |
| **Grid Layout & Pin** | Pin to Grid Context Menu Action | **Missing / Incomplete** | `calls/group/calls_group_members.cpp:1432-1467`, `Telegram/Resources/langs/lang.strings:6463` | `lng_group_call_context_pin_to_grid` exists in strings, but not referenced in code. |
| **Floating Overlay** | Frameless Semi-Transparent Top-Most Window | **Partial** | `calls/group/calls_group_floating_overlay.h/.cpp` | Window flags, `Ctrl+Shift+T`, opacity controls, dragging, Escape dismiss implemented. |
| **Floating Overlay** | Chat Content & Dynamic Resize Binding | **Incomplete / Stub** | `calls/group/calls_group_floating_overlay.cpp:149-158` | `setupChatContent()` is an empty stub. `_messagesUi` is never instantiated. |
| **Participant Sidebar** | In-Call Sidebar Searchbar | **Complete** | `calls/group/calls_group_members.cpp:1978-2002` | `Ui::InputField` at top of sidebar filtering participants via `searchByQuery`. |
| **Participant Sidebar** | Alphabetical Sorting | **Complete** | `calls/group/calls_group_members.cpp:635-646` | `delegate()->peerListSortRows` with case-insensitive name comparison. |
| **Participant Sidebar** | Direct "Pin to Screen" & "Open Chat" | **Partial** | `calls/group/calls_group_members.cpp:1432-1534`, `Telegram/Resources/langs/lang.strings:6464` | `lng_group_call_open_chat` is in strings, but not used in context menu. |
| **Audio / Microphone** | Audio Lockout / Listen-Only Mode | **Complete** | `calls/group/calls_group_panel.cpp:245,673` | Microphone toggle disabled, mic tooltip suppressed. |
| **Main Menu** | Replace "Calls" Button with Submenu | **Partial** | `calls/calls_box_controller.cpp:930-994`, `window/window_main_menu.cpp:707` | `ShowCallsMenu` is implemented in `calls_box_controller.cpp` but not called in `window_main_menu.cpp`. |
| **Main Menu** | Wallet Menu Item | **Missing** | `window/window_main_menu.cpp:662-715` | Not added under My Profile. |
| **Context Menus** | Rich Tasks Checklist Toggling | **Complete** | `api/api_rich_tasks.cpp/.h`, `history/view/history_view_message.cpp:4521-4541` | Right-click/click task marker toggle via `api().richTasks()`. |
| **Backend / Engine** | WebRTC Jitter Clamping (A1) | **Partial** | `ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`, `MediaManager.cpp:364` | `audio_jitter_buffer_fast_accelerate` and `audio_jitter_buffer_min_delay_ms = 50` configured. |
| **Backend / Engine** | SQLite PRAGMA Tuning (C1) | **Not Applicable / Planned** | N/A | TDesktop uses `lib_storage` binary cache database; SQLite is not part of the standard storage pipeline. |

---

## 3. Deep Dive into Specific Incomplete/Broken Areas

### 3.1 `calls_group_floating_overlay.cpp` (Incomplete Stub & Style Issues)
**File**: `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`  
**Issues Observed**:
1. **Empty stub**:
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
2. **Indentation and formatting violations**: Function bodies for `FloatingOverlay::FloatingOverlay`, `show`, `hide`, `toggle`, `isVisible`, `keyPressEvent`, `mousePressEvent`, `mouseMoveEvent`, `paintEvent`, `resizeEvent`, `updateGeometry`, and `togglePassthrough` have 0 indentation (flush left).
3. **Literal violations**: `QStringLiteral("Chat")` at line 134 instead of `u"Chat"_q` or language key.
4. **Single-line comments**: Multiple bloat comments (`// Set up UI`, `// Set up shortcut`, `// Make semi-transparent`, `// Setup chat content`) violating `REVIEW.md` and `AGENTS.md`.

### 3.2 `calls_group_viewport.cpp` (Dead Code / Logic Bug in 50/50 Grid Solver)
**File**: `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:560-585`  
**Observation**:
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
**Impact**: When `slotConstraint == 0` (unconstrained dynamic auto-layout), `fixedGridDim` is 0. The execution skips the entire `if (fixedGridDim > 0)` block. Thus, `if (count == 2 && slotConstraint == 0)` is unreachable dead code. The 2-feed 50/50 case must be checked before or outside the `if (fixedGridDim > 0)` condition.

### 3.3 `calls_box_controller.cpp/.h` & `window_main_menu.cpp` (Unwired Calls Submenu)
**File**: `Telegram/SourceFiles/calls/calls_box_controller.cpp:930-994` and `Telegram/SourceFiles/window/window_main_menu.cpp:703-708`  
**Observation**:
`ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window)` was implemented to display group calls inline and provide a create call action.
However, in `window_main_menu.cpp`:
```cpp
		addAction(
			tr::lng_menu_calls(),
			{ &st::menuIconPhone }
		)->setClickedCallback([=] {
			::Calls::ShowCallsBox(controller);
		});
```
It directly invokes `ShowCallsBox(controller)` instead of wiring the button or right-click / submenu to `ShowCallsMenu`.

### 3.4 Missing Main Menu Wallet Entry
**File**: `Telegram/SourceFiles/window/window_main_menu.cpp:662-715`  
**Observation**:
The menu has "My Profile", bots, "New Group", "New Channel", "Contacts", "Calls", and "Saved Messages". There is no explicit "Wallet" entry with a `NEW` badge inserted under My Profile.

### 3.5 Context Menu "Pin to Grid" & "Open Chat"
**File**: `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1432-1534`  
**Observation**:
`lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` are defined in `lang.strings`, but `createRowContextMenu` only contains `pin_camera` / `pin_screen` (which calls `_call->pinVideoEndpoint(...)`) and standard `tr::lng_context_send_message(tr::now)`. It does not offer multi-monitor "Pin to Screen" (Screen 1 vs Screen 2) or "Pin to Grid".

---

## 4. REVIEW.md & AGENTS.md Compliance Findings

1. **Comments**:
   - `calls_group_floating_overlay.cpp`: Contains 6 single-line comments describing simple next steps.
   - `calls_group_display_coordinator.cpp`: Contains 4 single-line comments.
   - `calls_group_panel.cpp`: Contains comments on listen-only mode and tooltips.
   - *Recommendation*: Remove all descriptive single-line comments as mandated by `REVIEW.md` ("Do NOT write comments in code").
2. **String Literals**:
   - `QStringLiteral` is used in `calls_group_floating_overlay.cpp:134`, `calls_group_panel.cpp:862`, `calls_group_members.cpp:1990`.
   - *Recommendation*: Replace with `u"..."_q` or localized `tr::lng_*` keys.
3. **C++17 Namespaces and Includes**:
   - Headers and sources properly use nested `namespace Calls::Group {`.
   - Include ordering mostly complies with nested folders first and `styles/style_*.h` separated at the end.
4. **Memory Management & RAII**:
   - `calls_group_display_coordinator.cpp` properly uses `base::make_unique_q<QWidget>()` and `std::unique_ptr<Viewport>`.
   - `calls_group_floating_overlay.cpp` creates `_toggleShortcut = new QShortcut(...)` using raw `new` rather than RAII or member ownership.

---

## 5. Summary of Recommended Implementation Actions

1. **Finalize `FloatingOverlay`**:
   - Connect `FloatingOverlay::setupChatContent()` to `_panel->uiShow()` and `_panel->call()->messages()` to initialize `_messagesUi`.
   - Fix indentation and replace `QStringLiteral` with `u"..."_q`.
   - Remove redundant single-line comments.
2. **Fix 2-feed 50/50 Grid Solver**:
   - In `calls_group_viewport.cpp:577`, move the `if (count == 2 && slotConstraint == 0)` check above `if (fixedGridDim > 0)`.
3. **Wire `ShowCallsMenu` & Wallet in Main Menu**:
   - In `window_main_menu.cpp`, connect the Calls button / context menu to `Calls::ShowCallsMenu`.
   - Add the Wallet entry with `Ui::NewBadge` under "My Profile" if requested by fork specifications.
4. **Wire "Pin to Grid" & "Open Chat" in Group Call Context Menu**:
   - In `calls_group_members.cpp`, use `tr::lng_group_call_context_pin_to_grid` and `tr::lng_group_call_open_chat` to invoke `_displayCoordinator->pinToScreen(...)` and open in-meeting chat.
5. **Code Style & Cleanup**:
   - Strip single-line comments across `calls_group_*` files.
   - Ensure CRLF/LF line ending consistency.
