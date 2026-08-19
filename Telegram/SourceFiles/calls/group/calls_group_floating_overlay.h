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
	void paintEvent(QPaintEvent *event) override;
	void resizeEvent(QResizeEvent *event) override;

private:
	void setupUI();
	void updateGeometry();
	void togglePassthrough();
	void setupChatContent();

	not_null<Panel*> _panel;
	bool _dragging = false;
	QPoint _dragStart;
	QRect _startGeometry;
	bool _passthrough = false;

	// Opacity control
	float _opacity = 0.7f;

	// Shortcut
	QShortcut *_toggleShortcut = nullptr;

	// Chat content
	std::unique_ptr<MessagesUi> _messagesUi;

};

} // namespace Calls::Group
