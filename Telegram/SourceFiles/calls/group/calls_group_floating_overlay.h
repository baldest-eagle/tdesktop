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

#include "ui/widgets/buttons.h"
#include "ui/widgets/labels.h"

class PeerData;

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

	void addChat(not_null<PeerData*> peer);
	void removeChat(PeerData *peer);
	void setActiveTab(int index);

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
	struct OverlayTab {
		PeerData *peer = nullptr;
		QString name;
	};

	struct TabRect {
		QRect rect;
		QRect closeRect;
	};

	struct SearchResult {
		not_null<PeerData*> peer;
		QString name;
		QRect rowRect;
		QRect openChatRect;
		QRect pinScreenRect;
		QRect addOverlayRect;
	};

	void setupUI();
	void updateGeometry();
	void togglePassthrough();
	void toggleSearch();
	void setupChatContent();
	void updateTabRects();
	void updateSearchResults();

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
	object_ptr<Ui::IconButton> _searchBtn = { nullptr };

	std::unique_ptr<MessagesUi> _messagesUi;

	std::vector<OverlayTab> _tabs;
	int _activeTabIndex = 0;
	std::vector<TabRect> _tabRects;
	rpl::lifetime _tabLifetime;

	bool _searchOpen = false;
	QString _searchQuery;
	std::vector<SearchResult> _searchResults;

};

} // namespace Calls::Group
