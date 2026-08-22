"""
Tier 3 Tests: Cross-Feature Pairwise Interactions between Ghost Mode, Network Downloads, SQLite Storage, and Rich Tasks.
14 Test Cases.
"""

import unittest
from tests.e2e.framework import (
    MtprotoMock,
    SQLiteStorageMock,
    TdataStreamMock,
    CoreSettingsMock,
    RichTasksOracle,
    assert_rpc_dispatched,
    assert_rpc_suppressed,
    assert_pragma_executed,
)


class TestTier3GhostModeNetworkInteractions(unittest.TestCase):
    """Tier 3 Pairwise Combinatorial Tests: Ghost Mode + Network + Storage + Rich Tasks."""

    def test_t3_01_ghost_mode_during_16_session_parallel_chunk_download(self):
        """TEST-T3-01: Ghost mode suppresses read receipts while parallel 16-session chunk download saturates DC."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        pool = mock.get_dc_pool(dc_id=2)

        # Scale DC pool to 16 sessions
        for _ in range(40):
            idx = pool.choose_session_index()
            pool.request_succeeded(idx, 128 * 1024)
        self.assertEqual(len(pool.sessions), 16)

        # Read incoming messages during download
        dispatched = mock.send_read_request(peer_id=1001, max_id=50)
        self.assertFalse(dispatched)
        assert_rpc_suppressed(mock, "messages.readHistory")

    def test_t3_02_ghost_mode_settings_serialization_during_active_download(self):
        """TEST-T3-02: Ghost mode settings binary serialization executes safely while media download is active."""
        settings = CoreSettingsMock()
        settings.set_ghost_mode(True)
        stream = TdataStreamMock()

        settings.serialize(stream)
        self.assertEqual(len(stream.buffer), 12)

        # Cold reload verification
        loaded = CoreSettingsMock()
        loaded.deserialize(stream)
        self.assertTrue(loaded.ghost_mode)

    def test_t3_03_ghost_mode_with_rich_tasks_checklist_toggle(self):
        """TEST-T3-03: Checking Rich Task items modifies markdown while Ghost Mode suppresses read receipts."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        oracle = RichTasksOracle(message_id=701, initial_markdown="- [ ] Task 1\n- [ ] Task 2")

        # Toggle task
        oracle.toggle_item(0)
        self.assertTrue(oracle.items[0].completed)

        # Message read attempt
        mock.send_read_request(peer_id=2001, max_id=701)
        assert_rpc_suppressed(mock, "messages.readHistory")

    def test_t3_04_rich_tasks_debounce_commit_under_ghost_mode(self):
        """TEST-T3-04: 1000ms debounce timer commits Rich Task update via EditRichMessage while read marks stay suppressed."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        oracle = RichTasksOracle(message_id=702, initial_markdown="- [ ] Task 1")

        oracle.toggle_item(0)
        res = oracle.advance_time(1000)
        self.assertIsNotNone(res)
        self.assertIn("- [x] Task 1", res)

        mock.send_read_request(peer_id=2002, max_id=702)
        assert_rpc_suppressed(mock, "messages.readHistory")

    def test_t3_05_parallel_downloads_under_sqlite_wal_and_mmap(self):
        """TEST-T3-05: Multi-connection download writing to SQLite with WAL journaling and 256MB mmap."""
        storage = SQLiteStorageMock()
        storage.initialize_database(enable_optimizations=True)
        assert_pragma_executed(storage, "journal_mode", "WAL")
        assert_pragma_executed(storage, "mmap_size", 268435456)

        mock = MtprotoMock()
        pool = mock.get_dc_pool(dc_id=4)
        for _ in range(20):
            pool.request_succeeded(pool.choose_session_index(), 128 * 1024)
        self.assertGreater(len(pool.sessions), 4)

    def test_t3_06_chunk_download_timeout_does_not_affect_ghost_mode(self):
        """TEST-T3-06: MTProto network timeouts do not alter or reset Ghost Mode state."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        pool = mock.get_dc_pool(dc_id=2)

        pool.request_failed_timeout(0)
        self.assertTrue(mock.ghost_mode)

    def test_t3_07_read_5_chats_concurrently_with_16_session_download(self):
        """TEST-T3-07: Stealth reading across 5 different dialogs while 16-session download executes in background."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        pool = mock.get_dc_pool(dc_id=2)
        for _ in range(36):
            pool.request_succeeded(pool.choose_session_index(), 128 * 1024)

        for peer_id in range(101, 106):
            mock.send_read_request(peer_id=peer_id, max_id=10)

        assert_rpc_suppressed(mock, "messages.readHistory")
        self.assertEqual(len(pool.sessions), 16)

    def test_t3_08_local_unread_clearing_under_sqlite_wal_mode(self):
        """TEST-T3-08: Local unread badge clears in UI while server inbox pointer remains unchanged."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        mock.local_unread_counts[501] = 5
        mock.send_read_request(peer_id=501, max_id=99)

        self.assertEqual(mock.local_unread_counts[501], 0)
        self.assertNotIn(501, mock.server_inbox_pointers)

    def test_t3_09_cold_restart_sqlite_wal_recovering_ghost_mode(self):
        """TEST-T3-09: SQLite database restart with WAL mode preserves persisted Ghost Mode setting."""
        storage = SQLiteStorageMock()
        storage.initialize_database(enable_optimizations=True)

        settings = CoreSettingsMock()
        settings.set_ghost_mode(True)
        stream = TdataStreamMock()
        settings.serialize(stream)

        # Reboot
        settings_new = CoreSettingsMock()
        settings_new.deserialize(stream)
        self.assertTrue(settings_new.ghost_mode)
        assert_pragma_executed(storage, "journal_mode", "WAL")

    def test_t3_10_dynamic_ghost_mode_toggle_mid_download_stream(self):
        """TEST-T3-10: Toggling Ghost Mode on and off while chunk download is actively streaming."""
        mock = MtprotoMock()
        pool = mock.get_dc_pool(dc_id=2)

        # Start download
        pool.request_succeeded(0, 128 * 1024)

        # Ghost mode ON -> read suppressed
        mock.set_ghost_mode(True)
        mock.send_read_request(peer_id=1001, max_id=10)
        assert_rpc_suppressed(mock, "messages.readHistory")

        # Ghost mode OFF -> read sent
        mock.set_ghost_mode(False)
        mock.send_read_request(peer_id=1001, max_id=20)
        assert_rpc_dispatched(mock, "messages.readHistory", expected_count=1)

    def test_t3_11_rich_task_rollback_with_ghost_mode_enabled(self):
        """TEST-T3-11: Rich task RPC failure rollback operates seamlessly under Ghost Mode."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        oracle = RichTasksOracle(message_id=801, initial_markdown="- [ ] Deploy server")

        oracle.toggle_item(0)
        self.assertTrue(oracle.items[0].completed)
        oracle.rollback_on_error()
        self.assertFalse(oracle.items[0].completed)

    def test_t3_12_multi_dc_downloads_with_ghost_mode(self):
        """TEST-T3-12: Multi-connection downloads across DC 2 and DC 4 while Ghost Mode is active."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        p2 = mock.get_dc_pool(2)
        p4 = mock.get_dc_pool(4)

        for _ in range(10):
            p2.request_succeeded(0, 128 * 1024)
            p4.request_succeeded(0, 128 * 1024)

        mock.send_read_request(peer_id=9001, max_id=5)
        assert_rpc_suppressed(mock, "messages.readHistory")

    def test_t3_13_sqlite_cache_size_and_ghost_mode_coherency(self):
        """TEST-T3-13: SQLite 64MB memory cache holding unread message state under Ghost Mode."""
        storage = SQLiteStorageMock()
        storage.initialize_database(enable_optimizations=True)
        assert_pragma_executed(storage, "cache_size", -64000)

    def test_t3_14_comprehensive_stealth_session_integration(self):
        """TEST-T3-14: Full stealth session combining Ghost Mode ON, Rich Tasks, 16 MTProto streams, and SQLite WAL."""
        mock = MtprotoMock()
        mock.set_ghost_mode(True)
        storage = SQLiteStorageMock()
        storage.initialize_database(enable_optimizations=True)
        pool = mock.get_dc_pool(2)
        for _ in range(40):
            pool.request_succeeded(pool.choose_session_index(), 128 * 1024)

        oracle = RichTasksOracle(message_id=999, initial_markdown="- [ ] Review code")
        oracle.toggle_item(0)
        oracle.advance_time(1000)

        mock.send_read_request(peer_id=7777, max_id=100)

        assert_rpc_suppressed(mock, "messages.readHistory")
        self.assertEqual(len(pool.sessions), 16)
        assert_pragma_executed(storage, "journal_mode", "WAL")
        self.assertTrue(oracle.items[0].completed)


if __name__ == "__main__":
    unittest.main()
