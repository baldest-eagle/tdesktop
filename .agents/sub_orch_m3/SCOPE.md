# Scope: Milestone M3 — Engine & Performance Subsystems

## Architecture
Milestone M3 focuses on backend performance tuning, transport layer optimization, and audio streaming engine configuration across storage and media subsystems:
1. **SQLite Storage PRAGMA Tuning (C1)**: Implemented `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h` with `SqlitePragmaConfig`, `BuildPragmaStatements()`, and `ApplySqlitePerformancePragmas()` applying `PRAGMA journal_mode = WAL;`, `PRAGMA mmap_size = 268435456;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA cache_size = -64000;`, and `PRAGMA temp_store = MEMORY;` with graceful fallback to `TRUNCATE` when WAL is unsupported.
2. **WebRTC Jitter Buffer Clamping (A1)**: Enforced `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50` across all WebRTC voice channel instantiation sites: `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp:364-365`, `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp:1565-1566`, and `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2Impl.cpp:344-345`.
3. **Multi-Connection MTProto Chunk Downloading (B1)**: Verified chunk parameters (`kDownloadPartSize = 128 KB`, `kMaxSessionsCount = 16`, `kMaxWaitedInSession = 4 MB`) in `Telegram/SourceFiles/storage/download_manager_mtproto.cpp/.h` and fixed the session timeout unshifting calculation (`MTP::GetDcIdShift(shiftedDcId) - MTP::kBaseDownloadDcShift`) in `download_manager_mtproto.cpp:130`.
4. **Audio Lockout & Listen-Only Invariants**: Verified listen-only zero-mic capture invariants in `tgcalls` and audio controllers.

## Feature Inventory
| # | Feature | Description | Milestone | Status | Source |
|---|---------|-------------|-----------|--------|--------|
| 3 | Multi-Connection MTProto Chunk Downloading | 16 parallel DC download sessions & timeout unshift fix in `download_manager_mtproto` | M3 | DONE | docs/fork_features.md:12 |
| 35 | Audio Lockout / Listen-Only Mode | Strict zero-mic capture prevention in `tgcalls` | M3 | DONE | docs/fork_features.md:56 |
| 36 | Microphone Controls Removal | Hides mic/mute buttons in listen-only mode | M3 | DONE | docs/fork_features.md:57 |
| 37 | Permanent Listen-Only Invariant | Controller drops outgoing audio descriptors | M3 | DONE | docs/fork_features.md:58 |
| 53 | SQLite PRAGMA Optimizations (C1) | WAL journaling, 256MB mmap, cache & fallback in `storage_sqlite_pragmas.h` | M3 | DONE | docs/fork_features.md:82 |
| 54 | WebRTC Playout Delay & Jitter Clamping (A1) | Fast accelerate and 50ms min jitter delay across tgcalls voice channels | M3 | DONE | docs/fork_features.md:83 |

## Interface Contracts
### Storage Initialization ↔ SQLite Engine
- `Storage::ApplySqlitePerformancePragmas(sqlite3 *db)` executes `PRAGMA temp_store = MEMORY;`, `PRAGMA cache_size = -64000;`, `PRAGMA journal_mode = WAL;` (with fallback to `TRUNCATE;`), `PRAGMA synchronous = NORMAL;`, and `PRAGMA mmap_size = 268435456;`.
### WebRTC Engine ↔ tgcalls Audio Playout
- WebRTC media manager, group call instance, and V2 1-on-1 calls configure `cricket::AudioOptions` with `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50`.
### MTProto DC Downloader ↔ Chunk Manager
- Part size is 128 KB (`kDownloadPartSize`), maximum parallel sessions count is 16 (`kMaxSessionsCount`), maximum queue wait is 4 MB (`kMaxWaitedInSession`), and session timeout dispatch unshifts via `kBaseDownloadDcShift` (16).

## Code Layout Ownership & Output Artifacts
- `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp`
- `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`
- `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`
