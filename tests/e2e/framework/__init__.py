"""
Telegram Desktop Fork E2E Test Framework.
"""

from .assertions import (
    GeometryRect,
    assert_rect_equal,
    assert_no_overlap,
    assert_bounded_within,
    assert_opacity_clamped,
    assert_rpc_dispatched,
    assert_rpc_suppressed,
    assert_zero_audio_packets,
    assert_pragma_executed,
)
from .grid_solver_oracle import GridSolverOracle, PinSlotAllocator
from .mtproto_mock import MtprotoMock, DcSessionPool, MtprotoSession
from .storage_mock import SQLiteStorageMock, TdataStreamMock, CoreSettingsMock
from .call_simulator import CallSimulator, VideoEndpoint
from .ui_simulator import (
    FloatingOverlaySimulator,
    MenuControllerSimulator,
    CallWindowControlsSimulator,
)
from .display_mock import DisplayCoordinatorMock, VirtualScreen
from .audio_jitter_oracle import WebRtcAudioJitterOracle
from .rich_tasks_oracle import RichTasksOracle, ChecklistItem

__all__ = [
    "GeometryRect",
    "assert_rect_equal",
    "assert_no_overlap",
    "assert_bounded_within",
    "assert_opacity_clamped",
    "assert_rpc_dispatched",
    "assert_rpc_suppressed",
    "assert_zero_audio_packets",
    "assert_pragma_executed",
    "GridSolverOracle",
    "PinSlotAllocator",
    "MtprotoMock",
    "DcSessionPool",
    "MtprotoSession",
    "SQLiteStorageMock",
    "TdataStreamMock",
    "CoreSettingsMock",
    "CallSimulator",
    "VideoEndpoint",
    "FloatingOverlaySimulator",
    "MenuControllerSimulator",
    "CallWindowControlsSimulator",
    "DisplayCoordinatorMock",
    "VirtualScreen",
    "WebRtcAudioJitterOracle",
    "RichTasksOracle",
    "ChecklistItem",
]
