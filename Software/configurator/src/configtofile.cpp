#include "configtofile.h"
#include <QFileInfo>
#include <QMessageBox>
#include <QSettings>
#include "common_defines.h"
#include "helisrboard.h"

#include <QDebug>

// Keys missing from a file keep the value already in devC (the defaults when
// called after DeviceConfig::resetConfig()), so older profiles still load.

bool ConfigToFile::loadDeviceConfigFromFile(QWidget *parent, const QString &fileName, dev_config_t &devC)
{
    qDebug()<<"Load device config from file";
    if (fileName.isEmpty() || QFileInfo::exists(fileName) == false) {
        return false;
    }
    QSettings s(fileName, QSettings::IniFormat);

    s.beginGroup("DeviceUsbConfig");
    if (s.contains("ConfigVersion") == false) {
        s.endGroup();
        QMessageBox::warning(parent, tr("Not a HeliSR profile"),
                             tr("%1 isn't a HeliSR Configurator profile (FreeJoy profiles can't be used). Nothing was loaded.")
                                 .arg(QFileInfo(fileName).fileName()));
        return false;
    }
    std::string name = s.value("DeviceName", QString(QByteArray(devC.device_name, qstrnlen(devC.device_name, HSR_NAME_LEN))))
                           .toString().toStdString();
    for (uint i = 0; i < sizeof(devC.device_name); i++) {
        devC.device_name[i] = i < name.size() ? name[i] : '\0';
    }
    bool ok;
    devC.vid = s.value("Vid", QString::number(devC.vid, 16)).toString().toUShort(&ok, 16);
    devC.pid = s.value("Pid", QString::number(devC.pid, 16)).toString().toUShort(&ok, 16);
    devC.exchange_period_ms = uint8_t(s.value("USBExchange", devC.exchange_period_ms).toInt());
    s.endGroup();

    s.beginGroup("PinsConfig");
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        devC.pins[i] = uint8_t(s.value(HsrBoard::spareLabel(i), devC.pins[i]).toInt());
    }
    s.endGroup();

    s.beginGroup("ShiftConfig");
    for (int i = 0; i < HSR_MAX_SHIFTS; ++i) {
        devC.shift_config[i].button = int8_t(s.value("Shift" + QString::number(i), devC.shift_config[i].button).toInt());
    }
    s.endGroup();

    s.beginGroup("TimersConfig");
    devC.button_timer1_ms = uint16_t(s.value("Timer1", devC.button_timer1_ms).toInt());
    devC.button_timer2_ms = uint16_t(s.value("Timer2", devC.button_timer2_ms).toInt());
    devC.button_timer3_ms = uint16_t(s.value("Timer3", devC.button_timer3_ms).toInt());
    devC.button_debounce_ms = uint16_t(s.value("Debounce", devC.button_debounce_ms).toInt());
    devC.a2b_debounce_ms = uint16_t(s.value("A2bDebounce", devC.a2b_debounce_ms).toInt());
    devC.encoder_press_time_ms = uint8_t(s.value("EncoderPress", devC.encoder_press_time_ms).toInt());
    devC.button_polling_interval_ticks = uint8_t(s.value("ButtonsPolling", devC.button_polling_interval_ticks).toInt());
    devC.encoder_polling_interval_ticks = uint8_t(s.value("EncodersPolling", devC.encoder_polling_interval_ticks).toInt());
    s.endGroup();

    for (int i = 0; i < HSR_MAX_BUTTONS; ++i) {
        button_t &b = devC.buttons[i];
        s.beginGroup("ButtonsConfig_" + QString::number(i));
        b.physical_num = int8_t(s.value("ButtonPhysicNumber", b.physical_num).toInt());
        b.type = uint8_t(s.value("ButtonType", b.type).toInt());
        b.shift_modificator = uint8_t(s.value("ShiftMod", b.shift_modificator).toInt());
        b.is_inverted = uint8_t(s.value("Inverted", b.is_inverted).toInt());
        b.is_disabled = uint8_t(s.value("Disabled", b.is_disabled).toInt());
        b.delay_timer = uint8_t(s.value("DelayTimer", b.delay_timer).toInt());
        b.press_timer = uint8_t(s.value("PressTimer", b.press_timer).toInt());
        s.endGroup();
    }

    for (int i = 0; i < HSR_MAX_AXES; ++i) {
        axis_config_t &a = devC.axis_config[i];
        s.beginGroup("AxesConfig_" + QString::number(i));
        a.calib_min = int16_t(s.value("CalibMin", a.calib_min).toInt());
        a.calib_center = int16_t(s.value("CalibCenter", a.calib_center).toInt());
        a.calib_max = int16_t(s.value("CalibMax", a.calib_max).toInt());
        a.is_centered = uint8_t(s.value("IsCentered", a.is_centered).toInt());
        a.out_enabled = uint8_t(s.value("OutEnabled", a.out_enabled).toInt());
        a.inverted = uint8_t(s.value("Inverted", a.inverted).toInt());
        a.function = uint8_t(s.value("Function", a.function).toInt());
        a.filter = uint8_t(s.value("Filter", a.filter).toInt());
        a.resolution = uint8_t(s.value("Resolution", a.resolution).toInt());
        a.channel = uint8_t(s.value("Channel", a.channel).toInt());
        a.deadband_size = uint8_t(s.value("DeadbandSize", a.deadband_size).toInt());
        a.is_dynamic_deadband = uint8_t(s.value("DynDeadbandEnabled", a.is_dynamic_deadband).toInt());
        a.source_main = int8_t(s.value("SourceMain", a.source_main).toInt());
        a.source_secondary = uint8_t(s.value("SourceSecond", a.source_secondary).toInt());
        a.offset_angle = uint8_t(s.value("OffsetAngle", a.offset_angle).toInt());
        a.button1 = int8_t(s.value("Button1", a.button1).toInt());
        a.button2 = int8_t(s.value("Button2", a.button2).toInt());
        a.button3 = int8_t(s.value("Button3", a.button3).toInt());
        a.divider = uint8_t(s.value("Divider", a.divider).toInt());
        a.button1_type = uint8_t(s.value("Button1Type", a.button1_type).toInt());
        a.button2_type = uint8_t(s.value("Button2Type", a.button2_type).toInt());
        a.button3_type = uint8_t(s.value("Button3Type", a.button3_type).toInt());
        a.prescaler = uint8_t(s.value("Prescaler", a.prescaler).toInt());
        s.endGroup();

        s.beginGroup("AxesCurvesConfig_" + QString::number(i));
        for (int j = 0; j < 11; ++j) {      // 11 - axis curve points count
            a.curve_shape[j] = int8_t(s.value("Point_" + QString::number(j), a.curve_shape[j]).toInt());
        }
        s.endGroup();

        axis_to_buttons_t &a2b = devC.axes_to_buttons[i];
        s.beginGroup("Axes2bConfig_" + QString::number(i));
        a2b.buttons_cnt = uint8_t(s.value("ButtonsCount", a2b.buttons_cnt).toInt());
        for (int j = 0; j < HSR_A2B_POINTS; ++j) {
            a2b.points[j] = uint8_t(s.value("Point_" + QString::number(j), a2b.points[j]).toInt());
        }
        s.endGroup();
    }

    for (int i = 0; i < HSR_MAX_ENCODERS; ++i) {
        s.beginGroup("EncodersConfig_" + QString::number(i));
        devC.encoders[i] = uint8_t(s.value("EncType", devC.encoders[i]).toInt());
        s.endGroup();
    }

    // PWM channels, named after their pins
    s.beginGroup("LedsPWMConfig");
    for (int c = 0; c < HSR_MAX_PWM; ++c) {
        led_pwm_config_t &p = devC.led_pwm_config[c];
        QString key = "Pin" + HsrBoard::spareLabel(HsrBoard::spareOfPwmChannel(c));
        p.duty_cycle = uint8_t(s.value(key, p.duty_cycle).toInt());
        p.is_axis = s.value(key + "_AxisEnabled", bool(p.is_axis)).toBool();
        p.axis_num = uint8_t(s.value(key + "_AxisNum", p.axis_num).toInt());
    }
    s.endGroup();

    s.beginGroup("LedsMonoConfig");
    for (uint i = 0; i < std::size(devC.led_timer_ms); ++i) {
        devC.led_timer_ms[i] = uint16_t(s.value("Timer_" + QString::number(i + 1), devC.led_timer_ms[i]).toInt());
    }
    s.endGroup();

    // single LEDs, by spare pin
    for (int i = 0; i < HSR_MAX_LEDS; ++i) {
        led_config_t &l = devC.leds[i];
        s.beginGroup("LedsConfig_Pin" + HsrBoard::spareLabel(i));
        l.input_num = int8_t(s.value("InputNum", l.input_num).toInt());
        l.type = uint8_t(s.value("LedType", l.type).toInt());
        l.timer = uint8_t(s.value("Timer", l.timer).toInt());
        s.endGroup();
    }

    sanitize(devC);
    devC.config_version = HSR_CONFIG_VERSION;
    return true;
}

// Keep a hand-edited or damaged file from producing settings the board can't have.
void ConfigToFile::sanitize(dev_config_t &devC)
{
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        uint8_t &p = devC.pins[i];
        if (p > PIN_LED_PWM || (p == PIN_AXIS_ANALOG && !HsrBoard::spareIsAnalog(i))
                || (p == PIN_LED_PWM && !HsrBoard::spareIsPwm(i))) {
            p = PIN_NOT_USED;
        }
    }
    for (int i = 0; i < HSR_MAX_BUTTONS; ++i) {
        button_t &b = devC.buttons[i];
        if (b.physical_num >= HSR_MAX_PHYS) b.physical_num = -1;
        if (b.type > SWITCH_CENTER) b.type = BUTTON_NORMAL;
        if (b.shift_modificator > HSR_MAX_SHIFTS) b.shift_modificator = 0;
    }
    for (int i = 0; i < HSR_MAX_AXES; ++i) {
        axis_config_t &a = devC.axis_config[i];
        if (a.source_main >= HSR_ANALOG_SOURCES || (a.source_main < 0 && a.source_main != SOURCE_NO
                                                   && a.source_main != SOURCE_ENCODER)) {
            a.source_main = SOURCE_NO;
        }
        if (a.channel >= HSR_MAX_ENCODERS) a.channel = 0;
        if (devC.axes_to_buttons[i].buttons_cnt > HSR_A2B_POINTS - 1) devC.axes_to_buttons[i].buttons_cnt = HSR_A2B_POINTS - 1;
    }
    for (int i = 0; i < HSR_MAX_SHIFTS; ++i) {
        if (devC.shift_config[i].button >= HSR_MAX_BUTTONS) devC.shift_config[i].button = -1;
    }
    for (int i = 0; i < HSR_MAX_LEDS; ++i) {
        if (devC.leds[i].input_num >= HSR_MAX_BUTTONS) devC.leds[i].input_num = -1;
    }
}


void ConfigToFile::saveDeviceConfigToFile(const QString &fileName, dev_config_t &devC)
{
    qDebug()<<"SaveDeviceConfigToFile() started";
    if (fileName.isEmpty()) return;
    QSettings s(fileName, QSettings::IniFormat);
    if (s.isWritable() == false) {
        qDebug()<<"SaveDeviceConfigToFile() failed."<<fileName<<"Read-Only";
        return;
    }
    s.clear();

    s.beginGroup("DeviceUsbConfig");
    s.setValue("ConfigVersion", HSR_CONFIG_VERSION);
    s.setValue("DeviceName", QString(QByteArray(devC.device_name, qstrnlen(devC.device_name, HSR_NAME_LEN))));
    s.setValue("Vid", QString::number(devC.vid, 16));
    s.setValue("Pid", QString::number(devC.pid, 16));
    s.setValue("USBExchange", devC.exchange_period_ms);
    s.endGroup();

    s.beginGroup("PinsConfig");
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        s.setValue(HsrBoard::spareLabel(i), devC.pins[i]);
    }
    s.endGroup();

    s.beginGroup("ShiftConfig");
    for (int i = 0; i < HSR_MAX_SHIFTS; ++i) {
        s.setValue("Shift" + QString::number(i), devC.shift_config[i].button);
    }
    s.endGroup();

    s.beginGroup("TimersConfig");
    s.setValue("Timer1", devC.button_timer1_ms);
    s.setValue("Timer2", devC.button_timer2_ms);
    s.setValue("Timer3", devC.button_timer3_ms);
    s.setValue("Debounce", devC.button_debounce_ms);
    s.setValue("A2bDebounce", devC.a2b_debounce_ms);
    s.setValue("EncoderPress", devC.encoder_press_time_ms);
    s.setValue("ButtonsPolling", devC.button_polling_interval_ticks);
    s.setValue("EncodersPolling", devC.encoder_polling_interval_ticks);
    s.endGroup();

    for (int i = 0; i < HSR_MAX_BUTTONS; ++i) {
        const button_t &b = devC.buttons[i];
        s.beginGroup("ButtonsConfig_" + QString::number(i));
        s.setValue("ButtonPhysicNumber", b.physical_num);
        s.setValue("ButtonType", b.type);
        s.setValue("ShiftMod", b.shift_modificator);
        s.setValue("Inverted", b.is_inverted);
        s.setValue("Disabled", b.is_disabled);
        s.setValue("DelayTimer", b.delay_timer);
        s.setValue("PressTimer", b.press_timer);
        s.endGroup();
    }

    for (int i = 0; i < HSR_MAX_AXES; ++i) {
        const axis_config_t &a = devC.axis_config[i];
        s.beginGroup("AxesConfig_" + QString::number(i));
        s.setValue("CalibMin", a.calib_min);
        s.setValue("CalibCenter", a.calib_center);
        s.setValue("CalibMax", a.calib_max);
        s.setValue("IsCentered", a.is_centered);
        s.setValue("OutEnabled", a.out_enabled);
        s.setValue("Inverted", a.inverted);
        s.setValue("Function", a.function);
        s.setValue("Filter", a.filter);
        s.setValue("Resolution", a.resolution);
        s.setValue("Channel", a.channel);
        s.setValue("DeadbandSize", a.deadband_size);
        s.setValue("DynDeadbandEnabled", a.is_dynamic_deadband);
        s.setValue("SourceMain", a.source_main);
        s.setValue("SourceSecond", a.source_secondary);
        s.setValue("OffsetAngle", a.offset_angle);
        s.setValue("Button1", a.button1);
        s.setValue("Button2", a.button2);
        s.setValue("Button3", a.button3);
        s.setValue("Divider", a.divider);
        s.setValue("Button1Type", a.button1_type);
        s.setValue("Button2Type", a.button2_type);
        s.setValue("Button3Type", a.button3_type);
        s.setValue("Prescaler", a.prescaler);
        s.endGroup();

        s.beginGroup("AxesCurvesConfig_" + QString::number(i));
        for (int j = 0; j < 11; ++j) {
            s.setValue("Point_" + QString::number(j), a.curve_shape[j]);
        }
        s.endGroup();

        const axis_to_buttons_t &a2b = devC.axes_to_buttons[i];
        s.beginGroup("Axes2bConfig_" + QString::number(i));
        s.setValue("ButtonsCount", a2b.buttons_cnt);
        for (int j = 0; j < HSR_A2B_POINTS; ++j) {
            s.setValue("Point_" + QString::number(j), a2b.points[j]);
        }
        s.endGroup();
    }

    for (int i = 0; i < HSR_MAX_ENCODERS; ++i) {
        s.beginGroup("EncodersConfig_" + QString::number(i));
        s.setValue("EncType", devC.encoders[i]);
        s.endGroup();
    }

    s.beginGroup("LedsPWMConfig");
    for (int c = 0; c < HSR_MAX_PWM; ++c) {
        const led_pwm_config_t &p = devC.led_pwm_config[c];
        QString key = "Pin" + HsrBoard::spareLabel(HsrBoard::spareOfPwmChannel(c));
        s.setValue(key, p.duty_cycle);
        s.setValue(key + "_AxisEnabled", bool(p.is_axis));
        s.setValue(key + "_AxisNum", p.axis_num);
    }
    s.endGroup();

    s.beginGroup("LedsMonoConfig");
    for (uint i = 0; i < std::size(devC.led_timer_ms); ++i) {
        s.setValue("Timer_" + QString::number(i + 1), devC.led_timer_ms[i]);
    }
    s.endGroup();

    for (int i = 0; i < HSR_MAX_LEDS; ++i) {
        const led_config_t &l = devC.leds[i];
        s.beginGroup("LedsConfig_Pin" + HsrBoard::spareLabel(i));
        s.setValue("InputNum", l.input_num);
        s.setValue("LedType", l.type);
        s.setValue("Timer", l.timer);
        s.endGroup();
    }
    s.sync();
}
