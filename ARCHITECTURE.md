# Telegram Desktop (`tdesktop`) — Architecture Guide

This document outlines the high-level architecture, module decomposition, data flow, and subsystem organization of this Telegram Desktop fork.

---

## 1. Architectural Overview

Telegram Desktop is built in modern **C++20** using a hybrid architecture:

- **Qt Framework** provides low-level windowing, screen enumeration, hardware abstractions, and graphics platform plugins (QPA).
- **Custom Reactive UI Toolkit (`lib_ui`)** handles widget layouts, high-performance rendering (OpenGL, Vulkan/Metal via RHI, software rasterization), fluid animations, and design-system styling.
- **Reactive Stream Paradigm (`rpl`)** connects user interactions, network events, and UI state mutations with deterministic lifetime management.
- **Custom Concurrency Engine (`lib_crl`)** provides lightweight cooperative multitasking, event-loop dispatchers, and thread-pool execution.

```
+-----------------------------------------------------------------------+
|                           User Interface                              |
|   MainWindow / SessionController | In-Call Panel | Floating Overlay  |
+-----------------------------------------------------------------------+
|                       Presentation & Views                            |
|     lib_ui (RpWidget, Style, BoxContent) | Viewport Compositor        |
+-----------------------------------------------------------------------+
|                    Application & State Machine                         |
|     Data::Session | History | Calls::GroupCall | DisplayCoordinator  |
+-----------------------------------------------------------------------+
|                         Network & Protocol                            |
|       MTP::Instance | Ghost Mode Decoupler | Rich Tasks API           |
+-----------------------------------------------------------------------+
|                      Hardware & Media Engine                          |
|         tgcalls (WebRTC) | FFmpeg | lib_crl Threading | Qt Core       |
+-----------------------------------------------------------------------+
```

---

## 2. Repository & Submodule Organization

The codebase is partitioned into distinct submodules and directory layers:

```text
tdesktop/
├── Telegram/
│   ├── SourceFiles/          # Core client application logic
│   │   ├── api/              # High-level MTProto API wrappers (messages, auth, calls, rich_tasks)
│   │   ├── calls/            # 1-on-1 and Group Calls (voice/video)
│   │   │   ├── group/        # Group call UI, DisplayCoordinator, FloatingOverlay, Viewport
│   │   │   └── ui/           # Call controls, animations, buttons
│   │   ├── core/             # Application lifecycle, crash handler, settings
│   │   ├── data/             # Domain models (PeerData, History, Media, Session, Stories)
│   │   ├── dialogs/          # Chats list, folder tabs, search indexing
│   │   ├── history/          # Message list rendering, message bubbles, layout engine
│   │   ├── info/             # Profile, shared media, group info panels
│   │   ├── main/             # Main account and session controllers
│   │   ├── mtproto/          # Low-level MTProto protocol implementation
│   │   ├── settings/         # Settings UI, cloud password, privacy toggles (incl. Ghost Mode)
│   │   ├── storage/          # Local encrypted storage (tdata), SQLite pragmas (C1)
│   │   ├── ui/               # Application-specific UI components & boxes
│   │   └── window/           # Window frames, titlebar, navigation controller
│   └── ThirdParty/           # Bundled submodules and third-party libraries
├── lib_base/                 # Base utility library (memory, algorithms, assertions)
├── lib_crl/                  # Concurrency & Runtime Library (threading, dispatchers)
├── lib_ui/                   # Reusable reactive UI framework & style engine
├── lib_webrtc/               # WebRTC abstraction layer
├── lib_tl/                   # Telegram Type Language (TL) compiler & generated classes
└── lib_storage/              # Low-level key-value & block storage primitives
```

---

## 3. Core Architectural Subsystems

### 3.1 Domain Model & State (`Telegram/SourceFiles/data/`)

- **`Main::Account` / `Main::Session`**: Represents an authenticated user session. Manages all state attached to a logged-in user account.
- **`Data::Session`**: Central registry for all in-memory entities:
  - **`Data::Histories` (`History`)**: Message history buffers for all dialogs. Ghost Mode check at `data/data_histories.cpp:717` suppresses read marks when enabled.
  - **`Data::Peers` (`PeerData`, `UserData`, `ChatData`, `ChannelData`)**: Identity caching, permissions, and profile states.
  - **`Data::Stories`**: Stories subsystem with stealth mode (`data/data_stories.cpp`). Applies `MTPStoriesStealthMode` and serializes `_stealthMode` state.
  - **`Data::CloudThemes`**: Remote and local themes management.

### 3.2 Network & MTProto Pipeline (`Telegram/SourceFiles/mtproto/` & `api/`)

- **`MTP::Instance`**: Top-level protocol coordinator managing connections to Telegram Data Centers (DCs).
- **`MTP::Sender`**: Helper to construct and send typed TL RPC queries with auto-retry, encryption, and deduplication.
- **Ghost Mode Decoupled Read Receipts (Fork Feature `E3`) — IMPLEMENTED**:
  - Intercepts viewport history reading triggers to suppress outbound `messages.readHistory` RPC invocations while maintaining local read state.
  - Gate in `data/data_histories.cpp:717`: `if (Core::App().settings().ghostMode())` — skips read mark when ghost mode is on.
  - Settings UI: `settings/sections/settings_privacy_security.cpp:1088` (`BuildGhostModeSection`).
  - Persistence: `core/core_settings.cpp:349` (`_ghostMode` field, qint32).
  - Stories stealth mode: `data/data_stories.cpp:293` (`apply(const MTPStoriesStealthMode &)`).
- **Multi-Connection MTProto Streaming (Fork Feature `B1`) — UNVERIFIED**:
  - Commit `f0e0edd68e` claims implementation ("feat(network): implement B1 multi-connection MTProto throughput boost and E3 Ghost mode read-receipt decoupling").
  - No parallel-download code found in `mtproto/` or `api/` at time of documentation refresh (Sep 9, 2026). Status uncertain — may have been rolled back or not fully landed.
- **Rich Tasks API (Fork Feature — IMPLEMENTED)**:
  - `api/api_rich_tasks.cpp/h`: Full API layer with `toggle()`, `send()`, `sendAccumulated()`, `finishRequest()`.
  - Returns success/failure and cleans stale entries (commit `0caee7074a`).
  - UI integration for right-click checklist toggling not yet verified.

### 3.3 Reactive UI Framework (`lib_ui` & `rpl`)

- **`Ui::RpWidget`**: Base class for reactive Qt widgets with integrated lifetime trackers and event subscriptions.
- **`rpl::event_stream` / `rpl::producer`**: Stream pipelines for UI events (clicks, scrolls, state changes) that auto-unsubscribe when widget scopes destroy.
- **`Ui::GL` / RHI Viewports**: Hardware-accelerated graphics backends optimizing frame delivery on Windows (Direct3D/OpenGL), macOS (Metal), and Linux (Vulkan/GL).

---

## 4. Group Calls & Multi-Screen Video Subsystem

The call subsystem (`Telegram/SourceFiles/calls/group/`) implements group voice/video chats on top of `tgcalls` (WebRTC):

```
                                +---------------------------+
                                | Calls::Group::GroupCall   |
                                |  (Core WebRTC State)      |
                                +-------------+-------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
       +-------------v-------------+                     +-------------v-------------+
       | Calls::Group::Panel       |                     | DisplayCoordinator       |
       | (Primary Call Window)     |                     | (Multi-Monitor Routing)   |
       +-------------+-------------+                     +-------------+-------------+
                     |                                                 |
       +-------------v-------------+                     +-------------v-------------+
       | Calls::Group::Viewport    |                     | FloatingOverlay           |
       | (Grid Solver & Tiles)     |                     | (Frameless Top-Most Chat) |
       +---------------------------+                     +---------------------------+
```

### Key Components:

1. **`Calls::Group::GroupCall`**: Central call coordinator. Manages participant sync, active-speaker notifications, WebRTC transport connections, and stream subscriptions.
2. **`Calls::Group::Panel`**: Main call window container. Houses top-bar actions, participant sidebar, floating controls, and viewport layouts.
   - **Grid Mode Toggle**: `_gridModeButton` (`calls_group_panel.cpp:859-877`) switches between `PanelMode::Wide` and `PanelMode::Grid` via `_viewport->setGridMode()`.
   - **Chat Panel Toggle**: `Panel::toggleChatPanel()` (`calls_group_panel.cpp:557`) slides out translucent chat panel with close button.
   - **Hangup Button**: `_hangup` wired to `endCall()` → `_call->hangup()` (`calls_group_panel.cpp:619,689`).
   - **Listen-Only Enforcement**: Microphone toggle disabled in permanent listen-only mode (`calls_group_panel.cpp:673`), tooltip suppressed (`calls_group_panel.cpp:245`, `StickedTooltip::Microphone`).
   - **Overlay Toggle**: `_floatingOverlay->toggle()` bound to panel controls (`calls_group_panel.cpp:432-433,884-885`).
3. **`Calls::Group::DisplayCoordinator`** *(Fork Component)*:
   - Queries and enumerates system displays (`QScreen`).
   - Manages multi-window routing (Screen 1 vs Screen 2).
   - `pinToScreen(int screenIndex, const VideoEndpoint &endpoint)` — pins participants to specific screens.
   - `unpinFromScreen(int screenIndex, const VideoEndpoint &endpoint)` — removes pins.
   - `pinnedCount(int screenIndex)` — tracks pinned count per screen.
   - Prevents active-speaker stream collisions and directs pinned feeds to secondary viewports.
   - Disabled random auto-filling / active-speaker slot hijacking on 2nd screen (commit `3e3905b56f`).
4. **`Calls::Group::FloatingOverlay`** *(Fork Component)*:
   - Frameless, semi-transparent top-most floating window (`Ctrl+Shift+T`).
   - Embeds live chat and search (`MessagesUi`) directly on top of full-screen meetings without stealing window focus.
   - `addChat(not_null<PeerData*> peer)` / `removeChat(PeerData *peer)` — manages chat tabs.
   - `toggleSearch()` — in-meeting search.
   - `keyPressEvent` handles Escape to dismiss and Ctrl+Shift+T global toggle.
   - Mouse events for drag, wheel, and hit-testing (pin screen button at `calls_group_floating_overlay.cpp:175`).
5. **`Calls::Group::Viewport` & Dynamic Grid Solver**:
   - Dynamically calculates tile geometry: `1×1` (full), `2×2` (50/50), `3×3`, or auto-fit.
   - Handles tile composition using GPU shaders (OpenGL/RHI).
   - Uncapped dynamic main grid scaling restored (commit `0a3147c76c`).
6. **Persistent Pin Allocator**:
   - Manages multiple concurrent participant pins across display changes and resolution adjustments.
   - Grid unpinning dialog and "Unpin / Remove from Screen" actions implemented.
7. **Audio Lockout / Zero-Mic Enforcement**:
   - Strips microphone capture pipelines in `tgcalls` for permanent listen-only operation.
   - Mic toggle disabled and tooltip suppressed when in lockout mode.

### Participant Sidebar & Search:

- **Entry-time chronological grid sorting**: Grid sorted by participant entry time (commit `9677a5c20b`).
- **Alphabetical sidebar**: Peer name comparison for alphabetical sorting (commit `384518b749`).
- **In-call sidebar searchbar**: Layout-anchored search field at top of sidebar for participant filtering.
- **Direct "Pin to Screen" & "Open Chat"**: From search results, wired via `lng_group_call_open_chat` (`calls_group_members.cpp:1578`).

### Context Menu Actions:

- Pin/unpin camera and screen actions in members context menu (`calls_group_members.cpp:1437-1504`).
- Screen target pinning prompt (`promptPinTargetScreen()`) for Screen 1 vs Screen 2 selection.

---

## 5. Threading & Concurrency Model

Telegram Desktop avoids heavy raw OS mutexes in favor of queue-based asynchronous task passing via **`lib_crl`**:

- **Main (GUI) Thread**:
  - Handles all Qt events, user input, paint events, and UI layout calculations.
  - Interacts directly with `Data::Session` models.
- **CRL Worker Thread Pool**:
  - Handles image decoding, text layout preprocessing, and disk cache serialization without blocking the UI.
- **MTProto Network Thread**:
  - Executes socket I/O, encryption/decryption (AES-IGE / SHA256), and packet serialization.
- **WebRTC / Media Threads**:
  - Managed by `tgcalls` for audio capture, video encoding/decoding, and jitter buffer synchronization.

---

## 6. Storage & Database Architecture

- **`tdata/` Local Encrypted Storage**:
  - Stores credentials, session keys, encrypted local settings, and user caches.
  - Key material is protected via OS-level encryption (DPAPI on Windows, Keychain on macOS).
- **SQLite Database Optimization (Fork Subsystem `C1`) — IMPLEMENTED**:
  - Configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and memory-mapped file access (`PRAGMA mmap_size = 268435456`) for instant local searches and non-blocking reads.
  - Implementation in `storage/storage_sqlite_pragmas.h:20-72`:
    - `journalMode = "WAL"` (line 20)
    - `PRAGMA journal_mode = %1;\nPRAGMA mmap_size = %2;\n` (lines 31-32)
    - Fallback to `TRUNCATE` if WAL setup fails (line 67)
    - `PRAGMA mmap_size = 268435456` (256 MB) if prepare succeeds (line 72)

---

## 7. Export Pipeline

The export subsystem (`Telegram/SourceFiles/export/`) converts chat data to HTML and JSON formats:

- **Data Layer** (`export/data/export_data_types.cpp/h`):
  - `MediaDice` struct with parsed dice emoji/value/game outcome (commit `3d4a2b28`).
  - `MediaStory` struct with peer/id/mention fields.
  - Reply-to parsing for both messages (`MTPDmessageReplyHeader`) and stories (`MTPDmessageReplyStoryHeader`).
  - Wallpaper actions (`ActionSetChatWallPaper`) partially wired.
- **HTML Output** (`export/output/export_output_html.cpp`):
  - `pushDice()` renders dice media.
  - Dice wrapper classes and CSS handling present.
  - Some HTML export TODOs remain (line 4913 area — `pushDice` implementation present but other wraps may be incomplete).
- **JSON Output** (`export/output/export_output_json.cpp`):
  - Wallpaper action serialization present (`set_same_chat_wallpaper` / `set_chat_wallpaper`).

---

## 8. Themes (Recent Addition)

- **Pure Black OLED** and **Soft Dark Slate** themes with custom accent palettes.
- Implemented in commit `d81a4c28b4` (`feat(theme): implement Pure Black OLED and Soft Dark Slate themes with custom accent palettes`).

---

## 9. Style & Conventions

- Adheres to repository formatting guidelines detailed in [`REVIEW.md`](file:///C:/Users/kyleh/tdesktop/REVIEW.md).
- Follows build toolchain rules detailed in [`AGENTS.md`](file:///C:/Users/kyleh/tdesktop/AGENTS.md).
- Tracks custom fork features in [`docs/fork_features.md`](file:///C:/Users/kyleh/tdesktop/docs/fork_features.md).

---

## 10. Known Gaps & Unimplemented Features

| Feature | Status | Notes |
|---------|--------|-------|
| A1: WebRTC Playout Delay & Jitter Clamping | **Not implemented** | Listed as "Planned" since Aug 20; no jitter buffer code found |
| B1: Multi-Connection MTProto Download | **Unverified** | Commit exists but no parallel-download code in mtproto/api |
| Wallet main menu entry | **Not found** | No menu entry or badge in codebase |
| Replace "Calls" with folder/submenu | **Not found** | No submenu implementation |
| CallButton → IconButton migration | **Partial** | lib_ui bump done; full migration unverified |
| callCancelRipple (#c04646) | **Not found** | Color value absent from codebase |
| "Pin to Grid" in history/view/search menus | **Not found** | Only in members context menu |
| Titlebar close → hangup | **Not found** | No explicit wiring |
| Simulcast upscaling signaling | **Unverified** | No explicit simulcast code found |
| TrackPeer cleanup (0b263e0608) | **Not found** | Commit reference not in log |

---

> Last updated: September 9, 2026 | Branch nightly — 44 commits ahead of `upstream/dev` (diverged lineage)
