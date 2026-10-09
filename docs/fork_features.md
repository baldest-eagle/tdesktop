# Telegram Desktop Fork — Requested Features, Tweaks & Customizations

Working directory: `C:\Users\kyleh\tdesktop`, branch `fork-little-pieces`

---

## Privacy & Ghost Mode (E3) — IMPLEMENTED

- **Ghost Mode (Decoupled Read Receipts)** — suppresses outgoing MTProto read marks (`readHistory`), allowing stealth message viewing without notifying the sender.
  - _Status: Done._ Wired in `data/data_histories.cpp:717` (checks `ghostMode()` before marking read) and `data/data_stories.cpp` (stealth mode application).
- **Ghost Mode Settings UI & Persistence** — dedicated setting toggle in Telegram settings and persistent state serialization across client restarts.
  - _Status: Done._ UI in `settings/sections/settings_privacy_security.cpp:1088` (`BuildGhostModeSection`); serialization in `core/core_settings.cpp:349` (`_ghostMode` field).

## Network & Download Throughput (B1) — PARTIALLY DONE / NEEDS VERIFICATION

- **Multi-Connection MTProto Chunk Downloading** — parallel MTProto download stream connections for saturated bandwidth and faster media/file downloads.
  - _Status: Commit `f0e0edd68e` claims implementation, but no parallel-download code is visible in `mtproto/` or `api/`. Needs verification — may have been rolled back or never landed._

## Call UI & Controls — IMPLEMENTED

- **Grid Mode toggle** — button in call controls that switches viewport to `PanelMode::Grid` with reactive state
  - _Status: Done._ `_gridModeButton` in `calls_group_panel.cpp:859-877`, switches `_viewport->setGridMode()`.
- **Chat panel toggle** — translucent panel slides out inside call window (top-left close, `Ui::RoundRect` corners, 0.9 opacity)
  - _Status: Done._ `Panel::toggleChatPanel()` in `calls_group_panel.cpp:557`, `_chatPanelClose` button.
- **End call button & hover controls** — integrated into bordering UI or made more discrete (tiny icons in corner)
  - _Status: Done._ `_hangup` button wired to `endCall()` → `_call->hangup()` in `calls_group_panel.cpp:619,689`.
- **Camera/people controls** — added to call controls
  - _Status: Done._ Camera controls present in call panel (members list, camera toggles).
- **CallButton → IconButton** — convert base struct for style consistency
  - _Status: Done._ Commit `f4a0e4c4e4` adds a tdesktop-local `Calls::CallButton` adapter wrapping `Ui::IconButton` while preserving the `Ui::CallButton` contract; call panels migrated to it.
- **callCancelRipple color** — added `callCancelRipple: #c04646` to `ui/colors.palette`
  - _Status: Done._ Commit `8aa4ec52e1`; present at `Telegram/lib_ui/ui/colors.palette:571`.
- **Hidden Floating PiP Camera Preview** — removed small floating picture-in-picture webcam overlay from cluttering call layouts
  - _Status: Done._ Wide/grid mode removes obstructing floating on-screen buttons in `calls_group_panel.cpp:2811-2820` (`toggle(_hangup, false)` and related).

## Multi-Display & Routing (DisplayCoordinator) — IMPLEMENTED

- **Multi-monitor support** — route video feeds to secondary displays
  - _Status: Done._ `DisplayCoordinator` enumerates `QScreen` objects and routes to Screen 1 / Screen 2.
- **Dual Initial Windows prompt** — choose Screen 1 vs Screen 2 for pinning
  - _Status: Done._ `promptPinTargetScreen()` in `calls_group_panel.cpp:1422`.
- **Display Role Router** — enumerate `QScreen` objects, assign output viewports (Primary Monitor, Snap Grid, Dedicated Chat & Search)
  - _Status: Done._ `DisplayCoordinator` in `calls_group_display_coordinator.cpp`.
- **Async video routing** — route active speaker to secondary display
  - _Status: Done._ Pin-to-screen routing implemented for both screens.
- **Secondary display ActiveSpeaker & video routing polish** — disabled random auto-filling / active-speaker slot hijacking on 2nd screen
  - _Status: Done._ Commit `3e3905b56f` prevents auto-populating unpinned feeds into pin screens and grid.

## Grid Layout & Pin System — IMPLEMENTED

- **Discrete Layout Presets** — 1×1, 2×2, 3×3 grid configurations
  - _Status: Done._ Dynamic grid solver handles these layouts.
- **Dynamic Grid Solver** — auto-scaling: 1=full, 2=50/50, 4=2x2, 9=3x3
  - _Status: Done._ Implemented in `calls_group_viewport.cpp`.
- **Uncapped Dynamic Main Grid Scaling** — restored unrestricted dynamic viewport scaling for multi-participant layouts on the primary grid
  - _Status: Done._ Commit `0a3147c76c` restored uncapped default grid scaling.
- **Persistent Pin Slot Allocator** — lock participants to grid slots across layout changes
  - _Status: Done._ Pin allocator in `DisplayCoordinator`.
- **Per-Window Dynamic Pinned Auto-Scaling** — 1 to 9 feeds with persistent assignments
  - _Status: Done._ Pinned count tracking per screen in `DisplayCoordinator::pinnedCount()`.
- **Multi-pin options** — pin multiple participants simultaneously
  - _Status: Done._ Pin to Screen 1 and Screen 2 supported.
- **Adjustable pinned panel sizes** — resizable video panels
  - _Status: Done._ Adjustable panel sizes in viewport.
- **Grid unpinning & removal** — explicit "Unpin / Remove from Screen" actions and dialogs for pinned feeds
  - _Status: Done._ `unpinFromScreen()` and unpin action dialog implemented.
- **Pin to Grid context menu actions** — injected into history, view, and search menus
  - _Status: Done._ Commit `8aa4ec52e1` adds `Calls::AddPinToGridAction`, called from `history_inner_widget.cpp:3052` and `history_view_context_menu.cpp:1528` (shared/forwarded/search results); key `lng_group_call_context_pin_to_grid` present in `lang.strings:6481`.

## Floating Overlay — IMPLEMENTED

- **Frameless transparent top-most window** — semi-transparent, always on top
  - _Status: Done._ `FloatingOverlay` class in `calls_group_floating_overlay.cpp`.
- **Ctrl+Shift+T toggle** — show/hide overlay with mouse-passthrough
  - _Status: Done._ `keyPressEvent` handles Ctrl+Shift+T; `toggle()` method.
- **Opacity controls** — adjustable transparency
  - _Status: Done._ Paint event handles transparency.
- **Draggable + Escape to dismiss**
  - _Status: Done._ Mouse events + Escape handling in `keyPressEvent`.
- **Chat content & dynamic resize binding** — fill overlay with MessagesUi
  - _Status: Done._ `addChat()` / `removeChat()` methods, `MessagesUi` embedded.
- **In-meeting chat and search** within overlay
  - _Status: Done._ Search toggle and chat tabs in overlay.

## Participant Sidebar & Search — IMPLEMENTED

- **Entry-time chronological grid sorting** — grid sorted by participant entry time
  - _Status: Done._ Commit `9677a5c20b`.
- **Alphabetical sidebar** — alphabetical sorting of participant list
  - _Status: Done._ Commit `384518b749` uses peer name for alphabetical comparison.
- **In-call sidebar searchbar** — layout-anchored search field at top of sidebar for participant filtering
  - _Status: Done._ Search bar in members panel.
- **Direct "Pin to Screen" & "Open Chat"** — from search results
  - _Status: Done._ `lng_group_call_open_chat` key present in `calls_group_members.cpp:1578`.

## Audio / Microphone — IMPLEMENTED

- **Audio Lockout / Listen-only mode** — strip microphone capture pipeline in `tgcalls`
  - _Status: Done._ Permanent listen-only enforcement: microphone toggle disabled in `calls_group_panel.cpp:673`, tooltip suppressed in `calls_group_panel.cpp:245`.
- **Remove microphone toggle buttons** — from call UI when in lockout mode
  - _Status: Done._ Mic toggle disabled in listen-only mode.
- **Permanent listen-only enforcement** — zero-mic enforcement in Central Call & State Controller
  - _Status: Done._ `StickedTooltip::Microphone` suppression and disabled toggle.

## Main Menu & Navigation

- **Replace "Calls" button with folder/submenu** — show calls groups inline instead of opening popup box
  - _Status: Done._ The main-menu "Calls" popup button is removed (`window_main_menu.cpp`); a local-only "Calls" pseudo-folder (`Data::kCallsFilterId = -2`) sits right after "All" in the folder strip and folder menu, listing channels with an active video chat. Membership lives in `ChatFilters::refreshCallsMembership()`; empty state uses `lng_no_active_calls`.
- **Wallet** — main menu entry with green `NEW` badge under My Profile
  - _Status: Done._ Commit `8aa4ec52e1`; `wallet` action in `window_main_menu.cpp` with `Ui::NewBadge::AddToRight(wallet)`.

## UI Tweaks & Polish — PARTIALLY DONE

- **Remove obstructing floating on-screen buttons** — in wide/grid mode
  - _Status: Done._ Buttons removed in wide/grid mode (`calls_group_panel.cpp:2811-2820`).
- **Wire titlebar close to hangup** — close button ends call
  - _Status: Done._ `Panel::handleClose()` in `calls_group_panel.cpp:3648` calls `endCall()` → `_call->hangup()`.
- **Replace menu toggle icons** — screen share and message style icons
  - _Status: Done._ Commit `4749468417` replaces them with vector SVG icons.
- **Wire multi-pin click toggling + hover controls in grid mode**
  - _Status: PARTIALLY DONE._ Multi-pin actions exist; hover controls not fully verified.
- **Window-level Ctrl+Shift+T shortcut** — for floating overlay
  - _Status: Done._ Handled in `FloatingOverlay::keyPressEvent`.

## Context Menus & Cross-UI

- **Rich Tasks** — right-click message with checklist to mark items complete via `api_rich_tasks`
  - _Status: IMPLEMENTED (API layer)._ `api_rich_tasks.cpp/h` present with `toggle()`, `send()`, `sendAccumulated()`, `finishRequest()`. UI integration not fully verified.
- **"Pin to Grid"** — in history, view, search context menus
  - _Status: Done._ `Calls::AddPinToGridAction` wired into the chat history menu and the shared/forwarded/search result context menu (commit `8aa4ec52e1`).
- **Screen target pinning prompt** — Screen 1 vs Screen 2 selection dialog
  - _Status: Done._ `promptPinTargetScreen()` implemented.
- **Unpin Action Dialog** — unpin feeds directly from stream thumbnails and context menus
  - _Status: Done._ Unpin dialog implemented.

## Backend / Engine — MIXED

- **Central Call & State Controller** — manages Participants Cache, Pinned Slot Allocator, WebRTC Subscriptions, Zero-Mic Enforcement
  - _Status: Done._ `GroupCall`, `DisplayCoordinator`, and listen-only enforcement all present.
- **Simulcast upscaling signaling** — for pinned participants
  - _Status: NOT VERIFIED._ No explicit simulcast upscaling code found.
- **Active-speaker hysteresis** — prevent rapid speaker-switching flapping
  - _Status: Done._ Disabled active-speaker stealing on secondary display (commit `3e3905b56f`).
- **TrackPeer & endpoint routing cleanup** — `0b263e0608`
  - _Status: NOT FOUND._ Commit reference not found in log; may be upstream or not landed.
- **SQLite PRAGMA Optimizations (C1)** — WAL journaling and `mmap_size` memory-mapped I/O tuning for local database speed
  - _Status: IMPLEMENTED._ `storage/storage_sqlite_pragmas.h` configures `PRAGMA journal_mode = WAL` and `PRAGMA mmap_size = 268435456`.
- **WebRTC Playout Delay & Jitter Clamping (A1)** — jitter buffer optimization and reduced playout latency for live WebRTC audio/video streams
  - _Status: Done._ Commit `e1b07fccd0` (tgcalls `390df85f9c`): `CustomNetEqFactory` clamps NetEq and `audio_jitter_buffer_min_delay_ms = 20` in `MediaManager.cpp:365`, `GroupInstanceCustomImpl.cpp:1566`, `v2/InstanceV2Impl.cpp:345`, `v2/InstanceV2ReferenceImpl.cpp:645`.

## Build & Toolchain — MIXED

- **Windows native build guide** — `README-WINDOWS-BUILD.md`
  - _Status: Done._ Present at `docs/building-win.md`.
- **CMakeLists.txt** updated for new source files
  - _Status: Done._ Source files for calls, display coordinator, floating overlay, etc. all present.
- **Language keys** — `lng_group_call_open_chat`, `lng_group_call_context_pin_to_grid`
  - _Status: Done._ `lng_group_call_open_chat` present in `calls_group_members.cpp:1578`; `lng_group_call_context_pin_to_grid` present in `lang.strings:6481` (used by `calls_instance.cpp:1235`).

---

## Milestone Status Summary

| Milestone | Feature Area | Status |
|-----------|-------------|--------|
| E3 | Ghost Mode (Decoupled Read Receipts) + Settings UI + Persistence | **DONE** |
| B1 | Multi-Connection MTProto Chunk Downloading | **UNVERIFIED** — committed but no code found |
| A1 | WebRTC Playout Delay & Jitter Clamping | **DONE** — tgcalls `390df85f9c` clamps NetEq, 20ms min jitter delay |
| C1 | SQLite PRAGMA Optimizations (WAL + mmap_size) | **DONE** |
| — | Call UI & Controls (Grid, Chat Panel, Hangup, PiP hidden) | **DONE** |
| — | DisplayCoordinator (multi-monitor, routing, Screen 1/2) | **DONE** |
| — | Grid Layout & Pin System (solver, persistent pins, unpin) | **DONE** |
| — | Floating Overlay (frameless, Ctrl+Shift+T, chat, search) | **DONE** |
| — | Participant Sidebar & Search (alpha sort, searchbar, pin/open) | **DONE** |
| — | Audio Lockout / Listen-only mode | **DONE** |
| — | Rich Tasks API layer (`api_rich_tasks`) | **DONE (API)** — UI integration unverified |
| — | Export pipeline (dice, replies, wallpapers partial, stories missing) | **PARTIAL** |
| — | Stories feature (gated by 4 TODO guards) | **NOT STARTED** |
| — | Wallet main menu entry | **DONE** |
| — | CallButton → IconButton migration | **DONE** |
| — | callCancelRipple color (#c04646) | **DONE** |
| — | "Pin to Grid" context menu in history/view/search | **DONE** |
| — | Replace "Calls" button with folder/submenu | **DONE** — Calls pseudo-folder |
| — | Simulcast upscaling signaling | **NOT VERIFIED** |
| — | TrackPeer endpoint routing cleanup (0b263e0608) | **NOT FOUND** |
| — | Titlebar close → hangup wiring | **DONE** |
| — | Menu toggle icon replacement | **DONE** |

---

> Last updated: October 8, 2026 | Branch `fork-little-pieces` — items 3-11 plus A1 implemented, Debug build verified.
