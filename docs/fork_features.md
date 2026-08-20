# Telegram Desktop Fork — Requested Features, Tweaks & Customizations

Working directory: `C:\Users\kyleh\tdesktop`, branch `nightly`

---

## Privacy & Ghost Mode (E3)
- **Ghost Mode (Decoupled Read Receipts)** — suppresses outgoing MTProto read marks (`readHistory`), allowing stealth message viewing without notifying the sender.
- **Ghost Mode Settings UI & Persistence** — dedicated setting toggle in Telegram settings and persistent state serialization across client restarts.

## Network & Download Throughput (B1)
- **Multi-Connection MTProto Chunk Downloading** — parallel MTProto download stream connections for saturated bandwidth and faster media/file downloads.

## Call UI & Controls
- **Grid Mode toggle** — button in call controls that switches viewport to `PanelMode::Grid` with reactive state
- **Chat panel toggle** — translucent panel slides out inside call window (top-left close, `Ui::RoundRect` corners, 0.9 opacity)
- **End call button & hover controls** — integrated into bordering UI or made more discrete (tiny icons in corner)
- **Camera/people controls** — added to call controls
- **CallButton → IconButton** — convert base struct for style consistency
- **callCancelRipple color** — added `callCancelRipple: #c04646` to `ui/colors.palette`
- **Hidden Floating PiP Camera Preview** — removed small floating picture-in-picture webcam overlay from cluttering call layouts

## Multi-Display & Routing (DisplayCoordinator)
- **Multi-monitor support** — route video feeds to secondary displays
- **Dual Initial Windows prompt** — choose Screen 1 vs Screen 2 for pinning
- **Display Role Router** — enumerate `QScreen` objects, assign output viewports (Primary Monitor, Snap Grid, Dedicated Chat & Search)
- **Async video routing** — route active speaker to secondary display
- **Secondary display ActiveSpeaker & video routing polish** — disabled random auto-filling / active-speaker slot hijacking on 2nd screen

## Grid Layout & Pin System
- **Discrete Layout Presets** — 1×1, 2×2, 3×3 grid configurations
- **Dynamic Grid Solver** — auto-scaling: 1=full, 2=50/50, 4=2x2, 9=3x3
- **Uncapped Dynamic Main Grid Scaling** — restored unrestricted dynamic viewport scaling for multi-participant layouts on the primary grid
- **Persistent Pin Slot Allocator** — lock participants to grid slots across layout changes
- **Per-Window Dynamic Pinned Auto-Scaling** — 1 to 9 feeds with persistent assignments
- **Multi-pin options** — pin multiple participants simultaneously
- **Adjustable pinned panel sizes** — resizable video panels
- **Grid unpinning & removal** — explicit "Unpin / Remove from Screen" actions and dialogs for pinned feeds
- **Pin to Grid context menu actions** — injected into history, view, and search menus

## Floating Overlay
- **Frameless transparent top-most window** — semi-transparent, always on top
- **Ctrl+Shift+T toggle** — show/hide overlay with mouse-passthrough
- **Opacity controls** — adjustable transparency
- **Draggable + Escape to dismiss**
- **Chat content & dynamic resize binding** — fill overlay with MessagesUi
- **In-meeting chat and search** within overlay

## Participant Sidebar & Search
- **Entry-time chronological grid sorting** — grid sorted by participant entry time
- **Alphabetical sidebar** — alphabetical sorting of participant list
- **In-call sidebar searchbar** — layout-anchored search field at top of sidebar for participant filtering
- **Direct "Pin to Screen" & "Open Chat"** — from search results

## Audio / Microphone
- **Audio Lockout / Listen-only mode** — strip microphone capture pipeline in `tgcalls`
- **Remove microphone toggle buttons** — from call UI when in lockout mode
- **Permanent listen-only enforcement** — zero-mic enforcement in Central Call & State Controller

## Main Menu & Navigation
- **Replace "Calls" button with folder/submenu** — show calls groups inline instead of opening popup box
- **Wallet** — main menu entry with green `NEW` badge under My Profile

## UI Tweaks & Polish
- **Remove obstructing floating on-screen buttons** — in wide/grid mode
- **Wire titlebar close to hangup** — close button ends call
- **Replace menu toggle icons** — screen share and message style icons
- **Wire multi-pin click toggling + hover controls in grid mode**
- **Window-level Ctrl+Shift+T shortcut** — for floating overlay

## Context Menus & Cross-UI
- **Rich Tasks** — right-click message with checklist to mark items complete via `api_rich_tasks`
- **"Pin to Grid"** — in history, view, search context menus
- **Screen target pinning prompt** — Screen 1 vs Screen 2 selection dialog
- **Unpin Action Dialog** — unpin feeds directly from stream thumbnails and context menus

## Backend / Engine
- **Central Call & State Controller** — manages Participants Cache, Pinned Slot Allocator, WebRTC Subscriptions, Zero-Mic Enforcement
- **Simulcast upscaling signaling** — for pinned participants
- **Active-speaker hysteresis** — prevent rapid speaker-switching flapping
- **TrackPeer & endpoint routing cleanup** — `0b263e0608`
- **SQLite PRAGMA Optimizations (C1 - In Progress)** — WAL journaling and `mmap_size` memory-mapped I/O tuning for local database speed
- **WebRTC Playout Delay & Jitter Clamping (A1 - Planned)** — jitter buffer optimization and reduced playout latency for live WebRTC audio/video streams

## Build & Toolchain
- **Windows native build guide** — `README-WINDOWS-BUILD.md`
- **CMakeLists.txt** updated for new source files
- **Language keys** — `lng_group_call_open_chat`, `lng_group_call_context_pin_to_grid`

---

> Last updated: August 20, 2026 | Branch 33 commits ahead of `upstream/nightly`
