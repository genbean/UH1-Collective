#ifndef HIDDEVICE_H
#define HIDDEVICE_H

#include <QObject>
#include <QStringList>
#include <atomic>
#include <mutex>
#include <string>
#include "hidapi.h"

// Talks to HeliSR devices over their settings channel (a vendor-defined HID
// collection, usage page 0xFF00). processData() runs in its own thread: it
// keeps the device list up to date, polls the live data, and carries out the
// read, write and bootloader requests the UI makes.
class HidDevice : public QObject
{
    Q_OBJECT

public:
    void getConfigFromDevice();
    void sendConfigToDevice();
    void enterBootloader();

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

    enum Work { WORK_PARAMS, WORK_READ, WORK_WRITE, WORK_BOOTLOADER };
    std::atomic<int> m_currentWork{WORK_PARAMS};
    std::atomic<bool> m_isFinish{false};
    std::atomic<bool> m_listChanged{false};

    hid_device *m_device = nullptr;
    bool m_compatible = false;
    int m_selectedDevice = -1;          // guarded by m_mutex

    bool transact(uint8_t cmd, uint8_t index, const void *data, int len, uint8_t *reply,
                  int timeoutMs = 250, int tries = 3);
    bool readInfo();
    bool readParams();
    bool readConfigFromDevice();
    bool writeConfigToDevice();
    bool startBootloader();
    void closeDevice();

    mutable std::mutex m_mutex;
};

#endif // HIDDEVICE_H
