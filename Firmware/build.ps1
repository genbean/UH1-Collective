# Builds the Heli Collective firmware with the Arduino IDE's own arduino-cli,
# and uploads it when -Port is given (e.g. .\build.ps1 -Port COM5).
# The .hex lands in Firmware\build\HeliCollective.ino.hex.
param([string]$Port)

$ErrorActionPreference = 'Stop'
$cli = Join-Path $env:LOCALAPPDATA 'Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
$config = Join-Path $env:USERPROFILE '.arduinoIDE\arduino-cli.yaml'
$sketch = Join-Path $PSScriptRoot 'HeliCollective'
$out = Join-Path $PSScriptRoot 'build'

# Windows PowerShell mangles quotes and spaces in arguments to an .exe, so the
# compile line goes through --% (passed as written, %VAR% expanded).
$env:HC_CONFIG = $config; $env:HC_OUT = $out; $env:HC_SKETCH = $sketch
& $cli --% --config-file "%HC_CONFIG%" compile -b arduino:avr:leonardo --build-property "build.usb_product=\"Heli Collective\"" --output-dir "%HC_OUT%" "%HC_SKETCH%"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Port) {
    & $cli --config-file $config upload -b arduino:avr:leonardo -p $Port --input-dir $out $sketch
    exit $LASTEXITCODE
}
