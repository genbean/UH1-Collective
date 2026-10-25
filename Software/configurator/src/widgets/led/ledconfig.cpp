#include "ledconfig.h"
#include "ui_ledconfig.h"

#include "led.h"
#include "common_types.h"
#include "deviceconfig.h"
#include "global.h"
#include "helisrboard.h"

#include <QDebug>
LedConfig::LedConfig(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::LedConfig)
{
    ui->setupUi(this);
    ui->layoutV_LED->setAlignment(Qt::AlignTop);
    // no host-controlled LEDs on HeliSR
    ui->text_source->hide();

    // one LED row per spare pin, shown when the pin is set to "LED"
    for (int i = 0; i < MAX_LEDS_NUM; i++) {
        LED *led = new LED(i, this);
        ui->layoutV_LED->addWidget(led);
        m_ledPtrList.append(led);
        led->hide();
    }
    for (int i = 0; i < MAX_AXIS_NUM; ++i) {
        ui->comboBox_axisCon5->addItem(HsrBoard::axisName(i));
        ui->comboBox_axisCon6->addItem(HsrBoard::axisName(i));
        ui->comboBox_axisCon9->addItem(HsrBoard::axisName(i));
        ui->comboBox_axisCon10->addItem(HsrBoard::axisName(i));
    }

    // PWM channels 0-3 are pins 5, 6, 9, 10
    m_pwmFrames[0] = ui->frame_Pwm5;
    m_pwmFrames[1] = ui->frame_Pwm6;
    m_pwmFrames[2] = ui->frame_Pwm9;
    m_pwmFrames[3] = ui->frame_Pwm10;
    for (QFrame *f : m_pwmFrames) {
        f->setEnabled(false);
    }
    setEnabledTimers(false);
}

LedConfig::~LedConfig()
{
    delete ui;
}

void LedConfig::retranslateUi()
{
    ui->retranslateUi(this);
    for (int i = 0; i < m_ledPtrList.size(); ++i) {
        m_ledPtrList[i]->retranslateUi();
    }
}

void LedConfig::setPins(const pin_func_t *pins)
{
    bool anyLed = false;
    for (int i = 0; i < MAX_LEDS_NUM; i++) {
        bool led = pins[i] == PIN_LED_SINGLE;
        m_ledPtrList[i]->setVisible(led);
        anyLed |= led;
    }
    setEnabledTimers(anyLed);
    for (int c = 0; c < HSR_MAX_PWM; ++c) {
        m_pwmFrames[c]->setEnabled(pins[HsrBoard::spareOfPwmChannel(c)] == PIN_LED_PWM);
    }
}

void LedConfig::setLedsState()
{
    const params_report_t &p = gEnv.pDeviceConfig->paramsReport;
    for (int i = 0; i < m_ledPtrList.size(); ++i)
    {
        if (m_ledPtrList[i]->isHidden()) {
            continue;
        }
        // shows the logical button the LED follows
        int button = m_ledPtrList[i]->currentButtonSelected();
        if (button >= 0 && button < HSR_MAX_BUTTONS) {
            m_ledPtrList[i]->setLedState(p.log_button_data[button / 8] & (1 << (button % 8)));
        }
    }
}

void LedConfig::setEnabledTimers(bool enabled)
{
    for (int i = 0; i < ui->layoutH_Timers->count(); ++i) {
        QWidget *w = ui->layoutH_Timers->itemAt(i)->widget();
        if (w) {
            w->setEnabled(enabled);
        }
    }
}

void LedConfig::readFromConfig()
{
    dev_config_t *devc = &gEnv.pDeviceConfig->config;
    // PWM channels
    led_pwm_config_t *pwm = devc->led_pwm_config;
    ui->spinBox_Pwm5->setValue(pwm[0].duty_cycle);
    ui->spinBox_Pwm6->setValue(pwm[1].duty_cycle);
    ui->spinBox_Pwm9->setValue(pwm[2].duty_cycle);
    ui->spinBox_Pwm10->setValue(pwm[3].duty_cycle);

    ui->checkBox_connected5->setChecked(pwm[0].is_axis);
    ui->checkBox_connected6->setChecked(pwm[1].is_axis);
    ui->checkBox_connected9->setChecked(pwm[2].is_axis);
    ui->checkBox_connected10->setChecked(pwm[3].is_axis);

    ui->comboBox_axisCon5->setCurrentIndex(pwm[0].axis_num);
    ui->comboBox_axisCon6->setCurrentIndex(pwm[1].axis_num);
    ui->comboBox_axisCon9->setCurrentIndex(pwm[2].axis_num);
    ui->comboBox_axisCon10->setCurrentIndex(pwm[3].axis_num);

    // on/off LEDs
    ui->spinBox_Timer1->setValue(devc->led_timer_ms[0]);
    ui->spinBox_Timer2->setValue(devc->led_timer_ms[1]);
    ui->spinBox_Timer3->setValue(devc->led_timer_ms[2]);
    ui->spinBox_Timer4->setValue(devc->led_timer_ms[3]);

    for (int i = 0; i < MAX_LEDS_NUM; ++i) {
        m_ledPtrList[i]->readFromConfig();
    }
}

void LedConfig::writeToConfig()
{
    dev_config_t *devc = &gEnv.pDeviceConfig->config;
    // PWM channels
    led_pwm_config_t *pwm = devc->led_pwm_config;
    pwm[0].duty_cycle = ui->spinBox_Pwm5->value();
    pwm[1].duty_cycle = ui->spinBox_Pwm6->value();
    pwm[2].duty_cycle = ui->spinBox_Pwm9->value();
    pwm[3].duty_cycle = ui->spinBox_Pwm10->value();

    pwm[0].is_axis = ui->checkBox_connected5->isChecked();
    pwm[1].is_axis = ui->checkBox_connected6->isChecked();
    pwm[2].is_axis = ui->checkBox_connected9->isChecked();
    pwm[3].is_axis = ui->checkBox_connected10->isChecked();

    pwm[0].axis_num = ui->comboBox_axisCon5->currentIndex();
    pwm[1].axis_num = ui->comboBox_axisCon6->currentIndex();
    pwm[2].axis_num = ui->comboBox_axisCon9->currentIndex();
    pwm[3].axis_num = ui->comboBox_axisCon10->currentIndex();

    // on/off LEDs
    devc->led_timer_ms[0] = ui->spinBox_Timer1->value();
    devc->led_timer_ms[1] = ui->spinBox_Timer2->value();
    devc->led_timer_ms[2] = ui->spinBox_Timer3->value();
    devc->led_timer_ms[3] = ui->spinBox_Timer4->value();

    for (int i = 0; i < MAX_LEDS_NUM; ++i) {
        m_ledPtrList[i]->writeToConfig();
    }
}
