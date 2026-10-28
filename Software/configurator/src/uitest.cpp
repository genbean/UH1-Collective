#include "uitest.h"
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QFileInfo>
#include <QPushButton>
#include <QTabWidget>
#include <QRandomGenerator>
#include <QThread>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include "deviceconfig.h"
#include "global.h"
#include "boardconfig.h"
#include "configtofile.h"
#include "helisrboard.h"
#include "mainwindow.h"
#include "shared/helisr_defaults.h"

namespace
{
void out(const QString &text)
{
    fputs(qPrintable(text + "\n"), stdout);
    fflush(stdout);
}

// ------------------------------------------------------- random settings --
// Values the pages can show: the ranges of their controls and the board's rules.
dev_config_t randomConfig(QRandomGenerator &rng)
{
    auto r = [&](int lo, int hi) { return int(rng.bounded(lo, hi + 1)); };
    dev_config_t c;
    hsr_config_defaults(&c);

    // name: printable ASCII, sometimes all 26 characters (no terminating NUL)
    memset(c.device_name, 0, sizeof(c.device_name));
    int len = rng.bounded(4) == 0 ? HSR_NAME_LEN : r(1, HSR_NAME_LEN - 1);
    for (int i = 0; i < len; ++i) c.device_name[i] = char(r(' ', '~'));
    c.vid = quint16(r(1, 0xFFFF));
    c.pid = quint16(r(1, 0xFFFF));
    c.exchange_period_ms = uint8_t(r(2, 255));
    c.button_debounce_ms = uint16_t(r(0, 65535));
    c.a2b_debounce_ms = uint16_t(r(0, 65535));
    c.encoder_press_time_ms = uint8_t(r(0, 255));
    c.button_timer1_ms = uint16_t(r(0, 65535));
    c.button_timer2_ms = uint16_t(r(0, 65535));
    c.button_timer3_ms = uint16_t(r(0, 65535));
    c.button_polling_interval_ticks = uint8_t(r(1, 20));
    c.encoder_polling_interval_ticks = uint8_t(r(1, 20));

    // spare pins the board has (Rev 4.0 has no pin 14)
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        if (HsrBoard::spareExists(i) == false) {
            c.pins[i] = PIN_NOT_USED;
            continue;
        }
        QVector<int> funcs = {PIN_NOT_USED, PIN_BUTTON_GND, PIN_BUTTON_VCC, PIN_LED_SINGLE};
        if (HsrBoard::spareIsAnalog(i)) funcs << PIN_AXIS_ANALOG;
        if (HsrBoard::spareIsPwm(i)) funcs << PIN_LED_PWM;
        c.pins[i] = pin_func_t(funcs[rng.bounded(int(funcs.size()))]);
    }

    // axis ranges: at most 37 in all
    int ranges = 0;
    int a2b[HSR_MAX_AXES];
    for (int a = 0; a < HSR_MAX_AXES; ++a) {
        int cnt = rng.bounded(3) == 0 ? r(1, 12) : 0;
        cnt = qMin(cnt, HSR_MAX_A2B_BUTTONS - ranges);
        ranges += cnt;
        a2b[a] = cnt;
        axis_to_buttons_t &t = c.axes_to_buttons[a];
        t.buttons_cnt = uint8_t(cnt);
        memset(t.points, 0, sizeof(t.points));
        if (cnt > 0) {
            // increasing points, as the slider keeps them
            int prev = r(0, 20);
            for (int j = 0; j <= cnt; ++j) {
                t.points[j] = uint8_t(qMin(prev, 255));
                prev += r(1, 255 / (cnt + 1));
            }
        } else {
            t.points[1] = 255;
        }
    }

    // axes
    QVector<int> sources = {SOURCE_NO, SOURCE_ENCODER};
    for (int s = 0; s < HSR_ANALOG_SOURCES; ++s) {
        if (HsrBoard::analogSourceAvailable(s, c.pins)) sources << s;
    }
    for (int a = 0; a < HSR_MAX_AXES; ++a) {
        axis_config_t &x = c.axis_config[a];
        x.calib_min = int16_t(r(AXIS_MIN_VALUE, -1));
        x.calib_max = int16_t(r(1, AXIS_MAX_VALUE));
        x.is_centered = uint8_t(r(0, 1));
        // the page keeps the centre half-way unless it's set by hand
        x.calib_center = int16_t(x.is_centered ? r(x.calib_min, x.calib_max) : (x.calib_max + x.calib_min) / 2);
        x.out_enabled = uint8_t(r(0, 1));
        x.inverted = uint8_t(r(0, 1));
        x.function = uint8_t(r(0, 3));
        x.filter = uint8_t(r(0, 7));
        for (int p = 0; p < 11; ++p) x.curve_shape[p] = int8_t(r(-100, 100));
        x.resolution = uint8_t(r(0, 15));
        x.channel = uint8_t(r(0, HSR_MAX_ENCODERS - 1));
        x.deadband_size = uint8_t(r(0, 127));
        x.is_dynamic_deadband = uint8_t(r(0, 1));
        x.source_main = axis_source_t(sources[rng.bounded(int(sources.size()))]);
        x.source_secondary = uint8_t(r(0, 7));
        x.offset_angle = uint8_t(r(0, 24));
        x.button1 = int8_t(r(-1, HSR_MAX_BUTTONS - 1));
        x.button2 = int8_t(r(-1, HSR_MAX_BUTTONS - 1));
        x.button3 = int8_t(r(-1, HSR_MAX_BUTTONS - 1));
        x.divider = uint8_t(r(0, 255));
        x.button1_type = uint8_t(r(0, 5));
        x.button2_type = uint8_t(r(0, 3));
        x.button3_type = uint8_t(r(0, 5));
        x.prescaler = uint8_t(r(0, 255));
    }

    // buttons: inputs that exist; at most 8 of each encoder input type
    QVector<HsrBoard::PhysInput> phys = HsrBoard::physicalInputs(c.pins, a2b);
    int encA = 0, encB = 0;
    for (int i = 0; i < HSR_MAX_BUTTONS; ++i) {
        button_t &b = c.buttons[i];
        b.physical_num = int8_t(rng.bounded(5) == 0 ? -1 : phys[rng.bounded(int(phys.size()))].phys);
        int type;
        do {
            type = r(0, SWITCH_CENTER);
        } while ((type == ENCODER_INPUT_A && encA >= HSR_MAX_ENCODERS) || (type == ENCODER_INPUT_B && encB >= HSR_MAX_ENCODERS));
        encA += type == ENCODER_INPUT_A;
        encB += type == ENCODER_INPUT_B;
        b.type = uint8_t(type);
        b.shift_modificator = uint8_t(r(0, HSR_MAX_SHIFTS));
        b.is_inverted = uint8_t(r(0, 1));
        b.is_disabled = uint8_t(r(0, 1));
        b.delay_timer = uint8_t(r(0, 3));
        b.press_timer = uint8_t(r(0, 3));
    }
    for (int i = 0; i < HSR_MAX_SHIFTS; ++i) c.shift_config[i].button = int8_t(r(-1, HSR_MAX_BUTTONS - 1));
    for (int i = 0; i < HSR_MAX_ENCODERS; ++i) c.encoders[i] = encoder_t(r(0, 2));

    // LEDs
    for (int ch = 0; ch < HSR_MAX_PWM; ++ch) {
        c.led_pwm_config[ch].duty_cycle = uint8_t(r(0, 100));
        c.led_pwm_config[ch].axis_num = uint8_t(r(0, 7));
        c.led_pwm_config[ch].is_axis = uint8_t(r(0, 1));
    }
    for (int i = 0; i < HSR_MAX_LEDS; ++i) {
        c.leds[i].input_num = int8_t(r(-1, HSR_MAX_BUTTONS - 1));
        c.leds[i].type = uint8_t(r(0, 1));
        int t = r(0, 4);
        c.leds[i].timer = uint8_t(t == 4 ? 15 : t);
    }
    for (int i = 0; i < 4; ++i) c.led_timer_ms[i] = uint16_t(r(0, 65535));
    return c;
}

// Parts the firmware never reads, so the pages needn't keep them.
void normalize(dev_config_t &c)
{
    c.config_version = HSR_CONFIG_VERSION;
    for (int a = 0; a < HSR_MAX_AXES; ++a) {
        axis_to_buttons_t &t = c.axes_to_buttons[a];
        int cnt = qMin<int>(t.buttons_cnt, HSR_A2B_POINTS - 1);
        for (int j = cnt > 0 ? cnt + 1 : 0; j < HSR_A2B_POINTS; ++j) t.points[j] = 0;
        c.axis_config[a].reserved0 = 0;
        c.axis_config[a].reserved1 = 0;
    }
    for (int ch = 0; ch < HSR_MAX_PWM; ++ch) c.led_pwm_config[ch].reserved = 0;
    for (int i = 0; i < HSR_MAX_LEDS; ++i) c.leds[i].reserved = 0;
}

// ------------------------------------------------- naming a byte offset --
QString describe(int off)
{
#define AT(member) int(offsetof(dev_config_t, member))
#define SIZE(member) int(sizeof(((dev_config_t *)nullptr)->member))
#define IN(member) (off >= AT(member) && off < AT(member) + SIZE(member))
    auto elem = [&](int base, int size, const char *name) {
        int i = (off - base) / size;
        return QPair<QString, int>(QStringLiteral("%1[%2]").arg(name).arg(i), (off - base) % size);
    };
    if (IN(config_version)) return "config_version";
    if (IN(device_name)) return QStringLiteral("device_name[%1]").arg(off - AT(device_name));
    if (IN(button_debounce_ms)) return "button_debounce_ms";
    if (IN(encoder_press_time_ms)) return "encoder_press_time_ms";
    if (IN(exchange_period_ms)) return "exchange_period_ms";
    if (IN(pins)) return QStringLiteral("pins[%1] (%2)").arg(off - AT(pins)).arg(HsrBoard::spareName(off - AT(pins)));
    if (IN(axis_config)) {
        auto e = elem(AT(axis_config), sizeof(axis_config_t), "axis_config");
        static const char *const f[30] = {"calib_min", "calib_min", "calib_center", "calib_center", "calib_max", "calib_max",
            "out_enabled/inverted/is_centered/function/filter", "curve_shape[0]", "curve_shape[1]", "curve_shape[2]",
            "curve_shape[3]", "curve_shape[4]", "curve_shape[5]", "curve_shape[6]", "curve_shape[7]", "curve_shape[8]",
            "curve_shape[9]", "curve_shape[10]", "resolution/channel", "deadband_size/is_dynamic_deadband", "source_main",
            "source_secondary/offset_angle", "button1", "button2", "button3", "divider", "reserved0",
            "button1_type/button2_type/button3_type", "prescaler", "reserved1"};
        return e.first + "." + f[e.second];
    }
    if (IN(buttons)) {
        auto e = elem(AT(buttons), sizeof(button_t), "buttons");
        static const char *const f[3] = {"physical_num", "type/shift_modificator", "is_inverted/is_disabled/delay_timer/press_timer"};
        return e.first + "." + f[e.second];
    }
    if (IN(button_timer1_ms)) return "button_timer1_ms";
    if (IN(button_timer2_ms)) return "button_timer2_ms";
    if (IN(button_timer3_ms)) return "button_timer3_ms";
    if (IN(a2b_debounce_ms)) return "a2b_debounce_ms";
    if (IN(axes_to_buttons)) {
        auto e = elem(AT(axes_to_buttons), sizeof(axis_to_buttons_t), "axes_to_buttons");
        return e.first + (e.second < HSR_A2B_POINTS ? QStringLiteral(".points[%1]").arg(e.second) : QString(".buttons_cnt"));
    }
    if (IN(shift_config)) return QStringLiteral("shift_config[%1]").arg(off - AT(shift_config));
    if (IN(vid)) return "vid";
    if (IN(pid)) return "pid";
    if (IN(led_pwm_config)) {
        auto e = elem(AT(led_pwm_config), sizeof(led_pwm_config_t), "led_pwm_config");
        return e.first + (e.second == 0 ? ".duty_cycle" : ".axis_num/is_axis");
    }
    if (IN(leds)) {
        auto e = elem(AT(leds), sizeof(led_config_t), "leds");
        return e.first + (e.second == 0 ? ".input_num" : ".type/timer");
    }
    if (IN(led_timer_ms)) return QStringLiteral("led_timer_ms[%1]").arg((off - AT(led_timer_ms)) / 2);
    if (IN(encoders)) return QStringLiteral("encoders[%1]").arg(off - AT(encoders));
    if (IN(button_polling_interval_ticks)) return "button_polling_interval_ticks";
    if (IN(encoder_polling_interval_ticks)) return "encoder_polling_interval_ticks";
    return QStringLiteral("offset %1").arg(off);
#undef AT
#undef SIZE
#undef IN
}

void settle()
{
    // queued updates (the board page's rebuild of the other pages) run here
    for (int i = 0; i < 5; ++i) {
        QCoreApplication::processEvents();
    }
}
}

namespace
{
// Waits until the window's Read button is enabled: a compatible device is
// connected and no transfer is running.
bool waitReady(QPushButton *read, int timeoutMs)
{
    QElapsedTimer t;
    t.start();
    while (t.elapsed() < timeoutMs) {
        QCoreApplication::processEvents(QEventLoop::AllEvents, 50);
        if (read->isEnabled()) return true;
        QThread::msleep(10);
    }
    return false;
}

// With a device: the window's own Write and Read buttons, the device's
// restart and the reconnection, then the original settings put back.
int deviceTest(MainWindow &window, QRandomGenerator &rng)
{
    QPushButton *read = window.findChild<QPushButton *>("pushButton_ReadConfig");
    QPushButton *write = window.findChild<QPushButton *>("pushButton_WriteConfig");
    if (!read || !write || waitReady(read, 10000) == false) {
        out("FAIL: no device ready");
        return 1;
    }
    auto readFromDevice = [&](dev_config_t *cfg) {
        memset(&gEnv.pDeviceConfig->config, 0, sizeof(dev_config_t));
        read->click();
        if (waitReady(read, 15000) == false) return false;
        *cfg = gEnv.pDeviceConfig->config;
        return true;
    };
    auto writeToDevice = [&](const dev_config_t &cfg) {
        gEnv.pDeviceConfig->config = cfg;
        window.UiReadFromConfig();
        settle();
        write->click();
        QThread::msleep(100);
        return waitReady(read, 20000);      // written, restarted, reconnected
    };

    dev_config_t original;
    if (readFromDevice(&original) == false) { out("FAIL: Read button"); return 1; }
    out("Read the device's settings with the Read button.");

    dev_config_t expected = randomConfig(rng);
    expected.vid = original.vid;            // keep the board where Windows knows it
    expected.pid = original.pid;
    expected.exchange_period_ms = 5;
    if (writeToDevice(expected) == false) { out("FAIL: Write button / reconnect"); return 1; }
    out("Wrote random settings with the Write button; the device restarted and reconnected.");
    dev_config_t got;
    if (readFromDevice(&got) == false) { out("FAIL: read back"); return 1; }
    normalize(expected);
    normalize(got);
    int diffs = 0;
    const uint8_t *e = reinterpret_cast<const uint8_t *>(&expected);
    const uint8_t *g = reinterpret_cast<const uint8_t *>(&got);
    for (int off = 0; off < int(sizeof(dev_config_t)); ++off) {
        if (e[off] != g[off] && diffs++ < 25) {
            out(QStringLiteral("  %1: expected 0x%2, got 0x%3").arg(describe(off))
                    .arg(e[off], 2, 16, QChar('0')).arg(g[off], 2, 16, QChar('0')));
        }
    }
    out(diffs ? QStringLiteral("FAIL: %1 byte(s) differ after the device round trip").arg(diffs)
              : QStringLiteral("Read back identical through the device: OK"));

    if (writeToDevice(original) == false) { out("FAIL: restoring the original settings"); return 1; }
    dev_config_t restored;
    if (readFromDevice(&restored) == false) { out("FAIL: read after restore"); return 1; }
    normalize(original);
    normalize(restored);
    bool same = memcmp(&original, &restored, sizeof(original)) == 0;
    out(same ? "Original settings restored: OK" : "FAIL: restored settings differ");
    return diffs == 0 && same ? 0 : 1;
}


// Shows settings on every page and writes them back; returns the bytes that changed.
QStringList throughPages(MainWindow &window, dev_config_t expected)
{
    gEnv.pDeviceConfig->config = expected;
    window.UiReadFromConfig();
    settle();

    // anything a page doesn't write keeps this pattern and shows up below
    memset(&gEnv.pDeviceConfig->config, 0x5A, sizeof(dev_config_t));
    window.UiWriteToConfig(false);
    dev_config_t got = gEnv.pDeviceConfig->config;

    normalize(expected);
    normalize(got);
    const uint8_t *e = reinterpret_cast<const uint8_t *>(&expected);
    const uint8_t *g = reinterpret_cast<const uint8_t *>(&got);
    QStringList diffs;
    for (int off = 0; off < int(sizeof(dev_config_t)); ++off) {
        if (e[off] != g[off]) {
            diffs << QStringLiteral("  %1: expected 0x%2, got 0x%3").arg(describe(off))
                         .arg(e[off], 2, 16, QChar('0')).arg(g[off], 2, 16, QChar('0'));
        }
    }
    return diffs;
}
}

// The Board page as a picture. Rev 4.0 has no board yet, so its I2C helper is
// shown with made-up readings (the window is told a Rev 4.0 device is there):
// a way to look at the page, not a test of it.
static int screenshot(MainWindow &window, const QString &file)
{
    if (HsrBoard::isRev40()) {
        DeviceConfig *d = gEnv.pDeviceConfig;
        d->info.board_id = HSR_BOARD_REV40;
        d->sensorConfig = {HSR_SENSOR_CONFIG_VERSION, 100, {{3412, 3801}, {0, 0}, {0, 0}, {310, 1250}}};
        hsr_sensor_status_t &s = d->sensorStatus;
        s = {};
        s.i2c_khz = 100;
        s.port[0] = {HSR_SENSOR_OK, HSR_SENSOR_RANGE_OK, 0x20, 131, 3602, 2002, 0};
        s.port[1] = {HSR_SENSOR_NO_SENSOR, 0, 0, 0, 0, 0, 0};
        s.port[2] = {HSR_SENSOR_NO_SENSOR, 0, 0, 0, 0, 0, 0};
        s.port[3] = {HSR_SENSOR_MAGNET_WEAK, HSR_SENSOR_RANGE_OK, 0x30, 255, 702, 1700, 3};
        for (int i = 0; i < HSR_AX_INPUTS; ++i) d->paramsReport.analog_inputs[i] = uint16_t(s.port[i].angle * HSR_RAW_MAX / 4095);
        d->paramsReport.analog_inputs_a2a3[0] = 1234;
        window.boardConfig()->setDeviceConnected(true);
        window.boardConfig()->sensorConfigReceived(true);
        window.boardConfig()->sensorStatusReceived();
        window.boardConfig()->updateLiveData();
    }
    QTabWidget *tabs = window.findChild<QTabWidget *>("tabWidget");
    QWidget *page = window.findChild<QWidget *>("tab_PinConfig");
    if (tabs && page) tabs->setCurrentWidget(page);
    window.resize(1500, 820);
    window.show();
    settle();
    QThread::msleep(300);
    settle();
    bool ok = window.grab().save(file);
    out(ok ? "Saved " + file : "FAIL: couldn't save " + file);
    return ok ? 0 : 1;
}

bool UiTest::isUiTestCommand(const QStringList &args)
{
    return args.contains("--ui-test") || args.contains("--ui-device-test") || args.contains("--ui-test-file")
           || args.contains("--ui-screenshot");
}

int UiTest::run(MainWindow &window, const QStringList &args)
{
    int i = args.indexOf("--ui-test");
    int count = (i >= 0 && i + 1 < args.size()) ? qMax(1, args[i + 1].toInt()) : 20;
    int s = args.indexOf("--seed");
    quint32 seed = (s >= 0 && s + 1 < args.size()) ? args[s + 1].toUInt() : 1;

    QElapsedTimer t;
    t.start();
    while (window.isInitialized() == false && t.elapsed() < 20000) {
        QCoreApplication::processEvents(QEventLoop::AllEvents, 50);
        QThread::msleep(5);
    }
    if (window.isInitialized() == false) {
        out("FAIL: the pages didn't finish starting");
        return 1;
    }

    // the window saves the board it shows when it closes: leave the user's choice as it was
    struct KeepBoard
    {
        int board = HsrBoard::board();
        ~KeepBoard() { HsrBoard::setBoard(board); }
    } keepBoard;

    QRandomGenerator rng(seed);
    if (args.contains("--ui-device-test")) {
        // the device's board, once it has connected; then kept
        QPushButton *read = window.findChild<QPushButton *>("pushButton_ReadConfig");
        if (read) waitReady(read, 10000);
        window.showBoard(HsrBoard::board(), false);
        out("Board: " + HsrBoard::boardName(HsrBoard::board()));
        return deviceTest(window, rng);
    }
    int b = args.indexOf("--board");
    QString boardArg = (b >= 0 && b + 1 < args.size()) ? args[b + 1] : QString();
    int board = HsrBoard::board();
    if (boardArg == "3.0") board = HSR_BOARD_REV30;
    else if (boardArg == "4.0") board = HSR_BOARD_REV40;
    else if (boardArg.isEmpty() == false) {
        out("--board takes 3.0 or 4.0");
        return 2;
    }
    // a device connecting during the test mustn't change the pages under it
    window.showBoard(board, false);
    settle();
    out("Board: " + HsrBoard::boardName(HsrBoard::board()));
    int shot = args.indexOf("--ui-screenshot");
    if (shot >= 0) {
        return shot + 1 < args.size() ? screenshot(window, args[shot + 1]) : 2;
    }
    // profiles: every file named after --ui-test-file, until the next option
    int f = args.indexOf("--ui-test-file");
    if (f >= 0) {
        int failedFiles = 0, files = 0;
        for (int k = f + 1; k < args.size() && args[k].startsWith("--") == false; ++k, ++files) {
            dev_config_t expected;
            hsr_config_defaults(&expected);
            if (ConfigToFile::loadDeviceConfigFromFile(nullptr, args[k], expected) == false) {
                out("FAIL: couldn't load " + args[k]);
                failedFiles++;
                continue;
            }
            // a pin the board doesn't have (Rev 4.0's pin 14) can't come back from its pages
            for (int i = 0; i < HSR_SPARE_PINS; ++i) {
                if (HsrBoard::spareExists(i) == false) expected.pins[i] = PIN_NOT_USED;
            }
            QStringList diffs = throughPages(window, expected);
            out(QStringLiteral("%1: %2").arg(QFileInfo(args[k]).fileName(),
                                             diffs.isEmpty() ? "unchanged through the pages" : "CHANGED"));
            for (int d = 0; d < qMin(int(diffs.size()), 25); ++d) out(diffs[d]);
            failedFiles += !diffs.isEmpty();
        }
        return failedFiles || files == 0 ? 1 : 0;
    }
    int failed = 0;
    for (int n = 0; n < count; ++n) {
        QStringList diffs = throughPages(window, randomConfig(rng));
        if (diffs.isEmpty()) {
            continue;
        }
        failed++;
        out(QStringLiteral("Setup %1 (seed %2): %3 byte(s) differ").arg(n + 1).arg(seed).arg(diffs.size()));
        for (int d = 0; d < qMin(int(diffs.size()), 25); ++d) out(diffs[d]);
    }
    out(QStringLiteral("%1 of %2 random setups came back unchanged through the pages").arg(count - failed).arg(count));
    return failed ? 1 : 0;
}
