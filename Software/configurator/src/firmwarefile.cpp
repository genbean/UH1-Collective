#include "firmwarefile.h"
#include <QByteArray>
#include <QCoreApplication>
#include <QFile>
#include <cstring>
#include "helisrboard.h"
#include "shared/helisr_protocol.h"

namespace
{
QString tr(const char *text)
{
    return QCoreApplication::translate("FirmwareFile", text);
}

QString versionText(int v)
{
    return QStringLiteral("%1.%2.%3").arg(v >> 8).arg((v >> 4) & 0xF).arg(v & 0xF);
}
}

// Intel HEX: ":LLAAAATT<data>CC" lines; data (00), end (01), segment (02) and
// linear (04) address records. The program is gathered into one image.
FirmwareFile::Info FirmwareFile::read(const QString &path)
{
    Info info;
    QFile f(path);
    if (f.open(QIODevice::ReadOnly | QIODevice::Text) == false) {
        info.error = tr("can't open the file");
        return info;
    }
    if (f.size() > 4 * 1024 * 1024) {
        info.error = tr("too big for a Pro Micro firmware");
        return info;
    }
    QByteArray image;
    uint32_t base = 0;
    bool ended = false;
    int lineNo = 0;
    while (f.atEnd() == false && ended == false) {
        QByteArray line = f.readLine().trimmed();
        lineNo++;
        if (line.isEmpty()) continue;
        QByteArray bytes = QByteArray::fromHex(line.mid(1));
        if (line[0] != ':' || bytes.size() < 5 || bytes.size() * 2 != line.size() - 1) {
            info.error = tr("line %1 isn't Intel HEX").arg(lineNo);
            return info;
        }
        const uint8_t *b = reinterpret_cast<const uint8_t *>(bytes.constData());
        int len = b[0];
        if (bytes.size() != len + 5) {
            info.error = tr("line %1 has the wrong length").arg(lineNo);
            return info;
        }
        uint8_t sum = 0;
        for (int i = 0; i < bytes.size(); ++i) sum = uint8_t(sum + b[i]);
        if (sum != 0) {
            info.error = tr("line %1 fails its checksum").arg(lineNo);
            return info;
        }
        uint32_t addr = (uint32_t(b[1]) << 8) | b[2];
        switch (b[3]) {
        case 0x00: {
            uint32_t at = base + addr;
            if (at + len > 1024 * 1024) {
                info.error = tr("line %1 is beyond a Pro Micro's flash").arg(lineNo);
                return info;
            }
            if (image.size() < int(at + len)) image.resize(int(at + len), char(0xFF));
            memcpy(image.data() + at, b + 4, size_t(len));
            info.bytes += len;
            break;
        }
        case 0x01: ended = true; break;
        case 0x02: base = ((uint32_t(b[4]) << 8) | b[5]) << 4; break;
        case 0x04: base = ((uint32_t(b[4]) << 8) | b[5]) << 16; break;
        default: break;     // start addresses: not needed
        }
    }
    if (ended == false || info.bytes == 0) {
        info.error = tr("no end record, or no program in it");
        return info;
    }
    info.readable = true;

    hsr_build_tag_t tag;
    static const char magic[] = HSR_BUILD_MAGIC;
    int at = image.indexOf(QByteArray(magic, sizeof(magic)));      // with its NUL
    if (at >= 0 && at + int(sizeof(tag)) <= image.size()) {
        memcpy(&tag, image.constData() + at, sizeof(tag));
        info.tagged = true;
        info.boardId = tag.board_id;
        info.cpuMhz = tag.cpu_mhz;
        info.firmwareVersion = tag.firmware_version;
    }
    return info;
}

QString FirmwareFile::describe(const Info &file)
{
    if (file.readable == false) return tr("not a firmware file (%1)").arg(file.error);
    if (file.tagged == false) return tr("a firmware that doesn't say which HeliSR board it's for");
    return tr("HeliSR firmware %1 for the %2 board, %3 MHz Pro Micro")
        .arg(versionText(file.firmwareVersion), HsrBoard::revisionName(file.boardId)).arg(file.cpuMhz);
}

FirmwareFile::Check FirmwareFile::check(const Info &file, int deviceBoard, int statedBoard)
{
    Check c;
    if (file.readable == false) {
        c.message = tr("This isn't a firmware file: %1.").arg(file.error);
        return c;
    }
    QString danger = tr("Rev 4.0 firmware on a Rev 3.0 board drives pins against the board's own chips.");
    QString fileBoard = HsrBoard::revisionName(file.boardId);

    // the user has said which board it is: the file must be for that board
    if (statedBoard) {
        if (file.tagged && file.boardId != statedBoard) {
            c.message = tr("This firmware is for the %1 board, not %2.").arg(fileBoard, HsrBoard::revisionName(statedBoard));
            return c;
        }
        c.verdict = Ok;
        return c;
    }
    if (file.tagged == false) {
        c.verdict = Confirm;
        c.message = tr("This .hex file doesn't say which HeliSR board it's for: it isn't HeliSR firmware, or it's older "
                       "than the board check. %1 Flash it only if you know it suits this board.").arg(danger);
        return c;
    }
    if (deviceBoard) {
        if (file.boardId == deviceBoard) {
            c.verdict = Ok;
            return c;
        }
        c.verdict = Confirm;
        c.message = tr("The device runs firmware for the %1 board, so it is most likely on a %1 board, and this firmware is "
                       "for the %2 board.").arg(HsrBoard::revisionName(deviceBoard), fileBoard) + " ";
        if (file.boardId == HSR_BOARD_REV40) {
            c.message += danger + " " + tr("Flash it only if this Pro Micro is on a Rev 4.0 board (or on no board).");
        } else {
            c.message += tr("On a board it isn't for, its inputs won't work. Flash it only if this Pro Micro is on a %1 "
                            "board (or on no board).").arg(fileBoard);
        }
        return c;
    }
    // a Pro Micro without HeliSR firmware: nothing says which board it's on
    if (file.boardId == HSR_BOARD_REV40) {
        c.verdict = Confirm;
        c.message = tr("This firmware is for the Rev 4.0 board. %1 Flash it only if this Pro Micro is on a Rev 4.0 board "
                       "(or on no board).").arg(danger);
        return c;
    }
    c.verdict = Ok;
    return c;
}
