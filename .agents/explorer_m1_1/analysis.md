# Technical Analysis Report: FloatingOverlay::setupChatContent() and Floating Overlay Architecture

**Explorer**: Explorer 1 (Milestone M1)  
**Date**: 2026-08-20  
**Target Files**:
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_panel.h`
- `Telegram/SourceFiles/calls/group/calls_group_panel.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_messages_ui.h`
- `Telegram/SourceFiles/calls/group/calls_group_messages_ui.cpp`

---

## 1. Executive Summary

`Calls::Group::FloatingOverlay` provides a lightweight, translucent, always-on-top floating window that allows participants in a Telegram group call / video stream to view active chat messages and donor badges in real time.

Prior to this investigation, `FloatingOverlay::setupChatContent()` was an empty placeholder method containing only comment stubs, preventing chat content from being instantiated or rendered in the overlay. Furthermore, the overlay implementation suffered from:
1. **Geometry calculation bug in `_messagesUi->move()`**: The previous code passed `36` as the `bottom` argument instead of calculating the parent widget bottom (`height() - 4`), which caused `MessagesUi` to position its `Ui::ElasticScroll` viewport completely off-screen at negative y coordinates (`36 - minHeight`).
2. **Missing UI element anchoring on resize**: `_closeBtn` and `_passthroughBtn` were instantiated as untracked raw pointers at fixed coordinates without repositioning in `resizeEvent()`.
3. **Coding convention violations (`REVIEW.md` & `AGENTS.md`)**: Missing tab indentations across multiple method bodies, extensive single-line comment bloat, raw `QStringLiteral` / string literals instead of `_q` suffixes, and use of `isVisible()` instead of `!isHidden()`.

This report provides the full architectural breakdown, data flow, lifetime analysis, and the concrete implementation blueprint for `FloatingOverlay::setupChatContent()` and its supporting methods.

---

## 2. Architecture and Data Flow

### 2.1 Component Relationships

```
+-------------------------------------------------------------+
|                      Calls::Group::Panel                    |
|  - owns _call (not_null<GroupCall*>)                        |
|  - owns _floatingOverlay (std::unique_ptr<FloatingOverlay>) |
|  - provides uiShow() (std::shared_ptr<ChatHelpers::Show>)   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                Calls::Group::FloatingOverlay                |
|  - parent: QWidget (Qt::Window | Frameless | StaysOnTop)    |
|  - reference: const not_null<Panel*> _panel                 |
|  - owns: std::unique_ptr<MessagesUi> _messagesUi            |
|  - owns: object_ptr<Ui::FlatLabel> _title                   |
|  - owns: object_ptr<Ui::IconButton> _closeBtn               |
|  - owns: object_ptr<Ui::IconButton> _passthroughBtn         |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                  Calls::Group::MessagesUi                   |
|  - parent: FloatingOverlay (this)                           |
|  - show: _panel->uiShow()                                   |
|  - mode: MessagesMode::GroupCall                            |
|  - messages: _panel->call()->messages()->listValue()        |
|  - topDonors: nullptr                                       |
|  - idUpdates: _panel->call()->messages()->idUpdates()       |
|  - canManage: _panel->call()->canManageValue()              |
|  - shown: _panel->call()->messagesEnabledValue()            |
|  - inputReserved: [=](QPoint) { return false; }             |
+-------------------------------------------------------------+
```

### 2.2 Data Feeds Sourced from `Panel` and `GroupCall`

1. **`ChatHelpers::Show` (`uiShow()`)**:
   - Signature: `std::shared_ptr<ChatHelpers::Show> Panel::uiShow()`
   - Source: `Panel::_cachedShow` wrapping `_window->uiShow()`
   - Role: Provides modal dialog, tooltip, and toast presentation capabilities to `MessagesUi`.
2. **Messages Stream (`listValue()`)**:
   - Signature: `rpl::producer<std::vector<Message>> Group::Messages::listValue() const`
   - Source: `_panel->call()->messages()->listValue()`
   - Role: Streams the chronological message list, updated as messages are added, edited, or purged.
3. **ID Updates Stream (`idUpdates()`)**:
   - Signature: `rpl::producer<MessageIdUpdate> Group::Messages::idUpdates() const`
   - Source: `_panel->call()->messages()->idUpdates()`
   - Role: Tracks client-to-server ID mapping after outgoing message dispatch.
4. **Administrative Rights (`canManageValue()`)**:
   - Signature: `rpl::producer<bool> GroupCall::canManageValue() const`
   - Source: `_panel->call()->canManageValue()`
   - Role: Dictates whether contextual deletion and moderation menus are active.
5. **Visibility Stream (`messagesEnabledValue()`)**:
   - Signature: `rpl::producer<bool> GroupCall::messagesEnabledValue() const`
   - Source: `_panel->call()->messagesEnabledValue()`
   - Role: Controls whether chat message rendering is enabled in the active call.

---

## 3. Deep Dive into Issues & Critical Fixes

### 3.1 Geometry Calculation & Sizing in `MessagesUi::move()`

`MessagesUi::move()` has the following signature and implementation in `calls_group_messages_ui.cpp:1901`:
```cpp
void MessagesUi::move(int left, int bottom, int width, int availableHeight);
```
In `MessagesUi::updateGeometries()` (`calls_group_messages_ui.cpp:1867-1894`):
```cpp
const auto bottom = _bottom - _pinnedScrollSkip;
const auto height = _views.empty() ? 0 : (_views.back().top + _views.back().height);
_messages->resize(_width, height);
const auto min = std::min(height, _availableHeight);
_scroll->setGeometry(_left, bottom - min, _width, min);
```
**The Bug**:
- In `calls_group_floating_overlay.cpp:128`, the placeholder called:
  `_messagesUi->move(4, 36, width() - 8, height() - 40);`
- Passing `bottom = 36` meant that for any non-zero content height `min`, `_scroll->setGeometry` computed:
  `y = 36 - min`
  For example, with `min = 300px`, `y = 36 - 300 = -264px`. The entire message container was clipped above the top edge of the window!
- **Fix**:
  `_messagesUi->move(4, height() - 4, width() - 8, height() - 40);`
  - `left` = `4`
  - `bottom` = `height() - 4`
  - `width` = `width() - 8`
  - `availableHeight` = `height() - 40` (reserving 36px header + 4px bottom padding)
  This correctly anchors the message scroll area from `y = 36` down to `y = height() - 4`.

### 3.2 Dynamic Header Button Layout

In `FloatingOverlay::setupUI()`:
- `_closeBtn` was placed at `(width() - 30, 5)`.
- `_passthroughBtn` was placed at `(width() - 55, 5)`.
Because they were stored only as local pointers in `setupUI()`, user-driven window resizing left the buttons orphaned at their initial static positions.
- **Fix**:
  Store `_closeBtn` and `_passthroughBtn` as `object_ptr<Ui::IconButton>` members and reposition them in `FloatingOverlay::resizeEvent()`:
  ```cpp
  if (_closeBtn) {
      _closeBtn->move(width() - 30, 5);
  }
  if (_passthroughBtn) {
      _passthroughBtn->move(width() - 55, 5);
  }
  ```

### 3.3 Lifetime and Ownership

- `FloatingOverlay` is owned by `Calls::Group::Panel` via `std::unique_ptr<FloatingOverlay> _floatingOverlay`.
- `Panel` outlives `FloatingOverlay`, and `FloatingOverlay` is destructed prior to `Panel` teardown.
- `MessagesUi` is owned by `FloatingOverlay` via `std::unique_ptr<MessagesUi> _messagesUi`.
- Child widgets (`Ui::FlatLabel`, `Ui::IconButton`) use `object_ptr` and are parented to `this` (`FloatingOverlay`), ensuring clean destruction upon window close.
- Qt shortcuts use `this` as parent (`new QShortcut(QKeySequence(u"Ctrl+Shift+T"_q), this)`), with lambda connections capturing `[=]`.

### 3.4 Review Guidelines Compliance (`REVIEW.md`)

| Rule | Violation in Original | Corrected Pattern |
|---|---|---|
| No single-line comments | 10+ single-line comment stubs | Removed all single-line comments |
| String literals | `QStringLiteral("Chat")`, `"Ctrl+Shift+T"` | `u"Chat"_q`, `u"Ctrl+Shift+T"_q` |
| Variable initialization | `_toggleShortcut` raw pointer | `_toggleShortcut = nullptr`, `object_ptr` for UI buttons |
| Visibility check | `isVisible()` | `!isHidden()` for logic branching |
| Type deduction | `QPainter p(this)` | `auto p = QPainter(this)` |
| Indentation | Zero-indentation on method bodies | Proper tab indentation throughout |
| Includes sorting | Arbitrary order | Folders first, alphabetical, styles last, Qt headers last |

---

## 4. Exact Proposed Implementation

### 4.1 Header: `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`

```cpp
/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#pragma once

#include "base/object_ptr.h"

#include <QtWidgets/QWidget>
#include <QtWidgets/QShortcut>

namespace Ui {
class RpWidget;
class FlatLabel;
class IconButton;
} // namespace Ui

namespace Calls::Group {

class Panel;
class MessagesUi;

class FloatingOverlay final : public QWidget {
public:
	FloatingOverlay(not_null<Panel*> panel);
	~FloatingOverlay();

	void show();
	void hide();
	void toggle();

	[[nodiscard]] bool isVisible() const;

protected:
	void keyPressEvent(QKeyEvent *event) override;
	void mousePressEvent(QMouseEvent *event) override;
	void mouseMoveEvent(QMouseEvent *event) override;
	void mouseReleaseEvent(QMouseEvent *event) override;
	void wheelEvent(QWheelEvent *event) override;
	void paintEvent(QPaintEvent *event) override;
	void resizeEvent(QResizeEvent *event) override;

private:
	void setupUI();
	void updateGeometry();
	void togglePassthrough();
	void setupChatContent();

	const not_null<Panel*> _panel;
	bool _dragging = false;
	QPoint _dragStart;
	QRect _startGeometry;
	bool _passthrough = false;

	float _opacity = 0.7f;

	QShortcut *_toggleShortcut = nullptr;

	object_ptr<Ui::FlatLabel> _title = { nullptr };
	object_ptr<Ui::IconButton> _closeBtn = { nullptr };
	object_ptr<Ui::IconButton> _passthroughBtn = { nullptr };

	std::unique_ptr<MessagesUi> _messagesUi;

};

} // namespace Calls::Group
```

### 4.2 Source: `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`

```cpp
/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_floating_overlay.h"

#include "calls/group/calls_group_call.h"
#include "calls/group/calls_group_messages.h"
#include "calls/group/calls_group_messages_ui.h"
#include "calls/group/calls_group_panel.h"
#include "ui/widgets/buttons.h"
#include "ui/widgets/labels.h"

#include "styles/style_calls.h"

#include <QtGui/QGuiApplication>
#include <QtGui/QKeyEvent>
#include <QtGui/QMouseEvent>
#include <QtGui/QPainter>
#include <QtGui/QScreen>
#include <QtWidgets/QApplication>

namespace Calls::Group {

FloatingOverlay::FloatingOverlay(not_null<Panel*> panel)
: QWidget(nullptr, Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint)
, _panel(panel) {
	setAttribute(Qt::WA_TranslucentBackground);
	setAttribute(Qt::WA_ShowWithoutActivating);

	const auto screen = QApplication::primaryScreen()->availableGeometry();
	setGeometry(screen.width() - 320, 100, 300, 400);

	setupUI();

	_toggleShortcut = new QShortcut(QKeySequence(u"Ctrl+Shift+T"_q), this);
	connect(_toggleShortcut, &QShortcut::activated, this, [=] { toggle(); });

	setWindowOpacity(_opacity);
}

FloatingOverlay::~FloatingOverlay() = default;

void FloatingOverlay::show() {
	QWidget::show();
	raise();
	activateWindow();
}

void FloatingOverlay::hide() {
	QWidget::hide();
}

void FloatingOverlay::toggle() {
	if (!isHidden()) {
		hide();
	} else {
		show();
	}
}

bool FloatingOverlay::isVisible() const {
	return !isHidden();
}

void FloatingOverlay::keyPressEvent(QKeyEvent *event) {
	if (event->key() == Qt::Key_Escape) {
		hide();
	}
	QWidget::keyPressEvent(event);
}

void FloatingOverlay::mousePressEvent(QMouseEvent *event) {
	if (event->button() == Qt::LeftButton && !_passthrough) {
		_dragging = true;
		_dragStart = event->globalPosition().toPoint();
		_startGeometry = geometry();
	}
	QWidget::mousePressEvent(event);
}

void FloatingOverlay::mouseMoveEvent(QMouseEvent *event) {
	if (_dragging) {
		const auto delta = event->globalPosition().toPoint() - _dragStart;
		setGeometry(_startGeometry.translated(delta));
	}
	QWidget::mouseMoveEvent(event);
}

void FloatingOverlay::mouseReleaseEvent(QMouseEvent *event) {
	if (event->button() == Qt::LeftButton) {
		_dragging = false;
	}
	QWidget::mouseReleaseEvent(event);
}

void FloatingOverlay::wheelEvent(QWheelEvent *event) {
	if (event->modifiers() & Qt::ControlModifier) {
		const auto delta = event->angleDelta().y();
		if (delta > 0) {
			_opacity = std::min(1.0f, _opacity + 0.05f);
		} else if (delta < 0) {
			_opacity = std::max(0.2f, _opacity - 0.05f);
		}
		setWindowOpacity(_opacity);
		update();
		event->accept();
		return;
	}
	QWidget::wheelEvent(event);
}

void FloatingOverlay::paintEvent(QPaintEvent *event) {
	auto p = QPainter(this);
	p.setOpacity(_opacity);
	p.fillRect(rect(), QColor(30, 30, 30, 200));
	p.setPen(QColor(255, 255, 255, 100));
	p.drawRect(rect().adjusted(0, 0, -1, -1));
	QWidget::paintEvent(event);
}

void FloatingOverlay::resizeEvent(QResizeEvent *event) {
	QWidget::resizeEvent(event);
	if (_messagesUi) {
		_messagesUi->move(4, height() - 4, width() - 8, height() - 40);
	}
	if (_closeBtn) {
		_closeBtn->move(width() - 30, 5);
	}
	if (_passthroughBtn) {
		_passthroughBtn->move(width() - 55, 5);
	}
}

void FloatingOverlay::setupUI() {
	_title.create(this, st::callButtonLabel);
	_title->setText(u"Chat"_q);
	_title->move(10, 10);

	_closeBtn.create(this, st::callAnswer.button);
	_closeBtn->move(width() - 30, 5);
	_closeBtn->setClickedCallback([=] { hide(); });

	_passthroughBtn.create(this, st::callAnswer.button);
	_passthroughBtn->move(width() - 55, 5);
	_passthroughBtn->setClickedCallback([=] { togglePassthrough(); });

	setupChatContent();
}

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

void FloatingOverlay::updateGeometry() {
	const auto screen = QApplication::primaryScreen()->availableGeometry();
	auto geo = geometry();
	if (geo.right() > screen.right()) {
		geo.moveRight(screen.right());
	}
	if (geo.bottom() > screen.bottom()) {
		geo.moveBottom(screen.bottom());
	}
	if (geo.left() < screen.left()) {
		geo.moveLeft(screen.left());
	}
	if (geo.top() < screen.top()) {
		geo.moveTop(screen.top());
	}
	setGeometry(geo);
}

void FloatingOverlay::togglePassthrough() {
	_passthrough = !_passthrough;
	setAttribute(Qt::WA_TransparentForMouseEvents, _passthrough);
}

} // namespace Calls::Group
```
