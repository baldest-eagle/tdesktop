/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_display_coordinator.h"

#include "ui/widgets/labels.h"
#include "styles/style_calls.h"

#include <QtGui/QGuiApplication>
#include <QtGui/QScreen>
#include <QtWidgets/QWidget>

namespace Calls::Group {
namespace {

[[nodiscard]] QString RoleText(DisplayRole role) {
	switch (role) {
	case DisplayRole::ActiveSpeaker: return "Active Speaker";
	case DisplayRole::GridViewport: return "Grid View";
	case DisplayRole::ChatStation: return "Chat Station";
	default: return "";
	}
}

} // namespace

DisplayCoordinator::DisplayCoordinator(
	not_null<QWidget*> parent,
	Ui::GL::Backend backend,
	rpl::producer<bool> gridMode,
	rpl::variable<bool> &chatPanelShown)
: _parent(parent)
, _backend(backend)
, _chatPanelShown(chatPanelShown)
, _gridMode(std::move(gridMode)) {
	const auto app = qobject_cast<QGuiApplication*>(QGuiApplication::instance());
	if (!app) {
		return;
	}
	QObject::connect(app, &QGuiApplication::screenAdded, [this](QScreen *screen) {
		updateScreens();
	});
	QObject::connect(app, &QGuiApplication::screenRemoved, [this](QScreen *screen) {
		updateScreens();
	});
}

DisplayCoordinator::~DisplayCoordinator() = default;

void DisplayCoordinator::updateScreens() {
	const auto app = qobject_cast<QGuiApplication*>(QGuiApplication::instance());
	if (!app) {
		return;
	}
	const auto screens = app->screens();
	const auto primary = app->primaryScreen();

	std::set<int> currentIndices;
	for (int i = 0; i < screens.size(); ++i) {
		if (screens[i] == primary) {
			continue;
		}
		currentIndices.insert(i);
		if (_displays.find(i) == _displays.end()) {
			createDisplayWindow(i, screens[i]);
		}
	}

	std::vector<int> toRemove;
	for (const auto &entry : _displays) {
		if (currentIndices.find(entry.first) == currentIndices.end()) {
			toRemove.push_back(entry.first);
		}
	}
	for (int idx : toRemove) {
		destroyDisplayWindow(idx);
	}

	if (!toRemove.empty() || !currentIndices.empty()) {
		_displayCountChanged.fire(static_cast<int>(_displays.size()));
	}
}

void DisplayCoordinator::createDisplayWindow(int displayIndex, QScreen *screen) {
	if (_displays.find(displayIndex) != _displays.end()) {
		return;
	}

	auto &display = _displays[displayIndex];
	display.screen = screen;
	display.role = DisplayRole::GridViewport;

	// Create a QWidget for this display
	display.widget = std::make_unique<QWidget>();
	if (!display.widget) {
		_displays.erase(displayIndex);
		return;
	}

	display.widget->setWindowTitle(RoleText(display.role));
	display.widget->setAttribute(Qt::WA_OpaquePaintEvent);

	// Position on the target screen
	const auto screenGeo = screen->availableGeometry();
	display.widget->setGeometry(screenGeo);
	display.widget->show();

	// Set up content
	setupWindowGeometry(display);
}

void DisplayCoordinator::destroyDisplayWindow(int displayIndex) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (it->second.widget) {
		it->second.widget->hide();
		it->second.widget.reset();
	}
	_displays.erase(it);
}

void DisplayCoordinator::setupWindowGeometry(DisplayWindow &display) {
	if (!display.widget) {
		return;
	}

	const auto screen = display.screen;
	if (!screen) {
		return;
	}

	const auto geo = screen->availableGeometry();
	display.widget->setGeometry(geo);
}

void DisplayCoordinator::setRole(int displayIndex, DisplayRole role) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	it->second.role = role;
	if (it->second.widget) {
		it->second.widget->setWindowTitle(RoleText(role));
	}
}

DisplayRole DisplayCoordinator::role(int displayIndex) const {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return DisplayRole::None;
	}
	return it->second.role;
}

void DisplayCoordinator::showDisplay(int displayIndex) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (it->second.widget) {
		it->second.widget->show();
		it->second.widget->raise();
		it->second.widget->activateWindow();
	}
}

void DisplayCoordinator::hideDisplay(int displayIndex) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (it->second.widget) {
		it->second.widget->hide();
	}
}

int DisplayCoordinator::displayCount() const {
	return static_cast<int>(_displays.size());
}

rpl::producer<int> DisplayCoordinator::displayCountChanged() const {
	return _displayCountChanged.events();
}

QString DisplayRoleText(DisplayRole role) {
	return RoleText(role);
}

} // namespace Calls::Group
