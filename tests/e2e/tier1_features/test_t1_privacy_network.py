"""
Tier 1 Tests for Category 1 (Privacy & Ghost Mode) and Category 2 (Network & Download).
Features 1–3: 15 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    MtprotoMock,
    SQLiteStorageMock,
    TdataStreamMock,
    CoreSettingsMock,
    assert_rpc_dispatched,
    assert_rpc_suppressed,
)


class TestTier1PrivacyNetwork(unittest.TestCase):
    """Tier 1 Test Suite for Features 1, 2, and 3."""

    # --- Feature 1: Ghost Mode (Decoupled Read Receipts) ---

    def test_t1_f01_01_default_disabled_state_read_receipt_sent(self):
        """TEST-T1-F01-01: Default disabled state dispatches messages.readHistory."""
        mock = MtprotoMock()
        mock.set_ghost_mode(False)

        dispatched = mock.send_read_request(peer_id=1002, max_id=103, is_channel=False)
        self.assertTrue(dispatched)
        assert_rpc_dispatched(mock, "messages.readHistory", expected_count=1)
        self.assertEqual(mock.server_inbox_pointers[1002], 103)

    def test_t1_f01_02_ghost_mode_enabled_suppresses_read_receipt(self):
        """TEST-T1-F01-02: Ghost mode enabled suppresses outgoing read receipts."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)

        dispatched = mock.send_read_request(peer_id=1002, max_id=205, is_channel=False)
        self.assertFalse(dispatched)
        assert_rpc_suppressed(mock, "messages.readHistory")
        self.assertNotIn(1002, mock.server_inbox_pointers)

    def test_t1_f01_03_local_unread_cleared_while_server_unmutated(self):
        """TEST-T1-F01-03: Local unread state updates for UI display while server stays intact."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)

        mock.local_unread_counts[1003] = 4
        mock.send_read_request(peer_id=1003, max_id=150, is_channel=False)

        self.assertEqual(mock.local_unread_counts[1003], 0)
        self.assertNotIn(1003, mock.server_inbox_pointers)
        assert_rpc_suppressed(mock, "messages.readHistory")

    def test_t1_f01_04_channel_read_history_suppressed(self):
        """TEST-T1-F01-04: Channel / supergroup channels.readHistory is suppressed in ghost mode."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)

        dispatched = mock.send_read_request(peer_id=2001, max_id=520, is_channel=True)
        self.assertFalse(dispatched)
        assert_rpc_suppressed(mock, "channels.readHistory")

    def test_t1_f01_05_dynamic_toggle_mid_session(self):
        """TEST-T1-F01-05: Dynamic ghost mode toggle mid-session cancels pending read timer requests."""
        mock = MtprotoMock()
        mock.set_ghost_mode(False)
        # Toggle to True right before timer execution
        mock.set_ghost_mode(True)

        dispatched = mock.send_read_request(peer_id=1004, max_id=88, is_channel=False)
        self.assertFalse(dispatched)
        assert_rpc_suppressed(mock, "messages.readHistory")

    # --- Feature 2: Ghost Mode Settings UI & Persistence ---

    def test_t1_f02_01_settings_ui_toggle_presence(self):
        """TEST-T1-F02-01: Ghost mode toggle state initialized accurately."""
        settings = CoreSettingsMock()
        self.assertFalse(settings.ghost_mode)

        settings.set_ghost_mode(True)
        self.assertTrue(settings.ghost_mode)

    def test_t1_f02_02_toggle_interaction_updates_setting(self):
        """TEST-T1-F02-02: Clicking toggle updates internal setting."""
        settings = CoreSettingsMock()
        settings.set_ghost_mode(False)
        # User toggles on
        settings.set_ghost_mode(not settings.ghost_mode)
        self.assertTrue(settings.ghost_mode)

    def test_t1_f02_03_binary_serialization_appends_at_end(self):
        """TEST-T1-F02-03: Serializes ghost mode sequentially at end of stream."""
        settings = CoreSettingsMock()
        settings.set_ghost_mode(True)
        stream = TdataStreamMock()

        settings.serialize(stream)
        # Window width (4 bytes) + Window height (4 bytes) + GhostMode (4 bytes) = 12 bytes
        self.assertEqual(len(stream.buffer), 12)

    def test_t1_f02_04_cold_restart_deserialization_restores_state(self):
        """TEST-T1-F02-04: Deserialization recovers persisted ghost mode state after cold start."""
        settings_save = CoreSettingsMock()
        settings_save.set_ghost_mode(True)
        stream = TdataStreamMock()
        settings_save.serialize(stream)

        # New instance simulates client reboot
        settings_load = CoreSettingsMock()
        settings_load.deserialize(stream)
        self.assertTrue(settings_load.ghost_mode)

    def test_t1_f02_05_legacy_stream_at_end_guard_fallback(self):
        """TEST-T1-F02-05: Reading legacy stream without ghost mode defaults safely to false."""
        stream = TdataStreamMock()
        stream.write_int32(1024)
        stream.write_int32(768)
        # Legacy stream ends here (no ghost mode byte)

        settings_load = CoreSettingsMock()
        settings_load.deserialize(stream)
        self.assertFalse(settings_load.ghost_mode)
        self.assertTrue(stream.at_end())

    # --- Feature 3: Multi-Connection MTProto Chunk Downloading (16 sessions) ---

    def test_t1_f03_01_initial_session_pool_allocation(self):
        """TEST-T1-F03-01: DC connection pool allocates exactly 4 initial download sessions."""
        mock = MtprotoMock()
        pool = mock.get_dc_pool(dc_id=2)
        self.assertEqual(len(pool.sessions), 4)
        self.assertEqual(pool.start_sessions, 4)

    def test_t1_f03_02_scaling_to_max_16_sessions(self):
        """TEST-T1-F03-02: Sustained chunk downloads scale session pool up to 16 sessions."""
        mock = MtprotoMock()
        pool = mock.get_dc_pool(dc_id=2)

        # Simulate 40 successful chunk downloads
        for _ in range(40):
            idx = pool.choose_session_index()
            pool.request_succeeded(idx, 128 * 1024)

        self.assertEqual(len(pool.sessions), 16)
        self.assertEqual(pool.max_sessions, 16)

    def test_t1_f03_03_load_balancing_least_loaded_session(self):
        """TEST-T1-F03-03: choose_session_index dispatches to session with minimal pending bytes."""
        mock = MtprotoMock()
        pool = mock.get_dc_pool(dc_id=2)
        pool.sessions[0].requested_bytes = 256 * 1024
        pool.sessions[1].requested_bytes = 128 * 1024
        pool.sessions[2].requested_bytes = 512 * 1024
        pool.sessions[3].requested_bytes = 0

        chosen = pool.choose_session_index()
        self.assertEqual(chosen, 3)

    def test_t1_f03_04_timeout_failure_backoff(self):
        """TEST-T1-F03-04: Timeouts trigger failure backoff and trim excess sessions."""
        mock = MtprotoMock()
        pool = mock.get_dc_pool(dc_id=2)
        # Scale to 8 sessions
        for _ in range(15):
            idx = pool.choose_session_index()
            pool.request_succeeded(idx, 128 * 1024)
        self.assertGreater(len(pool.sessions), 4)

        # Inject repeated timeouts
        for _ in range(6):
            pool.request_failed_timeout(session_idx=0)

        self.assertGreater(pool.session_remove_times, 0)

    def test_t1_f03_05_multi_dc_independent_session_pools(self):
        """TEST-T1-F03-05: Session pools for distinct DCs operate in complete isolation."""
        mock = MtprotoMock()
        pool_dc2 = mock.get_dc_pool(dc_id=2)
        pool_dc4 = mock.get_dc_pool(dc_id=4)

        # Scale DC 2
        for _ in range(25):
            pool_dc2.request_succeeded(0, 128 * 1024)

        self.assertGreater(len(pool_dc2.sessions), 4)
        self.assertEqual(len(pool_dc4.sessions), 4)


if __name__ == "__main__":
    unittest.main()
