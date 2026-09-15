/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/calls_group_viewport.h"

#include "base/platform/base_platform_info.h"
#include "calls/group/calls_group_call.h"
#include "calls/group/calls_group_common.h"
#include "calls/group/calls_group_members_row.h"
#include "calls/group/calls_group_viewport_opengl.h"
#include "calls/group/calls_group_viewport_raster.h"
#if QT_VERSION >= QT_VERSION_CHECK(6, 7, 0)
#include "calls/group/calls_group_viewport_rhi.h"
#include "ui/rhi/rhi_renderer.h"
#endif
#include "calls/group/calls_group_viewport_tile.h"
#include "data/data_group_call.h"
#include "lang/lang_keys.h"
#include "media/view/media_view_pip.h"
#include "ui/effects/animations.h"
#include "ui/effects/cross_line.h"
#include "ui/gl/gl_surface.h"
#include "ui/abstract_button.h"
#include "ui/integration.h"
#include "ui/painter.h"
#include "webrtc/webrtc_video_track.h"

#include <QtGui/QtEvents>
#include <QOpenGLShader>
#include <QOpenGLWidget>

#include "styles/style_calls.h"

namespace Calls::Group {
namespace {

[[nodiscard]] QRect InterpolateRect(QRect a, QRect b, float64 ratio) {
	const auto left = anim::interpolate(a.x(), b.x(), ratio);
	const auto top = anim::interpolate(a.y(), b.y(), ratio);
	const auto right = anim::interpolate(
		a.x() + a.width(),
		b.x() + b.width(),
		ratio);
	const auto bottom = anim::interpolate(
		a.y() + a.height(),
		b.y() + b.height(),
		ratio);
	return { left, top, right - left, bottom - top };
}

} // namespace

Viewport::Viewport(
	not_null<QWidget*> parent,
	PanelMode mode,
	Ui::GL::Backend backend,
	Ui::RpWidgetWrap *borrowedRp,
	bool borrowedOpenGL)
: _mode(mode)
, _opengl(borrowedOpenGL)
, _qrhi(borrowedRp && (backend == Ui::GL::Backend::QRhi))
, _content(borrowedRp
	? nullptr
	: Ui::GL::CreateSurface(parent, chooseRenderer(backend)))
, _borrowed(borrowedRp) {
	setup();
}

Viewport::~Viewport() {
	if (_borrowed) {
		if (_opengl) {
			const auto w = static_cast<QOpenGLWidget*>(widget().get());
			w->makeCurrent();
			const auto context = w->context();
			const auto valid = w->isValid()
				&& context
				&& (QOpenGLContext::currentContext() == context);
			ensureBorrowedCleared(valid ? context->functions() : nullptr);
		} else {
			ensureBorrowedCleared();
		}
	}
	_content.release();
}

not_null<QWidget*> Viewport::widget() const {
	return _borrowed ? _borrowed->rpWidget() : _content->rpWidget();
}

not_null<Ui::RpWidgetWrap*> Viewport::rp() const {
	return _borrowed ? _borrowed : _content.get();
}

void Viewport::setup() {
	if (_borrowed) {
		return;
	}

	const auto raw = widget();

	raw->resize(0, 0);
	raw->setAttribute(Qt::WA_OpaquePaintEvent);
	raw->setMouseTracking(true);

	_content->sizeValue(
	) | rpl::filter([=] {
		return wide() || videoStream();
	}) | rpl::on_next([=] {
		updateTilesGeometry();
	}, lifetime());

	_content->events(
	) | rpl::on_next([=](not_null<QEvent*> e) {
		const auto type = e->type();
		if (type == QEvent::Enter) {
			Ui::Integration::Instance().registerLeaveSubscription(raw);
			_mouseInside = true;
		} else if (type == QEvent::Leave) {
			Ui::Integration::Instance().unregisterLeaveSubscription(raw);
			setSelected({});
			_mouseInside = false;
		} else if (type == QEvent::MouseButtonPress) {
			handleMousePress(
				static_cast<QMouseEvent*>(e.get())->pos(),
				static_cast<QMouseEvent*>(e.get())->button());
		} else if (type == QEvent::MouseButtonRelease) {
			handleMouseRelease(
				static_cast<QMouseEvent*>(e.get())->pos(),
				static_cast<QMouseEvent*>(e.get())->button());
		} else if (type == QEvent::MouseMove) {
			handleMouseMove(static_cast<QMouseEvent*>(e.get())->pos());
		} else if (type == QEvent::Wheel) {
			if (_gridPageCount.current() > 1) {
				const auto wheel = static_cast<QWheelEvent*>(e.get());
				const auto deltaY = wheel->angleDelta().y();
				const auto deltaX = wheel->angleDelta().x();
				const auto delta = (std::abs(deltaX) > std::abs(deltaY)) ? deltaX : deltaY;
				if (delta < 0 && _gridPage.current() + 1 < _gridPageCount.current()) {
					setGridPage(_gridPage.current() + 1);
				} else if (delta > 0 && _gridPage.current() > 0) {
					setGridPage(_gridPage.current() - 1);
				}
			}
		}
	}, lifetime());
}

void Viewport::setGeometry(bool fullscreen, QRect geometry) {
	Expects(wide() || videoStream());

	if (_borrowed) {
		updateMyWidgetPart();
		_borrowedGeometry = geometry;
		updateMyWidgetPart();
		updateTilesGeometry();
		return;
	}

	const auto changed = (_fullscreen != fullscreen);
	if (changed) {
		_fullscreen = fullscreen;
	}
	if (widget()->geometry() != geometry) {
		widget()->setGeometry(geometry);
	} else if (changed) {
		updateTilesGeometry();
	}
}

void Viewport::resizeToWidth(int width) {
	Expects(!wide() && !videoStream());

	updateTilesGeometry(width);
}

void Viewport::setScrollTop(int scrollTop) {
	if (_scrollTop == scrollTop) {
		return;
	}
	_scrollTop = scrollTop;
	updateTilesGeometry();
}

bool Viewport::wide() const {
	return (_mode == PanelMode::Wide) || (_mode == PanelMode::Grid);
}

bool Viewport::videoStream() const {
	return (_mode == PanelMode::VideoStream);
}

void Viewport::setMode(PanelMode mode, not_null<QWidget*> parent) {
	if (_mode == mode && widget()->parent() == parent) {
		return;
	}
	_mode = mode;
	_scrollTop = 0;
	setControlsShown(1.);
	if (widget()->parent() != parent) {
		const auto hidden = widget()->isHidden();
		widget()->setParent(parent);
		if (!hidden) {
			widget()->show();
		}
	}
	if (!wide() && !videoStream()) {
		for (const auto &tile : _tiles) {
			tile->toggleTopControlsShown(false);
		}
	} else if (_selected.tile) {
		_selected.tile->toggleTopControlsShown(true);
	}
}

void Viewport::handleMousePress(QPoint position, Qt::MouseButton button) {
	handleMouseMove(position);
	setPressed(_selected);
}

void Viewport::handleMouseRelease(QPoint position, Qt::MouseButton button) {
	handleMouseMove(position);
	const auto pressed = _pressed;
	setPressed({});
	if (const auto tile = pressed.tile) {
		if (pressed == _selected) {
			if (videoStream()) {
				return;
			} else if (button == Qt::RightButton) {
				if (const auto row = tile->row()) {
					row->showContextMenu();
				}
			} else if (pressed.element == Selection::Element::PinButton
				|| pressed.element == Selection::Element::BackButton) {
				_pinToggles.fire({ tile->endpoint(), true });
			} else if (!wide()
				|| (_hasTwoOrMore && !_large)) {
				_clicks.fire_copy(tile->endpoint());
			}
		}
	}
}

void Viewport::handleMouseMove(QPoint position) {
	updateSelected(position);
}

void Viewport::updateSelected(QPoint position) {
	if (_borrowed || !widget()->rect().contains(position)) {
		setSelected({});
		return;
	}
	for (const auto &tile : _tiles) {
		const auto geometry = tile->visible()
			? tile->geometry()
			: QRect();
		if (geometry.contains(position)) {
			const auto pin = wide()
				&& tile->pinOuter().contains(position - geometry.topLeft());
			const auto back = wide()
				&& tile->backOuter().contains(position - geometry.topLeft());
			setSelected({
				.tile = tile.get(),
				.element = (pin
					? Selection::Element::PinButton
					: back
					? Selection::Element::BackButton
					: Selection::Element::Tile),
			});
			return;
		}
	}
	setSelected({});
}

void Viewport::updateSelected() {
	if (_borrowed) {
		return;
	}
	updateSelected(widget()->mapFromGlobal(QCursor::pos()));
}

void Viewport::setControlsShown(float64 shown) {
	_controlsShownRatio = shown;
	updateMyWidgetPart();
}

void Viewport::updateMyWidgetPart() {
	if (!_borrowed) {
		widget()->update();
	} else if (!_borrowedGeometry.isEmpty()) {
		widget()->update(_borrowedGeometry);
	}
}

void Viewport::setCursorShown(bool shown) {
	if (_cursorHidden == shown) {
		_cursorHidden = !shown;
		updateCursor();
	}
}

void Viewport::add(
		const VideoEndpoint &endpoint,
		VideoTileTrack track,
		rpl::producer<QSize> trackSize,
		rpl::producer<bool> pinned,
		bool self) {
	_tiles.push_back(std::make_unique<VideoTile>(
		endpoint,
		track,
		std::move(trackSize),
		std::move(pinned),
		[=] { updateMyWidgetPart(); },
		self));

	_tiles.back()->trackSizeValue(
	) | rpl::filter([](QSize size) {
		return !size.isEmpty();
	}) | rpl::on_next([=] {
		updateTilesGeometry();
	}, _tiles.back()->lifetime());

	_tiles.back()->track()->stateValue(
	) | rpl::on_next([=] {
		updateTilesGeometry();
	}, _tiles.back()->lifetime());
	_tilesCountChanges.fire(static_cast<int>(_tiles.size()));
}

void Viewport::remove(const VideoEndpoint &endpoint) {
	const auto i = ranges::find(_tiles, endpoint, &VideoTile::endpoint);
	if (i == end(_tiles)) {
		return;
	}
	const auto removing = i->get();
	const auto largeRemoved = (_large == removing);
	if (largeRemoved) {
		prepareLargeChangeAnimation();
		_large = nullptr;
	}
	_pinnedEndpoints.erase(
		std::remove(_pinnedEndpoints.begin(), _pinnedEndpoints.end(), endpoint),
		_pinnedEndpoints.end());
	_pinnedSlots.erase(endpoint);

	if (_selected.tile == removing) {
		setSelected({});
	}
	if (_pressed.tile == removing) {
		setPressed({});
	}
	for (auto &geometry : _startTilesLayout.list) {
		if (geometry.tile == removing) {
			geometry.tile = nullptr;
		}
	}
	for (auto &geometry : _finishTilesLayout.list) {
		if (geometry.tile == removing) {
			geometry.tile = nullptr;
		}
	}
	_tiles.erase(i);
	if (largeRemoved) {
		startLargeChangeAnimation();
	} else {
		updateTilesGeometry();
	}
	_tilesCountChanges.fire(static_cast<int>(_tiles.size()));
}

void Viewport::prepareLargeChangeAnimation() {
	if (!wide()) {
		return;
	} else if (_largeChangeAnimation.animating()) {
		updateTilesAnimated();
		const auto field = _finishTilesLayout.useColumns
			? &Geometry::columns
			: &Geometry::rows;
		for (auto &finish : _finishTilesLayout.list) {
			const auto tile = finish.tile;
			if (!tile) {
				continue;
			}
			finish.*field = tile->geometry();
		}
		_startTilesLayout = std::move(_finishTilesLayout);
		_largeChangeAnimation.stop();

		_startTilesLayout.list.erase(
			ranges::remove(_startTilesLayout.list, nullptr, &Geometry::tile),
			end(_startTilesLayout.list));
	} else {
		_startTilesLayout = applyLarge(std::move(_startTilesLayout));
	}
}

void Viewport::startLargeChangeAnimation() {
	Expects(!_largeChangeAnimation.animating());

	if (_borrowed
		|| !wide()
		|| anim::Disabled()
		|| (_startTilesLayout.list.size() < 2)
		|| !_opengl
		|| widget()->size().isEmpty()) {
		updateTilesGeometry();
		return;
	}
	_finishTilesLayout = applyLarge(
		countWide(widget()->width(), widget()->height()));
	if (_finishTilesLayout.list.empty()
		|| _finishTilesLayout.outer != _startTilesLayout.outer) {
		updateTilesGeometry();
		return;
	}
	_largeChangeAnimation.start(
		[=] { updateTilesAnimated(); },
		0.,
		1.,
		st::slideDuration);
}

Viewport::Layout Viewport::applyLarge(Layout layout) const {
	auto &list = layout.list;
	if (!_large) {
		return layout;
	}
	const auto i = ranges::find(list, _large, &Geometry::tile);
	if (i == end(list)) {
		return layout;
	}
	const auto field = layout.useColumns
		? &Geometry::columns
		: &Geometry::rows;
	const auto fullWidth = layout.outer.width();
	const auto fullHeight = layout.outer.height();
	const auto largeRect = (*i).*field;
	const auto largeLeft = largeRect.x();
	const auto largeTop = largeRect.y();
	const auto largeRight = largeLeft + largeRect.width();
	const auto largeBottom = largeTop + largeRect.height();
	for (auto &geometry : list) {
		if (geometry.tile == _large) {
			geometry.*field = { QPoint(), layout.outer };
		} else if (layout.useColumns) {
			auto &rect = geometry.columns;
			const auto center = rect.center();
			if (center.x() < largeLeft) {
				rect = rect.translated(-largeLeft, 0);
			} else if (center.x() > largeRight) {
				rect = rect.translated(fullWidth - largeRight, 0);
			} else if (center.y() < largeTop) {
				rect = QRect(
					0,
					rect.y() - largeTop,
					fullWidth,
					rect.height());
			} else if (center.y() > largeBottom) {
				rect = QRect(
					0,
					rect.y() + (fullHeight - largeBottom),
					fullWidth,
					rect.height());
			}
		} else {
			auto &rect = geometry.rows;
			const auto center = rect.center();
			if (center.y() < largeTop) {
				rect = rect.translated(0, -largeTop);
			} else if (center.y() > largeBottom) {
				rect = rect.translated(0, fullHeight - largeBottom);
			} else if (center.x() < largeLeft) {
				rect = QRect(
					rect.x() - largeLeft,
					0,
					rect.width(),
					fullHeight);
			} else {
				rect = QRect(
					rect.x() + (fullWidth - largeRight),
					0,
					rect.width(),
					fullHeight);
			}
		}
	}
	return layout;
}

void Viewport::updateTilesAnimated() {
	if (_borrowed || !_largeChangeAnimation.animating()) {
		updateTilesGeometry();
		return;
	}
	const auto ratio = _largeChangeAnimation.value(1.);
	const auto field = _finishTilesLayout.useColumns
		? &Geometry::columns
		: &Geometry::rows;
	for (const auto &finish : _finishTilesLayout.list) {
		const auto tile = finish.tile;
		if (!tile) {
			continue;
		}
		const auto i = ranges::find(
			_startTilesLayout.list,
			tile,
			&Geometry::tile);
		if (i == end(_startTilesLayout.list)) {
			LOG(("Tiles Animation Error 1!"));
			_largeChangeAnimation.stop();
			updateTilesGeometry();
			return;
		}
		const auto from = (*i).*field;
		const auto to = finish.*field;
		tile->setGeometry(
			InterpolateRect(from, to, ratio),
			TileAnimation{ from.size(), to.size(), ratio });
	}
	widget()->update();
}

Viewport::Layout Viewport::countWide(int outerWidth, int outerHeight) const {
	auto result = Layout{ .outer = QSize(outerWidth, outerHeight) };
	auto &sizes = result.list;
	sizes.reserve(_tiles.size());

	std::vector<not_null<VideoTile*>> inactiveTiles;
	if (!_pinnedEndpoints.empty()) {
		for (const auto &pinned : _pinnedEndpoints) {
			for (const auto &tile : _tiles) {
				if (tile->endpoint() == pinned) {
					const auto video = tile.get();
					const auto size = video->trackOrUserpicSize();
					if (!size.isEmpty()) {
						sizes.push_back(Geometry{ video, size });
					}
					break;
				}
			}
		}
		const_cast<Viewport*>(this)->_gridPageCount = 1;
		const_cast<Viewport*>(this)->_gridPage = 0;
	} else {
		auto unpinnedTiles = std::vector<not_null<VideoTile*>>();
		for (const auto &tile : _tiles) {
			const auto video = tile.get();
			const auto size = video->trackOrUserpicSize();
			if (!size.isEmpty()) {
				unpinnedTiles.push_back(video);
			}
		}
		std::sort(unpinnedTiles.begin(), unpinnedTiles.end(), [](not_null<VideoTile*> a, not_null<VideoTile*> b) {
			return a->entryTime() < b->entryTime();
		});

		const auto totalCount = int(unpinnedTiles.size());
		const auto pageCount = std::max(1, (totalCount + kMainGridPageSize - 1) / kMainGridPageSize);
		if (_gridPageCount.current() != pageCount) {
			const_cast<Viewport*>(this)->_gridPageCount = pageCount;
		}
		const auto currentPage = std::clamp(_gridPage.current(), 0, pageCount - 1);
		if (_gridPage.current() != currentPage) {
			const_cast<Viewport*>(this)->_gridPage = currentPage;
		}

		const auto startIndex = currentPage * kMainGridPageSize;
		const auto endIndex = std::min(totalCount, startIndex + kMainGridPageSize);

		for (auto i = startIndex; i < endIndex; ++i) {
			const auto video = unpinnedTiles[i];
			sizes.push_back(Geometry{ video.get(), video->trackOrUserpicSize() });
		}
		for (auto i = 0; i < startIndex; ++i) {
			inactiveTiles.push_back(unpinnedTiles[i]);
		}
		for (auto i = endIndex; i < totalCount; ++i) {
			inactiveTiles.push_back(unpinnedTiles[i]);
		}
	}

	const auto appendInactive = [&] {
		for (const auto video : inactiveTiles) {
			result.list.push_back(Geometry{
				.tile = video.get(),
				.size = video->trackOrUserpicSize(),
				.rows = QRect(),
				.columns = QRect(),
			});
		}
	};

	if (sizes.empty()) {
		appendInactive();
		return result;
	} else if (sizes.size() == 1) {
		sizes.front().rows = { 0, 0, outerWidth, outerHeight };
		sizes.front().columns = { 0, 0, outerWidth, outerHeight };
		appendInactive();
		return result;
	}

	auto columnsBlack = uint64();
	auto rowsBlack = uint64();
	const auto count = int(sizes.size());
	const auto skip = st::groupCallVideoLargeSkip;

	const auto slotConstraint = _slotCount.current();
	if (count == 2 && slotConstraint == 0) {
		const auto halfW = (outerWidth - skip) / 2;
		sizes[0].columns = sizes[0].rows = { 0, 0, halfW, outerHeight };
		sizes[1].columns = sizes[1].rows = {
			halfW + skip,
			0,
			outerWidth - halfW - skip,
			outerHeight,
		};
		result.useColumns = true;
		appendInactive();
		return result;
	}

	if (_pinnedEndpoints.empty()) {
		if (count == 3) {
			const auto cellW = (outerWidth - 2 * skip) / 3.0;
			for (auto i = 0; i < 3; ++i) {
				const auto left = int(base::SafeRound(i * (cellW + skip)));
				const auto right = int(base::SafeRound((i + 1) * cellW + i * skip));
				sizes[i].columns = sizes[i].rows = { left, 0, right - left, outerHeight };
			}
			result.useColumns = true;
			appendInactive();
			return result;
		} else if (count == 4) {
			const auto cellW = (outerWidth - skip) / 2.0;
			const auto cellH = (outerHeight - skip) / 2.0;
			for (auto i = 0; i < 4; ++i) {
				const auto c = i % 2;
				const auto r = i / 2;
				const auto left = int(base::SafeRound(c * (cellW + skip)));
				const auto top = int(base::SafeRound(r * (cellH + skip)));
				const auto right = int(base::SafeRound((c + 1) * cellW + c * skip));
				const auto bottom = int(base::SafeRound((r + 1) * cellH + r * skip));
				sizes[i].columns = sizes[i].rows = { left, top, right - left, bottom - top };
			}
			result.useColumns = true;
			appendInactive();
			return result;
		} else if (count == 5) {
			const auto cellW = (outerWidth - 2 * skip) / 3.0;
			const auto cellH = (outerHeight - skip) / 2.0;
			for (auto i = 0; i < 3; ++i) {
				const auto left = int(base::SafeRound(i * (cellW + skip)));
				const auto right = int(base::SafeRound((i + 1) * cellW + i * skip));
				const auto bottom = int(base::SafeRound(cellH));
				sizes[i].columns = sizes[i].rows = { left, 0, right - left, bottom };
			}
			const auto offsetX = int(base::SafeRound((outerWidth - (2 * cellW + skip)) / 2.0));
			const auto top = int(base::SafeRound(cellH + skip));
			const auto h = outerHeight - top;
			for (auto i = 0; i < 2; ++i) {
				const auto left = offsetX + int(base::SafeRound(i * (cellW + skip)));
				const auto right = offsetX + int(base::SafeRound((i + 1) * cellW + i * skip));
				sizes[3 + i].columns = sizes[3 + i].rows = { left, top, right - left, h };
			}
			result.useColumns = true;
			appendInactive();
			return result;
		} else if (count == 6) {
			const auto cellW = (outerWidth - 2 * skip) / 3.0;
			const auto cellH = (outerHeight - skip) / 2.0;
			for (auto i = 0; i < 6; ++i) {
				const auto c = i % 3;
				const auto r = i / 3;
				const auto left = int(base::SafeRound(c * (cellW + skip)));
				const auto top = int(base::SafeRound(r * (cellH + skip)));
				const auto right = int(base::SafeRound((c + 1) * cellW + c * skip));
				const auto bottom = int(base::SafeRound((r + 1) * cellH + r * skip));
				sizes[i].columns = sizes[i].rows = { left, top, right - left, bottom - top };
			}
			result.useColumns = true;
			appendInactive();
			return result;
		}
	}

	const auto fixedGridDim = (slotConstraint == 1)
		? 1
		: (slotConstraint == 4)
		? 2
		: (slotConstraint == 9)
		? 3
		: 0;

	if (fixedGridDim > 0) {
		const auto cols = fixedGridDim;
		const auto rows = fixedGridDim;
		const auto maxVisible = cols * rows;
		const auto visibleCount = std::min(count, maxVisible);
		const auto cellW = (outerWidth - (cols - 1) * skip) / float64(cols);
		const auto cellH = (outerHeight - (rows - 1) * skip) / float64(rows);

		for (auto i = 0; i != count; ++i) {
			auto &geometry = sizes[i];
			if (i < visibleCount) {
				const auto c = i % cols;
				const auto r = i / cols;
				const auto left = int(base::SafeRound(c * (cellW + skip)));
				const auto top = int(base::SafeRound(r * (cellH + skip)));
				const auto w = int(base::SafeRound((c + 1) * cellW + c * skip)) - left;
				const auto h = int(base::SafeRound((r + 1) * cellH + r * skip)) - top;
				geometry.columns = { left, top, w, h };
				geometry.rows = { left, top, w, h };
			} else {
				geometry.columns = QRect();
				geometry.rows = QRect();
			}
		}
		result.useColumns = true;
		appendInactive();
		return result;
	}

	const auto slices = int(std::ceil(std::sqrt(float64(count))));
	{
		auto index = 0;
		const auto columns = slices;
		const auto sizew = (outerWidth + skip) / float64(columns);
		for (auto column = 0; column != columns; ++column) {
			const auto left = int(base::SafeRound(column * sizew));
			const auto width = int(
				base::SafeRound(column * sizew + sizew - skip)) - left;
			const auto rows = int(base::SafeRound((count - index)
				/ float64(columns - column)));
			const auto sizeh = (outerHeight + skip) / float64(rows);
			for (auto row = 0; row != rows; ++row) {
				const auto top = int(base::SafeRound(row * sizeh));
				const auto height = int(base::SafeRound(
					row * sizeh + sizeh - skip)) - top;
				auto &geometry = sizes[index];
				geometry.columns = {
					left,
					top,
					width,
					height };
				const auto scaled = geometry.size.scaled(
					width,
					height,
					Qt::KeepAspectRatio);
				columnsBlack += (scaled.width() < width)
					? (width - scaled.width()) * height
					: (height - scaled.height()) * width;
				++index;
			}
		}
	}
	{
		auto index = 0;
		const auto rows = slices;
		const auto sizeh = (outerHeight + skip) / float64(rows);
		for (auto row = 0; row != rows; ++row) {
			const auto top = int(base::SafeRound(row * sizeh));
			const auto height = int(
				base::SafeRound(row * sizeh + sizeh - skip)) - top;
			const auto columns = int(base::SafeRound((count - index)
				/ float64(rows - row)));
			const auto sizew = (outerWidth + skip) / float64(columns);
			for (auto column = 0; column != columns; ++column) {
				const auto left = int(base::SafeRound(column * sizew));
				const auto width = int(base::SafeRound(
					column * sizew + sizew - skip)) - left;
				auto &geometry = sizes[index];
				geometry.rows = {
					left,
					top,
					width,
					height };
				const auto scaled = geometry.size.scaled(
					width,
					height,
					Qt::KeepAspectRatio);
				rowsBlack += (scaled.width() < width)
					? (width - scaled.width()) * height
					: (height - scaled.height()) * width;
				++index;
			}
		}
	}
	result.useColumns = (columnsBlack < rowsBlack);
	for (const auto video : inactiveTiles) {
		result.list.push_back(Geometry{
			.tile = video.get(),
			.size = video->trackOrUserpicSize(),
			.rows = QRect(),
			.columns = QRect(),
		});
	}
	return result;
}

void Viewport::showLarge(const VideoEndpoint &endpoint) {
	if (_borrowed) {
		return;
	}
	if (!_pinnedEndpoints.empty()) {
		if (!endpoint || !isPinned(endpoint)) {
			return;
		}
	}

	// If a video gets switched off, GroupCall first unpins it,
	// then removes it from Large endpoint, then removes from active tracks.
	//
	// If we want to animate large video removal properly, we need to
	// delay this update and start animation directly from removing of the
	// track from the active list. Otherwise final state won't be correct.
	_updateLargeScheduled = [=] {
		const auto i = ranges::find(_tiles, endpoint, &VideoTile::endpoint);
		const auto large = (i != end(_tiles)) ? i->get() : nullptr;
		if (_large != large) {
			prepareLargeChangeAnimation();
			_large = large;
			updateTopControlsVisibility();
			startLargeChangeAnimation();
		}

		Ensures(!_large || !_large->trackOrUserpicSize().isEmpty());
	};
	crl::on_main(widget(), [=] {
		if (!_updateLargeScheduled) {
			return;
		}
		base::take(_updateLargeScheduled)();
	});
}

void Viewport::updateTilesGeometry() {
	updateTilesGeometry(_borrowed
		? _borrowedGeometry.width()
		: widget()->width());
}

void Viewport::updateTilesGeometry(int outerWidth) {
	const auto mouseInside = _mouseInside.current();
	const auto guard = gsl::finally([&] {
		if (mouseInside) {
			updateSelected();
		}
		updateMyWidgetPart();
	});

	const auto outerHeight = _borrowed
		? _borrowedGeometry.height()
		: widget()->height();
	if (_tiles.empty() || !outerWidth) {
		_fullHeight = 0;
		return;
	}

	if (wide() || videoStream()) {
		updateTilesGeometryWide(outerWidth, outerHeight);
		refreshHasTwoOrMore();
		_fullHeight = 0;
	} else {
		updateTilesGeometryNarrow(outerWidth);
	}
}

void Viewport::refreshHasTwoOrMore() {
	auto hasTwoOrMore = false;
	auto oneFound = false;
	for (const auto &tile : _tiles) {
		if (!tile->trackOrUserpicSize().isEmpty()) {
			if (oneFound) {
				hasTwoOrMore = true;
				break;
			}
			oneFound = true;
		}
	}
	if (_hasTwoOrMore == hasTwoOrMore) {
		return;
	}
	_hasTwoOrMore = hasTwoOrMore;
	updateCursor();
	updateTopControlsVisibility();
}

void Viewport::updateTopControlsVisibility() {
	if (_selected.tile) {
		const auto inGrid = _gridMode.current();
		_selected.tile->toggleTopControlsShown(
			(_hasTwoOrMore && wide() && _large && _large == _selected.tile)
			|| inGrid);
	}
}

void Viewport::updateTilesGeometryWide(int outerWidth, int outerHeight) {
	if (!outerHeight) {
		return;
	} else if (_largeChangeAnimation.animating()) {
		if (_startTilesLayout.outer == QSize(outerWidth, outerHeight)) {
			return;
		}
		_largeChangeAnimation.stop();
	}

	_startTilesLayout = countWide(outerWidth, outerHeight);
	if (_large && !_large->trackOrUserpicSize().isEmpty()) {
		for (const auto &geometry : _startTilesLayout.list) {
			if (geometry.tile == _large) {
				setTileGeometry(_large, { 0, 0, outerWidth, outerHeight });
			} else {
				geometry.tile->hide();
			}
		}
	} else {
		const auto field = _startTilesLayout.useColumns
			? &Geometry::columns
			: &Geometry::rows;
		for (const auto &geometry : _startTilesLayout.list) {
			if (const auto video = geometry.tile) {
				setTileGeometry(video, geometry.*field);
			}
		}
	}
}

void Viewport::updateTilesGeometryNarrow(int outerWidth) {
	if (outerWidth <= st::groupCallNarrowMembersWidth) {
		updateTilesGeometryColumn(outerWidth);
		return;
	}

	const auto y = -_scrollTop;
	auto sizes = base::flat_map<not_null<VideoTile*>, QSize>();
	sizes.reserve(_tiles.size());
	for (const auto &tile : _tiles) {
		const auto video = tile.get();
		const auto size = video->trackOrUserpicSize();
		if (size.isEmpty()) {
			video->hide();
		} else {
			sizes.emplace(video, size);
		}
	}
	if (sizes.empty()) {
		_fullHeight = 0;
		return;
	} else if (sizes.size() == 1) {
		const auto size = sizes.front().second;
		const auto heightMin = (outerWidth * 9) / 16;
		const auto heightMax = (outerWidth * 3) / 4;
		const auto scaled = size.scaled(
			QSize(outerWidth, heightMax),
			Qt::KeepAspectRatio);
		const auto height = std::max(scaled.height(), heightMin);
		const auto skip = st::groupCallVideoSmallSkip;
		setTileGeometry(sizes.front().first, { 0, y, outerWidth, height });
		_fullHeight = height + skip;
		return;
	}
	const auto min = (st::groupCallWidth
		- st::groupCallMembersMargin.left()
		- st::groupCallMembersMargin.right()
		- st::groupCallVideoSmallSkip) / 2;
	const auto square = (outerWidth - st::groupCallVideoSmallSkip) / 2;
	const auto skip = (outerWidth - 2 * square);
	const auto put = [&](not_null<VideoTile*> tile, int column, int row) {
		setTileGeometry(tile, {
			(column == 2) ? 0 : column ? (outerWidth - square) : 0,
			y + row * (min + skip),
			(column == 2) ? outerWidth : square,
			min,
		});
	};
	const auto rows = (sizes.size() + 1) / 2;
	if (sizes.size() == 3) {
		put(sizes.front().first, 2, 0);
		put((sizes.begin() + 1)->first, 0, 1);
		put((sizes.begin() + 2)->first, 1, 1);
	} else {
		auto row = 0;
		auto column = 0;
		for (const auto &[video, endpoint] : sizes) {
			put(video, column, row);
			if (column) {
				++row;
				column = (row + 1 == rows && sizes.size() % 2) ? 2 : 0;
			} else {
				column = 1;
			}
		}
	}
	_fullHeight = rows * (min + skip);
}

void Viewport::updateTilesGeometryColumn(int outerWidth) {
	const auto y = -_scrollTop;
	auto top = 0;
	const auto layoutNext = [&](not_null<VideoTile*> tile) {
		const auto size = tile->trackOrUserpicSize();
		const auto shown = !size.isEmpty() && _large && tile != _large;
		const auto height = st::groupCallNarrowVideoHeight;
		if (!shown) {
			tile->hide();
		} else {
			setTileGeometry(tile, { 0, y + top, outerWidth, height });
			top += height + st::groupCallVideoSmallSkip;
		}
	};
	const auto topPeer = _large ? _large->peer().get() : nullptr;
	const auto reorderNeeded = [&] {
		if (!topPeer) {
			return false;
		}
		for (const auto &tile : _tiles) {
			if (tile.get() != _large && tile->peer() == topPeer) {
				return (tile.get() != _tiles.front().get())
					&& !tile->trackOrUserpicSize().isEmpty();
			}
		}
		return false;
	}();
	if (reorderNeeded) {
		_tilesForOrder.clear();
		_tilesForOrder.reserve(_tiles.size());
		for (const auto &tile : _tiles) {
			_tilesForOrder.push_back(tile.get());
		}
		ranges::stable_partition(
			_tilesForOrder,
			[&](not_null<VideoTile*> tile) {
				return (tile->peer() == topPeer);
			});
		for (const auto &tile : _tilesForOrder) {
			layoutNext(tile);
		}
	} else {
		for (const auto &tile : _tiles) {
			layoutNext(tile.get());
		}
	}
	_fullHeight = top;
}

void Viewport::setTileGeometry(not_null<VideoTile*> tile, QRect geometry) {
	tile->setGeometry(geometry);

	const auto min = std::min(geometry.width(), geometry.height());
	const auto kMedium = style::ConvertScale(540);
	const auto kSmall = style::ConvertScale(240);
	const auto &endpoint = tile->endpoint();
	const auto forceThumbnailQuality = !wide()
		&& !videoStream()
		&& (ranges::count(_tiles, false, &VideoTile::hidden) > 1);
	const auto forceFullQuality = videoStream()
		|| (wide() && (tile.get() == _large));
	const auto quality = forceThumbnailQuality
		? VideoQuality::Thumbnail
		: (forceFullQuality || min >= kMedium)
		? VideoQuality::Full
		: (min >= kSmall)
		? VideoQuality::Medium
		: VideoQuality::Thumbnail;
	if (tile->updateRequestedQuality(quality)) {
		_qualityRequests.fire(VideoQualityRequest{
			.endpoint = endpoint,
			.quality = quality,
		});
	}
}

void Viewport::setSelected(Selection value) {
	if (_selected == value) {
		return;
	}
	if (_selected.tile) {
		_selected.tile->toggleTopControlsShown(false);
	}
	_selected = value;
	updateTopControlsVisibility();
	updateCursor();
}

void Viewport::updateCursor() {
	if (_borrowed) {
		return;
	}
	const auto pointer = _selected.tile && (!wide() || _hasTwoOrMore);
	widget()->setCursor(_cursorHidden
		? Qt::BlankCursor
		: pointer
		? style::cur_pointer
		: style::cur_default);
}

void Viewport::setPressed(Selection value) {
	if (_pressed == value) {
		return;
	}
	_pressed = value;
}

Ui::GL::ChosenRenderer Viewport::chooseRenderer(Ui::GL::Backend backend) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 7, 0)
	if (backend == Ui::GL::Backend::QRhi) {
		_opengl = true;
		_qrhi = true;
		return {
			.renderer = std::make_unique<RendererRhi>(this),
			.backend = Ui::GL::Backend::QRhi,
		};
	}
#else
	if (backend == Ui::GL::Backend::QRhi) {
		return {
			.renderer = std::make_unique<RendererSW>(this),
			.backend = Ui::GL::Backend::QRhi,
		};
	}
#endif
	_opengl = (backend == Ui::GL::Backend::OpenGL);
	return {
		.renderer = makeRenderer(),
		.backend = backend,
	};
}

std::unique_ptr<Ui::GL::Renderer> Viewport::makeRenderer() {
#if QT_VERSION >= QT_VERSION_CHECK(6, 7, 0)
	if (_qrhi) {
		return std::make_unique<RendererRhi>(this);
	}
#endif
	return _opengl
		? std::unique_ptr<Ui::GL::Renderer>(
			std::make_unique<RendererGL>(this))
		: std::make_unique<RendererSW>(this);
}

bool Viewport::requireARGB32() const {
	return !_opengl;
}

int Viewport::fullHeight() const {
	return _fullHeight.current();
}

rpl::producer<int> Viewport::fullHeightValue() const {
	return _fullHeight.value();
}

rpl::producer<Viewport::PinToggle> Viewport::pinToggled() const {
	return _pinToggles.events();
}

void Viewport::setGridMode(bool grid) {
	_gridMode = grid;
	updateTilesGeometry();
}

void Viewport::setSlotCount(int count) {
	_slotCount = count;
	updateTilesGeometry();
}

void Viewport::setGridPage(int page) {
	const auto clamped = std::clamp(page, 0, _gridPageCount.current() - 1);
	if (_gridPage.current() != clamped) {
		_gridPage = clamped;
		updateTilesGeometry();
	}
}

int Viewport::gridPage() const {
	return _gridPage.current();
}

int Viewport::gridPageCount() const {
	return _gridPageCount.current();
}

rpl::producer<int> Viewport::gridPageValue() const {
	return _gridPage.value();
}

rpl::producer<int> Viewport::gridPageCountValue() const {
	return _gridPageCount.value();
}

void Viewport::togglePin(const VideoEndpoint &endpoint, bool pinned) {
	const auto i = std::find(_pinnedEndpoints.begin(), _pinnedEndpoints.end(), endpoint);
	if (pinned && i == _pinnedEndpoints.end()) {
		_pinnedEndpoints.push_back(endpoint);
		_pinnedSlots[endpoint] = static_cast<int>(_pinnedEndpoints.size()) - 1;
		updateTilesGeometry();
	} else if (!pinned && i != _pinnedEndpoints.end()) {
		_pinnedEndpoints.erase(i);
		_pinnedSlots.erase(endpoint);
		updateTilesGeometry();
	}
}

bool Viewport::isPinned(const VideoEndpoint &endpoint) const {
	return ranges::contains(_pinnedEndpoints, endpoint);
}

const std::vector<VideoEndpoint> &Viewport::pinnedEndpoints() const {
	return _pinnedEndpoints;
}

int Viewport::tilesCount() const {
	return static_cast<int>(_tiles.size());
}

rpl::producer<int> Viewport::tilesCountChanges() const {
	return _tilesCountChanges.events();
}

rpl::variable<bool> Viewport::gridModeValue() const {
	return _gridMode;
}

rpl::producer<VideoEndpoint> Viewport::clicks() const {
	return _clicks.events();
}

rpl::producer<VideoQualityRequest> Viewport::qualityRequests() const {
	return _qualityRequests.events();
}

rpl::producer<bool> Viewport::mouseInsideValue() const {
	return _mouseInside.value();
}

void Viewport::ensureBorrowedRenderer(QOpenGLFunctions &f) {
	Expects(_borrowed != nullptr);
	Expects(_opengl);

	if (_borrowedRenderer) {
		return;
	}
	_borrowedRenderer = makeRenderer();
	_borrowedRenderer->init(f);
}

void Viewport::ensureBorrowedCleared(QOpenGLFunctions *f) {
	Expects(_borrowed != nullptr);
	Expects(_opengl);

	if (const auto renderer = base::take(_borrowedRenderer)) {
		renderer->deinit(f);
	}
}

void Viewport::borrowedPaint(QOpenGLFunctions &f) {
	Expects(_borrowedRenderer != nullptr);
	Expects(_opengl);

	_borrowedRenderer->paint(static_cast<QOpenGLWidget*>(widget().get()), f);
}

void Viewport::ensureBorrowedRenderer() {
	Expects(_borrowed != nullptr);
	Expects(!_opengl);

	if (_borrowedRenderer) {
		return;
	}
	_borrowedRenderer = makeRenderer();
}

void Viewport::ensureBorrowedCleared() {
	Expects(_borrowed != nullptr);
	Expects(!_opengl);

	base::take(_borrowedRenderer);
}

void Viewport::borrowedPaint(Painter &p, const QRegion &clip) {
	Expects(_borrowedRenderer != nullptr);
	Expects(!_opengl);

	_borrowedRenderer->paintFallback(p, clip, Ui::GL::Backend::Raster);
}

#if QT_VERSION >= QT_VERSION_CHECK(6, 7, 0)
Ui::Rhi::Renderer *Viewport::ensureBorrowedRhi(
		QRhi *rhi,
		QRhiRenderTarget *rt,
		QRhiCommandBuffer *cb) {
	Expects(_borrowed != nullptr);

	if (!_borrowedRenderer) {
		_borrowedRenderer = makeRenderer();
	}
	if (const auto r = dynamic_cast<Ui::Rhi::Renderer*>(
			_borrowedRenderer.get())) {
		r->initialize(rhi, rt, cb);
		return r;
	}
	return nullptr;
}

void Viewport::borrowedPaintOffscreen(
		QRhi *rhi,
		QRhiRenderTarget *rt,
		QRhiCommandBuffer *cb) {
	if (const auto r = ensureBorrowedRhi(rhi, rt, cb)) {
		r->renderOffscreen(rhi, rt, cb);
	}
}

void Viewport::borrowedPaintOnscreen(
		QRhi *rhi,
		QRhiRenderTarget *rt,
		QRhiCommandBuffer *cb) {
	if (const auto r = ensureBorrowedRhi(rhi, rt, cb)) {
		r->renderOnscreen(rhi, rt, cb);
	}
}
#endif

QPoint Viewport::borrowedOrigin() const {
	return _borrowed ? _borrowedGeometry.topLeft() : QPoint();
}

rpl::lifetime &Viewport::lifetime() {
	return _lifetime;
}

rpl::producer<QString> MuteButtonTooltip(not_null<GroupCall*> call) {
	if (call->rtmp()) {
		return nullptr;
	}
	return call->mutedValue(
	) | rpl::map([](MuteState muted) {
		switch (muted) {
		case MuteState::Active:
		case MuteState::PushToTalk:
			return tr::lng_group_call_you_are_live();
		case MuteState::ForceMuted:
			return tr::lng_group_call_tooltip_force_muted();
		case MuteState::RaisedHand:
			return tr::lng_group_call_tooltip_raised_hand();
		case MuteState::Muted:
			return tr::lng_group_call_tooltip_microphone();
		}
		Unexpected("Value in MuteState in showNiceTooltip.");
	}) | rpl::flatten_latest();
}

} // namespace Calls::Group
