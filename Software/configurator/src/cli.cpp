#include "cli.h"
#include <QCoreApplication>
#include <QEventLoop>
#include <QFileInfo>
#include <QThread>
#include <QTimer>
#include <cstdio>
#include <cstring>
#include "avrflasher.h"
#include "configtofile.h"
#include "deviceconfig.h"
#include "firmwarefile.h"
#include "global.h"
#include "helisrboard.h"
#include "hiddevice.h"
#include "version.h"
#include "shared/helisr_defaults.h"

#ifdef Q_OS_WIN
#include <windows.h>
#endif

namespace
{
const QStringList COMMANDS = {"--info", "--read", "--write", "--write-defaults", "--params", "--flash",
                              "--flash-new", "--roundtrip", "--save-defaults", "--hex-info", "--sensors",
                              "--sensor-roundtrip", "--help"};

void out(const QString &text)
{
    fputs(qPrintable(text + "\n"), stdout);
    fflush(stdout);
}

// A GUI program has no console: use the caller's, unless the output is redirected.
void attachConsole()
{
#ifdef Q_OS_WIN
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    if ((h == nullptr || h == INVALID_HANDLE_VALUE) && AttachConsole(ATTACH_PARENT_PROCESS)) {
        freopen("CONOUT$", "w", stdout);
        freopen("CONOUT$", "w", stderr);
    }
#endif
}

// Runs the event loop until done() returns true or timeoutMs passes.
template <typename Done>
bool waitUntil(Done done, int timeoutMs)
{
    QEventLoop loop;
    QTimer poll;
    poll.setInterval(10);
    QObject::connect(&poll, &QTimer::timeout, &loop, [&] {
        if (done()) loop.quit();
    });
    QTimer timeout;
    timeout.setSingleShot(true);
    QObject::connect(&timeout, &QTimer::timeout, &loop, &QEventLoop::quit);
    poll.start();
    timeout.start(timeoutMs);
    if (done() == false) {
        loop.exec();
    }
    return done();
}

QString versionText(uint16_t v)
{
    return QStringLiteral("%1.%2.%3").arg(v >> 8).arg((v >> 4) & 0xF).arg(v & 0xF);
}

// The device worker in its own thread, as in the window.
class Session
{
public:
    explicit Session(int deviceIndex)
        : m_index(deviceIndex)
    {
        m_dev = new HidDevice();
        m_dev->moveToThread(&m_thread);
        QObject::connect(&m_thread, &QThread::started, m_dev, &HidDevice::processData);
        QObject::connect(m_dev, &HidDevice::hidDeviceList, &m_context, [this](const QStringList &names) {
            m_names = names;
            m_dev->setSelectedDevice(names.size() > m_index ? m_index : -1);
        });
        QObject::connect(m_dev, &HidDevice::deviceInfoReceived, &m_context, [this](bool compatible) {
            m_infoCount++;
            m_compatible = compatible;
        });
        QObject::connect(m_dev, &HidDevice::configReceived, &m_context, [this](bool ok) { m_readResult = ok ? 1 : 0; });
        QObject::connect(m_dev, &HidDevice::configSent, &m_context, [this](bool ok) { m_writeResult = ok ? 1 : 0; });
        QObject::connect(m_dev, &HidDevice::bootloaderStarted, &m_context, [this](bool ok) { m_bootResult = ok ? 1 : 0; });
        QObject::connect(m_dev, &HidDevice::paramsPacketReceived, &m_context, [this] { m_paramsCount++; });
        QObject::connect(m_dev, &HidDevice::sensorConfigReceived, &m_context, [this](bool ok) { m_sensorReadResult = ok ? 1 : 0; });
        QObject::connect(m_dev, &HidDevice::sensorConfigSent, &m_context, [this](bool ok) { m_sensorWriteResult = ok ? 1 : 0; });
        QObject::connect(m_dev, &HidDevice::sensorStatusReceived, &m_context, [this] { m_sensorStatusCount++; });
        m_thread.start();
    }

    ~Session()
    {
        m_dev->setIsFinish(true);
        m_thread.quit();
        m_thread.wait();
        delete m_dev;
    }

    //! wait for the (next) INFO answer
    bool connect(int timeoutMs = 6000)
    {
        int before = m_infoCount;
        if (waitUntil([&] { return m_infoCount > before; }, timeoutMs) == false) {
            out(m_names.isEmpty() ? "No HeliSR device found." : "The device didn't answer.");
            return false;
        }
        const hsr_info_t &info = gEnv.pDeviceConfig->info;
        if (m_compatible == false) {
            out(QStringLiteral("Firmware %1 (protocol %2, settings v%3) doesn't match this app (protocol %4, settings v%5).")
                    .arg(versionText(info.firmware_version)).arg(info.protocol_version).arg(info.config_version)
                    .arg(HSR_PROTOCOL_VERSION).arg(HSR_CONFIG_VERSION));
        }
        return true;
    }

    bool read()
    {
        m_readResult = -1;
        m_dev->getConfigFromDevice();
        return waitUntil([&] { return m_readResult >= 0; }, 10000) && m_readResult == 1;
    }

    //! write, then wait for the device to come back after its restart
    bool write()
    {
        m_writeResult = -1;
        int before = m_infoCount;
        m_dev->sendConfigToDevice();
        if (waitUntil([&] { return m_writeResult >= 0; }, 15000) == false || m_writeResult != 1) {
            return false;
        }
        return waitUntil([&] { return m_infoCount > before; }, 10000);
    }

    bool bootloader()
    {
        m_bootResult = -1;
        m_dev->enterBootloader();
        return waitUntil([&] { return m_bootResult >= 0; }, 5000) && m_bootResult == 1;
    }

    //! Rev 4.0: the AS5600 settings, into DeviceConfig::sensorConfig
    bool readSensors()
    {
        m_sensorReadResult = -1;
        m_dev->readSensorConfig();
        return waitUntil([&] { return m_sensorReadResult >= 0; }, 3000) && m_sensorReadResult == 1;
    }

    //! Rev 4.0: save AS5600 settings on the board; false if it refused them
    bool writeSensors(const hsr_sensor_config_t &config)
    {
        m_sensorWriteResult = -1;
        m_dev->writeSensorConfig(config);
        return waitUntil([&] { return m_sensorWriteResult >= 0; }, 3000) && m_sensorWriteResult == 1;
    }

    //! wait for this many more AS5600 status reports
    bool sensorStatus(int count, int timeoutMs)
    {
        int target = m_sensorStatusCount + count;
        return waitUntil([&] { return m_sensorStatusCount >= target; }, timeoutMs);
    }

    int paramsCount() const { return m_paramsCount; }
    bool compatible() const { return m_compatible; }
    QStringList names() const { return m_names; }

private:
    int m_index;
    QThread m_thread;
    HidDevice *m_dev;
    QObject m_context;
    QStringList m_names;
    int m_infoCount = 0;
    bool m_compatible = false;
    int m_readResult = -1;
    int m_writeResult = -1;
    int m_bootResult = -1;
    int m_paramsCount = 0;
    int m_sensorReadResult = -1;
    int m_sensorWriteResult = -1;
    int m_sensorStatusCount = 0;
};

void printInfo(const QStringList &names)
{
    const hsr_info_t &i = gEnv.pDeviceConfig->info;
    out("Devices:       " + names.join(", "));
    out("Firmware:      " + versionText(i.firmware_version) + QStringLiteral(", %1 MHz").arg(i.cpu_mhz)
        + (i.usb_serial_port ? ", with USB serial port" : ""));
    out(QStringLiteral("Protocol:      %1, board 0x%2 (%3), settings v%4 (%5 bytes)")
            .arg(i.protocol_version).arg(i.board_id, 2, 16, QChar('0')).arg(HsrBoard::boardName(i.board_id))
            .arg(i.config_version).arg(i.config_size));
    out(QStringLiteral("Board ID:      %1, settings from %2")
            .arg(i.unique_id, 8, 16, QChar('0')).arg(i.config_from_eeprom ? "EEPROM" : "factory defaults"));
    out(QStringLiteral("Health:        %1 B stack never used, longest pass %2 us, %3 commands, %4 replies dropped")
            .arg(i.stack_free).arg(i.pass_max_us).arg(i.commands).arg(i.replies_dropped));
}

// --board 3.0 / 4.0: the board the user says the Pro Micro is on (0 = not said, -1 = not a board)
int statedBoard(const QString &text)
{
    if (text.isEmpty()) return 0;
    if (text == "3.0" || text == "3") return HSR_BOARD_REV30;
    if (text == "4.0" || text == "4") return HSR_BOARD_REV40;
    return -1;
}

int flash(const QString &hex, Session *session, const QString &port, int stated)
{
    if (QFileInfo::exists(hex) == false) {
        out("No such file: " + hex);
        return 2;
    }
    // which board the file is for, against the board the Pro Micro is on
    FirmwareFile::Info file = FirmwareFile::read(hex);
    out(QFileInfo(hex).fileName() + ": " + FirmwareFile::describe(file));
    int deviceBoard = session ? gEnv.pDeviceConfig->info.board_id : 0;
    FirmwareFile::Check check = FirmwareFile::check(file, deviceBoard, stated);
    if (check.verdict != FirmwareFile::Ok) {
        out("Not flashed. " + check.message);
        if (check.verdict == FirmwareFile::Confirm) {
            out(file.tagged ? QStringLiteral("If you're sure, say which board it's on: --board %1")
                                  .arg(HsrBoard::revisionName(file.boardId).mid(4))
                            : QStringLiteral("If you're sure, say which board it's on: --board 3.0 or --board 4.0"));
        }
        return 1;
    }
    AvrFlasher avr;
    bool done = false, ok = false;
    int lastPercent = -10;
    QObject::connect(&avr, &AvrFlasher::status, [](const QString &s) { out(s); });
    QObject::connect(&avr, &AvrFlasher::progress, [&](int p) {
        if ((p >= lastPercent + 10 || p == 100) && p != lastPercent) {
            out(QStringLiteral("  %1 %").arg(p));
            lastPercent = p;
        }
    });
    QObject::connect(&avr, &AvrFlasher::finished, [&](bool success, const QString &message) {
        ok = success;
        done = true;
        out(message);
    });
    avr.prepare();
    if (session) {
        out("Restarting the device into its bootloader...");
        if (session->bootloader() == false) {
            out("The device didn't answer the bootloader command.");
            return 1;
        }
        avr.flashWhenBootloaderAppears(hex, 10000);
    } else if (port.isEmpty() == false) {
        out("1200-baud touch on " + port);
        if (AvrFlasher::touch1200(port) == false) {
            out(port + " couldn't be opened.");
            return 1;
        }
        avr.flashWhenBootloaderAppears(hex, 10000);
    } else {
        out("Double-tap RST on the Pro Micro now...");
        avr.flashWhenBootloaderAppears(hex, 20000);
    }
    waitUntil([&] { return done; }, 120000);
    return ok ? 0 : 1;
}

int roundtrip(Session &s)
{
    // 1. read the current settings
    if (s.read() == false) { out("FAIL: read"); return 1; }
    dev_config_t original = gEnv.pDeviceConfig->config;
    out("Read the settings.");

    // 2. write changed settings (most fields touched), read them back
    dev_config_t test = original;
    strncpy(test.device_name, "HSR Roundtrip Test", HSR_NAME_LEN);
    test.button_debounce_ms = 17;
    test.buttons[20].physical_num = 3;
    test.buttons[20].type = SWITCH_CENTER;
    test.axis_config[5].source_main = 2;
    test.axis_config[5].out_enabled = 1;
    test.axes_to_buttons[0].buttons_cnt = 3;
    test.led_pwm_config[2].duty_cycle = 77;
    test.encoders[7] = ENCODER_CONF_4x;
    gEnv.pDeviceConfig->config = test;
    if (s.write() == false) { out("FAIL: write"); return 1; }
    out("Wrote test settings; the device restarted.");
    if (s.read() == false) { out("FAIL: read back"); return 1; }
    bool same = memcmp(&test, &gEnv.pDeviceConfig->config, sizeof(test)) == 0;
    out(same ? "Read back identical: OK" : "FAIL: read back differs");
    printInfo(s.names());

    // 3. put the original back
    gEnv.pDeviceConfig->config = original;
    if (s.write() == false) { out("FAIL: restoring the original settings"); return 1; }
    if (s.read() == false) { out("FAIL: read after restore"); return 1; }
    bool restored = memcmp(&original, &gEnv.pDeviceConfig->config, sizeof(original)) == 0;
    out(restored ? "Original settings restored: OK" : "FAIL: restored settings differ");
    return same && restored ? 0 : 1;
}

QString sensorLine(const hsr_sensor_status_t &s)
{
    static const char *const names[] = {"starting", "OK", "no magnet", "magnet weak", "magnet strong", "no sensor",
                                        "no switch", "bus error"};
    QString line = QStringLiteral("%1 kHz, %2 bus resets |").arg(s.i2c_khz).arg(s.bus_resets);
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        const hsr_sensor_port_t &p = s.port[i];
        line += QStringLiteral(" AX%1 %2%3 raw %4 out %5 agc %6 err %7 |").arg(i + 1)
                    .arg(p.state < 8 ? names[p.state] : "?").arg((p.flags & HSR_SENSOR_RANGE_OK) ? " (range)" : "")
                    .arg(p.raw_angle).arg(p.angle).arg(p.agc).arg(p.errors);
    }
    return line;
}

QString sensorConfigLine(const hsr_sensor_config_t &c)
{
    QString line = QStringLiteral("v%1, %2 kHz |").arg(c.version).arg(c.i2c_khz);
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        line += QStringLiteral(" AX%1 %2-%3").arg(i + 1).arg(c.range[i].zpos).arg(c.range[i].mpos);
    }
    return line;
}

// Rev 4.0: the AS5600 settings saved, read back, refused when out of range,
// and the originals put back. Works without sensors: the board keeps the
// settings whether or not anything answers on its ports.
int sensorRoundtrip(Session &s)
{
    if (s.readSensors() == false) { out("FAIL: reading the AS5600 settings"); return 1; }
    hsr_sensor_config_t original = gEnv.pDeviceConfig->sensorConfig;
    out("Read:      " + sensorConfigLine(original));

    hsr_sensor_config_t test = original;
    test.i2c_khz = original.i2c_khz == 50 ? 25 : 50;
    test.range[0] = {1000, 3000};
    test.range[2] = {3900, 200};        // across 0
    test.range[3] = {0, 0};
    if (s.writeSensors(test) == false) { out("FAIL: writing test settings"); return 1; }
    if (s.readSensors() == false) { out("FAIL: read back"); return 1; }
    bool same = memcmp(&test, &gEnv.pDeviceConfig->sensorConfig, sizeof(test)) == 0;
    out("Wrote:     " + sensorConfigLine(test));
    out(same ? "Read back identical: OK" : "FAIL: read back " + sensorConfigLine(gEnv.pDeviceConfig->sensorConfig));
    bool clock = s.sensorStatus(3, 2000) && gEnv.pDeviceConfig->sensorStatus.i2c_khz == test.i2c_khz;
    out(clock ? "The status reports the new clock: OK" : "FAIL: the status doesn't report the new clock");
    out("Status:    " + sensorLine(gEnv.pDeviceConfig->sensorStatus));

    // out of range: refused, and nothing changes
    hsr_sensor_config_t bad = test;
    bad.range[1] = {100, 150};          // under 18 degrees
    bool refused = s.writeSensors(bad) == false;
    bad = test;
    bad.i2c_khz = 40;
    refused = refused && s.writeSensors(bad) == false;
    bool kept = s.readSensors() && memcmp(&test, &gEnv.pDeviceConfig->sensorConfig, sizeof(test)) == 0;
    out(refused && kept ? "Out-of-range settings refused, nothing changed: OK" : "FAIL: out-of-range settings");

    if (s.writeSensors(original) == false || s.readSensors() == false) { out("FAIL: restoring"); return 1; }
    bool restored = memcmp(&original, &gEnv.pDeviceConfig->sensorConfig, sizeof(original)) == 0;
    out(restored ? "Original settings restored: OK" : "FAIL: restored settings differ");
    return same && clock && refused && kept && restored ? 0 : 1;
}
}

bool Cli::isCliCommand(const QStringList &args)
{
    for (const QString &a : args) {
        if (COMMANDS.contains(a)) return true;
    }
    return false;
}

int Cli::run(const QStringList &args)
{
    attachConsole();
    auto value = [&](const QString &opt) {
        int i = args.indexOf(opt);
        return (i >= 0 && i + 1 < args.size()) ? args[i + 1] : QString();
    };
    int deviceIndex = qMax(1, value("--device").toInt()) - 1;

    if (args.contains("--help")) {
        out("HeliSR Configurator " APP_VERSION);
        out("  --info | --read <file.cfg> | --write <file.cfg> | --write-defaults | --params [s]");
        out("  --flash <file.hex> | --flash-new <file.hex> [--port COMx] [--board 3.0|4.0] | --roundtrip   [--device <n>]");
        out("  --sensors [s] | --sensor-roundtrip   (HeliSR Rev 4.0 boards)");
        out("  --save-defaults <file.cfg> | --hex-info <file.hex>   (no device needed)");
        out("--flash checks which board the file is for. --board says which board the Pro Micro is on, when");
        out("its firmware doesn't (a new Pro Micro) or says another one.");
        return 0;
    }
    int stated = statedBoard(value("--board"));
    if (stated < 0) {
        out("--board takes 3.0 or 4.0");
        return 2;
    }
    if (args.contains("--hex-info")) {
        FirmwareFile::Info file = FirmwareFile::read(value("--hex-info"));
        out(value("--hex-info") + ": " + FirmwareFile::describe(file));
        if (file.readable) out(QStringLiteral("%1 bytes of program").arg(file.bytes));
        return file.readable ? 0 : 1;
    }
    if (args.contains("--save-defaults")) {
        QString file = value("--save-defaults");
        if (file.isEmpty()) {
            out("--save-defaults needs a file name");
            return 2;
        }
        dev_config_t cfg;
        hsr_config_defaults(&cfg);
        ConfigToFile::saveDeviceConfigToFile(QFileInfo(file).absoluteFilePath(), cfg);
        out("Saved the factory settings to " + file);
        return 0;
    }
    if (args.contains("--flash-new")) {
        return flash(value("--flash-new"), nullptr, value("--port"), stated);
    }

    Session s(deviceIndex);
    if (s.connect() == false) {
        return 1;
    }
    if (args.contains("--flash")) {
        return flash(value("--flash"), &s, QString(), stated);
    }
    if (s.compatible() == false) {
        return 1;
    }

    if (args.contains("--info")) {
        printInfo(s.names());
        return 0;
    }
    if (args.contains("--read")) {
        QString file = value("--read");
        if (s.read() == false) { out("Reading the settings failed."); return 1; }
        ConfigToFile::saveDeviceConfigToFile(QFileInfo(file).absoluteFilePath(), gEnv.pDeviceConfig->config);
        out("Saved the settings to " + file);
        return 0;
    }
    if (args.contains("--write") || args.contains("--write-defaults")) {
        dev_config_t cfg;
        hsr_config_defaults(&cfg);
        if (args.contains("--write")) {
            QString file = value("--write");
            if (ConfigToFile::loadDeviceConfigFromFile(nullptr, file, cfg) == false) {
                out("Couldn't load " + file);
                return 1;
            }
        }
        gEnv.pDeviceConfig->config = cfg;
        if (s.write() == false) { out("Writing the settings failed."); return 1; }
        out("Settings written; the device restarted with them.");
        return 0;
    }
    if (args.contains("--params")) {
        int seconds = qMax(1, value("--params").toInt());
        QElapsedTimer t;
        t.start();
        while (t.elapsed() < seconds * 1000) {
            waitUntil([] { return false; }, 250);
            const params_report_t &p = gEnv.pDeviceConfig->paramsReport;
            QString line = QStringLiteral("%1 ms  AX:").arg(t.elapsed(), 5);
            for (int i = 0; i < HSR_ANALOG_SOURCES; ++i) {
                line += QStringLiteral(" %1").arg(p.analog_inputs[i], 4);
            }
            line += "  inputs:";
            for (int i = HSR_MAX_PHYS / 8 - 1; i >= 0; --i) {
                line += QStringLiteral(" %1").arg(p.phy_button_data[i], 2, 16, QChar('0'));
            }
            line += "  axes:";
            for (int i = 0; i < 4; ++i) {
                line += QStringLiteral(" %1").arg(p.axis_data[i], 6);
            }
            out(line);
        }
        out(QStringLiteral("%1 live data packets in %2 s").arg(s.paramsCount()).arg(seconds));
        return 0;
    }
    if (args.contains("--roundtrip")) {
        return roundtrip(s);
    }
    if (args.contains("--sensors") || args.contains("--sensor-roundtrip")) {
        if (gEnv.pDeviceConfig->info.board_id != HSR_BOARD_REV40) {
            out("The device isn't a HeliSR Rev 4.0 board: it has no I2C sensors.");
            return 1;
        }
        if (args.contains("--sensor-roundtrip")) {
            return sensorRoundtrip(s);
        }
        if (s.readSensors()) out("Settings: " + sensorConfigLine(gEnv.pDeviceConfig->sensorConfig));
        int seconds = qMax(1, value("--sensors").toInt());
        QElapsedTimer t;
        t.start();
        while (t.elapsed() < seconds * 1000) {
            if (s.sensorStatus(5, 2000) == false) { out("FAIL: no status"); return 1; }
            out(QStringLiteral("%1 ms  ").arg(t.elapsed(), 5) + sensorLine(gEnv.pDeviceConfig->sensorStatus));
        }
        return 0;
    }
    return 0;
}
