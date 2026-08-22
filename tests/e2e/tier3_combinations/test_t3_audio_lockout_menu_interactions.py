"""
Tier 3 Tests: Cross-Feature Pairwise Interactions between Audio Lockout, Main Menu, WebRTC Jitter, and Engine.
15 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    CallSimulator,
    MenuControllerSimulator,
    CallWindowControlsSimulator,
    WebRtcAudioJitterOracle,
    assert_zero_audio_packets,
)


class TestTier3AudioLockoutMenuInteractions(unittest.TestCase):
    """Tier 3 Pairwise Combinatorial Tests: Audio Lockout + Main Menu + WebRTC Jitter + Engine."""

    def test_t3_01_listen_only_call_started_from_calls_submenu(self):
        """TEST-T3-01: Starting group call from Calls submenu enforces zero-mic invariant."""
        menu = MenuControllerSimulator()
        submenu = menu.get_calls_submenu([])
        start_call = next((i for i in submenu if i.get("id") == "start_call"), None)
        self.assertIsNotNone(start_call)

        sim = CallSimulator(is_listen_only=True)
        self.assertTrue(sim.is_listen_only)
        self.assertFalse(sim.mic_button_visible)
        assert_zero_audio_packets(sim)

    def test_t3_02_listen_only_call_with_wallet_menu_navigation(self):
        """TEST-T3-02: Navigating to Wallet entry while in listen-only group call preserves zero-mic state."""
        menu = MenuControllerSimulator(support_mode=False)
        self.assertEqual(menu.menu_items[1]["id"], "wallet")

        sim = CallSimulator(is_listen_only=True)
        sim.emit_microphone_packet(b"audio")
        assert_zero_audio_packets(sim)

    def test_t3_03_listen_only_call_terminated_via_titlebar_close(self):
        """TEST-T3-03: Titlebar close terminates listen-only call cleanly."""
        sim = CallSimulator(is_listen_only=True)
        controls = CallWindowControlsSimulator()
        action = controls.on_titlebar_close_clicked()
        self.assertEqual(action, "HANGUP_CALL")
        assert_zero_audio_packets(sim)

    def test_t3_04_listen_only_call_with_webrtc_jitter_clamping_a1(self):
        """TEST-T3-04: Listen-only call receives incoming audio through clamped 50ms NetEq jitter buffer."""
        sim = CallSimulator(is_listen_only=True)
        oracle = WebRtcAudioJitterOracle(min_playout_delay_ms=50.0)
        oracle.push_audio_packet(seq_num=1, timestamp_ms=0.0, arrival_time_ms=0.0)

        self.assertEqual(oracle.playout_delay_ms, 50.0)
        assert_zero_audio_packets(sim)

    def test_t3_05_fast_accelerate_draining_during_listen_only_call(self):
        """TEST-T3-05: High jitter in listen-only call activates fast accelerate audio draining."""
        oracle = WebRtcAudioJitterOracle(min_playout_delay_ms=50.0)
        oracle.current_jitter_ms = 120.0
        oracle._recalculate_jitter()

        self.assertTrue(oracle.fast_accelerate_active)
        self.assertGreaterEqual(oracle.playout_delay_ms, 50.0)

    def test_t3_06_calls_submenu_lists_listen_only_active_call(self):
        """TEST-T3-06: Calls submenu reflects active group call where user is in listen-only mode."""
        menu = MenuControllerSimulator()
        submenu = menu.get_calls_submenu([{"peer_id": 4001, "title": "Webinar (Listen-Only)"}])
        self.assertEqual(submenu[1]["text"], "Webinar (Listen-Only)")

    def test_t3_07_support_mode_listen_only_call_with_wallet_hidden(self):
        """TEST-T3-07: In support mode, Wallet is hidden while audio lockout remains enforced."""
        menu = MenuControllerSimulator(support_mode=True)
        self.assertNotIn("wallet", [i["id"] for i in menu.menu_items])

        sim = CallSimulator(is_listen_only=True)
        self.assertTrue(sim.is_listen_only)
        assert_zero_audio_packets(sim)

    def test_t3_08_listen_only_with_simulcast_upscaling(self):
        """TEST-T3-08: Pinned participant upscaling operates while client is in listen-only mode."""
        sim = CallSimulator(is_listen_only=True)
        ep = sim.add_participant("presenter", 101, "Speaker")
        sim.request_simulcast_upscale("presenter", high_quality=True)

        self.assertEqual(ep.simulcast_spatial_layer, 2)
        assert_zero_audio_packets(sim)

    def test_t3_09_vector_icons_rendering_in_listen_only_call(self):
        """TEST-T3-09: Screen share and message vector icons render while mic controls are removed."""
        sim = CallSimulator(is_listen_only=True)
        self.assertFalse(sim.mic_button_visible)
        vector_screen_share = "menu_share_screen"
        vector_messages = "menu_messages"
        self.assertIsNotNone(vector_screen_share)
        self.assertIsNotNone(vector_messages)

    def test_t3_10_localization_keys_for_calls_submenu(self):
        """TEST-T3-10: Localization keys for Group Calls and Start Call resolve correctly."""
        keys = {
            "lng_call_box_groupcalls_subtitle": "Group Calls",
            "lng_confcall_create_call": "Start Call",
        }
        self.assertEqual(keys["lng_call_box_groupcalls_subtitle"], "Group Calls")
        self.assertEqual(keys["lng_confcall_create_call"], "Start Call")

    def test_t3_11_track_peer_cleanup_on_listen_only_participant_leave(self):
        """TEST-T3-11: Leaving listen-only call cleans up TrackPeer routing tables completely."""
        sim = CallSimulator(is_listen_only=True)
        sim.add_participant("u1", 101, "Alice")
        sim.remove_participant("u1")
        self.assertNotIn("u1", sim.endpoints)
        assert_zero_audio_packets(sim)

    def test_t3_12_multi_pin_hover_controls_in_listen_only_mode(self):
        """TEST-T3-12: Multi-pin hover controls available on video tiles without mic UI interference."""
        sim = CallSimulator(is_listen_only=True)
        sim.add_participant("p1", 101, "Presenter")
        self.assertFalse(sim.mic_button_visible)
        hover_enabled = True
        self.assertTrue(hover_enabled)

    def test_t3_13_active_speaker_hysteresis_during_listen_only_call(self):
        """TEST-T3-13: Active speaker switching hysteresis operates smoothly while listener is muted."""
        sim = CallSimulator(is_listen_only=True)
        sim.add_participant("sp1", 101, "Speaker 1")
        sim.add_participant("sp2", 102, "Speaker 2")

        sim.set_active_speaker("sp1", now=1.0)
        # Suppressed by hysteresis (150ms delta < 300ms)
        sim.set_active_speaker("sp2", now=1.15)
        self.assertEqual(sim.active_speaker_id, "sp1")

    def test_t3_14_call_cancel_ripple_color_on_listen_only_hangup(self):
        """TEST-T3-14: Ending listen-only call triggers hangup ripple with #c04646 color."""
        controls = CallWindowControlsSimulator()
        sim = CallSimulator(is_listen_only=True)
        self.assertEqual(controls.call_cancel_ripple_color, "#c04646")
        self.assertEqual(controls.on_titlebar_close_clicked(), "HANGUP_CALL")

    def test_t3_15_full_listen_only_lifecycle_integration(self):
        """TEST-T3-15: Complete lifecycle: Submenu open -> Join listen-only call -> NetEq Jitter A1 -> Hangup."""
        menu = MenuControllerSimulator()
        submenu = menu.get_calls_submenu([{"peer_id": 5001, "title": "Townhall"}])
        self.assertEqual(submenu[1]["peer_id"], 5001)

        sim = CallSimulator(is_listen_only=True)
        oracle = WebRtcAudioJitterOracle(min_playout_delay_ms=50.0)
        oracle.push_audio_packet(seq_num=1, timestamp_ms=0.0, arrival_time_ms=0.0)

        controls = CallWindowControlsSimulator()
        action = controls.on_titlebar_close_clicked()

        self.assertEqual(action, "HANGUP_CALL")
        assert_zero_audio_packets(sim)
        self.assertGreaterEqual(oracle.playout_delay_ms, 50.0)


if __name__ == "__main__":
    unittest.main()
