/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_display_coordinator.h"

#include "calls/group/calls_group_viewport.h"
#include "ui/platform/ui_platform_utility.h"
#include "ui/widgets/labels.h"

#include <QtGui/QGuiApplication>
#include <QtGui/QScreen>
#include <QtWidgets/QShortcut>
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
		if (_displays.find(i) == _displays.end()
			&& _routedEndpoints.find(i) != _routedEndpoints.end()
			&& !_routedEndpoints[i].empty()) {
			createDisplayWindow(i, screens[i]);
		}
	}

	std::vector<int> toRemove;
	for (const auto &entry : _displays) {
		if (entry.first < 0 || entry.first >= screens.size()) {
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
	Ui::Platform::EnsureAppWindow(display.widget.get());

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

	const auto escapeShortcut = new QShortcut(
		QKeySequence(Qt::Key_Escape),
		display.widget.get());
	escapeShortcut->setContext(Qt::WidgetShortcut);
	QObject::connect(escapeShortcut, &QShortcut::activated, [this, displayIndex] {
		destroyDisplayWindow(displayIndex);
	});

	display.viewport->pinToggled(
	) | rpl::on_next([this, displayIndex](const Viewport::PinToggle &toggle) {
		if (!toggle.pinned) {
			unpinFromScreen(displayIndex, toggle.endpoint);
		}
	}, display.viewport->lifetime());

	display.viewport->tilesCountChanges(
	) | rpl::on_next([this, displayIndex](int count) {
		if (count == 0) {
			crl::on_main([this, displayIndex] {
				checkAndCleanupEmptyScreens();
			});
		}
	}, display.viewport->lifetime());

	display.viewport->qualityRequests(
	) | rpl::on_next([=](const VideoQualityRequest &request) {
		_qualityRequests.fire_copy(request.endpoint);
	}, display.viewport->lifetime());

	setupWindowGeometry(display);
	_displayCountChanged.fire(static_cast<int>(_displays.size()));
}

void DisplayCoordinator::destroyDisplayWindow(int displayIndex) {
	auto it = _displays.find(displayIndex);
	if (it == _displays.end()) {
		_routedEndpoints.erase(displayIndex);
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
	_displayCountChanged.fire(static_cast<int>(_displays.size()));
}

void DisplayCoordinator::setupWindowGeometry(DisplayWindow &display) {
	if (!display.widget || !display.viewport) {
		return;
	}

	const auto screen = display.screen;
	if (!screen) {
		return;
	}

	auto geo = screen->availableGeometry();
	if (geo.isEmpty()) {
		const auto primary = QGuiApplication::primaryScreen();
		if (primary) {
			geo = primary->availableGeometry();
		}
	}
	if (!geo.isEmpty()) {
		display.widget->setGeometry(geo);
		display.viewport->setGeometry(false, QRect(0, 0, geo.width(), geo.height()));
	}
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
	if (!it->second.viewport->isPinned(endpoint)) {
		it->second.viewport->add(
			endpoint,
			track,
			std::move(trackSize),
			rpl::single(true),
			self);
		it->second.viewport->togglePin(endpoint, true);
	}
	showDisplay(screenIndex);
}

void DisplayCoordinator::unpinFromScreen(int screenIndex, const VideoEndpoint &endpoint) {
	auto it = _displays.find(screenIndex);
	auto rit = _routedEndpoints.find(screenIndex);

	if (endpoint.id.empty()) {
		auto matching = std::vector<VideoEndpoint>();
		if (rit != _routedEndpoints.end()) {
			for (const auto &e : rit->second) {
				if (e.peer == endpoint.peer && e.type == endpoint.type) {
					matching.push_back(e);
				}
			}
		}
		for (const auto &m : matching) {
			if (it != _displays.end() && it->second.viewport) {
				it->second.viewport->remove(m);
			}
			if (rit != _routedEndpoints.end()) {
				rit->second.erase(m);
			}
		}
	} else {
		if (it != _displays.end() && it->second.viewport) {
			it->second.viewport->remove(endpoint);
		}
		if (rit != _routedEndpoints.end()) {
			rit->second.erase(endpoint);
		}
	}
	if (rit != _routedEndpoints.end() && rit->second.empty()) {
		_routedEndpoints.erase(rit);
	}
	checkAndCleanupEmptyScreens();
}

bool DisplayCoordinator::isPinnedOnScreen(int screenIndex, const VideoEndpoint &endpoint) const {
	auto it = _routedEndpoints.find(screenIndex);
	if (it == _routedEndpoints.end()) {
		return false;
	}
	if (endpoint.id.empty()) {
		return std::any_of(it->second.begin(), it->second.end(), [&](const VideoEndpoint &e) {
			return e.peer == endpoint.peer && e.type == endpoint.type;
		});
	}
	return it->second.find(endpoint) != it->second.end();
}

int DisplayCoordinator::pinnedCount(int screenIndex) const {
	auto it = _routedEndpoints.find(screenIndex);
	return (it != _routedEndpoints.end()) ? int(it->second.size()) : 0;
}

std::vector<VideoEndpoint> DisplayCoordinator::pinnedEndpoints(int screenIndex) const {
	auto it = _routedEndpoints.find(screenIndex);
	if (it == _routedEndpoints.end()) {
		return {};
	}
	return { it->second.begin(), it->second.end() };
}

bool DisplayCoordinator::hasPinnedFeeds(int screenIndex) const {
	const auto dit = _displays.find(screenIndex);
	if (dit != _displays.end() && dit->second.viewport) {
		if (dit->second.viewport->tilesCount() == 0) {
			return false;
		}
	}
	const auto it = _routedEndpoints.find(screenIndex);
	if (it == _routedEndpoints.end() || it->second.empty()) {
		return false;
	}
	return true;
}

void DisplayCoordinator::checkAndCleanupEmptyScreens() {
	std::vector<int> emptyRouted;
	for (const auto &[screenIndex, endpoints] : _routedEndpoints) {
		if (endpoints.empty()) {
			emptyRouted.push_back(screenIndex);
		}
	}
	for (const auto idx : emptyRouted) {
		_routedEndpoints.erase(idx);
	}

	std::vector<int> toDestroy;
	for (const auto &[displayIndex, _] : _displays) {
		if (!hasPinnedFeeds(displayIndex)) {
			toDestroy.push_back(displayIndex);
		}
	}
	for (const auto idx : toDestroy) {
		destroyDisplayWindow(idx);
	}
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
	if (it == _displays.end() || !it->second.viewport) {
		return;
	}
	if (!it->second.viewport->isPinned(endpoint)) {
		it->second.viewport->add(endpoint, track, std::move(trackSize), std::move(pinned), self);
		it->second.viewport->togglePin(endpoint, true);
	}
}

void DisplayCoordinator::removeVideoTrack(int displayIndex, const VideoEndpoint &endpoint) {
	auto it = _displays.find(displayIndex);
	if (it != _displays.end() && it->second.viewport) {
		it->second.viewport->remove(endpoint);
	}
	auto rit = _routedEndpoints.find(displayIndex);
	if (rit != _routedEndpoints.end()) {
		rit->second.erase(endpoint);
		if (rit->second.empty()) {
			_routedEndpoints.erase(rit);
		}
	}
	checkAndCleanupEmptyScreens();
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

std::vector<int> DisplayCoordinator::activeScreenIndices() const {
	auto result = std::vector<int>();
	result.reserve(_displays.size());
	for (const auto &[index, _] : _displays) {
		result.push_back(index);
	}
	return result;
}

bool DisplayCoordinator::hasTrack(int displayIndex, const VideoEndpoint &endpoint) const {
	const auto it = _displays.find(displayIndex);
	if (it == _displays.end() || !it->second.viewport) {
		return false;
	}
	return it->second.viewport->isPinned(endpoint);
}

void DisplayCoordinator::removeVideoTrackFromAll(const VideoEndpoint &endpoint) {
	auto toRemove = std::vector<VideoEndpoint>();
	for (const auto &[screenIndex, endpoints] : _routedEndpoints) {
		for (const auto &e : endpoints) {
			if (endpoint.id.empty()) {
				if (e.peer == endpoint.peer && e.type == endpoint.type) {
					toRemove.push_back(e);
				}
			} else if (e == endpoint || (e.peer == endpoint.peer && e.type == endpoint.type)) {
				toRemove.push_back(e);
			}
		}
	}
	const auto displayIndices = activeScreenIndices();
	for (const auto &ep : toRemove) {
		for (const auto idx : displayIndices) {
			const auto it = _displays.find(idx);
			if (it != _displays.end() && it->second.viewport) {
				it->second.viewport->remove(ep);
			}
		}
		for (auto &[screenIndex, endpoints] : _routedEndpoints) {
			endpoints.erase(ep);
		}
	}
	for (const auto idx : displayIndices) {
		const auto it = _displays.find(idx);
		if (it != _displays.end() && it->second.viewport) {
			it->second.viewport->remove(endpoint);
		}
	}
	checkAndCleanupEmptyScreens();
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
