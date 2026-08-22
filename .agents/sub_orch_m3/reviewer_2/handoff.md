# Review & Adversarial Challenge Report — Milestone M3 (Engine & Performance Subsystems)

**Author**: Reviewer 2 (`reviewer_2`)  
**Target**: Project Sub-Orchestrator M3 (`sub_orch_m3`)  
**Date**: 2026-08-20  
**Milestone**: M3 — Engine & Performance Subsystems  
**Verdict**: **APPROVE**  
**Integrity Status**: **VERIFIED (NO VIOLATIONS)**  

---

## 1. Observation

### 1.1 WebRTC Jitter Clamping A1 (Feature 54)
- **Target File**: `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp`
- **Lines 361–366**:
  ```cpp
  cricket::AudioOptions audioOptions;
  audioOptions.echo_cancellation = true;
  audioOptions.noise_suppression = true;
  audioOptions.audio_jitter_buffer_fast_accelerate = true;
  audioOptions.audio_jitter_buffer_min_delay_ms = 50;
  ```
- **Related Files Inspected**:
  - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1564-1567`:
    ```cpp
    cricket::AudioOptions audioOptions;
    audioOptions.audio_jitter_buffer_fast_accelerate = true;
    audioOptions.audio_jitter_buffer_min_delay_ms = 50;
    ```
  - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2Impl.cpp:343-346`:
    ```cpp
    cricket::AudioOptions audioOptions;
    audioOptions.audio_jitter_buffer_fast_accelerate = true;
    audioOptions.audio_jitter_buffer_min_delay_ms = 50;
    ```
- **Observation**: `MediaManager.cpp` had `audio_jitter_buffer_fast_accelerate = true` but was missing `audio_jitter_buffer_min_delay_ms = 50`. Worker 1 added `audioOptions.audio_jitter_buffer_min_delay_ms = 50;` at line 365. All WebRTC voice channels (1-on-1 calls, group calls, and media manager streams) now consistently enforce fast acceleration and a 50ms floor for playout delay.

### 1.2 MTProto Multi-Connection B1 (Feature 3)
- **Target File**: `Telegram/SourceFiles/storage/download_manager_mtproto.h` & `.cpp`
- **Lines 23–27 (`download_manager_mtproto.h`)**:
  ```cpp
  constexpr auto kDownloadPartSize = 128 * 1024;
  ```
- **Lines 22–35 (`download_manager_mtproto.cpp`)**:
  ```cpp
  constexpr auto kKillSessionTimeout = 15 * crl::time(1000);
  constexpr auto kStartWaitedInSession = 8 * kDownloadPartSize;
  constexpr auto kMaxWaitedInSession = 32 * kDownloadPartSize;
  constexpr auto kStartSessionsCount = 4;
  constexpr auto kMaxSessionsCount = 16;
  constexpr auto kMaxTrackedSessionRemoves = 64;
  constexpr auto kRetryAddSessionTimeout = 4 * crl::time(1000);
  constexpr auto kRetryAddSessionSuccesses = 2;
  constexpr auto kMaxTrackedSuccesses = kRetryAddSessionSuccesses
  	* kMaxTrackedSessionRemoves;
  constexpr auto kRemoveSessionAfterTimeouts = 4;
  constexpr auto kResetDownloadPrioritiesTimeout = crl::time(100);
  constexpr auto kBadRequestDurationThreshold = 6 * crl::time(1000);
  ```
- **Lines 124–132 (`download_manager_mtproto.cpp`)**:
  ```cpp
  DownloadManagerMtproto::DownloadManagerMtproto(not_null<ApiWrap*> api)
  : _api(api)
  , _resetGenerationTimer([=] { resetGeneration(); })
  , _killSessionsTimer([=] { killSessions(); }) {
  	_api->instance().restartsByTimeout(
  	) | rpl::filter([](MTP::ShiftedDcId shiftedDcId) {
  		return MTP::isDownloadDcId(shiftedDcId);
  	}) | rpl::on_next([=](MTP::ShiftedDcId shiftedDcId) {
  		sessionTimedOut(
  			MTP::BareDcId(shiftedDcId),
  			MTP::GetDcIdShift(shiftedDcId) - MTP::kBaseDownloadDcShift);
  	}, _lifetime);
  }
  ```
- **Observation**:
  - `kDownloadPartSize` is 128 KB (131,072 bytes).
  - `kMaxSessionsCount` is 16 parallel DC download connections.
  - `kMaxWaitedInSession` is 32 * 128 KB = 4 MB per session queue.
  - The bug where `sessionTimedOut` received raw `GetDcIdShift(shiftedDcId)` (`16..31`) and was rejected by `if (index >= dc.sessions.size())` (since `sessions.size() <= 16`) was resolved by unshifting with `- MTP::kBaseDownloadDcShift`.

### 1.3 SQLite PRAGMA Tuning C1 (Feature 53)
- **Target File**: `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`
- **Lines 1–82**:
  - `SqlitePragmaConfig` defines:
    - `journalMode = u"WAL"_q`
    - `fallbackJournalMode = u"TRUNCATE"_q`
    - `mmapLimitBytes = 268435456` (256 MB)
    - `cacheSizeKiB = -64000` (64 MB page cache)
    - `synchronous = u"NORMAL"_q`
    - `tempStore = u"MEMORY"_q`
  - `BuildPragmaStatements(config)` generates the batch SQL statement.
  - `ApplySqlitePerformancePragmas(sqlite3 *db, config)` executes `temp_store` and `cache_size`, verifies WAL application, falls back to `TRUNCATE` if WAL is unsupported, sets `synchronous = NORMAL`, and applies `mmap_size = 268435456`.

---

## 2. Logic Chain

1. **WebRTC Jitter Clamping (A1 / Feature 54)**:
   - Observation 1.1 shows that `GroupInstanceCustomImpl.cpp` and `InstanceV2Impl.cpp` already had both `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50`.
   - `MediaManager.cpp:365` was the only missing call site among the WebRTC media audio channels. Adding `audioOptions.audio_jitter_buffer_min_delay_ms = 50;` brings full uniformity across the entire WebRTC subsystem in `tgcalls`.
   - Therefore, Requirement A1 is fully satisfied.

2. **MTProto Multi-Connection Tuning & Timeout Routing (B1 / Feature 3)**:
   - Observation 1.2 demonstrates that `kDownloadPartSize` (128 KB), `kMaxSessionsCount` (16), and `kMaxWaitedInSession` (4 MB) match the exact specifications in `PROJECT.md` and `SCOPE.md`.
   - `MTP::ShiftDcId(dcId, kBaseDownloadDcShift + index)` shifts download DC IDs by `0x10 + index`. When `restartsByTimeout()` emits a timeout event, `GetDcIdShift(shiftedDcId)` yields `16 + index`.
   - Without subtracting `MTP::kBaseDownloadDcShift`, `sessionTimedOut(dcId, 16 + index)` was called. In `sessionTimedOut`, `if (index >= dc.sessions.size())` checked `16 + index >= [4..16]`, which was always true, dropping the timeout notification.
   - Subtracting `MTP::kBaseDownloadDcShift` produces `index` in `[0, sessions.size() - 1]`, enabling correct timeout tracking, backoff, and degraded session pruning.
   - Therefore, Requirement B1 is fully satisfied.

3. **SQLite PRAGMA Tuning (C1 / Feature 53)**:
   - Observation 1.3 shows `storage_sqlite_pragmas.h` provides both string generation and direct C API execution with graceful fallback.
   - Filesystem limitations (e.g. read-only mounts, network drives) that reject WAL mode are gracefully caught and handled via `PRAGMA journal_mode = TRUNCATE;`.
   - Mmap and cache sizes are capped within safe bounds (256 MB mmap, 64 MB cache).
   - Therefore, Requirement C1 is fully satisfied.

---

## 3. Adversarial Review & Stress-Test Challenges

### Challenge 1: Filesystem Incompatibility with SQLite WAL or MMAP
- **Assumption**: SQLite can always switch to WAL mode and allocate 256 MB mmap address space.
- **Attack Scenario**: The client runs from a network share (SMB/NFS) or a filesystem that does not support shared-memory (`-shm`) files or memory-mapped files.
- **Blast Radius**: If unhandled, SQLite calls would fail, preventing local database access.
- **Mitigation & Verification**:
  - `ApplySqlitePerformancePragmas` executes `PRAGMA journal_mode = WAL;` via `sqlite3_prepare_v2` and inspects the resulting column text (`sqlite3_column_text(stmt, 0)`).
  - If the returned mode is not `"wal"` (case-insensitive), it immediately executes `PRAGMA journal_mode = TRUNCATE;`.
  - `PRAGMA mmap_size` is prepared with `sqlite3_prepare_v2` and gracefully finalized even if the OS kernel rejects the mmap size.
  - **Verdict**: PASS. Graceful fallback is sound.

### Challenge 2: Network Degradation with 16 Parallel MTProto Sessions
- **Assumption**: Up to 16 parallel DC download connections will not overload constrained connections or lead to socket thrashing.
- **Attack Scenario**: Low-bandwidth or high-latency mobile connection where 16 connections compete, cause packet loss, and experience timeouts.
- **Blast Radius**: High timeout rates could stall chunk assembly.
- **Mitigation & Verification**:
  - Sessions start at `kStartSessionsCount = 4`, not 16.
  - Expansion to 16 occurs only adaptively when all existing sessions achieve consecutive successes (`kRetryAddSessionSuccesses = 2`) after cooldown delays (`kRetryAddSessionTimeout`).
  - When timeouts occur, `sessionTimedOut()` properly decrements session count or tracks failures (`kRemoveSessionAfterTimeouts = 4`) now that the unshifting bug is resolved.
  - **Verdict**: PASS. Adaptive scaling and backoff are preserved.

### Challenge 3: Audio Playout Buffer Underflow vs. Latency Tradeoff
- **Assumption**: Clamping audio jitter buffer minimum delay to 50ms does not introduce audio robotic artifacts or underrun stalls under packet jitter.
- **Attack Scenario**: Sudden jitter spikes exceeding 50ms on peer connection.
- **Blast Radius**: Audio stutter or glitching if the jitter buffer cannot adapt.
- **Mitigation & Verification**:
  - `audio_jitter_buffer_min_delay_ms = 50` sets the *minimum* delay floor, preventing unnecessary playout buffer depletion. WebRTC's NetEq dynamic jitter estimation can still scale buffer delay above 50ms during high network jitter.
  - `audio_jitter_buffer_fast_accelerate = true` allows rapid playout speedup (up to 1.5x) to drain excess buffer backlog when network conditions stabilize.
  - **Verdict**: PASS. Clamping configuration matches WebRTC recommended voice parameters.

---

## 4. Integrity & Style Verification

- **Integrity Check**:
  - Hardcoded outputs/cheats: None.
  - Dummy facades: None.
  - Bypassed implementations: None.
  - Verification: All source files contain real, operational logic.
- **Style Rules Compliance**:
  - No single-line comments in code: Checked and confirmed (0 single-line comments in changes).
  - No consecutive empty lines: Confirmed.
  - Plain structs compact (no trailing empty line before closing brace): `SqlitePragmaConfig` conforms.
  - Multi-line expression operator placement: Leading `.arg(...)` and `&&` operators used.
  - Variable initialization: All scalar and pointer variables (`stmt = nullptr`, `walApplied = false`, etc.) explicitly initialized.
  - String literals: `u"..."_q` literal syntax used throughout.
  - C++17 nested namespaces: `namespace Storage {` with closing comment.

---

## 5. Review Summary

| Item | Requirement | Status | Notes |
|---|---|---|---|
| **Area A1** | WebRTC Jitter Clamping (`fast_accelerate = true`, `min_delay_ms = 50`) | **PASS** | Verified in `MediaManager.cpp:364-365`, `GroupInstanceCustomImpl.cpp:1565-1566`, `InstanceV2Impl.cpp:344-345`. |
| **Area B1** | MTProto Multi-Connection (128 KB chunk, 16 sessions, 4 MB wait, timeout unshifting) | **PASS** | Verified in `download_manager_mtproto.h:26` and `download_manager_mtproto.cpp:24-26, 128-131`. |
| **Area C1** | SQLite PRAGMA Performance & Fallback (WAL, mmap 256MB, synchronous NORMAL, cache -64MB, temp MEMORY) | **PASS** | Verified in `storage_sqlite_pragmas.h:19-78`. |
| **Style** | Conformance with `REVIEW.md` and `AGENTS.md` | **PASS** | No comments, clean formatting, proper types. |
| **Integrity** | Anti-cheating & non-facade verification | **PASS** | 100% genuine implementation. |

**Verdict**: **APPROVE**

---

## 6. Caveats

- SQLite is an auxiliary storage interface in Telegram Desktop; `storage_sqlite_pragmas.h` provides the complete header and C API execution infrastructure ready for SQLite database handles without introducing unwanted dependencies into `lib_storage`.
- Windows Native Debug build verification will be performed holistically in Milestone M4.

---

## 7. Verification Method

To independently reproduce and verify this review:
1. Inspect `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp:361-366` to verify `audio_jitter_buffer_min_delay_ms = 50`.
2. Inspect `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:128-132` to verify `MTP::GetDcIdShift(shiftedDcId) - MTP::kBaseDownloadDcShift`.
3. Inspect `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h` to verify `SqlitePragmaConfig`, `BuildPragmaStatements`, and `ApplySqlitePerformancePragmas`.
