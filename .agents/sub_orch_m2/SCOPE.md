# Scope: Milestone M2 — Navigation & Calls Menu Integration

## Architecture & Boundaries
This milestone owns the Telegram main menu integration, calls submenu popup, Wallet menu entry with NEW badge, and Ghost Mode settings & suppression.

## Files Owned
- `Telegram/SourceFiles/window/window_main_menu.cpp`
- `Telegram/SourceFiles/calls/calls_box_controller.cpp`
- `Telegram/SourceFiles/calls/calls_box_controller.h`
- `Telegram/SourceFiles/core/core_settings.cpp`
- `Telegram/SourceFiles/core/core_settings.h`
- `Telegram/SourceFiles/data/data_histories.cpp`
- `Telegram/SourceFiles/settings/sections/settings_privacy_security.cpp`
- `Telegram/SourceFiles/api/api_rich_tasks.cpp`
- `Telegram/SourceFiles/api/api_rich_tasks.h`

## Specific Tasks
1. **Calls Menu Integration in Main Menu**:
   - In `window/window_main_menu.cpp:704–714`, replaced direct modal `Calls::ShowCallsBox` call with `Ui::PopupMenu` and `Calls::ShowCallsMenu` (from `calls/calls_box_controller.h`), ensuring that clicking "Calls" in the main menu dynamically opens the structured popup menu listing active calls, Start Call, and Call History. [DONE]
2. **Wallet Menu Entry**:
   - Verified that the Wallet entry in `window/window_main_menu.cpp` is positioned below "My Profile" with the green `NEW` badge as specified in `docs/fork_features.md:62`. [DONE]
3. **Ghost Mode (E3)**:
   - Verified and finalized `data_histories.cpp` suppression of outgoing read marks when `ghostMode()` is true. [DONE]
   - Corrected `Core::Settings` serialization at the end of the stream with `!stream.atEnd()` fallback for backward compatibility. [DONE]
   - Corrected Privacy & Security settings pointer and toggle in `settings_privacy_security.cpp`. [DONE]
4. **Rich Tasks**:
   - Verified `api_rich_tasks.cpp/.h` implementation, debounce logic, and fixed iterator safety in `send()`. [DONE]
5. **Style & Conventions**:
   - Adhered strictly to `REVIEW.md` and `AGENTS.md` (no single-line comments, include sorting, 2-tab parameters, `crl::guard`, `MTP::Sender`, etc.). [DONE]

## Status: DONE
- Iteration 1 Gate Result: **PASS** (Reviewers: 2/2 APPROVE, Challengers: 2/2 APPROVE, Forensic Auditor: CLEAN).
