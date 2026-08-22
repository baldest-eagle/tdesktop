"""
Adversarial Stress Testing & Empirical Challenge Suite for Telegram Desktop Fork.
Directly executes stress harnesses, mathematical oracles, and boundary verification.
"""

import math
import os
import random
import sys
import unittest
from typing import List, Dict, Any, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.e2e.framework import (
    GridSolverOracle,
    PinSlotAllocator,
    MtprotoMock,
    DcSessionPool,
    SQLiteStorageMock,
    TdataStreamMock,
    CoreSettingsMock,
    WebRtcAudioJitterOracle,
    RichTasksOracle,
    CallSimulator,
    DisplayCoordinatorMock,
    GeometryRect,
    assert_rect_equal,
    assert_no_overlap,
    assert_bounded_within,
    assert_pragma_executed,
    assert_rpc_suppressed,
    assert_rpc_dispatched,
    assert_zero_audio_packets,
)


class TestAdversarialGridSolver(unittest.TestCase):
    """Empirical Stress Testing for Grid Layout Solver Oracle across 1..64 counts and extreme aspect ratios."""

    def setUp(self):
        self.solver = GridSolverOracle(skip=4)

    def test_stress_participant_counts_1_to_64_standard_viewport(self):
        """Stress-test all participant counts from 1 to 64 in 1920x1080 viewport."""
        viewport_w, viewport_h = 1920, 1080
        for count in range(1, 65):
            rects = self.solver.solve_dynamic_grid(viewport_w, viewport_h, count)
            self.assertEqual(len(rects), count, f"Failed count length check for count={count}")
            assert_no_overlap(rects, msg=f"Overlap detected at count={count}")
            for i, r in enumerate(rects):
                self.assertTrue(r.is_valid(), f"Invalid rect dimensions at count={count}, tile={i}: {r}")
                assert_bounded_within(r, viewport_w, viewport_h, msg=f"Out of bounds at count={count}, tile={i}")

    def test_stress_boundary_aspect_ratios_ultrawide_and_vertical(self):
        """Stress-test extreme boundary viewports: 32:9, 21:9, 9:16, 9:32, 1:1, 10:1, 1:10."""
        boundary_viewports = [
            (3840, 1080, "32:9 Ultrawide"),
            (5120, 1440, "32:9 Super Ultrawide"),
            (2560, 1080, "21:9 Ultrawide"),
            (10000, 1000, "10:1 Panoramic Banner"),
            (1080, 1920, "9:16 Vertical Mobile"),
            (1080, 3840, "9:32 Ultra-tall Mobile"),
            (500, 5000, "1:10 Ribbon"),
            (1000, 1000, "1:1 Square"),
            (2000, 2000, "1:1 Large Square"),
            (100, 100, "1:1 Micro Viewport"),
            (7680, 4320, "16:9 8K UHD"),
        ]

        test_counts = [1, 2, 3, 4, 5, 7, 8, 9, 13, 16, 25, 32, 37, 49, 64]

        for w, h, desc in boundary_viewports:
            for count in test_counts:
                rects = self.solver.solve_dynamic_grid(w, h, count)
                self.assertEqual(len(rects), count, f"Failed count for {desc} (w={w}, h={h}, count={count})")
                assert_no_overlap(rects, msg=f"Overlap in {desc} (count={count})")
                for r in rects:
                    self.assertTrue(r.is_valid(), f"Zero/negative area in {desc} (count={count}): {r}")
                    assert_bounded_within(r, w, h, msg=f"Out of bounds in {desc} (count={count})")

    def test_stress_varying_skip_margins(self):
        """Stress-test grid solver with various skip margins (0, 1, 2, 6, 8, 16)."""
        w, h = 1600, 900
        for skip in [0, 1, 2, 6, 8, 16]:
            custom_solver = GridSolverOracle(skip=skip)
            for count in [1, 2, 4, 6, 9, 16, 25, 36, 49, 64]:
                rects = custom_solver.solve_dynamic_grid(w, h, count)
                self.assertEqual(len(rects), count)
                assert_no_overlap(rects, msg=f"Overlap with skip={skip}, count={count}")
                for r in rects:
                    assert_bounded_within(r, w, h)

    def test_50_50_split_mathematical_precision(self):
        """Stress-test 50/50 split across odd and even viewport widths."""
        for width in range(100, 2000, 13):
            for height in [600, 720, 1080]:
                for skip in [0, 2, 4, 6]:
                    solver = GridSolverOracle(skip=skip)
                    rects = solver.solve_50_50_split(width, height)
                    self.assertEqual(len(rects), 2)
                    assert_no_overlap(rects)
                    # Width parity check
                    w_expected = (width - skip) // 2
                    self.assertEqual(rects[0].width, w_expected)
                    self.assertEqual(rects[1].width, w_expected)
                    self.assertEqual(rects[0].x, 0)
                    self.assertEqual(rects[1].x, w_expected + skip)
                    self.assertEqual(rects[0].height, height)
                    self.assertEqual(rects[1].height, height)


class TestAdversarialMtprotoPool(unittest.TestCase):
    """Empirical Stress Testing for MTProto Multi-Session Pool & Ghost Mode."""

    def test_concurrent_chunk_request_burst_and_pool_scaling(self):
        """Simulate 300 concurrent chunk downloads and verify expansion to 16 sessions."""
        pool = DcSessionPool(dc_id=2, start_sessions=4, max_sessions=16)
        self.assertEqual(len(pool.sessions), 4)

        chunk_size = 128 * 1024  # 128 KB
        total_chunks = 300

        # Dispatch 300 chunk requests
        dispatched_assignments = []
        for i in range(total_chunks):
            idx = pool.choose_session_index()
            pool.sessions[idx].requested_bytes += chunk_size
            dispatched_assignments.append(idx)

        # Verify load balancing distributed requests across all initial sessions
        initial_loads = [pool.sessions[s].requested_bytes for s in range(4)]
        self.assertTrue(all(load > 0 for load in initial_loads))

        # Complete requests in simulated arrival order
        for req_idx, s_idx in enumerate(dispatched_assignments):
            pool.request_succeeded(s_idx, chunk_size)

        # Pool must have dynamically scaled up to max_sessions (16)
        self.assertEqual(len(pool.sessions), 16)
        # All requested bytes must be resolved back to 0
        self.assertTrue(all(s.requested_bytes == 0 for s in pool.sessions))

    def test_fault_injection_timeout_burst_and_pool_shrinking(self):
        """Simulate network timeouts and verify controlled shrinking down to 4 sessions."""
        pool = DcSessionPool(dc_id=2, start_sessions=4, max_sessions=16)

        # Grow pool to 10 sessions
        for i in range(18):
            s_idx = pool.choose_session_index()
            pool.request_succeeded(s_idx, 128 * 1024)
        self.assertGreater(len(pool.sessions), 4)
        peak_sessions = len(pool.sessions)

        # Inject 30 successive timeouts
        for _ in range(30):
            pool.request_failed_timeout(session_idx=0)

        # Pool must have shrunk back to exactly start_sessions (4) and never below
        self.assertEqual(len(pool.sessions), 4)
        self.assertGreater(pool.session_remove_times, 0)

    def test_ghost_mode_read_receipt_suppression_invariant(self):
        """Stress-test Ghost Mode across 100 mixed peer read requests."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)

        for peer_id in range(1000, 1100):
            is_channel = (peer_id % 2 == 0)
            mock.local_unread_counts[peer_id] = 5
            dispatched = mock.send_read_request(peer_id, max_id=50, is_channel=is_channel)
            self.assertFalse(dispatched, "send_read_request should return False under Ghost Mode")
            # Local unread cleared for UI presentation
            self.assertEqual(mock.local_unread_counts[peer_id], 0)

        # Invariant: ZERO messages.readHistory or channels.readHistory RPCs dispatched to server
        assert_rpc_suppressed(mock, "messages.readHistory")
        assert_rpc_suppressed(mock, "channels.readHistory")
        self.assertEqual(len(mock.dispatched_rpcs), 0)


class TestAdversarialSqliteAndTdata(unittest.TestCase):
    """Empirical Stress Testing for SQLite PRAGMAs and Binary Serialization."""

    def test_sqlite_pragma_c1_configuration_invariants(self):
        """Verify C1 PRAGMA optimizations and default fallback paths."""
        storage = SQLiteStorageMock()
        storage.initialize_database(enable_optimizations=True)

        assert_pragma_executed(storage, "journal_mode", "WAL")
        assert_pragma_executed(storage, "mmap_size", 268435456)
        assert_pragma_executed(storage, "synchronous", "NORMAL")
        assert_pragma_executed(storage, "cache_size", -64000)
        assert_pragma_executed(storage, "temp_store", "MEMORY")

        # Verify fallback path
        storage_fallback = SQLiteStorageMock()
        storage_fallback.initialize_database(enable_optimizations=False)
        self.assertEqual(storage_fallback.get_pragma("journal_mode"), "DELETE")
        self.assertEqual(storage_fallback.get_pragma("synchronous"), "FULL")

    def test_tdata_stream_backwards_compatibility_and_fuzzing(self):
        """Verify binary stream append-at-end rule and legacy fallback safety."""
        # 1. Legacy stream without ghost_mode field
        legacy_stream = TdataStreamMock()
        legacy_stream.write_int32(1280)  # window_width
        legacy_stream.write_int32(800)   # window_height
        # No ghostMode written (legacy client)

        settings = CoreSettingsMock()
        settings.deserialize(legacy_stream)
        self.assertEqual(settings._window_width, 1280)
        self.assertEqual(settings._window_height, 800)
        self.assertFalse(settings.ghost_mode, "Legacy stream must default ghost_mode to False")

        # 2. Modern stream with ghost_mode = True
        modern_stream = TdataStreamMock()
        settings_save = CoreSettingsMock()
        settings_save.set_ghost_mode(True)
        settings_save.serialize(modern_stream)

        settings_load = CoreSettingsMock()
        settings_load.deserialize(modern_stream)
        self.assertTrue(settings_load.ghost_mode, "Modern stream must preserve ghost_mode=True")

        # 3. Stream fuzzing: truncated buffer handles EOF cleanly
        bad_stream = TdataStreamMock()
        bad_stream.write_int32(100)  # incomplete data
        with self.assertRaises(EOFError):
            bad_settings = CoreSettingsMock()
            bad_settings.deserialize(bad_stream)


class TestAdversarialWebRtcJitter(unittest.TestCase):
    """Empirical Stress Testing for WebRTC Playout Delay & Jitter Clamping."""

    def test_continuous_clamping_under_10000_erratic_packets(self):
        """Stress-test 10,000 audio packets with random inter-arrival jitter spikes."""
        oracle = WebRtcAudioJitterOracle(min_playout_delay_ms=50.0, max_playout_delay_ms=120.0)
        rng = random.Random(42)

        arrival_cursor = 0.0
        for seq in range(10000):
            timestamp_ms = seq * 20.0
            # Inject erratic network transit variance [-15ms, +180ms]
            jitter_noise = rng.uniform(-15.0, 180.0)
            arrival_cursor += 20.0 + jitter_noise

            oracle.push_audio_packet(seq, timestamp_ms, arrival_cursor)
            drained = oracle.drain_playout_packet()
            self.assertIsNotNone(drained)
            self.assertEqual(drained["seq_num"], seq)

            # Playout delay MUST strictly obey [50.0, 120.0] invariant
            self.assertGreaterEqual(oracle.playout_delay_ms, 50.0 - 1e-5)
            self.assertLessEqual(oracle.playout_delay_ms, 120.0 + 1e-5)

    def test_fast_accelerate_activation_and_recovery_cycle(self):
        """Verify fast accelerate triggers when jitter > 80ms and deactivates on recovery."""
        oracle = WebRtcAudioJitterOracle(min_playout_delay_ms=50.0, max_playout_delay_ms=120.0)

        # Baseline steady state
        oracle.push_audio_packet(1, 0.0, 0.0)
        oracle.push_audio_packet(2, 20.0, 20.0)
        self.assertFalse(oracle.fast_accelerate_active)

        # Inject massive jitter burst (300ms packet arrival spike)
        for i in range(3, 15):
            oracle.push_audio_packet(i, i * 20.0, i * 20.0 + (300.0 if i % 2 == 1 else 0.0))

        self.assertTrue(oracle.current_jitter_ms > 80.0)
        self.assertTrue(oracle.fast_accelerate_active)
        self.assertLessEqual(oracle.playout_delay_ms, 120.0)

        # Recover to smooth steady arrivals
        for i in range(15, 120):
            oracle.push_audio_packet(i, i * 20.0, 1000.0 + i * 20.0)

        self.assertFalse(oracle.fast_accelerate_active)
        self.assertAlmostEqual(oracle.playout_delay_ms, 50.0, places=1)


class TestAdversarialRichTasks(unittest.TestCase):
    """Empirical Stress Testing for Rich Tasks Debounce, Optimistic UI, and RPC Rollback."""

    def test_dirty_rescheduling_debounce_burst(self):
        """Simulate rapid burst of 50 item toggles and verify timer rescheduling."""
        md = "\n".join([f"- [ ] Step {i}" for i in range(10)])
        oracle = RichTasksOracle(message_id=999, initial_markdown=md)

        # Toggle items every 100ms for 50 steps (total 5000ms duration)
        for i in range(50):
            target_idx = i % 10
            oracle.toggle_item(target_idx)
            oracle.advance_time(100)
            # Debounce timer should continuously reschedule and NEVER commit prematurely
            self.assertTrue(oracle.debounce_timer_active)
            self.assertEqual(oracle.pending_save_dispatches, 0)

        # Now let timer run out completely (1000ms idle)
        res = oracle.advance_time(1000)
        self.assertIsNotNone(res)
        self.assertFalse(oracle.debounce_timer_active)
        # Exactly 1 consolidated batch RPC dispatch
        self.assertEqual(oracle.pending_save_dispatches, 1)

    def test_optimistic_mutation_and_network_rollback(self):
        """Verify optimistic state update and full state restoration on RPC rollback."""
        initial_md = "- [ ] Write tests\n- [ ] Run benchmark\n- [x] Initial review"
        oracle = RichTasksOracle(message_id=1001, initial_markdown=initial_md)

        # Optimistic user toggle
        oracle.toggle_item(0)  # Check "Write tests"
        oracle.toggle_item(2)  # Uncheck "Initial review"
        self.assertTrue(oracle.items[0].completed)
        self.assertFalse(oracle.items[2].completed)

        # Simulate network error rollback
        oracle.rollback_on_error()

        # Invariant: Restores exact original server markdown and items
        self.assertEqual(oracle.current_markdown, initial_md)
        self.assertFalse(oracle.items[0].completed)
        self.assertTrue(oracle.items[2].completed)
        self.assertFalse(oracle.debounce_timer_active)


class TestAdversarialHighScaleParticipantStress(unittest.TestCase):
    """Empirical Probe 1: High-Scale Participant Stress (100+ to 500+ participants in grid solver and sidebar sorting)."""

    def setUp(self):
        self.solver = GridSolverOracle(skip=4)

    def test_grid_solver_scale_100_to_500_participants(self):
        """Stress-test dynamic grid solver scaling up to 500 participants across diverse viewport resolutions."""
        viewports = [
            (1920, 1080, "1080p FHD"),
            (3840, 2160, "4K UHD"),
            (7680, 4320, "8K UHD"),
            (5120, 1440, "32:9 Super Ultrawide"),
            (1080, 1920, "9:16 Portrait"),
        ]
        test_participant_scales = [100, 150, 200, 300, 500]

        for vw, vh, label in viewports:
            for count in test_participant_scales:
                rects = self.solver.solve_dynamic_grid(vw, vh, count)
                self.assertEqual(len(rects), count, f"Tile count mismatch for {count} in {label}")
                assert_no_overlap(rects, msg=f"Overlap at {count} in {label}")
                for i, r in enumerate(rects):
                    self.assertTrue(r.is_valid(), f"Invalid rect at count={count}, tile={i} in {label}: {r}")
                    assert_bounded_within(r, vw, vh, msg=f"Out-of-bounds tile {i} at count={count} in {label}")

    def test_sidebar_sorting_and_search_scale_500_participants(self):
        """Stress-test sidebar sorting, Unicode normalization, case-insensitivity, and search filtering at 500+ scale."""
        sim = CallSimulator()
        rng = random.Random(1337)
        names = [
            "Alice", "bob", "Charlie", "DANIEL", "david", "Eve", "Frank",
            "Élodie", "Ömer", "Владимир", "Анна", "田中", "佐藤", "🚀 Star", "🔥 Flame"
        ]

        # Populate 500 participants with varying entry times and names
        for i in range(500):
            base_name = names[i % len(names)]
            unique_name = f"{base_name} {i:03d}"
            entry_time = 1000.0 + rng.uniform(0, 5000)
            sim.add_participant(f"ep_{i}", 10000 + i, unique_name, entry_time=entry_time)

        # 1. Verify Alphabetical Sorting Stability
        sorted_alpha = sim.get_participants_alphabetical()
        self.assertEqual(len(sorted_alpha), 500)
        for j in range(len(sorted_alpha) - 1):
            name_a = sorted_alpha[j].name.lower()
            name_b = sorted_alpha[j + 1].name.lower()
            self.assertLessEqual(name_a, name_b, f"Alphabetical sorting violation: '{name_a}' > '{name_b}'")

        # 2. Verify Chronological Sorting Stability
        sorted_chrono = sim.get_participants_chronological()
        self.assertEqual(len(sorted_chrono), 500)
        for j in range(len(sorted_chrono) - 1):
            self.assertLessEqual(sorted_chrono[j].entry_time, sorted_chrono[j + 1].entry_time)

        # 3. Verify Search Filtering under High Scale
        # Filter by Unicode name "Élodie"
        res_unicode = sim.filter_participants("élodie")
        self.assertGreater(len(res_unicode), 0)
        self.assertTrue(all("élodie" in p.name.lower() for p in res_unicode))

        # Filter by Peer ID substring
        res_peer = sim.filter_participants("1005")
        self.assertGreater(len(res_peer), 0)
        self.assertTrue(all("1005" in str(p.peer_id) or "1005" in p.name for p in res_peer))

        # Filter by Empty Query returns all 500 alphabetical
        res_all = sim.filter_participants("")
        self.assertEqual(len(res_all), 500)
        self.assertEqual([p.endpoint_id for p in res_all], [p.endpoint_id for p in sorted_alpha])


class TestAdversarialActiveSpeakerHysteresis(unittest.TestCase):
    """Empirical Probe 2: Active-Speaker Hysteresis under rapid switching and audio level fluctuations."""

    def test_rapid_speaker_switching_hysteresis_damping(self):
        """Simulate 1,000 rapid speaker switch attempts within 300ms damping window."""
        sim = CallSimulator()
        sim.add_participant("s_a", 101, "Speaker A")
        sim.add_participant("s_b", 102, "Speaker B")
        sim.add_participant("s_c", 103, "Speaker C")

        # Initial speaker assignment at t=1.0s
        sim.set_active_speaker("s_a", now=1.000)
        self.assertEqual(sim.active_speaker_id, "s_a")

        # 1,000 rapid switch attempts between t=1.001s and t=1.299s (all within <300ms damping window)
        for step in range(1, 1000):
            t = 1.000 + (step * 0.00029)  # Max t = 1.2897s < 1.300s
            target = "s_b" if step % 2 == 0 else "s_c"
            switched = sim.set_active_speaker(target, now=t)
            self.assertFalse(switched, f"Hysteresis damping failed at t={t:.4f}s for speaker {target}")
            self.assertEqual(sim.active_speaker_id, "s_a", "Active speaker must remain locked to s_a")

        # Legitimate switch after hysteresis window expires at t=1.301s (>300ms)
        switched_legit = sim.set_active_speaker("s_b", now=1.301)
        self.assertTrue(switched_legit, "Switch to s_b should succeed after 300ms hysteresis window")
        self.assertEqual(sim.active_speaker_id, "s_b")

    def test_audio_level_fluctuations_and_silence_preservation(self):
        """Verify speaker selection under erratic volume spikes and preservation of active speaker during silence."""
        sim = CallSimulator()
        for i in range(10):
            sim.add_participant(f"p_{i}", 200 + i, f"Participant {i}")

        current_time = 10.0
        # Speaker 3 talks loudly
        sim.endpoints["p_3"].audio_level = 0.95
        sim.set_active_speaker("p_3", now=current_time)
        self.assertEqual(sim.active_speaker_id, "p_3")

        # Noise fluctuations across others for 200ms
        for dt in [0.05, 0.10, 0.15, 0.20]:
            sim.endpoints["p_5"].audio_level = 0.98  # Brief spike
            switched = sim.set_active_speaker("p_5", now=current_time + dt)
            self.assertFalse(switched, "Noise spike during damping window must not switch speaker")
            self.assertEqual(sim.active_speaker_id, "p_3")

        # Silence falls across entire room (all audio levels drop to 0.0)
        for ep in sim.endpoints.values():
            ep.audio_level = 0.0

        # Invariant: Silence preserves last active speaker
        self.assertEqual(sim.active_speaker_id, "p_3")


class TestAdversarialMultiDisplayRouter(unittest.TestCase):
    """Empirical Probe 3: Multi-Display Router Robustness under dynamic secondary display connect/disconnect."""

    def test_dynamic_display_connect_disconnect_and_fallback(self):
        """Simulate multi-monitor topology changes, role assignment, and graceful pinned feed fallback."""
        coordinator = DisplayCoordinatorMock()
        # Default topology: Screen 1 (Primary), Screen 2 (StageGrid)
        self.assertEqual(len(coordinator.screens), 2)
        self.assertEqual(coordinator.get_primary_screen().screen_id, 1)

        # Pin key presentation feed to Screen 2
        coordinator.pin_feed_to_screen(screen_id=2, feed_id="deck_feed_alpha")
        self.assertEqual(coordinator.screens[2].pinned_feed_id, "deck_feed_alpha")
        self.assertIsNone(coordinator.screens[1].pinned_feed_id)

        # Connect Screen 3 (ChatStation)
        coordinator.add_screen(3, "Monitor 3 (Chat)", GeometryRect(3840, 0, 1920, 1080), is_primary=False)
        coordinator.assign_role(3, "ChatStation")
        self.assertEqual(coordinator.screens[3].assigned_role, "ChatStation")

        # Unplug Screen 2 dynamically (e.g. HDMI cable disconnected)
        removed_screen = coordinator.remove_screen(screen_id=2)
        self.assertIsNotNone(removed_screen)
        self.assertEqual(removed_screen.screen_id, 2)
        self.assertNotIn(2, coordinator.screens)

        # Invariant: Pinned feed "deck_feed_alpha" must gracefully fallback to Primary Screen (1)
        primary = coordinator.get_primary_screen()
        self.assertEqual(primary.pinned_feed_id, "deck_feed_alpha", "Feed must fallback to primary display on disconnect")

    def test_rapid_connect_disconnect_cycling(self):
        """Stress-test 100 consecutive rapid display plug/unplug cycles."""
        coordinator = DisplayCoordinatorMock()
        for cycle in range(100):
            sid = 10 + cycle
            coordinator.add_screen(sid, f"TempScreen {sid}", GeometryRect(1920, 0, 1920, 1080))
            coordinator.assign_role(sid, "StageGrid")
            coordinator.pin_feed_to_screen(sid, f"feed_{cycle}")
            coordinator.remove_screen(sid)

        # Primary screen remains intact and stable
        primary = coordinator.get_primary_screen()
        self.assertIsNotNone(primary)
        self.assertEqual(primary.screen_id, 1)


class TestAdversarialListenOnlyZeroMicGuarantee(unittest.TestCase):
    """Empirical Probe 4: Listen-Only Mode audio capture zero-mic guarantee under illegal client state injection."""

    def test_hostile_illegal_state_injection_zero_mic(self):
        """Forcefully inject illegal state mutations and verify zero outgoing audio packets."""
        sim = CallSimulator(is_listen_only=True)
        self.assertTrue(sim.is_listen_only)
        self.assertFalse(sim.mic_button_visible)
        assert_zero_audio_packets(sim)

        # Attack Scenario 1: Maliciously set mic_muted = False
        sim.mic_muted = False
        # Attempt 1,000 raw audio packet transmissions
        for i in range(1000):
            emitted = sim.emit_microphone_packet(b"\x00\x01\x02\x03" * 40)
            self.assertFalse(emitted, f"Audio packet {i} emitted despite listen-only mode!")

        # Attack Scenario 2: Call set_listen_only(True) repeatedly and try unmuting
        sim.set_listen_only(True)
        sim.mic_muted = False
        for i in range(5000):
            emitted = sim.emit_microphone_packet(b"\xFF\xFE\xFD" * 50)
            self.assertFalse(emitted)

        # Invariant: Absolute zero audio packets emitted under all hostile injections
        assert_zero_audio_packets(sim)

    def test_webrtc_sdp_recvonly_invariant(self):
        """Verify WebRTC SDP negotiation strictly adheres to recvonly in listen-only mode."""
        sim = CallSimulator(is_listen_only=True)
        sdp = sim.generate_sdp()
        self.assertIn("a=recvonly", sdp)
        self.assertNotIn("a=sendrecv", sdp)

        # Regular call SDP negotiation
        sim_normal = CallSimulator(is_listen_only=False)
        sdp_normal = sim_normal.generate_sdp()
        self.assertIn("a=sendrecv", sdp_normal)


class TestAdversarialRichTasksConcurrency(unittest.TestCase):
    """Empirical Probe 5: Rich Tasks Checkbox Mutation Concurrency, Debounce Rescheduling, and Atomic Rollback."""

    def test_high_concurrency_checkbox_mutations(self):
        """Simulate 500 out-of-order checkbox mutations across 100 items within debounce interval."""
        md_tasks = "\n".join([f"- [ ] Task Item {i:03d}" for i in range(100)])
        oracle = RichTasksOracle(message_id=5555, initial_markdown=md_tasks)
        self.assertEqual(len(oracle.items), 100)

        rng = random.Random(42)
        # Execute 500 rapid mutations
        for op in range(500):
            idx = rng.randint(0, 99)
            oracle.toggle_item(idx)
            # Advance small time delta (20ms) -> well below 1000ms debounce
            oracle.advance_time(20)
            self.assertTrue(oracle.debounce_timer_active)
            self.assertEqual(oracle.pending_save_dispatches, 0, "Premature dispatch occurred during mutation burst!")

        # Let full 1000ms idle elapsed
        res = oracle.advance_time(1000)
        self.assertIsNotNone(res)
        self.assertFalse(oracle.debounce_timer_active)
        # Exactly 1 consolidated batch RPC
        self.assertEqual(oracle.pending_save_dispatches, 1)

    def test_atomic_rollback_on_server_error(self):
        """Verify atomic restoration to last confirmed server state without markdown corruption."""
        original_md = "- [ ] Spec Design\n- [x] Unit Tests\n- [ ] Code Review"
        oracle = RichTasksOracle(message_id=7777, initial_markdown=original_md)

        # Mutate local state
        oracle.toggle_item(0)  # Check 0
        oracle.toggle_item(1)  # Uncheck 1
        oracle.toggle_item(2)  # Check 2
        self.assertTrue(oracle.items[0].completed)
        self.assertFalse(oracle.items[1].completed)
        self.assertTrue(oracle.items[2].completed)

        # Simulate network error / server rejection
        oracle.rollback_on_error()

        # Invariant: Complete atomic restoration to original server markdown
        self.assertEqual(oracle.current_markdown, original_md)
        self.assertFalse(oracle.items[0].completed)
        self.assertTrue(oracle.items[1].completed)
        self.assertFalse(oracle.items[2].completed)
        self.assertFalse(oracle.debounce_timer_active)


if __name__ == "__main__":
    unittest.main()

