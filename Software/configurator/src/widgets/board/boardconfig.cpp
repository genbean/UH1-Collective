#include "boardconfig.h"
#include <QComboBox>
#include <QGridLayout>
#include <QGroupBox>
#include <QLabel>
#include <QProgressBar>
#include <QVBoxLayout>
#include "as5600helper.h"
#include "deviceconfig.h"
#include "global.h"
#include "helisrboard.h"

static const char *const AX_CONNECTOR[HSR_AX_INPUTS] = {"J11", "J12", "J13", "J14"};

BoardConfig::BoardConfig(QWidget *parent)
    : QWidget(parent)
{
    QHBoxLayout *columns = new QHBoxLayout(this);

    // left: the board's own inputs, and the summary
    QVBoxLayout *left = new QVBoxLayout;
    m_boardGroup = new QGroupBox(this);
    QGridLayout *boardGrid = new QGridLayout(m_boardGroup);
    m_inText = new QLabel(m_boardGroup);
    m_inText->setWordWrap(true);
    boardGrid->addWidget(m_inText, 0, 0, 1, 2);
    m_axText = new QLabel(m_boardGroup);
    m_axText->setWordWrap(true);
    boardGrid->addWidget(m_axText, 1, 0, 1, 2);
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_axNames[i] = new QLabel(m_boardGroup);
        m_axBars[i] = new QProgressBar(m_boardGroup);
        m_axBars[i]->setRange(0, HSR_RAW_MAX);
        m_axBars[i]->setValue(0);
        m_axBars[i]->setFormat("%v");
        boardGrid->addWidget(m_axNames[i], 2 + i, 0);
        boardGrid->addWidget(m_axBars[i], 2 + i, 1);
    }
    boardGrid->setColumnStretch(1, 1);
    left->addWidget(m_boardGroup);

    m_summaryGroup = new QGroupBox(this);
    QVBoxLayout *summaryLayout = new QVBoxLayout(m_summaryGroup);
    m_summary = new QLabel(m_summaryGroup);
    m_summary->setWordWrap(true);
    m_summary->setTextFormat(Qt::RichText);
    summaryLayout->addWidget(m_summary);
    left->addWidget(m_summaryGroup);
    left->addStretch(1);
    columns->addLayout(left, 4);

    // middle: the spare pins
    m_spareGroup = new QGroupBox(this);
    QGridLayout *spareGrid = new QGridLayout(m_spareGroup);
    m_spareText = new QLabel(m_spareGroup);
    m_spareText->setWordWrap(true);
    spareGrid->addWidget(m_spareText, 0, 0, 1, 4);
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        m_spareNames[i] = new QLabel(m_spareGroup);
        m_spareCombos[i] = new QComboBox(m_spareGroup);
        m_spareInfo[i] = new QLabel(m_spareGroup);
        m_spareBars[i] = new QProgressBar(m_spareGroup);
        m_spareBars[i]->setRange(0, HSR_RAW_MAX);
        m_spareBars[i]->setFormat("%v");
        m_spareBars[i]->setVisible(false);
        spareGrid->addWidget(m_spareNames[i], 1 + i, 0);
        spareGrid->addWidget(m_spareCombos[i], 1 + i, 1);
        spareGrid->addWidget(m_spareInfo[i], 1 + i, 2);
        spareGrid->addWidget(m_spareBars[i], 1 + i, 3);
        connect(m_spareCombos[i], qOverload<int>(&QComboBox::currentIndexChanged), this, [this, i] {
            pinComboChanged(i);
        });
    }
    spareGrid->setColumnStretch(3, 1);
    spareGrid->setRowStretch(1 + HSR_SPARE_PINS, 1);
    columns->addWidget(m_spareGroup, 5);

    // right: the AS5600 programming helper
    m_as5600 = new As5600Helper(this);
    connect(m_as5600, &As5600Helper::applyCalibration, this, &BoardConfig::applyCalibration);
    columns->addWidget(m_as5600, 4);

    setTexts();
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        fillPinCombo(i);
    }
    updateSummary();
}

void BoardConfig::setTexts()
{
    m_boardGroup->setTitle(tr("HeliSR Rev 3.0 board"));
    m_inText->setText(tr("<b>IN1–IN16</b> (J1, J2): 16 buttons. Wire each switch between its input and GND. "
                         "They are physical inputs 1–16 on the Button Config page."));
    m_axText->setText(tr("<b>AX1–AX4</b> (J11–J14): analog inputs for pots, Hall sensors or AS5600 sensors. "
                         "Choose them as axis sources on the Axes Config page. Live readings (0–%1):").arg(HSR_RAW_MAX));
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        QString name = QStringLiteral("AX%1 (%2)").arg(i + 1).arg(AX_CONNECTOR[i]);
        if (i == 0) name += ", PROG1";
        if (i == 3) name += ", PROG4";
        m_axNames[i]->setText(name);
    }

    m_spareGroup->setTitle(tr("Spare Pro Micro pins"));
    m_spareText->setText(tr("These pins aren't broken out on the board: solder a wire to the Pro Micro's pin to use one. "
                            "Buttons to GND use the pin's internal pull-up; buttons to VCC need a 10 kΩ pull-down. "
                            "Only pins 4, 6, 8, 9 and 10 read analog, and only 5, 6, 9 and 10 do PWM."));
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        m_spareNames[i]->setText(HsrBoard::spareName(i));
        int current = m_spareCombos[i]->currentIndex();
        if (current >= 0) {
            fillPinCombo(i);
        }
    }
    m_summaryGroup->setTitle(tr("Summary"));
    m_as5600->retranslateUi();
}

void BoardConfig::retranslateUi()
{
    setTexts();
    updateSummary();
}

void BoardConfig::fillPinCombo(int i)
{
    QComboBox *cb = m_spareCombos[i];
    QSignalBlocker blocker(cb);
    cb->clear();
    cb->addItem(tr("Not used"), PIN_NOT_USED);
    cb->addItem(tr("Button to GND"), PIN_BUTTON_GND);
    cb->addItem(tr("Button to VCC"), PIN_BUTTON_VCC);
    if (HsrBoard::spareIsAnalog(i)) {
        cb->addItem(tr("Axis analog"), PIN_AXIS_ANALOG);
    }
    cb->addItem(tr("LED"), PIN_LED_SINGLE);
    if (HsrBoard::spareIsPwm(i)) {
        cb->addItem(tr("LED PWM"), PIN_LED_PWM);
    }
    int index = cb->findData(m_pins[i]);
    cb->setCurrentIndex(index < 0 ? 0 : index);
}

void BoardConfig::pinComboChanged(int i)
{
    pin_func_t func = pin_func_t(m_spareCombos[i]->currentData().toInt());
    m_pins[i] = func;

    QString info;
    switch (func) {
    case PIN_BUTTON_GND:
    case PIN_BUTTON_VCC:
        info = tr("physical input %1").arg(HSR_PHYS_SPARE_FIRST + i + 1);
        break;
    case PIN_AXIS_ANALOG:
        info = tr("axis source");
        break;
    case PIN_LED_SINGLE:
        info = tr("LED page");
        break;
    case PIN_LED_PWM:
        info = tr("PWM channel %1").arg(HsrBoard::pwmChannelOfSpare(i) + 1);
        break;
    default:
        break;
    }
    m_spareInfo[i]->setText(info);
    m_spareBars[i]->setVisible(func == PIN_AXIS_ANALOG);

    updateSummary();
    if (m_bulkUpdate == false) {
        emit pinsChanged();
    }
}

const pin_func_t *BoardConfig::pins() const
{
    return m_pins;
}

bool BoardConfig::limitIsReached() const
{
    return m_limit;
}

void BoardConfig::setA2bCounts(const QVector<int> &counts)
{
    m_a2bCounts = counts;
    updateSummary();
}

void BoardConfig::updateSummary()
{
    int spareButtons = 0, spareAxes = 0, leds = 0, pwm = 0;
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        switch (m_pins[i]) {
        case PIN_BUTTON_GND:
        case PIN_BUTTON_VCC: spareButtons++; break;
        case PIN_AXIS_ANALOG: spareAxes++; break;
        case PIN_LED_SINGLE: leds++; break;
        case PIN_LED_PWM: pwm++; break;
        default: break;
        }
    }
    int ranges = 0;
    for (int c : m_a2bCounts) {
        ranges += c;
    }

    bool tooMany = ranges > HSR_MAX_A2B_BUTTONS;
    QString rangesText = tr("Axis ranges (axis-to-button): %1 of %2").arg(ranges).arg(HSR_MAX_A2B_BUTTONS);
    if (tooMany) {
        rangesText = "<span style=\"color: white; background-color: rgb(200, 0, 0);\">&nbsp;" + rangesText
                     + tr(": too many, the device can't be written") + "&nbsp;</span>";
    }
    m_summary->setText(tr("Physical inputs: 16 (IN1–IN16) + %1 spare pin(s) + %2 axis range(s)").arg(spareButtons).arg(ranges)
                       + "<br>" + rangesText
                       + "<br>" + tr("Axis sources: AX1–AX4 + %1 spare pin(s)").arg(spareAxes)
                       + "<br>" + tr("LEDs: %1 on/off, %2 PWM").arg(leds).arg(pwm)
                       + "<br>" + tr("Logical buttons: up to %1, in up to %2 hats; %3 encoders; %4 shift layers")
                                      .arg(HSR_MAX_BUTTONS).arg(HSR_MAX_POVS).arg(HSR_MAX_ENCODERS).arg(HSR_MAX_SHIFTS));

    if (tooMany != m_limit) {
        m_limit = tooMany;
        emit limitReached(m_limit);
    }
}

void BoardConfig::updateLiveData()
{
    const params_report_t &p = gEnv.pDeviceConfig->paramsReport;
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_axBars[i]->setValue(p.analog_inputs[i]);
    }
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        int source = HsrBoard::analogSourceOfSpare(i);
        if (source >= 0 && m_spareBars[i]->isVisible()) {
            m_spareBars[i]->setValue(p.analog_inputs[source]);
        }
    }
    m_as5600->updateReading(p, m_connected);
}

void BoardConfig::setDeviceConnected(bool connected)
{
    m_connected = connected;
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_axBars[i]->setEnabled(connected);
    }
    if (connected == false) {
        m_as5600->updateReading(gEnv.pDeviceConfig->paramsReport, false);
    }
}

void BoardConfig::resetAllPins()
{
    m_bulkUpdate = true;
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        m_spareCombos[i]->setCurrentIndex(0);
    }
    m_bulkUpdate = false;
    emit pinsChanged();
}

void BoardConfig::readFromConfig()
{
    // one pinsChanged() at the end, not one per pin
    m_bulkUpdate = true;
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        m_pins[i] = gEnv.pDeviceConfig->config.pins[i];
        int index = m_spareCombos[i]->findData(m_pins[i]);
        if (index < 0) {
            index = 0;
        }
        if (index == m_spareCombos[i]->currentIndex()) {
            pinComboChanged(i);
        } else {
            m_spareCombos[i]->setCurrentIndex(index);
        }
    }
    m_bulkUpdate = false;
    emit pinsChanged();
}

void BoardConfig::writeToConfig()
{
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        gEnv.pDeviceConfig->config.pins[i] = m_pins[i];
    }
}
