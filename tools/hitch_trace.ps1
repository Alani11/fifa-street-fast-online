<#
.SYNOPSIS  Record a Windows ETW trace (CPU sampling + GPU + context switches) while you play, to find the ~40 ms in-match hitches.
.DESCRIPTION
  Needs an elevated PowerShell (wpr requires admin). Nothing is changed on the system; wpr only records.
  1. Run:  .\hitch_trace.ps1            (starts recording, launches the light profile)
  2. Play a match for 1-2 minutes, note roughly when the stutters happen, quit the game.
  3. The script stops the trace and writes hitch.etl next to this file.
  4. Open hitch.etl in Windows Performance Analyzer (free, Microsoft Store). Look at:
       - "CPU Usage (Sampled)" grouped by Thread, around the stutter times: which thread (and which fifastreet_* / rexgpu symbol) is busy
       - "GPU Utilization" / "Video" graphs: is a GPU packet 40 ms long?
       - "CPU Usage (Precise)" Waits: a thread blocked on a fence/event for 40 ms
  Send me the top stacks (or the thread name) and I can tell whether it is guest code, readback, or the host GPU queue.
#>
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$etl = Join-Path $here 'hitch.etl'
wpr -start CPU -start GPU -filemode
try {
  & (Join-Path $here 'play.ps1') -Profile light | Out-Host
  Read-Host 'Play, then press Enter here after you close the game'
} finally {
  wpr -stop $etl
  "trace written: $etl"
}
