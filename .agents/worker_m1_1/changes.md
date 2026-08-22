# Changes Summary — Milestone M1 (Worker 1)

## Target Files Modified

### 1. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
- Added member pointers `object_ptr<Ui::FlatLabel> _title`, `object_ptr<Ui::IconButton> _closeBtn`, and `object_ptr<Ui::IconButton> _passthroughBtn` to retain references for dynamic resizing.
- Added `const` qualifier to `_panel` (`const not_null<Panel*> _panel;`).
- Cleaned up comments and maintained strict formatting per `REVIEW.md` (empty line before closing class brace).

### 2. `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
- **Implemented `setupChatContent()`**:
  - Instantiates `MessagesUi` parented to `this` (the overlay widget).
  - Supplies data streams from `_panel->call()`: `uiShow()`, `MessagesMode::GroupCall`, `listValue()`, `nullptr` for topDonors, `idUpdates()`, `canManageValue()`, `messagesEnabledValue()`, and input reservation predicate `[=](QPoint) { return false; }`.
  - Positions `_messagesUi` using bottom-anchored coordinates: `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)`.
- **Dynamic Resize Anchoring**:
  - In `resizeEvent()`, updates geometries for `_messagesUi`, `_closeBtn` (`width() - 30, 5`), and `_passthroughBtn` (`width() - 55, 5`).
- **Style Cleanups**:
  - Replaced string literals with `_q` literals (`u"Ctrl+Shift+T"_q`, `u"Chat"_q`).
  - Switched `isVisible()` check to `!isHidden()`.
  - Replaced raw `QPainter p(this)` with `auto p = QPainter(this)`.
  - Ensured includes are alphabetically ordered with nested folders first and style headers separated.
  - Eliminated all single-line comments.

### 3. `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp`
- **Fixed 50/50 Viewport Grid Split**:
  - Relocated the `count == 2 && slotConstraint == 0` split branch from inside `if (fixedGridDim > 0)` (where it was unreachable dead code) to before the `fixedGridDim` check.
  - Calculated the right tile width as `outerWidth - halfW - skip` to eliminate 1px rounding gaps on odd window dimensions.
  - Set `sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight }` and `sizes[1].columns = sizes[1].rows = { halfW + skip, 0, outerWidth - halfW - skip, outerHeight }`.
  - Set `result.useColumns = true; return result;`.
  - Removed single-line comments.

### 4. `Telegram/SourceFiles/calls/group/calls_group_members.cpp`
- **Wired Context Menu Actions**:
  - Wired `tr::lng_group_call_context_pin_to_grid(tr::now)` for camera pinning action in participant context menu.
  - Added `tr::lng_group_call_open_chat(tr::now)` in `else` branch of `if (participantPeer->isUser())` so non-user participants (channels and groups) have an "Open Chat" action invoking `showHistory`.
  - Cleaned up inline comments.
