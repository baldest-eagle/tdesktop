# Handoff Report: Milestone M2 — Rich Tasks Investigation & Scope-Wide Style/Convention Audit (Explorer 3)

## 1. Observation

### 1.1 Rich Tasks Implementation & Lifecycle (`api_rich_tasks.h` / `api_rich_tasks.cpp`)
- **Header**: `Telegram/SourceFiles/api/api_rich_tasks.h`
  - Declares `class RichTasks final` owned as `_richTasks` (`std::unique_ptr<Api::RichTasks>`) by `ApiWrap` (`apiwrap.h:459, 832`), lifetime bound to `Main::Session`.
  - Methods:
    - `[[nodiscard]] bool togglingAllowed(not_null<HistoryItem*> item) const;` (lines 34)
    - `void toggle(not_null<HistoryItem*> item, const Iv::Markdown::PreparedEditListItemSource &source);` (lines 35–37)
  - Data structure:
    - `struct Accumulated { std::shared_ptr<const Iv::RichPage> original; crl::time scheduled = 0; mtpRequestId requestId = 0; bool dirty = false; };`
    - `base::flat_map<FullMsgId, Accumulated> _entries;`
    - `base::Timer _sendTimer;`
- **Implementation**: `Telegram/SourceFiles/api/api_rich_tasks.cpp`
  - **Debounce Logic (lines 23, 57–81)**:
    - Constant delay `kSendDelay = crl::time(1000)` (1 second).
    - When `toggle()` is called on an item:
      - Validates `togglingAllowed(item)` (`page && !page->part && item->allowsEdit(base::unixtime::now())`).
      - Clones `Iv::RichPage(*was)` and modifies state via `Iv::Editor::State(page, nullptr).toggleTaskState(source)`.
      - Preserves initial unmodified page snapshot in `entry.original = was` for rollback on error.
      - Sets `entry.dirty = true` and `entry.scheduled = crl::now()`.
      - Optimistically applies local UI update: `item->applyLocalRichPage(std::move(page));`.
      - Dispatches `_sendTimer.callOnce(kSendDelay)` if not already pending.
    - When `sendAccumulated()` triggers:
      - Computes elapsed time `wait = entry.scheduled + kSendDelay - now`.
      - If `wait <= 0`, calls `send(itemId, entry)`. Otherwise reschedules timer for `nearest`.
  - **API Request Pattern & Session Lifetime Guarding (lines 83–110)**:
    - Uses `EditRichMessage(item, ...)` in `api/api_editing.h/.cpp` which builds `MTPmessages_EditMessage` with serialized rich page via `Iv::SerializeInputRichMessage(session, *page, Iv::SerializeInputRichMessageMode::FinalSubmit)`.
    - Handles automatic file reference renewal (`FILE_REFERENCE_*`) via `api->refreshFileReference` inside `EditRichMessage`.
    - Dispatches done/fail callbacks to `finishRequest(itemId, false)` and `finishRequest(itemId, true)`.
  - **Error Handling & State Rollback (lines 112–133)**:
    - On failure (`failed == true`):
      - Extracts `original` snapshot from `entry.original`.
      - Reverts optimistic local UI change via `item->applyLocalRichPage(original)`.
      - Erases entry from `_entries`.
    - On success:
      - If `!dirty`, removes entry from `_entries`.
      - If `dirty` (user toggled additional tasks while previous request was in-flight), marks `entry.scheduled = crl::now()` and triggers next `sendAccumulated()` batch.
  - **Identified Iterator Invalidation Bug in `send()` (lines 84–88)**:
    - In `RichTasks::send(FullMsgId itemId, Accumulated &entry)`:
      ```cpp
      const auto item = _session->data().message(itemId);
      if (!item) {
          _entries.remove(itemId);
          return;
      }
      ```
    - `send()` is invoked directly within a range-for loop in `sendAccumulated()`:
      `for (auto &[itemId, entry] : _entries) { ... send(itemId, entry); ... }`.
    - Calling `_entries.remove(itemId)` during range-for iteration invalidates the iterators of `base::flat_map`, causing potential undefined behavior / heap crash if a tracked message was deleted while pending debounce.

---

### 1.2 Comprehensive Style & Convention Audit Across All M2 Scope Files

| # | File Path | Observations & Detected Issues | Severity |
|---|-----------|--------------------------------|----------|
| 1 | `Telegram/SourceFiles/window/window_main_menu.cpp` | **1. Unsorted & Misplaced Includes**: Line 30 has `#include "settings/settings_common.h"` embedded inside `info/profile/...` headers. `info/profile/` and `info/stories/` appear after `info/info_memento.h` instead of folders-first.<br>**2. Calls Menu Action (Line 707)**: Still directly calls modal `::Calls::ShowCallsBox(controller);` instead of opening `Ui::PopupMenu` with `::Calls::ShowCallsMenu`.<br>**3. Wallet Entry (Line 673)**: `SetupMenuBots(_menu, controller);` correctly placed below "My Profile", renders green `NEW` badge via `Ui::NewBadge::AddToRight`. | Functional & Style |
| 2 | `Telegram/SourceFiles/calls/calls_box_controller.h` | **1. Unsorted Includes**: Line 11 `#include "ui/layers/generic_box.h"` is placed before line 12 `#include "mtproto/sender.h"` (`m` should come before `u`).<br>**2. Nested Namespace**: Lines 18–19 use old nested syntax `namespace Calls { namespace GroupCalls {` instead of C++17 `namespace Calls::GroupCalls {`.<br>**3. Single-line Comment**: Line 75 contains `int _loadRequestId = 0; // Not a real mtpRequestId.` (violates `REVIEW.md:5-10` comment ban). | Style |
| 3 | `Telegram/SourceFiles/calls/calls_box_controller.cpp` | **1. Unsorted Includes**: Lines 10–52 are completely unsorted across directories (`lang/`, `ui/`, `core/`, `calls/`, `history/`, `mainwidget.h`, `window/`, `main/`, `data/`, etc.). Style includes (`styles/style_*.h`) at lines 47–52 are also unsorted.<br>**2. Include Comments**: Lines 37, 48, 49 contain trailing comments (`// Data::ChannelHasActiveCall.`, `// infoTopBarMenu`, `// st::boxLabel.`).<br>**3. Function Parameter Indentation**: Lines 930–932 `ShowCallsMenu` uses 1 tab for parameter continuations instead of 2 tabs.<br>**4. Single-line Comments**: Lines 555–568 contain inline comments on TL arguments (`// q`, `// saved_peer_id`, etc.); lines 714–715 contain single-line comments. | Style |
| 4 | `Telegram/SourceFiles/core/core_settings.h` | Lines 784–795 declare `setGhostMode()`, `ghostMode()`, `ghostModeValue()`, `ghostModeChanges()`. Line 1153 initializes `rpl::variable<bool> _ghostMode = false;`. Class has empty line before closing brace. Conforms to conventions. | Clean |
| 5 | `Telegram/SourceFiles/core/core_settings.cpp` | Ghost Mode serialization properly added at line 295 (`computeSerializedLength`), line 464 (`serialize`), line 634 & 869–871 (`deserialize` with `!stream.atEnd()`), line 1246 (`_ghostMode = (ghostMode == 1);`). Single-line comment `+ sizeof(qint32) // _ghostMode` at line 295 matches the surrounding legacy serialization pattern. | Clean |
| 6 | `Telegram/SourceFiles/data/data_histories.cpp` | **Single-line Comment**: Line 716 contains `// Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers`. Violates `REVIEW.md` comment policy. Logic at lines 717–721 correctly zeroes `willReadTill`/`willReadWhen` and suppresses MTProto `readHistory` calls. | Style |
| 7 | `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp` | Lines 1091–1118: Ghost Mode subsection title, toggle button with `ghostModeValue()`, and explanatory text using `lng_settings_ghost_mode` and `lng_settings_ghost_mode_about`. Uses `u"..."_q` literals and correct reactive chaining. | Clean |
| 8 | `Telegram/SourceFiles/api/api_rich_tasks.h` | **Include Sort Order**: Line 10 `#include "base/timer.h"` is placed before line 11 `#include "base/flat_map.h"` (`f` should precede `t`). Class and struct formatting conforms to `REVIEW.md`. | Style |
| 9 | `Telegram/SourceFiles/api/api_rich_tasks.cpp` | **Iterator Invalidation**: Line 86 calls `_entries.remove(itemId);` within range-for loop in `sendAccumulated()`. Style formatting (leading operators, no comments, normal return types) conforms. | Bug / Safety |

---

## 2. Logic Chain

1. **Rich Tasks Debounce & State Consistency**:
   - The 1000ms debounce interval in `api_rich_tasks.cpp` coalesces high-frequency user checkbox toggles on rich markdown task lists into a single outgoing `MTPmessages_EditMessage` request.
   - Retaining `entry.original` guarantees optimistic UI updates are safe: if the server rejects the edit (e.g. edit window expired or peer permissions restricted), `finishRequest(itemId, true)` restores the exact pre-edit markdown structure via `item->applyLocalRichPage(original)`.
   - **Iterator Safety Fix**: Mutating `_entries` inside `send()` while `sendAccumulated()` is iterating `_entries` can be cleanly resolved by omitting `_entries.remove(itemId);` from `send()` (similar to `TodoLists::send` in `api_todo_lists.cpp:225–228`), allowing stale entries to simply skip sending and be cleaned up on demand or in `finishRequest()`.

2. **Main Menu Calls Integration (`window_main_menu.cpp`)**:
   - `window_main_menu.cpp:707` currently executes `::Calls::ShowCallsBox(controller);`.
   - To satisfy `PROJECT.md:84–85` and `docs/fork_features.md:61`, clicking the Calls button must create a `Ui::PopupMenu` with `st::popupMenuWithIcons`, populate it using `::Calls::ShowCallsMenu(_contextMenu.get(), controller);`, and show it at `QCursor::pos()`.

3. **Style & Convention Enforcement**:
   - `REVIEW.md` strictly mandates:
     - No single-line descriptive comments (remove line 716 in `data_histories.cpp`, line 75 in `calls_box_controller.h`).
     - Alphabetical `#include` sorting with nested directories first, followed by separate style headers at the bottom.
     - C++17 nested namespaces (`namespace Calls::GroupCalls {`).
     - Two-tab (`\t\t`) continuation indentation on function definitions.

---

## 3. Caveats & Risks

1. **Include Sorting in Large Legacy Files**:
   - In `calls_box_controller.cpp` and `window_main_menu.cpp`, dozens of legacy includes are unsorted. When reorganizing includes, ensure no forward declaration or implicit macro dependency is broken.
2. **Rich Tasks Concurrent Deletion**:
   - If a message containing rich tasks is deleted from the local database during the 1-second debounce delay, `_session->data().message(itemId)` safely returns `nullptr`. Omitting `_entries.remove(itemId)` in `send()` prevents iterator invalidation without leaking memory (entries are small and pruned on subsequent passes).
3. **Ghost Mode Local vs Upstream State**:
   - Ghost mode intentionally decouples local UI read state from upstream MTProto receipts. Blue checkmarks remain hidden from senders while the local user sees the conversation as read.

---

## 4. Conclusion & Recommendations for Worker

### Recommended Changes for Worker:

#### 1. Fix `Telegram/SourceFiles/window/window_main_menu.cpp`:
- **Lines 703–708**: Replace direct `ShowCallsBox` call with `Ui::PopupMenu` and `ShowCallsMenu`:
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
- **Lines 28–33**: Fix misplaced `#include "settings/settings_common.h"` and sort `info/` includes.

#### 2. Fix `Telegram/SourceFiles/api/api_rich_tasks.cpp` and `api_rich_tasks.h`:
- In `api_rich_tasks.h:10–11`: Swap include order to put `"base/flat_map.h"` before `"base/timer.h"`.
- In `api_rich_tasks.cpp:84–88`: Remove `_entries.remove(itemId);` from `RichTasks::send` to prevent iterator invalidation during range-for loop in `sendAccumulated()`.

#### 3. Fix `Telegram/SourceFiles/data/data_histories.cpp`:
- **Line 716**: Remove single-line comment `// Ghost Mode: If enabled, do not send read receipts upstream to Telegram servers`.

#### 4. Fix `Telegram/SourceFiles/calls/calls_box_controller.h`:
- **Lines 10–12**: Sort includes (`mtproto/sender.h` before `ui/layers/generic_box.h`).
- **Lines 18–19**: Convert `namespace Calls { namespace GroupCalls {` to `namespace Calls::GroupCalls {`.
- **Line 75**: Remove comment `// Not a real mtpRequestId.`.

#### 5. Fix `Telegram/SourceFiles/calls/calls_box_controller.cpp`:
- **Lines 930–932**: Format `ShowCallsMenu` parameter continuations with 2 tabs (`\t\t`).
- Remove trailing comments on include lines 37, 48, 49.

---

## 5. Verification Method

1. **Static Analysis & Inspection**:
   - Inspect all 9 files to confirm absence of single-line comments in new/modified blocks.
   - Verify `#include` alphabetical ordering and C++17 namespace syntax.
2. **Build Verification**:
   - Build the Telegram target:
     ```bash
     cmake --build out --config Debug --target Telegram
     ```
   - Ensure clean compilation with zero warnings or link errors.
3. **Behavioral Invalidation Checks**:
   - Clicking "Calls" in the main menu must display the popup menu listing active video chats, "Start New Call", and "Calls" history.
   - Enabling Ghost Mode in Privacy & Security settings must keep outgoing read receipts suppressed in `data_histories.cpp:717`.
   - Toggling markdown checklist items in Instant View / rich messages must debounce 1s and sync via `EditRichMessage`.
