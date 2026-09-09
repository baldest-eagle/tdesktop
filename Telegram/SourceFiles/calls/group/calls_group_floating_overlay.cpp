/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_floating_overlay.h"

#include "calls/group/calls_group_call.h"
#include "calls/group/calls_group_messages.h"
#include "calls/group/calls_group_messages_ui.h"
#include "calls/group/calls_group_panel.h"
#include "data/data_group_call.h"
#include "data/data_peer.h"
#include "data/data_session.h"
#include "history/history.h"
#include "history/history_item.h"
#include "history/view/history_view_element.h"
#include "chat_helpers/compose/compose_show.h"
#include "window/window_session_controller.h"
#include "main/main_session.h"
#include "ui/layers/show.h"
#include "ui/widgets/buttons.h"
#include "ui/widgets/labels.h"

#include <QtGui/QGuiApplication>
#include <QtGui/QKeyEvent>
#include <QtGui/QMouseEvent>
#include <QtGui/QPainter>
#include <QtGui/QScreen>
#include <QtWidgets/QApplication>

#include "styles/style_calls.h"

namespace Calls::Group {

FloatingOverlay::FloatingOverlay(not_null<Panel*> panel)
: QWidget(nullptr, Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint)
, _panel(panel) {
	setAttribute(Qt::WA_TranslucentBackground);
	setAttribute(Qt::WA_ShowWithoutActivating);

	const auto screen = QApplication::primaryScreen()->availableGeometry();
	setGeometry(screen.width() - 320, 100, 300, 400);

	_tabs.push_back({ nullptr, u"Call Chat"_q });

	setupUI();

	_toggleShortcut = new QShortcut(QKeySequence(u"Ctrl+Shift+T"_q), this);
	_toggleShortcut->setContext(Qt::ApplicationShortcut);
	connect(_toggleShortcut, &QShortcut::activated, this, [=] { toggle(); });

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
	if (!isHidden()) {
		hide();
	} else {
		show();
	}
}

bool FloatingOverlay::isVisible() const {
	return !isHidden();
}

void FloatingOverlay::addChat(not_null<PeerData*> peer) {
	for (int i = 0; i < _tabs.size(); ++i) {
		if (_tabs[i].peer == peer) {
			setActiveTab(i);
			return;
		}
	}
	if (_tabs.size() >= 3) {
		return;
	}
	_tabs.push_back({ peer, peer->name() });
	setActiveTab(_tabs.size() - 1);
}

void FloatingOverlay::removeChat(PeerData *peer) {
	const auto i = std::find_if(_tabs.begin(), _tabs.end(), [&](const OverlayTab &t) {
		return t.peer == peer;
	});
	if (i != _tabs.end()) {
		_tabs.erase(i);
		if (_tabs.empty()) {
			_tabs.push_back({ nullptr, u"Call Chat"_q });
		}
		if (_activeTabIndex >= _tabs.size()) {
			_activeTabIndex = _tabs.size() - 1;
		}
		setActiveTab(_activeTabIndex);
	}
}

void FloatingOverlay::setActiveTab(int index) {
	if (index < 0 || index >= _tabs.size()) {
		return;
	}
	_activeTabIndex = index;
	setupChatContent();
	update();
}

void FloatingOverlay::updateTabRects() {
	_tabRects.clear();
	if (_tabs.size() <= 1) {
		return;
	}
	int x = 10;
	const int y = 5;
	const int h = 26;

	QFont font = st::callButtonLabel.style.font;
	QFontMetrics fm(font);

	for (int i = 0; i < _tabs.size(); ++i) {
		const auto &tab = _tabs[i];
		const int textW = fm.horizontalAdvance(tab.name);
		const int closeW = (i == 0) ? 0 : 16;
		const int dotW = (tab.peer != nullptr) ? 8 : 0;
		const int tabW = 8 + dotW + textW + closeW + 8;

		QRect r(x, y, tabW, h);
		QRect cr = closeW ? QRect(x + 8 + dotW + textW + 2, y + (h - 12)/2, 12, 12) : QRect();

		_tabRects.push_back({ r, cr });
		x += tabW + 5;
	}
}

void FloatingOverlay::toggleSearch() {
	_searchOpen = !_searchOpen;
	_searchQuery = QString();
	updateSearchResults();
	update();
}

void FloatingOverlay::updateSearchResults() {
	_searchResults.clear();
	if (!_searchOpen) {
		return;
	}
	const auto real = _panel->call()->lookupReal();
	if (!real) {
		return;
	}
	const auto &participants = real->participants();
	int y = 45;
	const int rowHeight = 32;
	for (const auto &p : participants) {
		const auto peer = p.peer;
		const auto name = peer->name();
		if (!_searchQuery.isEmpty() && !name.contains(_searchQuery, Qt::CaseInsensitive)) {
			continue;
		}
		const auto rowRect = QRect(10, y, width() - 20, rowHeight);
		const auto openChatRect = QRect(width() - 170, y + 4, 45, 24);
		const auto pinScreenRect = QRect(width() - 120, y + 4, 40, 24);
		const auto addOverlayRect = QRect(width() - 75, y + 4, 65, 24);
		_searchResults.push_back({
			peer,
			name,
			rowRect,
			openChatRect,
			pinScreenRect,
			addOverlayRect,
		});
		y += rowHeight + 4;
		if (y > height() - 50) {
			break;
		}
	}
}

void FloatingOverlay::keyPressEvent(QKeyEvent *event) {
	if (event->key() == Qt::Key_Escape) {
		if (_searchOpen) {
			toggleSearch();
			return;
		}
		hide();
	} else if (event->matches(QKeySequence::Find) || (event->key() == Qt::Key_F && (event->modifiers() & Qt::ControlModifier))) {
		toggleSearch();
		return;
	} else if (_searchOpen) {
		if (event->key() == Qt::Key_Backspace) {
			if (!_searchQuery.isEmpty()) {
				_searchQuery.chop(1);
				updateSearchResults();
				update();
			}
			return;
		} else if (!event->text().isEmpty() && event->text().at(0).isPrint()) {
			_searchQuery.append(event->text());
			updateSearchResults();
			update();
			return;
		}
	}
	QWidget::keyPressEvent(event);
}

void FloatingOverlay::mousePressEvent(QMouseEvent *event) {
	if (event->button() == Qt::LeftButton && !_passthrough) {
		const auto pos = event->pos();
		if (_searchOpen) {
			for (const auto &res : _searchResults) {
				if (res.openChatRect.contains(pos)) {
					const auto resolved = _panel->uiShow()->resolveWindow();
					if (resolved) {
						resolved->showPeerHistory(res.peer);
					}
					toggleSearch();
					event->accept();
					return;
				} else if (res.pinScreenRect.contains(pos)) {
					const auto real = _panel->call()->lookupReal();
					const auto participant = real ? real->participantByPeer(res.peer) : nullptr;
					if (participant) {
						const auto endpoint = VideoEndpoint{
							VideoEndpointType::Camera,
							res.peer,
							participant->cameraEndpoint(),
						};
						_panel->promptPinTargetScreen(endpoint);
					}
					toggleSearch();
					event->accept();
					return;
				} else if (res.addOverlayRect.contains(pos)) {
					addChat(res.peer);
					toggleSearch();
					event->accept();
					return;
				}
			}
		}

		if (_tabs.size() > 1) {
			updateTabRects();
			for (int i = 0; i < _tabs.size(); ++i) {
				const auto &tr = _tabRects[i];
				if (i > 0 && tr.closeRect.contains(pos)) {
					removeChat(_tabs[i].peer);
					event->accept();
					return;
				} else if (tr.rect.contains(pos)) {
					setActiveTab(i);
					event->accept();
					return;
				}
			}
		}

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

void FloatingOverlay::wheelEvent(QWheelEvent *event) {
	if (event->modifiers() & Qt::ControlModifier) {
		const auto delta = event->angleDelta().y();
		if (delta > 0) {
			_opacity = std::min(1.0f, _opacity + 0.05f);
		} else if (delta < 0) {
			_opacity = std::max(0.2f, _opacity - 0.05f);
		}
		setWindowOpacity(_opacity);
		update();
		event->accept();
		return;
	}
	QWidget::wheelEvent(event);
}

void FloatingOverlay::paintEvent(QPaintEvent *event) {
	auto p = QPainter(this);
	p.setOpacity(_opacity);
	p.fillRect(rect(), QColor(30, 30, 30, 220));
	p.setPen(QColor(255, 255, 255, 100));
	p.drawRect(rect().adjusted(0, 0, -1, -1));

	if (_tabs.size() > 1 && !_searchOpen) {
		updateTabRects();
		QFont font = st::callButtonLabel.style.font;
		p.setFont(font);
		for (int i = 0; i < _tabs.size(); ++i) {
			const auto &tab = _tabs[i];
			const auto &tr = _tabRects[i];
			const bool active = (i == _activeTabIndex);

			if (active) {
				p.fillRect(tr.rect, QColor(60, 60, 60, 200));
			} else {
				p.fillRect(tr.rect, QColor(40, 40, 40, 100));
			}

			p.setPen(QColor(255, 255, 255, 40));
			p.drawRect(tr.rect);

			bool hasUnread = false;
			if (tab.peer) {
				const auto history = tab.peer->owner().historyLoaded(tab.peer);
				hasUnread = history && (history->unreadCount() > 0 || history->unreadMark());
			}

			if (hasUnread && !active) {
				p.setBrush(QColor(82, 136, 236));
				p.setPen(Qt::NoPen);
				p.drawEllipse(QPoint(tr.rect.left() + 7, tr.rect.center().y()), 3, 3);
			}

			p.setPen(active ? QColor(255, 255, 255) : QColor(200, 200, 200));
			const int textOffset = (hasUnread && !active) ? 14 : 8;
			p.drawText(tr.rect.adjusted(textOffset, 0, 0, 0), Qt::AlignVCenter | Qt::AlignLeft, tab.name);

			if (i > 0) {
				p.setPen(QColor(255, 255, 255, 120));
				p.drawText(tr.closeRect, Qt::AlignCenter, u"x"_q);
			}
		}
	}

	if (_searchOpen) {
		p.fillRect(QRect(0, 0, width(), height()), QColor(20, 20, 20, 245));

		p.setFont(st::callButtonLabel.style.font);
		p.setPen(QColor(255, 255, 255));
		const auto prompt = u"Search Callers: "_q + _searchQuery + u"|"_q;
		p.drawText(QRect(10, 10, width() - 50, 26), Qt::AlignVCenter | Qt::AlignLeft, prompt);

		for (const auto &res : _searchResults) {
			p.fillRect(res.rowRect, QColor(40, 40, 40, 180));
			p.setPen(QColor(255, 255, 255, 40));
			p.drawRect(res.rowRect);

			p.setPen(QColor(255, 255, 255));
			p.drawText(res.rowRect.adjusted(8, 0, -180, 0), Qt::AlignVCenter | Qt::AlignLeft, res.name);

			p.fillRect(res.openChatRect, QColor(50, 80, 120, 220));
			p.setPen(QColor(200, 230, 255));
			p.drawText(res.openChatRect, Qt::AlignCenter, u"Chat"_q);

			p.fillRect(res.pinScreenRect, QColor(60, 100, 70, 220));
			p.setPen(QColor(200, 255, 220));
			p.drawText(res.pinScreenRect, Qt::AlignCenter, u"Pin"_q);

			p.fillRect(res.addOverlayRect, QColor(100, 70, 120, 220));
			p.setPen(QColor(240, 210, 255));
			p.drawText(res.addOverlayRect, Qt::AlignCenter, u"+Overlay"_q);
		}
	}

	QWidget::paintEvent(event);
}

void FloatingOverlay::resizeEvent(QResizeEvent *event) {
	QWidget::resizeEvent(event);
	if (_messagesUi) {
		_messagesUi->move(4, 35, width() - 8, height() - 44);
	}
	if (_closeBtn) {
		_closeBtn->move(width() - 30, 5);
	}
	if (_passthroughBtn) {
		_passthroughBtn->move(width() - 55, 5);
	}
	if (_searchBtn) {
		_searchBtn->move(width() - 80, 5);
	}
}

void FloatingOverlay::setupUI() {
	_title.create(this, st::callButtonLabel);
	_title->setText(u"Chat"_q);
	_title->move(10, 10);

	_closeBtn.create(this, st::callAnswer.button);
	_closeBtn->move(width() - 30, 5);
	_closeBtn->setClickedCallback([=] { hide(); });

	_passthroughBtn.create(this, st::callAnswer.button);
	_passthroughBtn->move(width() - 55, 5);
	_passthroughBtn->setClickedCallback([=] { togglePassthrough(); });

	_searchBtn.create(this, st::callAnswer.button);
	_searchBtn->move(width() - 80, 5);
	_searchBtn->setClickedCallback([=] { toggleSearch(); });

	setupChatContent();
}

void FloatingOverlay::setupChatContent() {
	_messagesUi = nullptr;
	_tabLifetime.destroy();

	if (_tabs.size() > 1 && _title) {
		_title->hide();
	} else if (_title) {
		_title->show();
	}

	const auto &tab = _tabs[_activeTabIndex];
	if (!tab.peer) {
		const auto call = _panel->call();
		_messagesUi = std::make_unique<MessagesUi>(
			this,
			_panel->uiShow(),
			MessagesMode::GroupCall,
			call->messages()->listValue(),
			nullptr,
			call->messages()->idUpdates(),
			call->canManageValue(),
			call->messagesEnabledValue(),
			[=](QPoint) { return false; });
	} else {
		const auto peer = tab.peer;
		auto getMessages = [=] {
			std::vector<Message> result;
			const auto history = peer->owner().history(peer);
			for (const auto &block : history->blocks) {
				for (const auto &item : block->messages) {
					const auto data = item->data();
					if (!data) continue;
					result.push_back({
						data->id,
						data->date(),
						0,  // pinFinishDate
						data->from() ? data->from() : data->history()->peer,
						data->originalText(),
						0,  // stars
						false,  // failed
						false,  // admin
						data->out()
					});
				}
			}
			if (result.size() > 50) {
				result.erase(result.begin(), result.end() - 50);
			}
			return result;
		};

		auto messagesVar = std::make_shared<rpl::variable<std::vector<Message>>>(getMessages());

		peer->session().data().newItemAdded(
		) | rpl::on_next([=](not_null<HistoryItem*> item) {
			if (item->history()->peer == peer) {
				messagesVar->reset(getMessages());
			}
		}, _tabLifetime);

		_messagesUi = std::make_unique<MessagesUi>(
			this,
			_panel->uiShow(),
			MessagesMode::GroupCall,
			messagesVar->value(),
			nullptr,
			rpl::never<MessageIdUpdate>(),
			rpl::single(false),
			rpl::single(true),
			[=](QPoint) { return false; });
	}

	if (_messagesUi) {
		_messagesUi->move(4, 35, width() - 8, height() - 44);
	}
}

void FloatingOverlay::updateGeometry() {
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
