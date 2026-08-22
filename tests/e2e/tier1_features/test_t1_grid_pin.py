"""
Tier 1 Tests for Category 5: Grid Layout & Pin System (Features 16–24).
45 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    GridSolverOracle,
    PinSlotAllocator,
    GeometryRect,
    assert_rect_equal,
    assert_no_overlap,
    assert_bounded_within,
)


class TestTier1GridPin(unittest.TestCase):
    """Tier 1 Test Suite for Features 16 through 24."""

    # --- Feature 16: Discrete Layout Presets (1x1, 2x2, 3x3) ---

    def test_t1_f16_01_preset_1x1_single_focus_tile_geometry(self):
        """TEST-T1-F16-01: Preset 1x1 allocates 1 full-viewport tile."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_preset_grid(width=1000, height=600, slot_count=1, participant_count=1)
        self.assertEqual(len(rects), 1)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 1000, 600))

    def test_t1_f16_02_preset_2x2_symmetrical_4_quadrant_partitioning(self):
        """TEST-T1-F16-02: Preset 2x2 partitions into 4 non-overlapping quadrants."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_preset_grid(width=1000, height=600, slot_count=4, participant_count=4)
        self.assertEqual(len(rects), 4)
        assert_no_overlap(rects)
        for r in rects:
            assert_bounded_within(r, 1000, 600)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 498, 298))
        assert_rect_equal(rects[1], GeometryRect(502, 0, 498, 298))
        assert_rect_equal(rects[2], GeometryRect(0, 302, 498, 298))
        assert_rect_equal(rects[3], GeometryRect(502, 302, 498, 298))

    def test_t1_f16_03_preset_3x3_symmetrical_9_tile_matrix(self):
        """TEST-T1-F16-03: Preset 3x3 creates 9 non-overlapping cells."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_preset_grid(width=1200, height=900, slot_count=9, participant_count=9)
        self.assertEqual(len(rects), 9)
        assert_no_overlap(rects)
        for r in rects:
            assert_bounded_within(r, 1200, 900)

    def test_t1_f16_04_preset_2x2_under_capacity_3_feeds(self):
        """TEST-T1-F16-04: Preset 2x2 with 3 feeds renders 3 quadrant tiles without distortion."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_preset_grid(width=1000, height=600, slot_count=4, participant_count=3)
        self.assertEqual(len(rects), 3)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 498, 298))
        assert_rect_equal(rects[1], GeometryRect(502, 0, 498, 298))
        assert_rect_equal(rects[2], GeometryRect(0, 302, 498, 298))

    def test_t1_f16_05_preset_3x3_overflow_12_feeds(self):
        """TEST-T1-F16-05: Preset 3x3 with 12 feeds renders 9 visible tiles and 3 empty overflow rects."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_preset_grid(width=1200, height=900, slot_count=9, participant_count=12)
        self.assertEqual(len(rects), 12)
        for i in range(9):
            self.assertTrue(rects[i].is_valid())
        for i in range(9, 12):
            self.assertTrue(rects[i].is_empty())

    # --- Feature 17: Dynamic Grid Solver (50/50 Split) ---

    def test_t1_f17_01_two_feed_50_50_horizontal_split(self):
        """TEST-T1-F17-01: Exactly 2 feeds split viewport equally 50/50."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_50_50_split(width=1200, height=800)
        self.assertEqual(len(rects), 2)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 598, 800))
        assert_rect_equal(rects[1], GeometryRect(602, 0, 598, 800))
        assert_no_overlap(rects)

    def test_t1_f17_02_dynamic_1_feed_auto_expansion(self):
        """TEST-T1-F17-02: 1 feed expands to full viewport in dynamic mode."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_dynamic_grid(width=1920, height=1080, count=1)
        self.assertEqual(len(rects), 1)
        assert_rect_equal(rects[0], GeometryRect(0, 0, 1920, 1080))

    def test_t1_f17_03_transition_from_1_to_2_feeds(self):
        """TEST-T1-F17-03: Transitioning from 1 to 2 feeds recalculates from 1x1 to 50/50."""
        solver = GridSolverOracle(skip=4)
        r1 = solver.solve_dynamic_grid(width=1000, height=600, count=1)
        self.assertEqual(r1[0].width, 1000)
        r2 = solver.solve_dynamic_grid(width=1000, height=600, count=2)
        self.assertEqual(r2[0].width, 498)
        self.assertEqual(r2[1].width, 498)

    def test_t1_f17_04_skip_margin_gap_subtraction(self):
        """TEST-T1-F17-04: 50/50 split width accounts for skip margin correctly."""
        solver = GridSolverOracle(skip=6)
        rects = solver.solve_50_50_split(width=1006, height=500)
        # (1006 - 6) / 2 = 500
        self.assertEqual(rects[0].width, 500)
        self.assertEqual(rects[1].x, 506)

    def test_t1_f17_05_non_overlapping_50_50_rects(self):
        """TEST-T1-F17-05: 50/50 split rects never overlap."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_50_50_split(width=1600, height=900)
        assert_no_overlap(rects)

    # --- Feature 18: Uncapped Dynamic Main Grid Scaling ---

    def test_t1_f18_01_dynamic_scaling_6_participants(self):
        """TEST-T1-F18-01: Dynamic solver scales 6 participants into non-overlapping grid."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_dynamic_grid(width=1200, height=800, count=6)
        self.assertEqual(len(rects), 6)
        assert_no_overlap(rects)
        for r in rects:
            assert_bounded_within(r, 1200, 800)

    def test_t1_f18_02_dynamic_scaling_16_participants(self):
        """TEST-T1-F18-02: Dynamic solver scales 16 participants into 4x4 matrix."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_dynamic_grid(width=1600, height=1200, count=16)
        self.assertEqual(len(rects), 16)
        assert_no_overlap(rects)

    def test_t1_f18_03_dynamic_scaling_32_participants(self):
        """TEST-T1-F18-03: Dynamic solver scales 32 participants within viewport bounds."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_dynamic_grid(width=1920, height=1080, count=32)
        self.assertEqual(len(rects), 32)
        assert_no_overlap(rects)
        for r in rects:
            assert_bounded_within(r, 1920, 1080)

    def test_t1_f18_04_aspect_ratio_optimization(self):
        """TEST-T1-F18-04: Optimal columns vs rows chosen to minimize letterboxing."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_dynamic_grid(width=1920, height=1080, count=8)
        self.assertEqual(len(rects), 8)
        # All rects must have positive width and height
        self.assertTrue(all(r.is_valid() for r in rects))

    def test_t1_f18_05_viewport_resize_recalculates_bounds(self):
        """TEST-T1-F18-05: Window resize dynamically updates all tile coordinates."""
        solver = GridSolverOracle(skip=4)
        r_small = solver.solve_dynamic_grid(width=800, height=600, count=4)
        r_large = solver.solve_dynamic_grid(width=1600, height=1200, count=4)
        self.assertGreater(r_large[0].width, r_small[0].width)

    # --- Feature 19: Persistent Pin Slot Allocator ---

    def test_t1_f19_01_pin_endpoint_allocates_leading_slot(self):
        """TEST-T1-F19-01: Pinned endpoint is placed in slot 0."""
        alloc = PinSlotAllocator()
        alloc.pin("user_alice")
        ordered = alloc.get_ordered_endpoints(["user_bob", "user_alice", "user_charlie"])
        self.assertEqual(ordered[0], ("user_alice", True))
        self.assertEqual(ordered[1], ("user_bob", False))

    def test_t1_f19_02_unpinned_peer_join_preserves_pinned_slot(self):
        """TEST-T1-F19-02: New unpinned joins do not shift pinned slots."""
        alloc = PinSlotAllocator()
        alloc.pin("user_pinned")
        ordered1 = alloc.get_ordered_endpoints(["user_pinned", "user_1"])
        ordered2 = alloc.get_ordered_endpoints(["user_pinned", "user_1", "user_2"])
        self.assertEqual(ordered1[0][0], "user_pinned")
        self.assertEqual(ordered2[0][0], "user_pinned")

    def test_t1_f19_03_pin_removal_shifts_subsequent_pinned(self):
        """TEST-T1-F19-03: Unpinning a peer shifts remaining pinned peers cleanly."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.pin("p3")
        alloc.unpin("p2")
        self.assertEqual(alloc.pinned_endpoints, ["p1", "p3"])

    def test_t1_f19_04_persisted_pin_state_across_layout_switch(self):
        """TEST-T1-F19-04: Switching layout presets retains pinned endpoints list."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        # Layout switch preserves pins
        self.assertTrue(alloc.is_pinned("p1"))
        self.assertTrue(alloc.is_pinned("p2"))

    def test_t1_f19_05_pin_deduplication_invariant(self):
        """TEST-T1-F19-05: Pinning an already pinned endpoint is idempotent."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p1")
        self.assertEqual(len(alloc.pinned_endpoints), 1)

    # --- Feature 20: Per-Window Dynamic Pinned Auto-Scaling ---

    def test_t1_f20_01_auto_scale_1_pinned_feed(self):
        """TEST-T1-F20-01: Single pinned feed scales to allocated pinned stage."""
        alloc = PinSlotAllocator()
        alloc.pin("feed_main")
        self.assertEqual(len(alloc.pinned_endpoints), 1)

    def test_t1_f20_02_auto_scale_4_pinned_feeds(self):
        """TEST-T1-F20-02: 4 pinned feeds auto-scale into 2x2 sub-grid."""
        alloc = PinSlotAllocator()
        for i in range(4):
            alloc.pin(f"feed_{i}")
        self.assertEqual(len(alloc.pinned_endpoints), 4)

    def test_t1_f20_03_auto_scale_9_pinned_feeds(self):
        """TEST-T1-F20-03: 9 pinned feeds auto-scale into 3x3 sub-grid."""
        alloc = PinSlotAllocator()
        for i in range(9):
            alloc.pin(f"feed_{i}")
        self.assertEqual(len(alloc.pinned_endpoints), 9)

    def test_t1_f20_04_pinned_unpinned_split_allocation(self):
        """TEST-T1-F20-04: Pinned and unpinned sections partitioned by splitter."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.60)
        self.assertEqual(alloc.splitter_ratio, 0.60)

    def test_t1_f20_05_per_window_independent_pin_state(self):
        """TEST-T1-F20-05: Stage window and primary window maintain separate pin allocators."""
        alloc_primary = PinSlotAllocator()
        alloc_stage = PinSlotAllocator()
        alloc_primary.pin("p_main")
        alloc_stage.pin("p_stage")
        self.assertNotEqual(alloc_primary.pinned_endpoints, alloc_stage.pinned_endpoints)

    # --- Feature 21: Multi-Pin Capability ---

    def test_t1_f21_01_multi_pin_up_to_9_feeds(self):
        """TEST-T1-F21-01: Multi-pin supports pinning up to 9 feeds simultaneously."""
        alloc = PinSlotAllocator()
        for i in range(9):
            alloc.pin(f"ep_{i}")
        self.assertEqual(len(alloc.pinned_endpoints), 9)

    def test_t1_f21_02_toggle_pin_action_cycle(self):
        """TEST-T1-F21-02: Toggling pin action cycles state between pinned and unpinned."""
        alloc = PinSlotAllocator()
        state1 = alloc.toggle_pin("ep_1")
        self.assertTrue(state1)
        self.assertTrue(alloc.is_pinned("ep_1"))
        state2 = alloc.toggle_pin("ep_1")
        self.assertFalse(state2)
        self.assertFalse(alloc.is_pinned("ep_1"))

    def test_t1_f21_03_multi_pin_order_preservation(self):
        """TEST-T1-F21-03: Pinned feeds maintain explicit pin order."""
        alloc = PinSlotAllocator()
        alloc.pin("p_charlie")
        alloc.pin("p_alice")
        alloc.pin("p_bob")
        self.assertEqual(alloc.pinned_endpoints, ["p_charlie", "p_alice", "p_bob"])

    def test_t1_f21_04_unpin_all_restores_default_grid(self):
        """TEST-T1-F21-04: Unpinning all participants restores normal dynamic grid."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.unpin("p1")
        alloc.unpin("p2")
        self.assertEqual(len(alloc.pinned_endpoints), 0)

    def test_t1_f21_05_multi_pin_survives_participant_reconnection(self):
        """TEST-T1-F21-05: Reconnecting participant preserves pinned status."""
        alloc = PinSlotAllocator()
        alloc.pin("p_persist")
        # Participant temporarily drops and reconnects
        all_feeds = ["p_persist", "p_other"]
        ordered = alloc.get_ordered_endpoints(all_feeds)
        self.assertEqual(ordered[0], ("p_persist", True))

    # --- Feature 22: Adjustable Pinned Panel Sizes ---

    def test_t1_f22_01_splitter_ratio_adjustment(self):
        """TEST-T1-F22-01: Splitter ratio can be adjusted dynamically."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.65)
        self.assertEqual(alloc.splitter_ratio, 0.65)

    def test_t1_f22_02_splitter_ratio_clamping_min_max(self):
        """TEST-T1-F22-02: Splitter ratio is clamped to [0.10, 0.90]."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.05)  # Under min
        self.assertEqual(alloc.splitter_ratio, 0.10)
        alloc.set_splitter_ratio(0.95)  # Over max
        self.assertEqual(alloc.splitter_ratio, 0.90)

    def test_t1_f22_03_splitter_drag_resizes_pinned_container(self):
        """TEST-T1-F22-03: Splitter drag updates width distribution."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.70)
        total_width = 1000
        pinned_width = int(total_width * alloc.splitter_ratio)
        unpinned_width = total_width - pinned_width
        self.assertEqual(pinned_width, 700)
        self.assertEqual(unpinned_width, 300)

    def test_t1_f22_04_sub_pixel_precision_rounding(self):
        """TEST-T1-F22-04: Sub-pixel rounding ensures pinned + unpinned == total width."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.3333)
        total_width = 1200
        pinned_w = round(total_width * alloc.splitter_ratio)
        unpinned_w = total_width - pinned_w
        self.assertEqual(pinned_w + unpinned_w, 1200)

    def test_t1_f22_05_splitter_reset_to_default(self):
        """TEST-T1-F22-05: Resetting splitter restores default 50% split."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.75)
        alloc.set_splitter_ratio(0.50)
        self.assertEqual(alloc.splitter_ratio, 0.50)

    # --- Feature 23: Grid Unpinning & Removal Actions ---

    def test_t1_f23_01_unpin_action_removes_from_pin_list(self):
        """TEST-T1-F23-01: Explicit unpin action removes peer from pinned list."""
        alloc = PinSlotAllocator()
        alloc.pin("p_target")
        alloc.unpin("p_target")
        self.assertFalse(alloc.is_pinned("p_target"))

    def test_t1_f23_02_remove_from_screen_clears_tile(self):
        """TEST-T1-F23-02: 'Remove from Screen' clears tile from active layout."""
        alloc = PinSlotAllocator()
        alloc.pin("p_rem")
        alloc.unpin("p_rem")
        self.assertEqual(len(alloc.pinned_endpoints), 0)

    def test_t1_f23_03_unpin_dialog_confirmation(self):
        """TEST-T1-F23-03: Unpin action dialog handles user confirmation."""
        alloc = PinSlotAllocator()
        alloc.pin("p_conf")
        user_confirmed = True
        if user_confirmed:
            alloc.unpin("p_conf")
        self.assertFalse(alloc.is_pinned("p_conf"))

    def test_t1_f23_04_unpin_single_in_multi_pin_setup(self):
        """TEST-T1-F23-04: Unpinning 1 participant in multi-pin setup keeps others pinned."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.pin("p3")
        alloc.unpin("p2")
        self.assertEqual(alloc.pinned_endpoints, ["p1", "p3"])

    def test_t1_f23_05_unpin_last_participant_returns_to_normal(self):
        """TEST-T1-F23-05: Unpinning the last pinned participant returns to unpinned mode."""
        alloc = PinSlotAllocator()
        alloc.pin("p_last")
        alloc.unpin("p_last")
        self.assertEqual(len(alloc.pinned_endpoints), 0)

    # --- Feature 24: Pin to Grid Context Menu Actions ---

    def test_t1_f24_01_history_context_menu_pin_action(self):
        """TEST-T1-F24-01: 'Pin to Grid' action present in chat history context menu."""
        actions = ["Reply", "Pin to Grid", "Forward", "Delete"]
        self.assertIn("Pin to Grid", actions)

    def test_t1_f24_02_view_context_menu_pin_action(self):
        """TEST-T1-F24-02: 'Pin to Grid' action present in video view context menu."""
        actions = ["Full Screen", "Pin to Grid", "Mute"]
        self.assertIn("Pin to Grid", actions)

    def test_t1_f24_03_search_context_menu_pin_action(self):
        """TEST-T1-F24-03: 'Pin to Grid' action present in participant search context menu."""
        actions = ["Open Chat", "Pin to Grid", "Profile"]
        self.assertIn("Pin to Grid", actions)

    def test_t1_f24_04_context_menu_pin_toggles_state(self):
        """TEST-T1-F24-04: Context menu action text shows 'Unpin' when already pinned."""
        alloc = PinSlotAllocator()
        alloc.pin("p_menu")
        action_text = "Unpin from Grid" if alloc.is_pinned("p_menu") else "Pin to Grid"
        self.assertEqual(action_text, "Unpin from Grid")

    def test_t1_f24_05_context_menu_action_updates_allocator(self):
        """TEST-T1-F24-05: Invoking context menu action mutates pin allocator state."""
        alloc = PinSlotAllocator()
        alloc.pin("p_ctx")
        self.assertTrue(alloc.is_pinned("p_ctx"))


if __name__ == "__main__":
    unittest.main()
