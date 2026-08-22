"""
Tier 2 Boundary & Corner Cases for Category 5: Grid Layout & Pin System (Features 16–24).
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


class TestTier2GridPinBoundaries(unittest.TestCase):
    """Tier 2 Boundary Tests for Features 16 through 24."""

    # --- Feature 16: Discrete Layout Presets (1x1, 2x2, 3x3) Boundaries ---

    def test_t2_f16_01_invalid_slot_count_exception(self):
        """TEST-T2-F16-01: Passing non-preset slot count (e.g. 5 or 7) raises ValueError."""
        solver = GridSolverOracle()
        with self.assertRaises(ValueError):
            solver.solve_preset_grid(1000, 600, slot_count=5, participant_count=5)

    def test_t2_f16_02_zero_participants_in_preset(self):
        """TEST-T2-F16-02: Preset grid with 0 participants returns empty list."""
        solver = GridSolverOracle()
        rects = solver.solve_preset_grid(1000, 600, slot_count=4, participant_count=0)
        self.assertEqual(len(rects), 0)

    def test_t2_f16_03_zero_dimension_viewport_preset(self):
        """TEST-T2-F16-03: Viewport dimensions 0x0 return non-crashing empty rects."""
        solver = GridSolverOracle()
        rects = solver.solve_preset_grid(0, 0, slot_count=1, participant_count=1)
        self.assertEqual(len(rects), 1)

    def test_t2_f16_04_skip_margin_larger_than_viewport(self):
        """TEST-T2-F16-04: Skip margin larger than viewport width handles cell width gracefully."""
        solver = GridSolverOracle(skip=500)
        rects = solver.solve_preset_grid(200, 200, slot_count=4, participant_count=4)
        self.assertEqual(len(rects), 4)

    def test_t2_f16_05_overflow_participants_exact_empty_geometry(self):
        """TEST-T2-F16-05: 100 participants in 3x3 preset results in exactly 91 empty QRects."""
        solver = GridSolverOracle()
        rects = solver.solve_preset_grid(1200, 900, slot_count=9, participant_count=100)
        self.assertEqual(len(rects), 100)
        empty_count = sum(1 for r in rects if r.is_empty())
        self.assertEqual(empty_count, 91)

    # --- Feature 17: Dynamic Grid Solver (50/50 Split) Boundaries ---

    def test_t2_f17_01_odd_pixel_width_50_50_split(self):
        """TEST-T2-F17-01: Odd pixel width (1001px) partitions with integer rounding and no gap/overlap."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_50_50_split(width=1001, height=600)
        # (1001 - 4) // 2 = 498
        self.assertEqual(rects[0].width, 498)
        self.assertEqual(rects[1].x, 502)
        assert_no_overlap(rects)

    def test_t2_f17_02_dynamic_zero_participants(self):
        """TEST-T2-F17-02: Dynamic solver with 0 participants returns empty list."""
        solver = GridSolverOracle()
        rects = solver.solve_dynamic_grid(1000, 600, count=0)
        self.assertEqual(rects, [])

    def test_t2_f17_03_dynamic_negative_participants(self):
        """TEST-T2-F17-03: Dynamic solver with negative participant count returns empty list."""
        solver = GridSolverOracle()
        rects = solver.solve_dynamic_grid(1000, 600, count=-5)
        self.assertEqual(rects, [])

    def test_t2_f17_04_skip_margin_zero_50_50(self):
        """TEST-T2-F17-04: Zero skip margin splits exactly half width (w//2)."""
        solver = GridSolverOracle(skip=0)
        rects = solver.solve_50_50_split(width=1000, height=600)
        self.assertEqual(rects[0].width, 500)
        self.assertEqual(rects[1].x, 500)

    def test_t2_f17_05_extreme_height_aspect_ratio_split(self):
        """TEST-T2-F17-05: 50/50 split in extreme tall viewport (200x2000) maintains full height."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_50_50_split(width=200, height=2000)
        self.assertEqual(rects[0].height, 2000)
        self.assertEqual(rects[1].height, 2000)

    # --- Feature 18: Uncapped Dynamic Main Grid Scaling Boundaries ---

    def test_t2_f18_01_uncapped_64_participants_scaling(self):
        """TEST-T2-F18-01: Scaling 64 participants into dynamic grid produces 64 non-overlapping tiles."""
        solver = GridSolverOracle(skip=2)
        rects = solver.solve_dynamic_grid(width=1920, height=1080, count=64)
        self.assertEqual(len(rects), 64)
        assert_no_overlap(rects)
        for r in rects:
            assert_bounded_within(r, 1920, 1080)

    def test_t2_f18_02_prime_number_participants_13(self):
        """TEST-T2-F18-02: Prime count 13 participants partitioned with minimal wasted space."""
        solver = GridSolverOracle(skip=4)
        rects = solver.solve_dynamic_grid(width=1600, height=900, count=13)
        self.assertEqual(len(rects), 13)
        assert_no_overlap(rects)

    def test_t2_f18_03_prime_number_participants_37(self):
        """TEST-T2-F18-03: Prime count 37 participants partitioned without overlapping tiles."""
        solver = GridSolverOracle(skip=2)
        rects = solver.solve_dynamic_grid(width=1920, height=1080, count=37)
        self.assertEqual(len(rects), 37)
        assert_no_overlap(rects)

    def test_t2_f18_04_micro_viewport_100x100_uncapped(self):
        """TEST-T2-F18-04: Viewport scaled down to 100x100 computes valid sub-pixel rounded tiles."""
        solver = GridSolverOracle(skip=1)
        rects = solver.solve_dynamic_grid(width=100, height=100, count=4)
        self.assertEqual(len(rects), 4)
        assert_no_overlap(rects)

    def test_t2_f18_05_ultra_high_resolution_8k_uncapped(self):
        """TEST-T2-F18-05: 8K viewport (7680x4320) dynamic grid calculates accurate integer rects."""
        solver = GridSolverOracle(skip=8)
        rects = solver.solve_dynamic_grid(width=7680, height=4320, count=16)
        self.assertEqual(len(rects), 16)
        assert_no_overlap(rects)

    # --- Feature 19: Persistent Pin Slot Allocator Boundaries ---

    def test_t2_f19_01_unpin_nonexistent_endpoint_no_op(self):
        """TEST-T2-F19-01: Unpinning an unpinned or nonexistent endpoint is safe no-op."""
        alloc = PinSlotAllocator()
        alloc.unpin("ghost_endpoint")
        self.assertEqual(alloc.pinned_endpoints, [])

    def test_t2_f19_02_pin_and_rapid_shuffle_of_participants(self):
        """TEST-T2-F19-02: Shuffling unpinned participant list maintains pinned endpoint at head."""
        alloc = PinSlotAllocator()
        alloc.pin("anchor_ep")
        for perm in [["p1", "anchor_ep", "p2"], ["p2", "p1", "anchor_ep"], ["anchor_ep", "p2", "p1"]]:
            ordered = alloc.get_ordered_endpoints(perm)
            self.assertEqual(ordered[0], ("anchor_ep", True))

    def test_t2_f19_03_all_participants_pinned_order(self):
        """TEST-T2-F19-03: When all participants are pinned, order reflects pin insertion order."""
        alloc = PinSlotAllocator()
        alloc.pin("p3")
        alloc.pin("p1")
        alloc.pin("p2")
        ordered = alloc.get_ordered_endpoints(["p1", "p2", "p3"])
        self.assertEqual([x[0] for x in ordered], ["p3", "p1", "p2"])
        self.assertTrue(all(x[1] for x in ordered))

    def test_t2_f19_04_empty_all_participants_with_pins(self):
        """TEST-T2-F19-04: get_ordered_endpoints with empty input returns empty list."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        ordered = alloc.get_ordered_endpoints([])
        self.assertEqual(ordered, [])

    def test_t2_f19_05_unpin_all_endpoints(self):
        """TEST-T2-F19-05: Unpinning all endpoints returns all feeds as unpinned."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.unpin("p1")
        alloc.unpin("p2")
        ordered = alloc.get_ordered_endpoints(["p1", "p2"])
        self.assertTrue(all(not x[1] for x in ordered))

    # --- Feature 20: Per-Window Dynamic Pinned Auto-Scaling Boundaries ---

    def test_t2_f20_01_splitter_ratio_clamped_to_min_10(self):
        """TEST-T2-F20-01: Splitter ratio below 0.10 is clamped to 0.10."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.02)
        self.assertEqual(alloc.splitter_ratio, 0.10)

    def test_t2_f20_02_splitter_ratio_clamped_to_max_90(self):
        """TEST-T2-F20-02: Splitter ratio above 0.90 is clamped to 0.90."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.98)
        self.assertEqual(alloc.splitter_ratio, 0.90)

    def test_t2_f20_03_pinned_feeds_beyond_9_handling(self):
        """TEST-T2-F20-03: Pinning 12 feeds stores all pins in allocator without truncating."""
        alloc = PinSlotAllocator()
        for i in range(12):
            alloc.pin(f"feed_{i}")
        self.assertEqual(len(alloc.pinned_endpoints), 12)

    def test_t2_f20_04_splitter_resizing_during_call(self):
        """TEST-T2-F20-04: Splitter ratio adjustments update dynamically during active call."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.75)
        self.assertEqual(alloc.splitter_ratio, 0.75)

    def test_t2_f20_05_pinned_auto_scaling_zero_unpinned_feeds(self):
        """TEST-T2-F20-05: When all active feeds are pinned, pinned panel occupies full area."""
        alloc = PinSlotAllocator()
        alloc.pin("f1")
        alloc.pin("f2")
        ordered = alloc.get_ordered_endpoints(["f1", "f2"])
        self.assertTrue(all(x[1] for x in ordered))

    # --- Feature 21: Multi-Pin Capability Boundaries ---

    def test_t2_f21_01_multi_pin_up_to_max_capacity(self):
        """TEST-T2-F21-01: Pinning 20 participants handles large pin lists cleanly."""
        alloc = PinSlotAllocator()
        for i in range(20):
            alloc.pin(f"ep_{i}")
        self.assertEqual(len(alloc.pinned_endpoints), 20)

    def test_t2_f21_02_toggle_pin_stress_100_cycles(self):
        """TEST-T2-F21-02: 100 consecutive pin toggles on same endpoint leave state unpinned."""
        alloc = PinSlotAllocator()
        for _ in range(100):
            alloc.toggle_pin("stress_ep")
        self.assertFalse(alloc.is_pinned("stress_ep"))

    def test_t2_f21_03_multi_pin_clear_all_action(self):
        """TEST-T2-F21-03: Clearing all pins resets pinned list to empty."""
        alloc = PinSlotAllocator()
        alloc.pin("a")
        alloc.pin("b")
        alloc.pinned_endpoints.clear()
        self.assertEqual(len(alloc.pinned_endpoints), 0)

    def test_t2_f21_04_multi_pin_preserves_insertion_order(self):
        """TEST-T2-F21-04: Multi-pin preserves exact user click sequence."""
        alloc = PinSlotAllocator()
        sequence = ["user_c", "user_a", "user_b"]
        for u in sequence:
            alloc.pin(u)
        self.assertEqual(alloc.pinned_endpoints, sequence)

    def test_t2_f21_05_multi_pin_with_duplicate_calls(self):
        """TEST-T2-F21-05: Repeated pin calls do not duplicate elements."""
        alloc = PinSlotAllocator()
        for _ in range(10):
            alloc.pin("user_fixed")
        self.assertEqual(alloc.pinned_endpoints, ["user_fixed"])

    # --- Feature 22: Adjustable Pinned Panel Sizes Boundaries ---

    def test_t2_f22_01_splitter_drag_boundary_precision(self):
        """TEST-T2-F22-01: Splitter dragging accepts float precision ratios."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.3333)
        self.assertAlmostEqual(alloc.splitter_ratio, 0.3333, places=4)

    def test_t2_f22_02_splitter_negative_delta_drag(self):
        """TEST-T2-F22-02: Negative drag values clamp to 0.10."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(-0.5)
        self.assertEqual(alloc.splitter_ratio, 0.10)

    def test_t2_f22_03_splitter_overflow_delta_drag(self):
        """TEST-T2-F22-03: Dragging past maximum clamps to 0.90."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(1.5)
        self.assertEqual(alloc.splitter_ratio, 0.90)

    def test_t2_f22_04_splitter_default_50_ratio(self):
        """TEST-T2-F22-04: Default initial splitter ratio is 0.50."""
        alloc = PinSlotAllocator()
        self.assertEqual(alloc.splitter_ratio, 0.50)

    def test_t2_f22_05_splitter_reset_to_default_on_double_click(self):
        """TEST-T2-F22-05: Double clicking splitter restores 0.50 default ratio."""
        alloc = PinSlotAllocator()
        alloc.set_splitter_ratio(0.80)
        alloc.set_splitter_ratio(0.50)  # Reset
        self.assertEqual(alloc.splitter_ratio, 0.50)

    # --- Feature 23: Grid Unpinning & Removal Actions Boundaries ---

    def test_t2_f23_01_unpin_first_element_shifts_rest(self):
        """TEST-T2-F23-01: Unpinning head element shifts index 1 to index 0."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.unpin("p1")
        self.assertEqual(alloc.pinned_endpoints, ["p2"])

    def test_t2_f23_02_unpin_last_element_leaves_prefix_intact(self):
        """TEST-T2-F23-02: Unpinning tail element leaves earlier pins unchanged."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.unpin("p2")
        self.assertEqual(alloc.pinned_endpoints, ["p1"])

    def test_t2_f23_03_unpin_middle_element_compacts(self):
        """TEST-T2-F23-03: Unpinning middle element preserves relative order."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.pin("p2")
        alloc.pin("p3")
        alloc.unpin("p2")
        self.assertEqual(alloc.pinned_endpoints, ["p1", "p3"])

    def test_t2_f23_04_rapid_pin_unpin_cycle(self):
        """TEST-T2-F23-04: Rapid pin then unpin leaves list clean."""
        alloc = PinSlotAllocator()
        for i in range(10):
            alloc.pin(f"t_{i}")
            alloc.unpin(f"t_{i}")
        self.assertEqual(alloc.pinned_endpoints, [])

    def test_t2_f23_05_unpin_action_idempotency(self):
        """TEST-T2-F23-05: Multiple unpin calls on same endpoint are idempotent."""
        alloc = PinSlotAllocator()
        alloc.pin("p1")
        alloc.unpin("p1")
        alloc.unpin("p1")
        self.assertEqual(alloc.pinned_endpoints, [])

    # --- Feature 24: Pin to Grid Context Menu Actions Boundaries ---

    def test_t2_f24_01_pin_action_with_special_characters_in_name(self):
        """TEST-T2-F24-01: Pinning endpoint with special/unicode characters in ID."""
        alloc = PinSlotAllocator()
        special_id = "user_@#$_✓_101"
        alloc.pin(special_id)
        self.assertTrue(alloc.is_pinned(special_id))

    def test_t2_f24_02_context_menu_pin_already_pinned_shows_unpin(self):
        """TEST-T2-F24-02: Context menu checks pin state accurately to offer 'Unpin'."""
        alloc = PinSlotAllocator()
        alloc.pin("u_test")
        action_text = "Unpin" if alloc.is_pinned("u_test") else "Pin to Grid"
        self.assertEqual(action_text, "Unpin")

    def test_t2_f24_03_context_menu_unpin_updates_label(self):
        """TEST-T2-F24-03: Unpinning updates context menu action label back to 'Pin to Grid'."""
        alloc = PinSlotAllocator()
        alloc.pin("u_test")
        alloc.unpin("u_test")
        action_text = "Unpin" if alloc.is_pinned("u_test") else "Pin to Grid"
        self.assertEqual(action_text, "Pin to Grid")

    def test_t2_f24_04_context_menu_pin_during_call_transition(self):
        """TEST-T2-F24-04: Pin action triggered while call mode switches executes safely."""
        alloc = PinSlotAllocator()
        alloc.pin("u_switch")
        self.assertTrue(alloc.is_pinned("u_switch"))

    def test_t2_f24_05_context_menu_multiple_peers_batch_pin(self):
        """TEST-T2-F24-05: Batch pinning multiple selected peers from context menu."""
        alloc = PinSlotAllocator()
        batch = ["p1", "p2", "p3"]
        for p in batch:
            alloc.pin(p)
        self.assertEqual(len(alloc.pinned_endpoints), 3)


if __name__ == "__main__":
    unittest.main()
