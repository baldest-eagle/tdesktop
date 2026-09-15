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
#include "ui/abstract_button.h"
#include "ui/widgets/buttons.h"
#include "ui/widgets/labels.h"

#include <QtGui/QCloseEvent>
#include <QtGui/QGuiApplication>
#include <QtGui/QKeyEvent>
#include <QtGui/QMouseEvent>
#include <QtGui/QPainter>
#include <QtGui/QPainterPath>
#include <QtGui/QScreen>
#include <QtWidgets/QApplication>

#include "styles/style_calls.h"

namespace Calls::Group {

class HeaderButton final : public Ui::AbstractButton {
public:
	enum class Type {
		Close,
		Search,
		Passthrough,
	};

	HeaderButton(QWidget *parent, Type type)
	: AbstractButton(parent)
	, _type(type) {
		setPointerCursor(true);
		resize(28, 28);
	}

	void setActive(bool active) {
		if (_active != active) {
			_active = active;
			update();
		}
	}

protected:
	void paintEvent(QPaintEvent *e) override {
		auto p = QPainter(this);
		p.setRenderHint(QPainter::Antialiasing);

		const auto r = rect();
		if (isDown()) {
			p.setPen(Qt::NoPen);
			p.setBrush(QColor(255, 255, 255, 40));
			p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 5, 5);
		} else if (isOver()) {
			p.setPen(Qt::NoPen);
			p.setBrush(QColor(255, 255, 255, _type == Type::Close ? 55 : 25));
			p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 5, 5);
		} else if (_active) {
			p.setPen(Qt::NoPen);
			p.setBrush(QColor(82, 136, 236, 80));
			p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 5, 5);
		}

		auto iconColor = _active
			? QColor(100, 175, 255)
			: (_type == Type::Close && isOver())
			? QColor(255, 90, 90)
			: isOver()
			? QColor(255, 255, 255)
			: QColor(200, 205, 215);

		p.setPen(QPen(iconColor, 1.8, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin));

		const auto center = r.center();
		if (_type == Type::Close) {
			const int d = 5;
			p.drawLine(center.x() - d, center.y() - d, center.x() + d, center.y() + d);
			p.drawLine(center.x() + d, center.y() - d, center.x() - d, center.y() + d);
		} else if (_type == Type::Search) {
			p.setBrush(Qt::NoBrush);
			p.drawEllipse(QPoint(center.x() - 1, center.y() - 1), 5, 5);
			p.drawLine(center.x() + 3, center.y() + 3, center.x() + 7, center.y() + 7);
		} else if (_type == Type::Passthrough) {
			p.setBrush(Qt::NoBrush);
			p.drawLine(center.x(), center.y() - 6, center.x(), center.y() + 3);
			p.drawLine(center.x() - 5, center.y() - 2, center.x() + 5, center.y() - 2);
			p.drawLine(center.x() - 3, center.y() - 6, center.x() + 3, center.y() - 6);
			p.drawLine(center.x(), center.y() + 3, center.x(), center.y() + 7);
		}
	}

private:
	Type _type;
	bool _active = false;
};

class OpacitySlider final : public QWidget {
public:
	OpacitySlider(QWidget *parent)
	: QWidget(parent) {
		setCursor(Qt::PointingHandCursor);
		setToolTip(u"Adjust overlay transparency (or Ctrl+Wheel)"_q);
	}

	void setValue(float val) {
		_value = std::clamp(val, _minVal, _maxVal);
		update();
	}

	[[nodiscard]] float value() const {
		return _value;
	}

	void setChangedCallback(Fn<void(float)> callback) {
		_callback = std::move(callback);
	}

protected:
	void paintEvent(QPaintEvent *e) override {
		auto p = QPainter(this);
		p.setRenderHint(QPainter::Antialiasing);

		const auto center = QPointF(10.0, height() / 2.0);
		const auto iconColor = (_hovered || _dragging)
			? QColor(220, 225, 235)
			: QColor(160, 165, 175);
		p.setPen(QPen(iconColor, 1.2));
		p.setBrush(Qt::NoBrush);
		p.drawEllipse(center, 5.0, 5.0);
		p.setBrush(iconColor);
		p.drawPie(QRectF(5.0, height() / 2.0 - 5.0, 10.0, 10.0), 90 * 16, 180 * 16);

		const auto trackLeft = 24.0f;
		const auto trackRight = float(width() - 40);
		const auto trackY = (height() - 4) / 2.0f;
		p.setPen(Qt::NoPen);
		p.setBrush(QColor(255, 255, 255, 38));
		p.drawRoundedRect(QRectF(trackLeft, trackY, trackRight - trackLeft, 4.0), 2.0, 2.0);

		const auto fraction = std::clamp((_value - _minVal) / (_maxVal - _minVal), 0.0f, 1.0f);
		const auto thumbX = trackLeft + fraction * (trackRight - trackLeft);

		p.setBrush((_hovered || _dragging) ? QColor(90, 155, 255) : QColor(72, 134, 232));
		p.drawRoundedRect(QRectF(trackLeft, trackY, thumbX - trackLeft, 4.0), 2.0, 2.0);

		const auto radius = _dragging ? 6.5 : (_hovered ? 6.0 : 5.0);
		if (_hovered || _dragging) {
			p.setPen(Qt::NoPen);
			p.setBrush(QColor(90, 155, 255, 60));
			p.drawEllipse(QPointF(thumbX, height() / 2.0), radius + 3.0, radius + 3.0);
		}
		p.setPen(QPen(QColor(0, 0, 0, 45), 1.0));
		p.setBrush(QColor(255, 255, 255));
		p.drawEllipse(QPointF(thumbX, height() / 2.0), radius, radius);

		const auto pct = QString::number(int(std::round(_value * 100))) + u"%"_q;
		QFont font = st::normalFont;
		font.setPointSize(std::max(8, font.pointSize() - 2));
		font.setWeight(QFont::DemiBold);
		p.setFont(font);
		p.setPen((_hovered || _dragging) ? QColor(240, 245, 255) : QColor(160, 165, 175));
		p.drawText(QRect(width() - 36, 0, 36, height()), Qt::AlignVCenter | Qt::AlignLeft, pct);
	}

	void mousePressEvent(QMouseEvent *e) override {
		if (e->button() == Qt::LeftButton) {
			_dragging = true;
			updateFromPos(e->pos().x());
			e->accept();
			return;
		}
		QWidget::mousePressEvent(e);
	}

	void mouseMoveEvent(QMouseEvent *e) override {
		if (_dragging) {
			updateFromPos(e->pos().x());
			e->accept();
			return;
		}
		QWidget::mouseMoveEvent(e);
	}

	void mouseReleaseEvent(QMouseEvent *e) override {
		if (e->button() == Qt::LeftButton && _dragging) {
			_dragging = false;
			update();
			e->accept();
			return;
		}
		QWidget::mouseReleaseEvent(e);
	}

#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
	void enterEvent(QEnterEvent *e) override {
		_hovered = true;
		update();
		QWidget::enterEvent(e);
	}
#else
	void enterEvent(QEvent *e) override {
		_hovered = true;
		update();
		QWidget::enterEvent(e);
	}
#endif

	void leaveEvent(QEvent *e) override {
		_hovered = false;
		update();
		QWidget::leaveEvent(e);
	}

	void wheelEvent(QWheelEvent *e) override {
		const auto delta = e->angleDelta().y();
		if (delta > 0) {
			setValue(_value + 0.05f);
		} else if (delta < 0) {
			setValue(_value - 0.05f);
		}
		if (_callback) {
			_callback(_value);
		}
		e->accept();
	}

private:
	void updateFromPos(int x) {
		const auto trackLeft = 24.0f;
		const auto trackRight = float(width() - 40);
		if (trackRight <= trackLeft) {
			return;
		}
		const auto fraction = std::clamp((float(x) - trackLeft) / (trackRight - trackLeft), 0.0f, 1.0f);
		const auto newVal = std::clamp(_minVal + fraction * (_maxVal - _minVal), _minVal, _maxVal);
		if (std::abs(newVal - _value) > 0.005f) {
			_value = newVal;
			update();
			if (_callback) {
				_callback(_value);
			}
		}
	}

	float _value = 0.92f;
	float _minVal = 0.25f;
	float _maxVal = 1.0f;
	bool _dragging = false;
	bool _hovered = false;
	Fn<void(float)> _callback;
};

FloatingOverlay::FloatingOverlay(not_null<Panel*> panel)
: QWidget(nullptr, Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint)
, _panel(panel) {
	setAttribute(Qt::WA_TranslucentBackground);
	setAttribute(Qt::WA_ShowWithoutActivating);

	const auto screen = QApplication::primaryScreen()->availableGeometry();
	setGeometry(screen.width() - 360, 100, 340, 480);

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
	_panel->overlayVisibilityChanged();
}

void FloatingOverlay::hide() {
	QWidget::hide();
	_panel->overlayVisibilityChanged();
}

void FloatingOverlay::closeEvent(QCloseEvent *event) {
	hide();
	event->ignore();
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
	const int y = 6;
	const int h = 26;

	QFont font = st::normalFont;
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
	if (_searchBtn) {
		_searchBtn->setActive(_searchOpen);
	}
	if (_messagesUi) {
		_messagesUi->setVisible(!_searchOpen);
		if (!_searchOpen) {
			const auto footerH = 26;
			const auto bottom = height() - footerH;
			const auto h = bottom - 39;
			_messagesUi->move(4, bottom, width() - 8, h);
		}
	}
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
	int y = 46;
	const int rowHeight = 32;
	for (const auto &p : participants) {
		const auto peer = p.peer;
		const auto name = peer->name();
		if (!_searchQuery.isEmpty() && !name.contains(_searchQuery, Qt::CaseInsensitive)) {
			continue;
		}
		const auto rowRect = QRect(8, y, width() - 16, rowHeight);
		const auto openChatRect = QRect(width() - 160, y + 4, 45, 24);
		const auto pinScreenRect = QRect(width() - 110, y + 4, 40, 24);
		const auto addOverlayRect = QRect(width() - 65, y + 4, 55, 24);
		_searchResults.push_back({
			peer,
			name,
			rowRect,
			openChatRect,
			pinScreenRect,
			addOverlayRect,
		});
		y += rowHeight + 4;
		if (y > height() - 60) {
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
					const auto peer = res.peer;
					toggleSearch();
					addChat(peer);
					event->accept();
					return;
				}
			}
		}

		if (_tabs.size() > 1 && !_searchOpen && pos.y() <= 38) {
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

		if (pos.y() <= 38 || pos.y() >= height() - 26) {
			_dragging = true;
			_dragStart = event->globalPos();
			_startGeometry = geometry();
		}
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
			_opacity = std::max(0.25f, _opacity - 0.05f);
		}
		setWindowOpacity(_opacity);
		if (_opacitySlider) {
			_opacitySlider->setValue(_opacity);
		}
		update();
		event->accept();
		return;
	}
	QWidget::wheelEvent(event);
}

void FloatingOverlay::paintEvent(QPaintEvent *event) {
	auto p = QPainter(this);
	p.setRenderHint(QPainter::Antialiasing);

	const auto fullRect = rect();

	p.setPen(QColor(255, 255, 255, 30));
	p.setBrush(QColor(24, 26, 32, 245));
	p.drawRoundedRect(fullRect.adjusted(0, 0, -1, -1), 10, 10);

	QPainterPath headerPath;
	headerPath.moveTo(0, 38);
	headerPath.lineTo(0, 10);
	headerPath.arcTo(0, 0, 20, 20, 180, -90);
	headerPath.lineTo(width() - 10, 0);
	headerPath.arcTo(width() - 20, 0, 20, 20, 90, -90);
	headerPath.lineTo(width(), 38);
	headerPath.closeSubpath();
	p.fillPath(headerPath, QColor(16, 18, 22, 230));

	p.setPen(QColor(255, 255, 255, 20));
	p.drawLine(0, 38, width(), 38);

	const auto footerH = 26;
	QPainterPath footerPath;
	footerPath.moveTo(0, height() - footerH);
	footerPath.lineTo(width(), height() - footerH);
	footerPath.lineTo(width(), height() - 10);
	footerPath.arcTo(width() - 20, height() - 20, 20, 20, 0, -90);
	footerPath.lineTo(10, height());
	footerPath.arcTo(0, height() - 20, 20, 20, 270, -90);
	footerPath.closeSubpath();
	p.fillPath(footerPath, QColor(16, 18, 22, 210));

	p.setPen(QColor(255, 255, 255, 18));
	p.drawLine(0, height() - footerH, width(), height() - footerH);

	QFont hintFont = st::normalFont;
	hintFont.setPointSize(std::max(8, hintFont.pointSize() - 2));
	p.setFont(hintFont);
	p.setPen(QColor(135, 140, 150, 190));
	p.drawText(QRect(185, height() - footerH, width() - 195, footerH), Qt::AlignVCenter | Qt::AlignRight,
		u"Ctrl+Shift+T hide"_q);

	if (_tabs.size() <= 1 && !_searchOpen) {
		p.setFont(st::semiboldFont);
		p.setPen(QColor(240, 240, 245));
		p.drawText(QRect(12, 5, width() - 115, 16), Qt::AlignVCenter | Qt::AlignLeft, u"Call Overlay"_q);

		QFont subFont = st::normalFont;
		subFont.setPointSize(std::max(8, subFont.pointSize() - 2));
		p.setFont(subFont);
		p.setPen(QColor(140, 145, 155));
		const auto subtitle = (_tabs.size() == 1 && _tabs[0].peer)
			? _tabs[0].name
			: u"Live Chat \u2022 Ctrl+Shift+T"_q;
		p.drawText(QRect(12, 21, width() - 115, 14), Qt::AlignVCenter | Qt::AlignLeft, subtitle);
	}

	if (_tabs.size() > 1 && !_searchOpen) {
		updateTabRects();
		QFont font = st::normalFont;
		p.setFont(font);
		for (int i = 0; i < _tabs.size(); ++i) {
			const auto &tab = _tabs[i];
			const auto &tr = _tabRects[i];
			const bool active = (i == _activeTabIndex);

			p.setPen(Qt::NoPen);
			if (active) {
				p.setBrush(QColor(60, 65, 80, 220));
			} else {
				p.setBrush(QColor(35, 38, 48, 160));
			}
			p.drawRoundedRect(tr.rect, 5, 5);

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

			p.setPen(active ? QColor(255, 255, 255) : QColor(190, 195, 205));
			const int textOffset = (hasUnread && !active) ? 14 : 8;
			p.drawText(tr.rect.adjusted(textOffset, 0, 0, 0), Qt::AlignVCenter | Qt::AlignLeft, tab.name);

			if (i > 0) {
				p.setPen(QColor(255, 255, 255, 120));
				p.drawText(tr.closeRect, Qt::AlignCenter, u"\u00d7"_q);
			}
		}
	}

	if (_searchOpen) {
		p.fillRect(QRect(0, 38, width(), height() - 38 - 26), QColor(20, 22, 28, 250));

		p.setFont(st::semiboldFont);
		p.setPen(QColor(255, 255, 255));
		const auto prompt = _searchQuery.isEmpty()
			? u"Search Callers (type to filter)..."_q
			: (u"Search Callers: "_q + _searchQuery + u"|"_q);
		p.drawText(QRect(12, 6, width() - 110, 26), Qt::AlignVCenter | Qt::AlignLeft, prompt);

		for (const auto &res : _searchResults) {
			p.setPen(Qt::NoPen);
			p.setBrush(QColor(35, 38, 48, 180));
			p.drawRoundedRect(res.rowRect, 6, 6);

			p.setPen(QColor(240, 240, 245));
			p.setFont(st::semiboldFont);
			p.drawText(res.rowRect.adjusted(10, 0, -170, 0), Qt::AlignVCenter | Qt::AlignLeft, res.name);

			p.setFont(st::normalFont);
			p.setBrush(QColor(50, 90, 150, 220));
			p.drawRoundedRect(res.openChatRect, 4, 4);
			p.setPen(QColor(210, 235, 255));
			p.drawText(res.openChatRect, Qt::AlignCenter, u"Chat"_q);

			p.setBrush(QColor(45, 115, 75, 220));
			p.drawRoundedRect(res.pinScreenRect, 4, 4);
			p.setPen(QColor(210, 255, 230));
			p.drawText(res.pinScreenRect, Qt::AlignCenter, u"Pin"_q);

			p.setBrush(QColor(110, 65, 140, 220));
			p.drawRoundedRect(res.addOverlayRect, 4, 4);
			p.setPen(QColor(245, 220, 255));
			p.drawText(res.addOverlayRect, Qt::AlignCenter, u"+Tab"_q);
		}
	}

	QWidget::paintEvent(event);
}

void FloatingOverlay::resizeEvent(QResizeEvent *event) {
	QWidget::resizeEvent(event);
	const auto footerH = 26;
	if (!_searchOpen && _messagesUi) {
		const auto bottom = height() - footerH;
		const auto h = bottom - 39;
		_messagesUi->move(4, bottom, width() - 8, h);
	}
	if (_opacitySlider) {
		_opacitySlider->setGeometry(10, height() - footerH + 2, 175, 22);
	}
	if (_closeBtn) {
		_closeBtn->move(width() - 34, 5);
	}
	if (_passthroughBtn) {
		_passthroughBtn->move(width() - 66, 5);
	}
	if (_searchBtn) {
		_searchBtn->move(width() - 98, 5);
	}
}

void FloatingOverlay::setupUI() {
	_closeBtn.create(this, HeaderButton::Type::Close);
	_closeBtn->move(width() - 34, 5);
	_closeBtn->setToolTip(u"Close overlay (Esc / Ctrl+Shift+T)"_q);
	_closeBtn->setClickedCallback([=] { hide(); });

	_passthroughBtn.create(this, HeaderButton::Type::Passthrough);
	_passthroughBtn->move(width() - 66, 5);
	_passthroughBtn->setToolTip(u"Toggle click-through mode"_q);
	_passthroughBtn->setClickedCallback([=] { togglePassthrough(); });

	_searchBtn.create(this, HeaderButton::Type::Search);
	_searchBtn->move(width() - 98, 5);
	_searchBtn->setToolTip(u"Search call participants (Ctrl+F)"_q);
	_searchBtn->setClickedCallback([=] { toggleSearch(); });

	_opacitySlider.create(this);
	_opacitySlider->setValue(_opacity);
	_opacitySlider->setGeometry(10, height() - 24, 175, 22);
	_opacitySlider->show();
	_opacitySlider->setChangedCallback([=](float val) {
		_opacity = val;
		setWindowOpacity(_opacity);
	});

	setupChatContent();
}

void FloatingOverlay::setupChatContent() {
	_messagesUi = nullptr;
	_tabLifetime.destroy();

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
		const auto peer = not_null{ tab.peer };
		auto getMessages = [=] {
			std::vector<Message> result;
			const auto history = peer->owner().historyLoaded(peer)
				? peer->owner().history(peer).get()
				: nullptr;
			if (!history) {
				return result;
			}
			for (const auto &block : history->blocks) {
				for (const auto &item : block->messages) {
					const auto data = item->data();
					if (!data || data->emptyText()) continue;
					auto from = peer;
					if (const auto fromPeer = data->from()) {
						from = fromPeer;
					} else if (const auto h = data->history()) {
						from = h->peer;
					}
					result.push_back({
						data->id,
						data->date(),
						0,
						from,
						data->originalText(),
						0,
						false,
						false,
						data->out()
					});
				}
			}
			if (result.size() > 50) {
				result.erase(result.begin(), result.end() - 50);
			}
			return result;
		};

		auto messagesStream = std::make_shared<rpl::event_stream<std::vector<Message>>>();

		peer->session().data().newItemAdded(
		) | rpl::on_next([=](not_null<HistoryItem*> item) {
			if (item->history()->peer == peer) {
				messagesStream->fire(getMessages());
			}
		}, _tabLifetime);

		_messagesUi = std::make_unique<MessagesUi>(
			this,
			_panel->uiShow(),
			MessagesMode::GroupCall,
			messagesStream->events_starting_with(getMessages()),
			nullptr,
			rpl::never<MessageIdUpdate>(),
			rpl::single(false),
			rpl::single(true),
			[=](QPoint) { return false; });
	}

	if (_messagesUi) {
		const auto footerH = 26;
		const auto bottom = height() - footerH;
		const auto h = bottom - 39;
		_messagesUi->move(4, bottom, width() - 8, h);
		_messagesUi->setVisible(!_searchOpen);
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
	if (_passthroughBtn) {
		_passthroughBtn->setActive(_passthrough);
		_passthroughBtn->setToolTip(_passthrough
			? u"Click-through enabled"_q
			: u"Toggle click-through mode"_q);
	}
	update();
}

} // namespace Calls::Group
