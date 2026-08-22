"""
Rich assertion helpers and geometric validators for Telegram Desktop E2E test suite.
"""

from typing import List, Tuple, Dict, Any, Optional


class GeometryRect:
    """Represents a 2D bounding box (x, y, width, height) matching QRect behavior."""

    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def is_empty(self) -> bool:
        return self.width <= 0 or self.height <= 0

    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0

    def intersects(self, other: "GeometryRect") -> bool:
        if self.is_empty() or other.is_empty():
            return False
        return not (
            self.right <= other.left
            or other.right <= self.left
            or self.bottom <= other.top
            or other.bottom <= self.top
        )

    def intersection(self, other: "GeometryRect") -> "GeometryRect":
        if not self.intersects(other):
            return GeometryRect(0, 0, 0, 0)
        nx = max(self.x, other.x)
        ny = max(self.y, other.y)
        nw = min(self.right, other.right) - nx
        nh = min(self.bottom, other.bottom) - ny
        return GeometryRect(nx, ny, max(0, nw), max(0, nh))

    def contains(self, other: "GeometryRect") -> bool:
        if other.is_empty():
            return True
        return (
            other.left >= self.left
            and other.right <= self.right
            and other.top >= self.top
            and other.bottom <= self.bottom
        )

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, GeometryRect):
            return self.to_tuple() == other.to_tuple()
        if isinstance(other, (tuple, list)) and len(other) == 4:
            return self.to_tuple() == tuple(other)
        return False

    def __repr__(self) -> str:
        return f"QRect({self.x}, {self.y}, {self.width}, {self.height})"


def assert_rect_equal(
    actual: Any, expected: Any, msg: Optional[str] = None
) -> None:
    """Asserts that two rectangles match in coordinates and dimensions."""
    r_act = actual if isinstance(actual, GeometryRect) else GeometryRect(*actual)
    r_exp = (
        expected
        if isinstance(expected, GeometryRect)
        else GeometryRect(*expected)
    )

    err = f"Rectangle mismatch: actual {r_act} != expected {r_exp}"
    if msg:
        err = f"{msg} -> {err}"
    assert r_act == r_exp, err


def assert_no_overlap(
    rects: List[GeometryRect], msg: Optional[str] = None
) -> None:
    """Asserts that no two valid rectangles in the list overlap with each other."""
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            r1 = rects[i]
            r2 = rects[j]
            if r1.is_valid() and r2.is_valid():
                inter = r1.intersection(r2)
                err = f"Overlap detected between rect[{i}] {r1} and rect[{j}] {r2}: intersection={inter}"
                if msg:
                    err = f"{msg} -> {err}"
                assert not r1.intersects(r2), err


def assert_bounded_within(
    rect: GeometryRect,
    outer_width: int,
    outer_height: int,
    msg: Optional[str] = None,
) -> None:
    """Asserts that the rectangle fits entirely inside [0, outer_width] x [0, outer_height]."""
    outer = GeometryRect(0, 0, outer_width, outer_height)
    err = f"Rectangle {rect} is not fully contained within bounding viewport (0, 0, {outer_width}, {outer_height})"
    if msg:
        err = f"{msg} -> {err}"
    assert outer.contains(rect), err


def assert_opacity_clamped(
    opacity: float,
    min_opacity: float = 0.20,
    max_opacity: float = 1.00,
    msg: Optional[str] = None,
) -> None:
    """Asserts that an opacity float is within the valid clamp bounds [min_opacity, max_opacity]."""
    err = f"Opacity {opacity} is outside clamped interval [{min_opacity}, {max_opacity}]"
    if msg:
        err = f"{msg} -> {err}"
    assert min_opacity - 1e-5 <= opacity <= max_opacity + 1e-5, err


def assert_rpc_dispatched(
    mock_engine: Any,
    rpc_name: str,
    expected_count: Optional[int] = None,
    msg: Optional[str] = None,
) -> None:
    """Asserts that a specified RPC was sent by the client."""
    calls = mock_engine.get_dispatched_rpcs(rpc_name)
    actual_count = len(calls)
    if expected_count is not None:
        err = f"Expected {expected_count} calls to RPC '{rpc_name}', but found {actual_count}."
        if msg:
            err = f"{msg} -> {err}"
        assert actual_count == expected_count, err
    else:
        err = f"Expected at least 1 call to RPC '{rpc_name}', but found 0."
        if msg:
            err = f"{msg} -> {err}"
        assert actual_count > 0, err


def assert_rpc_suppressed(
    mock_engine: Any, rpc_name: str, msg: Optional[str] = None
) -> None:
    """Asserts that no calls to the specified RPC were dispatched."""
    calls = mock_engine.get_dispatched_rpcs(rpc_name)
    actual_count = len(calls)
    err = f"Expected RPC '{rpc_name}' to be suppressed (0 calls), but found {actual_count} calls: {calls}."
    if msg:
        err = f"{msg} -> {err}"
    assert actual_count == 0, err


def assert_zero_audio_packets(
    call_engine: Any, msg: Optional[str] = None
) -> None:
    """Asserts that zero outgoing microphone audio packets were emitted."""
    packets = call_engine.get_outgoing_audio_packets_count()
    err = f"Listen-only invariant violated: outgoing audio packet count is {packets} (expected 0)."
    if msg:
        err = f"{msg} -> {err}"
    assert packets == 0, err


def assert_pragma_executed(
    storage_mock: Any,
    pragma_key: str,
    expected_value: Any,
    msg: Optional[str] = None,
) -> None:
    """Asserts that a SQLite PRAGMA was configured with the expected value."""
    actual_value = storage_mock.get_pragma(pragma_key)
    err = f"SQLite PRAGMA '{pragma_key}' mismatch: actual '{actual_value}' != expected '{expected_value}'"
    if msg:
        err = f"{msg} -> {err}"
    assert (
        str(actual_value).upper() == str(expected_value).upper()
        or actual_value == expected_value
    ), err
