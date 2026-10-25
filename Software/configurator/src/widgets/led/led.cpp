#include "led.h"
#include "ui_led.h"
#include "helisrboard.h"
#include <QEvent>
#include <QMouseEvent>
#include <QCursor>

LED::LED(int ledNumber, QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::LED)
    , m_ledCurrentState(false)
{
    ui->setupUi(this);
    m_ledNumber = ledNumber;
    ui->pushButton_LEDNumber->setText(HsrBoard::spareLabel(ledNumber));
    ui->pushButton_LEDNumber->setEnabled(false);
    ui->pushButton_LEDNumber->setCheckable(true);
    ui->pushButton_LEDNumber->setFlat(true);
    // no host-controlled LEDs on HeliSR
    ui->checkBox_HostControlled->hide();
    // 0 = no button
    ui->spinBox_InputNumber->setRange(0, HSR_MAX_BUTTONS);
    ui->spinBox_InputNumber->setSpecialValueText("-");

    for (uint i = 0; i < std::size(m_ledList); ++i) {
        ui->comboBox_Function->addItem(m_ledList[i].guiName);
    }

    for (uint i = 0; i < std::size(m_TimerList); ++i) {
        ui->comboBox_Timer->addItem(m_TimerList[i].guiName);
    }
}

LED::~LED()
{
    delete ui;
}

void LED::retranslateUi()
{
    ui->retranslateUi(this);
}

int LED::currentButtonSelected() const
{
    return ui->spinBox_InputNumber->value() - 1;
}

void LED::setLedState(bool state)
{
    if (state != m_ledCurrentState) {
        m_ledCurrentState = state;
        ui->pushButton_LEDNumber->setChecked(state);
    }
}

void LED::readFromConfig()
{
    led_config_t *led = &gEnv.pDeviceConfig->config.leds[m_ledNumber];
    ui->spinBox_InputNumber->setValue(led->input_num + 1);
    ui->comboBox_Function->setCurrentIndex(led->type);
    // timer 0-3, or 15 (FreeJoy's -1) for steady: the first list item
    ui->comboBox_Timer->setCurrentIndex(led->timer <= 3 ? led->timer + 1 : 0);
}

void LED::writeToConfig()
{
    led_config_t *led = &gEnv.pDeviceConfig->config.leds[m_ledNumber];
    led->input_num = int8_t(ui->spinBox_InputNumber->value() - 1);
    led->type = ui->comboBox_Function->currentIndex();
    int timer = ui->comboBox_Timer->currentIndex();
    led->timer = timer > 0 ? timer - 1 : 15;
}
