# Scope: E2E Testing Track Orchestrator

## Architecture
The E2E Testing Track provides an opaque-box, requirement-driven automated test suite verifying all 57 Telegram Desktop fork features and 13 categories without relying on implementation internals.
Test Runner: Python-based standalone CLI runner (`py tests/e2e/run_all.py`) verifying behaviors, configurations, protocol interactions, state transitions, layout constraints, and error handling across 659 test cases.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Ghost Mode (Decoupled Read Receipts) | Suppresses outgoing MTProto read marks in `data_histories.cpp` | T1..T4 | docs/fork_features.md:8 |
| 2 | Ghost Mode Settings UI & Persistence | Privacy toggle serialized at stream end in `core_settings` | T1..T4 | docs/fork_features.md:9 |
| 3 | Multi-Connection MTProto Chunk Downloading | 16 parallel DC download sessions in `download_manager_mtproto` | T1..T4 | docs/fork_features.md:12 |
| 4 | Grid Mode Toggle | Button to switch between presentation and grid views | T1..T4 | docs/fork_features.md:15 |
| 5 | In-Call Chat Panel Slide-Out | Translucent chat slide-out panel | T1..T4 | docs/fork_features.md:16 |
| 6 | End Call Button & Hover Controls | Streamlined hangup button and auto-hiding controls | T1..T4 | docs/fork_features.md:17 |
| 7 | Camera & Participant Bar Controls | Toolbar video and participant list toggles | T1..T4 | docs/fork_features.md:18 |
| 8 | CallButton to IconButton Migration | Unified button primitive in `calls.style` | T1..T4 | docs/fork_features.md:19 |
| 9 | callCancelRipple Palette Color | Red ripple accent color `#c04646` in `colors.palette` | T1..T4 | docs/fork_features.md:20 |
| 10 | Hidden Floating PiP Camera Preview | Local camera integrated into grid/sidebar | T1..T4 | docs/fork_features.md:21 |
| 11 | Multi-Monitor Stage Window Support | Auxiliary display routing via `DisplayCoordinator` | T1..T4 | docs/fork_features.md:24 |
| 12 | Dual Initial Windows Prompt | Target display selection dialog | T1..T4 | docs/fork_features.md:25 |
| 13 | Display Role Router | Display roles: ActiveSpeaker, GridViewport, ChatStation | T1..T4 | docs/fork_features.md:26 |
| 14 | Async Video Stream Routing | Non-blocking frame dispatch to secondary displays | T1..T4 | docs/fork_features.md:27 |
| 15 | Secondary Display Active-Speaker Isolation | Guarded `updateAudioLevels` on auxiliary displays | T1..T4 | docs/fork_features.md:28 |
| 16 | Discrete Layout Presets (1x1, 2x2, 3x3) | Symmetrical tile presets for fixed participant counts | T1..T4 | docs/fork_features.md:31 |
| 17 | Dynamic Grid Solver (50/50 Split) | Optimal auto-scaling grid solver (1=full, 2=50/50, etc.) | T1..T4 | docs/fork_features.md:32 |
| 18 | Uncapped Dynamic Main Grid Scaling | Dynamic viewport scaling without tile caps | T1..T4 | docs/fork_features.md:33 |
| 19 | Persistent Pin Slot Allocator | Locked pinned slots across layout mutations | T1..T4 | docs/fork_features.md:34 |
| 20 | Per-Window Dynamic Pinned Auto-Scaling | Auto-scales 1..9 pinned feeds to fill stage | T1..T4 | docs/fork_features.md:35 |
| 21 | Multi-Pin Capability | Simultaneous multi-peer pinning | T1..T4 | docs/fork_features.md:36 |
| 22 | Adjustable Pinned Panel Sizes | Resizable splitters for featured feeds | T1..T4 | docs/fork_features.md:37 |
| 23 | Grid Unpinning & Removal Actions | Unpin action and dialog to remove pinned feeds | T1..T4 | docs/fork_features.md:38 |
| 24 | Pin to Grid Context Menu Actions | Injects `lng_group_call_context_pin_to_grid` | T1..T4 | docs/fork_features.md:39 |
| 25 | Frameless Transparent Top-Most Overlay | Companion overlay window (`calls_group_floating_overlay`) | T1..T4 | docs/fork_features.md:42 |
| 26 | Ctrl+Shift+T Keyboard Toggle | Global/window shortcut for floating overlay | T1..T4 | docs/fork_features.md:43 |
| 27 | Opacity Adjustment via Ctrl+Wheel | 20% to 100% opacity scaling with Ctrl+Wheel | T1..T4 | docs/fork_features.md:44 |
| 28 | Draggable Canvas & Escape to Dismiss | Left-click drag repositioning and Esc hide | T1..T4 | docs/fork_features.md:45 |
| 29 | Embedded Chat & Dynamic Resize | `MessagesUi` parenting in `FloatingOverlay::setupChatContent` | T1..T4 | docs/fork_features.md:46 |
| 30 | In-Meeting Chat Search | Real-time chat filtering in overlay | T1..T4 | docs/fork_features.md:47 |
| 31 | Chronological Entry-Time Grid Sorting | Joins ordered by join timestamp | T1..T4 | docs/fork_features.md:50 |
| 32 | Alphabetical Sidebar Sorting | Case-insensitive A-Z sorting via `peerListSortRows` | T1..T4 | docs/fork_features.md:51 |
| 33 | In-Call Sidebar Search Bar | Anchored participant search in `calls_group_members` | T1..T4 | docs/fork_features.md:52 |
| 34 | Search Results Quick Actions | Quick pin/chat action buttons on search rows | T1..T4 | docs/fork_features.md:53 |
| 35 | Audio Lockout / Listen-Only Mode | Strict zero-mic capture prevention in `tgcalls` | T1..T4 | docs/fork_features.md:56 |
| 36 | Microphone Controls Removal | Hides mic/mute buttons in listen-only mode | T1..T4 | docs/fork_features.md:57 |
| 37 | Permanent Listen-Only Invariant | Controller drops outgoing audio descriptors | T1..T4 | docs/fork_features.md:58 |
| 38 | Calls Submenu in Main Menu | Integrates `Calls::ShowCallsMenu` into `window_main_menu` | T1..T4 | docs/fork_features.md:61 |
| 39 | Wallet Entry with NEW Badge | TON wallet menu item under My Profile | T1..T4 | docs/fork_features.md:62 |
| 40 | Wide/Grid Obstructing Button Cleanup | Repositions floating controls in grid mode | T1..T4 | docs/fork_features.md:65 |
| 41 | Titlebar Close Wired to Hangup | Window close triggers call termination | T1..T4 | docs/fork_features.md:66 |
| 42 | Screen Share & Message Toggle Icons | Vector icons matching `calls.style` | T1..T4 | docs/fork_features.md:67 |
| 43 | Multi-Pin Hover Controls | Pin icon on video tile hover | T1..T4 | docs/fork_features.md:68 |
| 44 | Window-Level Ctrl+Shift+T Key Handler | Key handler in `calls_group_panel` | T1..T4 | docs/fork_features.md:69 |
| 45 | Rich Tasks (Checklist Items) | Interactive markdown task list items in `api_rich_tasks` | T1..T4 | docs/fork_features.md:72 |
| 46 | Cross-UI Pin to Grid Actions | Pin to Grid available in history & context menus | T1..T4 | docs/fork_features.md:73 |
| 47 | Screen Target Pinning Prompt | Multi-monitor target selection dialog | T1..T4 | docs/fork_features.md:74 |
| 48 | Stream Thumbnail Unpin Action Dialog | Thumbnail unpin context menu | T1..T4 | docs/fork_features.md:75 |
| 49 | Central Call & State Controller | Centralized controller for participant cache & slots | T1..T4 | docs/fork_features.md:78 |
| 50 | Simulcast Upscaling Signaling | Quality requests for pinned/large tiles | T1..T4 | docs/fork_features.md:79 |
| 51 | Active-Speaker Hysteresis | Damping to prevent speaker flapping | T1..T4 | docs/fork_features.md:80 |
| 52 | TrackPeer & Endpoint Routing Cleanup | Clean endpoint-to-peer mapping | T1..T4 | docs/fork_features.md:81 |
| 53 | SQLite PRAGMA Optimizations (C1) | WAL journaling and mmap_size tuning | T1..T4 | docs/fork_features.md:82 |
| 54 | WebRTC Playout Delay & Jitter Clamping (A1) | Fast accelerate and 50ms min jitter delay in tgcalls | T1..T4 | docs/fork_features.md:83 |
| 55 | Windows Native Build Guide | Documented MSVC 2022 build steps | T1..T4 | docs/fork_features.md:86 |
| 56 | CMakeLists.txt Source Synchronization | All fork sources registered in target | T1..T4 | docs/fork_features.md:87 |
| 57 | Fork Localization Language Keys | Complete language keys in `lang.strings` | T1..T4 | docs/fork_features.md:88 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| T1 | Test Infra Harness & Tier 1 Feature Tests | Test runner infrastructure + 285 test cases (5 per feature across 57 features) | none | DONE |
| T2 | Tier 2 Boundary & Corner Cases | 285 boundary/corner test cases (5 per feature across 57 features) | T1 | DONE |
| T3 | Tier 3 Cross-Feature Combinations | 60 pairwise interaction test cases | T2 | DONE |
| T4 | Tier 4 Real-World Application Workloads | 29 realistic multi-feature application workflow scenarios | T3 | DONE |
| T5 | Verification & TEST_READY Publication | Execute full suite (659 tests), verify 0 failures, publish `TEST_READY.md` | T4 | DONE |

## Code Layout for E2E Tests
- `tests/e2e/` — Root for E2E test suite
- `tests/e2e/run_all.py` — Main entry point test runner with tier filtering, JSON/JUnit output, and summary reporting
- `tests/e2e/tier1_features/` — Tier 1 Feature coverage tests
- `tests/e2e/tier2_boundaries/` — Tier 2 Boundary & Corner cases
- `tests/e2e/tier3_combinations/` — Tier 3 Pairwise feature combination tests
- `tests/e2e/tier4_scenarios/` — Tier 4 Real-world comprehensive workload tests
- `tests/e2e/framework/` — Test harness, mock protocol, state simulation, assertion helpers
