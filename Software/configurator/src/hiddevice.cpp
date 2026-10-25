#include <QThread>
#include <QDebug>
#include <QElapsedTimer>
#include <cstring>
#include <thread>
#include "hiddevice.h"
#include "hidapi.h"
#include "common_defines.h"
#include "deviceconfig.h"
#include "global.h"

// HeliSR's settings channel: every packet is [report ID, command, index, status,
// 60 data bytes], and the device answers each command with a packet carrying
// the same command and index (see firmware/HeliSR/src/shared/helisr_protocol.h).

static const int DEVICE_SEARCH_DELAY = 1000;    // ms between device list updates
static const int PARAMS_PERIOD = 10;            // ms between live data reads
static const ushort SETTINGS_USAGE_PAGE = 0xFF00;
static const int RESTART_WAIT = 700;              // ms for a restarting device to drop off the bus

static const int CONFIG_CHUNKS = (sizeof(dev_config_t) + HSR_PACKET_DATA - 1) / HSR_PACKET_DATA;
static const int PARAMS_PARTS = (sizeof(params_report_t) + HSR_PACKET_DATA - 1) / HSR_PACKET_DATA;

void HidDevice::processData()
{
    // Device list: hid_enumerate() can take a while with many devices, so it
    // runs in its own thread (this worker has no event loop).
    std::thread th([&] {
        while (m_isFinish == false) {
            QList<Device> found;
            hid_device_info *first = hid_enumerate(0x0, 0x0);
            for (hid_device_info *d = first; d; d = d->next) {
                if (QString::fromWCharArray(d->manufacturer_string ? d->manufacturer_string : L"") != HSR_MANUFACTURER) {
                    continue;
                }
                // the settings collection; hidapi on some systems doesn't report usage pages
                if (d->usage_page != SETTINGS_USAGE_PAGE && !(d->usage_page == 0 && d->interface_number == 1)) {
                    continue;
                }
                Device dev;
                dev.vid = d->vendor_id;
                dev.pid = d->product_id;
                dev.path = d->path;
                dev.name = QString::fromWCharArray(d->product_string ? d->product_string : L"");
                QString serial = QString::fromWCharArray(d->serial_number ? d->serial_number : L"");
                if (serial.isEmpty() == false) {
                    dev.name += " (" + serial + ")";
                }
                found.append(dev);
            }
            hid_free_enumeration(first);

            {
                std::lock_guard<std::mutex> lock(m_mutex);
                bool changed = found.size() != m_hidDevicesList.size();
                for (int i = 0; changed == false && i < found.size(); ++i) {
                    changed = found[i].path != m_hidDevicesList[i].path || found[i].name != m_hidDevicesList[i].name;
                }
                if (changed) {
                    m_hidDevicesList = found;
                    QStringList names;
                    for (const Device &dev : found) {
                        names.append(dev.name);
                    }
                    m_listChanged = true;
                    emit hidDeviceList(names);
                }
            }
            for (int i = 0; i < DEVICE_SEARCH_DELAY / 50 && m_isFinish == false; ++i) {
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
            }
        }
    });

    int openedDevice = -1;
    bool disconnectedSent = false;
    QElapsedTimer paramsTimer;
    QElapsedTimer infoTimer;

    while (m_isFinish == false)
    {
        std::string path;
        int selected;
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            if (m_selectedDevice >= m_hidDevicesList.size()) {
                m_selectedDevice = int(m_hidDevicesList.size()) - 1;
            }
            selected = m_selectedDevice;
            if (selected >= 0) {
                path = m_hidDevicesList[selected].path;
            }
        }

        // (re)open the selected device when the selection or the list changes,
        // and after a restart (the device comes back under the same path)
        if (selected != openedDevice || m_listChanged.exchange(false) || m_device == nullptr) {
            closeDevice();
            openedDevice = -1;
            if (selected >= 0) {
                m_device = hid_open_path(path.c_str());
                if (m_device) {
                    bool compatible = readInfo();
                    if (compatible == false && gEnv.pDeviceConfig->info.firmware_version == 0) {
                        // no answer: still starting up, or just restarting; try again shortly
                        closeDevice();
                        QThread::msleep(300);
                        continue;
                    }
                    openedDevice = selected;
                    disconnectedSent = false;
                    m_compatible = compatible;
                    infoTimer.start();
                    qDebug().nospace() << "Opened HeliSR device " << selected + 1;
                    emit deviceConnected();
                    emit deviceInfoReceived(m_compatible);
                }
            }
        }

        if (m_device == nullptr) {
            if (disconnectedSent == false) {
                emit deviceDisconnected();
                disconnectedSent = true;
            }
            m_currentWork = WORK_PARAMS;
            QThread::msleep(200);
            continue;
        }

        switch (m_currentWork) {
        case WORK_READ:
            emit configReceived(m_compatible && readConfigFromDevice());
            m_currentWork = WORK_PARAMS;
            break;

        case WORK_WRITE:
            if (m_compatible && writeConfigToDevice()) {
                // the device restarts with the new settings and enumerates again
                closeDevice();
                emit configSent(true);
                QThread::msleep(RESTART_WAIT);
            } else {
                emit configSent(false);
            }
            m_currentWork = WORK_PARAMS;
            break;

        case WORK_BOOTLOADER:
            if (startBootloader()) {
                closeDevice();
                emit bootloaderStarted(true);
                QThread::msleep(RESTART_WAIT);
            } else {
                emit bootloaderStarted(false);
            }
            m_currentWork = WORK_PARAMS;
            break;

        default:
            if (m_compatible == false) {
                // no live data from firmware this app doesn't understand; just
                // check now and then that it's still there
                if (infoTimer.elapsed() > 1000) {
                    infoTimer.start();
                    bool compatible = readInfo();
                    if (m_device && compatible != m_compatible) {
                        m_compatible = compatible;
                        emit deviceInfoReceived(m_compatible);
                    }
                }
                QThread::msleep(50);
                break;
            }
            if (paramsTimer.isValid() && paramsTimer.elapsed() < PARAMS_PERIOD) {
                QThread::msleep(1);
                break;
            }
            paramsTimer.start();
            if (readParams()) {
                emit paramsPacketReceived();
            }
            break;
        }
    }
    closeDevice();
    th.join();
}

void HidDevice::closeDevice()
{
    if (m_device) {
        hid_close(m_device);
        m_device = nullptr;
    }
}

// Send one command and wait for its answer. reply gets the whole 64-byte packet.
bool HidDevice::transact(uint8_t cmd, uint8_t index, const void *data, int len, uint8_t *reply,
                         int timeoutMs, int tries)
{
    uint8_t out[HSR_PACKET_SIZE] = {HSR_REPORT_CFG, cmd, index, 0};
    if (data && len > 0) {
        memcpy(out + HSR_PACKET_HEADER, data, qMin(len, HSR_PACKET_DATA));
    }

    for (int t = 0; t < tries && m_device; ++t) {
        if (hid_write(m_device, out, sizeof(out)) < 0) {
            closeDevice();
            return false;
        }
        QElapsedTimer timer;
        timer.start();
        while (timer.elapsed() < timeoutMs) {
            int res = hid_read_timeout(m_device, reply, HSR_PACKET_SIZE, timeoutMs - int(timer.elapsed()));
            if (res < 0) {
                closeDevice();
                return false;
            }
            if (res >= HSR_PACKET_HEADER && reply[0] == HSR_REPORT_CFG && reply[1] == cmd && reply[2] == index) {
                return true;
            }
        }
        qDebug() << "No answer to command" << cmd << "index" << index << "- retrying";
    }
    return false;
}

bool HidDevice::readInfo()
{
    uint8_t reply[HSR_PACKET_SIZE];
    hsr_info_t &info = gEnv.pDeviceConfig->info;
    info = {};
    if (transact(HSR_CMD_INFO, 0, nullptr, 0, reply) == false || reply[3] != HSR_OK) {
        qDebug() << "No INFO answer";
        return false;
    }
    memcpy(&info, reply + HSR_PACKET_HEADER, sizeof(info));
    qDebug().nospace() << "Firmware " << Qt::hex << info.firmware_version << ", protocol " << Qt::dec
                       << info.protocol_version << ", board " << Qt::hex << info.board_id << Qt::dec
                       << ", settings v" << info.config_version << " (" << info.config_size << " bytes), "
                       << info.cpu_mhz << " MHz, stack free " << info.stack_free << " B";
    return info.protocol_version == HSR_PROTOCOL_VERSION && info.config_version == HSR_CONFIG_VERSION
           && info.config_size == sizeof(dev_config_t);
}

bool HidDevice::readParams()
{
    uint8_t reply[HSR_PACKET_SIZE];
    params_report_t params;
    for (int part = 0; part < PARAMS_PARTS; ++part) {
        if (transact(HSR_CMD_PARAMS, uint8_t(part), nullptr, 0, reply, 100, 1) == false || reply[3] != HSR_OK) {
            return false;
        }
        int offset = part * HSR_PACKET_DATA;
        memcpy(reinterpret_cast<uint8_t *>(&params) + offset, reply + HSR_PACKET_HEADER,
               qMin(int(HSR_PACKET_DATA), int(sizeof(params)) - offset));
    }
    gEnv.pDeviceConfig->paramsReport = params;
    return true;
}

bool HidDevice::readConfigFromDevice()
{
    uint8_t reply[HSR_PACKET_SIZE];
    dev_config_t config;
    for (int chunk = 0; chunk < CONFIG_CHUNKS; ++chunk) {
        if (transact(HSR_CMD_READ, uint8_t(chunk), nullptr, 0, reply) == false || reply[3] != HSR_OK) {
            qDebug() << "Reading settings failed at chunk" << chunk;
            return false;
        }
        int offset = chunk * HSR_PACKET_DATA;
        memcpy(reinterpret_cast<uint8_t *>(&config) + offset, reply + HSR_PACKET_HEADER,
               qMin(int(HSR_PACKET_DATA), int(sizeof(config)) - offset));
    }
    if (config.config_version != HSR_CONFIG_VERSION) {
        qDebug() << "Settings version" << config.config_version << "isn't" << HSR_CONFIG_VERSION;
        return false;
    }
    gEnv.pDeviceConfig->config = config;
    qDebug() << "All settings received";
    return true;
}

bool HidDevice::writeConfigToDevice()
{
    uint8_t reply[HSR_PACKET_SIZE];
    dev_config_t config = gEnv.pDeviceConfig->config;
    config.config_version = HSR_CONFIG_VERSION;
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&config);

    for (int chunk = 0; chunk < CONFIG_CHUNKS; ++chunk) {
        int offset = chunk * HSR_PACKET_DATA;
        int len = qMin(int(HSR_PACKET_DATA), int(sizeof(config)) - offset);
        if (transact(HSR_CMD_WRITE, uint8_t(chunk), bytes + offset, len, reply) == false || reply[3] != HSR_OK) {
            qDebug() << "Writing settings failed at chunk" << chunk;
            // throw away the partial write
            transact(HSR_CMD_RELOAD, 0, nullptr, 0, reply);
            return false;
        }
    }

    uint16_t crc = hsr_crc16(bytes, sizeof(config));
    uint8_t crcBytes[2] = {uint8_t(crc & 0xFF), uint8_t(crc >> 8)};
    if (transact(HSR_CMD_COMMIT, 0, crcBytes, 2, reply, 2000, 1) == false) {
        qDebug() << "No answer to COMMIT";
        return false;
    }
    if (reply[3] != HSR_OK) {
        qDebug() << "COMMIT refused, status" << reply[3];
        transact(HSR_CMD_RELOAD, 0, nullptr, 0, reply);
        return false;
    }
    qDebug() << "All settings sent and saved; the device restarts";
    return true;
}

bool HidDevice::startBootloader()
{
    uint8_t reply[HSR_PACKET_SIZE];
    static const char key[] = "bootloader run";
    if (transact(HSR_CMD_BOOTLOADER, 0, key, sizeof(key) - 1, reply, 500, 1) == false || reply[3] != HSR_OK) {
        qDebug() << "Bootloader command not acknowledged";
        return false;
    }
    qDebug() << "Device is starting its bootloader";
    return true;
}

// another device selected in comboBox
void HidDevice::setSelectedDevice(int deviceNumber)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    if (deviceNumber > m_hidDevicesList.size() - 1) {
        deviceNumber = int(m_hidDevicesList.size() - 1);
    }
    m_selectedDevice = deviceNumber;
}

// stop processData()
void HidDevice::setIsFinish(bool isFinish)
{
    m_isFinish = isFinish;
}

// button "read config" clicked
void HidDevice::getConfigFromDevice()
{
    m_currentWork = WORK_READ;
}

// button "write config" clicked
void HidDevice::sendConfigToDevice()
{
    m_currentWork = WORK_WRITE;
}

// flasher: restart the device into its bootloader
void HidDevice::enterBootloader()
{
    m_currentWork = WORK_BOOTLOADER;
}
