"""
Tier 3 Tests: Cross-Feature Pairwise Interactions between Multi-Display, Floating Overlay, and Embedded Chat.
15 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    DisplayCoordinatorMock,
    FloatingOverlaySimulator,
    CallSimulator,
    GeometryRect,
    assert_rect_equal,
    assert_opacity_clamped,
)


class TestTier3MultiDisplayOverlayInteractions(unittest.TestCase):
    """Tier 3 Pairwise Combinatorial Tests: Multi-Display + Floating Overlay + Embedded Chat."""

    def test_t3_01_stage_window_on_screen_2_with_overlay_on_screen_1(self):
        """TEST-T3-01: Video feed routed to stage window on screen 2 while companion overlay runs on screen 1."""
        coordinator = DisplayCoordinatorMock()
        overlay = FloatingOverlaySimulator(x=100, y=100, width=400, height=600)
        coordinator.pin_feed_to_screen(screen_id=2, feed_id="speaker_feed")
        overlay.toggle_visibility()

        self.assertEqual(coordinator.screens[2].pinned_feed_id, "speaker_feed")
        self.assertTrue(overlay.visible)
        assert_rect_equal(overlay.geometry, GeometryRect(100, 100, 400, 600))

    def test_t3_02_dual_prompt_selection_with_open_overlay(self):
        """TEST-T3-02: Target screen prompt routes feed to Screen 2 while overlay remains open on top."""
        coordinator = DisplayCoordinatorMock()
        overlay = FloatingOverlaySimulator()
        overlay.visible = True

        coordinator.prompt_target_screen("feed_bob", chosen_screen_id=2)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_bob")
        self.assertTrue(overlay.visible)

    def test_t3_03_drag_overlay_across_screen_boundary(self):
        """TEST-T3-03: Dragging overlay from primary screen (0..1920) across to secondary screen (1920..3840)."""
        coordinator = DisplayCoordinatorMock()
        overlay = FloatingOverlaySimulator(x=1700, y=100, width=400, height=600)
        overlay.drag_move(dx=400, dy=50)

        self.assertEqual(overlay.geometry.x, 2100)
        self.assertEqual(overlay.geometry.y, 150)
        # Overlay is now positioned over Screen 2
        sec_screen = coordinator.screens[2]
        self.assertTrue(sec_screen.geometry.contains(GeometryRect(overlay.geometry.x, overlay.geometry.y, 100, 100)))

    def test_t3_04_ctrl_shift_t_toggle_with_fullscreen_stage(self):
        """TEST-T3-04: Ctrl+Shift+T toggles overlay without disrupting secondary display fullscreen stage."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "stage_feed")
        overlay = FloatingOverlaySimulator()

        overlay.toggle_visibility()
        self.assertTrue(overlay.visible)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "stage_feed")

        overlay.toggle_visibility()
        self.assertFalse(overlay.visible)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "stage_feed")

    def test_t3_05_opacity_adjustment_over_secondary_screen(self):
        """TEST-T3-05: Adjusting opacity on overlay placed over secondary stage window."""
        overlay = FloatingOverlaySimulator(x=2000, y=100)
        overlay.adjust_opacity(120)
        self.assertAlmostEqual(overlay.opacity, 0.75)
        assert_opacity_clamped(overlay.opacity)

    def test_t3_06_in_meeting_chat_search_during_stage_streaming(self):
        """TEST-T3-06: Searching in-meeting chat inside overlay while secondary stage streams video."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "live_stream")
        overlay = FloatingOverlaySimulator()
        overlay.chat_messages = [
            {"id": 1, "text": "Presentation slide 1"},
            {"id": 2, "text": "Question about slide 1"},
        ]
        results = overlay.set_search_query("slide 1")
        self.assertEqual(len(results), 2)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "live_stream")

    def test_t3_07_active_speaker_isolation_with_top_most_overlay(self):
        """TEST-T3-07: Secondary display active-speaker isolation works concurrently with top-most overlay."""
        sim = CallSimulator()
        sim.secondary_display_pinned_id = "feed_pinned"
        overlay = FloatingOverlaySimulator()
        overlay.visible = True

        sim.add_participant("sp1", 101, "Alice")
        sim.set_active_speaker("sp1")
        self.assertEqual(sim.secondary_display_pinned_id, "feed_pinned")
        self.assertTrue(overlay.visible)

    def test_t3_08_screen_disconnect_fallback_preserves_overlay(self):
        """TEST-T3-08: Disconnecting secondary display falls back video to primary while overlay stays intact."""
        coordinator = DisplayCoordinatorMock()
        overlay = FloatingOverlaySimulator(x=200, y=200)
        overlay.visible = True
        coordinator.pin_feed_to_screen(2, "deck_feed")

        coordinator.remove_screen(2)
        primary = coordinator.get_primary_screen()
        self.assertEqual(primary.pinned_feed_id, "deck_feed")
        self.assertTrue(overlay.visible)

    def test_t3_09_chat_station_role_with_companion_hud_overlay(self):
        """TEST-T3-09: Display Role Router assigns ChatStation to screen 3 while overlay runs on screen 1."""
        coordinator = DisplayCoordinatorMock()
        coordinator.add_screen(3, "Screen 3", GeometryRect(3840, 0, 1080, 1920))
        coordinator.assign_role(3, "ChatStation")
        overlay = FloatingOverlaySimulator(x=50, y=50)
        overlay.visible = True

        self.assertEqual(coordinator.screens[3].assigned_role, "ChatStation")
        self.assertTrue(overlay.visible)

    def test_t3_10_pin_from_search_to_secondary_display(self):
        """TEST-T3-10: Pinning a participant from sidebar search directly to Screen 2."""
        coordinator = DisplayCoordinatorMock()
        sim = CallSimulator()
        sim.add_participant("u1", 101, "Alice Special")
        filtered = sim.filter_participants("Alice")
        self.assertEqual(len(filtered), 1)

        coordinator.pin_feed_to_screen(2, filtered[0].endpoint_id)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "u1")

    def test_t3_11_escape_dismisses_overlay_only(self):
        """TEST-T3-11: Pressing Escape dismisses overlay without affecting stage window on screen 2."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "feed_stage")
        overlay = FloatingOverlaySimulator()
        overlay.visible = True

        overlay.dismiss()
        self.assertFalse(overlay.visible)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_stage")

    def test_t3_12_overlay_dynamic_resize_with_active_stage(self):
        """TEST-T3-12: Resizing overlay chat window while secondary stage video is running."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "feed_stage")
        overlay = FloatingOverlaySimulator(width=300, height=400)
        overlay.resize(new_width=500, new_height=700)

        assert_rect_equal(overlay.geometry, GeometryRect(100, 100, 500, 700))
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_stage")

    def test_t3_13_unpin_from_thumbnail_with_active_overlay(self):
        """TEST-T3-13: Unpinning feed from stage thumbnail leaves overlay unaffected."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "feed_stage")
        overlay = FloatingOverlaySimulator()
        overlay.visible = True

        coordinator.unpin_feed_from_screen(2)
        self.assertIsNone(coordinator.screens[2].pinned_feed_id)
        self.assertTrue(overlay.visible)

    def test_t3_14_rapid_multi_monitor_pin_swapping_with_overlay(self):
        """TEST-T3-14: Swapping pinned feeds between Screen 1 and Screen 2 with overlay open."""
        coordinator = DisplayCoordinatorMock()
        overlay = FloatingOverlaySimulator()
        overlay.visible = True
        coordinator.pin_feed_to_screen(1, "feed_a")
        coordinator.pin_feed_to_screen(2, "feed_b")

        # Swap
        coordinator.pin_feed_to_screen(1, "feed_b")
        coordinator.pin_feed_to_screen(2, "feed_a")

        self.assertEqual(coordinator.screens[1].pinned_feed_id, "feed_b")
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "feed_a")
        self.assertTrue(overlay.visible)

    def test_t3_15_audio_isolation_with_multi_screen_and_overlay(self):
        """TEST-T3-15: Primary screen handles audio output while Screen 2 displays video and overlay shows chat."""
        coordinator = DisplayCoordinatorMock()
        coordinator.pin_feed_to_screen(2, "video_feed")
        primary = coordinator.get_primary_screen()
        overlay = FloatingOverlaySimulator()
        overlay.visible = True

        self.assertTrue(primary.is_primary)
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "video_feed")
        self.assertTrue(overlay.visible)


if __name__ == "__main__":
    unittest.main()
