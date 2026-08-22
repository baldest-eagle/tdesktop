# Telegram Desktop Fork — Comprehensive Specification & Features Survey Report

**Survey Target**: `c:\Users\kyleh\tdesktop` (Branch: `nightly`)  
**Primary Specification**: `docs/fork_features.md`, `README-WINDOWS-BUILD.md`, `REVIEW.md`, `AGENTS.md`  
**Date**: August 20, 2026  
**Agent**: Spec Miner (`.agents/spec_miner_survey/`)

---

## Executive Summary

This report provides an exhaustive survey and formal specification inventory of all custom features, tweaks, performance optimizations, UI enhancements, and backend engine components defined for the Telegram Desktop (`tdesktop`) fork.

All 57 distinct feature specifications across 13 functional categories have been probed, verified against the existing codebase, and cataloged with exact requirements, acceptance criteria, source references, constants, and edge case behaviors.

---

## Features Discovered

| # | Category | Feature | Description | Inputs / Triggers | Outputs / Observable Behavior | Error / Fallback Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| 1 | Privacy & Ghost Mode (E3) | Ghost Mode (Decoupled Read Receipts) | Suppresses outgoing MTProto read marks (`messages.readHistory`, `channels.readHistory`), allowing stealth message viewing without notifying sender. | User views unread messages while `ghostMode` is enabled. | `Histories::sendReadRequest` drops outgoing read requests (`state.willReadTill = 0; state.willReadWhen = 0; return;`). Sender sees messages as unread. | If disabled, standard MTProto `readHistory` is dispatched immediately. | `docs/fork_features.md:8`, `data/data_histories.cpp:717` |
| 2 | Privacy & Ghost Mode (E3) | Ghost Mode Settings UI & Persistence | Dedicated toggle in Privacy & Security settings, serialized across restarts in `Core::Settings`. | User toggles switch in Settings -> Privacy & Security. | `_ghostMode` serialized as `qint32` at end of binary settings stream; UI updates dynamically. | Unreadable / corrupted settings fallback to `false` (standard read receipt behavior). | `docs/fork_features.md:9`, `core/core_settings.cpp:464`, `settings/sections/settings_privacy_security.cpp:1093` |
| 3 | Network & Download (B1) | Multi-Connection MTProto Chunk Downloading | Saturated bandwidth downloading utilizing parallel DC session connections. | File/media download initiation in `DownloadManagerMtproto`. | Spawns up to `kMaxSessionsCount = 16` concurrent DC connections requesting `kDownloadPartSize = 128 KB` chunks up to `kMaxWaitedInSession = 4 MB` window. | Failed parts trigger fallback to single connection, CDN hash re-verification, or DC reconnect. | `docs/fork_features.md:12`, `storage/download_manager_mtproto.h:26`, `storage/download_manager_mtproto.cpp:24-30` |
| 4 | Call UI & Controls | Grid Mode Toggle | Control button to toggle between speaker/presentation view and multi-participant grid. | User clicks Grid button in group call control bar. | Switches `PanelMode` between `PanelMode::Wide` and `PanelMode::Grid`; triggers `_viewport->setGridMode(bool)`. | If single participant, remains in full-tile presentation view. | `docs/fork_features.md:15`, `calls/group/calls_group_panel.cpp:869`, `calls/group/calls_group_common.h:136` |
| 5 | Call UI & Controls | In-Call Chat Panel Slide-Out | Slide-out panel for text chat inside the active call window. | User clicks Chat button in group call control bar. | Translucent side panel with `Ui::RoundRect` corners (0.9 opacity) slides in smoothly without blocking call canvas. | ESC or top-left close button slides panel back out. | `docs/fork_features.md:16`, `calls/group/calls_group_messages_ui.cpp` |
| 6 | Call UI & Controls | End Call Button & Hover Controls | Streamlined hangup button and auto-hiding hover controls. | Hovering over call window / clicking hangup. | Hover bar displays control buttons; auto-hides after inactivity timeout. Hangup terminates call. | Unhandled mouse exits reset hover fade animation immediately. | `docs/fork_features.md:17`, `calls/group/calls_group_panel.cpp`, `calls/calls_panel.cpp` |
| 7 | Call UI & Controls | Camera & Participant Bar Controls | Dedicated buttons in toolbar for video toggling and participant drawer. | User clicks Camera or Participants icon. | Toggles video capture / reveals sidebar. | Disabled with explanatory tooltip if video is disabled by admin. | `docs/fork_features.md:18`, `calls/group/calls_group_panel.cpp` |
| 8 | Call UI & Controls | CallButton to IconButton Base Migration | Converted `CallButton` style primitive for unified style system compliance. | Codegen parsing `calls.style`. | Generated C++ style structs inherit unified `IconButton` styling. | Fallback to default button styles if field is omitted. | `docs/fork_features.md:19`, `README-WINDOWS-BUILD.md:64`, `calls/calls.style:17` |
| 9 | Call UI & Controls | callCancelRipple Palette Color | Red ripple accent color `#c04646` for destructive call actions. | User clicks cancel / hangup button with ripple effect. | Renders `#c04646` animated circular ripple on click origin. | Defaults to `windowBgRipple` if absent. | `docs/fork_features.md:20`, `Telegram/lib_ui/ui/colors.palette:571` |
| 10 | Call UI & Controls | Hidden Floating PiP Camera Preview | Cleaned call layout by removing intrusive floating webcam PiP overlay. | User enables personal webcam during group call. | Local camera feed is integrated into standard grid / sidebar tile without rendering a floating PiP on top of other feeds. | If grid is full, self-tile resides in sidebar. | `docs/fork_features.md:21`, `calls/group/calls_group_panel.cpp` |
| 11 | Multi-Display (DisplayCoordinator) | Multi-Monitor Stage Window Support | Route video feeds to secondary displays / external monitors. | User selects secondary display in multi-monitor environment. | Spawns dedicated stage window on target `QScreen` via `DisplayCoordinator`. | Single-monitor systems hide multi-display options. | `docs/fork_features.md:24`, `calls/group/calls_group_display_coordinator.h:51` |
| 12 | Multi-Display (DisplayCoordinator) | Dual Initial Windows Prompt | Target selection prompt (Screen 1 vs Screen 2) on multi-monitor pin. | Pin action triggered when `displayCount() > 1`. | Displays modal choice asking which screen should receive the feed. | Canceling dialog aborts pinning action. | `docs/fork_features.md:25`, `calls/group/calls_group_display_coordinator.cpp:216` |
| 13 | Multi-Display (DisplayCoordinator) | Display Role Router | Configures displays for `ActiveSpeaker`, `GridViewport`, `ChatStation`, or `None`. | Setting display role in coordinator. | Adapts window geometry, viewport rendering, and chrome based on assigned role. | Fallback to `DisplayRole::None` if screen disconnected. | `docs/fork_features.md:26`, `calls/group/calls_group_display_coordinator.h:37-49` |
| 14 | Multi-Display (DisplayCoordinator) | Async Video Stream Routing | Asynchronous video feed dispatch to auxiliary display pipelines. | Video frame arrives from tgcalls SFU. | Frame rendered in secondary display viewport without blocking main UI event loop. | Dropped frames logged; pipeline recovers on keyframe. | `docs/fork_features.md:27`, `calls/group/calls_group_display_coordinator.cpp:232` |
| 15 | Multi-Display (DisplayCoordinator) | Secondary Display Active-Speaker Isolation | Prevent random speaker hijacking on secondary screen. | Active speaker changes in call. | `updateAudioLevels` on secondary screens is guarded so only explicitly pinned streams appear. | No fallback hijacking permitted. | `docs/fork_features.md:28`, `calls/group/calls_group_display_coordinator.cpp:317` |
| 16 | Grid Layout & Pin System | Discrete Layout Presets (1x1, 2x2, 3x3) | Standard symmetrical tile layouts for fixed participant counts. | Participant count equals 1, 4, or 9. | Tiles lay out in exact 1x1, 2x2, or 3x3 grids with uniform aspect ratios. | Non-square counts use dynamic solver. | `docs/fork_features.md:31`, `calls/group/calls_group_viewport.cpp:767` |
| 17 | Grid Layout & Pin System | Dynamic Grid Solver | Auto-scaling solver: 1=full, 2=50/50, 3=2+1, 4=2x2, 5..6=3x2, etc. | Changing active video tile count. | Solves optimal row/column distribution minimizing letterboxing. | Falls back to single column in narrow mode. | `docs/fork_features.md:32`, `calls/group/calls_group_viewport.cpp:850` |
| 18 | Grid Layout & Pin System | Uncapped Dynamic Main Grid Scaling | Dynamic viewport scaling supporting unrestricted participant counts. | Scaling call window or adding participants. | Computes smooth geometry without artificial tile count caps. | Minimum tile dimension enforced (`st::groupCallNarrowVideoHeight`). | `docs/fork_features.md:33`, `calls/group/calls_group_viewport.cpp:767-830` |
| 19 | Grid Layout & Pin System | Persistent Pin Slot Allocator | Locks pinned feeds to specific grid slots across layout mutations. | User pins participant to grid slot. | Pinned participant stays locked in slot; non-pinned flows around. | Removing pinned peer compacts remaining slots. | `docs/fork_features.md:34`, `calls/group/calls_group_viewport.h:242` |
| 20 | Grid Layout & Pin System | Per-Window Dynamic Pinned Auto-Scaling | Auto-scales 1 to 9 pinned feeds to fill available window canvas. | Resizing stage window containing 1..9 pinned feeds. | Tiles rescale proportionally while maintaining locked order. | Oversized counts wrap to scrollable viewport. | `docs/fork_features.md:35`, `calls/group/calls_group_viewport.cpp:1037` |
| 21 | Grid Layout & Pin System | Multi-Pin Capability | Supports simultaneously pinning multiple participants. | User pins second/third participant. | Viewport allocates multiple hero/featured slots. | Unpinning all returns to active speaker auto-flow. | `docs/fork_features.md:36`, `calls/group/calls_group_viewport.h:96` |
| 22 | Grid Layout & Pin System | Adjustable Pinned Panel Sizes | Resizable splitters / sizing for featured panels. | User drags panel border or resizes call window. | Adjusts tile bounding rectangles dynamically. | Bound to min/max constraints (240px to 100% canvas). | `docs/fork_features.md:37`, `calls/group/calls_group_viewport.cpp:916` |
| 23 | Grid Layout & Pin System | Grid Unpinning & Removal Actions | Unpin action and dialog to remove feeds from pinned stage. | User clicks Unpin button on tile or in context menu. | `Viewport::togglePin(endpoint, false)` removes feed from pinned list. | If not pinned, action is disabled. | `docs/fork_features.md:38`, `calls/group/calls_group_viewport.cpp:1043` |
| 24 | Grid Layout & Pin System | Pin to Grid Context Menu Actions | Injects "Pin to grid" action into history, view, and participant menus. | Right-clicking user row or video tile. | Adds `lng_group_call_context_pin_to_grid` item to popup menu. | Hidden if user has no active video/screencast. | `docs/fork_features.md:39`, `calls/group/calls_group_menu.cpp`, `Telegram/Resources/langs/lang.strings:6463` |
| 25 | Floating Overlay | Frameless Transparent Top-Most Overlay | Semi-transparent floating companion window for calls. | Triggered via shortcut or menu toggle. | Frameless, always-on-top window created with `Qt::WindowStaysOnTopHint | Qt::WA_TranslucentBackground`. | Position clamped to screen bounding box on resize. | `docs/fork_features.md:42`, `calls/group/calls_group_floating_overlay.h:26` |
| 26 | Floating Overlay | Ctrl+Shift+T Keyboard Toggle | Shortcut to show/hide floating overlay. | Pressing `Ctrl+Shift+T`. | Toggles `FloatingOverlay::toggle()`. | Ignored if no call is active. | `docs/fork_features.md:43`, `calls/group/calls_group_floating_overlay.cpp:38` |
| 27 | Floating Overlay | Opacity Adjustment via Ctrl+Wheel | Dynamically adjusts overlay transparency from 20% to 100%. | `Ctrl + MouseWheel` over overlay. | Changes opacity by ±0.05 step (`0.20f` to `1.0f`); updates `setWindowOpacity`. | Clamped at minimum 0.20f to prevent invisible lost windows. | `docs/fork_features.md:44`, `calls/group/calls_group_floating_overlay.cpp:100-112` |
| 28 | Floating Overlay | Draggable Canvas & Escape to Dismiss | Left-click drag anywhere to reposition; `Esc` to close. | Mouse drag or `Esc` keypress. | Translates geometry by drag delta; hides on `Esc`. | Constrained within visible screen workspace boundaries. | `docs/fork_features.md:45`, `calls/group/calls_group_floating_overlay.cpp:70-90` |
| 29 | Floating Overlay | Embedded Chat & Dynamic Resize | Renders active call messages UI inside overlay. | Resizing overlay window. | `MessagesUi` resizes and repaints chat stream inside container. | Shows empty placeholder if call has no chat. | `docs/fork_features.md:46`, `calls/group/calls_group_floating_overlay.cpp:128` |
| 30 | Floating Overlay | In-Meeting Chat Search | Filter and search messages directly from floating overlay. | User enters query in overlay search box. | Highlights matching chat items in real time. | Shows "No results" if query doesn't match. | `docs/fork_features.md:47` |
| 31 | Participant Sidebar & Search | Chronological Entry-Time Grid Sorting | Arranges active grid video tiles by user join timestamp. | Participant joins call. | Earlier joiners take leading positions in grid tile order. | Tied join times break tie by PeerId. | `docs/fork_features.md:50`, `calls/group/calls_group_members.cpp` |
| 32 | Participant Sidebar & Search | Alphabetical Sidebar Sorting | Sorts participant list in sidebar alphabetically (A-Z). | Participant list updates. | `peerListSortRows` orders rows via `QString::compare(nameA, nameB, Qt::CaseInsensitive)`. | Active speakers / raised hands sorted at top before alphabetical group. | `docs/fork_features.md:51`, `calls/group/calls_group_members.cpp:635` |
| 33 | Participant Sidebar & Search | In-Call Sidebar Search Bar | Anchored search bar at top of participant drawer. | User types name/username in sidebar search. | `searchByQuery` filters participant rows in real time. | Empty query restores full alphabetical list. | `docs/fork_features.md:52`, `calls/group/calls_group_members.cpp:1978` |
| 34 | Participant Sidebar & Search | Search Results Quick Actions | "Pin to Screen" and "Open Chat" buttons directly on search rows. | User hovers/clicks search result row. | Direct action triggers stage pinning or chat navigation (`lng_group_call_open_chat`). | Disabled if participant left call. | `docs/fork_features.md:53`, `calls/group/calls_group_members.cpp`, `Telegram/Resources/langs/lang.strings:6464` |
| 35 | Audio / Microphone | Audio Lockout / Listen-Only Mode | Disables audio capture pipeline in `tgcalls` for strict listen-only mode. | Lockout mode activated. | `tgcalls` does not open microphone audio device or create audio send channel. | Audio receive channel remains active. | `docs/fork_features.md:56`, `ThirdParty/tgcalls/tgcalls/MediaManager.cpp` |
| 36 | Audio / Microphone | Microphone Controls Removal | Hides mic/mute buttons from call UI in lockout mode. | Lockout mode active. | Call bottom bar omits mute button or displays immutable listen-only badge. | Unmute requests blocked with notification. | `docs/fork_features.md:57`, `calls/group/calls_group_panel.cpp:2873` |
| 37 | Audio / Microphone | Permanent Listen-Only Invariant | Central controller enforces zero-mic transmission invariant. | Any attempt to send audio upstream. | Controller drops outgoing audio descriptors and asserts zero capture. | Prevents accidental audio leakage. | `docs/fork_features.md:58`, `calls/group/calls_group_call.cpp` |
| 38 | Main Menu & Navigation | Calls Submenu in Main Menu | Replaces simple "Calls" box launcher with structured popup menu. | User clicks "Calls" in Telegram main menu. | `ShowCallsMenu` opens menu with active group calls, Start Call, and Call History items. | If no active group calls, lists standard call options. | `docs/fork_features.md:61`, `calls/calls_box_controller.cpp:930`, `window/window_main_menu.cpp:707` |
| 39 | Main Menu & Navigation | Wallet Entry with NEW Badge | Main menu entry under My Profile for TON wallet with green badge. | User opens Telegram main menu. | Displays Wallet menu item with green `NEW` badge below "My Profile". | Clicking navigates to Wallet section or opens TON wallet mini-app. | `docs/fork_features.md:62`, `window/window_main_menu.cpp:670` |
| 40 | UI Tweaks & Polish | Wide/Grid Mode Obstructing Button Cleanup | Removes overlapping buttons in wide/grid video mode. | Entering wide or grid layout mode. | Repositions or hides floating controls overlapping video tiles. | Re-shown when switching back to compact mode. | `docs/fork_features.md:65`, `calls/group/calls_group_panel.cpp` |
| 41 | UI Tweaks & Polish | Titlebar Close Wired to Hangup | Window close button triggers call hangup/leave. | User clicks window close [X] button. | Closes call session, sends leave packet, closes window. | Prompts confirmation if user is group call host. | `docs/fork_features.md:66`, `calls/group/calls_group_panel.cpp`, `calls/calls_panel.cpp` |
| 42 | UI Tweaks & Polish | Screen Share & Message Toggle Icons | Vector icon polish for screen sharing and message panel toggles. | Call control toolbar rendering. | Renders crisp updated icons matching `calls.style`. | Fallbacks to default monochrome icons. | `docs/fork_features.md:67`, `calls/calls.style:941` |
| 43 | UI Tweaks & Polish | Multi-Pin Hover Controls | Hovering video tiles reveals pin icon for single-click toggling. | Mouse hover over any video tile. | Displays pin button in tile header; clicking toggles pinned state. | Non-hover state hides controls to keep video clean. | `docs/fork_features.md:68`, `calls/group/calls_group_viewport.cpp:758` |
| 44 | UI Tweaks & Polish | Window-Level Ctrl+Shift+T Key Handler | Window-level shortcut binding for floating overlay. | User presses `Ctrl+Shift+T` in call window. | Toggles floating companion overlay. | Ignored if focus is in text input. | `docs/fork_features.md:69`, `calls/group/calls_group_panel.cpp` |
| 45 | Context Menus & Cross-UI | Rich Tasks (Checklist Items) | Interactive markdown task list items toggled via right-click / click. | User toggles checklist task in rich message. | `Api::RichTasks::toggle` modifies `Iv::RichPage`, queues `EditRichMessage` with 1000ms debounce. | Aborts if message does not permit editing. | `docs/fork_features.md:72`, `api/api_rich_tasks.h:30`, `api/api_rich_tasks.cpp:40` |
| 46 | Context Menus & Cross-UI | Cross-UI "Pin to Grid" Actions | "Pin to Grid" action available across history, view, and search menus. | Right-clicking video stream anywhere. | Injects `lng_group_call_context_pin_to_grid` into context menu. | Hidden if stream is already pinned on current display. | `docs/fork_features.md:73`, `history/view/history_view_context_menu.cpp` |
| 47 | Context Menus & Cross-UI | Screen Target Pinning Prompt | Prompt to choose Screen 1 vs Screen 2 for multi-monitor pinning. | User selects "Pin to Screen" with multiple displays connected. | Shows dialog to pick target monitor. | Default to Screen 2 for stage presentations. | `docs/fork_features.md:74`, `calls/group/calls_group_menu.cpp` |
| 48 | Context Menus & Cross-UI | Stream Thumbnail Unpin Action Dialog | Direct unpin options on stream thumbnails and context menus. | Right-clicking pinned thumbnail. | Presents "Unpin from Screen" action. | Confirms unpin and re-tiles remaining streams. | `docs/fork_features.md:75`, `calls/group/calls_group_viewport.cpp:1043` |
| 49 | Backend / Engine | Central Call & State Controller | Centralized controller for participant cache, slot allocator, subscriptions. | Group call events, participant state changes. | Maintains synchronized state between UI, WebRTC media engine, and signaling. | Recovers state on network reconnection. | `docs/fork_features.md:78`, `calls/group/calls_group_call.h`, `calls/calls_instance.h` |
| 50 | Backend / Engine | Simulcast Upscaling Signaling | Quality requests for pinned / full-sized participants. | Video tile resized or pinned (`min >= 540px` -> Full, `min >= 240px` -> Medium). | Fires `VideoQualityRequest` to SFU requesting high-bitrate stream layer. | Drops back to Thumbnail when tile is small/hidden. | `docs/fork_features.md:79`, `calls/group/calls_group_viewport.cpp:920-940` |
| 51 | Backend / Engine | Active-Speaker Hysteresis | Hysteresis damping to prevent rapid speaker-switching flapping. | Fast alternating speech energy levels between participants. | Holds active speaker assignment (`_speakerThreshold = 0.05`, `_speakerHoldFrames`) before switching. | Prevents jarring visual tile bouncing. | `docs/fork_features.md:80`, `calls/group/calls_group_display_coordinator.h:116-118` |
| 52 | Backend / Engine | TrackPeer & Endpoint Routing Cleanup | Clean endpoint-to-peer mapping and track lifecycle management. | Participant streams start/stop. | Tracks properly mapped to `VideoEndpoint` structs; avoids dangling track pointers (`0b263e0608`). | Cleans up GPU textures on track destruction. | `docs/fork_features.md:81`, `calls/group/calls_group_common.h` |
| 53 | Backend / Engine (C1) | SQLite PRAGMA Optimizations (C1) | WAL journaling (`PRAGMA journal_mode = WAL;`) and `mmap_size` memory-mapped I/O tuning (`PRAGMA mmap_size = 268435456;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA cache_size = -64000;`) for database throughput. | Local storage database connection initialization. | Executes PRAGMA tuning on database open; enables concurrent read/write and memory-mapped page cache. | Graceful fallback if filesystem does not support WAL/mmap. | `docs/fork_features.md:82`, `ORIGINAL_REQUEST.md:11`, `storage/localstorage.cpp` |
| 54 | Backend / Engine (A1) | WebRTC Playout Delay & Jitter Clamping (A1) | Jitter buffer optimization and clamped playout latency (`audio_jitter_buffer_min_delay_ms = 50;`, `audio_jitter_buffer_fast_accelerate = true`). | WebRTC voice/video channel creation in `tgcalls`. | Configures cricket `AudioOptions` with fast accelerate and 50ms min delay for minimal voice latency. | Network jitter spikes handled by WebRTC NetEq fallback. | `docs/fork_features.md:83`, `ORIGINAL_REQUEST.md:11`, `ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`, `MediaManager.cpp:364` |
| 55 | Build & Toolchain | Windows Native Build Guide | Documented steps and tweaks for native MSVC 2022 building. | Developer building on Windows without Docker. | Outlines `prepare.py` adjustments, `-j1` memory safety flag, and MSVC build environment. | Catches common MSYS2/PATH and PCH memory errors. | `docs/fork_features.md:86`, `README-WINDOWS-BUILD.md:1` |
| 56 | Build & Toolchain | CMakeLists.txt Source Synchronization | All custom fork sources registered in `Telegram/CMakeLists.txt`. | CMake configuration step. | Targets build with all fork units linked (`calls_group_display_coordinator`, `calls_group_floating_overlay`, `calls_box_controller`, `api_rich_tasks`). | Missing source registrations produce link errors. | `docs/fork_features.md:87`, `Telegram/CMakeLists.txt:456-459` |
| 57 | Build & Toolchain | Fork Localization Language Keys | Complete set of localization keys for fork features. | Language pack loading. | `lng_group_call_open_chat`, `lng_group_call_context_pin_to_grid`, `lng_settings_ghost_mode`, `lng_settings_ghost_mode_about`. | Falls back to English strings if untranslated. | `docs/fork_features.md:88`, `Telegram/Resources/langs/lang.strings:6463-6464` |

---

## Edge Cases & Failure Modes Observed

| # | Feature | Input / Condition | Observed / Required Behavior |
|---|---|---|---|
| 1 | Ghost Mode | User marks chat as read manually or scrolls past new messages | When `ghostMode()` is true, `state.willReadTill = 0` drops the request. Local UI updates read status locally for user convenience, but server/sender never receives `readHistory` MTProto update. |
| 2 | Ghost Mode Serialization | Old client data reading Core Settings without `_ghostMode` field | Binary stream check `!stream.atEnd()` guards the `ghostMode` read. Older profiles default cleanly to `false` without stream offset corruption. |
| 3 | Multi-Connection MTProto | Connection drops / DC timeout during parallel chunk download | `DownloadManagerMtproto` removes the failing session index via `removeSession(dcId)`, adjusts `requested` counters, and redistributes pending chunks to surviving sessions. |
| 4 | DisplayCoordinator | Secondary monitor unplugged while stage window is active | `DisplayCoordinator::updateScreens()` detects display removal, tears down auxiliary window, and moves all pinned feeds back to primary grid. |
| 5 | DisplayCoordinator Active-Speaker | Audio energy spikes on secondary display | `updateAudioLevels` is a no-op for secondary windows. Only explicitly pinned participant feeds appear on the 2nd display, preventing active-speaker auto-stealing. |
| 6 | Floating Overlay Opacity | User scrolls Ctrl+Wheel down repeatedly | Clamped at minimum `0.20f` opacity to prevent the window from becoming completely invisible and untargetable. Clamped at maximum `1.0f`. |
| 7 | Floating Overlay Mouse Passthrough | Click-through mode enabled | `Qt::WA_TransparentForMouseEvents` set to `true`. Mouse events pass directly through to underlying desktop/windows. Dismissible via `Ctrl+Shift+T`. |
| 8 | Grid Solver | Odd number of participants (e.g. 3 or 5) | `countWide` arranges tiles symmetrically: for 3 tiles, allocates 2 on top row and 1 centered on bottom row; computes tile bounding rectangles to avoid distorted aspect ratios. |
| 9 | Multi-Pin Viewport | User pins 10+ participants | Pinned slot allocator scales down tile geometries up to 9 visible slots; remaining pinned tiles become accessible via vertical scrolling within viewport. |
| 10 | Rich Tasks Debounce | Rapid multiple checkbox clicks in checklist | `RichTasks` batches all local edits into `Iv::RichPage` and resets debounce timer `_sendTimer.callOnce(kSendDelay)` (1000ms). Only one `EditRichMessage` RPC is sent for the entire batch. |
| 11 | Audio Lockout | Admin grants microphone permission to locked-out user | Zero-mic invariant in controller blocks capture device initialization; UI remains in listen-only mode regardless of server-side permissions. |
| 12 | SQLite PRAGMA Tuning (C1) | Read-only filesystem / network share where WAL shared memory (`.shm`) fails | SQLite database connection attempts WAL mode; if `PRAGMA journal_mode=WAL` fails, gracefully falls back to `TRUNCATE` or `DELETE` mode without failing database initialization. |
| 13 | WebRTC Jitter Clamping (A1) | Severe network packet loss / bursty latency | With `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50`, WebRTC NetEq fast-accelerates audio playout after bursts to catch up, minimizing voice lag while WebRTC PLC (packet loss concealment) conceals dropped frames. |
| 14 | Calls Box Submenu | Main menu clicked while call is already active | Main menu Calls submenu displays active call banner with "Return to Call" option in addition to Start Call and Call History. |

---

## Detailed Category Analysis & Verification Reference

### Category A: Privacy & Ghost Mode (E3)
- **Primary Source Files**:
  - `Telegram/SourceFiles/core/core_settings.h` (`ghostMode()`, `ghostModeValue()`, `_ghostMode`)
  - `Telegram/SourceFiles/core/core_settings.cpp` (Serialization in `writeSettings`, `readSettings`)
  - `Telegram/SourceFiles/data/data_histories.cpp` (Suppression in `sendReadRequest`)
  - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp` (Toggle UI builder)
- **Acceptance Invariants**:
  - Outgoing `messages.readHistory` and `channels.readHistory` must NOT be dispatched when `ghostMode()` is true.
  - Serialization order must remain at the very end of the binary stream to ensure forward/backward compatibility.

### Category B: Network & Download Throughput (B1)
- **Primary Source Files**:
  - `Telegram/SourceFiles/storage/download_manager_mtproto.h` (`kDownloadPartSize`, `kMaxSessionsCount`)
  - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp` (`kMaxWaitedInSession`, session allocation)
  - `Telegram/SourceFiles/mtproto/dedicated_file_loader.h` / `.cpp`
- **Constants**:
  - `kDownloadPartSize = 131072` (128 KB)
  - `kMaxSessionsCount = 16`
  - `kMaxWaitedInSession = 32 * kDownloadPartSize = 4194304` (4 MB)

### Category C: Calls UI, Viewport & Grid System
- **Primary Source Files**:
  - `Telegram/SourceFiles/calls/group/calls_group_common.h` (`PanelMode::Grid`, `VideoQuality`)
  - `Telegram/SourceFiles/calls/group/calls_group_panel.h` / `.cpp` (Mode management, UI buttons)
  - `Telegram/SourceFiles/calls/group/calls_group_viewport.h` / `.cpp` (Grid solver, tile layout, pinning)
  - `Telegram/SourceFiles/calls/group/calls_group_viewport_tile.h` / `.cpp`
  - `Telegram/SourceFiles/calls/calls.style` (`CallButton` struct, button dimensions)
  - `Telegram/lib_ui/ui/colors.palette` (`callCancelRipple: #c04646`)

### Category D: Multi-Display Stage Routing (DisplayCoordinator)
- **Primary Source Files**:
  - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h`
  - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp`
- **Roles & Routing**:
  - `DisplayRole::ActiveSpeaker`, `DisplayRole::GridViewport`, `DisplayRole::ChatStation`, `DisplayRole::None`.
  - Independent stage windows attached to separate `QScreen` targets.
  - Anti-hijack protection: `updateAudioLevels` is a no-op on secondary displays.

### Category E: Floating Overlay
- **Primary Source Files**:
  - `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
  - `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
- **Specifications**:
  - Window flags: `Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint`
  - Attributes: `Qt::WA_TranslucentBackground`, `Qt::WA_ShowWithoutActivating`
  - Shortcut: `Ctrl+Shift+T`
  - Opacity: 0.20 to 1.00 (step 0.05) via `Ctrl+Wheel`
  - Chat integration: Embedded `MessagesUi` layout

### Category F: Sidebar & In-Call Search
- **Primary Source Files**:
  - `Telegram/SourceFiles/calls/group/calls_group_members.h` / `.cpp`
- **Features**:
  - Case-insensitive alphabetical sorting via `peerListSortRows`
  - Anchored search bar widget `_searchWrap` with `_searchField`
  - Filtering via `searchByQuery(const QString &query)`

### Category G: Audio Lockout & Zero-Mic Enforcement
- **Primary Source Files**:
  - `Telegram/SourceFiles/calls/group/calls_group_call.h` / `.cpp`
  - `Telegram/SourceFiles/calls/calls_controller_webrtc.cpp`
  - `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp`
- **Invariants**:
  - Audio capture device is omitted from initialization.
  - Zero audio frames transmitted over RTP.

### Category H: Main Menu Navigation & Calls Submenu
- **Primary Source Files**:
  - `Telegram/SourceFiles/window/window_main_menu.cpp`
  - `Telegram/SourceFiles/calls/calls_box_controller.h` / `.cpp` (`ShowCallsMenu`, `GroupCalls::ListController`)
- **Features**:
  - Main menu Calls button opens popup submenu `ShowCallsMenu` listing active group calls, Start Call, and History.
  - Main menu Wallet item positioned under My Profile with green `NEW` badge.

### Category I: Rich Tasks & Markdown Checklists
- **Primary Source Files**:
  - `Telegram/SourceFiles/api/api_rich_tasks.h` / `.cpp`
  - `Telegram/SourceFiles/history/view/history_view_context_menu.cpp`
- **Features**:
  - `Api::RichTasks::toggle` parses `Iv::RichPage`, toggles item state, schedules debounced `EditRichMessage` (1000ms delay).

### Category J: Backend Engine & Performance Optimizations
- **C1: SQLite PRAGMA Optimizations**:
  - `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for non-blocking concurrent reads and writes)
  - `PRAGMA mmap_size = 268435456;` (256 MB memory-mapped I/O)
  - `PRAGMA synchronous = NORMAL;`
  - `PRAGMA cache_size = -64000;` (64 MB page cache)
  - `PRAGMA temp_store = MEMORY;`
- **A1: WebRTC Jitter Clamping & Latency Optimization**:
  - `audio_jitter_buffer_fast_accelerate = true;`
  - `audio_jitter_buffer_min_delay_ms = 50;` (Clamped low-latency playout buffer)
  - Opus codec config: clockrate 48000 Hz, channels 2, `kCodecParamUseInbandFec = 1`, `kCodecParamPTime = 20` (or `120` for conference).

### Category K: Code Style & Quality Standards Compliance (REVIEW.md)
- **Style Rules to Enforce across All Fork Code**:
  1. No single-line comments in implementation files.
  2. Empty line before closing brace in all `class` definitions with access specifiers.
  3. Operators placed at the beginning of continuation lines in multi-line expressions (`&&`, `||`, `;`).
  4. Minimize type checks: direct cast over `is` + `as` (`if (const auto user = peer->asUser())`).
  5. Always initialize basic type variables (`= 0`, `= false`, `= nullptr`).
  6. Use `tr::` projections for `TextWithEntities` (`tr::bold`, `tr::rich`, `tr::marked`).
  7. Multi-line function calls: one argument per line.
  8. Avoid `std::optional::value()`; use `value_or()` or `operator*`.
  9. Include order: alphabetical, nested folders first, styles (`styles/style_*.h`) last.
  10. C++17 nested namespaces (`namespace Calls::Group {`).
  11. Use `base::take` for read-and-reset operations.
  12. RAII cleanup via `gsl::finally` or RAII guards.
  13. No `Q_OS_LINUX` in new code; use `!defined Q_OS_WIN && !defined Q_OS_MAC` or `Platform::IsLinux()`.
  14. UTF-8 without BOM encoding; LF line endings for git repository tracking.
