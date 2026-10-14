"""
WebRTC Group Call Simulator, Central Call & State Controller, and Audio Lockout Engine.
"""

from typing import List, Dict, Any, Optional, Set
import time


QUALITY_THUMBNAIL = "Thumbnail"
QUALITY_MEDIUM = "Medium"
QUALITY_FULL = "Full"

_SPATIAL_LAYER = {
    QUALITY_THUMBNAIL: 0,
    QUALITY_MEDIUM: 1,
    QUALITY_FULL: 2,
}


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
        self.requested_quality = QUALITY_THUMBNAIL  # GroupCall::requestVideoQuality
        self.endpoint_type = "Camera"  # "Camera" or "Screen"
        self.is_speaking = False
        self.audio_level = 0.0


class CallSimulator:
    """Central call controller managing WebRTC sessions, participants, audio lockout, and video routing."""

    kFullAsMediumsCount = 4   # 1 Full is like 4 Mediums.
    kMaxMediumQualities = 16  # 4 Fulls or 16 Mediums.

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
        self.pinned_screens: Dict[int, Set[str]] = {}
        self.quality_update_pending: bool = False
        self.quality_update_count: int = 0
        self.requested_video_channels: List[Dict[str, Any]] = []

    def add_participant(
        self,
        endpoint_id: str,
        peer_id: int,
        name: str,
        entry_time: float = 0.0,
        has_video: bool = True,
        native_width: int = 1280,
        native_height: int = 720,
        endpoint_type: str = "Camera",
    ) -> VideoEndpoint:
        ep = VideoEndpoint(
            endpoint_id, peer_id, name, entry_time, has_video, native_width, native_height
        )
        ep.endpoint_type = endpoint_type
        self.endpoints[endpoint_id] = ep
        return ep

    def remove_participant(self, endpoint_id: str) -> None:
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
        if self.active_speaker_id == endpoint_id:
            self.active_speaker_id = None
        if self.secondary_display_pinned_id == endpoint_id:
            self.secondary_display_pinned_id = None
        for pinned in self.pinned_screens.values():
            pinned.discard(endpoint_id)

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

    # --- Simulcast quality-tier signalling (F50 / F59) ----------------

    def request_video_quality(self, endpoint_id: str, quality: str) -> bool:
        """Mirrors `GroupCall::requestVideoQuality`.

        Updates the endpoint's requested tier and schedules a requested-channels
        refresh. Returns False for an unknown endpoint or an unchanged tier, exactly
        like the C++ early-return.
        """
        ep = self.endpoints.get(endpoint_id)
        if ep is None or ep.requested_quality == quality:
            return False
        ep.requested_quality = quality
        ep.simulcast_spatial_layer = _SPATIAL_LAYER.get(quality, 0)
        self.quality_update_pending = True
        return True

    def request_simulcast_upscale(self, endpoint_id: str, high_quality: bool) -> None:
        """Signals WebRTC SFU to upscale resolution for pinned endpoints."""
        self.request_video_quality(
            endpoint_id,
            QUALITY_FULL if high_quality else QUALITY_THUMBNAIL,
        )

    def pin_to_screen(self, endpoint_id: str, screen_index: int = 1) -> bool:
        """Pinning requests Full quality for the endpoint on that screen."""
        self.pinned_screens.setdefault(screen_index, set()).add(endpoint_id)
        return self.request_video_quality(endpoint_id, QUALITY_FULL)

    def unpin_from_screen(self, endpoint_id: str, screen_index: int = 1) -> bool:
        """Unpinning reverts the endpoint to Medium instead of leaving it Full."""
        self.pinned_screens.get(screen_index, set()).discard(endpoint_id)
        return self.request_video_quality(endpoint_id, QUALITY_MEDIUM)

    def is_pinned(self, endpoint_id: str) -> bool:
        return any(endpoint_id in pinned for pinned in self.pinned_screens.values())

    def update_requested_video_channels(self) -> List[Dict[str, Any]]:
        """Mirrors `GroupCall::updateRequestedVideoChannels`.

        Produces the per-endpoint min/max tier list that is handed to tgcalls, then
        applies the bandwidth budget: `count(Full) * kFullAsMediumsCount + count(Medium)`
        is capped at `kMaxMediumQualities`, downgrading Full cameras to Medium and
        then Medium to Thumbnail.
        """
        self.quality_update_pending = False
        self.quality_update_count += 1

        channels: List[Dict[str, Any]] = []
        mediums = 0
        full_cameras = 0
        full_screencasts = 0

        for ep in self.endpoints.values():
            if not ep.has_video:
                continue
            quality = ep.requested_quality
            is_screen = (ep.endpoint_type == "Screen")
            min_quality = (
                QUALITY_FULL
                if (quality == QUALITY_FULL and is_screen)
                else QUALITY_THUMBNAIL
            )
            if quality == QUALITY_FULL:
                max_quality = QUALITY_FULL
            elif quality == QUALITY_MEDIUM:
                max_quality = QUALITY_MEDIUM
            else:
                max_quality = QUALITY_THUMBNAIL
            if max_quality == QUALITY_FULL:
                if is_screen:
                    full_screencasts += 1
                else:
                    full_cameras += 1
            elif max_quality == QUALITY_MEDIUM:
                mediums += 1
            channels.append(
                {
                    "endpointId": ep.endpoint_id,
                    "minQuality": min_quality,
                    "maxQuality": max_quality,
                }
            )

        mediums_count = mediums + (full_cameras + full_screencasts) * self.kFullAsMediumsCount
        downgrade_some = mediums_count > self.kMaxMediumQualities
        downgrade_all = (full_screencasts * self.kFullAsMediumsCount) > self.kMaxMediumQualities
        if downgrade_some:
            for channel in channels:
                if channel["maxQuality"] == QUALITY_FULL:
                    camera = channel["minQuality"] != QUALITY_FULL
                    if camera:
                        channel["maxQuality"] = QUALITY_MEDIUM
                    elif downgrade_all:
                        channel["maxQuality"] = QUALITY_THUMBNAIL
                        channel["minQuality"] = QUALITY_THUMBNAIL
            mediums += full_cameras
            full_cameras = 0
        if mediums > self.kMaxMediumQualities:
            for channel in channels:
                if channel["maxQuality"] == QUALITY_MEDIUM:
                    channel["maxQuality"] = QUALITY_THUMBNAIL

        self.requested_video_channels = channels
        return channels

    def on_stage_endpoints(self) -> List[str]:
        """Endpoints advertised as on-stage (Full max tier) to the SFU."""
        return [
            c["endpointId"]
            for c in self.requested_video_channels
            if c["maxQuality"] == QUALITY_FULL
        ]
