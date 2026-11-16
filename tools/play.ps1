<#
.SYNOPSIS  Launch the locally built fifastreet.exe with the same REX_* settings the real launcher uses, in three profiles.
.DESCRIPTION
  Why this exists: the engine defaults are wrong for this game. readback_resolve defaults to "none" (stadium floors render black),
  vsync defaults to true (every GPU wait costs two refreshes = lag), occlusion queries are on, and the window starts fullscreen.
  Profiles (all D3D12, guest video mode 1280x720, internal resolution 1x):
    balanced : launcher "Balanced" profile  - fxaa, readback "some" (the validated setting that keeps floors clean)
    light    : no post effect, no MSAA, no occlusion queries, readback "some" with the large full-frame ranges skipped (smooth + correct colors),
               frame stats off, logging off, 960x540 window
    potato   : light + 640x360 window and the frame limiter left on auto
    -Adapter N picks the DXGI GPU (on the dev PC 0 = Intel UHD, 1 = RTX 3060; default -1 let Windows pick the Intel one = the lag cause)
    -SkipAddrs a,b,c skips 'some' readback of those resolve ranges (large full-frame targets; keeps the floor 1282B000)
    -Readback full|some|fast|none overrides the readback mode (some = launcher-validated floors but ~2x slower at the menus here; fast = pitch confirmed fine in a match on this PC)
  Usage:  .\play.ps1 -Profile light            (menus + match; read Logs\perf-report.json afterwards for FPS per scene)
          .\play.ps1 -Profile balanced -Fullscreen
#>
param(
  [ValidateSet('balanced','light','potato')][string]$Profile = 'light',
  [string]$Exe = 'C:\src\sim_recomp\dist\Game\fifastreet.exe',
  [string]$GameData = 'C:\Users\junai\Downloads\fifa-street-12\Game',
  [switch]$Fullscreen,
  [switch]$Online,      # join the community ReStreet online service (server/name/key read from online.json; the key is only passed to the game, never printed)
  [string]$OnlineConfig = 'C:/Users/junai/Downloads/fifa-street-12/online.json',
  [switch]$Windowed,   # light/potato now start fullscreen (fills the screen); -Windowed gives the small window
  [ValidateSet('','full','some','fast','none')][string]$Readback = '',
  [int]$Adapter = -1,
  [string]$SkipAddrs = '',
  [switch]$Measure,
  [hashtable]$ExtraEnv = @{}
)

# Pick the hardware GPU with the most dedicated memory (the discrete GPU on a laptop). Windows/the engine otherwise take the first adapter = integrated GPU.
function Get-BestAdapter {
  try {
    Add-Type -ErrorAction Stop -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public static class GpuPick {
  [DllImport("dxgi.dll", ExactSpelling=true)] static extern int CreateDXGIFactory1(ref Guid iid, out IntPtr f);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int EnumA(IntPtr f, uint i, out IntPtr a);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetD(IntPtr a, out Desc d);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Desc { [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string Description; public uint V,D,S,R; public UIntPtr Mem, Sys, Shared; public uint Lo; public int Hi; public uint Flags; }
  static T M<T>(IntPtr o, int slot) where T: class { return (T)(object)Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(Marshal.ReadIntPtr(o), slot*IntPtr.Size), typeof(T)); }
  public static int Best(out string name) {
    name = ""; int best = -1; ulong mem = 0; int count = 0; var iid = new Guid("770aae78-f26f-4dba-a829-253c83d1b387"); IntPtr f;
    if (CreateDXGIFactory1(ref iid, out f) != 0) return -1;
    var en = M<EnumA>(f, 12);
    for (uint i = 0; ; i++) { IntPtr a; if (en(f, i, out a) != 0) break; Desc d; M<GetD>(a, 10)(a, out d); Marshal.Release(a);
      if ((d.Flags & 2) != 0) continue; count++; ulong m = d.Mem.ToUInt64(); if (m > mem) { mem = m; best = (int)i; name = d.Description; } }
    return count < 2 ? -1 : best;
  }
}
"@
    $n = ''; $i = [GpuPick]::Best([ref]$n); if ($i -ge 0) { Write-Host "GPU auto-select: adapter $i = $n" }; return $i
  } catch { Write-Host "GPU auto-select failed: $($_.Exception.Message)"; return -1 }
}
$ErrorActionPreference = 'Stop'
if ($Adapter -lt 0) { $Adapter = Get-BestAdapter }
if ($Profile -ne 'balanced' -and -not $Windowed) { $Fullscreen = $true }   # fullscreen measured as fast as windowed with 'some' readback
$dir = Split-Path $Exe
$logs = Join-Path $dir 'Logs'; New-Item -ItemType Directory -Force $logs | Out-Null
$e = @{
  REX_GAME_DATA_ROOT = $GameData
  REX_VIDEO_MODE_WIDTH = '1280'; REX_VIDEO_MODE_HEIGHT = '720'
  REX_DRAW_RESOLUTION_SCALE_X = '1'; REX_DRAW_RESOLUTION_SCALE_Y = '1'
  REX_GUEST_VBLANK_UNLOCKED = 'true'
  REX_VSYNC = 'false'; REX_TRUE_VSYNC = '0'                    # blocking host vsync doubles every GPU wait
  REX_FRAME_LIMITER_MIN_HZ = '1000'
  REX_READBACK_SOME_SYNC_BELOW = '0'                          # keep only the sync readback that keeps floors clean (1282B000)
  REX_READBACK_MEMEXPORT = 'true'; REX_D3D12_READBACK_MEMEXPORT = 'true'; REX_READBACK_MEMEXPORT_FAST = 'true'
  REX_CLEAR_MEMORY_PAGE_STATE = 'false'
  REX_ASYNC_SHADER_COMPILATION = 'true'
  REX_D3D12_READBACK_SHORT_WAIT = 'true'; REX_D3D12_READBACK_SPIN_US = '500'
  REX_RENDER_TARGET_PATH_D3D12 = ''
  REX_D3D12_ALLOW_VARIABLE_REFRESH_RATE_AND_TEARING = 'false'
  REX_LOG_VERBOSE = 'false'
  REX_PERF_REPORT = (Join-Path $logs 'perf-report.json')
  REX_FULLSCREEN = $(if ($Fullscreen) { 'true' } else { 'false' })
}
switch ($Profile) {
  'balanced' { $e += @{ REX_SWAP_POST_EFFECT='fxaa'; REX_NATIVE_2X_MSAA='false'; REX_OCCLUSION_QUERY_ENABLE='false'
                        REX_READBACK_RESOLVE='some'; REX_WINDOW_WIDTH='1280'; REX_WINDOW_HEIGHT='720'; REX_LOG_LEVEL='warn' } }
  'light'    { $e += @{ REX_SWAP_POST_EFFECT='none'; REX_NATIVE_2X_MSAA='false'; REX_OCCLUSION_QUERY_ENABLE='false'
                        REX_READBACK_RESOLVE='some'; REX_ANISOTROPIC_OVERRIDE='-1'; REX_WINDOW_WIDTH='1280'; REX_WINDOW_HEIGHT='720'
                        REX_LOG_LEVEL='off' } }
  'potato'   { $e += @{ REX_SWAP_POST_EFFECT='none'; REX_NATIVE_2X_MSAA='false'; REX_OCCLUSION_QUERY_ENABLE='false'
                        REX_READBACK_RESOLVE='some'; REX_ANISOTROPIC_OVERRIDE='-1'
                        REX_WINDOW_WIDTH='640'; REX_WINDOW_HEIGHT='360'; REX_LOG_LEVEL='off' } }
}
if ($Profile -eq 'potato') { $e['REX_FRAME_LIMITER_MIN_HZ'] = 'auto' }
if ($Readback) { $e['REX_READBACK_RESOLVE'] = $Readback }
$defaultSkip = '12493000,1283F000,12BC3000,12BD7000,12F5D000,1335D000,1375D000,13F5D000,15094000,150A8000'   # full-frame resolve ranges seen in a match (3.5-4 MB each); 'some' read ~15 of them per frame = 8 FPS. The floor (1282B000) is kept.
# NOTE: the old default skip list produced a green tint / black pitch; 'some' alone is correct and was measured faster than 'fast'. -SkipAddrs stays for experiments.
if ($Adapter -ge 0) { $e['REX_D3D12_ADAPTER'] = [string]$Adapter }
if ($SkipAddrs) { $e['REX_READBACK_SOME_SKIP_ADDRS'] = $SkipAddrs }
if ($Online) {
  if (Test-Path $OnlineConfig) {
    $oc = Get-Content $OnlineConfig -Raw | ConvertFrom-Json
    $e['FIFASTREET_SERVER'] = [string]$oc.server; $e['FIFASTREET_PLAYER_NAME'] = [string]$oc.name; $e['FIFASTREET_PLAYER_KEY'] = [string]$oc.key
    $e['FIFASTREET_ONLINE_EXPERIMENT'] = '1'; $e['FIFASTREET_ONLINE_ENDPOINT_PROBE'] = '1'; $e['FIFASTREET_NET_DIAG'] = ''
    Write-Host "online: server=$($oc.server) name=$($oc.name)"
  } else { Write-Host "online.json not found at $OnlineConfig - starting offline" }
}
foreach ($k in $ExtraEnv.Keys) { $e[$k] = [string]$ExtraEnv[$k] }
if ($Measure) { $e['REX_LOG_FRAME_STATS']='true'; $e['REX_LOG_LEVEL']='info'; $e['REX_LOG_FILE']=(Join-Path $logs "$Profile.log") }
foreach ($k in $e.Keys) { [Environment]::SetEnvironmentVariable($k, [string]$e[$k], 'Process') }
Get-ChildItem Env: | ? { $_.Name -like 'REX_*' -and -not $e.ContainsKey($_.Name) } | % { Remove-Item "Env:$($_.Name)" }
Remove-Item (Join-Path $logs 'perf-report.json') -ErrorAction SilentlyContinue
$p = Start-Process -FilePath $Exe -WorkingDirectory $dir -ArgumentList "--game_data_root=$GameData" -PassThru
"profile=$Profile pid=$($p.Id)  perf report: $($e.REX_PERF_REPORT)"
