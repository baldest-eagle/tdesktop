## 2026-08-20T19:22:26Z
You are Worker 1 for Milestone M3 (Engine & Performance Subsystems).

Your working directory is: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\worker_1\
The original request is at: c:\Users\kyleh\tdesktop\.agents\ORIGINAL_REQUEST.md
The project plan is at: c:\Users\kyleh\tdesktop\PROJECT.md
The scope document is at: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\SCOPE.md

Explorer Reports:
- Explorer 1: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\explorer_1\handoff.md
- Explorer 2: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\explorer_2\handoff.md
- Explorer 3: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\explorer_3\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Write Ownership:
You own exclusively:
- `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp`
- `Telegram/SourceFiles/storage/download_manager_mtproto.cpp`
- `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`

Tasks to execute:
1. **WebRTC Jitter Clamping A1 (Feature 54)**:
   In `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp` (around lines 361-366), add:
   `audioOptions.audio_jitter_buffer_min_delay_ms = 50;`
   right after `audioOptions.audio_jitter_buffer_fast_accelerate = true;` before `_mediaEngine->voice().CreateReceiveChannel(...)`.
   Ensure no single-line comments are added, formatting matches surrounding code.

2. **MTProto Multi-Connection B1 (Feature 3)**:
   In `Telegram/SourceFiles/storage/download_manager_mtproto.cpp` (around line 130), fix the timeout calculation:
   Change:
   `MTP::GetDcIdShift(shiftedDcId)`
   to:
   `MTP::GetDcIdShift(shiftedDcId) - MTP::kBaseDownloadDcShift`
   Ensure no single-line comments are added, formatting matches surrounding code.

3. **SQLite PRAGMA Tuning C1 (Feature 53)**:
   Create `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h` containing the standard helper struct and utilities for applying the 5 PRAGMAs (`journal_mode = WAL;`, `mmap_size = 268435456;`, `synchronous = NORMAL;`, `cache_size = -64000;`, `temp_store = MEMORY;`) with graceful fallback, matching the exact design in Explorer 1's handoff report and adhering strictly to `REVIEW.md` and `AGENTS.md` (no single-line comments, auto type deduction, `_q` literals).

4. **Style & Conformance**:
   - Check all edited files against `REVIEW.md` and `AGENTS.md`.
   - Ensure NO single-line comments are present in the changes.
   - Verify line endings and no UTF-8 BOM.

5. **Verification**:
   - Verify file modifications and verify that changes compile or parse cleanly.
   - Run compilation check if needed.

6. **Handoff**:
   Write your detailed handoff report to `c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\worker_1\handoff.md` and send a completion message back.
