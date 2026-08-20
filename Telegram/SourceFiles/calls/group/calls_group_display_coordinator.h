/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#pragma once

#include "base/object_ptr.h"
#include "base/unique_qptr.h"
#include "ui/rp_widget.h"
#include "calls/group/calls_group_call.h"
#include "calls/group/calls_group_common.h"
#include "calls/group/calls_group_viewport.h"

#include <QtGui/QScreen>

#include <map>
#include <set>
#include <utility>

class QWidget;

namespace Ui {
class FlatLabel;
namespace GL {
enum class Backend;
} // namespace GL
} // namespace Ui

namespace Calls::Group {

class Viewport;
enum class PanelMode;

enum class DisplayRole {
	ActiveSpeaker,
	GridViewport,
	ChatStation,
	None,
};

struct DisplayWindow {
	base::unique_qptr<QWidget> widget;
	std::unique_ptr<Viewport> viewport;
	DisplayRole role = DisplayRole::None;
	QScreen *screen = nullptr;
};

class DisplayCoordinator final {
public:
	DisplayCoordinator(
		not_null<QWidget*> parent,
		Ui::GL::Backend backend,
		rpl::variable<bool> gridMode,
		rpl::variable<bool> &chatPanelShown);
	~DisplayCoordinator();

	void updateScreens();
	void setRole(int displayIndex, DisplayRole role);
	DisplayRole role(int displayIndex) const;

	void showDisplay(int displayIndex);
	void hideDisplay(int displayIndex);

	// Video routing & Pinning Stage
	void pinToScreen(
		int screenIndex,
		const VideoEndpoint &endpoint,
		const VideoTileTrack &track,
		rpl::producer<QSize> trackSize,
		bool self);
	void unpinFromScreen(int screenIndex, const VideoEndpoint &endpoint);
	[[nodiscard]] bool isPinnedOnScreen(int screenIndex, const VideoEndpoint &endpoint) const;
	[[nodiscard]] int pinnedCount(int screenIndex) const;
	void ensureStageWindow(int screenIndex);

	void addVideoTrack(
		int displayIndex,
		const VideoEndpoint &endpoint,
		const VideoTileTrack &track,
		rpl::producer<QSize> trackSize,
		rpl::producer<bool> pinned,
		bool self);
	void removeVideoTrack(int displayIndex, const VideoEndpoint &endpoint);
	void showLarge(int displayIndex, const VideoEndpoint &endpoint);

	// Active speaker detection
	void updateAudioLevels(const std::vector<std::pair<PeerData*, double>> &levels);

	[[nodiscard]] int displayCount() const;
	[[nodiscard]] rpl::producer<int> displayCountChanged() const;
	[[nodiscard]] rpl::producer<VideoEndpoint> qualityRequests() const;

private:
	void createDisplayWindow(int displayIndex, QScreen *screen);
	void destroyDisplayWindow(int displayIndex);
	void setupWindowGeometry(DisplayWindow &display);
	void updateViewportParent(int displayIndex);

	not_null<QWidget*> _parent;
	Ui::GL::Backend _backend;
	rpl::variable<bool> &_chatPanelShown;
	rpl::variable<bool> _gridMode;

	std::map<int, DisplayWindow> _displays;
	std::map<int, std::set<VideoEndpoint>> _routedEndpoints;
	rpl::event_stream<int> _displayCountChanged;
	rpl::event_stream<VideoEndpoint> _qualityRequests;
	rpl::lifetime _lifetime;

	// Active speaker tracking
	PeerData *_activeSpeaker = nullptr;
	std::map<not_null<PeerData*>, VideoEndpoint> _peerToEndpoints;
	double _speakerThreshold = 0.05;
	int _speakerHoldFrames = 0;

};

[[nodiscard]] QString DisplayRoleText(DisplayRole role);

} // namespace Calls::Group
