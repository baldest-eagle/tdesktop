# BRIEFING — 2026-08-20T20:49:00Z

## Mission
Objective review and adversarial challenge for Milestone M2 (Navigation & Calls Menu Integration).

## 🔒 My Identity
- Archetype: reviewer
- Roles: reviewer, critic
- Working directory: c:\Users\kyleh\tdesktop\.agents\reviewer_m2_1
- Original parent: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Milestone: M2
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code
- Report findings with clear evidence (file path, line numbers)
- Check integrity violations (hardcoded test results, facade logic, bypassed work, fabricated verification, self-certifying work)
- Adhere strictly to AGENTS.md, REVIEW.md, PROJECT.md, and SCOPE.md conventions

## Current Parent
- Conversation ID: cc351ddd-67a8-4da7-b053-fdba88cdf5ba
- Updated: 2026-08-20T20:49:00Z

## Review Scope
- **Files to review**:
  - `Telegram/SourceFiles/window/window_main_menu.cpp`
  - `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
  - `Telegram/SourceFiles/core/core_settings.cpp`
  - `Telegram/SourceFiles/core/core_settings.h`
  - `Telegram/SourceFiles/data/data_histories.cpp`
  - `Telegram/SourceFiles/api/api_rich_tasks.h`
  - `Telegram/SourceFiles/api/api_rich_tasks.cpp`
  - `Telegram/SourceFiles/calls/calls_box_controller.h`
  - `Telegram/SourceFiles/calls/calls_box_controller.cpp`
- **Interface contracts**: PROJECT.md, SCOPE.md, docs/fork_features.md
- **Review criteria**: Correctness, Logical Completeness, Quality (style/formatting/comments/includes/line endings), Risk Assessment, Adversarial Stress-testing

## Review Checklist
- **Items reviewed**:
  - [x] Main menu Calls popup integration (`window_main_menu.cpp:703-714`)
  - [x] TON Wallet entry under My Profile with NEW badge (`window_main_menu.cpp:663-678`, `window_main_menu_helpers.cpp:278-360`)
  - [x] Ghost Mode settings UI and singleton pointer fix (`settings_privacy_security.cpp:1088-1118, 1203`)
  - [x] Ghost Mode serialization strictly at end of stream (`core_settings.cpp:349, 527, 634, 1058-1060, 1246`)
  - [x] Read receipt suppression in Ghost Mode & comment elimination (`data_histories.cpp:716-720`)
  - [x] Rich Tasks include sorting & iterator safety fix (`api_rich_tasks.h:10-11`, `api_rich_tasks.cpp:83-88`)
  - [x] Calls Box Controller includes, nested namespaces, 2-tab indent, comment policy (`calls_box_controller.h:10-12, 18`, `calls_box_controller.cpp:10-54, 930-995`)
- **Verdict**: APPROVE
- **Unverified claims**: None. All claims independently verified in source files.

## Attack Surface
- **Hypotheses tested**:
  - Ghost Mode rapid toggling / flapping during active chat session -> Handled gracefully; state flags reset cleanly.
  - Legacy `tdata` deserialization without `_ghostMode` -> Backward-compatible via `!stream.atEnd()` check and default fallback `0`.
  - Rapid multi-toggle rich tasks race condition -> Debounced safely with `kSendDelay = 1000ms`, local optimistic state, failure rollback via `original` snapshot, and iterator safety during `sendAccumulated`.
  - Main menu Calls popup destruction & memory safety -> Managed via `base::unique_qptr<Ui::PopupMenu>` parented to button widget and `crl::guard` on action callbacks.
- **Vulnerabilities found**: 0 critical, 0 major, 0 minor.
- **Untested angles**: Hardware-specific graphics acceleration (out of M2 scope).

## Key Decisions Made
- Confirmed full compliance with `AGENTS.md` and `REVIEW.md`.
- Issued verdict: APPROVE.

## Artifact Index
- c:\Users\kyleh\tdesktop\.agents\reviewer_m2_1\DISPATCH.md — Dispatch instructions
- c:\Users\kyleh\tdesktop\.agents\reviewer_m2_1\BRIEFING.md — Persistent working memory
- c:\Users\kyleh\tdesktop\.agents\reviewer_m2_1\handoff.md — Final review report
