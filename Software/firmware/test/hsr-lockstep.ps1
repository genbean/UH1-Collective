# Replays a trace from the PC tests on a Pro Micro running the test firmware
# (build with -DHSR_TEST_STEP), and checks that every pass gives the same
# results on the AVR as on the PC: same buttons, inputs, axes, hats, shifts,
# LEDs and PWM. This catches anything that behaves differently on the AVR,
# such as arithmetic that overflows its 16-bit int.
#   .\host\run-host-tests.ps1 -Trace host\build\trace.txt -Random 10
#   .\hsr-lockstep.ps1 -Trace host\build\trace.txt
# The settings are written to the board's RAM only (never saved), and the
# board's own inputs are ignored until it restarts.
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
param([Parameter(Mandatory = $true)][string]$Trace)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'hsr-usb-lib.ps1')

$lines = Get-Content $Trace
$scenarios = @()
$cur = $null
foreach ($l in $lines) {
    if ($l.StartsWith('scenario ')) { $cur = [pscustomobject]@{ Name = $l.Substring(9); Config = $null; Steps = New-Object System.Collections.Generic.List[string] }; $scenarios += $cur }
    elseif ($l.StartsWith('config ')) { $cur.Config = $l.Substring(7) }
    elseif ($l.StartsWith('step ')) { $cur.Steps.Add($l) }
}
"{0} scenarios, {1} passes" -f $scenarios.Count, ($scenarios | ForEach-Object { $_.Steps.Count } | Measure-Object -Sum).Sum

Open-Settings
$failed = 0
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
    foreach ($s in $scenarios) {
        if ($s.Steps.Count -eq 0) { continue }
        $cfg = New-Object byte[] $CONFIG_SIZE
        for ($i = 0; $i -lt $CONFIG_SIZE; $i++) { $cfg[$i] = [Convert]::ToByte($s.Config.Substring(2 * $i, 2), 16) }
        for ($i = 0; $i -lt $CHUNKS; $i++) {
            $len = [math]::Min($CHUNK, $CONFIG_SIZE - $i * $CHUNK)
            $d = New-Object byte[] $len
            [Array]::Copy($cfg, $i * $CHUNK, $d, 0, $len)
            Invoke-Cmd $CMD.WRITE $i $d | Out-Null
        }
        $r = [Hsr]::Transact(0x70, 0, $null, 1000)
        if (-not $r -or $r[3] -ne 0) { throw 'TEST_APPLY refused: flash the test firmware (build.ps1 -Test) first' }

        $done = 0
        $err = [Hsr]::StepAll($s.Steps.ToArray(), [ref]$done)
        if ($err) { "  FAIL  {0}: {1}" -f $s.Name, $err; $failed++ }
        else { "  ok    {0} ({1} passes)" -f $s.Name, $done }
    }
    $r = Invoke-Cmd $CMD.INFO
    $d = $r[4..63]
    "stack never used during the run: {0} B; longest pass {1} us" -f [BitConverter]::ToUInt16($d, 15), [BitConverter]::ToUInt16($d, 21)
} finally { [Hsr]::Close() }

"{0} of {1} scenarios identical on the Pro Micro and the PC ({2:N0} s)" -f ($scenarios.Count - $failed), $scenarios.Count, $sw.Elapsed.TotalSeconds
if ($failed) { exit 1 }
