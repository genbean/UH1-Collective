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

#include <QDebug>

// the installer puts the release firmware here, next to the app
static const char *const FIRMWARE_16MHZ = "/firmware/HeliSR_16MHz.hex";
static const char *const FIRMWARE_8MHZ = "/firmware/HeliSR_8MHz.hex";
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
    QString dir = QCoreApplication::applicationDirPath();
    struct { QString text; QString file; } items[] = {
        {tr("HeliSR for a 5 V / 16 MHz Pro Micro"), dir + FIRMWARE_16MHZ},
        {tr("HeliSR for a 3.3 V / 8 MHz Pro Micro"), dir + FIRMWARE_8MHZ},
    };
    for (auto &item : items) {
        bool found = QFileInfo::exists(item.file);
        m_firmware->addItem(found ? item.text : item.text + " " + tr("(not found)"), found ? item.file : QString());
    }
    m_firmware->addItem(tr("Another .hex file..."), QString("*"));
    if (current >= 0) {
        m_firmware->setCurrentIndex(current);
    } else if (m_firmware->itemData(0).toString().isEmpty()) {
        m_firmware->setCurrentIndex(2);
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
        m_deviceMhz = info->cpu_mhz;
        QString ver = QStringLiteral("%1.%2.%3").arg(info->firmware_version >> 8).arg((info->firmware_version >> 4) & 0xF)
                          .arg(info->firmware_version & 0xF);
        m_deviceLabel->setText(tr("Connected device: HeliSR firmware v%1, %2 MHz Pro Micro.").arg(ver).arg(info->cpu_mhz));
        // offer the matching build
        int want = info->cpu_mhz == 8 ? 1 : 0;
        if (m_firmware->itemData(want).toString().isEmpty() == false) {
            m_firmware->setCurrentIndex(want);
        }
    } else if (isConnect == false) {
        m_deviceMhz = 0;
        m_deviceLabel->setText(tr("No HeliSR device connected."));
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
    if (file.isEmpty()) {
        return QString();
    }
    // an 8 MHz build on a 16 MHz board (or the other way round) has no working USB until reflashed
    int fileMhz = file.endsWith(FIRMWARE_8MHZ) ? 8 : file.endsWith(FIRMWARE_16MHZ) ? 16 : 0;
    if (m_deviceMhz && fileMhz && fileMhz != m_deviceMhz) {
        if (QMessageBox::warning(this, tr("Clock speed"),
                                 tr("The connected Pro Micro runs at %1 MHz, but this firmware is for %2 MHz. Its USB won't "
                                    "work until it's flashed again with a double tap on RST. Flash anyway?")
                                     .arg(m_deviceMhz).arg(fileMhz),
                                 QMessageBox::Yes | QMessageBox::No, QMessageBox::No) != QMessageBox::Yes) {
            return QString();
        }
    }
    return file;
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
