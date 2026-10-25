#ifndef CLI_H
#define CLI_H

#include <QStringList>

// HeliSR Configurator from the command line, using the same device and
// flasher code as the window:
//   HeliSRConfigurator --info
//   HeliSRConfigurator --read <profile.cfg>       save the device's settings to a profile
//   HeliSRConfigurator --write <profile.cfg>      write a profile to the device
//   HeliSRConfigurator --write-defaults           write the factory settings
//   HeliSRConfigurator --params [seconds]         print the live readings
//   HeliSRConfigurator --flash <file.hex>         update the connected device's firmware
//   HeliSRConfigurator --flash-new <file.hex> [--port COMx]   flash a Pro Micro without HeliSR firmware
//   HeliSRConfigurator --roundtrip                write, read back and compare, then restore
//   HeliSRConfigurator --save-defaults <file.cfg>   the factory settings as a profile (no device)
// Add --device <n> (from 1) to pick one of several boards.
namespace Cli
{
    bool isCliCommand(const QStringList &args);
    int run(const QStringList &args);
}

#endif // CLI_H
