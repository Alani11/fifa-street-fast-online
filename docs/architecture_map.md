# Workspace architecture map (recon of `port_code` and `engine_data`)

Everything here was read from files in the workspace. Not everything in `port_code` was read: the 40 C# launcher and installer sources were mapped by `Program.cs`, `main.cpp`, `fifastreet_app.h` and file names, not line by line.

## What the project is
ReStreet is a Windows port of the Xbox 360 game FIFA Street (2012), built by static recompilation with the ReXGlue SDK (`docs/BUILDING.md`, pinned ReXGlue commit `c94f5ebd…`, plus a local patch). The repository ships a launcher, an installer, a Linux launcher and viewer, and an asset explorer. It contains **no game logic source**: the gameplay code is the recompiled guest code, generated locally from the user's own ISO and not present here.

## Layers and entry points

| Layer | Path | Entry point | Role |
|---|---|---|---|
| Recompiled game host | `Installer/recomp-template/src` | `main.cpp`: `REX_DEFINE_APP(fifastreet, FifastreetApp::Create)` | Host app around the generated code (`generated/default/fifastreet_init.h`, not in workspace) |
| Guest modules | `fifadllzf.xex.dll`, `FootballCompEngzf.xex.dll`, `default.xex` | n/a | Game code, built into `fifastreet_fifadllzf_xex.dll` etc. (CMake targets `fifastreet_fifadllzf_xex`, `fifastreet_FootballCompEngzf_xex`) |
| Launcher (Windows) | `Launcher/sim_coreStreetLauncher/Program.cs` | `Main`; flags `--preview-lobby`, `--preview-friends`, `--preview` | WinForms launcher, friends/lobby UI, updater, save restore, Discord presence |
| Launcher (Linux) | `Launcher/sim_coreStreetLauncher.Linux/` | `Program.cs` | Proton/Wine launcher and installer (`Proton.cs`, `Setup.cs`, `GameStart.cs`) |
| Installer | `Installer/sim_coreStreetSetupTool/Program.cs` | `Main` (`--install-test <ISO> <dest>`, `--update-test` per docs) | ISO extraction, SHA-256 checks of the three modules, credit patch (`CreditPatch.cs`, uses `LzxDecoder.cs` and `chunklzx`) |
| Asset explorer | `Tools/ReStreetAssetScan/Program.cs` | commands `list`, `extract`, `buttons`; no-arg player front end | Reads BIG archives, decodes `chunklzx`/`chunkzip`/RefPack: the reference for `docs/binary_formats.md` |
| Linux viewer | `Viewer/resources/app/main.js` | Electron `main` | Window for the launcher page on Wine/Proton |
| Release build | `Installer/BuildPrecompiled.py`, `ci/*.json` | script | Packages runtime backends and payload |

## Scripting and engine hooks
* Host hooks (virtual methods of `rex::ReXApp`, `fifastreet_app.h`): the project overrides `OnPreSetup` (defaults `gpu_plugin` to `xenos`), `OnConfigurePaths` (searches the executable folder, `GameData`, parent for `default.xex`), `OnCreateDialogs` (window title "FIFA Street PC") and `OnPostSetup` (sets cvar `gpu_allow_invalid_fetch_constants = true`). The commented list names the unused hooks: `OnPostInitLogging`, `OnLoadXexImage`, `OnPostLoadXexImage`, `OnShutdown`, achievements overlays.
* `native_libc_hooks.cpp` and `stubs.cpp` are guest-DLL kernel/libc stubs; `config/verify_*.py` check generated code (`verify_ctr_region.py` asserts specific dispatcher functions such as `sub_8264B0AC`).
* Game scripting is Lua inside `data0.big` (`data/fifarna/lua/*.lua`, 26 files: asset binders such as `ball.lua`, `player.lua`, `stadium.lua`, plus `boot.lua`, `initialize.lua`, `settings.lua`, `postfx.lua`). These are rendering/asset scripts. They call `gSportsRNA`/`gRenderables`; no gameplay physics is in them.
* UI is Scaleform-style `.big` movie archives under `data/ui` (`chunklzx` members), not analyzed.

## Configuration schemas

| File | Format | Keys (examples) |
|---|---|---|
| `engine_data/settings.json` | JSON | `ExePath`, `GamePath`, `Resolution`, `RefreshRate`, `GraphicsApi`, `PostEffect`, `InternalResolutionScale`, `VSync`, `VRR`, `MSAA`, `OnlineMode` |
| `engine_data/Binaries/ajustes-del-port.txt` | `KEY=value` environment lines | `REX_GPU_PLUGIN`, `REX_CACHE_ROOT`, `REX_LOG_LEVEL`, `REX_MNK_MODE`, many `REX_*` renderer switches with Spanish names |
| `Installer/backend-manifest.json`, `ci/backend-manifest.json` | JSON | `backends.D3D12 / Vulkan` with `runtimeHash` and `gpuHash` (SHA-256) |
| `engine_data/online.json` | JSON | `server`, `name`, `key`. The `key` is a per-player secret; its value is deliberately not reproduced here and should be rotated if this workspace is shared |
| `engine_data/Binaries/Logs/perf-report.json` | JSON | session seconds and per-scene `fps_avg`, `fps_1_low`, `stutters_50ms`, `worst_ms` |
| `engine_data/online-patch.json`, `presence.json`, `ui/lang.js` | JSON / JS | online patch data, presence, launcher translations |
| In-game INI (inside `data0.big`) | `KEY = value // comment`, `[SECTION]` | `streetdefault.ini`, `heroperf.ini`, `ant.ini`, `platform.ini`, `product.ini`, `buttondata*.ini`, `accomplishments.ini` (see `physics_spec.md`, `state_machine.md`) |

## File extensions seen

| Extension | Where | Handled in |
|---|---|---|
| `.big` | BIG4 outer, BIGF nested, many with `chunklzx` or `chunkzip` bodies | `binary_formats.md` sections 1–2 |
| `.vlt`, `.bin`, `.opt` | Attrib vault databases | section 3 |
| `.dat` | neural nets (`neuralnet`), cameras | section 4; cameras not analyzed |
| `.seq`, `.libfinal` | skill-move AI sequences | section 5 |
| `.db`, `-meta.xml` | t3db database | section 6 |
| `.ini`, `.lua`, `.xml`, `.txt`, `.ttf`, `.cdb` | text, fonts, render db | read as text where relevant |
| `.sbs` | sound bank (`SBKS`) | `data4.big`, not analyzed |
| `.fxo` | shader objects inside `shader.big` (`chunkzip`) | not analyzed |
| `.rx3`, `.ast`, `.skl`, `.anm`, `.msh` | referenced by Lua paths or scan list only | **no such file in workspace** |

## Dependency notes
`CMakeLists.txt` builds `fifastreet` with `rexglue_setup_target(fifastreet GPU_PLUGINS xenos)`; the runtime pair `rexruntime.dll` + `rexgpu-xenos.dll` (D3D12 or Vulkan) must come from the same build. `Linux - Proton&Wine.md` and `Launcher/.../Proton.cs` cover the Wine path. `licenses/` lists ReXGlue (BSD-3), FFmpeg, SDL3, imgui, glslang, Vulkan, LLVM, Ninja, .NET and MonoGame's MS-PL LZX decoder.

## Recompiled game code (built locally)
`Installer/BuildFifaStreet.ps1 -SourceBuild` (with `-GameData` pointing at the extracted ISO's `Game` folder) runs `rexglue` over `default.xex`, `fifadllzf.xex.dll` and `FootballCompEngzf.xex.dll`, writing `generated/{default,fifadllzf_xex,FootballCompEngzf_xex}` and compiling them into `fifastreet.exe` plus two module DLLs. The workspace's `tools/*.py` index that output (`physics_spec.md` section 7). Build notes: the ReXGlue release needs the VS 2022 toolchain and a Windows 11 SDK; git on Windows must not leave symlinks as text files (19 submodule links were copied by hand); `Installer/compiler` was junctioned to the scoop LLVM because the script looks for `C:\Program Files\LLVM` or `Installer\compiler`.

## Tooling used for this documentation
`/universal-modder:game-recon`, `reverse-engineering` and `reverse-engineer-anything` were loaded and followed by hand (BIG/chunk parsing, byte-level checks, binary probes); `um scan` and the REA MCP server were not run. `understand-anything-knowledge-graph`, `codebase-design` and `skill-finder` were loaded, but their commands (`/understand`, the skills-hub MCP tools) are not available in this session, so **no knowledge graph or skill chain was generated**.
