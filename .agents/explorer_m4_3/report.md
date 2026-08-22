# Comprehensive Localization Strings, Header & Symbol Integrity Audit Report (Milestone M4)

**Auditor:** Explorer M4.3  
**Date:** 2026-08-20  
**Scope:** Milestones M1, M2, M3, M4 across Telegram Desktop fork repository  

---

## Executive Summary

A comprehensive audit was performed across the Telegram Desktop codebase to verify:
1. **Localization Strings Integrity (`lang.strings`)**: Verification of all fork localization keys across Milestones M1-M4, ensuring zero missing keys, zero syntax errors, and zero duplicate entries.
2. **Exported & Referenced Symbol Integrity**: Exhaustive validation of function signatures, calling conventions, class declarations, and implementations for all fork modifications (Calls submenu, Floating Overlay, SQLite PRAGMA tuning, Multi-Connection MTProto chunk downloading, Rich Tasks checklist toggling, and WebRTC jitter clamping).
3. **Header, Include & Namespace Integrity**: Verification of header guards, absence of circular include graphs, correct forward declarations, and namespace consistency.

**Audit Status:** **PASS (CLEAN)**  
All required localization strings, symbols, header guards, namespaces, and call sites are verified to be complete, correct, and compliant with repository conventions (`REVIEW.md` and `AGENTS.md`).

---

## 1. Localization Strings Audit (`Telegram/Resources/langs/lang.strings`)

### 1.1 Verified Fork Keys Table

| Language Key | Line in `lang.strings` | Translation Value | Referenced By | Verification Status |
|---|---|---|---|---|
| `lng_group_call_context_pin_to_grid` | 6463 | `"Pin to grid"` | `calls_group_members.cpp:1452` | **VERIFIED (Valid, Unique)** |
| `lng_group_call_open_chat` | 6464 | `"Open Chat"` | `calls_group_members.cpp:1536` | **VERIFIED (Valid, Unique)** |
| `lng_menu_calls` | 12 | `"Calls"` | `window_main_menu.cpp:705` | **VERIFIED (Valid, Unique)** |
| `lng_settings_ghost_mode` | 902 | `"Ghost Mode"` | `settings_privacy_security.cpp:1094, 1100` | **VERIFIED (Valid, Unique)** |
| `lng_settings_ghost_mode_about` | 903 | `"Messages are marked as read locally, but read receipts are not sent to the server. The blue checkmarks are hidden from the sender."` | `settings_privacy_security.cpp:1117` | **VERIFIED (Valid, Unique)** |
| `lng_call_box_title` | 6306 | `"Calls"` | `calls_box_controller.cpp:541, 889, 990` | **VERIFIED (Valid, Unique)** |
| `lng_call_box_clear_all` | 6312 | `"Clear All"` | `calls_box_controller.cpp:912` | **VERIFIED (Valid, Unique)** |
| `lng_call_box_groupcalls_subtitle` | 6315 | `"Active video chats"` | `calls_box_controller.cpp:859, 958` | **VERIFIED (Valid, Unique)** |
| `lng_confcall_create_call` | 6588 | `"Start New Call"` | `calls_box_controller.cpp:800, 981` | **VERIFIED (Valid, Unique)** |

### 1.2 Syntax and Duplicate Check
- **Duplicate Check**: Exact pattern searches confirmed that each of the fork keys appears exactly once in `Telegram/Resources/langs/lang.strings`.
- **Syntax Validation**: All keys follow the required `"key" = "value";` format with proper quote escaping and terminating semicolons.
- **Pluralization Rules**: Standard `#one`/`#other` keys (e.g. `lng_confcall_create_call_description#one`, `lng_confcall_create_call_description#other`) follow Qt/tdesktop localization format.

---

## 2. Exported & Referenced Symbol Integrity Audit

### 2.1 `::Calls::ShowCallsMenu` Integration
- **Header Declaration** (`Telegram/SourceFiles/calls/calls_box_controller.h:89-91`):
  ```cpp
  namespace Calls {
  void ShowCallsMenu(
      not_null<Ui::PopupMenu*> menu,
      not_null<::Window::SessionController*> window);
  }
  ```
- **Definition** (`Telegram/SourceFiles/calls/calls_box_controller.cpp:931-995`):
  Implements dynamic population of active group calls (`GroupCalls::ListController`), Start New Call action (`Calls::Group::PrepareCreateCallBox`), and Call History box (`Calls::ShowCallsBox`), utilizing `crl::guard(menu, ...)` for lifetime safety.
- **Call Site** (`Telegram/SourceFiles/window/window_main_menu.cpp:708-714`):
  ```cpp
  calls->setClickedCallback([=] {
      _contextMenu = base::make_unique_q<Ui::PopupMenu>(
          calls,
          st::popupMenuWithIcons);
      ::Calls::ShowCallsMenu(_contextMenu.get(), controller);
      _contextMenu->popup(QCursor::pos());
  });
  ```
  **Status**: Fully aligned. Argument types (`not_null<Ui::PopupMenu*>`, `not_null<::Window::SessionController*>`) match declaration.

### 2.2 `FloatingOverlay::setupChatContent` Integration
- **Header Declaration** (`Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h:50`):
  ```cpp
  namespace Calls::Group {
  class FloatingOverlay final : public QWidget {
      ...
      void setupChatContent();
      ...
  };
  }
  ```
- **Definition** (`Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp:154-167`):
  ```cpp
  void FloatingOverlay::setupChatContent() {
      const auto call = _panel->call();
      _messagesUi = std::make_unique<MessagesUi>(
          this,
          _panel->uiShow(),
          MessagesMode::GroupCall,
          call->messages()->listValue(),
          nullptr,
          call->messages()->idUpdates(),
          call->canManageValue(),
          call->messagesEnabledValue(),
          [=](QPoint) { return false; });
      _messagesUi->move(4, height() - 4, width() - 8, height() - 40);
  }
  ```
  **Status**: Fully aligned. Constructor arguments match `MessagesUi` (`calls_group_messages_ui.h:53-62`).

### 2.3 `ApplySqlitePerformancePragmas` & SQLite C1 Optimization
- **Header Definition** (`Telegram/SourceFiles/storage/storage_sqlite_pragmas.h:17-81`):
  - Namespace: `Storage`
  - Guarded by `#if defined(SQLITE_OK) || defined(_SQLITE3_H_)` for safe inclusion before or after SQLite engine headers.
  - `BuildPragmaStatements()` provided for connection initialization strings:
    - `PRAGMA journal_mode = WAL;` (with fallback to `TRUNCATE`)
    - `PRAGMA mmap_size = 268435456;` (256 MB)
    - `PRAGMA synchronous = NORMAL;`
    - `PRAGMA cache_size = -64000;` (64 MB)
    - `PRAGMA temp_store = MEMORY;`
  **Status**: Verified clean.

### 2.4 `DownloadManagerMtproto` (Multi-Connection MTProto Chunk Downloading)
- **Header & Implementation** (`storage/download_manager_mtproto.h`, `storage/download_manager_mtproto.cpp`):
  - Saturated multi-connection downloading: `kMaxSessionsCount = 16;` (line 26).
  - All public and private methods fully declared and defined:
    - `changeRequestedAmount(MTP::DcId dcId, int index, int delta)`
    - `requestSucceeded(MTP::DcId dcId, int index, int amountAtRequestStart, crl::time timeAtRequestStart)`
    - `checkSendNextAfterSuccess(MTP::DcId dcId)`
    - `chooseSessionIndex(MTP::DcId dcId) const`
    - `enqueue(not_null<Task*> task, int priority)`, `remove(not_null<Task*> task)`
    - `notifyTaskFinished()`, `taskFinished()`, `notifyNonPremiumDelay(DocumentId id)`
    - `killSessionsSchedule()`, `killSessionsCancel()`, `killSessions()`
  **Status**: 100% symbol completeness and signature matching.

### 2.5 `Api::RichTasks` (Checklist Items Toggle)
- **Header & Implementation** (`api/api_rich_tasks.h`, `api/api_rich_tasks.cpp`):
  - Methods: `togglingAllowed(not_null<HistoryItem*> item)`, `toggle(not_null<HistoryItem*> item, const Iv::Markdown::PreparedEditListItemSource &source)`, `sendAccumulated()`, `send(...)`, `finishRequest(...)`.
  - Integration: Wired into `ApiWrap` (`apiwrap.h:459, 832`, `apiwrap.cpp:223, 5705-5706`) and `HistoryView::Message` (`history_view_message.cpp:4522, 4535`).
  **Status**: 100% symbol completeness and wiring.

### 2.6 `tgcalls` & `MediaManager` (WebRTC Playout Jitter Clamping A1)
- **Files Modified**:
  - `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp:364-365`
  - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`
  - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2Impl.cpp:344-345`
- **Configuration Injected**:
  ```cpp
  audioOptions.audio_jitter_buffer_fast_accelerate = true;
  audioOptions.audio_jitter_buffer_min_delay_ms = 50;
  ```
  **Status**: Verified in cricket::AudioOptions and peer connection configuration across all tgcalls instance implementations.

### 2.7 Ghost Mode Binary Serialization
- **Implementation** (`core/core_settings.h:784-795, 1153`, `core/core_settings.cpp:349, 527, 634, 1059, 1246`):
  - Serialization: Appended at end of stream (`stream << qint32(_ghostMode.current() ? 1 : 0);`).
  - Deserialization: Guarded with `if (!stream.atEnd()) { stream >> ghostMode; }`.
  - Suppression: `Histories::sendReadRequest` (`data/data_histories.cpp:716-720`) returns early when `Core::App().settings().ghostMode()` is true.
  **Status**: Adheres strictly to binary serialization backward-compatibility rules.

---

## 3. Header, Namespace & Dependency Integrity Audit

### 3.1 Header Guards Check
All inspected headers contain valid header guards:
- `#pragma once` in:
  - `Telegram/SourceFiles/calls/calls_box_controller.h`
  - `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
  - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h`
  - `Telegram/SourceFiles/calls/group/calls_group_viewport.h`
  - `Telegram/SourceFiles/calls/group/calls_group_members.h`
  - `Telegram/SourceFiles/calls/group/calls_group_panel.h`
  - `Telegram/SourceFiles/calls/group/calls_group_messages_ui.h`
  - `Telegram/SourceFiles/calls/group/calls_group_common.h`
  - `Telegram/SourceFiles/calls/calls_instance.h`
  - `Telegram/SourceFiles/calls/calls_panel.h`
  - `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`
  - `Telegram/SourceFiles/storage/download_manager_mtproto.h`
  - `Telegram/SourceFiles/api/api_rich_tasks.h`
  - `Telegram/SourceFiles/core/core_settings.h`
  - `Telegram/SourceFiles/window/window_main_menu.h`
- Standard `#ifndef TGCALLS_* / #define TGCALLS_*` guards in `Telegram/ThirdParty/tgcalls/` headers.

### 3.2 Circular Include Analysis
- **`calls_box_controller.h` ↔ `window_main_menu.h`**: Forward declaration of `namespace Window { class SessionController; }` in `calls_box_controller.h` avoids circularity; `window_main_menu.cpp` includes `calls_box_controller.h` in translation unit.
- **`calls_group_floating_overlay.h` ↔ `calls_group_panel.h`**: `calls_group_floating_overlay.h` forward-declares `class Panel;` and `class MessagesUi;`. `calls_group_panel.h` includes `calls_group_floating_overlay.h`. No circular include cycle.
- **`calls_group_display_coordinator.h` ↔ `calls_group_panel.h`**: `calls_group_display_coordinator.h` forward declares `QWidget` and includes `calls_group_call.h`/`calls_group_viewport.h`, but not `calls_group_panel.h`. Clean DAG (Directed Acyclic Graph).
- **`api_rich_tasks.h` ↔ `apiwrap.h`**: `api_rich_tasks.h` forward declares `class ApiWrap;`. `apiwrap.h` forward declares `namespace Api { class RichTasks; }`. Clean DAG.

### 3.3 Namespace Consistency
| Component | Declared Namespace | Implementation Namespace | Consistency |
|---|---|---|---|
| Floating Overlay | `Calls::Group` | `Calls::Group` | **MATCH** |
| Display Coordinator | `Calls::Group` | `Calls::Group` | **MATCH** |
| Viewport & Viewport Tiles | `Calls::Group` | `Calls::Group` | **MATCH** |
| Calls Box & Menu Controller | `Calls`, `Calls::GroupCalls` | `Calls`, `Calls::GroupCalls` | **MATCH** |
| Main Menu & Helpers | `Window` | `Window` | **MATCH** |
| Storage Pragmas & Download Manager | `Storage` | `Storage` | **MATCH** |
| Rich Tasks | `Api` | `Api` | **MATCH** |
| Core Settings | `Core` | `Core` | **MATCH** |
| WebRTC / tgcalls | `tgcalls` | `tgcalls` | **MATCH** |

### 3.4 CMake Registration Check
- `Telegram/CMakeLists.txt` registers:
  - `calls/calls_box_controller.cpp`, `calls/calls_box_controller.h` (lines 464-465)
  - `calls/group/calls_group_floating_overlay.cpp`, `calls/group/calls_group_floating_overlay.h` (lines 458-459)
  - `calls/group/calls_group_display_coordinator.cpp`, `calls/group/calls_group_display_coordinator.h` (lines 456-457)
  - `calls/group/calls_group_viewport.cpp`, `calls/group/calls_group_viewport.h` (lines 448-449)
  - `calls/group/calls_group_members.cpp`, `calls/group/calls_group_members.h` (lines 424-425)
  - `api/api_rich_tasks.cpp`, `api/api_rich_tasks.h` (lines 199-200)
  - `storage/download_manager_mtproto.cpp`, `storage/download_manager_mtproto.h` (lines 1850-1851)
- *Note*: `storage/storage_sqlite_pragmas.h` is a header-only utility; its inclusion in `Telegram/CMakeLists.txt` can optionally be added under `storage/` for Visual Studio solution tree completeness.

---

## 4. Conclusion & Audit Sign-Off

The localization keys, symbol declarations, method implementations, header guards, and namespaces across Milestones M1 through M4 have been thoroughly audited and verified. No broken references, missing language strings, syntax errors, or circular dependencies exist.
