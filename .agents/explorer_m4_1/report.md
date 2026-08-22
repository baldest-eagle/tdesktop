# Milestone M4 — Style & Conventions Audit Report

**Auditor**: Explorer M4.1 (Style & Conventions Specialist)  
**Date**: 2026-08-20  
**Scope**: Complete audit of all modified and added source files across Milestones M1, M2, and M3 against `REVIEW.md` and `AGENTS.md`.

---

## Executive Summary

A comprehensive, line-by-line inspection was performed across all 15 primary target source files (and associated headers/callers) comprising the features delivered in Milestones M1, M2, and M3.

Overall, the codebase demonstrates strong adherence to Telegram Desktop's modern C++20 architecture (e.g., zero uninitialized basic types, proper empty line before closing braces in class definitions with access specifiers, strict zero `Q_OS_LINUX` occurrences, proper binary stream serialization at stream-end for `_ghostMode`, robust `MTP::Sender` and `crl::guard` usage).

However, several mechanical style and formatting discrepancies were identified that should be resolved to achieve 100% compliance with `REVIEW.md` and `AGENTS.md`.

### Audit Scorecard

| Category / Rule | Status | Notes |
|---|---|---|
| **1. No Bloat / Single-Line Comments** | ⚠️ Minor Issues | Bloat comments found in `calls_group_viewport.cpp`, `calls_group_members.cpp`, `calls_group_display_coordinator.cpp`, and dead commented code in `calls_group_viewport.cpp`. |
| **2. `auto` / `const auto &` Deduction** | ⚠️ Minor Issues | Explicit vector typing in `calls_group_viewport.cpp:531` and missing `const` in `calls_group_members.cpp:1984,1991`. |
| **3. `u"..."_q` Literal Usage** | ⚠️ Minor Issues | `QStringLiteral` used in `calls_group_members.cpp:1994` and `calls_group_panel.cpp`; raw string literals used in `calls_group_display_coordinator.cpp:23-26`. |
| **4. No `Q_OS_LINUX` in New Code** | ✅ PASS (100%) | 0 occurrences in all modified/added files. |
| **5. Parameter Continuation (2 Tabs)** | ✅ PASS (100%) | All multi-line function calls and signatures use 2 tabs (`\t\t`). |
| **6. Empty Line Before Class Closing Brace** | ✅ PASS (100%) | All class definitions with access specifiers contain an empty line before `};`. Plain structs are compact without trailing empty line. |
| **7. Include Ordering & Styles Last** | ⚠️ Minor Issues | `styles/style_*.h` placed before Qt/std headers in `calls_group_floating_overlay.cpp`, `calls_group_viewport.cpp`, `calls_group_display_coordinator.cpp`; out-of-order include blocks in `download_manager_mtproto.cpp` and `calls_group_viewport.h/.cpp`. |
| **8. `crl::guard` & `MTP::Sender` Lifetime** | ✅ PASS | `Calls::ShowCallsMenu` uses `crl::guard`; `BoxController` uses `MTP::Sender _api`; `RichTasks` uses safe ID mapping. |
| **9. Basic Type Initialization** | ✅ PASS (100%) | All primitive fields (`int`, `bool`, `float`, pointers) in classes and structs are explicitly initialized. |
| **10. `tr::` Projections for `TextWithEntities`** | ✅ PASS (100%) | All translation keys use live `tr::` producers. |
| **11. Encoding & BOM** | ✅ PASS (100%) | UTF-8 without BOM across all files. |

---

## Detailed File-by-File Analysis

### 1. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h` & `.cpp`
- **Header (`.h`)**:
  - Empty line before closing brace on `class FloatingOverlay`: line 68. (PASS)
  - Member variables initialized (`_dragging = false;`, `_passthrough = false;`, `_opacity = 0.7f;`, `_toggleShortcut = nullptr;`). (PASS)
  - No bloat comments. (PASS)
- **Source (`.cpp`)**:
  - **Include Ordering Violation** (Lines 17-25): `styles/style_calls.h` is included before `<QtGui/...>` and `<QtWidgets/...>`. `styles/style_*.h` must always be placed at the very bottom of the include block, separated by an empty line.
  - Shortcut string literal `u"Ctrl+Shift+T"_q` (line 39) and title `u"Chat"_q` (line 140) use `_q`. (PASS)
  - `isVisible()` delegates to `!isHidden()` (lines 58, 66). (PASS)

---

### 2. `Telegram/SourceFiles/calls/group/calls_group_viewport.h` & `.cpp`
- **Header (`.h`)**:
  - **Include Ordering Violation** (Lines 10-11):
    ```cpp
    #include "ui/rp_widget.h"
    #include "ui/effects/animations.h"
    ```
    Per `REVIEW.md`, nested folders must precede files in the same directory (`ui/effects/animations.h` before `ui/rp_widget.h`).
  - Class `Viewport` has empty line before closing brace (line 250). (PASS)
  - All struct/class fields initialized (`_opengl = false;`, `_qrhi = false;`, `_hasTwoOrMore = false;`, etc.). (PASS)
- **Source (`.cpp`)**:
  - **Include Ordering Violation** (Lines 21-36):
    - `media/view/media_view_pip.h` is before `base/platform/base_platform_info.h` (alphabetical: `base/` before `media/`).
    - `styles/style_calls.h` (line 31) is before `<QOpenGLShader>`, `<QtGui/QtEvents>`, `<QOpenGLWidget>`. Style includes must be last.
  - **Bloat Comments**:
    - Line 29: `#include "data/data_group_call.h" // MuteButtonTooltip.` (trailing include comment).
    - Line 515: `// Allocate pinned tiles to fixed leading slots first` (describes next loop).
    - Lines 529-530: `// Fill remaining slots with unpinned active tiles sorted chronologically by entryTime` / `// (oldest in Slot 0 top-left, newest in bottom-right)`.
  - **Dead Code Block**:
    - Lines 1175-1221: 46 lines of commented-out legacy code in `MuteButtonTooltip`. Should be removed.
  - **Type Deduction**:
    - Line 531: `std::vector<not_null<VideoTile*>> unpinnedTiles;` -> prefer `auto unpinnedTiles = std::vector<not_null<VideoTile*>>();`.

---

### 3. `Telegram/SourceFiles/calls/group/calls_group_members.h` & `.cpp`
- **Header (`.h`)**:
  - Class `Members`: empty line before `};` at line 131. (PASS)
  - **Namespace Mismatch**: Line 31 opens `namespace Calls::Group {`, but line 133 closes with `} // namespace Calls`. Should be `} // namespace Calls::Group`.
- **Source (`.cpp`)**:
  - **Include Ordering Violation** (Line 44): `#include "ui/widgets/fields/input_field.h"` is placed after `webrtc/webrtc_video_track.h`. Alphabetically it belongs under `ui/widgets/` before `webrtc/`.
  - **Bloat Comment** (Line 1982): `// In-call username search bar at the top of the sidebar` (describes following widget).
  - **Literal Syntax** (Line 1994): `rpl::single(QStringLiteral("Search username...")));` -> use `u"Search username..."_q`.
  - **Type Constness**:
    - Line 1984: `auto searchWrap = ...` -> `const auto searchWrap = ...`
    - Line 1991: `auto searchField = ...` -> `const auto searchField = ...`

---

### 4. `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h` & `.cpp`
- **Header (`.h`)**:
  - **Include Ordering Violation** (Line 12): `#include "ui/rp_widget.h"` is placed before `#include "calls/group/..."`. Alphabetical order: `base/`, `calls/`, `ui/`.
  - Class `DisplayCoordinator` has empty line before closing brace (line 119). (PASS)
  - Primitive fields initialized (`_speakerThreshold = 0.05;`, `_speakerHoldFrames = 0;`, `_activeSpeaker = nullptr;`). (PASS)
- **Source (`.cpp`)**:
  - **Include Ordering Violation** (Lines 12-16): `styles/style_calls.h` is placed before `<QtGui/...>` and `<QtWidgets/...>`. Styles must be last.
  - **Literal Syntax** (Lines 23-26):
    ```cpp
    case DisplayRole::ActiveSpeaker: return "Active Speaker";
    case DisplayRole::GridViewport: return "Grid View";
    case DisplayRole::ChatStation: return "Chat Station";
    default: return "";
    ```
    Returns implicit `const char[]` -> `QString` conversions. Should be `u"Active Speaker"_q`, `u"Grid View"_q`, `u"Chat Station"_q`, and `QString()` or `u""_q`.
  - **Bloat Comments**:
    - Line 52: `// Detect existing screens on startup`
    - Line 101: `// Create a top-level window for this display`
    - Line 113: `// Create a Viewport for this display`
    - Line 124: `// Position on the target screen`
    - Line 131: `// Connect quality requests from this viewport`
    - Line 137: `// Set up content`
    - Line 154: `// Clean up routed endpoints for this display`
    - Line 171: `// Set viewport geometry to fill the widget`
  - **Loop Auto Deduction**:
    - Line 67: `for (int i = 0; i < screens.size(); ++i)` -> `for (auto i = 0; i != screens.size(); ++i)`
    - Line 83: `for (int idx : toRemove)` -> `for (const auto idx : toRemove)`

---

### 5. `Telegram/SourceFiles/calls/calls_box_controller.h` & `.cpp`
- **Header (`.h`)**:
  - Includes sorted: `boxes/peer_list_box.h`, `mtproto/sender.h`, `ui/layers/generic_box.h`. (PASS)
  - `ListController` and `BoxController` have empty lines before closing braces. (PASS)
  - `_api` (`MTP::Sender`) member present. (PASS)
  - Fields initialized (`_offsetId = 0;`, `_loadRequestId = 0;`, `_allLoaded = false;`). (PASS)
- **Source (`.cpp`)**:
  - Include block alphabetically sorted, styles placed last separated by empty line. (PASS)
  - `GroupCallRow`: empty line before `};` (line 114). (PASS)
  - `ShowCallsMenu`: All action callbacks guarded with `crl::guard(menu, [=] { ... })` (lines 970, 982, 991). (PASS)
  - `MTPmessages_Search` call uses `_api.request(...)`. (PASS)

---

### 6. `Telegram/SourceFiles/window/window_main_menu.cpp`
- Includes alphabetically sorted, nested folders first, styles last. (PASS)
- `ShowCallsMenu` integration cleanly wired to calls action click handler (line 712). (PASS)
- No bloat comments in added code. (PASS)

---

### 7. `Telegram/SourceFiles/core/core_settings.h` & `.cpp`
- **Header (`.h`)**:
  - `_ghostMode` initialized as `rpl::variable<bool> _ghostMode = false;` (line 1153). (PASS)
  - Empty line before closing brace of `class Settings final` (line 1245). (PASS)
- **Source (`.cpp`)**:
  - `_ghostMode` serialization appended at the **very end** of the binary stream (line 527):
    `stream << qint32(_ghostMode.current() ? 1 : 0);` (PASS)
  - `_ghostMode` deserialization guarded with `!stream.atEnd()` (line 1058-1060):
    ```cpp
    if (!stream.atEnd()) {
        stream >> ghostMode;
    }
    ```
    (PASS)
  - Default fallback initialized before reading (line 634): `qint32 ghostMode = _ghostMode.current() ? 1 : 0;`. (PASS)
  - Adheres 100% to AGENTS.md binary serialization guidelines.

---

### 8. `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
- Ghost Mode section added at lines 1090-1118.
- Uses `u"..."_q` literals for IDs and keywords (`u"privacy/ghost_mode"_q`, `u"ghost"_q`, etc.). (PASS)
- Live `tr::lng_settings_ghost_mode()` producers used. (PASS)
- Correctly bound to `toggle->lifetime()`. (PASS)
- Clean, 0 bloat comments. (PASS)

---

### 9. `Telegram/SourceFiles/data/data_histories.cpp`
- Ghost Mode check in `Histories::sendReadRequest` (lines 716-720):
  ```cpp
  if (Core::App().settings().ghostMode()) {
      state.willReadTill = 0;
      state.willReadWhen = 0;
      return;
  }
  ```
- Suppresses read mark dispatch cleanly. (PASS)

---

### 10. `Telegram/SourceFiles/api/api_rich_tasks.h` & `.cpp`
- **Header (`.h`)**:
  - Includes sorted, class `RichTasks` has trailing empty line before `};` (line 56). (PASS)
  - Struct `Accumulated` has all fields initialized. (PASS)
- **Source (`.cpp`)**:
  - Parameter continuation uses 2 tabs (`\t\t`). (PASS)
  - Multi-line expression operators placed at the start of continuation lines (lines 100-103). (PASS)
  - Zero bloat comments. (PASS)

---

### 11. `Telegram/SourceFiles/storage/download_manager_mtproto.h` & `.cpp`
- **Header (`.h`)**:
  - Class `DownloadManagerMtproto`, `Queue`, and `DownloadMtprotoTask` have empty line before `};`. (PASS)
  - All basic type fields initialized. (PASS)
- **Source (`.cpp`)**:
  - **Include Ordering Violation** (Lines 10-18):
    ```cpp
    #include "mtproto/facade.h"
    #include "mtproto/mtproto_auth_key.h"
    #include "mtproto/mtproto_response.h"
    #include "main/main_session.h"
    #include "data/data_session.h"
    #include "data/data_document.h"
    #include "apiwrap.h"
    #include "base/openssl_help.h"
    ```
    Should be sorted alphabetically (`apiwrap.h`, `base/...`, `data/...`, `main/...`, `mtproto/...`).
  - Constants and multi-session 16 DC downloading logic (`kStartSessionsCount = 4`, `kMaxSessionsCount = 16`) clean. (PASS)

---

### 12. `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`
- Struct `SqlitePragmaConfig` has all fields initialized with `u"..."_q` literals. (PASS)
- `ApplySqlitePerformancePragmas` initializes `stmt = nullptr;` and `walApplied = false;`. (PASS)
- Clean, compact, zero bloat comments. (PASS)

---

### 13. `Telegram/ThirdParty/tgcalls` (`MediaManager.cpp`, `GroupInstanceCustomImpl.cpp`, `InstanceV2Impl.cpp`)
- Jitter buffer fast accelerate (`audio_jitter_buffer_fast_accelerate = true;`) and 50ms min delay (`audio_jitter_buffer_min_delay_ms = 50;`) properly configured.
- Conforms to tgcalls third-party coding patterns. (PASS)

---

## Actionable Remediation Checklist for Worker M4.1

To achieve 100% compliance across the codebase, Worker M4.1 should apply the following targeted fixes:

1. **`calls_group_floating_overlay.cpp`**:
   - Move `#include "styles/style_calls.h"` below the Qt headers `<QtWidgets/QApplication>` with an empty line preceding it.
2. **`calls_group_viewport.h`**:
   - Swap `#include "ui/rp_widget.h"` and `#include "ui/effects/animations.h"` so nested folder `effects/` comes first.
3. **`calls_group_viewport.cpp`**:
   - Reorder `#include "base/platform/base_platform_info.h"` before `media/view/media_view_pip.h`.
   - Move `#include "styles/style_calls.h"` below `<QOpenGLWidget>` at the end of includes.
   - Remove trailing include comment on `#include "data/data_group_call.h"`.
   - Delete single-line bloat comments at lines 515 and 529-530.
   - Delete dead commented-out code in `MuteButtonTooltip` (lines 1175-1202, 1221) and re-indent line 1206.
   - Change `std::vector<not_null<VideoTile*>> unpinnedTiles;` to `auto unpinnedTiles = std::vector<not_null<VideoTile*>>();`.
4. **`calls_group_members.h`**:
   - Fix namespace comment on line 133 to `} // namespace Calls::Group`.
5. **`calls_group_members.cpp`**:
   - Reorder `#include "ui/widgets/fields/input_field.h"` to sit under `ui/widgets/` before `webrtc/`.
   - Delete bloat comment on line 1982 (`// In-call username search bar...`).
   - Replace `QStringLiteral("Search username...")` on line 1994 with `u"Search username..."_q`.
   - Add `const` to `const auto searchWrap` (line 1984) and `const auto searchField` (line 1991).
6. **`calls_group_display_coordinator.h`**:
   - Reorder `#include "ui/rp_widget.h"` to follow `#include "calls/group/..."`.
7. **`calls_group_display_coordinator.cpp`**:
   - Move `#include "styles/style_calls.h"` to the bottom of the include block below `<QtWidgets/QWidget>`.
   - Replace raw string returns in `RoleText` (lines 23-26) with `u"Active Speaker"_q`, `u"Grid View"_q`, `u"Chat Station"_q`, and `QString()`.
   - Delete single-line bloat comments at lines 52, 101, 113, 124, 131, 137, 154, 171.
   - Use `const auto` / `auto` in loops (lines 67, 83).
8. **`download_manager_mtproto.cpp`**:
   - Sort include directives alphabetically:
     ```cpp
     #include "apiwrap.h"
     #include "base/openssl_help.h"
     #include "data/data_document.h"
     #include "data/data_session.h"
     #include "main/main_session.h"
     #include "mtproto/facade.h"
     #include "mtproto/mtproto_auth_key.h"
     #include "mtproto/mtproto_response.h"
     ```
9. **`calls_group_panel.cpp`**:
   - Replace `QStringLiteral(...)` with `u"..."_q` at lines 862, 882, 1478, 1479, 1483, 1487, 1509, 1525.
   - Remove bloat comments at lines 1493, 1519, 1535.
