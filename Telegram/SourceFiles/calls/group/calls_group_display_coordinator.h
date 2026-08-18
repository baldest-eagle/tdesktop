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
struct VideoEndpoint;
struct VideoTileTrack;
enum class PanelMode;

enum class DisplayRole {
	ActiveSpeaker,
	GridViewport,
	ChatStation,
	None,
};

struct DisplayWindow {
	std::unique_ptr<QWidget> widget;
	std::unique_ptr<Viewport> viewport;
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

	// Video routing
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
	rpl::producer<bool> _gridMode;

	std::map<int, DisplayWindow> _displays;
	rpl::event_stream<int> _displayCountChanged;
	rpl::event_stream<VideoEndpoint> _qualityRequests;
	rpl::lifetime _lifetime;

	// Active speaker tracking
	PeerData *_activeSpeaker = nullptr;
	double _speakerThreshold = 0.05;

};

[[nodiscard]] QString DisplayRoleText(DisplayRole role);

} // namespace Calls::Group
