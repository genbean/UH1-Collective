#ifndef HELISRBOARD_H
#define HELISRBOARD_H

#include <QString>
#include <QVector>
#include "common_types.h"

// What the HeliSR boards offer and what the pages call each input. The pages
// show one board at a time: the connected device's, else the one chosen on the
// Board page. Both boards have the same settings layout. The numbering itself
// is the firmware's (helisr_config.h):
//   physical inputs 0-15 = IN1-IN16, 16-26 = spare pins by index, 27-63 = axis ranges;
//   analog sources 0-3 = AX1-AX4, 4-8 = the analog-capable spare pins,
//   9-10 = Rev 4.0's A2 and A3.
// Rev 4.0 has no spare pin 9 (pin 14) and reads AX1-AX4 over I2C.
namespace HsrBoard
{
    //! the board the pages show: HSR_BOARD_REV30 or HSR_BOARD_REV40
    int board();
    //! unknown board IDs are taken as Rev 3.0
    void setBoard(int boardId);
    bool isRev40();
    bool knownBoard(int boardId);
    //! "HeliSR Rev 3.0", "HeliSR Rev 4.0", or "board 0x50"
    QString boardName(int boardId);
    //! "Rev 3.0"
    QString revisionName(int boardId);

    //! whether the board shown has this spare pin
    bool spareExists(int spareIndex);
    //! Pro Micro silkscreen label of a spare pin: "TX", "RX", "4" ... "16"
    QString spareLabel(int spareIndex);
    //! "Pin TX", "Pin 4" ...
    QString spareName(int spareIndex);
    bool spareIsAnalog(int spareIndex);
    bool spareIsPwm(int spareIndex);
    //! PWM channel (0-3) of a spare pin, or -1
    int pwmChannelOfSpare(int spareIndex);
    //! spare pin of a PWM channel (pins 5, 6, 9, 10)
    int spareOfPwmChannel(int channel);
    //! analog source number (4-8) of a spare pin, or -1
    int analogSourceOfSpare(int spareIndex);
    //! spare pin of an analog source 4-8, or -1 for AX1-AX4, A2 and A3
    int spareOfAnalogSource(int source);
    //! "AX1" ... "AX4", "Pin 4" ..., "Pin A2"
    QString analogSourceName(int source);
    //! whether an analog source is available on the board shown with these pin settings
    bool analogSourceAvailable(int source, const pin_func_t *pins);

    //! "X", "Y" ... "Slider 2"
    QString axisName(int axis);

    struct PhysInput
    {
        int phys;           // firmware physical input number
        QString name;       // "IN5", "Pin TX", "X range 2"
        QString shortName;  // for the round state indicators: "IN5", "TX", "X2"
    };
    //! The physical inputs that exist with these pin settings and axis-range counts, in number order.
    QVector<PhysInput> physicalInputs(const pin_func_t *pins, const int *a2bCounts);
    //! Name of a physical input number with these settings, or an empty string if it doesn't exist.
    QString physicalInputName(int phys, const pin_func_t *pins, const int *a2bCounts);
}

#endif // HELISRBOARD_H
