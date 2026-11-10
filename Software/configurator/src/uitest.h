#ifndef UITEST_H
#define UITEST_H

#include <QStringList>

class MainWindow;

// Page round-trip test: random valid settings are shown on every page and
// written back from the pages; every byte must come back unchanged.
//   HeliSRConfigurator --ui-test [count] [--seed n]
//   HeliSRConfigurator --ui-device-test [--seed n]   (Write and Read buttons with a device)
//   HeliSRConfigurator --ui-test-file <profile.cfg> ...   (profiles through the pages)
//   HeliSRConfigurator --ui-screenshot <file.png>   (the Board page, with made-up sensor
//                                                    readings, no device needed)
// Random settings use only what the HeliSR Rev 4.0 board has.
namespace UiTest
{
    bool isUiTestCommand(const QStringList &args);
    int run(MainWindow &window, const QStringList &args);
}

#endif // UITEST_H
