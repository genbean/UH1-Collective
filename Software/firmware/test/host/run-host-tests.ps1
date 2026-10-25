# Builds and runs the HeliSR PC tests: the firmware's own logic files,
# compiled for the PC with stand-ins for the board, driven by scripted inputs.
#   .\run-host-tests.ps1                      run the scenario tests
#   .\run-host-tests.ps1 -FreeJoy <path>      also compare with FreeJoy's original code
#                                             (path to a FreeJoy source checkout)
#   .\run-host-tests.ps1 -Trace trace.txt     write a trace for ..\hsr-lockstep.ps1
#   .\run-host-tests.ps1 -Random 10           also run 10 random scenarios (into the trace)
# Needs MinGW-w64 g++ (e.g. Qt's: aqt install-tool windows desktop tools_mingw1310
# qt.tools.win64_mingw1310). Pass -MinGW <bin folder> if it isn't in the default place.
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
param(
    [string]$MinGW = (Join-Path $env:USERPROFILE 'Qt\Tools\mingw1310_64\bin'),
    [string]$FreeJoy,
    [string]$Trace,
    [int]$Random = 0
)

$ErrorActionPreference = 'Stop'
$gpp = Join-Path $MinGW 'g++.exe'
if (-not (Test-Path $gpp)) { throw "g++ not found in $MinGW" }

$here = $PSScriptRoot
$fw = Join-Path $here '..\..\HeliSR\src'
$out = Join-Path $here 'build'
New-Item -ItemType Directory -Force $out | Out-Null

$sources = @('sim.cpp', 'tests.cpp', 'main.cpp', 'random_settings.cpp' | ForEach-Object { Join-Path $here $_ })
$sources += @('settings.cpp', 'buttons.cpp', 'axes.cpp', 'leds.cpp', 'pipeline.cpp', 'joy_layout.cpp' | ForEach-Object { Join-Path $fw $_ })

# Trap (rather than report) undefined behaviour such as signed overflow, so no
# runtime library is needed; -ftrapv covers signed + - * as well.
$flags = @('-std=gnu++17', '-O1', '-g', '-Wall', '-Wextra', '-Wno-unused-parameter',
           '-fsanitize=undefined', '-fsanitize-trap=undefined', '-ftrapv',
           "-I$(Join-Path $here 'stubs')", "-I$fw", '-static')

if ($FreeJoy) {
    $fj = Join-Path $FreeJoy 'application'
    if (-not (Test-Path (Join-Path $fj 'Src\buttons.c'))) { throw "No FreeJoy source in $FreeJoy" }
    # The comparison works on FreeJoy's 0-4095 analog range, with HeliSR's
    # fixes of FreeJoy bugs switched off (HSR_FREEJOY_EXACT) so results can be
    # demanded identical; the fixes have their own tests in the normal build.
    $flags += @('-DHSR_WITH_FREEJOY', '-DHSR_FREEJOY_EXACT', '-DHSR_RAW_MAX=4095')
    $sources += Join-Path $here 'freejoy_compare.cpp'
    $fjObjs = & (Join-Path $here 'build-freejoy.ps1') -MinGW $MinGW -FreeJoy $FreeJoy -Out $out
    $sources += $fjObjs
}

$exe = Join-Path $out 'hsr_host_tests.exe'
# Windows PowerShell turns a native program's stderr (compiler warnings) into
# errors under 'Stop', so relax it for the compiler and check the exit code.
$ErrorActionPreference = 'Continue'
& $gpp @flags @sources -o $exe 2>&1 | ForEach-Object { Write-Host "$_" }
$built = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($built -ne 0) { throw 'Build failed' }

$runArgs = @()
if ($Trace) { $runArgs += @('--trace', $Trace) }
if ($Random) { $runArgs += @('--random', $Random) }
& $exe @runArgs
exit $LASTEXITCODE
