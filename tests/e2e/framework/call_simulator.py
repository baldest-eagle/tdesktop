"""
WebRTC Group Call Simulator, Central Call & State Controller, and Audio Lockout Engine.
"""

from typing import List, Dict, Any, Optional, Set
import time


class VideoEndpoint:
    """Represents a video/audio stream endpoint in a group call."""

    def __init__(
        self,
        endpoint_id: str,
        peer_id: int,
        name: str,
        entry_time: float = 0.0,
        has_video: bool = True,
        native_width: int = 1280,
        native_height: int = 720,
    ):
        self.endpoint_id = endpoint_id
        self.peer_id = peer_id
        self.name = name
        self.entry_time = entry_time if entry_time > 0.0 else time.time()
        self.has_video = has_video
        self.native_width = native_width
        self.native_height = native_height
        self.simulcast_spatial_layer = 0  # 0: Low, 1: Medium, 2: High (1080p)
        self.is_speaking = False
        self.audio_level = 0.0


class CallSimulator:
    """Central call controller managing WebRTC sessions, participants, audio lockout, and video routing."""

    def __init__(self, is_listen_only: bool = False):
        self.is_listen_only: bool = is_listen_only
        self.endpoints: Dict[str, VideoEndpoint] = {}
        self.outgoing_audio_packets: int = 0
        self.mic_muted: bool = True
        self.mic_button_visible: bool = not is_listen_only
        self.active_speaker_id: Optional[str] = None
        self._last_speaker_switch_time: float = 0.0
        self.hysteresis_threshold: float = 0.30  # 300ms damping
        self.stage_screen_id: Optional[int] = None
        self.secondary_display_pinned_id: Optional[str] = None
        self.secondary_display_active_speaker_disabled: bool = True

    def add_participant(
        self,
        endpoint_id: str,
        peer_id: int,
        name: str,
        entry_time: float = 0.0,
        has_video: bool = True,
        native_width: int = 1280,
        native_height: int = 720,
    ) -> VideoEndpoint:
        ep = VideoEndpoint(
            endpoint_id, peer_id, name, entry_time, has_video, native_width, native_height
        )
        self.endpoints[endpoint_id] = ep
        return ep

    def remove_participant(self, endpoint_id: str) -> None:
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
        if self.active_speaker_id == endpoint_id:
            self.active_speaker_id = None
        if self.secondary_display_pinned_id == endpoint_id:
            self.secondary_display_pinned_id = None

    def get_participants_chronological(self) -> List[VideoEndpoint]:
        """Sorts participants by entry time for main grid rendering."""
        return sorted(self.endpoints.values(), key=lambda ep: ep.entry_time)

    def get_participants_alphabetical(self) -> List[VideoEndpoint]:
        """Sorts participants alphabetically by display name for sidebar."""
        return sorted(self.endpoints.values(), key=lambda ep: ep.name.lower())

    def filter_participants(self, query: str) -> List[VideoEndpoint]:
        """Filters sidebar participants by search query string."""
        q = query.strip().lower()
        if not q:
            return self.get_participants_alphabetical()
        return [
            ep
            for ep in self.get_participants_alphabetical()
            if q in ep.name.lower() or q in str(ep.peer_id)
        ]

    def set_listen_only(self, enabled: bool) -> None:
        """Enforces audio lockout / listen-only invariant."""
        self.is_listen_only = enabled
        if enabled:
            self.mic_button_visible = False
            self.mic_muted = True
            # Zero out any pending packets
            self.outgoing_audio_packets = 0
        else:
            self.mic_button_visible = True

    def emit_microphone_packet(self, data: bytes) -> bool:
        """Attempts to transmit audio packet from local mic."""
        if self.is_listen_only:
            # Drop packet immediately, zero mic enforcement
            return False
        if not self.mic_muted:
            self.outgoing_audio_packets += 1
            return True
        return False

    def get_outgoing_audio_packets_count(self) -> int:
        return self.outgoing_audio_packets

    def generate_sdp(self) -> str:
        """Generates WebRTC SDP offer/answer reflecting listen-only mode."""
        if self.is_listen_only:
            return "v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=recvonly\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=recvonly\r\n"
        return "v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=sendrecv\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=sendrecv\r\n"

    def set_active_speaker(self, endpoint_id: str, now: float = 0.0) -> bool:
        """Sets active speaker applying hysteresis threshold to prevent rapid flapping."""
        if now == 0.0:
            now = time.time()

        if self.active_speaker_id == endpoint_id:
            return True

        if self.active_speaker_id is not None and (now - self._last_speaker_switch_time < self.hysteresis_threshold):
            # Suppress rapid flapping
            return False

        self.active_speaker_id = endpoint_id
        self._last_speaker_switch_time = now

        # Active speaker isolation check on secondary display
        if (
            self.secondary_display_pinned_id is None
            and not self.secondary_display_active_speaker_disabled
        ):
            self.secondary_display_pinned_id = endpoint_id

        return True

    def request_simulcast_upscale(self, endpoint_id: str, high_quality: bool) -> None:
        """Signals WebRTC SFU to upscale resolution for pinned endpoints."""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].simulcast_spatial_layer = 2 if high_quality else 0
