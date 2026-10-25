# HeliSR logic test for a bare Pro Micro (nothing on the inputs).
# Uploads settings that drive the ported FreeJoy features from inputs that
# exist without hardware, checks the joystick report byte for byte, checks the
# settings read back exactly, then restores the factory settings.
#
#   - IN1 inverted                     -> button 1 on
#   - centre of a 3-position switch on IN3/IN4 (both open) -> button 2 on
#   - AX1 (floating, reads 0) gives X = minimum; X's axis-to-button ranges
#     0-85-170-255 make range 1 active -> button 15 on, button 16 off
#   - hat 1: up = range 1 (active), right/down/left = range 2 -> hat up
#   - Y inverted -> maximum;  Z with curve point 0 moved to 0 -> centre;
#     Rx = "equal" to Y -> maximum
#   - a PWM LED and a single LED on spare pins (exercises the code only)
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'hsr-usb-lib.ps1')

$fail = 0
function Check([string]$what, $got, $want) {
    if ("$got" -eq "$want") { "  PASS  $what" }
    else { "  FAIL  $what`n        got  $got`n        want $want"; $script:fail++ }
}

function AxisOff([int]$i) { 43 + 30 * $i }
function BtnOff([int]$j) { 283 + 3 * $j }
function A2bOff([int]$i) { 483 + 14 * $i }

function Get-JoyInterface { Get-HsrInterfaces | Where-Object { $_.UsagePage -eq 1 -and $_.Usage -eq 4 } | Select-Object -First 1 }
function Get-Info {
    Open-Settings
    try { $r = Invoke-Cmd $CMD.INFO; return , $r[4..63] } finally { [Hsr]::Close() }
}

"--- factory settings from the firmware"
Open-Settings
try {
    Invoke-Cmd $CMD.DEFAULTS | Out-Null
    $c = Read-Config
} finally { [Hsr]::Close() }
Check 'config_version' ([BitConverter]::ToUInt16($c, 0)) 2
Check 'axis 0 prescaler (FreeJoy default 100)' $c[(AxisOff 0) + 28] 100

"--- building the test settings"
$name = [Text.Encoding]::ASCII.GetBytes('HeliSR Logic Test')
for ($i = 0; $i -lt 26; $i++) { $c[2 + $i] = 0 }
[Array]::Copy($name, 0, $c, 2, $name.Length)

$c[(BtnOff 0) + 2] = $c[(BtnOff 0) + 2] -bor 1                  # button 1: inverted
$c[(BtnOff 1)] = 2; $c[(BtnOff 1) + 1] = 31                       # button 2: IN3, SWITCH_CENTER
$c[(BtnOff 14)] = 27                                              # button 15: X range 1
$c[(BtnOff 15)] = 28                                              # button 16: X range 2
$c[(BtnOff 16)] = 27; $c[(BtnOff 16) + 1] = 5                     # POV1 up    <- range 1
$c[(BtnOff 17)] = 28; $c[(BtnOff 17) + 1] = 6                     # POV1 right <- range 2
$c[(BtnOff 18)] = 28; $c[(BtnOff 18) + 1] = 7                     # POV1 down  <- range 2
$c[(BtnOff 19)] = 28; $c[(BtnOff 19) + 1] = 8                     # POV1 left  <- range 2

$o = A2bOff 0; $c[$o] = 0; $c[$o + 1] = 85; $c[$o + 2] = 170; $c[$o + 3] = 255; $c[$o + 13] = 3

$c[(AxisOff 1) + 6] = $c[(AxisOff 1) + 6] -bor 0x02               # Y inverted
$c[(AxisOff 2) + 7] = 0                                           # Z curve point 0: -100 -> 0
$c[(AxisOff 3) + 6] = $c[(AxisOff 3) + 6] -bor (3 -shl 3)         # Rx function EQUAL
$c[(AxisOff 3) + 21] = ($c[(AxisOff 3) + 21] -band 0xF8) -bor 1   # ... of axis 1 (Y)

$c[32 + 3] = 5; $c[604 + 0] = 30                                  # spare pin "5": PWM, 30 %
$c[32 + 0] = 4; $c[612 + 0] = 0; $c[612 + 1] = 0x0F -shl 3        # spare pin TX: LED <- button 1, steady

Open-Settings
try { Write-Config $c } finally { [Hsr]::Close() }
"  saved; waiting for the restart"
Start-Sleep -Seconds 4

"--- after the restart"
$joy = Get-JoyInterface
Check 'USB name' $joy.Product 'HeliSR Logic Test'
Check 'joystick report length (16 buttons, 4 axes, 1 hat)' $joy.InLen 12

Open-Settings
try { $back = Read-Config } finally { [Hsr]::Close() }
Check 'settings read back exactly' ([Hsr]::Crc16($back, $CONFIG_SIZE)) ([Hsr]::Crc16($c, $CONFIG_SIZE))

Start-Sleep -Milliseconds 2500     # a READ pauses processing and reports for 2 s
$lines = @([Hsr]::RawReports($joy.Path, 3, 1000) -split "`n" | Where-Object { $_ })
$raw = $lines[-1]
Check 'report' $raw '01-03-40-01-80-FF-7F-00-00-FF-7F-00'

$caps = [Hsr]::Joysticks($joy.Vid, $joy.Pid)
"  joystick API: $($caps.Trim() -replace "`n", ' / ')"
Check 'joystick API: 4 axes, 16 buttons' ($caps -match '4 axes, 16 buttons') $true
Check 'joystick API: hat up (POV 0)' ($caps -match 'POV 0\b') $true

$info = Get-Info
"  stack never used: $([BitConverter]::ToUInt16($info, 15)) B"

"--- restoring factory settings"
Open-Settings
try { Invoke-Cmd $CMD.DEFAULTS | Out-Null; $d = Read-Config; Write-Config $d } finally { [Hsr]::Close() }
Start-Sleep -Seconds 4
Check 'factory name back' (Get-JoyInterface).Product 'HeliSR'

if ($fail) { "$fail check(s) FAILED"; exit 1 } else { 'All checks passed.' }
