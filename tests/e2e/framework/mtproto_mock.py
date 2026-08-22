"""
MTProto Mock & Protocol Simulation Engine for Telegram Desktop E2E tests.
"""

from typing import Dict, List, Any, Optional, Tuple


class MtprotoSession:
    """Represents an individual MTProto download connection/session."""

    def __init__(self, session_id: int):
        self.session_id = session_id
        self.requested_bytes = 0
        self.successes = 0
        self.max_waited_amount = 8 * 128 * 1024  # 8 * 128KB


class DcSessionPool:
    """Manages parallel download sessions for a specific Data Center (DC)."""

    def __init__(self, dc_id: int, start_sessions: int = 4, max_sessions: int = 16):
        self.dc_id = dc_id
        self.start_sessions = start_sessions
        self.max_sessions = max_sessions
        self.sessions: List[MtprotoSession] = [
            MtprotoSession(i) for i in range(start_sessions)
        ]
        self.timeouts = 0
        self.session_remove_times = 0

    def choose_session_index(self) -> int:
        """Selects the session index with the minimal pending requested bytes."""
        min_idx = 0
        min_load = self.sessions[0].requested_bytes
        for i, s in enumerate(self.sessions):
            if s.requested_bytes < min_load:
                min_load = s.requested_bytes
                min_idx = i
        return min_idx

    def request_succeeded(self, session_idx: int, bytes_count: int) -> None:
        """Marks a successful chunk download, potentially expanding the session pool up to max."""
        if 0 <= session_idx < len(self.sessions):
            self.sessions[session_idx].requested_bytes = max(
                0, self.sessions[session_idx].requested_bytes - bytes_count
            )
            self.sessions[session_idx].successes += 1

        # Check if we should scale session pool up to 16
        if len(self.sessions) < self.max_sessions:
            total_successes = sum(s.successes for s in self.sessions)
            if total_successes % 2 == 0:  # Expand on every 2 successes
                new_id = len(self.sessions)
                self.sessions.append(MtprotoSession(new_id))

    def request_failed_timeout(self, session_idx: int) -> None:
        """Handles timeout error, incrementing failure counter and shrinking excess sessions if needed."""
        self.timeouts += 1
        if self.timeouts >= 3 and len(self.sessions) > self.start_sessions:
            self.sessions.pop()
            self.session_remove_times += 1
            self.timeouts = 0


class MtprotoMock:
    """Central MTProto session manager and RPC interceptor."""

    def __init__(self):
        self.dispatched_rpcs: List[Dict[str, Any]] = []
        self.dc_pools: Dict[int, DcSessionPool] = {}
        self.ghost_mode: bool = False
        self.local_unread_counts: Dict[int, int] = {}
        self.server_inbox_pointers: Dict[int, int] = {}

    def set_ghost_mode(self, enabled: bool) -> None:
        self.ghost_mode = enabled

    def get_dc_pool(self, dc_id: int) -> DcSessionPool:
        if dc_id not in self.dc_pools:
            self.dc_pools[dc_id] = DcSessionPool(dc_id)
        return self.dc_pools[dc_id]

    def send_read_request(
        self, peer_id: int, max_id: int, is_channel: bool = False
    ) -> bool:
        """Simulates Histories::sendReadRequest."""
        # Under Ghost Mode, read requests are suppressed
        if self.ghost_mode:
            # Local unread count may be cleared for display, but server is never notified
            self.local_unread_counts[peer_id] = 0
            return False

        rpc_name = "channels.readHistory" if is_channel else "messages.readHistory"
        self.dispatched_rpcs.append(
            {
                "rpc": rpc_name,
                "peer_id": peer_id,
                "max_id": max_id,
            }
        )
        self.local_unread_counts[peer_id] = 0
        self.server_inbox_pointers[peer_id] = max_id
        return True

    def dispatch_rpc(self, rpc_name: str, **kwargs: Any) -> Dict[str, Any]:
        record = {"rpc": rpc_name, **kwargs}
        self.dispatched_rpcs.append(record)
        return record

    def get_dispatched_rpcs(self, rpc_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if rpc_name is None:
            return list(self.dispatched_rpcs)
        return [r for r in self.dispatched_rpcs if r.get("rpc") == rpc_name]

    def clear_rpc_log(self) -> None:
        self.dispatched_rpcs.clear()
