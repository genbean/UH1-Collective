# HeliSR USB test tool: talks to the firmware's settings channel and the
# joystick through Windows' own HID and joystick APIs (no downloads needed).
#
#   .\hsr-usb-test.ps1 list               HID interfaces of HeliSR boards
#   .\hsr-usb-test.ps1 info               the firmware's INFO reply
#   .\hsr-usb-test.ps1 read               read and summarise the settings
#   .\hsr-usb-test.ps1 setname "My Box"   change the USB name, save, restart
#   .\hsr-usb-test.ps1 defaults           factory settings, save, restart
#   .\hsr-usb-test.ps1 params             live data (raw analog, inputs, buttons)
#   .\hsr-usb-test.ps1 joystick           what Windows' joystick API sees
#   .\hsr-usb-test.ps1 rawjoy             raw joystick input reports from the HID interface
#   .\hsr-usb-test.ps1 bootloader         start the Pro Micro's bootloader
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
param([Parameter(Mandatory = $true)][string]$Command, [string]$Arg)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'hsr-usb-lib.ps1')

switch ($Command) {
    'list' {
        $devs = Get-HsrInterfaces
        if (-not $devs) { 'No HeliSR HID interfaces found.'; break }
        $devs | ForEach-Object {
            '{0:X4}:{1:X4} v{2:X4}  usage page 0x{3:X4} usage 0x{4:X2}  in {5} out {6}  "{7}" / "{8}" serial {9}' -f `
                $_.Vid, $_.Pid, $_.Version, $_.UsagePage, $_.Usage, $_.InLen, $_.OutLen, $_.Manufacturer, $_.Product, $_.Serial
        }
    }
    'info' {
        Open-Settings
        try {
            $r = Invoke-Cmd $CMD.INFO
            $d = $r[4..63]
            'firmware 0x{0:X4}  protocol {1}  board 0x{2:X2}  config version {3}  config size {4}  {5} MHz  USB serial port {6}  unique ID {7:X8}  settings from EEPROM {8}  stack never used {9} B  commands {10}  replies dropped {11}  longest pass {12} us' -f `
                [BitConverter]::ToUInt16($d, 0), $d[2], $d[3], [BitConverter]::ToUInt16($d, 4), [BitConverter]::ToUInt16($d, 6), $d[8], $d[9], [BitConverter]::ToUInt32($d, 10), $d[14], [BitConverter]::ToUInt16($d, 15), [BitConverter]::ToUInt16($d, 17), [BitConverter]::ToUInt16($d, 19), [BitConverter]::ToUInt16($d, 21)
        } finally { [Hsr]::Close() }
    }
    'read' {
        Open-Settings
        try { $c = Read-Config; Show-Config $c; 'CRC 0x{0:X4}' -f [Hsr]::Crc16($c, $CONFIG_SIZE) } finally { [Hsr]::Close() }
    }
    'setname' {
        if (-not $Arg) { throw 'setname needs a name' }
        Open-Settings
        try {
            $c = Read-Config
            for ($i = 0; $i -lt 26; $i++) { $c[2 + $i] = 0 }
            $b = [Text.Encoding]::ASCII.GetBytes($Arg)
            [Array]::Copy($b, 0, $c, 2, [math]::Min(25, $b.Length))
            Write-Config $c
            "Saved; the board restarts with the name '$Arg'."
        } finally { [Hsr]::Close() }
    }
    'defaults' {
        Open-Settings
        try {
            Invoke-Cmd $CMD.DEFAULTS | Out-Null
            $c = Read-Config
            Write-Config $c
            'Factory settings saved; the board restarts.'
        } finally { [Hsr]::Close() }
    }
    'params' {
        Open-Settings
        try {
            $p = New-Object byte[] 69
            $a = Invoke-Cmd $CMD.PARAMS 0; [Array]::Copy($a, 4, $p, 0, 60)
            $b = Invoke-Cmd $CMD.PARAMS 1; [Array]::Copy($b, 4, $p, 60, 9)
            $s16 = { param($o) [BitConverter]::ToInt16($p, $o) }
            'firmware 0x{0:X4}' -f [BitConverter]::ToUInt16($p, 0)
            'axis out   ' + ((0..7 | ForEach-Object { & $s16 (18 + 2 * $_) }) -join ' ')
            'analog raw ' + ((0..8 | ForEach-Object { [BitConverter]::ToUInt16($p, 34 + 2 * $_) }) -join ' ')
            'physical   ' + (($p[52..59] | ForEach-Object { '{0:X2}' -f $_ }) -join ' ')
            'logical    ' + (($p[60..67] | ForEach-Object { '{0:X2}' -f $_ }) -join ' ')
        } finally { [Hsr]::Close() }
    }
    'joystick' {
        $dev = Get-HsrInterfaces | Select-Object -First 1
        if (-not $dev) { throw 'No HeliSR board found' }
        [Hsr]::Joysticks($dev.Vid, $dev.Pid)
    }
    'badcommit' {
        # Negative test: a COMMIT with the wrong checksum must be refused and nothing saved.
        Open-Settings
        try {
            $c = Read-Config
            for ($i = 0; $i -lt $CHUNKS; $i++) {
                $len = [math]::Min($CHUNK, $CONFIG_SIZE - $i * $CHUNK)
                $d = New-Object byte[] $len; [Array]::Copy($c, $i * $CHUNK, $d, 0, $len)
                Invoke-Cmd $CMD.WRITE $i $d | Out-Null
            }
            $crc = [Hsr]::Crc16($c, $CONFIG_SIZE) -bxor 0xFFFF
            $r = [Hsr]::Transact([byte]$CMD.COMMIT, 0, [byte[]]@(($crc -band 0xFF), ($crc -shr 8)), 2000)
            if (-not $r) { 'FAIL: no reply' } elseif ($r[3] -eq 3) { 'OK: refused with ERR_CRC' } else { "FAIL: status $($STATUS[$r[3]])" }
            Invoke-Cmd $CMD.RELOAD | Out-Null
        } finally { [Hsr]::Close() }
    }
    'rawjoy' {
        $dev = Get-HsrInterfaces | Where-Object { $_.UsagePage -eq 1 -and $_.Usage -eq 4 } | Select-Object -First 1
        if (-not $dev) { throw 'No HeliSR joystick interface found' }
        "input report length $($dev.InLen)"
        [Hsr]::RawReports($dev.Path, 5, 1000)
    }
    'bootloader' {
        Open-Settings
        try {
            # A READ first pauses the firmware's input processing for 2 s, so the
            # bootloader command is answered at once.
            $paused = $false
            for ($i = 0; $i -lt 20 -and -not $paused; $i++) { $paused = [bool][Hsr]::Transact([byte]$CMD.READ, 0, $null, 300) }
            if (-not $paused) { throw 'The firmware did not answer.' }
            Invoke-Cmd $CMD.BOOTLOADER 0 ([Text.Encoding]::ASCII.GetBytes('bootloader run')) | Out-Null
            'Bootloader requested.'
        } finally { [Hsr]::Close() }
    }
    default { throw "Unknown command '$Command'" }
}
