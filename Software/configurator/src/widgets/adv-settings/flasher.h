#ifndef FLASHER_H
#define FLASHER_H

#include <QWidget>
#include "common_defines.h"

QT_BEGIN_NAMESPACE
class QComboBox;
class QLabel;
class QProgressBar;
class QPushButton;
class QToolButton;
QT_END_NAMESPACE

class AvrFlasher;

// Firmware updates: a connected HeliSR device is restarted into its bootloader
// over USB; a Pro Micro without HeliSR firmware gets a 1200-baud touch on its
// serial port, or a double tap on RST. avrdude then writes the .hex.
class Flasher : public QWidget
{
    Q_OBJECT

public:
    explicit Flasher(QWidget *parent = nullptr);

    void retranslateUi();

    //! a HeliSR device is open (info: its INFO answer, or nullptr)
    void deviceConnected(bool isConnect, const hsr_info_t *info = nullptr);
    bool isBusy() const;

signals:
    void enterBootloaderRequested();

public slots:
    void bootloaderStarted(bool isSuccess);

private:
    void fillFirmwareList();
    void refreshPorts();
    QString chooseHexFile();
    void flashConnected();
    void flashNewBoard();
    void setBusy(bool busy);
    void flashFinished(bool success, const QString &message);

    AvrFlasher *m_avr;
    QString m_hexFile;
    bool m_connected = false;
    int m_deviceMhz = 0;

    QLabel *m_deviceLabel;
    QLabel *m_fileLabel;
    QComboBox *m_firmware;
    QPushButton *m_flashButton;
    QLabel *m_newBoardLabel;
    QComboBox *m_ports;
    QToolButton *m_refreshPorts;
    QPushButton *m_flashNewButton;
    QProgressBar *m_progress;
    QLabel *m_status;
};

#endif // FLASHER_H
