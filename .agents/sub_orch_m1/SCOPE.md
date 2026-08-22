# Scope: Milestone M1 (Calls UI, Floating Overlay & Viewport Grid)

## Architecture & Target Files
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp` (and `.h` if needed)
- `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp` (and `.h` if needed)
- `Telegram/SourceFiles/calls/group/calls_group_members.cpp` (and related menu/context files if needed)

## Tasks & Requirements
1. **FloatingOverlay::setupChatContent()**:
   - Complete implementation in `calls_group_floating_overlay.cpp`.
   - Properly create and parent `MessagesUi` / chat content using `_panel` and window controllers.
   - Clean up formatting and style per `REVIEW.md` (no single line comments, `_q` literals, proper return types, auto usage).
2. **50/50 Viewport Grid Split Condition**:
   - In `calls_group_viewport.cpp:577` (and dynamic grid layout solver), fix the 50/50 split condition so 2 active feeds correctly split half-width on screen when `slotConstraint == 0` (or dynamic mode) instead of hitting dead code in `if (fixedGridDim > 0)`.
3. **Group Call Context Actions (Pin to Grid & Open Chat)**:
   - In `calls_group_members.cpp` / group calls menus, wire `lng_group_call_context_pin_to_grid` and `lng_group_call_open_chat` so participants have direct "Pin to Grid" and "Open Chat" actions in context menus.
4. **Code Conventions & Quality**:
   - Adhere strictly to project conventions in `REVIEW.md` and `AGENTS.md`.

## Milestone Execution Status
| # | Task | Target Files | Status |
|---|------|--------------|--------|
| 1 | Setup Chat Content in Floating Overlay | calls_group_floating_overlay.cpp | DONE |
| 2 | Fix 50/50 Grid Viewport Split Condition | calls_group_viewport.cpp | DONE |
| 3 | Wire Pin to Grid and Open Chat Context Actions | calls_group_members.cpp | DONE |
| 4 | Verification & Audit | All affected files | DONE |
