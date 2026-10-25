# Builds a HeliSR release: both firmware builds, HeliSR Configurator with Qt
# deployed next to it, avrdude, the licences, an Inno Setup installer and a
# portable zip.
#   .\build-release.ps1
#   .\build-release.ps1 -QtDir C:\Qt\6.8.3\mingw_64 -MinGWDir C:\Qt\Tools\mingw1310_64
# Needs: the Arduino IDE 2.x (firmware), Qt 6 + MinGW (configurator), Inno Setup 6.
# Results land in Software\packaging\output\.
param(
    [string]$QtDir = (Join-Path $env:USERPROFILE 'Qt\6.8.3\mingw_64'),
    [string]$MinGWDir = (Join-Path $env:USERPROFILE 'Qt\Tools\mingw1310_64'),
    [string]$AvrdudeDir,        # default: the Arduino IDE's newest avrdude
    [string]$InnoDir,           # default: Inno Setup 6 in its usual places
    [switch]$SkipFirmware,
    [switch]$SkipInstaller
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$software = Split-Path $here
$work = Join-Path $here 'work'
$stage = Join-Path $work 'stage'
$output = Join-Path $here 'output'

function Step($text) { Write-Host "`n=== $text" -ForegroundColor Cyan }
function Check($what) { if ($LASTEXITCODE -ne 0) { throw "$what failed ($LASTEXITCODE)" } }
function Need($path, $what) { if (-not (Test-Path $path)) { throw "$what not found: $path" } }

# ------------------------------------------------------------------ tools --
Need (Join-Path $QtDir 'bin\qmake.exe') 'Qt (use -QtDir)'
Need (Join-Path $MinGWDir 'bin\mingw32-make.exe') 'MinGW (use -MinGWDir)'
if (-not $AvrdudeDir) {
    $root = Join-Path $env:LOCALAPPDATA 'Arduino15\packages\arduino\tools\avrdude'
    Need $root 'The Arduino IDE''s avrdude (use -AvrdudeDir)'
    $AvrdudeDir = (Get-ChildItem $root -Directory | Sort-Object Name | Select-Object -Last 1).FullName
}
Need (Join-Path $AvrdudeDir 'bin\avrdude.exe') 'avrdude.exe'
Need (Join-Path $AvrdudeDir 'etc\avrdude.conf') 'avrdude.conf'
if (-not $SkipInstaller) {
    if (-not $InnoDir) {
        $InnoDir = @((Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6'),
                     (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6'),
                     (Join-Path $env:ProgramFiles 'Inno Setup 6')) |
                   Where-Object { Test-Path (Join-Path $_ 'ISCC.exe') } | Select-Object -First 1
    }
    if (-not $InnoDir) { throw 'Inno Setup 6 not found (use -InnoDir, or -SkipInstaller)' }
}
$env:PATH = (Join-Path $QtDir 'bin') + ';' + (Join-Path $MinGWDir 'bin') + ';' + $env:PATH

# the app's version, from version.h
$versionH = Get-Content (Join-Path $software 'configurator\src\version.h') -Raw
$v = foreach ($part in 'MAJOR', 'MINOR', 'PATCH') {
    if ($versionH -notmatch "#define ${part}_VERSION (\d+)") { throw "version.h: no ${part}_VERSION" }
    $Matches[1]
}
$version = $v -join '.'
Write-Host "HeliSR Configurator $version"
Write-Host "Qt:      $QtDir"
Write-Host "avrdude: $AvrdudeDir"

if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force $stage, $output | Out-Null

# --------------------------------------------------------------- firmware --
$firmware = Join-Path $software 'firmware'
if (-not $SkipFirmware) {
    Step 'Firmware, 16 MHz'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $firmware 'build.ps1')
    Check 'Firmware build (16 MHz)'
    Step 'Firmware, 8 MHz'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $firmware 'build.ps1') -Mhz8
    Check 'Firmware build (8 MHz)'
}
New-Item -ItemType Directory -Force (Join-Path $stage 'firmware') | Out-Null
foreach ($f in @(@('noserial', 'HeliSR_16MHz.hex'), @('noserial-8mhz', 'HeliSR_8MHz.hex'))) {
    $hex = Join-Path $firmware "build\$($f[0])\HeliSR.ino.hex"
    Need $hex 'Firmware .hex (run without -SkipFirmware)'
    Copy-Item $hex (Join-Path $stage "firmware\$($f[1])")
}

# ----------------------------------------------------------- configurator --
Step 'HeliSR Configurator'
$build = Join-Path $work 'build'
New-Item -ItemType Directory -Force $build | Out-Null
Push-Location $build
try {
    & qmake (Join-Path $software 'configurator\HeliSRConfigurator.pro') 'CONFIG+=release'
    Check 'qmake'
    & mingw32-make -j $env:NUMBER_OF_PROCESSORS
    Check 'mingw32-make'
} finally { Pop-Location }
$exe = Join-Path $build 'src\release\HeliSRConfigurator.exe'
Need $exe 'HeliSRConfigurator.exe'
Copy-Item $exe $stage

Step 'Qt libraries (windeployqt)'
& windeployqt --release --no-translations --no-system-d3d-compiler --no-opengl-sw `
    --skip-plugin-types 'tls,networkinformation,generic' (Join-Path $stage 'HeliSRConfigurator.exe')
Check 'windeployqt'

# ------------------------------------------------------ avrdude, licences --
Step 'avrdude and licences'
$avr = Join-Path $stage 'avrdude'
New-Item -ItemType Directory -Force $avr | Out-Null
Copy-Item (Join-Path $AvrdudeDir 'bin\avrdude.exe'), (Join-Path $AvrdudeDir 'etc\avrdude.conf') $avr
Copy-Item (Join-Path $AvrdudeDir 'LICENSE.txt') $avr

$lic = Join-Path $stage 'licenses'
New-Item -ItemType Directory -Force $lic | Out-Null
Copy-Item (Join-Path $software 'LICENSE') (Join-Path $lic 'GPL-3.0.txt')
Copy-Item (Join-Path $here 'licenses\LGPL-3.0.txt') $lic
Copy-Item (Join-Path $AvrdudeDir 'LICENSE.txt') (Join-Path $lic 'GPL-2.0.txt')
Copy-Item (Join-Path $MinGWDir 'licenses\gcc\COPYING.RUNTIME') (Join-Path $lic 'GCC-RUNTIME-EXCEPTION.txt')
Copy-Item (Join-Path $MinGWDir 'licenses\winpthreads\COPYING') (Join-Path $lic 'winpthreads-COPYING.txt')
Copy-Item (Join-Path $here 'THIRD-PARTY-NOTICES.txt'), (Join-Path $here 'README.txt') $stage
Copy-Item (Join-Path $software 'NOTICE.md') $stage

# ------------------------------------------------------------- packages --
$base = "HeliSR-Configurator-$version"
if (-not $SkipInstaller) {
    Step 'Installer (Inno Setup)'
    & (Join-Path $InnoDir 'ISCC.exe') /Q "/DAppVersion=$version" "/DStageDir=$stage" "/DOutputDir=$output" `
        "/DSourceDir=$software" "/DOutputName=$base-Setup" (Join-Path $here 'HeliSRConfigurator.iss')
    Check 'ISCC'
}

Step 'Portable zip'
$zip = Join-Path $output "$base-portable.zip"
if (Test-Path $zip) { Remove-Item $zip }
# entry by entry: Windows PowerShell's Compress-Archive and ZipFile write
# backslashes into the zip's paths, which other unzip tools mishandle
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$stream = [IO.File]::Open($zip, [IO.FileMode]::Create)
$archive = New-Object IO.Compression.ZipArchive($stream, [IO.Compression.ZipArchiveMode]::Create)
try {
    Get-ChildItem $stage -Recurse -File | ForEach-Object {
        $name = $_.FullName.Substring($stage.Length + 1).Replace('\', '/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $name,
            [IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
} finally { $archive.Dispose(); $stream.Dispose() }

$sums = Get-ChildItem $output -File | Where-Object { $_.Name -like "$base*" -and $_.Name -notlike '*SHA256SUMS*' } | ForEach-Object {
    '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name
}
# LF line endings, so sha256sum -c also accepts it
[IO.File]::WriteAllText((Join-Path $output "$base-SHA256SUMS.txt"), (($sums -join "`n") + "`n"))
Step 'Done'
Get-ChildItem $output -File | Where-Object { $_.Name -like "$base*" } |
    ForEach-Object { '{0,-48} {1,10:N0} bytes' -f $_.Name, $_.Length }
