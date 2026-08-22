# Handoff Report: Milestone M4 — Style & Conventions Audit

**Agent**: Explorer M4.1 (Style & Conventions Specialist)  
**Parent Conversation ID**: `9d377efc-5403-45ca-a2b8-cbcad1470ef4`  
**Working Directory**: `c:\Users\kyleh\tdesktop\.agents\explorer_m4_1\`  
**Target Milestone**: M4 (Style & Conventions Verification)  
**Detailed Report**: `c:\Users\kyleh\tdesktop\.agents\explorer_m4_1\report.md`

---

## 1. Observation

Direct line-by-line inspection was conducted across all 15 source files and related headers across Milestones M1, M2, and M3 against `REVIEW.md` and `AGENTS.md`.

### Key Direct Observations:
1. **Include Ordering & Styles Placement**:
   - `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp:17-25`:
     `#include "styles/style_calls.h"` is placed before `<QtGui/QGuiApplication>` and other Qt headers.
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.h:10-11`:
     `#include "ui/rp_widget.h"` is placed before `#include "ui/effects/animations.h"` (nested folder not sorted first).
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:21-36`:
     `media/view/media_view_pip.h` is before `base/platform/base_platform_info.h`; `styles/style_calls.h` is before `<QOpenGLShader>`.
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp:44`:
     `#include "ui/widgets/fields/input_field.h"` is placed after `webrtc/webrtc_video_track.h`.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h:12`:
     `#include "ui/rp_widget.h"` is placed before `#include "calls/group/..."`.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:12-16`:
     `styles/style_calls.h` is placed before `<QtGui/...>` and `<QtWidgets/...>`.
   - `Telegram/SourceFiles/storage/download_manager_mtproto.cpp:10-18`:
     `apiwrap.h` and `base/openssl_help.h` are placed after `data/data_document.h`.

2. **Bloat Comments & Dead Code**:
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:515`:
     `// Allocate pinned tiles to fixed leading slots first`
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:529-530`:
     `// Fill remaining slots with unpinned active tiles sorted chronologically by entryTime`
     `// (oldest in Slot 0 top-left, newest in bottom-right)`
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:1175-1221`:
     46 lines of commented-out legacy code in `MuteButtonTooltip` (`//return rpl::single(std::make_tuple...`).
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1982`:
     `// In-call username search bar at the top of the sidebar`
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:52, 101, 113, 124, 131, 137, 154, 171`:
     Single-line descriptive comments preceding standard function calls.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:1493, 1519, 1535`:
     `// Restore to main grid`, `// Remove from main grid view`.

3. **String Literals Syntax (`u"..."_q`)**:
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1994`:
     `rpl::single(QStringLiteral("Search username...")));` uses `QStringLiteral` instead of `u"Search username..."_q`.
   - `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp:23-26`:
     `case DisplayRole::ActiveSpeaker: return "Active Speaker";` uses raw `const char[]` string literals implicitly converting to `QString`.
   - `Telegram/SourceFiles/calls/group/calls_group_panel.cpp:862, 882, 1478, 1479, 1483, 1487, 1509, 1525`:
     Uses `QStringLiteral(...)` instead of `u"..."_q`.

4. **Type Deduction (`auto`)**:
   - `Telegram/SourceFiles/calls/group/calls_group_viewport.cpp:531`:
     `std::vector<not_null<VideoTile*>> unpinnedTiles;` uses explicit type.
   - `Telegram/SourceFiles/calls/group/calls_group_members.cpp:1984, 1991`:
     `auto searchWrap`, `auto searchField` can be `const auto`.

5. **Namespace Comment Mismatch**:
   - `Telegram/SourceFiles/calls/group/calls_group_members.h:133`:
     `namespace Calls::Group {` is closed with `} // namespace Calls`.

6. **Compliant Core Architectural Invariants**:
   - `Telegram/SourceFiles/core/core_settings.cpp:527, 1058-1060`: `_ghostMode` is appended at the very end of binary serialization, read with `!stream.atEnd()` guard, and has default fallback.
   - `Telegram/SourceFiles/calls/calls_box_controller.cpp:970, 982, 991`: All menu action callbacks use `crl::guard(menu, [=] { ... })` and `MTP::Sender _api;`.
   - Class closing braces: All classes with access specifiers have empty lines before `};`.
   - Basic type initialization: 100% of primitive members are initialized.
   - `Q_OS_LINUX`: 0 occurrences in new code.

---

## 2. Logic Chain

1. **Rule Base**: `REVIEW.md` and `AGENTS.md` mandate specific conventions:
   - "Do NOT write comments in code: Do not write single-line comments that describe what the next line does - they are bloat."
   - "Prefer the project literal `u"..."_q` instead of the verbose `QStringLiteral("...")` macro."
   - "Sort `#include` directives alphabetically with two special rules: 1. Nested folders before files in the same directory. 2. Style includes (`styles/style_*.h`) always go last, separated from the rest."
   - "Prefer `auto` (or `const auto`, `const auto &`) instead of explicit types."
   - "Always add an empty line before the closing brace of a class (which has one or more sections like `public:` / `private:`)."
2. **Comparison with Observations**:
   - Observation 1 demonstrates that 6 files place style headers before Qt/std headers or misorder nested/standard includes.
   - Observation 2 identifies 15+ single-line bloat comments describing obvious subsequent statements and a 46-line block of commented-out dead code.
   - Observation 3 identifies multiple `QStringLiteral` macros and raw string literals requiring `u"..."_q`.
   - Observations 4 & 5 identify localized type deduction and namespace label mismatches.
3. **Core Compliance**:
   - Major architectural invariants (MTP request safety, binary stream serialization ordering, basic type initialization, empty line class closing braces, zero `Q_OS_LINUX`) are fully compliant.

---

## 3. Caveats

- Only the 15 specified source files and their direct M1-M3 callers/helpers were audited. Third-party WebRTC code in `Telegram/ThirdParty/tgcalls` follows upstream WebRTC formatting conventions, so style rules regarding `_q` and `crl::` do not apply to `tgcalls`.
- `calls_box_controller.cpp:556-569` contains inline TL argument comments (`// q`, `// saved_peer_id`) which are standard TL MTProto schema mappings; these are not bloat comments.
- `calls_box_controller.cpp:700-702` contains algorithmic invariant descriptions for binary search; these are compliant with the 4+ line algorithm comment exception.

---

## 4. Conclusion

The M1, M2, and M3 codebase is architecturally solid, type-safe, and follows primary Telegram Desktop conventions. 

A specific set of mechanical style fixes is required:
1. Reordering include directives in 5 files to ensure alphabetical ordering and `styles/style_*.h` placed last.
2. Stripping single-line bloat comments and dead commented code in `calls_group_viewport.cpp`, `calls_group_members.cpp`, `calls_group_display_coordinator.cpp`, and `calls_group_panel.cpp`.
3. Converting `QStringLiteral` and raw `const char[]` string literals to `u"..."_q`.
4. Updating `calls_group_members.h` namespace closing comment.

Worker M4.1 can immediately execute these exact fixes using the checklist in `report.md`.

---

## 5. Verification Method

To independently verify these findings:
1. Inspect the reported line numbers via `view_file` or `grep_search`:
   - `calls_group_floating_overlay.cpp:17-25` (style include placement)
   - `calls_group_viewport.cpp:515, 529, 1175` (bloat comments and dead code)
   - `calls_group_members.cpp:1994` (QStringLiteral)
   - `calls_group_display_coordinator.cpp:23-26` (raw string returns)
   - `download_manager_mtproto.cpp:10-18` (include sorting)
2. Verify that applying the fixes resolves all linter/reviewer style checks.
3. Invalidation condition: If any flagged comment represents a documented multi-line mathematical algorithm (>= 4 lines) or if a `QStringLiteral` is in an external 3rd-party library header.
