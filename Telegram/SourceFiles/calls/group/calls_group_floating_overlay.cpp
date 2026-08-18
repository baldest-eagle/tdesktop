/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_floating_overlay.h"

#include "calls/group/calls_group_panel.h"
#include "ui/widgets/labels.h"
#include "ui/widgets/buttons.h"
#include "styles/style_calls.h"

#include <QtGui/QKeyEvent>
#include <QtGui/QMouseEvent>
#include <QtGui/QPainter>
#include <QtWidgets/QApplication>
#include <QtWidgets/QMainWindow>

namespace Calls::Group {

FloatingOverlay::FloatingOverlay(not_null<Panel*> panel)
: QWidget(nullptr, Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint)
, _panel(panel) {
setAttribute(Qt::WA_TranslucentBackground);
setAttribute(Qt::WA_ShowWithoutActivating);
setAttribute(Qt::WA_TransparentForMouseEvents, _passthrough);

// Set initial geometry
const auto screen = QApplication::primaryScreen()->availableGeometry();
setGeometry(screen.width() - 320, 100, 300, 400);

// Set up UI
setupUI();

// Set up shortcut
_toggleShortcut = new QShortcut(QKeySequence("Ctrl+Shift+T"), this);
connect(_toggleShortcut, &QShortcut::activated, this, [this] { toggle(); });

// Make semi-transparent
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
if (isVisible()) {
hide();
} else {
show();
}
}

bool FloatingOverlay::isVisible() const {
return QWidget::isVisible();
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
_dragStart = event->globalPos();
_startGeometry = geometry();
}
QWidget::mousePressEvent(event);
}

void FloatingOverlay::mouseMoveEvent(QMouseEvent *event) {
if (_dragging) {
const auto delta = event->globalPos() - _dragStart;
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

void FloatingOverlay::paintEvent(QPaintEvent *event) {
QPainter p(this);
p.setOpacity(_opacity);
p.fillRect(rect(), QColor(30, 30, 30, 200));
p.setPen(QColor(255, 255, 255, 100));
p.drawRect(rect().adjusted(0, 0, -1, -1));
QWidget::paintEvent(event);
}

void FloatingOverlay::setupUI() {
// Title bar
auto *title = new Ui::FlatLabel(this, st::groupCallBox);
title->setText("Chat");
title->move(10, 10);

// Close button
auto *closeBtn = new Ui::IconButton(this, st::groupCallMenuToggleSmall);
closeBtn->move(width() - 30, 5);
connect(closeBtn, &Ui::IconButton::clicked, this, [this] { hide(); });

// Passthrough toggle
auto *passthroughBtn = new Ui::IconButton(this, st::groupCallMenuToggleSmall);
passthroughBtn->move(width() - 55, 5);
connect(passthroughBtn, &Ui::IconButton::clicked, this, [this] { togglePassthrough(); });
}

void FloatingOverlay::updateGeometry() {
// Keep within screen bounds
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
