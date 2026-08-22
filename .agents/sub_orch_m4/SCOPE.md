# Scope: Milestone M4 — Code Style, Conventions & Windows Native Debug Build Verification

## Architecture & Boundaries
This milestone owns repository-wide style and convention validation per `REVIEW.md` and `AGENTS.md`, and the verification of the Windows Native Debug build target (`cmake --build out --config Debug --target Telegram`).

## Specific Tasks
1. **Style & Conventions Audit**:
   - Verify that all modified/added files adhere to `REVIEW.md`:
     - No single-line comments describing what the next line does.
     - `auto` type deduction.
     - `_q` literal usage for `QString` literals (`u"..."_q`).
     - No `Q_OS_LINUX` in new code; use `!defined Q_OS_WIN && !defined Q_OS_MAC` or `Platform::IsLinux()`.
     - Parameter continuation indentation with 2 tabs.
     - Empty line before closing brace in class definitions with access specifiers.
     - Include ordering: alphabetical, nested folders first, styles (`style_*.h`) last.
     - `crl::guard` on async callbacks and `MTP::Sender` usage where appropriate.
     - CRLF/LF line ending consistency without UTF-8 BOM.
2. **Windows Native Debug Build Verification**:
   - Execute or verify the Windows Native Debug compilation and link (`cmake --build out --config Debug --target Telegram` or inspection of compilation units).
   - Ensure all target object files (`calls_box_controller.obj`, `calls_group_display_coordinator.obj`, `calls_group_floating_overlay.obj`, `api_rich_tasks.obj`, `calls_group_viewport.obj`, `calls_group_members.obj`, `window_main_menu.obj`, `storage_sqlite_pragmas.h`, `tgcalls` modifications) compile and link into `out/Debug/Telegram.exe` without unresolved symbols or missing dependencies.
3. **Multi-Agent Verification Gate**:
   - Explorer -> Worker -> Reviewer -> Challenger -> Forensic Auditor (`teamwork_preview_auditor`).
   - Binary veto on integrity violation.

## Deliverables
- Clean build and style verification report in `handoff.md`.
