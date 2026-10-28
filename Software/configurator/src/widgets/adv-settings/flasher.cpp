#include "flasher.h"
#include <QComboBox>
#include <QCoreApplication>
#include <QFileDialog>
#include <QFileInfo>
#include <QGridLayout>
#include <QLabel>
#include <QMessageBox>
#include <QProgressBar>
#include <QPushButton>
#include <QToolButton>
#include "avrflasher.h"
#include "firmwarefile.h"
#include "helisrboard.h"

#include <QDebug>

// the installer puts the release firmware here, next to the app (5 V / 16 MHz Pro Micro), one per board
static const struct
{
    int board;
    const char *file;
} FIRMWARE_FILES[] = {
    {HSR_BOARD_REV30, "/firmware/HeliSR_Rev3.0_16MHz.hex"},
    {HSR_BOARD_REV40, "/firmware/HeliSR_Rev4.0_16MHz.hex"},
};
static const int FIRMWARE_COUNT = int(sizeof(FIRMWARE_FILES) / sizeof(FIRMWARE_FILES[0]));
static const int BOOTLOADER_WAIT_MS = 10000;
static const int DOUBLE_TAP_WAIT_MS = 20000;

Flasher::Flasher(QWidget *parent)
    : QWidget(parent)
    , m_avr(new AvrFlasher(this))
{
    QGridLayout *grid = new QGridLayout(this);
    m_deviceLabel = new QLabel(this);
    m_deviceLabel->setWordWrap(true);
    grid->addWidget(m_deviceLabel, 0, 0, 1, 3);

    m_fileLabel = new QLabel(this);
    grid->addWidget(m_fileLabel, 1, 0);
    m_firmware = new QComboBox(this);
    grid->addWidget(m_firmware, 1, 1, 1, 2);

    m_flashButton = new QPushButton(this);
    m_flashButton->setEnabled(false);
    grid->addWidget(m_flashButton, 2, 0, 1, 3);

    m_newBoardLabel = new QLabel(this);
    m_newBoardLabel->setWordWrap(true);
    grid->addWidget(m_newBoardLabel, 3, 0, 1, 3);
    m_ports = new QComboBox(this);
    grid->addWidget(m_ports, 4, 0, 1, 2);
    m_refreshPorts = new QToolButton(this);
    m_refreshPorts->setIcon(QIcon(":/Images/reset.png"));
    grid->addWidget(m_refreshPorts, 4, 2);
    m_flashNewButton = new QPushButton(this);
    grid->addWidget(m_flashNewButton, 5, 0, 1, 3);

    m_progress = new QProgressBar(this);
    m_progress->setRange(0, 100);
    m_progress->setValue(0);
    grid->addWidget(m_progress, 6, 0, 1, 3);
    m_status = new QLabel(this);
    m_status->setWordWrap(true);
    m_status->setMinimumHeight(40);
    m_status->setAlignment(Qt::AlignLeft | Qt::AlignTop);
    grid->addWidget(m_status, 7, 0, 1, 3);
    grid->setColumnStretch(1, 1);
    grid->setContentsMargins(0, 0, 0, 0);

    connect(m_flashButton, &QPushButton::clicked, this, &Flasher::flashConnected);
    connect(m_flashNewButton, &QPushButton::clicked, this, &Flasher::flashNewBoard);
    connect(m_refreshPorts, &QToolButton::clicked, this, &Flasher::refreshPorts);
    connect(m_avr, &AvrFlasher::progress, m_progress, &QProgressBar::setValue);
    connect(m_avr, &AvrFlasher::status, m_status, &QLabel::setText);
    connect(m_avr, &AvrFlasher::finished, this, &Flasher::flashFinished);

    retranslateUi();
}

void Flasher::retranslateUi()
{
    m_fileLabel->setText(tr("Firmware:"));
    m_flashButton->setText(tr("Flash firmware to the connected device"));
    m_newBoardLabel->setText(tr("<br>A Pro Micro without HeliSR firmware: pick its serial port (an Arduino sketch's port), "
                                "or choose a double tap and tap RST twice when asked."));
    m_flashNewButton->setText(tr("Flash a Pro Micro without HeliSR firmware"));
    m_refreshPorts->setToolTip(tr("Refresh the list of serial ports"));
    fillFirmwareList();
    refreshPorts();
    deviceConnected(m_connected);
}

void Flasher::fillFirmwareList()
{
    int current = m_firmware->currentIndex();
    m_firmware->clear();
    bool anyFound = false;
    for (const auto &fw : FIRMWARE_FILES) {
        QString file = QCoreApplication::applicationDirPath() + fw.file;
        QString text = tr("%1 (5 V / 16 MHz Pro Micro)").arg(HsrBoard::boardName(fw.board));
        bool found = QFileInfo::exists(file);
        anyFound |= found;
        m_firmware->addItem(found ? text : text + " " + tr("(not found)"), found ? file : QString());
    }
    m_firmware->addItem(tr("Another .hex file..."), QString("*"));
    if (current >= 0) {
        m_firmware->setCurrentIndex(current);
    } else if (anyFound == false) {
        m_firmware->setCurrentIndex(FIRMWARE_COUNT);
    }
}

void Flasher::refreshPorts()
{
    QString current = m_ports->currentData().toString();
    m_ports->clear();
    m_ports->addItem(tr("Double tap on RST"), QString());
    for (const QString &port : AvrFlasher::serialPorts()) {
        m_ports->addItem(port, port);
    }
    int index = m_ports->findData(current);
    m_ports->setCurrentIndex(index < 0 ? 0 : index);
}

void Flasher::deviceConnected(bool isConnect, const hsr_info_t *info)
{
    m_connected = isConnect;
    if (isConnect && info && info->firmware_version) {
        QString ver = QStringLiteral("%1.%2.%3").arg(info->firmware_version >> 8).arg((info->firmware_version >> 4) & 0xF)
                          .arg(info->firmware_version & 0xF);
        m_deviceLabel->setText(tr("Connected device: HeliSR firmware v%1 for the %2 board, %3 MHz Pro Micro.")
                                   .arg(ver, HsrBoard::revisionName(info->board_id)).arg(info->cpu_mhz));
        // offer the firmware for the board it's on
        if (info->board_id != m_deviceBoard && m_avr->isBusy() == false) {
            for (int i = 0; i < FIRMWARE_COUNT; ++i) {
                if (FIRMWARE_FILES[i].board == info->board_id) m_firmware->setCurrentIndex(i);
            }
        }
        m_deviceBoard = info->board_id;
    } else if (isConnect == false) {
        m_deviceLabel->setText(tr("No HeliSR device connected."));
        m_deviceBoard = 0;
    }
    m_flashButton->setEnabled(isConnect && m_avr->isBusy() == false);
}

bool Flasher::isBusy() const
{
    return m_avr->isBusy();
}

QString Flasher::chooseHexFile()
{
    QString file = m_firmware->currentData().toString();
    if (file == "*") {
        file = QFileDialog::getOpenFileName(this, tr("Open firmware"), QString(), tr("Firmware (*.hex)"));
    }
    return file;
}

bool Flasher::approveFile(const QString &file, int deviceBoard)
{
    FirmwareFile::Info info = FirmwareFile::read(file);
    FirmwareFile::Check check = FirmwareFile::check(info, deviceBoard, 0);
    if (check.verdict == FirmwareFile::Ok) {
        return true;
    }
    if (check.verdict == FirmwareFile::Refuse) {
        flashFinished(false, check.message);
        return false;
    }
    QMessageBox box(QMessageBox::Warning, tr("Which board?"), check.message, QMessageBox::NoButton, this);
    QString what = info.tagged ? tr("It's on a %1 board: flash it").arg(HsrBoard::revisionName(info.boardId))
                               : tr("Flash it anyway");
    QPushButton *flash = box.addButton(what, QMessageBox::AcceptRole);
    QPushButton *cancel = box.addButton(QMessageBox::Cancel);
    box.setDefaultButton(cancel);
    box.exec();
    if (box.clickedButton() != flash) {
        m_status->setText(tr("Not flashed."));
        m_status->setStyleSheet(QString());
        return false;
    }
    return true;
}

void Flasher::setBusy(bool busy)
{
    m_flashButton->setEnabled(!busy && m_connected);
    m_flashNewButton->setEnabled(!busy);
    m_firmware->setEnabled(!busy);
    m_ports->setEnabled(!busy);
    m_refreshPorts->setEnabled(!busy);
    if (busy) {
        m_status->setStyleSheet(QString());
        m_progress->setValue(0);
    }
}

void Flasher::flashConnected()
{
    m_hexFile = chooseHexFile();
    if (m_hexFile.isEmpty()) return;
    if (approveFile(m_hexFile, m_deviceBoard) == false) {
        m_hexFile.clear();
        return;
    }
    setBusy(true);
    m_avr->prepare();
    m_status->setText(tr("Restarting the device into its bootloader..."));
    emit enterBootloaderRequested();
}

void Flasher::bootloaderStarted(bool isSuccess)
{
    if (m_hexFile.isEmpty()) return;
    if (isSuccess) {
        m_avr->flashWhenBootloaderAppears(m_hexFile, BOOTLOADER_WAIT_MS);
    } else {
        flashFinished(false, tr("The device didn't answer the bootloader command. Unplug and replug it, or use "
                                "a double tap on RST below."));
    }
}

void Flasher::flashNewBoard()
{
    m_hexFile = chooseHexFile();
    if (m_hexFile.isEmpty()) return;
    if (approveFile(m_hexFile, 0) == false) {
        m_hexFile.clear();
        return;
    }
    QString port = m_ports->currentData().toString();
    setBusy(true);
    m_avr->prepare();
    if (port.isEmpty()) {
        m_avr->flashWhenBootloaderAppears(m_hexFile, DOUBLE_TAP_WAIT_MS);
        m_status->setText(tr("Double-tap RST on the Pro Micro now (twice quickly)..."));
    } else if (AvrFlasher::touch1200(port)) {
        m_avr->flashWhenBootloaderAppears(m_hexFile, BOOTLOADER_WAIT_MS);
    } else {
        flashFinished(false, tr("%1 couldn't be opened. Close any program using it, or use a double tap on RST.").arg(port));
    }
}

void Flasher::flashFinished(bool success, const QString &message)
{
    m_hexFile.clear();
    setBusy(false);
    m_status->setText(message);
    m_status->setStyleSheet(success ? "color: white; background-color: rgb(0, 128, 0); padding: 4px;"
                                    : "color: white; background-color: rgb(200, 0, 0); padding: 4px;");
    refreshPorts();
}
