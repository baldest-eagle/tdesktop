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
|       MTP::Instance | Multi-Connection MTProto | Ghost Mode Decoupler |
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
│   │   ├── api/              # High-level MTProto API wrappers (messages, auth, calls)
│   │   ├── calls/            # 1-on-1 and Group Calls (voice/video)
│   │   │   ├── group/        # Group call UI, DisplayCoordinator, FloatingOverlay
│   │   │   └── ui/           # Call controls, animations, buttons
│   │   ├── core/             # Application lifecycle, crash handler, settings
│   │   ├── data/             # Domain models (PeerData, History, Media, Session)
│   │   ├── dialogs/          # Chats list, folder tabs, search indexing
│   │   ├── history/          # Message list rendering, message bubbles, layout engine
│   │   ├── info/             # Profile, shared media, group info panels
│   │   ├── main/             # Main account and session controllers
│   │   ├── mtproto/          # Low-level MTProto protocol implementation
│   │   ├── settings/         # Settings UI, cloud password, privacy toggles
│   │   ├── storage/          # Local encrypted storage (tdata), cache management
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
  - **`Data::Histories` (`History`)**: Message history buffers for all dialogs.
  - **`Data::Peers` (`PeerData`, `UserData`, `ChatData`, `ChannelData`)**: Identity caching, permissions, and profile states.
  - **`Data::CloudThemes`**: Remote and local themes management.

### 3.2 Network & MTProto Pipeline (`Telegram/SourceFiles/mtproto/` & `api/`)
- **`MTP::Instance`**: Top-level protocol coordinator managing connections to Telegram Data Centers (DCs).
- **`MTP::Sender`**: Helper to construct and send typed TL RPC queries with auto-retry, encryption, and deduplication.
- **Multi-Connection MTProto Streaming (Fork Feature `B1`)**:
  - Distributes large media and document chunk downloads across multiple parallel TCP/MTProto connection channels to saturate available bandwidth.
- **Ghost Mode Decoupled Read Receipts (Fork Feature `E3`)**:
  - Intercepts viewport history reading triggers to suppress outbound `messages.readHistory` RPC invocations while maintaining local read state.

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
3. **`Calls::Group::DisplayCoordinator`** *(Fork Component)*:
   - Queries and enumerates system displays (`QScreen`).
   - Manages multi-window routing (Screen 1 vs Screen 2).
   - Prevents active-speaker stream collisions and directs pinned feeds to secondary viewports.
4. **`Calls::Group::FloatingOverlay`** *(Fork Component)*:
   - Frameless, semi-transparent top-most floating window (`Ctrl+Shift+T`).
   - Embeds live chat and search (`MessagesUi`) directly on top of full-screen meetings without stealing window focus.
5. **`Calls::Group::Viewport` & Dynamic Grid Solver**:
   - Dynamically calculates tile geometry: `1×1` (full), `2×2` (50/50), `3×3`, or auto-fit.
   - Handles tile composition using GPU shaders (OpenGL/RHI).
6. **Persistent Pin Allocator**:
   - Manages multiple concurrent participant pins across display changes and resolution adjustments.
7. **Audio Lockout / Zero-Mic Enforcement**:
   - Strips microphone capture pipelines in `tgcalls` for permanent listen-only operation.

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
- **SQLite Database Optimization (Fork Subsystem `C1`)**:
  - Configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and memory-mapped file access (`PRAGMA mmap_size`) for instant local searches and non-blocking reads.

---

## 7. Style & Conventions

- Adheres to repository formatting guidelines detailed in [`REVIEW.md`](file:///C:/Users/kyleh/tdesktop/REVIEW.md).
- Follows build toolchain rules detailed in [`AGENTS.md`](file:///C:/Users/kyleh/tdesktop/AGENTS.md).
- Tracks custom fork features in [`tdesktop_fork_features.md`](file:///C:/Users/kyleh/Desktop/tdesktop_fork_features.md).
