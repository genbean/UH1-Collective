#ifndef UITEST_H
#define UITEST_H

#include <QStringList>

class MainWindow;

// Page round-trip test: random valid settings are shown on every page and
// written back from the pages; every byte must come back unchanged.
//   HeliSRConfigurator --ui-test [count] [--seed n] [--board 3.0|4.0]
//   HeliSRConfigurator --ui-device-test [--seed n]   (Write and Read buttons with a device)
//   HeliSRConfigurator --ui-test-file <profile.cfg> ... [--board 3.0|4.0]   (profiles through the pages)
//   HeliSRConfigurator --ui-screenshot <file.png> [--board 3.0|4.0]  (the Board page; on Rev 4.0 with
//                                                                    made-up sensor readings, no device needed)
// The pages show one board throughout: --board, else the one they showed last
// (a device's, for --ui-device-test). Random settings use only what that board has.
namespace UiTest
{
    bool isUiTestCommand(const QStringList &args);
    int run(MainWindow &window, const QStringList &args);
}

#endif // UITEST_H
