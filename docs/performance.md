# Performance and black-pitch fix (locally built game)

## Cause (measured, this PC)
The engine defaults differ from what the real launcher sets (`port_code/Launcher/sim_coreStreetLauncher/LauncherForm.cs` lines 1255-1370 and the engine cvar defaults in `ReXGlue/src`):

| Setting | Engine default | Effect |
|---|---|---|
| `readback_resolve` | `none` | Stadium floor drawn through a resolve that must be read back: pitch black |
| `vsync` | `true` | Launcher comment: host VSync makes every GPU wait cost two refreshes (lag) |
| `occlusion_query_enable` | `true` | Extra GPU work |
| `fullscreen` | `true` | Display scaling cost on small devices |
| log level | `info` | Disk writes every 100 ms from online/kernel trace lines |

## Menu frame rate (50 s at the menus, `Guest frame timing` log lines)
| Run | Avg FPS | Min FPS | Worst frame |
|---|---|---|---|
| Stock defaults | about 58 | 29 | 165-482 ms |
| `balanced` (some readback, fxaa) | 44.0 | 21.8 | 106 ms |
| `light` + `some` readback | 46.0 | 23.7 | 100 ms |
| `potato` + `some` readback | 46.9 | 24.1 | 101 ms |
| `light` + `fast` readback | 101.8 | 82.2 | 15 ms |

`some` readback halves the frame rate here. With `light` + `fast` the pitch was checked by the user in a match and drew correctly.

## Use
`tools/play.ps1` (copy in `dist/Game/play.ps1`, launchers `play-light.cmd`, `play-potato.cmd`):
`-Profile balanced | light | potato`, `-Readback full|some|fast|none`, `-Fullscreen`, `-Measure` (logs frame timing to `Logs\<profile>.log`).
All profiles: D3D12, guest 1280x720, internal scale 1, no host vsync, sync-readback list kept to the floor address only, no MSAA, no occlusion queries.
`light`: no post effect, fast readback, 960x540 window, logging off. `potato`: same with a 640x360 window and the frame limiter on `auto`.

## Limits (not solved)
* Internal render size cannot go below the game's 1280x720 (the scale cvar is an integer, 1 minimum), so a very weak GPU still renders 720p; only presentation size shrinks.
* CPU cost of the recompiled game code was not reduced.
* `potato` was benchmarked at the menus only on this PC, not on a weak machine or in a match; `fast` readback was checked visually only for the pitch.
* Other missing-render reports (besides the pitch) were not reproduced.

## Root cause of the in-match lag: wrong GPU (found and fixed)
This laptop has an Intel UHD (integrated) and an NVIDIA RTX 3060 (discrete). The engine log said `DXGI adapter: Intel(R) UHD Graphics`, because the launcher's "Automatic" GPU choice (settings `"Gpu": 0`) leaves the pick to the engine, which takes the first adapter. In a match that gave a steady ~27 FPS (menus 100+ FPS). On the RTX 3060 the user reported it very smooth.
Adapter indices on this PC: 0 = Intel UHD, 1 = RTX 3060, 2 = Microsoft Basic Render Driver (software).

Second cost found in matches: `some` readback copied about 15 full-frame render targets (3.5-4 MB each) to the CPU every frame (8-9 FPS on the Intel GPU). The default `light` profile now skips those large ranges (`REX_READBACK_SOME_SKIP_ADDRS`, list in `tools/play.ps1`) and keeps the floor (`1282B000`); the user confirmed correct colors. `fast` readback removed the luminance copies too and left colors dark, so it is no longer the default.

## Permanent fix (what was changed)
| Where | Change | Status |
|---|---|---|
| `fifa-street-12/settings.json` (backup `settings.json.bak-before-gpu-fix`) | `"Gpu": 0` (Automatic) to `2` (the RTX 3060 entry of the launcher's list: 0 Automatic, 1 Intel, 2 RTX, 3 WARP) | applied; takes effect the next time the existing launcher starts |
| `port_code/Launcher/sim_coreStreetLauncher/DxgiAdapters.cs`, `LauncherForm.cs` | "Automatic" now picks the hardware adapter with the most dedicated memory (D3D12 only) | source patched, launcher **not rebuilt** |
| `tools/play.ps1` | picks the same adapter automatically (`GPU auto-select: adapter 1 = NVIDIA ...`) | working, verified in the engine log |
| `tools/prefer-nvidia-gpu.reg` | Windows per-app GPU preference `GpuPreference=2` for the game and launcher executables | **not applied**: it is a Windows setting, double-click it yourself |

## Still not solved
* A phone cannot run this build (x86-64 Windows, Direct3D 12 / Vulkan recompiled Xbox 360 code); it would need an ARM64 Android port of the runtime and renderer, touch controls and tuning.
* Internal render size floors at 1280x720; CPU cost of the recompiled code was not reduced.
* The skip list was captured in one match on one PC; other stadiums or modes may resolve other large ranges.

## Measured in a match on the RTX 3060 (default `light` profile, `-Measure` logging on)
Menus about 990 FPS. In a match: mostly 110-145 FPS with worst frame 10-13 ms (smooth), a 785 ms spike while the match loads (DLC module load, missing optional `charactercmn_1300_3.rx3` / `fifacamera_1300.dat` files reported by the VFS as not found, then falling back), and occasional ~38-40 ms hitches (7 windows in 10 minutes: 19:42:35, 19:42:45, 19:43:40, 19:43:55, 19:44:20, 19:45:05, 19:48:25).
Checked and not the cause of most hitches: `some` readback invalidation refreshes (50 events; 4 of the 7 hitch windows had none in the 5 s before), shader/pipeline creation (no creation lines after load), logging volume (the logging used for the measurement is off in normal runs; about 23,500 lines were online-socket polling every 100 ms plus the readback table). The cause of the remaining hitches is **unknown**; next step would be a CPU/GPU capture (PIX or Tracy: the runtime ships `TracyClient.dll`).


## Hitch profiling aid (added)

`tools/hitch_trace.ps1` records an ETW trace (`wpr -start CPU -start GPU`) around a play session of the `light` profile; open the resulting `hitch.etl` in Windows Performance Analyzer. It must run in an elevated shell and was **not run yet** (it needs someone playing a match). The unexplained ~38-40 ms spikes (7 in ~10 minutes) remain open until a trace shows which thread or GPU packet is busy at those times.

## Final settings (measured, RTX 3060 Laptop, demo/attract 3D scene, `light` profile)

| Setting | FPS (typical) | Note |
|---|---|---|
| readback `fast`, 1280x720 window | 83 | not faster than `some`; pitch stays dark in matches |
| readback `fast`, 1920x1080 | 48 | cost grows with window size |
| readback `fast`, 2400x1350 | 15-28 | |
| readback `none`, 1920x1080 | 225 | black pitch (shows readback is the cost) |
| readback `some`, 1280x720 | 120-140 | validated colors |
| readback `some`, 1920x1080 | 82-88 | |
| readback `some`, fullscreen | 115 | same as windowed |
| old `light` skip list (any size) | n/a | green/yellow tint, black pitch: **removed** |

Decision: all profiles use `some`; `light` and `potato` start fullscreen (`-Windowed` for a window), no skip list. `play.cmd` / `play-light.cmd` start it. The in-match hitch trace (`tools/hitch.etl`, 3.2 GB) was recorded but not analysed here.
