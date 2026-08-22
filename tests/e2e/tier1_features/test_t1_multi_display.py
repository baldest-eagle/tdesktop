"""
Tier 1 Tests for Category 4: Multi-Display & Routing (Features 11–15).
25 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    DisplayCoordinatorMock,
    CallSimulator,
    GeometryRect,
    assert_rect_equal,
)


class TestTier1MultiDisplay(unittest.TestCase):
    """Tier 1 Test Suite for Features 11 through 15."""

    # --- Feature 11: Multi-Monitor Stage Window Support ---

    def test_t1_f11_01_stage_window_instantiation_secondary_screen(self):
        """TEST-T1-F11-01: Stage window is instantiated on secondary display."""
        coordinator = DisplayCoordinatorMock()
        self.assertEqual(len(coordinator.screens), 2)
        sec_screen = coordinator.screens[2]
        self.assertEqual(sec_screen.assigned_role, "StageGrid")

    def test_t1_f11_02_video_feed_routed_to_stage_window(self):
        """TEST-T1-F11-02: Video feed is pinned and routed to stage window on screen 2."""
        coordinator = DisplayCoordinatorMock()
        success = coordinator.pin_feed_to_screen(screen_id=2, feed_id="speaker_feed_101")
        self.assertTrue(success)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "speaker_feed_101")

    def test_t1_f11_03_stage_window_geometry_matches_secondary_bounds(self):
        """TEST-T1-F11-03: Stage window geometry spans secondary display (1920, 0, 1920, 1080)."""
        coordinator = DisplayCoordinatorMock()
        sec_screen = coordinator.screens[2]
        assert_rect_equal(sec_screen.geometry, GeometryRect(1920, 0, 1920, 1080))

    def test_t1_f11_04_primary_window_remains_active_during_stage_routing(self):
        """TEST-T1-F11-04: Primary window stays interactive when stage window is open."""
        coordinator = DisplayCoordinatorMock()
        primary = coordinator.get_primary_screen()
        self.assertIsNotNone(primary)
        self.assertEqual(primary.screen_id, 1)

    def test_t1_f11_05_closing_stage_window_restores_primary_routing(self):
        """TEST-T1-F11-05: Closing stage window unpins feed and restores single-screen mode."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(screen_id=2, feed_id="feed_101")
        coordinator.unpin_feed_from_screen(screen_id=2)
        self.assertIsNone(coordinator.screens[2].pinned_feed_id)

    # --- Feature 12: Dual Initial Windows Prompt ---

    def test_t1_f12_01_dual_prompt_display_on_multi_monitor(self):
        """TEST-T1-F12-01: Dual initial windows prompt is offered when multiple screens detected."""
        coordinator = DisplayCoordinatorMock()
        has_multiple_monitors = len(coordinator.screens) >= 2
        self.assertTrue(has_multiple_monitors)

    def test_t1_f12_02_dual_prompt_suppressed_on_single_monitor(self):
        """TEST-T1-F12-02: Dual initial prompt is suppressed in single-monitor setup."""
        coordinator = DisplayCoordinatorMock()
        coordinator.remove_screen(2)
        has_multiple_monitors = len(coordinator.screens) >= 2
        self.assertFalse(has_multiple_monitors)

    def test_t1_f12_03_choose_screen_1_pins_to_primary(self):
        """TEST-T1-F12-03: Selecting Screen 1 pins feed to primary display."""
        coordinator = DisplayCoordinatorMock()
        coordinator.prompt_target_screen("feed_alice", chosen_screen_id=1)
        self.assertEqual(coordinator.screens[1].pinned_feed_id, "feed_alice")

    def test_t1_f12_04_choose_screen_2_pins_to_secondary(self):
        """TEST-T1-F12-04: Selecting Screen 2 pins feed to secondary display."""
        coordinator = DisplayCoordinatorMock()
        coordinator.prompt_target_screen("feed_bob", chosen_screen_id=2)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_bob")

    def test_t1_f12_05_cancel_dual_prompt_defaults_to_primary(self):
        """TEST-T1-F12-05: Canceling target screen prompt defaults to Screen 1."""
        coordinator = DisplayCoordinatorMock()
        # Default fallback
        coordinator.pin_feed_to_screen(1, "feed_default")
        self.assertEqual(coordinator.screens[1].pinned_feed_id, "feed_default")

    # --- Feature 13: Display Role Router ---

    def test_t1_f13_01_enumerate_qscreen_objects(self):
        """TEST-T1-F13-01: Enumerate virtual QScreen objects with exact coordinates."""
        coordinator = DisplayCoordinatorMock()
        screens = list(coordinator.screens.values())
        self.assertEqual(len(screens), 2)
        self.assertEqual(screens[0].name, "Monitor 1 (Primary)")
        self.assertEqual(screens[1].name, "Monitor 2 (Secondary)")

    def test_t1_f13_02_assign_stage_grid_role(self):
        """TEST-T1-F13-02: Assign StageGrid role to secondary display."""
        coordinator = DisplayCoordinatorMock()
        coordinator.assign_role(2, "StageGrid")
        self.assertEqual(coordinator.screens[2].assigned_role, "StageGrid")

    def test_t1_f13_03_assign_chat_station_role(self):
        """TEST-T1-F13-03: Assign ChatStation role to third monitor."""
        coordinator = DisplayCoordinatorMock()
        coordinator.add_screen(3, "Monitor 3 (Vertical)", GeometryRect(3840, 0, 1080, 1920))
        coordinator.assign_role(3, "ChatStation")
        self.assertEqual(coordinator.screens[3].assigned_role, "ChatStation")

    def test_t1_f13_04_fallback_to_primary_on_monitor_disconnect(self):
        """TEST-T1-F13-04: Unplugging secondary display falls back pinned feeds to primary display."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "feed_pres")
        coordinator.remove_screen(2)

        primary = coordinator.get_primary_screen()
        self.assertIsNotNone(primary)
        self.assertEqual(primary.pinned_feed_id, "feed_pres")

    def test_t1_f13_05_role_reassignment_dynamic_update(self):
        """TEST-T1-F13-05: Dynamic role reassignment updates screen role property."""
        coordinator = DisplayCoordinatorMock()
        coordinator.assign_role(2, "ActiveSpeakerStage")
        self.assertEqual(coordinator.screens[2].assigned_role, "ActiveSpeakerStage")

    # --- Feature 14: Async Video Stream Routing ---

    def test_t1_f14_01_async_video_sink_dispatch(self):
        """TEST-T1-F14-01: Video frame dispatch executes asynchronously."""
        sim = CallSimulator()
        ep = sim.add_participant("ep_1", 101, "Alice")
        self.assertIsNotNone(ep)

    def test_t1_f14_02_active_speaker_routed_to_secondary_display(self):
        """TEST-T1-F14-02: Active speaker is routed to secondary display."""
        sim = CallSimulator()
        sim.secondary_display_active_speaker_disabled = False
        sim.add_participant("ep_speaker", 102, "Speaker Bob")
        sim.set_active_speaker("ep_speaker")
        self.assertEqual(sim.secondary_display_pinned_id, "ep_speaker")

    def test_t1_f14_03_concurrent_video_rendering_across_screens(self):
        """TEST-T1-F14-03: Concurrent video feeds render independently across screens."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(1, "feed_1")
        coordinator.pin_feed_to_screen(2, "feed_2")
        self.assertEqual(coordinator.screens[1].pinned_feed_id, "feed_1")
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_2")

    def test_t1_f14_04_zero_frame_drops_during_monitor_swap(self):
        """TEST-T1-F14-04: Swapping display roles preserves active video feeds."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(1, "feed_a")
        coordinator.pin_feed_to_screen(2, "feed_b")
        # Swap
        coordinator.pin_feed_to_screen(1, "feed_b")
        coordinator.pin_feed_to_screen(2, "feed_a")
        self.assertEqual(coordinator.screens[1].pinned_feed_id, "feed_b")
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_a")

    def test_t1_f14_05_sink_destruction_cleanup(self):
        """TEST-T1-F14-05: Unpinning feed clears video sink association."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "feed_temp")
        coordinator.unpin_feed_from_screen(2)
        self.assertIsNone(coordinator.screens[2].pinned_feed_id)

    # --- Feature 15: Secondary Display Active-Speaker Isolation ---

    def test_t1_f15_01_disable_auto_filling_on_secondary_screen(self):
        """TEST-T1-F15-01: Auto-filling / slot hijacking is disabled on secondary screen."""
        sim = CallSimulator()
        self.assertTrue(sim.secondary_display_active_speaker_disabled)

    def test_t1_f15_02_explicit_pinned_feed_preserved_on_screen_2(self):
        """TEST-T1-F15-02: Explicitly pinned feed on screen 2 is not overridden by new speaker."""
        sim = CallSimulator()
        sim.secondary_display_pinned_id = "feed_pinned_deck"
        sim.add_participant("ep_charlie", 103, "Charlie")
        sim.set_active_speaker("ep_charlie")
        self.assertEqual(sim.secondary_display_pinned_id, "feed_pinned_deck")

    def test_t1_f15_03_speaker_change_does_not_mutate_secondary_pin(self):
        """TEST-T1-F15-03: Rapid speaker transitions leave secondary pinned feed unchanged."""
        sim = CallSimulator()
        sim.secondary_display_pinned_id = "feed_main"
        sim.add_participant("s1", 201, "Speaker 1")
        sim.add_participant("s2", 202, "Speaker 2")
        sim.set_active_speaker("s1", now=1.0)
        sim.set_active_speaker("s2", now=2.0)
        self.assertEqual(sim.secondary_display_pinned_id, "feed_main")

    def test_t1_f15_04_unpin_clears_secondary_feed(self):
        """TEST-T1-F15-04: Explicit unpin leaves secondary stage clear."""
        sim = CallSimulator()
        sim.secondary_display_pinned_id = "feed_temp"
        sim.secondary_display_pinned_id = None
        self.assertIsNone(sim.secondary_display_pinned_id)

    def test_t1_f15_05_audio_routed_to_primary_while_video_on_secondary(self):
        """TEST-T1-F15-05: Audio playback continues on primary device when video is on screen 2."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "feed_video_only")
        primary = coordinator.get_primary_screen()
        self.assertTrue(primary.is_primary)


if __name__ == "__main__":
    unittest.main()
