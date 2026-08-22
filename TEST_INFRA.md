# E2E Test Infra: Telegram Desktop Fork

## Test Philosophy
- **Requirement-Driven & Opaque-Box**: Tests are derived directly from `PROJECT.md § Feature Inventory` and `docs/fork_features.md`, treating the client interface, configs, data streams, and event pipelines as black-box systems.
- **Methodology**: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.
- **Independence**: Test suite does not depend on internal private C++ symbols or compiler ABI; tests execute against external interfaces, state serializers, layout solvers, RPC payloads, protocol models, and client event handlers.
- **Deterministic & Automated**: The test runner executes via `py tests/e2e/run_all.py` on Windows/Linux, returning exit code 0 when all tests pass.

## Feature Inventory & Category Mapping
| # | Feature | Category | Source (Requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|----------|---------------------|:------:|:------:|:------:|
| 1 | Ghost Mode (Decoupled Read Receipts) | Privacy & Ghost Mode (E3) | docs/fork_features.md:8 | 5 | 5 | ✓ |
| 2 | Ghost Mode Settings UI & Persistence | Privacy & Ghost Mode (E3) | docs/fork_features.md:9 | 5 | 5 | ✓ |
| 3 | Multi-Connection MTProto Chunk Downloading | Network & Download (B1) | docs/fork_features.md:12 | 5 | 5 | ✓ |
| 4 | Grid Mode Toggle | Call UI & Controls | docs/fork_features.md:15 | 5 | 5 | ✓ |
| 5 | In-Call Chat Panel Slide-Out | Call UI & Controls | docs/fork_features.md:16 | 5 | 5 | ✓ |
| 6 | End Call Button & Hover Controls | Call UI & Controls | docs/fork_features.md:17 | 5 | 5 | ✓ |
| 7 | Camera & Participant Bar Controls | Call UI & Controls | docs/fork_features.md:18 | 5 | 5 | ✓ |
| 8 | CallButton to IconButton Migration | Call UI & Controls | docs/fork_features.md:19 | 5 | 5 | ✓ |
| 9 | callCancelRipple Palette Color | Call UI & Controls | docs/fork_features.md:20 | 5 | 5 | ✓ |
| 10 | Hidden Floating PiP Camera Preview | Call UI & Controls | docs/fork_features.md:21 | 5 | 5 | ✓ |
| 11 | Multi-Monitor Stage Window Support | Multi-Display & Routing | docs/fork_features.md:24 | 5 | 5 | ✓ |
| 12 | Dual Initial Windows Prompt | Multi-Display & Routing | docs/fork_features.md:25 | 5 | 5 | ✓ |
| 13 | Display Role Router | Multi-Display & Routing | docs/fork_features.md:26 | 5 | 5 | ✓ |
| 14 | Async Video Stream Routing | Multi-Display & Routing | docs/fork_features.md:27 | 5 | 5 | ✓ |
| 15 | Secondary Display Active-Speaker Isolation | Multi-Display & Routing | docs/fork_features.md:28 | 5 | 5 | ✓ |
| 16 | Discrete Layout Presets (1x1, 2x2, 3x3) | Grid Layout & Pin System | docs/fork_features.md:31 | 5 | 5 | ✓ |
| 17 | Dynamic Grid Solver (50/50 Split) | Grid Layout & Pin System | docs/fork_features.md:32 | 5 | 5 | ✓ |
| 18 | Uncapped Dynamic Main Grid Scaling | Grid Layout & Pin System | docs/fork_features.md:33 | 5 | 5 | ✓ |
| 19 | Persistent Pin Slot Allocator | Grid Layout & Pin System | docs/fork_features.md:34 | 5 | 5 | ✓ |
| 20 | Per-Window Dynamic Pinned Auto-Scaling | Grid Layout & Pin System | docs/fork_features.md:35 | 5 | 5 | ✓ |
| 21 | Multi-Pin Capability | Grid Layout & Pin System | docs/fork_features.md:36 | 5 | 5 | ✓ |
| 22 | Adjustable Pinned Panel Sizes | Grid Layout & Pin System | docs/fork_features.md:37 | 5 | 5 | ✓ |
| 23 | Grid Unpinning & Removal Actions | Grid Layout & Pin System | docs/fork_features.md:38 | 5 | 5 | ✓ |
| 24 | Pin to Grid Context Menu Actions | Grid Layout & Pin System | docs/fork_features.md:39 | 5 | 5 | ✓ |
| 25 | Frameless Transparent Top-Most Overlay | Floating Overlay | docs/fork_features.md:42 | 5 | 5 | ✓ |
| 26 | Ctrl+Shift+T Keyboard Toggle | Floating Overlay | docs/fork_features.md:43 | 5 | 5 | ✓ |
| 27 | Opacity Adjustment via Ctrl+Wheel | Floating Overlay | docs/fork_features.md:44 | 5 | 5 | ✓ |
| 28 | Draggable Canvas & Escape to Dismiss | Floating Overlay | docs/fork_features.md:45 | 5 | 5 | ✓ |
| 29 | Embedded Chat & Dynamic Resize | Floating Overlay | docs/fork_features.md:46 | 5 | 5 | ✓ |
| 30 | In-Meeting Chat Search | Floating Overlay | docs/fork_features.md:47 | 5 | 5 | ✓ |
| 31 | Chronological Entry-Time Grid Sorting | Participant Sidebar & Search | docs/fork_features.md:50 | 5 | 5 | ✓ |
| 32 | Alphabetical Sidebar Sorting | Participant Sidebar & Search | docs/fork_features.md:51 | 5 | 5 | ✓ |
| 33 | In-Call Sidebar Search Bar | Participant Sidebar & Search | docs/fork_features.md:52 | 5 | 5 | ✓ |
| 34 | Search Results Quick Actions | Participant Sidebar & Search | docs/fork_features.md:53 | 5 | 5 | ✓ |
| 35 | Audio Lockout / Listen-Only Mode | Audio / Microphone | docs/fork_features.md:56 | 5 | 5 | ✓ |
| 36 | Microphone Controls Removal | Audio / Microphone | docs/fork_features.md:57 | 5 | 5 | ✓ |
| 37 | Permanent Listen-Only Invariant | Audio / Microphone | docs/fork_features.md:58 | 5 | 5 | ✓ |
| 38 | Calls Submenu in Main Menu | Main Menu & Navigation | docs/fork_features.md:61 | 5 | 5 | ✓ |
| 39 | Wallet Entry with NEW Badge | Main Menu & Navigation | docs/fork_features.md:62 | 5 | 5 | ✓ |
| 40 | Wide/Grid Obstructing Button Cleanup | UI Tweaks & Polish | docs/fork_features.md:65 | 5 | 5 | ✓ |
| 41 | Titlebar Close Wired to Hangup | UI Tweaks & Polish | docs/fork_features.md:66 | 5 | 5 | ✓ |
| 42 | Screen Share & Message Toggle Icons | UI Tweaks & Polish | docs/fork_features.md:67 | 5 | 5 | ✓ |
| 43 | Multi-Pin Hover Controls | UI Tweaks & Polish | docs/fork_features.md:68 | 5 | 5 | ✓ |
| 44 | Window-Level Ctrl+Shift+T Key Handler | UI Tweaks & Polish | docs/fork_features.md:69 | 5 | 5 | ✓ |
| 45 | Rich Tasks (Checklist Items) | Context Menus & Cross-UI | docs/fork_features.md:72 | 5 | 5 | ✓ |
| 46 | Cross-UI Pin to Grid Actions | Context Menus & Cross-UI | docs/fork_features.md:73 | 5 | 5 | ✓ |
| 47 | Screen Target Pinning Prompt | Context Menus & Cross-UI | docs/fork_features.md:74 | 5 | 5 | ✓ |
| 48 | Stream Thumbnail Unpin Action Dialog | Context Menus & Cross-UI | docs/fork_features.md:75 | 5 | 5 | ✓ |
| 49 | Central Call & State Controller | Backend / Engine | docs/fork_features.md:78 | 5 | 5 | ✓ |
| 50 | Simulcast Upscaling Signaling | Backend / Engine | docs/fork_features.md:79 | 5 | 5 | ✓ |
| 51 | Active-Speaker Hysteresis | Backend / Engine | docs/fork_features.md:80 | 5 | 5 | ✓ |
| 52 | TrackPeer & Endpoint Routing Cleanup | Backend / Engine | docs/fork_features.md:81 | 5 | 5 | ✓ |
| 53 | SQLite PRAGMA Optimizations (C1) | Backend / Engine | docs/fork_features.md:82 | 5 | 5 | ✓ |
| 54 | WebRTC Playout Delay & Jitter Clamping (A1) | Backend / Engine | docs/fork_features.md:83 | 5 | 5 | ✓ |
| 55 | Windows Native Build Guide | Build & Toolchain | docs/fork_features.md:86 | 5 | 5 | ✓ |
| 56 | CMakeLists.txt Source Synchronization | Build & Toolchain | docs/fork_features.md:87 | 5 | 5 | ✓ |
| 57 | Fork Localization Language Keys | Build & Toolchain | docs/fork_features.md:88 | 5 | 5 | ✓ |

## Test Architecture
- **Location**: `tests/e2e/`
- **Invocation**: `py tests/e2e/run_all.py` (or `py tests/e2e/run_all.py --tier 1`, `--tier 2`, `--tier 3`, `--tier 4`)
- **Exit Code Semantics**:
  - `0`: All tests passed successfully.
  - `1`: One or more test assertions failed or timed out.
- **Directory Layout**:
  ```text
  tests/e2e/
  ├── framework/
  │   ├── __init__.py
  │   ├── assertions.py
  │   ├── call_simulator.py
  │   ├── grid_solver_oracle.py
  │   ├── mtproto_mock.py
  │   └── storage_mock.py
  ├── tier1_features/
  │   ├── __init__.py
  │   ├── test_t1_privacy_network.py
  │   ├── test_t1_calls_ui.py
  │   ├── test_t1_multi_display.py
  │   ├── test_t1_grid_pin.py
  │   ├── test_t1_floating_overlay.py
  │   ├── test_t1_sidebar_audio.py
  │   ├── test_t1_menu_polish.py
  │   └── test_t1_context_engine_build.py
  ├── tier2_boundaries/
  │   ├── __init__.py
  │   ├── test_t2_privacy_network_boundaries.py
  │   ├── test_t2_calls_ui_boundaries.py
  │   ├── test_t2_multi_display_boundaries.py
  │   ├── test_t2_grid_pin_boundaries.py
  │   ├── test_t2_floating_overlay_boundaries.py
  │   ├── test_t2_sidebar_audio_boundaries.py
  │   ├── test_t2_menu_polish_boundaries.py
  │   └── test_t2_context_engine_build_boundaries.py
  ├── tier3_combinations/
  │   ├── __init__.py
  │   ├── test_t3_call_ui_grid_interactions.py
  │   ├── test_t3_multi_display_overlay_interactions.py
  │   ├── test_t3_ghost_mode_network_interactions.py
  │   └── test_t3_audio_lockout_menu_interactions.py
  ├── tier4_scenarios/
  │   ├── __init__.py
  │   └── test_t4_real_world_scenarios.py
  └── run_all.py
  ```

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Large Townhall Presentation | F4 (Grid Mode), F11 (Multi-Display), F16 (Presets), F21 (Multi-Pin), F35 (Listen-Only) | High |
| 2 | Executive Stealth Chat & Call Review | F1 (Ghost Mode), F2 (Settings UI), F5 (Slide-out Chat), F25 (Floating Overlay), F30 (Chat Search) | High |
| 3 | Heavy Media Ingestion & Chunk Download | F3 (Multi-Connection MTProto 16 parallel), F53 (SQLite PRAGMA C1 WAL/mmap) | Medium |
| 4 | Multi-Monitor Trading / Monitoring Station | F11 (Multi-Monitor Stage), F12 (Dual Initial Prompt), F13 (Display Role Router), F14 (Async Video), F15 (Active-Speaker Isolation) | High |
| 5 | Dynamic Interactive Sprint Planning | F45 (Rich Tasks / Interactive Checklists), F29 (Embedded Chat in Overlay), F38 (Calls Submenu) | Medium |
| 6 | Fast-Paced Multi-Speaker Debate | F51 (Active-Speaker Hysteresis), F54 (WebRTC Jitter Clamping A1), F17 (Dynamic Grid 50/50), F49 (Central Controller) | High |
| 7 | Webinar with Listen-Only Attendees | F35 (Audio Lockout), F36 (Mic Control Removal), F37 (Permanent Invariant), F33 (Sidebar Search), F34 (Quick Actions) | Medium |
| 8 | Compact HUD Companion Overlay Workflow | F25 (Top-Most Overlay), F26 (Ctrl+Shift+T), F27 (Opacity Ctrl+Wheel), F28 (Drag & Esc), F29 (MessagesUi) | Medium |
| 9 | Rapid Participant Inflow & Dynamic Re-sorting | F31 (Entry-Time Chronological Grid), F32 (Alphabetical Sidebar), F18 (Uncapped Grid Scaling) | High |
| 10 | Pinned Panel Resizing & Splitter Adjustment | F19 (Pin Allocator), F20 (Dynamic Pinned Auto-Scaling), F22 (Adjustable Panel Sizes), F43 (Multi-Pin Hover) | Medium |
| 11 | Cross-UI Context Menu Navigation Flow | F24 (Pin to Grid Context Menu), F46 (Cross-UI Pin), F47 (Screen Target Prompt), F48 (Thumbnail Unpin Dialog) | Medium |
| 12 | Navigation & Wallet Inspection Flow | F38 (Calls Submenu in Main Menu), F39 (Wallet Entry with NEW Badge), F57 (Language Keys) | Low |
| 13 | Emergency Hangup & Fast Call Termination | F6 (End Call Button), F40 (Obstructing Button Cleanup), F41 (Titlebar Close Hangup) | Low |
| 14 | Network Degradation & Multi-Connection Resilience | F3 (Multi-Connection DC Failover/Concurrency), F50 (Simulcast Upscaling Signaling) | High |
| 15 | Overlay Keyboard Mastery & Focus Shift | F26 (Ctrl+Shift+T), F44 (Window-Level Ctrl+Shift+T), F28 (Escape Dismissal) | Medium |
| 16 | Massive Group Call Grid Solver Scale (1 to 64 peers) | F16 (Presets 1x1, 2x2, 3x3), F17 (Dynamic 50/50), F18 (Uncapped Scaling) | High |
| 17 | Zero-Mic Enforcement Under Call Reconnection | F35 (Listen-Only), F37 (Permanent Listen-Only Invariant), F49 (Central State Controller) | Medium |
| 18 | High-Throughput Database Write & Cache Coherency | F53 (SQLite PRAGMA WAL & Cache -64000), F1 (Ghost Mode Local vs Server Mark) | High |
| 19 | Dual-Screen Presentation with Chat Station | F13 (Display Role Router: ChatStation), F14 (Async Video), F29 (Embedded Chat) | High |
| 20 | Complete Custom Theme & Style Conformance | F8 (CallButton to IconButton), F9 (callCancelRipple #c04646), F42 (Vector Icons) | Low |
| 21 | Multi-Participant Pinning with Quality Upscaling | F21 (Multi-Pin), F50 (Simulcast Upscale), F52 (TrackPeer / Endpoint Routing) | High |
| 22 | Sidebar Search & Real-Time Participant Actions | F33 (Sidebar Searchbar), F34 (Direct Pin/Chat Actions), F23 (Grid Unpinning) | Medium |
| 23 | Overlay Dynamic Resize & Chat Scroll Persistence | F29 (MessagesUi Parenting & Resize), F30 (In-Meeting Chat Search) | Medium |
| 24 | WebRTC Playout Latency & Rapid Speaker Jitter Test | F54 (Playout Delay & Jitter Clamping A1), F51 (Active-Speaker Damping) | High |
| 25 | Settings Toggle Round-Trip & App Restart | F2 (Ghost Mode Persistence in core_settings), F1 (Suppressed Receipts) | Medium |
| 26 | Multi-Display Dynamic Disconnection & Fallback | F11 (Multi-Monitor Stage), F13 (Display Role Fallback to Primary), F15 (Audio Guard) | High |
| 27 | Rich Task Status Toggle & History Sync | F45 (Interactive Markdown Checklist), F1 (Stealth Task Completion) | Medium |
| 28 | Comprehensive Localization Keys Completeness | F57 (Language Keys: lng_group_call_open_chat, lng_group_call_context_pin_to_grid) | Low |
| 29 | End-to-End Fork System Lifecycle Integration | Full integration of all 13 categories from startup to call termination | High |

## Coverage Thresholds
- **Tier 1 (Feature Coverage)**: ≥5 test cases per feature × 57 features = **285 test cases**
- **Tier 2 (Boundary & Corner Cases)**: ≥5 test cases per feature × 57 features = **285 test cases**
- **Tier 3 (Cross-Feature Combinations)**: Pairwise coverage across feature categories = **≥57 test cases**
- **Tier 4 (Real-World Application Scenarios)**: Realistic end-user workloads = **29 test cases**
- **Total Suite Minimum**: 285 + 285 + 57 + 29 = **656 test cases**
