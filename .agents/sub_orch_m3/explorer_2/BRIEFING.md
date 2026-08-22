# BRIEFING — 2026-08-20T19:22:00Z

## Mission
Investigate WebRTC Jitter Buffer Clamping (Feature 54 / A1) and Listen-Only / Zero-Mic Capture Invariants (Features 35, 36, 37) in tgcalls and calls engine for Milestone M3.

## 🔒 My Identity
- Archetype: explorer
- Roles: Teamwork explorer
- Working directory: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\explorer_2
- Original parent: 030d3ddb-d357-4da3-bcec-3c3efe471af9
- Milestone: M3 (Engine & Performance Subsystems)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Base working directory: c:\Users\kyleh\tdesktop\.agents\sub_orch_m3\explorer_2\
- Produce self-contained 5-component handoff report

## Current Parent
- Conversation ID: 030d3ddb-d357-4da3-bcec-3c3efe471af9
- Updated: 2026-08-20T19:22:00Z

## Investigation State
- **Explored paths**:
  - `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp`
  - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp`
  - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceReferenceImpl.cpp`
  - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2Impl.cpp`
  - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2CompatImpl.cpp`
  - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2ReferenceImpl.cpp`
  - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp`
  - `Telegram/SourceFiles/calls/group/calls_group_call.cpp`
  - `Telegram/SourceFiles/calls/calls_controller_webrtc.cpp`
- **Key findings**:
  - `GroupInstanceCustomImpl.cpp:1565-1566` & `InstanceV2Impl.cpp:344-345` have both `audio_jitter_buffer_fast_accelerate = true` and `audio_jitter_buffer_min_delay_ms = 50`.
  - `MediaManager.cpp:364` has `audioOptions.audio_jitter_buffer_fast_accelerate = true;` but is MISSING `audioOptions.audio_jitter_buffer_min_delay_ms = 50;`.
  - Listen-only invariants (Features 35, 36, 37) are enforced via on-demand outgoing channel creation in `GroupInstanceCustomImpl.cpp`, tooltip suppression, no-op click handlers in `calls_group_panel.cpp`, and mute state synchronization in `calls_group_call.cpp`.
- **Unexplored areas**: None within scope of Explorer 2.

## Key Decisions Made
- Confirmed single concrete defect in `MediaManager.cpp:364` for Worker to fix.

## Artifact Index
- DISPATCH.md — Dispatch log
- BRIEFING.md — Persistent state index
- progress.md — Liveness heartbeat
- handoff.md — Final investigation report
