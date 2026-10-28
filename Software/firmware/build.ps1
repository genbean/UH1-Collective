# Builds the HeliSR firmware with the Arduino IDE's own arduino-cli.
#   .\build.ps1                 HeliSR Rev 3.0, 5 V / 16 MHz Pro Micro, without the USB serial port
#   .\build.ps1 -Board 4.0      HeliSR Rev 4.0 (AS5600s over I2C). Never put this
#                               build on a Rev 3.0 board: it drives pins the
#                               board's chips drive too
#   .\build.ps1 -Serial         with the Arduino USB serial port (for development:
#                               lets the Arduino IDE upload without a RST double-tap)
#   .\build.ps1 -Test           test firmware: the PC drives the logic in lockstep
#                               (test\hsr-lockstep.ps1); not for normal use
#   .\build.ps1 -Port COM5      build and upload
# The .hex lands in Software\firmware\build\<variant>\: noserial, serial and
# noserial-test for Rev 3.0, the same with "rev40-" in front for Rev 4.0.
# The options combine (-Board 4.0 -Serial).
# HeliSR supports the 5 V / 16 MHz Pro Micro only.
param([string]$Port, [switch]$Serial, [switch]$Test, [ValidateSet('3.0', '4.0')][string]$Board = '3.0')

$ErrorActionPreference = 'Stop'
$cli = Join-Path $env:LOCALAPPDATA 'Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
$config = Join-Path $env:USERPROFILE '.arduinoIDE\arduino-cli.yaml'
$sketch = Join-Path $PSScriptRoot 'HeliSR'

if ($Serial) { $variant = 'serial'; $flags = '-DHSR_USB_SERIAL=1' }
else         { $variant = 'noserial'; $flags = '-DCDC_DISABLED' }
$clock = '16000000L'
if ($Test) { $variant = "$variant-test"; $flags = "$flags -DHSR_TEST_STEP" }
if ($Board -eq '4.0') { $variant = "rev40-$variant"; $flags = "$flags -DHSR_BOARD_REV=40" }
$out = Join-Path $PSScriptRoot "build\$variant"
# Each variant keeps its own build cache: arduino-cli fails to clean a shared
# one when the build flags change.
$cache = Join-Path $PSScriptRoot "build\cache-$variant"

# Windows PowerShell mangles quotes in arguments to an .exe, so the compile
# line goes through --% (passed as written, %VAR% expanded). None of these
# variables may be empty: an empty one is deleted and --% would pass its name.
$env:HSR_CONFIG = $config; $env:HSR_OUT = $out; $env:HSR_CACHE = $cache
$env:HSR_SKETCH = $sketch; $env:HSR_FLAGS = $flags; $env:HSR_CLOCK = $clock
& $cli --% --config-file "%HSR_CONFIG%" compile -b arduino:avr:leonardo --warnings all --build-path "%HSR_CACHE%" --build-property "build.f_cpu=%HSR_CLOCK%" --build-property "build.extra_flags={build.usb_flags} %HSR_FLAGS%" --output-dir "%HSR_OUT%" "%HSR_SKETCH%"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Port) {
    & $cli --config-file $config upload -b arduino:avr:leonardo -p $Port --input-dir $out $sketch
    exit $LASTEXITCODE
}
