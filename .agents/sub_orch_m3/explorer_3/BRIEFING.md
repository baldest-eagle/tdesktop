# BRIEFING — 2026-08-20T19:20:30Z

## Mission
Investigate Multi-Connection MTProto Chunk Downloading (Feature 3 / B1) in Telegram Desktop, verify chunk download parameters, parallel DC session management, edge cases, and prepare recommendations for the Worker.

## 🔒 My Identity
- Archetype: Explorer (Teamwork Explorer)
- Roles: Read-only investigation, synthesis, handoff report
- Working directory: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\explorer_3
- Original parent: 030d3ddb-d357-4da3-bcec-3c3efe471af9
- Milestone: M3 (Engine & Performance Subsystems)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement in source code
- Examine Multi-Connection MTProto Chunk Downloading in detail
- Verify constants (kDownloadPartSize, kMaxSessionsCount, kMaxWaitedInSession) and parallel session handling
- Deliver structured handoff.md and send_message to parent

## Current Parent
- Conversation ID: 030d3ddb-d357-4da3-bcec-3c3efe471af9
- Updated: 2026-08-20T19:20:30Z

## Investigation State
- **Explored paths**:
  - `Telegram/SourceFiles/storage/download_manager_mtproto.h`
  - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`
  - `Telegram/SourceFiles/storage/file_download_mtproto.h`
  - `Telegram/SourceFiles/storage/file_download_mtproto.cpp`
  - `Telegram/SourceFiles/storage/file_download.h`
  - `Telegram/SourceFiles/storage/file_download.cpp`
  - `Telegram/SourceFiles/storage/file_upload.cpp`
  - `Telegram/SourceFiles/media/streaming/media_streaming_loader_mtproto.h`
  - `Telegram/SourceFiles/media/streaming/media_streaming_loader_mtproto.cpp`
  - `Telegram/SourceFiles/data/data_media_preload.h`
  - `Telegram/SourceFiles/data/data_media_preload.cpp`
  - `Telegram/SourceFiles/mtproto/core_types.h`
  - `Telegram/SourceFiles/mtproto/facade.h`
  - `Telegram/SourceFiles/mtproto/mtp_instance.h`
  - `Telegram/SourceFiles/mtproto/mtp_instance.cpp`
- **Key findings**:
  - `kDownloadPartSize = 128 * 1024` (128 KB) verified in `storage/download_manager_mtproto.h:26`.
  - `kMaxSessionsCount = 16` verified in `storage/download_manager_mtproto.cpp:26` (matches `MTP::kMaxMediaDcCount = 16` in `mtproto/core_types.h:51`).
  - `kMaxWaitedInSession = 32 * kDownloadPartSize = 4 MB` verified in `storage/download_manager_mtproto.cpp:24`.
  - Initial DC session count is 4 (`kStartSessionsCount = 4`), initial per-session window is 1 MB (`kStartWaitedInSession = 8 * 128 KB`).
  - Sessions dynamically scale up from 4 to 16 based on sustained request completion, and scale down on timeouts / slow requests (threshold 6s).
  - Out-of-order chunk assembly supported across file downloads, streaming, and video preloads.
  - Critical bug discovered in `storage/download_manager_mtproto.cpp:130`: `restartsByTimeout` passes `MTP::GetDcIdShift(shiftedDcId)` (which is `16 + index`) directly to `sessionTimedOut`, causing timeout events from the transport layer to be silently discarded because `index >= dc.sessions.size()`. Needs `- MTP::kBaseDownloadDcShift`.
- **Unexplored areas**: None, full subsystem and dependent layers thoroughly investigated.

## Key Decisions Made
- Fully documented parameter verification, load balancing, dynamic session scaling, fault recovery, and consumer integrations.
- Identified actionable bug fix for `restartsByTimeout` session index calculation.

## Artifact Index
- DISPATCH.md — Dispatch log
- BRIEFING.md — Situational awareness
- progress.md — Progress heartbeat
- handoff.md — Complete 5-component handoff report
