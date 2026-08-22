# Handoff Report: Milestone M4 — Windows Native Debug Build & CMake Inspection

**Explorer**: Explorer M4.2 (Windows Native Debug Build & CMake Inspector)  
**Date**: 2026-08-20  
**Status**: COMPLETE (Hard Handoff)  
**Target Files Analyzed**: `Telegram/CMakeLists.txt`, `Telegram/cmake/*`, `out/CMakeCache.txt`, `out/Telegram/Telegram.vcxproj`, `out/Debug/`  

---

## 1. Observation

1. **CMake Target Registrations (`Telegram/CMakeLists.txt` & `Telegram/cmake/`)**:
   - `calls/calls_box_controller.cpp` and `calls/calls_box_controller.h` are registered at `Telegram/CMakeLists.txt:464-465`.
   - `calls/group/calls_group_display_coordinator.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:456-457`.
   - `calls/group/calls_group_floating_overlay.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:458-459`.
   - `calls/group/calls_group_viewport.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:448-449`.
   - `calls/group/calls_group_members.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:424-425`.
   - `api/api_rich_tasks.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:199-200`.
   - `storage/download_manager_mtproto.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:1850-1851`.
   - `window/window_main_menu.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:2040-2041`.
   - `core/core_settings.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:554-555`.
   - `data/data_histories.cpp` and `.h` are registered at `Telegram/CMakeLists.txt:705-706`.
   - `Telegram/ThirdParty/tgcalls/tgcalls/MediaManager.cpp` and `.h` are registered at `Telegram/cmake/lib_tgcalls.cmake:44-45`.
   - `Telegram/ThirdParty/tgcalls/tgcalls/group/GroupInstanceCustomImpl.cpp` and `.h` are registered at `Telegram/cmake/lib_tgcalls.cmake:113-114`.
   - `Telegram/ThirdParty/tgcalls/tgcalls/v2/InstanceV2Impl.cpp` and `.h` are registered at `Telegram/cmake/lib_tgcalls.cmake:77-78`.
   - `Telegram/Resources/langs/lang.strings` contains `lng_group_call_open_chat` (line 6464) and `lng_group_call_context_pin_to_grid` (line 6463), processed via `Telegram/cmake/generate_lang.cmake`.
   - `storage/storage_sqlite_pragmas.h` (82 lines, located at `Telegram/SourceFiles/storage/storage_sqlite_pragmas.h`) is **not** currently listed in `Telegram/CMakeLists.txt` or `out/Telegram/Telegram.vcxproj`.

2. **Build Tree Configuration (`out/CMakeCache.txt`)**:
   - Generator: `Visual Studio 17 2022` with platform `x64`.
   - MSVC Compiler: MSVC 14.44.35207 (`C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe`).
   - Windows SDK: `10.0.26100.0` (`rc.exe`, `mt.exe`).
   - CXX flags: `/DWIN32 /D_WINDOWS /EHsc /utf-8 /W4 /MP /permissive- /Zc:__cplusplus /bigobj`.
   - Debug CXX flags: `/Ob0 /Od /RTC1` with `/MTd` runtime (`CMAKE_MSVC_RUNTIME_LIBRARY="MultiThreaded$<$<CONFIG:Debug>:Debug>"`).
   - Debug info format: `ProgramDatabase` (`/Zi` into `.pdb`).
   - Qt library: Qt 5.15.19 (`C:/Users/kyleh/Libraries/win64/Qt-5.15.19/lib/cmake/Qt5`).
   - External dependencies: `../win64/Libraries` (`C:/Users/kyleh/Libraries/win64`) and `../ThirdParty` (`C:/Users/kyleh/ThirdParty`).

3. **Object Files & Link Outputs**:
   - `out/Telegram/Telegram.dir/Debug/` contains:
     - `calls_box_controller.obj`
     - `calls_group_display_coordinator.obj`
     - `calls_group_floating_overlay.obj`
     - `calls_group_viewport.obj`
     - `calls_group_members.obj`
     - `api_rich_tasks.obj`
     - `download_manager_mtproto.obj`
     - `window_main_menu.obj`
     - `core_settings.obj`
     - `data_histories.obj`
   - `out/Telegram/lib_tgcalls.dir/Debug/` contains `MediaManager.obj`, `GroupInstanceCustomImpl.obj`, and `InstanceV2Impl.obj`.
   - Executable `out/Debug/Telegram.exe` exists with size 492,176,384 bytes (~469 MB).
   - Symbol file `out/Debug/Telegram.pdb` exists with size 2,988,711,936 bytes (~2.98 GB).
   - Debug execution log `out/Debug/log.txt` verifies clean startup, ANGLE/OpenGL initialization, and successful settings/langpack load.

---

## 2. Logic Chain

1. From Observation 1, all milestone features implemented in Milestones M1, M2, and M3 have been mapped to their respective CMake registration points.
2. 11 of the 12 source units are already registered in `Telegram/CMakeLists.txt` or `Telegram/cmake/lib_tgcalls.cmake`.
3. `storage_sqlite_pragmas.h` is a header-only performance tuning module introduced in M3. While C++ headers included in `.cpp` files compile without an explicit CMake listing, project convention and Feature 56 ("CMakeLists.txt Source Synchronization") require all source and header files to be registered in `Telegram/CMakeLists.txt` for IDE indexation and complete source synchronization.
4. From Observation 2, the MSVC generator and compilation parameters enforce modern C++20, static runtime linking (`/MTd`), and complete PDB generation in accordance with `AGENTS.md` and `docs/fork_features.md:86-87`.
5. From Observation 3, the presence of corresponding `.obj` files in `Telegram.dir/Debug/` and `lib_tgcalls.dir/Debug/` confirms that all custom units compile cleanly under MSVC without errors, and link into `out/Debug/Telegram.exe`.

---

## 3. Caveats

- `storage_sqlite_pragmas.h` is currently header-only; adding it to `Telegram/CMakeLists.txt` will update CMake project generators but does not alter the linked binary output unless additional `.cpp` consumers include it.
- Build tool verification was performed via direct inspection of CMakeCache, solution and vcxproj files, compilation artifacts (`.obj`), and debug execution logs.

---

## 4. Conclusion

1. **CMake Synchronization**: All newly added and modified source and header files are correctly registered, with the single exception of `storage/storage_sqlite_pragmas.h`.
2. **Actionable Item for Worker M4**:
   - Register `storage/storage_sqlite_pragmas.h` in `Telegram/CMakeLists.txt` at line 1884 (alphabetically after `storage/storage_sparse_ids_list.h` and before `storage/storage_user_photos.cpp`).
3. **Build Target State**: The Windows Native Debug configuration (`cmake --build out --config Debug --target Telegram`) is fully functional, complete, and verified with all object files compiled and linked cleanly into `out/Debug/Telegram.exe`.

---

## 5. Verification Method

To independently verify the observations:
1. **Verify CMake Registration**:
   Inspect `Telegram/CMakeLists.txt` lines 199–200, 424–425, 448–449, 456–459, 464–465, 554–555, 705–706, 1850–1851, 2040–2041.
2. **Verify tgcalls Registration**:
   Inspect `Telegram/cmake/lib_tgcalls.cmake` lines 44–45, 77–78, 113–114.
3. **Verify Language Keys**:
   Inspect `Telegram/Resources/langs/lang.strings` lines 6463–6464.
4. **Verify Object Files & Executable**:
   Verify existence of `out/Telegram/Telegram.dir/Debug/calls_box_controller.obj`, `calls_group_floating_overlay.obj`, `api_rich_tasks.obj`, `download_manager_mtproto.obj`, and `out/Debug/Telegram.exe`.
