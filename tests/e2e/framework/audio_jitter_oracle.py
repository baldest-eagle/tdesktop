"""
WebRTC NetEq Playout Delay & Jitter Clamping Oracle (Feature 54 / A1 Optimization).
"""

from typing import List, Dict, Any, Optional


class WebRtcAudioJitterOracle:
    """Simulates tgcalls WebRTC NetEq jitter buffer and playout delay clamping."""

    def __init__(self, min_playout_delay_ms: float = 50.0, max_playout_delay_ms: float = 120.0):
        self.min_playout_delay_ms = min_playout_delay_ms
        self.max_playout_delay_ms = max_playout_delay_ms
        self.buffered_packets: List[Dict[str, Any]] = []
        self.current_jitter_ms: float = 0.0
        self.playout_delay_ms: float = min_playout_delay_ms
        self.fast_accelerate_active: bool = False

    def push_audio_packet(self, seq_num: int, timestamp_ms: float, arrival_time_ms: float) -> None:
        """Pushes an incoming RTP audio packet into NetEq buffer."""
        self.buffered_packets.append(
            {
                "seq_num": seq_num,
                "timestamp_ms": timestamp_ms,
                "arrival_time_ms": arrival_time_ms,
            }
        )
        self._recalculate_jitter()

    def _recalculate_jitter(self) -> None:
        """Calculates inter-arrival jitter and clamps playout delay."""
        if len(self.buffered_packets) >= 2:
            p_last = self.buffered_packets[-1]
            p_prev = self.buffered_packets[-2]
            delta_arrival = p_last["arrival_time_ms"] - p_prev["arrival_time_ms"]
            delta_transit = p_last["timestamp_ms"] - p_prev["timestamp_ms"]
            jitter_sample = abs(delta_arrival - delta_transit)
            self.current_jitter_ms = 0.9 * self.current_jitter_ms + 0.1 * jitter_sample

        # Fast accelerate mode if jitter buffer exceeds threshold
        if self.current_jitter_ms > 80.0:
            self.fast_accelerate_active = True
            # Fast drain to bring playout latency down to min_playout_delay_ms
            self.playout_delay_ms = max(
                self.min_playout_delay_ms,
                min(self.max_playout_delay_ms, self.min_playout_delay_ms + self.current_jitter_ms * 0.2),
            )
        else:
            self.fast_accelerate_active = False
            self.playout_delay_ms = max(
                self.min_playout_delay_ms,
                min(self.max_playout_delay_ms, self.min_playout_delay_ms + self.current_jitter_ms),
            )

    def drain_playout_packet(self) -> Optional[Dict[str, Any]]:
        """Drains next audio packet for speaker playback."""
        if self.buffered_packets:
            return self.buffered_packets.pop(0)
        return None
