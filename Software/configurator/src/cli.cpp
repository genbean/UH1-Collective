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
                              "--flash-new", "--roundtrip", "--help"};

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
};

void printInfo(const QStringList &names)
{
    const hsr_info_t &i = gEnv.pDeviceConfig->info;
    out("Devices:       " + names.join(", "));
    out("Firmware:      " + versionText(i.firmware_version) + QStringLiteral(", %1 MHz").arg(i.cpu_mhz)
        + (i.usb_serial_port ? ", with USB serial port" : ""));
    out(QStringLiteral("Protocol:      %1, board 0x%2, settings v%3 (%4 bytes)")
            .arg(i.protocol_version).arg(i.board_id, 2, 16, QChar('0')).arg(i.config_version).arg(i.config_size));
    out(QStringLiteral("Board ID:      %1, settings from %2")
            .arg(i.unique_id, 8, 16, QChar('0')).arg(i.config_from_eeprom ? "EEPROM" : "factory defaults"));
    out(QStringLiteral("Health:        %1 B stack never used, longest pass %2 us, %3 commands, %4 replies dropped")
            .arg(i.stack_free).arg(i.pass_max_us).arg(i.commands).arg(i.replies_dropped));
}

int flash(const QString &hex, Session *session, const QString &port)
{
    if (QFileInfo::exists(hex) == false) {
        out("No such file: " + hex);
        return 2;
    }
    AvrFlasher avr;
    bool done = false, ok = false;
    int lastPercent = -10;
    QObject::connect(&avr, &AvrFlasher::status, [](const QString &s) { out(s); });
    QObject::connect(&avr, &AvrFlasher::progress, [&](int p) {
        if (p >= lastPercent + 10 || p == 100) {
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
        out("  --flash <file.hex> | --flash-new <file.hex> [--port COMx] | --roundtrip   [--device <n>]");
        return 0;
    }
    if (args.contains("--flash-new")) {
        return flash(value("--flash-new"), nullptr, value("--port"));
    }

    Session s(deviceIndex);
    if (s.connect() == false) {
        return 1;
    }
    if (args.contains("--flash")) {
        return flash(value("--flash"), &s, QString());
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
    return 0;
}
