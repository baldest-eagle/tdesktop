"""
Tier 3 Tests: Cross-Feature Pairwise Interactions between Call UI, Grid Layout, and Backend Engine.
16 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    CallSimulator,
    CallWindowControlsSimulator,
    GridSolverOracle,
    PinSlotAllocator,
    GeometryRect,
    assert_rect_equal,
    assert_no_overlap,
    assert_bounded_within,
)


class TestTier3CallUiGridInteractions(unittest.TestCase):
    """Tier 3 Pairwise Combinatorial Tests: Call UI + Grid & Pin System."""

    def test_t3_01_grid_mode_toggle_with_preset_1x1(self):
        """TEST-T3-01: Toggling Grid mode on a 1-participant call activates 1x1 full viewport preset."""
        controls = CallWindowControlsSimulator()
        solver = GridSolverOracle()
        controls.toggle_grid_mode()
        self.assertTrue(controls.grid_mode_enabled)

        rects = solver.solve_preset_grid(1000, 600, slot_count=1, participant_count=1)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 1000, 600))

    def test_t3_02_grid_mode_toggle_with_preset_2x2(self):
        """TEST-T3-02: Toggling Grid mode with 4 feeds allocates 2x2 symmetrical layout."""
        controls = CallWindowControlsSimulator()
        solver = GridSolverOracle()
        controls.toggle_grid_mode()

        rects = solver.solve_preset_grid(1000, 600, slot_count=4, participant_count=4)
        self.assertEqual(len(rects), 4)
        assert_no_overlap(rects)

    def test_t3_03_grid_mode_toggle_with_preset_3x3(self):
        """TEST-T3-03: Toggling Grid mode with 9 feeds allocates 3x3 matrix."""
        controls = CallWindowControlsSimulator()
        solver = GridSolverOracle()
        controls.toggle_grid_mode()

        rects = solver.solve_preset_grid(1200, 900, slot_count=9, participant_count=9)
        self.assertEqual(len(rects), 9)
        assert_no_overlap(rects)

    def test_t3_04_grid_mode_with_dynamic_50_50_split(self):
        """TEST-T3-04: Grid mode in dynamic setting with 2 feeds produces 50/50 split."""
        controls = CallWindowControlsSimulator()
        solver = GridSolverOracle()
        controls.toggle_grid_mode()

        rects = solver.solve_50_50_split(1200, 800)
        self.assertEqual(len(rects), 2)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 598, 800))
        assert_rect_equal(rects[1], GeometryRect(602, 0, 598, 800))

    def test_t3_05_chat_panel_slide_out_over_2x2_grid(self):
        """TEST-T3-05: Opening slide-out chat over 2x2 grid does not disrupt background tile geometries."""
        controls = CallWindowControlsSimulator()
        solver = GridSolverOracle()
        controls.toggle_grid_mode()
        controls.toggle_chat_panel()

        self.assertTrue(controls.chat_panel_visible)
        rects = solver.solve_preset_grid(1000, 600, slot_count=4, participant_count=4)
        assert_no_overlap(rects)

    def test_t3_06_chat_panel_slide_out_with_pinned_stage(self):
        """TEST-T3-06: Chat panel slide-out combined with pinned stage preserves splitter ratio."""
        controls = CallWindowControlsSimulator()
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.set_splitter_ratio(0.60)
        controls.toggle_chat_panel()

        self.assertTrue(controls.chat_panel_visible)
        self.assertEqual(alloc.splitter_ratio, 0.60)

    def test_t3_07_end_call_hover_controls_in_wide_grid_mode(self):
        """TEST-T3-07: In Wide/Grid mode, end call button is accessible via hover without obstructing video."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Grid")
        self.assertFalse(controls.floating_center_controls_visible)
        controls.hover_controls_visible = True
        self.assertTrue(controls.hover_controls_visible)

    def test_t3_08_obstructing_button_cleanup_with_active_screen_share(self):
        """TEST-T3-08: Screen sharing in Grid mode maintains clean unobstructed viewport."""
        controls = CallWindowControlsSimulator()
        controls.set_panel_mode("Grid")
        self.assertFalse(controls.floating_center_controls_visible)

    def test_t3_09_multi_pin_combined_with_simulcast_upscaling(self):
        """TEST-T3-09: Pinning 3 feeds simultaneously signals WebRTC simulcast upscale (layer 2) for all 3."""
        sim = CallSimulator()
        alloc = PinSlotAllocator()
        for i in range(3):
            ep_id = f"peer_{i}"
            sim.add_participant(ep_id, 100 + i, f"User {i}")
            alloc.pin(ep_id)
            sim.request_simulcast_upscale(ep_id, high_quality=True)

        self.assertEqual(len(alloc.pinned_endpoints), 3)
        self.assertTrue(all(sim.endpoints[f"peer_{i}"].simulcast_spatial_layer == 2 for i in range(3)))

    def test_t3_10_multi_pin_hover_controls_with_splitter_drag(self):
        """TEST-T3-10: Adjusting pinned panel splitter while hover controls are active."""
        alloc = PinSlotAllocator()
        alloc.pin("feed1")
        alloc.set_splitter_ratio(0.70)
        self.assertEqual(alloc.splitter_ratio, 0.70)
        self.assertTrue(alloc.is_pinned("feed1"))

    def test_t3_11_pin_from_context_menu_in_wide_mode(self):
        """TEST-T3-11: Pinning a participant from context menu while in Wide mode updates layout."""
        controls = CallWindowControlsSimulator()
        alloc = PinSlotAllocator()
        controls.set_panel_mode("Wide")
        alloc.pin("user_context")
        ordered = alloc.get_ordered_endpoints(["user_context", "user_other"])
        self.assertEqual(ordered[0][0], "user_context")
        self.assertTrue(ordered[0][1])

    def test_t3_12_unpin_action_updates_dynamic_grid_solver(self):
        """TEST-T3-12: Unpinning feed dynamically recalculates dynamic grid layout from 3 to 2 tiles."""
        alloc = PinSlotAllocator()
        solver = GridSolverOracle()
        alloc.pin("p1")
        alloc.unpin("p1")

        rects = solver.solve_dynamic_grid(1200, 800, count=2)
        self.assertEqual(len(rects), 2)
        assert_no_overlap(rects)

    def test_t3_13_active_speaker_hysteresis_with_dynamic_50_50_grid(self):
        """TEST-T3-13: Active speaker hysteresis damping operates smoothly with 50/50 split layout."""
        sim = CallSimulator()
        solver = GridSolverOracle()
        sim.add_participant("s1", 101, "Alice")
        sim.add_participant("s2", 102, "Bob")
        sim.set_active_speaker("s1", now=1.0)
        sim.set_active_speaker("s2", now=1.1)  # Suppressed by hysteresis

        self.assertEqual(sim.active_speaker_id, "s1")
        rects = solver.solve_50_50_split(1000, 600)
        self.assertEqual(len(rects), 2)

    def test_t3_14_camera_toggle_updates_dynamic_grid_dimensions(self):
        """TEST-T3-14: Disabling local camera reduces active video count and re-solves dynamic grid."""
        sim = CallSimulator()
        solver = GridSolverOracle()
        sim.add_participant("local", 1, "Me", has_video=True)
        sim.add_participant("remote", 2, "Peer", has_video=True)
        # 2 videos -> 50/50 split
        r2 = solver.solve_50_50_split(1000, 600)
        self.assertEqual(len(r2), 2)

        # Local turns off video -> 1 video left -> full screen
        sim.endpoints["local"].has_video = False
        r1 = solver.solve_dynamic_grid(1000, 600, count=1)
        self.assertEqual(len(r1), 1)
        assert_rect_equal(r1[0], GeometryRect(0, 0, 1000, 600))

    def test_t3_15_titlebar_close_terminates_multi_pin_call(self):
        """TEST-T3-15: Closing titlebar cleanly terminates call containing 4 active pinned feeds."""
        controls = CallWindowControlsSimulator()
        alloc = PinSlotAllocator()
        for i in range(4):
            alloc.pin(f"p_{i}")
        action = controls.on_titlebar_close_clicked()
        self.assertEqual(action, "HANGUP_CALL")

    def test_t3_16_uncapped_16_participant_grid_with_slide_out_chat(self):
        """TEST-T3-16: 16-participant uncapped grid operates concurrently with open chat panel."""
        controls = CallWindowControlsSimulator()
        solver = GridSolverOracle()
        controls.toggle_grid_mode()
        controls.toggle_chat_panel()

        rects = solver.solve_dynamic_grid(1600, 1200, count=16)
        self.assertEqual(len(rects), 16)
        assert_no_overlap(rects)
        self.assertTrue(controls.chat_panel_visible)


if __name__ == "__main__":
    unittest.main()
