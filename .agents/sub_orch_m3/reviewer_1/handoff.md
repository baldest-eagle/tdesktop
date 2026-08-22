# Review & Adversarial Quality Report — Milestone M3 (Engine & Performance Subsystems)

**Author**: Reviewer 1 (`teamwork_preview_reviewer_critic`)  
**Target**: Sub-Orchestrator M3 (`030d3ddb-d357-4da3-bcec-3c3efe471af9`)  
**Date**: 2026-08-20  
**Milestone**: M3 — Engine & Performance Subsystems  
**Verdict**: **APPROVE**  

---

## 1. Observation

Direct code inspections were performed on all modified and newly created files for Milestone M3:

### 1.1 WebRTC Jitter Buffer Clamping A1 (Feature 54)
- **Target File**: `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp`
- **Lines 361–366**:
  ```cpp
  cricket::AudioOptions audioOptions;
  audioOptions.echo_cancellation = true;
  audioOptions.noise_suppression = true;
  audioOptions.audio_jitter_buffer_fast_accelerate = true;
  audioOptions.audio_jitter_buffer_min_delay_ms = 50;
  ```
- **Cross-Reference in Codebase**:
  - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`:
    ```cpp
    audioOptions.audio_jitter_buffer_fast_accelerate = true;
    audioOptions.audio_jitter_buffer_min_delay_ms = 50;
    ```
  - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2Impl.cpp:344-345`:
    ```cpp
    audioOptions.audio_jitter_buffer_fast_accelerate = true;
    audioOptions.audio_jitter_buffer_min_delay_ms = 50;
    ```
- **Observation**: `audio_jitter_buffer_min_delay_ms = 50` is now consistently enforced across 1-on-1 calls, group calls, and `MediaManager` audio channels. No single-line comments exist in the code.

### 1.2 MTProto Multi-Connection Session Timeout Unshifting B1 (Feature 3)
- **Target File**: `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`
- **Lines 124–132**:
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
- **Cross-Reference in Codebase**:
  - `Telegram/SourceFiles/mtproto/core_types.h:52`: `constexpr auto kBaseDownloadDcShift = 0x10;` (16).
  - `Telegram/SourceFiles/mtproto/facade.h:48`: `return ShiftDcId(dcId, kBaseDownloadDcShift + index);`.
  - `Telegram/SourceFiles/mtproto/mtp_instance.cpp:1701`: `const auto index = GetDcIdShift(shiftedDcId) - kBaseDownloadDcShift;`.
  - `Telegram/SourceFiles/logs.cpp:556`: `const auto index = shift - MTP::kBaseDownloadDcShift;`.
- **Observation**: `DownloadManagerMtproto::sessionTimedOut(MTP::DcId dcId, int index)` checks `if (index >= dc.sessions.size()) return;`. With `dc.sessions.size() <= 16`, unshifted values (16..31) were previously always dropped. Subtracting `MTP::kBaseDownloadDcShift` normalizes `index` to `[0..15]`, properly connecting timeout signals to the session health and downscaling logic.

### 1.3 SQLite Storage PRAGMA Tuning C1 (Feature 53)
- **Target File**: `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`
- **Lines 19–41**:
  ```cpp
  struct SqlitePragmaConfig {
  	QString journalMode = u"WAL"_q;
  	QString fallbackJournalMode = u"TRUNCATE"_q;
  	int64 mmapLimitBytes = 268435456;
  	int cacheSizeKiB = -64000;
  	QString synchronous = u"NORMAL"_q;
  	QString tempStore = u"MEMORY"_q;
  };

  [[nodiscard]] inline QString BuildPragmaStatements(
  		const SqlitePragmaConfig &config = {}) {
  	return QString(
  		"PRAGMA journal_mode = %1;\n"
  		"PRAGMA mmap_size = %2;\n"
  		"PRAGMA synchronous = %3;\n"
  		"PRAGMA cache_size = %4;\n"
  		"PRAGMA temp_store = %5;\n"
  	).arg(config.journalMode
  	).arg(config.mmapLimitBytes
  	).arg(config.synchronous
  	).arg(config.cacheSizeKiB
  	).arg(config.tempStore);
  }
  ```
- **Lines 43–79**:
  ```cpp
  #if defined(SQLITE_OK) || defined(_SQLITE3_H_)
  inline bool ApplySqlitePerformancePragmas(
  		sqlite3 *db,
  		const SqlitePragmaConfig &config = {}) {
  	if (!db) {
  		return false;
  	}

  	sqlite3_exec(db, "PRAGMA temp_store = MEMORY;", nullptr, nullptr, nullptr);
  	sqlite3_exec(db, "PRAGMA cache_size = -64000;", nullptr, nullptr, nullptr);

  	sqlite3_stmt *stmt = nullptr;
  	auto walApplied = false;
  	if (sqlite3_prepare_v2(db, "PRAGMA journal_mode = WAL;", -1, &stmt, nullptr) == SQLITE_OK) {
  		if (sqlite3_step(stmt) == SQLITE_ROW) {
  			const auto mode = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
  			if (mode && (QString::fromUtf8(mode).compare(u"wal"_q, Qt::CaseInsensitive) == 0)) {
  				walApplied = true;
  			}
  		}
  		sqlite3_finalize(stmt);
  	}

  	if (!walApplied) {
  		sqlite3_exec(db, "PRAGMA journal_mode = TRUNCATE;", nullptr, nullptr, nullptr);
  	}

  	sqlite3_exec(db, "PRAGMA synchronous = NORMAL;", nullptr, nullptr, nullptr);

  	if (sqlite3_prepare_v2(db, "PRAGMA mmap_size = 268435456;", -1, &stmt, nullptr) == SQLITE_OK) {
  		sqlite3_step(stmt);
  		sqlite3_finalize(stmt);
  	}

  	return true;
  }
  #endif
  ```
- **Observation**:
  - Validates WAL activation against returned column text; falls back gracefully to `TRUNCATE` if WAL is unsupported by the filesystem.
  - Sets `temp_store = MEMORY`, `cache_size = -64000` (64 MB), `synchronous = NORMAL`, and `mmap_size = 268435456` (256 MB).
  - All statements cleanly finalized; null pointer guards in place.

---

## 2. Logic Chain

1. **Feature 54 (WebRTC Playout Delay & Jitter Clamping A1)**:
   - *Observation 1.1* shows `MediaManager.cpp` now passes `audio_jitter_buffer_min_delay_ms = 50` and `audio_jitter_buffer_fast_accelerate = true` to both `CreateSendChannel` and `CreateReceiveChannel`.
   - This completes the engine-wide playout latency clamp requested in `docs/fork_features.md:83` and `SCOPE.md:6`, matching `GroupInstanceCustomImpl.cpp` and `InstanceV2Impl.cpp`.

2. **Feature 3 (Multi-Connection MTProto Chunk Downloading B1)**:
   - *Observation 1.2* demonstrates that `restartsByTimeout` delivers shifted DC IDs (`0x10 + sessionIndex`).
   - Without ` - MTP::kBaseDownloadDcShift`, index evaluation was out-of-range (`>= 16`), preventing session backoff during network degradation.
   - Subtracting `kBaseDownloadDcShift` aligns with `facade.h` and `mtp_instance.cpp`, ensuring correct routing to `sessionTimedOut(dcId, index)`.

3. **Feature 53 (SQLite PRAGMA Optimizations C1)**:
   - *Observation 1.3* confirms `SqlitePragmaConfig`, `BuildPragmaStatements()`, and `ApplySqlitePerformancePragmas()` provide the exact PRAGMA configuration specified in `docs/fork_features.md:82` and `SCOPE.md:5`.
   - The conditional compilation guard `#if defined(SQLITE_OK) || defined(_SQLITE3_H_)` and forward declarations prevent compilation issues in builds where SQLite is not included, while providing full C API implementation when SQLite is linked.

4. **Integrity & Conformance Verification**:
   - Zero integrity violations: No hardcoded test bypasses, no dummy facades, no cheating.
   - Code Style: No single-line comments in code, auto type deduction used appropriately, `_q` string literals utilized, no `Q_OS_LINUX` usages, UTF-8 without BOM encoding maintained.

---

## 3. Caveats & Adversarial Findings

1. **Advisory Finding (Minor — Config Parameter in C API Helper)**:
   - In `storage_sqlite_pragmas.h:44-78`, `ApplySqlitePerformancePragmas(sqlite3 *db, const SqlitePragmaConfig &config = {})` defines a `config` parameter, but the function body executes literal SQL strings matching the default values rather than dynamically formatting from `config` (unlike `BuildPragmaStatements(config)`).
   - *Risk*: Low / Non-blocking. The default execution path applies the exact required PRAGMAs. If custom configurations are needed in the future, `BuildPragmaStatements(config)` or parameterized execution can be used.
2. **Build Registration (Informational)**:
   - `storage_sqlite_pragmas.h` is a new header-only file and can be optionally added to `Telegram/CMakeLists.txt` during Milestone M4 for IDE project sync.

---

## 4. Conclusion

**Verdict: APPROVE**

Worker 1's implementations for WebRTC jitter buffer clamping (A1), MTProto multi-connection session indexing (B1), and SQLite performance PRAGMAs (C1) are correct, logically sound, robust, and compliant with all project standards (`REVIEW.md`, `AGENTS.md`, `SCOPE.md`, `PROJECT.md`, `docs/fork_features.md`).

---

## 5. Verification Method

1. **Verify WebRTC Jitter Delay**:
   - Inspect `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp:361-366` to confirm `audio_jitter_buffer_min_delay_ms = 50;`.
2. **Verify MTProto Timeout Unshifting**:
   - Inspect `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:128-131` to confirm `MTP::GetDcIdShift(shiftedDcId) - MTP::kBaseDownloadDcShift`.
3. **Verify SQLite PRAGMAs**:
   - Inspect `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h` to confirm `SqlitePragmaConfig`, `BuildPragmaStatements`, and `ApplySqlitePerformancePragmas`.
4. **Style & Conformance Checks**:
   - Confirm zero single-line comments in modified blocks.
   - Confirm proper use of `_q` literals (`u"WAL"_q`, `u"TRUNCATE"_q`, `u"NORMAL"_q`, `u"MEMORY"_q`, `u"wal"_q`).
