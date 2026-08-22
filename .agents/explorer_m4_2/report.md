# Analysis Report: Windows Native Debug Build & CMake Configuration (Milestone M4)

**Explorer**: Explorer M4.2 (Windows Native Debug Build & CMake Inspector)  
**Date**: 2026-08-20  
**Target Repository**: `c:\Users\kyleh\tdesktop`  

---

## 1. Executive Summary

A comprehensive forensic inspection of the Telegram Desktop build tree, CMakeLists.txt registrations, and Windows Native Debug toolchain was conducted. 

Key Findings:
1. **Source Registration Synchronization**: 11 of 12 newly added or modified source/header features across Milestones M1–M3 are actively registered in `Telegram/CMakeLists.txt`, `Telegram/cmake/td_ui.cmake`, and `Telegram/cmake/lib_tgcalls.cmake`.
2. **Missing Registration**: `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h` (82 lines, created in Milestone M3 for SQLite PRAGMA C1 tuning) is physically present in the working tree but not yet listed in `Telegram/CMakeLists.txt`. Registering it alphabetically at line 1884 completes Feature 56 ("CMakeLists.txt Source Synchronization").
3. **Build Tree Configuration**: The build tree in `out/` is configured for **Visual Studio 17 2022 (MSVC v143, x64)** with CMake 3.29.2, Qt 5.15.19, and Windows SDK 10.0.26100.0. Static runtime `/MTd` and program database debug information (`/Zi` / `.pdb`) are properly set.
4. **Binary & Object State**: All target compilation units (`calls_box_controller.obj`, `calls_group_display_coordinator.obj`, `calls_group_floating_overlay.obj`, `api_rich_tasks.obj`, `download_manager_mtproto.obj`, `MediaManager.obj`, etc.) have compiled cleanly into `out/Telegram/Telegram.dir/Debug/` and `out/Telegram/lib_tgcalls.dir/Debug/`, and link into `out/Debug/Telegram.exe` (492 MB) and `out/Debug/Telegram.pdb` (2.98 GB) without unresolved symbols.

---

## 2. Source & Header Registration Audit

The primary executable target `Telegram` is defined in `Telegram/CMakeLists.txt` using the `nice_target_sources(Telegram ${src_loc} ...)` mechanism, augmented by component cmake modules in `Telegram/cmake/`.

### 2.1 Inventory of Milestone M1–M4 Code Artifacts

| Artifact | Location | Registration Location | Status | Object File Verified |
|---|---|---|---|---|
| `calls_box_controller.cpp/.h` | `Telegram/SourceFiles/calls/` | `Telegram/CMakeLists.txt:464-465` | **REGISTERED** | `calls_box_controller.obj` (Present) |
| `calls_group_display_coordinator.cpp/.h` | `Telegram/SourceFiles/calls/group/` | `Telegram/CMakeLists.txt:456-457` | **REGISTERED** | `calls_group_display_coordinator.obj` (Present) |
| `calls_group_floating_overlay.cpp/.h` | `Telegram/SourceFiles/calls/group/` | `Telegram/CMakeLists.txt:458-459` | **REGISTERED** | `calls_group_floating_overlay.obj` (Present) |
| `calls_group_viewport.cpp/.h` | `Telegram/SourceFiles/calls/group/` | `Telegram/CMakeLists.txt:448-449` | **REGISTERED** | `calls_group_viewport.obj` (Present) |
| `calls_group_members.cpp/.h` | `Telegram/SourceFiles/calls/group/` | `Telegram/CMakeLists.txt:424-425` | **REGISTERED** | `calls_group_members.obj` (Present) |
| `api_rich_tasks.cpp/.h` | `Telegram/SourceFiles/api/` | `Telegram/CMakeLists.txt:199-200` | **REGISTERED** | `api_rich_tasks.obj` (Present) |
| `download_manager_mtproto.cpp/.h` | `Telegram/SourceFiles/storage/` | `Telegram/CMakeLists.txt:1850-1851` | **REGISTERED** | `download_manager_mtproto.obj` (Present) |
| `window_main_menu.cpp/.h` | `Telegram/SourceFiles/window/` | `Telegram/CMakeLists.txt:2040-2041` | **REGISTERED** | `window_main_menu.obj` (Present) |
| `core_settings.cpp/.h` | `Telegram/SourceFiles/core/` | `Telegram/CMakeLists.txt:554-555` | **REGISTERED** | `core_settings.obj` (Present) |
| `data_histories.cpp/.h` | `Telegram/SourceFiles/data/` | `Telegram/CMakeLists.txt:705-706` | **REGISTERED** | `data_histories.obj` (Present) |
| `tgcalls/MediaManager.cpp` | `Telegram/ThirdParty/tgcalls/tgcalls/` | `Telegram/cmake/lib_tgcalls.cmake:44-45` | **REGISTERED** | `lib_tgcalls.dir/Debug/MediaManager.obj` (Present) |
| `tgcalls/GroupInstanceCustomImpl.cpp` | `Telegram/ThirdParty/tgcalls/tgcalls/group/` | `Telegram/cmake/lib_tgcalls.cmake:113-114` | **REGISTERED** | `lib_tgcalls.dir/Debug/GroupInstanceCustomImpl.obj` (Present) |
| `tgcalls/InstanceV2Impl.cpp` | `Telegram/ThirdParty/tgcalls/tgcalls/v2/` | `Telegram/cmake/lib_tgcalls.cmake:77-78` | **REGISTERED** | `lib_tgcalls.dir/Debug/InstanceV2Impl.obj` (Present) |
| `storage_sqlite_pragmas.h` | `Telegram/SourceFiles/storage/` | `Telegram/CMakeLists.txt` | **NOT REGISTERED** | Header-only (Needs CMake listing) |
| `lang.strings` | `Telegram/Resources/langs/` | `Telegram/cmake/generate_lang.cmake` | **REGISTERED** | Keys verified (`lng_group_call_open_chat`, `lng_group_call_context_pin_to_grid`) |

### 2.2 Recommendation for `storage_sqlite_pragmas.h`
In `Telegram/CMakeLists.txt`, add `storage/storage_sqlite_pragmas.h` between lines 1883 and 1884:
```cmake
    storage/storage_sparse_ids_list.cpp
    storage/storage_sparse_ids_list.h
    storage/storage_sqlite_pragmas.h
    storage/storage_user_photos.cpp
    storage/storage_user_photos.h
```

---

## 3. Build Tree Configuration & Toolchain Inspection

### 3.1 CMake Configuration (`out/CMakeCache.txt`)
- **Generator**: `Visual Studio 17 2022`
- **Platform / Architecture**: `x64` (`CMAKE_GENERATOR_PLATFORM:STRING=x64`)
- **Build Types Supported**: `Debug;Release;MinSizeRel;RelWithDebInfo`
- **MSVC Toolset**: MSVC 14.44.35207 (`C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/`)
- **Windows SDK**: `10.0.26100.0` (`mt.exe`, `rc.exe`)
- **Python**: `C:/Users/kyleh/ThirdParty/python/Scripts/python` (Python 3.14.7)
- **NuGet**: `C:/Users/kyleh/ThirdParty/NuGet/nuget.exe`
- **Qt Version**: `Qt 5.15.19` (`C:/Users/kyleh/Libraries/win64/Qt-5.15.19/lib/cmake/Qt5`)

### 3.2 Compiler & Linker Settings
- **C++ Standard & Features**: C++20 (`/Zc:__cplusplus`, `/permissive-`, `/utf-8`, `/W4`, `/MP`, `/EHsc`, `/bigobj`)
- **MSVC Runtime Library**: `/MTd` for Debug (`CMAKE_MSVC_RUNTIME_LIBRARY="MultiThreaded$<$<CONFIG:Debug>:Debug>"`)
- **Debug Flags (CXX)**: `/Ob0 /Od /RTC1`
- **Debug Info**: Program Database (`/Zi` into `.pdb`)
- **Linker Options**: `/machine:x64 /INCREMENTAL:NO /DEPENDENTLOADFLAG:0x800 $<$<CONFIG:Debug>:/NODEFAULTLIB:LIBCMT /DEBUG:FASTLINK>`

---

## 4. Object Files & Target State

The generated solution `out/Telegram.sln` and project `out/Telegram/Telegram.vcxproj` contain 9,369 lines of configuration defining targets for `Telegram`, `lib_tgcalls`, `td_ui`, `lib_base`, `lib_crl`, `lib_storage`, and associated subsystems.

### 4.1 Verified Build Output Files
- **Primary Binary**: `c:\Users\kyleh\tdesktop\out\Debug\Telegram.exe` (492,176,384 bytes)
- **Debug Symbol File**: `c:\Users\kyleh\tdesktop\out\Debug\Telegram.pdb` (2,988,711,936 bytes)
- **Runtime Execution Log**: `c:\Users\kyleh\tdesktop\out\Debug\log.txt` (Confirmed valid launch with DirectX 11 / ANGLE OpenGL ES 3.0 runtime, 10,993 cached language keys, and audio/video device enumeration).

---

## 5. Potential Issues & Verification Checklist

1. **`storage_sqlite_pragmas.h` Registration**:
   While `storage_sqlite_pragmas.h` is a header-only utility and does not produce a standalone `.obj`, registering it in `Telegram/CMakeLists.txt` guarantees inclusion in Visual Studio solution filters and ensures compliance with Feature 56.
2. **Build Cleanliness**:
   No unresolved externals, missing libraries, or dangling symbols were detected across the Debug compilation output.
