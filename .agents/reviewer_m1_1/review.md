# Quality & Adversarial Review Report: Milestone M1 (Worker 1)

**Reviewer**: Reviewer 1 (Milestone M1)  
**Roles**: Reviewer & Critic  
**Working Directory**: `c:\Users\kyleh\tdesktop\.agents\reviewer_m1_1\`  
**Target Files**:
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_members.cpp`

---

## 1. Executive Summary & Verdict

**Verdict**: **APPROVE**  
**Integrity Assessment**: **CLEAN (No Integrity Violations)**  
**Overall Risk Assessment**: **LOW**

All three assigned tasks for Milestone M1 have been correctly, genuinely, and robustly implemented by Worker 1:
1. `FloatingOverlay::setupChatContent()` is fully instantiated with live `MessagesUi`, accurate bottom-anchored geometry calculations, dynamic resize handling, and strict adherence to `REVIEW.md`.
2. The dynamic 50/50 viewport grid layout branch (`calls_group_viewport.cpp:561-572`) is cleanly extracted before `if (fixedGridDim > 0)`, resolving the dead code bug and preventing odd-width pixel gaps.
3. `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` are accurately wired in `calls_group_members.cpp:1452, 1536` for video pinning and channel/group chat navigation.

---

## 2. Quality Review & Verification Findings

### Dimension 1: Correctness & Functional Verification

- **`FloatingOverlay::setupChatContent()` (`calls_group_floating_overlay.cpp:154-167`)**:
  - `MessagesUi` constructor is invoked with parent `this`, show helper `_panel->uiShow()`, `MessagesMode::GroupCall`, live message feed `call->messages()->listValue()`, `nullptr` for topDonors, `idUpdates()`, `canManageValue()`, `messagesEnabledValue()`, and input filter `[=](QPoint) { return false; }`.
  - Coordinates `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` correctly supply `bottom = height() - 4` and `availableHeight = height() - 40`. Because `MessagesUi::updateGeometries()` positions its internal `_scroll` at `bottom - minHeight`, this reserves the top header region `[0, 36]` for `_title`, `_closeBtn`, and `_passthroughBtn`, and places the bottom at `height() - 4`.
  - Dynamic resizing in `resizeEvent()` updates `_messagesUi->move()`, `_closeBtn->move(width() - 30, 5)`, and `_passthroughBtn->move(width() - 55, 5)` whenever the overlay widget is resized.

- **50/50 Viewport Grid Split (`calls_group_viewport.cpp:560-572`)**:
  - In dynamic mode (`slotConstraint == 0`) with 2 active feeds (`count == 2`), the split branch executes immediately before `fixedGridDim > 0` calculation.
  - Geometry for tile 0: `{ 0, 0, halfW, outerHeight }`.
  - Geometry for tile 1: `{ halfW + skip, 0, outerWidth - halfW - skip, outerHeight }`.
  - Assigning `outerWidth - halfW - skip` to tile 1 guarantees that odd pixel dimensions (e.g. `outerWidth = 1001`) span the exact container width without subpixel gaps or clipping.
  - Setting `result.useColumns = true; return result;` cleanly completes the layout calculation.

- **Participant Context Actions (`calls_group_members.cpp:1445-1466, 1530-1538`)**:
  - `lng_group_call_context_pin_to_grid` ("Pin to grid") is wired when a video camera feed is not currently pinned, routing to `_call->pinVideoEndpoint(camera)`.
  - `lng_group_call_open_chat` ("Open Chat") is wired in the `else` branch of `if (participantPeer->isUser())`, allowing channel and group participants in the voice chat to open their chat history via `showHistory`.

### Dimension 2: Integrity Audit

- **Hardcoded test hacks**: None. All geometry math, data subscriptions, and action triggers are generic and dynamic.
- **Facade / Dummy implementations**: None. Real `MessagesUi` instance with real reactive streams, real layout solver, and real context menu actions.
- **Shortcuts / Task bypasses**: None.
- **Fabricated verification artifacts**: None.

### Dimension 3: Style & Project Guideline Conformance (`REVIEW.md` / `AGENTS.md`)

| Rule | Requirement | Result |
|---|---|---|
| **Empty line before class closing brace** | Required for classes with sections | `calls_group_floating_overlay.h:68` PASS |
| **No consecutive empty lines** | Max 1 empty line | PASS across all modified files |
| **Multi-line operators** | Leading operators on continuation lines | `calls_group_viewport.cpp:575-580` PASS |
| **No single-line comments** | Omit bloat comments | PASS across all modified files |
| **Variable initialization** | Initialize basic types | `_dragging = false`, `_opacity = 0.7f`, etc. PASS |
| **Include sorting** | Nested folders first, styles separated last | `calls_group_floating_overlay.cpp:8-25` PASS |
| **QString literals** | Use `u"..."_q` literals | `u"Ctrl+Shift+T"_q`, `u"Chat"_q` PASS |
| **Visibility checks** | Use `!isHidden()` instead of `isVisible()` | `calls_group_floating_overlay.cpp:58, 66` PASS |
| **Method attributes** | `[[nodiscard]]` on header decl only | `isVisible()` decl has `[[nodiscard]]`, def does not PASS |
| **Nested namespaces** | C++17 `namespace Calls::Group {` | PASS |

---

## 3. Adversarial Stress-Testing & Critical Challenges

### Challenge 1: `MessagesUi` Anchor Space & Header Clipping Under Resize
- **Stress Scenario**: Floating overlay resized to minimum possible dimensions or odd screen resolutions.
- **Analysis**:
  - `MessagesUi::move(int left, int bottom, int width, int availableHeight)` defines `_bottom = height() - 4` and `_availableHeight = height() - 40`.
  - In `MessagesUi::updateGeometries()`, `_scroll` geometry is set to `setGeometry(_left, bottom - min, _width, min)` where `min = std::min(height, _availableHeight) <= height() - 40`.
  - Therefore, `bottom - min = (height() - 4) - min >= (height() - 4) - (height() - 40) = 36`.
  - The scroll container never ascends into the header region `[0, 36]`, completely protecting `_title` (top: 10), `_closeBtn` (top: 5), and `_passthroughBtn` (top: 5) from message occlusion.
- **Outcome**: **PASS (Robust)**

### Challenge 2: Odd Outer Width Grid Geometry Rounding
- **Stress Scenario**: 2 feeds on odd-width monitor / viewport (e.g. `outerWidth = 1279px`, `skip = 4px`).
- **Analysis**:
  - `halfW = (1279 - 4) / 2 = 1275 / 2 = 637px`.
  - Feed 0 width: `637px` (span `[0, 637)`).
  - Gap: `4px` (span `[637, 641)`).
  - Feed 1 left: `637 + 4 = 641px`.
  - Feed 1 width: `1279 - 637 - 4 = 638px` (span `[641, 1279)`).
  - Total span = `0 + 637 + 4 + 638 = 1279px`.
  - No 1px black seam on the right border.
- **Outcome**: **PASS (Robust)**

### Challenge 3: Context Menu Peer Type Handling (Channel, Group, User)
- **Stress Scenario**: A broadcast channel or megagroup joins the call as a speaking participant; user opens context menu.
- **Analysis**:
  - If `participantPeer->isUser()` is false (Channel/Chat):
    - Profile item shows `lng_context_view_channel` or `lng_context_view_group`.
    - Message item shows `lng_group_call_open_chat` ("Open Chat") which triggers `showHistory`.
    - `showHistory` invokes `window->showPeerHistory(participantPeer, ::Window::SectionShow::Way::Forward)`.
    - Session window correctly navigates to the channel/group message feed.
  - If `participantPeer->isUser()` is true:
    - Shows `lng_context_send_message` ("Send Message") invoking `showHistory`.
- **Outcome**: **PASS (Robust)**

---

## 4. Summary of Verified Claims

- `FloatingOverlay::setupChatContent()` connects live `MessagesUi` $\rightarrow$ **VERIFIED PASS**
- Floating overlay header buttons dynamically reposition on resize $\rightarrow$ **VERIFIED PASS**
- 50/50 Viewport Grid layout condition is reached and avoids odd-dimension pixel gaps $\rightarrow$ **VERIFIED PASS**
- `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` wired and present in `lang.strings` $\rightarrow$ **VERIFIED PASS**
- `REVIEW.md` and `AGENTS.md` rules strictly observed $\rightarrow$ **VERIFIED PASS**
