/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#pragma once

#include "base/object_ptr.h"
#include "ui/gl/gl_backend.h"

#include <QtGui/QScreen>

#include <map>
#include <set>

class QWidget;

namespace Ui {
class RpWidget;
class FlatLabel;
} // namespace Ui

namespace Calls::Group {

class Viewport;

enum class DisplayRole {
	ActiveSpeaker,
	GridViewport,
	ChatStation,
	None,
};

struct DisplayWindow {
	std::unique_ptr<QWidget> widget;
	DisplayRole role = DisplayRole::None;
	QScreen *screen = nullptr;
};

class DisplayCoordinator final {
public:
	DisplayCoordinator(
		not_null<QWidget*> parent,
		Ui::GL::Backend backend,
		rpl::producer<bool> gridMode,
		rpl::variable<bool> &chatPanelShown);
	~DisplayCoordinator();

	void updateScreens();
	void setRole(int displayIndex, DisplayRole role);
	DisplayRole role(int displayIndex) const;

	void showDisplay(int displayIndex);
	void hideDisplay(int displayIndex);

	[[nodiscard]] int displayCount() const;
	[[nodiscard]] rpl::producer<int> displayCountChanged() const;

private:
	void createDisplayWindow(int displayIndex, QScreen *screen);
	void destroyDisplayWindow(int displayIndex);
	void setupWindowGeometry(DisplayWindow &display);

	not_null<QWidget*> _parent;
	Ui::GL::Backend _backend;
	rpl::variable<bool> &_chatPanelShown;
	rpl::producer<bool> _gridMode;

	std::map<int, DisplayWindow> _displays;
	rpl::event_stream<int> _displayCountChanged;
	rpl::lifetime _lifetime;

};

[[nodiscard]] QString DisplayRoleText(DisplayRole role);

} // namespace Calls::Group
