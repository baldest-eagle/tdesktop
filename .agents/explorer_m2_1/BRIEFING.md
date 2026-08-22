# BRIEFING — 2026-08-20T19:19:45Z

## Mission
Investigate and report on Milestone M2 Task 1: Navigation & Calls Menu Integration (Calls popup menu integration in `window_main_menu.cpp` and Wallet menu item verification).

## 🔒 My Identity
- Archetype: explorer
- Roles: Teamwork explorer (read-only investigation, evidence chain, synthesis, handoff)
- Working directory: c:\Users\kyleh\tdesktop\.agents\explorer_m2_1\
- Original parent: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Milestone: M2 (Navigation & Calls Menu Integration)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Produce handoff.md following 5-component handoff report structure
- All observations must include exact file paths and line numbers

## Current Parent
- Conversation ID: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Updated: 2026-08-20T19:19:45Z

## Investigation State
- **Explored paths**:
  - `Telegram/SourceFiles/window/window_main_menu.cpp:662-715`
  - `Telegram/SourceFiles/window/window_main_menu_helpers.cpp:278-361`
  - `Telegram/SourceFiles/calls/calls_box_controller.h:88-90`
  - `Telegram/SourceFiles/calls/calls_box_controller.cpp:930-994`
  - `Telegram/SourceFiles/inline_bots/bot_attach_web_view.cpp:2635-2640`
  - `Telegram/SourceFiles/ui/new_badges.cpp:18-51`
- **Key findings**:
  - `window_main_menu.cpp:707` currently calls `::Calls::ShowCallsBox(controller)`.
  - `Calls::ShowCallsMenu` is fully declared and implemented in `calls_box_controller.h/.cpp` accepting `(not_null<Ui::PopupMenu*> menu, not_null<::Window::SessionController*> window)`.
  - Replacing `ShowCallsBox` with `_contextMenu = base::make_unique_q<Ui::PopupMenu>(calls, st::popupMenuWithIcons); ::Calls::ShowCallsMenu(_contextMenu.get(), controller); _contextMenu->popup(QCursor::pos());` wires the popup menu correctly.
  - Wallet entry is already placed directly below "My Profile" in `window_main_menu.cpp:673` via `SetupMenuBots(_menu, controller)` and displays the green `NEW` badge (`Ui::NewBadge::AddToRight(button)` with `st::windowBgActive`) matching `docs/fork_features.md:62`.
- **Unexplored areas**: None for this task.

## Key Decisions Made
- Fully formulated exact before/after code snippets for Worker.
- Documented findings in `handoff.md`.

## Artifact Index
- `.agents/explorer_m2_1/DISPATCH.md` — Inbound instructions
- `.agents/explorer_m2_1/BRIEFING.md` — Persistent state
- `.agents/explorer_m2_1/progress.md` — Heartbeat and task progress
- `.agents/explorer_m2_1/handoff.md` — Final handoff report
