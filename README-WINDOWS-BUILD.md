# Telegram Desktop — Windows Native Build Guide

This document describes the tweaks and workarounds needed to build Telegram Desktop natively on Windows (without Docker/WSL).

## Prerequisites

- **Visual Studio 2022** (BuildTools or Community/Pro)
- **CMake** 4.4.2+ (minimum 3.25)
- **Ninja** build system
- **Qt 5.15.2** for MSVC 2019 64-bit
- **Python 3.12+** (3.14 recommended)
- **Git** for Windows

## Directory Layout

```
L:\Telegram\                    # BuildPath
L:\Telegram\tdesktop\           # Repository
L:\Telegram\Libraries\          # 32-bit dependencies (Linux/macOS)
L:\Telegram\win64\Libraries\    # 64-bit dependencies (Windows)
L:\Telegram\ThirdParty\         # Build tools (NuGet, Python, etc.)
```

## Build Steps

### 1. Open Developer Command Prompt

Use **"x64 Native Tools Command Prompt for VS 2022"** (or `vcvars64.bat`).

### 2. Run prepare.py

```bash
python Telegram/build/prepare/prepare.py
```

This builds all 34 dependency stages (OpenSSL, FFmpeg, libvpx, zlib, etc.).

**Tweaks applied to `prepare.py`:**

| Issue | Fix |
|-------|-----|
| MSYS2 `find` conflicts with Windows `find.exe` | Removed MSYS2 from global `PATH_PREFIX` |
| libwebp nmake can't auto-detect arch via MSYS2 | Added `ARCH=x64` to libwebp nmake calls |
| Breakpad requires ATL headers (`atlbase.h`) | Skipped breakpad stage (replaced with `echo SKIPPED`) |

### 3. CMake Configure

```bash
cmake --build out --config Debug --target Telegram
```

Build files are generated at `out/`.

### 4. Build

```bash
cmake --build out --config Debug --target Telegram -j1
```

**Important:** Use `-j1` (single-threaded) to avoid PCH memory exhaustion on large Qt resource files (`qrc_telegram.cpp`, `qrc_models.cpp`, `qrc_animations.cpp`).

## Fork-Specific Fixes

### CallButton Struct Definition

The codegen (`codegen_style.exe`) parses `.style` files to learn struct fields. The fork's `CallButton` is a C++ class, but the style system needs a struct definition. Added to `Telegram/SourceFiles/calls/calls.style`:

```style
CallButton {
    button: IconButton;
    bg: color;
    bgSize: pixels;
    bgPosition: point;
    angle: double;
    outerRadius: pixels;
    outerBg: color;
    label: FlatLabel;
    cornerButtonPosition: point;
    cornerButtonBorder: pixels;
}
```

### Include Path Fix

Fork's `calls_panel.cpp` and `calls_group_panel.cpp` included `ui/widgets/call_button.h` but the file is at `ui/controls/call_button.h`. Fixed both includes.

### Missing Palette Color

Added `callCancelRipple` to `Telegram/lib_ui/ui/colors.palette`:

```
callCancelRipple: #c04646; // phone call popup cancel button ripple effect
```

### Removed Broken Fork-Only Files

These fork-only files had compilation errors and were removed:
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_floating_overlay.h`
- `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.cpp`
- `Telegram/SourceFiles/calls/group/calls_group_display_coordinator.h`

Also removed from `Telegram/CMakeLists.txt`.

## Build Launcher Scripts

Helper scripts in `C:\tmp\`:

| Script | Purpose |
|--------|---------|
| `tdesktop_launcher.py` | Runs `prepare.py` with clean env (no MSYS2 in PATH) |
| `tdesktop_configure_launcher.py` | CMake configure with clean env |
| `tdesktop_build_launcher.py` | Build with clean env, `-j1` |

All launchers:
1. Call `vcvars64.bat` to set up MSVC environment
2. Filter PATH to remove MSYS2, Strawberry Perl, and Git usr/bin
3. Run the build command

## Output

- **Executable:** `out/Debug/Telegram.exe` (~491 MB)
- **Libraries:** `out/Debug/*.lib`

## Troubleshooting

### "Cannot open include file: 'ui/widgets/call_button.h'"
Fix: Change to `ui/controls/call_button.h` in the source file.

### "type name 'callAnswerBg' not found" (codegen error)
Fix: Ensure `CallButton` struct is defined in `calls.style` before any variables that use it.

### "Failed to create virtual memory for PCH" / "internal heap limit reached"
Fix: Reduce parallelism. Use `-j1` instead of full parallel builds.

### "The system cannot find the batch label specified - VCEnd"
Fix: This appears after a build failure. It's a secondary error — fix the primary error first.

### Breakpad fails with "atlbase.h not found"
Fix: Breakpad is skipped in `prepare.py`. ATL headers require MFC/ATL component from VS Installer, which doesn't work via CLI. Breakpad is only needed for crash reporting — not required for a functioning build.

## Known Remaining Gaps

The fork adds files that may reference APIs not present on the dev branch:
- `api/api_rich_tasks.cpp`
- `chat_helpers/rich_paste_toast.cpp`
- `history/view/controls/history_view_video_cover_uploader.cpp`
- `info/profile/tabs/adapters/info_profile_tab_chats.cpp`

These may need API stubs or further fixes if they cause build errors.
