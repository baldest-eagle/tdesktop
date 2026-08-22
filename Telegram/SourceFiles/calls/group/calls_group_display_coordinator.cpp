/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_display_coordinator.h"

#include "calls/group/calls_group_viewport.h"
#include "ui/widgets/labels.h"

#include <QtGui/QGuiApplication>
#include <QtGui/QScreen>
#include <QtWidgets/QWidget>

#include "styles/style_calls.h"

namespace Calls::Group {
namespace {

[[nodiscard]] QString RoleText(DisplayRole role) {
	switch (role) {
	case DisplayRole::ActiveSpeaker: return u"Active Speaker"_q;
	case DisplayRole::GridViewport: return u"Grid View"_q;
	case DisplayRole::ChatStation: return u"Chat Station"_q;
	default: return QString();
	}
}

} // namespace

DisplayCoordinator::DisplayCoordinator(
	not_null<QWidget*> parent,
	Ui::GL::Backend backend,
	rpl::variable<bool> gridMode,
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

	updateScreens();
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
	for (auto i = 0; i != screens.size(); ++i) {
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
	for (const auto idx : toRemove) {
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

	display.widget = base::make_unique_q<QWidget>(
		nullptr,
		Qt::Window | Qt::FramelessWindowHint);
	if (!display.widget) {
		_displays.erase(displayIndex);
		return;
	}

	display.widget->setWindowTitle(RoleText(display.role));
	display.widget->setAttribute(Qt::WA_OpaquePaintEvent);

	display.viewport = std::make_unique<Viewport>(
		display.widget.get(),
		PanelMode::Wide,
		_backend);
	if (!display.viewport) {
		display.widget.reset();
		_displays.erase(displayIndex);
		return;
	}

	const auto screenGeo = screen->geometry();
	display.widget->setGeometry(screenGeo);
	display.viewport->widget()->show();
	display.widget->show();
	display.widget->raise();

	display.viewport->qualityRequests(
	) | rpl::on_next([=](const VideoQualityRequest &request) {
		_qualityRequests.fire_copy(request.endpoint);
	}, display.viewport->lifetime());

	setupWindowGeometry(display);
}

void DisplayCoordinator::destroyDisplayWindow(int displayIndex) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (it->second.viewport) {
		it->second.viewport.reset();
	}
	if (it->second.widget) {
		it->second.widget->hide();
		it->second.widget.reset();
	}
	_displays.erase(it);
	_routedEndpoints.erase(displayIndex);
}

void DisplayCoordinator::setupWindowGeometry(DisplayWindow &display) {
	if (!display.widget || !display.viewport) {
		return;
	}

	const auto screen = display.screen;
	if (!screen) {
		return;
	}

	const auto geo = screen->availableGeometry();
	display.widget->setGeometry(geo);

	display.viewport->setGeometry(false, QRect(0, 0, geo.width(), geo.height()));
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

void DisplayCoordinator::ensureStageWindow(int screenIndex) {
	if (_displays.find(screenIndex) != _displays.end()) {
		return;
	}
	const auto app = qobject_cast<QGuiApplication*>(QGuiApplication::instance());
	if (!app) {
		return;
	}
	const auto screens = app->screens();
	if (screenIndex >= 0 && screenIndex < screens.size()) {
		createDisplayWindow(screenIndex, screens[screenIndex]);
	} else if (!screens.empty()) {
		createDisplayWindow(screenIndex, screens.front());
	}
}

void DisplayCoordinator::pinToScreen(
		int screenIndex,
		const VideoEndpoint &endpoint,
		const VideoTileTrack &track,
		rpl::producer<QSize> trackSize,
		bool self) {
	ensureStageWindow(screenIndex);
	auto it = _displays.find(screenIndex);
	if (it == _displays.end() || !it->second.viewport) {
		return;
	}
	_routedEndpoints[screenIndex].insert(endpoint);
	it->second.viewport->add(
		endpoint,
		track,
		std::move(trackSize),
		rpl::single(true),
		self);
	it->second.viewport->togglePin(endpoint, true);
	showDisplay(screenIndex);
}

void DisplayCoordinator::unpinFromScreen(int screenIndex, const VideoEndpoint &endpoint) {
	auto it = _displays.find(screenIndex);
	if (it == _displays.end() || !it->second.viewport) {
		return;
	}
	_routedEndpoints[screenIndex].erase(endpoint);
	it->second.viewport->togglePin(endpoint, false);
	it->second.viewport->remove(endpoint);
	if (_routedEndpoints[screenIndex].empty()) {
		hideDisplay(screenIndex);
	}
}

bool DisplayCoordinator::isPinnedOnScreen(int screenIndex, const VideoEndpoint &endpoint) const {
	auto it = _routedEndpoints.find(screenIndex);
	if (it == _routedEndpoints.end()) {
		return false;
	}
	return it->second.find(endpoint) != it->second.end();
}

int DisplayCoordinator::pinnedCount(int screenIndex) const {
	auto it = _routedEndpoints.find(screenIndex);
	return (it != _routedEndpoints.end()) ? int(it->second.size()) : 0;
}

void DisplayCoordinator::addVideoTrack(
		int displayIndex,
		const VideoEndpoint &endpoint,
		const VideoTileTrack &track,
		rpl::producer<QSize> trackSize,
		rpl::producer<bool> pinned,
		bool self) {
	_peerToEndpoints[endpoint.peer] = endpoint;
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (!it->second.viewport) {
		return;
	}
	it->second.viewport->add(endpoint, track, std::move(trackSize), std::move(pinned), self);
}

void DisplayCoordinator::removeVideoTrack(int displayIndex, const VideoEndpoint &endpoint) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (!it->second.viewport) {
		return;
	}
	it->second.viewport->remove(endpoint);
}

void DisplayCoordinator::showLarge(int displayIndex, const VideoEndpoint &endpoint) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		return;
	}
	if (!it->second.viewport) {
		return;
	}
	it->second.viewport->showLarge(endpoint);
}

void DisplayCoordinator::updateAudioLevels(const std::vector<std::pair<PeerData*, double>> &levels) {
	// Active speaker auto-stealing disabled to ensure only explicitly pinned feeds appear on secondary displays
}

int DisplayCoordinator::displayCount() const {
	return static_cast<int>(_displays.size());
}

rpl::producer<int> DisplayCoordinator::displayCountChanged() const {
	return _displayCountChanged.events();
}

rpl::producer<VideoEndpoint> DisplayCoordinator::qualityRequests() const {
	return _qualityRequests.events();
}

QString DisplayRoleText(DisplayRole role) {
	return RoleText(role);
}

} // namespace Calls::Group
