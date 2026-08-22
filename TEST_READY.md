# E2E Test Suite Ready

## Test Runner
- **Command**: `py tests/e2e/run_all.py`
- **Expected**: All 659 tests pass with exit code 0
- **Filtered Invocations**:
  - Tier 1 only: `py tests/e2e/run_all.py --tier 1`
  - Tier 2 only: `py tests/e2e/run_all.py --tier 2`
  - Tier 3 only: `py tests/e2e/run_all.py --tier 3`
  - Tier 4 only: `py tests/e2e/run_all.py --tier 4`
  - By Feature ID: `py tests/e2e/run_all.py --feature f01`
  - By Category: `py tests/e2e/run_all.py --category "Privacy & Ghost Mode"`
  - With Export: `py tests/e2e/run_all.py --json reports/e2e_results.json --junit reports/junit.xml`

## Coverage Summary
| Tier | Count | Description |
|------|------:|-------------|
| 1. Feature Coverage | 285 | 5 test cases per feature across all 57 features (13 categories) |
| 2. Boundary & Corner Cases | 285 | 5 boundary/corner test cases per feature across all 57 features |
| 3. Cross-Feature Combinations | 60 | Pairwise combinatorial interactions between major subsystem features |
| 4. Real-World Application Workloads | 29 | Comprehensive multi-step real-world end-user workflow application scenarios |
| **Total** | **659** | Complete opaque-box automated test coverage (exceeds 656 minimum) |

## Feature Checklist
| # | Feature | Category | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|----------|:------:|:------:|:------:|:------:|
| 1 | Ghost Mode (Decoupled Read Receipts) | Privacy & Ghost Mode (E3) | 5 | 5 | ✓ | ✓ |
| 2 | Ghost Mode Settings UI & Persistence | Privacy & Ghost Mode (E3) | 5 | 5 | ✓ | ✓ |
| 3 | Multi-Connection MTProto Chunk Downloading | Network & Download (B1) | 5 | 5 | ✓ | ✓ |
| 4 | Grid Mode Toggle | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 5 | In-Call Chat Panel Slide-Out | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 6 | End Call Button & Hover Controls | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 7 | Camera & Participant Bar Controls | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 8 | CallButton to IconButton Migration | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 9 | callCancelRipple Palette Color | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 10 | Hidden Floating PiP Camera Preview | Call UI & Controls | 5 | 5 | ✓ | ✓ |
| 11 | Multi-Monitor Stage Window Support | Multi-Display & Routing | 5 | 5 | ✓ | ✓ |
| 12 | Dual Initial Windows Prompt | Multi-Display & Routing | 5 | 5 | ✓ | ✓ |
| 13 | Display Role Router | Multi-Display & Routing | 5 | 5 | ✓ | ✓ |
| 14 | Async Video Stream Routing | Multi-Display & Routing | 5 | 5 | ✓ | ✓ |
| 15 | Secondary Display Active-Speaker Isolation | Multi-Display & Routing | 5 | 5 | ✓ | ✓ |
| 16 | Discrete Layout Presets (1x1, 2x2, 3x3) | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 17 | Dynamic Grid Solver (50/50 Split) | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 18 | Uncapped Dynamic Main Grid Scaling | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 19 | Persistent Pin Slot Allocator | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 20 | Per-Window Dynamic Pinned Auto-Scaling | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 21 | Multi-Pin Capability | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 22 | Adjustable Pinned Panel Sizes | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 23 | Grid Unpinning & Removal Actions | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 24 | Pin to Grid Context Menu Actions | Grid Layout & Pin System | 5 | 5 | ✓ | ✓ |
| 25 | Frameless Transparent Top-Most Overlay | Floating Overlay | 5 | 5 | ✓ | ✓ |
| 26 | Ctrl+Shift+T Keyboard Toggle | Floating Overlay | 5 | 5 | ✓ | ✓ |
| 27 | Opacity Adjustment via Ctrl+Wheel | Floating Overlay | 5 | 5 | ✓ | ✓ |
| 28 | Draggable Canvas & Escape to Dismiss | Floating Overlay | 5 | 5 | ✓ | ✓ |
| 29 | Embedded Chat & Dynamic Resize | Floating Overlay | 5 | 5 | ✓ | ✓ |
| 30 | In-Meeting Chat Search | Floating Overlay | 5 | 5 | ✓ | ✓ |
| 31 | Chronological Entry-Time Grid Sorting | Participant Sidebar & Search | 5 | 5 | ✓ | ✓ |
| 32 | Alphabetical Sidebar Sorting | Participant Sidebar & Search | 5 | 5 | ✓ | ✓ |
| 33 | In-Call Sidebar Search Bar | Participant Sidebar & Search | 5 | 5 | ✓ | ✓ |
| 34 | Search Results Quick Actions | Participant Sidebar & Search | 5 | 5 | ✓ | ✓ |
| 35 | Audio Lockout / Listen-Only Mode | Audio / Microphone | 5 | 5 | ✓ | ✓ |
| 36 | Microphone Controls Removal | Audio / Microphone | 5 | 5 | ✓ | ✓ |
| 37 | Permanent Listen-Only Invariant | Audio / Microphone | 5 | 5 | ✓ | ✓ |
| 38 | Calls Submenu in Main Menu | Main Menu & Navigation | 5 | 5 | ✓ | ✓ |
| 39 | Wallet Entry with NEW Badge | Main Menu & Navigation | 5 | 5 | ✓ | ✓ |
| 40 | Wide/Grid Obstructing Button Cleanup | UI Tweaks & Polish | 5 | 5 | ✓ | ✓ |
| 41 | Titlebar Close Wired to Hangup | UI Tweaks & Polish | 5 | 5 | ✓ | ✓ |
| 42 | Screen Share & Message Toggle Icons | UI Tweaks & Polish | 5 | 5 | ✓ | ✓ |
| 43 | Multi-Pin Hover Controls | UI Tweaks & Polish | 5 | 5 | ✓ | ✓ |
| 44 | Window-Level Ctrl+Shift+T Key Handler | UI Tweaks & Polish | 5 | 5 | ✓ | ✓ |
| 45 | Rich Tasks (Checklist Items) | Context Menus & Cross-UI | 5 | 5 | ✓ | ✓ |
| 46 | Cross-UI Pin to Grid Actions | Context Menus & Cross-UI | 5 | 5 | ✓ | ✓ |
| 47 | Screen Target Pinning Prompt | Context Menus & Cross-UI | 5 | 5 | ✓ | ✓ |
| 48 | Stream Thumbnail Unpin Action Dialog | Context Menus & Cross-UI | 5 | 5 | ✓ | ✓ |
| 49 | Central Call & State Controller | Backend / Engine | 5 | 5 | ✓ | ✓ |
| 50 | Simulcast Upscaling Signaling | Backend / Engine | 5 | 5 | ✓ | ✓ |
| 51 | Active-Speaker Hysteresis | Backend / Engine | 5 | 5 | ✓ | ✓ |
| 52 | TrackPeer & Endpoint Routing Cleanup | Backend / Engine | 5 | 5 | ✓ | ✓ |
| 53 | SQLite PRAGMA Optimizations (C1) | Backend / Engine | 5 | 5 | ✓ | ✓ |
| 54 | WebRTC Playout Delay & Jitter Clamping (A1) | Backend / Engine | 5 | 5 | ✓ | ✓ |
| 55 | Windows Native Build Guide | Build & Toolchain | 5 | 5 | ✓ | ✓ |
| 56 | CMakeLists.txt Source Synchronization | Build & Toolchain | 5 | 5 | ✓ | ✓ |
| 57 | Fork Localization Language Keys | Build & Toolchain | 5 | 5 | ✓ | ✓ |
