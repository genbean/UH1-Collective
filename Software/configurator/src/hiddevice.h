#ifndef HIDDEVICE_H
#define HIDDEVICE_H

#include <QObject>
#include <QStringList>
#include <atomic>
#include <mutex>
#include <string>
#include "hidapi.h"
#include "shared/helisr_protocol.h"

// Talks to HeliSR devices over their settings channel (a vendor-defined HID
// collection, usage page 0xFF00). processData() runs in its own thread: it
// keeps the device list up to date, polls the live data (and on Rev 4.0
// boards the AS5600s' status), and carries out the read, write and
// bootloader requests the UI makes.
class HidDevice : public QObject
{
    Q_OBJECT

public:
    void getConfigFromDevice();
    void sendConfigToDevice();
    void enterBootloader();
    //! Rev 4.0: read the AS5600 settings again / save new ones on the board
    void readSensorConfig();
    void writeSensorConfig(const hsr_sensor_config_t &config);
    //! Rev 4.0: read this AX port's sensor in full (SENSOR_DEBUG) a few times a second; -1 stops
    void setSensorDebugPort(int port);
    //! Rev 4.0: start this port's counters again (with its next SENSOR_DEBUG read)
    void clearSensorCounters(int port);

    void setIsFinish(bool isFinish);
    void setSelectedDevice(int deviceNumber);

public slots:
    void processData();

signals:
    void deviceDisconnected();
    void deviceConnected();
    //! INFO answered: whether this configurator understands the device's settings
    void deviceInfoReceived(bool compatible);
    void paramsPacketReceived();

    void configReceived(bool isSuccess);
    void configSent(bool isSuccess);
    //! the device acknowledged the bootloader command and is restarting into it
    void bootloaderStarted(bool isSuccess);

    //! Rev 4.0: the AS5600 settings read (on connecting, or when asked), in DeviceConfig::sensorConfig
    void sensorConfigReceived(bool isSuccess);
    //! Rev 4.0: saved on the board (DeviceConfig::sensorConfig is what it now holds), or refused
    void sensorConfigSent(bool isSuccess);
    //! Rev 4.0: DeviceConfig::sensorStatus updated (about 20 times a second)
    void sensorStatusReceived();
    //! Rev 4.0: DeviceConfig::sensorDebug updated (the port setSensorDebugPort named), or not answered
    void sensorDebugReceived(bool isSuccess);

    void hidDeviceList(const QStringList &deviceNames);

private:
    struct Device
    {
        ushort vid;
        ushort pid;
        std::string path;
        QString name;
    };
    QList<Device> m_hidDevicesList;     // guarded by m_mutex

    enum Work { WORK_PARAMS, WORK_READ, WORK_WRITE, WORK_BOOTLOADER, WORK_SENSOR_READ, WORK_SENSOR_WRITE };
    std::atomic<int> m_currentWork{WORK_PARAMS};
    std::atomic<bool> m_isFinish{false};
    std::atomic<bool> m_listChanged{false};
    std::atomic<int> m_debugPort{-1};
    std::atomic<int> m_clearPort{-1};

    hid_device *m_device = nullptr;
    bool m_compatible = false;
    bool m_sensors = false;             // a Rev 4.0 board: it has the SENSOR commands
    int m_selectedDevice = -1;          // guarded by m_mutex
    hsr_sensor_config_t m_sensorConfigOut = {};     // guarded by m_mutex

    bool transact(uint8_t cmd, uint8_t index, const void *data, int len, uint8_t *reply,
                  int timeoutMs = 250, int tries = 3);
    bool readInfo();
    bool readParams();
    bool readConfigFromDevice();
    bool writeConfigToDevice();
    bool startBootloader();
    bool readSensorConfigFromDevice();
    bool writeSensorConfigToDevice();
    bool readSensorStatus();
    bool readSensorDebug(int port);
    void closeDevice();

    mutable std::mutex m_mutex;
};

#endif // HIDDEVICE_H
