# Compiles FreeJoy's original buttons.c, encoders.c, axis_to_buttons.c and
# analog.c (unmodified) for the PC, with stand-in STM32 headers, plus the
# bridge. Writes the object files to <Out>\fj and returns their paths.
# Used by run-host-tests.ps1 -FreeJoy.
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
param([string]$MinGW, [string]$FreeJoy, [string]$Out)

$ErrorActionPreference = 'Stop'
$gcc = Join-Path $MinGW 'gcc.exe'
$src = Join-Path $FreeJoy 'application'
$dir = Join-Path $Out 'fj'
New-Item -ItemType Directory -Force $dir | Out-Null

# FreeJoy's headers and the four sources, side by side so their #include "..."
# lines find each other; then the stand-ins for the STM32 and LED headers.
Copy-Item (Join-Path $src 'Inc\*.h') $dir -Force
foreach ($f in 'buttons.c', 'encoders.c', 'axis_to_buttons.c', 'analog.c') { Copy-Item (Join-Path $src "Src\$f") $dir -Force }
Copy-Item (Join-Path $PSScriptRoot 'freejoy\stm32f10x.h') $dir -Force
Set-Content -Path (Join-Path $dir 'stm32f10x_conf.h') -Value '/* stand-in: no STM32 peripheral library */' -Encoding ascii
Set-Content -Path (Join-Path $dir 'ws2812b.h') -Value "#include `"common_types.h`"`nvoid WS2812b_Init(void);" -Encoding ascii
Copy-Item (Join-Path $PSScriptRoot 'freejoy\fj_bridge.c'), (Join-Path $PSScriptRoot 'freejoy\fj_bridge.h') $dir -Force

# Rename FreeJoy's globals that share a name with HeliSR's. -fwrapv: signed
# overflow wraps, as on FreeJoy's ARM target, instead of trapping.
$flags = @('-std=gnu11', '-O1', '-g', '-fwrapv', '-w', "-I$dir",
           '-Dshifts_state=fj_shifts_state', '-Draw_axis_data=fj_raw_axis_data',
           '-Dscaled_axis_data=fj_scaled_axis_data', '-Dout_axis_data=fj_out_axis_data')

$objs = @()
foreach ($f in 'buttons.c', 'encoders.c', 'axis_to_buttons.c', 'analog.c', 'fj_bridge.c') {
    $o = Join-Path $dir ($f -replace '\.c$', '.o')
    $ErrorActionPreference = 'Continue'
    & $gcc @flags -c (Join-Path $dir $f) -o $o 2>&1 | ForEach-Object { "$_" } | Write-Host
    $ok = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($ok -ne 0) { throw "FreeJoy build failed: $f" }
    $objs += $o
}
return $objs
