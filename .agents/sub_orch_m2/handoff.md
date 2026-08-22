# Sub-Orchestrator Handoff Report: Milestone M2 (Navigation & Calls Menu Integration)

**Milestone**: M2 (Navigation & Calls Menu Integration)  
**Parent Orchestrator**: `5278ca9a-12ca-434c-963d-a5a03310dd33`  
**Sub-Orchestrator Directory**: `c:\Users\kyleh\tdesktop\.agents\sub_orch_m2\`  
**Date**: 2026-08-20  
**Gate Result**: **PASS** (Reviewers: 2/2 APPROVE, Challengers: 2/2 APPROVE, Forensic Auditor: CLEAN)

---

## 1. Observation

All Milestone M2 scope items have been implemented, refined, adversarially stress-tested, independently reviewed, and forensically audited across 8 owned files:

### 1.1 Calls Popup Menu Integration & Wallet Entry (`window_main_menu.cpp`)
- **Calls Popup Menu Wiring (lines 704–714)**:
  ```cpp
  		const auto calls = addAction(
  			tr::lng_menu_calls(),
  			{ &st::menuIconPhone }
  		);
  		calls->setClickedCallback([=] {
  			_contextMenu = base::make_unique_q<Ui::PopupMenu>(
  				calls,
  				st::popupMenuWithIcons);
  			::Calls::ShowCallsMenu(_contextMenu.get(), controller);
  			_contextMenu->popup(QCursor::pos());
  		});
  ```
  Replaced direct modal `Calls::ShowCallsBox` call with dynamic `Ui::PopupMenu` popup populated via `::Calls::ShowCallsMenu` adhering to `PROJECT.md:84–85` and `docs/fork_features.md:61`.
- **Wallet Menu Entry (lines 663–678)**:
  `SetupMenuBots(_menu, controller)` is positioned directly beneath "My Profile" (`tr::lng_menu_my_profile()`) and renders TON Wallet with the green `NEW` badge (`Ui::NewBadge::AddToRight(button)` using `st::windowBgActive`) adhering to `docs/fork_features.md:62`.
- **Include Formatting (lines 71–75)**:
  Alphabetical includes with style headers segregated by a blank line and trailing comments removed.

### 1.2 Calls Box Controller Interface & Polish (`calls_box_controller.h/.cpp`)
- **Header (`calls_box_controller.h`)**:
  Folder-first sorted includes, C++17 nested namespace `namespace Calls::GroupCalls {`, and clean declaration of `ShowCallsMenu`.
- **Implementation (`calls_box_controller.cpp:931–995`)**:
  - `ShowCallsMenu` dynamically populates active group calls, Start Group Call action (`Calls::Group::PrepareCreateCallBox`), and Call History action (`Calls::ShowCallsBox`).
  - Parameter continuation indentation formatted with 2 tabs (`\t\t`).
  - All action callbacks guarded against popup dismissal via `crl::guard(menu, [=] { ... })`.

### 1.3 Ghost Mode Settings & Binary Serialization (`core_settings.h/.cpp`, `settings_privacy_security.cpp`, `data_histories.cpp`)
- **Core Settings Binary Stream Alignment (`core_settings.cpp:349, 527, 1058–1060, 1246`)**:
  `_ghostMode` (+`sizeof(qint32)`) serialization relocated strictly to the tail of the stream after `_chatFiltersTabsMode` with `!stream.atEnd()` guarded deserialization, guaranteeing 100% backward compatibility with legacy `tdata` formats per `AGENTS.md`.
- **Settings UI Toggle Pointer Fix (`settings_privacy_security.cpp:1088–1118`)**:
  `const auto settings = &Core::App().settings();` resolves pointer decay and properly updates singleton application settings on toggle changes.
- **Read Receipt Suppression (`data_histories.cpp:713–721`)**:
  `Histories::sendReadRequest` zeroes `willReadTill`/`willReadWhen` and returns early when `ghostMode()` is true, suppressing outgoing `MTPmessages_ReadHistory` and `MTPchannels_ReadHistory` network packets while retaining local unread count/notification clearing. Single-line descriptive comments removed.

### 1.4 Rich Tasks Markdown Checklists (`api_rich_tasks.h/.cpp`)
- **Iterator Safety Bug Fix (`api_rich_tasks.cpp:83–88`)**:
  Removed in-loop `_entries.remove(itemId)` in `RichTasks::send` to prevent iterator invalidation during range-for loop in `sendAccumulated()`.
- **Debounce & Rollback**:
  1000ms debounce interval, optimistic UI updates via `applyLocalRichPage`, and error rollback via snapshot `entry.original` verified.

---

## 2. Logic Chain

1. **Popup Menu Lifetime & Synchronization**:
   - Assigning a fresh popup menu to `MainMenu::_contextMenu` via `base::make_unique_q` synchronously deletes any previous active menu, cancelling previous lifetime subscriptions and safely dropping pending callbacks without memory leaks.
2. **Backward-Compatible Binary Serialization**:
   - Appending `_ghostMode` to the tail of `Core::Settings` binary stream ensures legacy profiles deserialize without offset shifts, while modern profiles accurately persist user ghost mode preferences across restarts.
3. **Protocol Decoupling**:
   - Intercepting `sendReadRequest` in `data_histories.cpp` prevents outgoing read marks from ever being constructed or transmitted over MTProto, achieving true stealth reading while local UI and notifications operate normally.
4. **Adversarial & Forensic Verification**:
   - Zero hardcoded test values, zero facade implementations, zero bypasses. All code is authentic, functional, and fully conforms to `REVIEW.md` and `AGENTS.md`.

---

## 3. Caveats

- **Ghost Mode Cross-Device State**:
  - When Ghost Mode is active, read progress is maintained locally in the client database and memory, but never synchronized to the Telegram cloud or remote peers. Secondary devices logged into the same account will continue to display unread badges until read with Ghost Mode disabled. This is the intended behavior per `docs/fork_features.md:8`.

---

## 4. Conclusion & Gate Verdicts

| Role | Subagent Name | Verdict |
|---|---|---|
| Worker | `worker_m2_2` | **DONE** (Clean implementation & verification) |
| Primary Reviewer | `reviewer_m2_1` | **APPROVE** |
| Secondary Reviewer | `reviewer_m2_2` | **APPROVE** |
| UI / Lifecycle Challenger | `challenger_m2_1` | **APPROVE** |
| Persistence / Protocol Challenger | `challenger_m2_2` | **APPROVE** |
| Forensic Auditor | `auditor_m2_1` | **CLEAN** |

**Milestone M2 Gate Result: PASS**

---

## 5. Verification Method

1. **Source Inspection**:
   - `Telegram/SourceFiles/window/window_main_menu.cpp:704–714` (Calls popup menu wiring).
   - `Telegram/SourceFiles/window/window_main_menu.cpp:663–678` (Wallet placement under My Profile with green NEW badge).
   - `Telegram/SourceFiles/calls/calls_box_controller.h:18, 89–91` and `calls_box_controller.cpp:931–995` (`ShowCallsMenu` implementation).
   - `Telegram/SourceFiles/core/core_settings.cpp:349, 527, 1058–1060, 1246` (`_ghostMode` tail serialization).
   - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp:1088–1118` (Ghost mode UI toggle & pointer fix).
   - `Telegram/SourceFiles/data/data_histories.cpp:713–721` (Ghost mode read receipt suppression).
   - `Telegram/SourceFiles/api/api_rich_tasks.cpp:83–88` (Rich tasks iterator safety fix).
2. **Build Target**:
   ```bash
   cmake --build out --config Debug --target Telegram
   ```
