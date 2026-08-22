# Telegram Desktop: Build & Architecture Survey Report

**Survey Date**: August 20, 2026  
**Target Repository**: `c:\Users\kyleh\tdesktop` (Branch: `nightly`)  
**Investigator**: Explorer Agent (Build & Architecture Survey)

---

## 1. Executive Summary

This survey evaluates the build architecture, toolchain configuration, target definitions, and source registrations of the **Telegram Desktop (`tdesktop`)** repository on Windows Native and WSL environments.

### Key Takeaways
- **Build Status**: The Windows Native Debug build tree is configured at `c:\Users\kyleh\tdesktop\out\` targeting **Visual Studio 17 2022 (MSVC 14.44.35207, x64)** and Windows SDK `10.0.26100.0`.
- **Existing Artifacts**: A successful Debug executable (`out/Debug/Telegram.exe`, ~492 MB) and symbol file (`out/Debug/Telegram.pdb`, ~2.98 GB) are present in the build directory.
- **Source Registration**: All target custom and fork source files—including `calls/calls_box_controller.cpp/.h`, `calls/group/calls_group_display_coordinator.cpp/.h`, `calls/group/calls_group_floating_overlay.cpp/.h`, `api/api_rich_tasks.cpp/.h`, and `chat_helpers/rich_paste_toast.cpp/.h`—are properly registered in `Telegram/CMakeLists.txt` and have compiled `.obj` artifacts in `out/Telegram/Telegram.dir/Debug/`.
- **Toolchain Requirements**: Windows Native Debug compilation requires an x64 Native Tools Command Prompt with MSYS2/Perl filtered from `PATH` to avoid command collisions with Windows native binaries (`find.exe`, `link.exe`), and `-j1` / bounded parallelism to avoid PCH heap limits during Qt resource compilation.

---

## 2. Toolchain & Environment Matrix

| Component | Windows Native Build | WSL / Linux Container Build |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 (MSVC Toolchain) | Ubuntu / CentOS Docker Container |
| **Compiler / IDE** | MSVC 19.44.35207 (VS 2022 BuildTools) | GCC / Clang via Docker CentOS Environment |
| **Architecture** | `x64` (`/machine:x64`) | `x86_64` |
| **C++ Standard** | `cxx_std_20` (C++20 with `/Zc:__cplusplus`) | `cxx_std_20` (C++20) |
| **CMake Generator** | Visual Studio 17 2022 (`Telegram.sln`) | Unix Makefiles / Ninja inside Container |
| **Qt Version** | Qt 5.15.2 (MSVC 2019/2022 64-bit static) | Qt 5.15.2 static in `/usr/local` |
| **Dependencies Root** | `../win64/Libraries` (`L:\Telegram\win64\Libraries`) | `../Libraries` (`L:\Telegram\Libraries`) |
| **Build Entry Point** | `cmake --build out --config Debug --target Telegram -j1` | `Telegram/build/docker/centos_env/build_debug.sh` |

---

## 3. CMake Architecture & Target Hierarchy

The project build system uses a modular target hierarchy structured across the root `CMakeLists.txt`, `cmake/` modules, and `Telegram/CMakeLists.txt`.

```
Telegram (Executable Target, AUTOMOC ON)
│
├── desktop-app::common_options (Interface Target)
│   └── Includes Windows SDK headers, MSVC flags (/W4, /utf-8, /bigobj, /EHsc)
│   └── Links Win32 system libraries (dwmapi, uxtheme, crypt32, propsys, etc.)
│
├── Sub-Libraries (in Telegram/):
│   ├── desktop-app::lib_base         (Foundation utilities, logging, assertion)
│   ├── desktop-app::lib_crl          (Cross-platform reactive loop / threading)
│   ├── desktop-app::lib_rpl          (Reactive programming library)
│   ├── desktop-app::lib_ui           (Custom widgets, styling, layout, call buttons)
│   ├── desktop-app::lib_tl           (Type Language MTProto serialization)
│   ├── desktop-app::lib_spellcheck   (Hunspell dictionary wrappers)
│   ├── desktop-app::lib_storage      (Encrypted binary cache and database facade)
│   ├── desktop-app::lib_lottie       (Vector animations via rlottie)
│   ├── desktop-app::lib_qr           (QR code rendering)
│   ├── desktop-app::lib_translate    (Language translation bindings)
│   ├── desktop-app::lib_webrtc       (WebRTC audio/video capture platform abstraction)
│   └── desktop-app::lib_webview      (WebView2 integration)
│
├── Modular CMake Targets (in Telegram/cmake/):
│   ├── tdesktop::lib_tgcalls         (Telegram group/1-on-1 calls engine)
│   ├── tdesktop::lib_fido2           (FIDO2 / Passkey authentication)
│   ├── tdesktop::lib_prisma          (Prisma photo editing filters)
│   ├── tdesktop::td_export           (Data export engine)
│   ├── tdesktop::td_iv               (Instant View parser)
│   ├── tdesktop::td_lang             (Language pack compiler / string loader)
│   ├── tdesktop::td_mtproto          (MTProto 2.0 network transport & encryption)
│   ├── tdesktop::td_scheme           (TL scheme code generator & schema classes)
│   ├── tdesktop::td_tde2e            (End-to-end encryption module)
│   ├── tdesktop::td_ui               (Telegram Desktop application UI components)
│   └── tdesktop::td_webauthn         (WebAuthn Windows API bridge)
│
└── External Dependencies:
    ├── Qt 5.15.2 (Core, Gui, Widgets, Network, Svg, OpenGL)
    ├── OpenSSL 3.x (libcrypto, libssl)
    ├── FFmpeg (avcodec, avformat, avutil, swscale, swresample)
    ├── WebRTC (native libwebrtc static library)
    ├── OpenAL / RNNoise / xxHash / zlib / minizip / kcoreaddons
```

---

## 4. Source Registration & Custom Fork Modules Audit

All core files and fork-specific components were surveyed against `Telegram/CMakeLists.txt` and verified in the build tree:

| Source File | Location | CMakeLists Registration | Debug Object Status |
| :--- | :--- | :--- | :--- |
| `calls_box_controller.cpp/.h` | `Telegram/SourceFiles/calls/` | Line 464-465 | `out/Telegram/Telegram.dir/Debug/calls_box_controller.obj` (Present) |
| `calls_group_display_coordinator.cpp/.h` | `Telegram/SourceFiles/calls/group/` | Line 456-457 | `out/Telegram/Telegram.dir/Debug/calls_group_display_coordinator.obj` (Present) |
| `calls_group_floating_overlay.cpp/.h` | `Telegram/SourceFiles/calls/group/` | Line 458-459 | `out/Telegram/Telegram.dir/Debug/calls_group_floating_overlay.obj` (Present) |
| `api_rich_tasks.cpp/.h` | `Telegram/SourceFiles/api/` | Line 199-200 | `out/Telegram/Telegram.dir/Debug/api_rich_tasks.obj` (Present) |
| `rich_paste_toast.cpp/.h` | `Telegram/SourceFiles/chat_helpers/` | Line 513-514 | `out/Telegram/Telegram.dir/Debug/rich_paste_toast.obj` (Present) |
| `history_view_video_cover_uploader.cpp/.h` | `Telegram/SourceFiles/history/view/controls/` | Line 865-866 | `out/Telegram/Telegram.dir/Debug/history_view_video_cover_uploader.obj` (Present) |
| `info_profile_tab_chats.cpp/.h` | `Telegram/SourceFiles/info/profile/tabs/adapters/` | Line 1248-1249 | `out/Telegram/Telegram.dir/Debug/info_profile_tab_chats.obj` (Present) |
| `call_button.cpp/.h` | `Telegram/lib_ui/ui/controls/` | `Telegram/lib_ui/CMakeLists.txt` | Linked via `desktop-app::lib_ui` (Present) |

### Language & Palette Assets
- **`lang.strings`**: Keys `lng_settings_ghost_mode`, `lng_settings_ghost_mode_about`, `lng_group_call_open_chat`, and `lng_group_call_context_pin_to_grid` are registered in `Telegram/Resources/langs/lang.strings`.
- **`colors.palette`**: `callCancelRipple: #c04646` is defined in `Telegram/lib_ui/ui/colors.palette:571`.
- **`calls.style`**: `CallButton` struct definition and styling rules are populated in `Telegram/SourceFiles/calls/calls.style:17`.

---

## 5. Subsystems Deep-Dive: Calls, Storage & WebRTC

### 5.1 Calls Controller & Group Call Architecture (`Calls::BoxController`)
- Located in `calls_box_controller.h` and `calls_box_controller.cpp`.
- Implements `Calls::GroupCalls::ListController` and `Calls::BoxController` derived from `PeerListController`.
- Utilizes `MTP::Sender _api` to guarantee lifecycle-bound RPC cancellation on controller destruction.
- Handles `ClearCallsBox`, `ShowCallsBox`, and `ShowCallsMenu` for main menu inline folder / popup integration.

### 5.2 Storage & SQLite Optimization Context (`C1`)
- Telegram Desktop's primary offline storage uses a custom encrypted binary cache (`Storage::Cache::Database`, `Storage::Databases`, `storage_account.cpp`) with XXH32 checksums, binlog compaction, and `QDataStream` serialization into `tdata/`.
- WAL journaling (`PRAGMA journal_mode = WAL`) and memory-mapped file access (`PRAGMA mmap_size`) referenced in `ARCHITECTURE.md` apply to local database subsystems where SQLite query concurrency and instant search indexing are utilized.

### 5.3 WebRTC Jitter Clamping & Playout Delay (`A1`)
- Implemented within `lib_tgcalls` (`MediaManager.cpp`, `GroupInstanceCustomImpl.cpp`, `InstanceV2Impl.cpp`).
- Audio options explicitly set:
  ```cpp
  cricket::AudioOptions audioOptions;
  audioOptions.audio_jitter_buffer_fast_accelerate = true;
  audioOptions.audio_jitter_buffer_min_delay_ms = 50;
  ```
- Clamps playout delay to a 50ms baseline while accelerating jitter buffer catch-up for live stream voice sync.

---

## 6. Compiler, Linker & Performance Configurations

### MSVC Compilation Flags (`cmake/options_win.cmake`)
- Standard: `/std:c++20` (`cxx_std_20`)
- Exception Handling: `/EHsc` (C++ exceptions only)
- Encoding: `/utf-8`
- Warning Level: `/W4` with specific benign warnings silenced (`/wd4100`, `/wd4244`, `/wd4267`, `/wd4702`, etc.)
- Section Expansion: `/bigobj` (critical for large schema serialization units like `scheme.cpp` and `qrc` files)
- Precompiled Headers: `stdafx.h` via `target_precompile_headers(Telegram PRIVATE ...)`

### Linker Configuration
- Runtime: Static MSVC Debug CRT (`MultiThreadedDebug` / `/MTd`)
- Flags: `/NODEFAULTLIB:LIBCMT /DEBUG:FASTLINK /INCREMENTAL:NO /DEPENDENTLOADFLAG:0x800`
- Architecture: `/machine:x64` with `/LARGEADDRESSAWARE`

---

## 7. Build Prerequisites, Potential Pitfalls & Mitigation

1. **PCH Memory Limit / Virtual Memory Exhaustion**:
   - *Symptom*: `fatal error C1060: compiler is out of heap space` or `Failed to create virtual memory for PCH` during Qt resource file generation (`qrc_telegram.cpp`, `qrc_models.cpp`).
   - *Mitigation*: Limit concurrent compiler threads during full rebuilds using `-j1` or `-j2` (`cmake --build out --config Debug --target Telegram -j1`).
2. **MSYS2 / Strawberry Perl PATH Shadowing**:
   - *Symptom*: MSYS2 `find` or `link.exe` intercepting Windows SDK tools resulting in `The system cannot find the batch label specified - VCEnd` or invalid switch errors.
   - *Mitigation*: Execute from clean `vcvars64.bat` environment with MSYS2/Perl paths removed from `PATH`.
3. **Breakpad ATL Dependency**:
   - *Symptom*: Missing `atlbase.h` when compiling crash reporting tools.
   - *Mitigation*: Crash reporting / Breakpad stage is intentionally skipped in Windows native developer builds (`prepare.py`).
4. **Header Include Paths for Call Widgets**:
   - *Symptom*: `Cannot open include file: 'ui/widgets/call_button.h'`.
   - *Mitigation*: Use verified location `#include "ui/controls/call_button.h"`.

---

## 8. Verified Build & Test Commands

### Windows Native Debug Incremental Build
```cmd
:: From repository root (c:\Users\kyleh\tdesktop):
cmake --build out --config Debug --target Telegram -j1
```

### Windows Native Rebuild Target
```cmd
cmake --build out --config Debug --target Telegram --clean-first
```

### WSL / Linux Docker Build Entry
```bash
Telegram/build/docker/centos_env/build_debug.sh
```

---

## 9. Conclusion

The build system and architectural foundation of the Telegram Desktop project on `nightly` are in a sound, consistent state. All custom fork sources (`calls_box_controller`, `display_coordinator`, `floating_overlay`, `rich_tasks`, etc.) are correctly integrated into CMakeLists, linked with required libraries, and compiled into the existing Debug build output (`Telegram.exe`).
