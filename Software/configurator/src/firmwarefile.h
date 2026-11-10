#ifndef FIRMWAREFILE_H
#define FIRMWAREFILE_H

#include <QString>

// What a firmware .hex file is for, read from the build tag every HeliSR build
// carries (hsr_build_tag_t in helisr_protocol.h), and whether it may go on a
// board. Firmware for another board drives pins against the board's chips, so
// the flasher checks before it starts: only HeliSR Rev 4.0 firmware
// (HSR_BOARD_ID) goes on without a question.
namespace FirmwareFile
{
    struct Info
    {
        bool readable = false;      // an Intel HEX file that parsed
        bool tagged = false;        // has a HeliSR build tag
        int boardId = 0;            // the tag's board ID (HSR_BOARD_ID for this app's board), if tagged
        int cpuMhz = 0;
        int firmwareVersion = 0;
        int bytes = 0;              // of program
        QString error;              // why it isn't readable
    };

    Info read(const QString &path);

    enum Verdict {
        Ok,         // flash it
        Confirm,    // only if the user says the board is right (the window asks; the command line wants --board)
        Refuse,     // never
    };
    struct Check
    {
        Verdict verdict = Refuse;
        QString message;            // why, for the user; empty for Ok
    };

    //! deviceBoard: INFO's board_id of the HeliSR firmware running now, or 0 (none, or a new Pro Micro);
    //! statedBoard: HSR_BOARD_ID if the user says the Pro Micro is on a HeliSR Rev 4.0 board, else 0
    Check check(const Info &file, int deviceBoard, int statedBoard);

    //! "HeliSR firmware 1.0.0 for the Rev 4.0 board", or a note that the file doesn't say
    QString describe(const Info &file);
}

#endif // FIRMWAREFILE_H
