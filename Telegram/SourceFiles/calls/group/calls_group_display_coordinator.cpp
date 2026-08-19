/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_display_coordinator.h"

#include "calls/group/calls_group_viewport.h"
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

	// Detect existing screens on startup
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

	// Create a Viewport for this display
	display.viewport = std::make_unique<Viewport>(
		display.widget.get(),
		PanelMode::Wide,
		_backend);
	if (!display.viewport) {
		display.widget.reset();
		_displays.erase(displayIndex);
		return;
	}

	// Position on the target screen
	const auto screenGeo = screen->availableGeometry();
	display.widget->setGeometry(screenGeo);
	display.widget->show();

	// Connect quality requests from this viewport
	display.viewport->qualityRequests(
	) | rpl::on_next([=](const VideoQualityRequest &request) {
		_qualityRequests.fire(request.endpoint);
	}, display.viewport->lifetime());

	// Set up content
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
	// Clean up routed endpoints for this display
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

	// Set viewport geometry to fill the widget
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

	// Re-route video based on new role
	if (role == DisplayRole::ActiveSpeaker && _activeSpeaker) {
		// Show active speaker large
		showLarge(displayIndex, /* active speaker endpoint */);
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

void DisplayCoordinator::addVideoTrack(
		int displayIndex,
		const VideoEndpoint &endpoint,
		const VideoTileTrack &track,
		rpl::producer<QSize> trackSize,
		rpl::producer<bool> pinned,
		bool self) {
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
	// Find the loudest speaker
	PeerData* newSpeaker = nullptr;
	double maxLevel = 0.0;
	for (const auto &[peer, level] : levels) {
		if (level > maxLevel && level > _speakerThreshold) {
			maxLevel = level;
			newSpeaker = peer;
		}
	}

	if (newSpeaker != _activeSpeaker) {
		_activeSpeaker = newSpeaker;
		// Update displays with ActiveSpeaker role
		for (auto &[index, display] : _displays) {
			if (display.role == DisplayRole::ActiveSpeaker && display.viewport) {
				// Show the active speaker large
				// Note: need to find the endpoint for this peer
			}
		}
	}
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
