# Project: Telegram Desktop (tdesktop) Fork Audit & Feature Completion

## Architecture
Telegram Desktop is a Qt-based desktop messaging client using MTProto, WebRTC (`tgcalls`), and custom UI widgets (`lib_ui`, `td_ui`).
The fork introduces custom enhancements across multiple subsystems:
1. **Calls UI & Viewport**: Group call viewport grid solving (`calls_group_viewport`), floating transparent companion overlay (`calls_group_floating_overlay`), multi-display routing (`calls_group_display_coordinator`), and member search/sorting (`calls_group_members`).
2. **Navigation & Menus**: Calls submenu integration (`calls_box_controller`, `window_main_menu`), Wallet entry with NEW badge, and privacy controls (`settings_privacy_security`).
3. **Core & Network**: Ghost Mode read receipt suppression (`data_histories`, `core_settings`), multi-connection MTProto chunk downloading (`download_manager_mtproto`), Rich Tasks interactive checklists (`api_rich_tasks`).
4. **Backend Engine**: WebRTC playout jitter clamping A1 (`tgcalls`), SQLite PRAGMA performance tuning C1 (`storage`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Ghost Mode (Decoupled Read Receipts) | Suppresses outgoing MTProto read marks in `data_histories.cpp` | M2 | docs/fork_features.md:8 |
| 2 | Ghost Mode Settings UI & Persistence | Privacy toggle serialized at stream end in `core_settings` | M2 | docs/fork_features.md:9 |
| 3 | Multi-Connection MTProto Chunk Downloading | 16 parallel DC download sessions in `download_manager_mtproto` | M3 | docs/fork_features.md:12 |
| 4 | Grid Mode Toggle | Button to switch between presentation and grid views | M1 | docs/fork_features.md:15 |
| 5 | In-Call Chat Panel Slide-Out | Translucent chat slide-out panel | M1 | docs/fork_features.md:16 |
| 6 | End Call Button & Hover Controls | Streamlined hangup button and auto-hiding controls | M1 | docs/fork_features.md:17 |
| 7 | Camera & Participant Bar Controls | Toolbar video and participant list toggles | M1 | docs/fork_features.md:18 |
| 8 | CallButton to IconButton Migration | Unified button primitive in `calls.style` | M1 | docs/fork_features.md:19 |
| 9 | callCancelRipple Palette Color | Red ripple accent color `#c04646` in `colors.palette` | M1 | docs/fork_features.md:20 |
| 10 | Hidden Floating PiP Camera Preview | Local camera integrated into grid/sidebar | M1 | docs/fork_features.md:21 |
| 11 | Multi-Monitor Stage Window Support | Auxiliary display routing via `DisplayCoordinator` | M1 | docs/fork_features.md:24 |
| 12 | Dual Initial Windows Prompt | Target display selection dialog | M1 | docs/fork_features.md:25 |
| 13 | Display Role Router | Display roles: ActiveSpeaker, GridViewport, ChatStation | M1 | docs/fork_features.md:26 |
| 14 | Async Video Stream Routing | Non-blocking frame dispatch to secondary displays | M1 | docs/fork_features.md:27 |
| 15 | Secondary Display Active-Speaker Isolation | Guarded `updateAudioLevels` on auxiliary displays | M1 | docs/fork_features.md:28 |
| 16 | Discrete Layout Presets (1x1, 2x2, 3x3) | Symmetrical tile presets for fixed participant counts | M1 | docs/fork_features.md:31 |
| 17 | Dynamic Grid Solver (50/50 Split) | Optimal auto-scaling grid solver (1=full, 2=50/50, etc.) | M1 | docs/fork_features.md:32 |
| 18 | Uncapped Dynamic Main Grid Scaling | Dynamic viewport scaling without tile caps | M1 | docs/fork_features.md:33 |
| 19 | Persistent Pin Slot Allocator | Locked pinned slots across layout mutations | M1 | docs/fork_features.md:34 |
| 20 | Per-Window Dynamic Pinned Auto-Scaling | Auto-scales 1..9 pinned feeds to fill stage | M1 | docs/fork_features.md:35 |
| 21 | Multi-Pin Capability | Simultaneous multi-peer pinning | M1 | docs/fork_features.md:36 |
| 22 | Adjustable Pinned Panel Sizes | Resizable splitters for featured feeds | M1 | docs/fork_features.md:37 |
| 23 | Grid Unpinning & Removal Actions | Unpin action and dialog to remove pinned feeds | M1 | docs/fork_features.md:38 |
| 24 | Pin to Grid Context Menu Actions | Injects `lng_group_call_context_pin_to_grid` | M1 | docs/fork_features.md:39 |
| 25 | Frameless Transparent Top-Most Overlay | Companion overlay window (`calls_group_floating_overlay`) | M1 | docs/fork_features.md:42 |
| 26 | Ctrl+Shift+T Keyboard Toggle | Global/window shortcut for floating overlay | M1 | docs/fork_features.md:43 |
| 27 | Opacity Adjustment via Ctrl+Wheel | 20% to 100% opacity scaling with Ctrl+Wheel | M1 | docs/fork_features.md:44 |
| 28 | Draggable Canvas & Escape to Dismiss | Left-click drag repositioning and Esc hide | M1 | docs/fork_features.md:45 |
| 29 | Embedded Chat & Dynamic Resize | `MessagesUi` parenting in `FloatingOverlay::setupChatContent` | M1 | docs/fork_features.md:46 |
| 30 | In-Meeting Chat Search | Real-time chat filtering in overlay | M1 | docs/fork_features.md:47 |
| 31 | Chronological Entry-Time Grid Sorting | Joins ordered by join timestamp | M1 | docs/fork_features.md:50 |
| 32 | Alphabetical Sidebar Sorting | Case-insensitive A-Z sorting via `peerListSortRows` | M1 | docs/fork_features.md:51 |
| 33 | In-Call Sidebar Search Bar | Anchored participant search in `calls_group_members` | M1 | docs/fork_features.md:52 |
| 34 | Search Results Quick Actions | Quick pin/chat action buttons on search rows | M1 | docs/fork_features.md:53 |
| 35 | Audio Lockout / Listen-Only Mode | Strict zero-mic capture prevention in `tgcalls` | M3 | docs/fork_features.md:56 |
| 36 | Microphone Controls Removal | Hides mic/mute buttons in listen-only mode | M3 | docs/fork_features.md:57 |
| 37 | Permanent Listen-Only Invariant | Controller drops outgoing audio descriptors | M3 | docs/fork_features.md:58 |
| 38 | Calls Submenu in Main Menu | Integrates `Calls::ShowCallsMenu` into `window_main_menu` | M2 | docs/fork_features.md:61 |
| 39 | Wallet Entry with NEW Badge | TON wallet menu item under My Profile | M2 | docs/fork_features.md:62 |
| 40 | Wide/Grid Obstructing Button Cleanup | Repositions floating controls in grid mode | M1 | docs/fork_features.md:65 |
| 41 | Titlebar Close Wired to Hangup | Window close triggers call termination | M1 | docs/fork_features.md:66 |
| 42 | Screen Share & Message Toggle Icons | Vector icons matching `calls.style` | M1 | docs/fork_features.md:67 |
| 43 | Multi-Pin Hover Controls | Pin icon on video tile hover | M1 | docs/fork_features.md:68 |
| 44 | Window-Level Ctrl+Shift+T Key Handler | Key handler in `calls_group_panel` | M1 | docs/fork_features.md:69 |
| 45 | Rich Tasks (Checklist Items) | Interactive markdown task list items in `api_rich_tasks` | M2 | docs/fork_features.md:72 |
| 46 | Cross-UI Pin to Grid Actions | Pin to Grid available in history & context menus | M1 | docs/fork_features.md:73 |
| 47 | Screen Target Pinning Prompt | Multi-monitor target selection dialog | M1 | docs/fork_features.md:74 |
| 48 | Stream Thumbnail Unpin Action Dialog | Thumbnail unpin context menu | M1 | docs/fork_features.md:75 |
| 49 | Central Call & State Controller | Centralized controller for participant cache & slots | M1 | docs/fork_features.md:78 |
| 50 | Simulcast Upscaling Signaling | Quality requests for pinned/large tiles | M1 | docs/fork_features.md:79 |
| 51 | Active-Speaker Hysteresis | Damping to prevent speaker flapping | M1 | docs/fork_features.md:80 |
| 52 | TrackPeer & Endpoint Routing Cleanup | Clean endpoint-to-peer mapping | M1 | docs/fork_features.md:81 |
| 53 | SQLite PRAGMA Optimizations (C1) | WAL journaling and mmap_size tuning | M3 | docs/fork_features.md:82 |
| 54 | WebRTC Playout Delay & Jitter Clamping (A1) | Fast accelerate and 50ms min jitter delay in tgcalls | M3 | docs/fork_features.md:83 |
| 55 | Windows Native Build Guide | Documented MSVC 2022 build steps | M4 | docs/fork_features.md:86 |
| 56 | CMakeLists.txt Source Synchronization | All fork sources registered in target | M4 | docs/fork_features.md:87 |
| 57 | Fork Localization Language Keys | Complete language keys in `lang.strings` | M4 | docs/fork_features.md:88 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Calls UI, Floating Overlay & Viewport Grid | Implement `setupChatContent` in `calls_group_floating_overlay.cpp`, fix 50/50 dynamic grid solver bug in `calls_group_viewport.cpp`, wire `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` in `calls_group_members.cpp` | none | DONE (Gate: PASS, Auditor: CLEAN) |
| M2 | Navigation & Calls Menu Integration | Wire `Calls::ShowCallsMenu` into `window_main_menu.cpp`, verify Wallet menu item with NEW badge, verify Ghost Mode read receipt suppression | none | DONE (Gate: PASS, Auditor: CLEAN) |
| M3 | Engine & Performance Subsystems | Verify/finalize SQLite PRAGMA C1 tuning in storage initialization and WebRTC jitter buffer clamping A1 in `tgcalls` | none | DONE (Gate: PASS, Auditor: CLEAN) |
| M4 | Code Style & Windows Native Debug Build | Verify code style conformance with `REVIEW.md`/`AGENTS.md` (no single-line comments, crl::guard, MTP::Sender), execute and verify Windows Native Debug compilation (`cmake --build out --config Debug --target Telegram`) | M1, M2, M3 | IN_PROGRESS |
| M5 | Final Milestone: E2E Integration & Verification | Pass 100% E2E test suite (Tiers 1-4) and adversarial coverage hardening (Tier 5) | M4 | IN_PROGRESS |

## Interface Contracts
### Calls::Group::FloatingOverlay ↔ Calls::Group::Panel
- `FloatingOverlay::setupChatContent()` retrieves chat controller and parent `Ui::Show` instance from `Panel`, instantiates `MessagesUi`, and binds resize signals.
### Calls::ShowCallsMenu ↔ Window::MainMenu
- `Calls::ShowCallsMenu(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window)` dynamically populates active calls, start call, and history entries when user clicks Calls menu action.
### Storage Initialization ↔ SQLite Engine
- `ApplySqlitePerformancePragmas` executes `PRAGMA journal_mode = WAL;`, `PRAGMA mmap_size = 268435456;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA cache_size = -64000;`, `PRAGMA temp_store = MEMORY;` with fallback handling to `TRUNCATE`.

## Code Layout
- `Telegram/SourceFiles/calls/group/` — Floating overlay, viewport grid, display coordinator, members panel
- `Telegram/SourceFiles/calls/` — `calls_box_controller.cpp/.h`, `calls.style`
- `Telegram/SourceFiles/window/` — `window_main_menu.cpp`
- `Telegram/SourceFiles/core/` — `core_settings.h/.cpp`
- `Telegram/SourceFiles/data/` — `data_histories.cpp`
- `Telegram/SourceFiles/storage/` — `download_manager_mtproto.cpp/.h`, `storage_sqlite_pragmas.h`
- `Telegram/ThirdParty/tgcalls/` — WebRTC jitter clamping A1 (`MediaManager.cpp`, `GroupInstanceCustomImpl.cpp`, `InstanceV2Impl.cpp`)
- `Telegram/Resources/langs/` — `lang.strings`
