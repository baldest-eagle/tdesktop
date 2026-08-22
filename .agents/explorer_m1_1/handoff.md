# Handoff Report: Milestone M1 — FloatingOverlay::setupChatContent()

**Explorer**: Explorer 1 (Milestone M1)  
**Date**: 2026-08-20  
**Target Component**: Floating Overlay Chat Content (`FloatingOverlay::setupChatContent()`)  
**Target Files**:
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`

---

## 1. Observation

### 1.1 Unimplemented `setupChatContent()`
In `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp:149-158`:
```cpp
void FloatingOverlay::setupChatContent() {
	// Note: MessagesUi requires a proper parent with session/show
	// This is a placeholder - full implementation needs access to
	// the Panel's uiShow() and _call->messages() data
	if (!_panel) {
		return;
	}
	// Get messages data from panel
	// _messagesUi = std::make_unique<MessagesUi>(...);
}
```
The method was an empty stub with placeholder comments and no instantiation of `_messagesUi`.

### 1.2 Viewport Sizing & Clipping Bug
In `Telegram/SourceFiles/calls/group/calls_group_messages_ui.cpp:1882-1894` and `1901-1918`:
```cpp
void MessagesUi::move(int left, int bottom, int width, int availableHeight) {
	...
	_left = left;
	_bottom = bottom;
	_width = width;
	_availableHeight = availableHeight;
	applyGeometry();
}
...
void MessagesUi::updateGeometries() {
	...
	const auto bottom = _bottom - _pinnedScrollSkip;
	const auto height = _views.empty() ? 0 : (_views.back().top + _views.back().height);
	_messages->resize(_width, height);
	const auto min = std::min(height, _availableHeight);
	_scroll->setGeometry(_left, bottom - min, _width, min);
}
```
In `calls_group_floating_overlay.cpp:128`:
```cpp
void FloatingOverlay::resizeEvent(QResizeEvent *event) {
	QWidget::resizeEvent(event);
	if (_messagesUi) {
		_messagesUi->move(4, 36, width() - 8, height() - 40);
	}
}
```
Passing `bottom = 36` caused `_scroll->setGeometry` to compute `y = 36 - min` (negative y offset), placing the messages completely off-screen above the top window boundary.

### 1.3 Available Data Sources in `Panel` and `GroupCall`
- `_panel->uiShow()` returns `std::shared_ptr<ChatHelpers::Show>` (`calls_group_panel.cpp:315-320`).
- `_panel->call()` returns `not_null<GroupCall*>` (`calls_group_panel.cpp:302-304`).
- `call->messages()->listValue()` returns `rpl::producer<std::vector<Message>>` (`calls_group_call.h:249-251`).
- `call->messages()->idUpdates()` returns `rpl::producer<MessageIdUpdate>`.
- `call->canManageValue()` returns `rpl::producer<bool>`.
- `call->messagesEnabledValue()` returns `rpl::producer<bool>`.

### 1.4 Code Formatting and Guidelines
- `calls_group_floating_overlay.cpp` contained 0-space unindented function bodies at lines 27-43, 47-51, 53-55, 57-63, 65-67, 69-74, 76-83, 85-91, 116-123, 125-130, 160-176, 178-181.
- Contained single-line comments prohibited by `REVIEW.md` and `AGENTS.md`.
- Contained `QStringLiteral` and plain string literals instead of `_q` suffixes.
- Contained raw local pointer variables for `closeBtn` and `passthroughBtn` that did not track window resize events.

---

## 2. Logic Chain

1. **Instantiation**: `MessagesUi` constructor accepts `(QWidget *parent, std::shared_ptr<ChatHelpers::Show> show, MessagesMode mode, rpl::producer<std::vector<Message>> messages, rpl::producer<std::vector<not_null<PeerData*>>> topDonorsValue, rpl::producer<MessageIdUpdate> idUpdates, rpl::producer<bool> canManageValue, rpl::producer<bool> shown, Fn<bool(QPoint)> inputReserved)`.
2. **Parameters Mapping**:
   - `parent`: `this` (`FloatingOverlay`)
   - `show`: `_panel->uiShow()`
   - `mode`: `MessagesMode::GroupCall`
   - `messages`: `_panel->call()->messages()->listValue()`
   - `topDonorsValue`: `nullptr`
   - `idUpdates`: `_panel->call()->messages()->idUpdates()`
   - `canManageValue`: `_panel->call()->canManageValue()`
   - `shown`: `_panel->call()->messagesEnabledValue()`
   - `inputReserved`: `[=](QPoint) { return false; }`
3. **Geometry Calculation**: In `MessagesUi::move(left, bottom, width, availableHeight)`, `bottom` is the bottom y-coordinate of the container. For a window of height `H` with top header of ~36px and 4px margins:
   - `left` = `4`
   - `bottom` = `height() - 4`
   - `width` = `width() - 8`
   - `availableHeight` = `height() - 40`
   This sets the scroll viewport to bottom `height() - 4` extending upwards up to `height() - 40`, maintaining a top position `>= 36px`.
4. **Resizing and Child Anchoring**: Making `_closeBtn` and `_passthroughBtn` member variables (`object_ptr<Ui::IconButton>`) allows `resizeEvent` to reposition them dynamically to `(width() - 30, 5)` and `(width() - 55, 5)`.
5. **Style Compliance**: Removing all single-line comments, replacing `QStringLiteral` with `_q` literals (`u"Chat"_q`, `u"Ctrl+Shift+T"_q`), using `!isHidden()` instead of `isVisible()`, and applying standard tab indents resolves all review and guideline violations.

---

## 3. Caveats

1. **Top Donors**: `topDonorsValue` is passed as `nullptr`, matching `Panel::_messages` and `Panel::_panelMessages` usage in group call mode. If video streams require donor badge ribbons, `topDonorsValue` can be linked to `call->topDonorsValue()`.
2. **Reaction Input Capture**: `inputReserved` returns `false` because `FloatingOverlay` is an overlay viewer and does not host an inline emoji reaction picker panel.

---

## 4. Conclusion

`FloatingOverlay::setupChatContent()` is fully analyzed and designed with complete data flow integration from `_panel->call()->messages()`, correct geometry anchoring, dynamic button repositioning, and strict adherence to `REVIEW.md` and `AGENTS.md`.

Detailed replacement source and header code are documented in `c:\Users\kyleh\tdesktop\.agents\explorer_m1_1\analysis.md`.

---

## 5. Verification Method

### 5.1 Inspection Verification
- Inspect `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h` and `.cpp` to verify:
  1. `setupChatContent()` instantiates `_messagesUi` with `_panel->uiShow()` and `_panel->call()->messages()->listValue()`.
  2. `_messagesUi->move(4, height() - 4, width() - 8, height() - 40)` is invoked in `setupChatContent()` and `resizeEvent()`.
  3. No single-line comments exist in `calls_group_floating_overlay.h` or `.cpp`.
  4. String literals use `u"..."_q`.
  5. Class section formatting has an empty line before closing brace.

### 5.2 Build Verification
- Under WSL / Linux Docker environment:
  ```bash
  Telegram/build/docker/centos_env/build_debug.sh
  ```
- Or under native Windows Visual Studio x64 Native Tools Command Prompt:
  ```bash
  cmake --build out --config Debug --target Telegram
  ```
