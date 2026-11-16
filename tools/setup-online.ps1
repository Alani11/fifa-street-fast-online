# First-run setup (safe to re-run): creates online.json (server + player name) and settings.json (paths + tuned defaults)
# next to the launcher. The launcher then makes your personal key. Nothing is overwritten if it already exists.
param([string]$Name = '', [string]$Server = 'restreet-pt.duckdns.org', [string]$GameData = '')
$here = $PSScriptRoot
$online = Join-Path $here 'online.json'
if (-not (Test-Path $online)) {
  if (-not $Name) { $Name = 'Player' + (Get-Random -Minimum 1000 -Maximum 9999) }
  @{ server = $Server; name = $Name.Trim() } | ConvertTo-Json | Set-Content $online -Encoding utf8
  Write-Host "online.json created: server=$Server name=$($Name.Trim())"
}
$settings = Join-Path $here 'settings.json'
if (-not (Test-Path $settings)) {
  # game data = the extracted game files (the folder that contains default.xex). Looked for next to this file, then in common places.
  $cands = @($GameData, (Join-Path $here 'Game'), (Join-Path (Split-Path $here) 'Game'), "$env:USERPROFILE\Downloads\fifa-street-12\Game") | ? { $_ }
  $game = $cands | ? { Test-Path (Join-Path $_ 'default.xex') } | Select-Object -First 1
  if (-not $game) { Write-Host "Game data not found. Put the extracted game files (folder containing default.xex) in a folder named Game next to this file, or run: setup-online.ps1 -GameData <folder>"; $game = (Join-Path $here 'Game') }
  # launcher GPU index = DXGI index + 1 (0 = Automatic = first adapter, often the weak integrated GPU): pick the adapter with most VRAM
  $gpu = 0
  try {
    Add-Type -ErrorAction Stop -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public static class GpuPick2 {
  [DllImport("dxgi.dll", ExactSpelling=true)] static extern int CreateDXGIFactory1(ref Guid iid, out IntPtr f);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int EnumA(IntPtr f, uint i, out IntPtr a);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetD(IntPtr a, out Desc d);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Desc { [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string Description; public uint V,D,S,R; public UIntPtr Mem, Sys, Shared; public uint Lo; public int Hi; public uint Flags; }
  static T M<T>(IntPtr o, int slot) where T: class { return (T)(object)Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(Marshal.ReadIntPtr(o), slot*IntPtr.Size), typeof(T)); }
  public static int Best() {
    int best = -1; ulong mem = 0; int count = 0; var iid = new Guid("770aae78-f26f-4dba-a829-253c83d1b387"); IntPtr f;
    if (CreateDXGIFactory1(ref iid, out f) != 0) return -1;
    var en = M<EnumA>(f, 12);
    for (uint i = 0; ; i++) { IntPtr a; if (en(f, i, out a) != 0) break; Desc d; M<GetD>(a, 10)(a, out d); Marshal.Release(a);
      if ((d.Flags & 2) != 0) continue; count++; ulong m = d.Mem.ToUInt64(); if (m > mem) { mem = m; best = (int)i; } }
    return count < 2 ? -1 : best;
  }
}
"@
    $b = [GpuPick2]::Best(); if ($b -ge 0) { $gpu = $b + 1 }
  } catch {}
  $s = [ordered]@{
    ExePath = (Join-Path $here 'Binaries\fifastreet.exe'); GamePath = $game
    Fullscreen = $true; Monitor = 0; GraphicsApi = 0; GameLanguage = 1; Gpu = $gpu; GpuUsesDxgi = $true
    PostEffect = 0; ReadbackResolve = 1; LogFrameStats = $false; InternalResolutionScale = 1
    ReadbackMemexport = $true; ReadbackMemexportFast = $true; ClearMemoryPageState = $false
    OcclusionQueries = $false; AsyncShaders = $true; VSync = $false; VRR = $true; MSAA = $false; Profile = 0; OnlineMode = $true
  }
  $s | ConvertTo-Json | Set-Content $settings -Encoding utf8
  Write-Host "settings.json created: game data = $game ; GPU index = $gpu"
}
