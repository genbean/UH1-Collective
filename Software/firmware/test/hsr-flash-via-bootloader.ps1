# Flash a HeliSR board without the Arduino IDE: ask the running firmware to
# start the bootloader over the settings channel, wait for the bootloader's
# serial port, and write the .hex with avrdude. This is the path HeliSR
# Configurator will use.
#   .\hsr-flash-via-bootloader.ps1 -Hex ..\build\noserial\HeliSR.ino.hex
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
param([Parameter(Mandatory = $true)][string]$Hex)

$ErrorActionPreference = 'Stop'
$Hex = (Resolve-Path $Hex).Path
$avrdudeDir = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Arduino15\packages\arduino\tools\avrdude') -Directory | Sort-Object Name | Select-Object -Last 1
$avrdude = Join-Path $avrdudeDir.FullName 'bin\avrdude.exe'
$conf = Join-Path $avrdudeDir.FullName 'etc\avrdude.conf'

function Get-SerialPorts {
    Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match '\((COM\d+)\)' } |
        ForEach-Object { [pscustomobject]@{ Port = $Matches[1]; Id = $_.DeviceID; Name = $_.Name } }
}

$before = @(Get-SerialPorts | ForEach-Object { $_.Id })
& (Join-Path $PSScriptRoot 'hsr-usb-test.ps1') bootloader
$sw = [Diagnostics.Stopwatch]::StartNew()

# The bootloader enumerates with its own USB IDs, so it shows up as a port
# with a device ID that wasn't there before.
$port = $null
while ($sw.ElapsedMilliseconds -lt 8000 -and -not $port) {
    Start-Sleep -Milliseconds 200
    $port = Get-SerialPorts | Where-Object { $before -notcontains $_.Id } | Select-Object -First 1
}
if (-not $port) { throw 'The bootloader port did not appear within 8 s.' }
"Bootloader on $($port.Port) after $($sw.ElapsedMilliseconds) ms: $($port.Id)"

# Run avrdude as a plain process: it reports progress on stderr, which
# Windows PowerShell would otherwise turn into an error and abort mid-flash.
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $avrdude
$psi.Arguments = "`"-C$conf`" -patmega32u4 -cavr109 -P$($port.Port) -b57600 -D `"-Uflash:w:${Hex}:i`""
$psi.UseShellExecute = $false
$psi.RedirectStandardError = $true
$psi.RedirectStandardOutput = $true
$proc = [Diagnostics.Process]::Start($psi)
$errText = $proc.StandardError.ReadToEndAsync()
$outText = $proc.StandardOutput.ReadToEnd()
$proc.WaitForExit()
$outText + $errText.Result
if ($proc.ExitCode -ne 0) { throw "avrdude failed ($($proc.ExitCode))" }
'Flashed.'
