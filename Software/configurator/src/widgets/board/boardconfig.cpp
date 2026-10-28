#include "boardconfig.h"
#include <QComboBox>
#include <QGridLayout>
#include <QGroupBox>
#include <QLabel>
#include <QProgressBar>
#include <QVBoxLayout>
#include "as5600helper.h"
#include "as5600i2chelper.h"
#include "deviceconfig.h"
#include "global.h"
#include "helisrboard.h"

static const char *const AX_CONNECTOR[HSR_AX_INPUTS] = {"J11", "J12", "J13", "J14"};
static const int A2A3_SOURCE[2] = {HSR_SOURCE_A2, HSR_SOURCE_A3};

BoardConfig::BoardConfig(QWidget *parent)
    : QWidget(parent)
{
    QHBoxLayout *columns = new QHBoxLayout(this);

    // left: the board's own inputs, and the summary
    QVBoxLayout *left = new QVBoxLayout;
    m_boardGroup = new QGroupBox(this);
    QGridLayout *boardGrid = new QGridLayout(m_boardGroup);
    m_boardLabel = new QLabel(m_boardGroup);
    boardGrid->addWidget(m_boardLabel, 0, 0);
    m_boardCombo = new QComboBox(m_boardGroup);
    m_boardCombo->addItem(HsrBoard::boardName(HSR_BOARD_REV30), HSR_BOARD_REV30);
    m_boardCombo->addItem(HsrBoard::boardName(HSR_BOARD_REV40), HSR_BOARD_REV40);
    boardGrid->addWidget(m_boardCombo, 0, 1, 1, 2);
    m_inText = new QLabel(m_boardGroup);
    m_inText->setWordWrap(true);
    boardGrid->addWidget(m_inText, 1, 0, 1, 3);
    m_axText = new QLabel(m_boardGroup);
    m_axText->setWordWrap(true);
    boardGrid->addWidget(m_axText, 2, 0, 1, 3);
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_axNames[i] = new QLabel(m_boardGroup);
        m_axBars[i] = new QProgressBar(m_boardGroup);
        m_axBars[i]->setRange(0, HSR_RAW_MAX);
        m_axBars[i]->setValue(0);
        m_axBars[i]->setFormat("%v");
        m_axState[i] = new QLabel(m_boardGroup);
        boardGrid->addWidget(m_axNames[i], 3 + i, 0);
        boardGrid->addWidget(m_axBars[i], 3 + i, 1);
        boardGrid->addWidget(m_axState[i], 3 + i, 2);
    }
    m_a2a3Text = new QLabel(m_boardGroup);
    m_a2a3Text->setWordWrap(true);
    boardGrid->addWidget(m_a2a3Text, 7, 0, 1, 3);
    for (int i = 0; i < 2; ++i) {
        m_a2a3Names[i] = new QLabel(m_boardGroup);
        m_a2a3Bars[i] = new QProgressBar(m_boardGroup);
        m_a2a3Bars[i]->setRange(0, HSR_RAW_MAX);
        m_a2a3Bars[i]->setValue(0);
        m_a2a3Bars[i]->setFormat("%v");
        boardGrid->addWidget(m_a2a3Names[i], 8 + i, 0);
        boardGrid->addWidget(m_a2a3Bars[i], 8 + i, 1);
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

    // right: the AS5600 helper for the board (PROG buttons on Rev 3.0, I2C on Rev 4.0)
    m_as5600 = new As5600Helper(this);
    connect(m_as5600, &As5600Helper::applyCalibration, this, &BoardConfig::applyCalibration);
    columns->addWidget(m_as5600, 4);
    m_as5600i2c = new As5600I2cHelper(this);
    connect(m_as5600i2c, &As5600I2cHelper::applyCalibration, this, &BoardConfig::applyCalibration);
    connect(m_as5600i2c, &As5600I2cHelper::writeSensorConfig, this, &BoardConfig::writeSensorConfig);
    columns->addWidget(m_as5600i2c, 4);

    // the user's choice; a connected device's board is set through setBoard()
    connect(m_boardCombo, qOverload<int>(&QComboBox::activated), this, [this] {
        int id = m_boardCombo->currentData().toInt();
        if (id != HsrBoard::board()) {
            HsrBoard::setBoard(id);
            applyBoard();
        }
    });

    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        fillPinCombo(i);
    }
    m_bulkUpdate = true;
    applyBoard();
    m_bulkUpdate = false;
}

void BoardConfig::setBoard(int boardId)
{
    if (HsrBoard::knownBoard(boardId) == false || boardId == HsrBoard::board()) {
        return;
    }
    HsrBoard::setBoard(boardId);
    applyBoard();
}

// The board shown changed: its texts, its spare pins, its helper.
void BoardConfig::applyBoard()
{
    bool rev40 = HsrBoard::isRev40();
    m_boardCombo->setCurrentIndex(m_boardCombo->findData(HsrBoard::board()));
    bool bulk = m_bulkUpdate;
    m_bulkUpdate = true;
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        bool exists = HsrBoard::spareExists(i);
        m_spareNames[i]->setVisible(exists);
        m_spareCombos[i]->setVisible(exists);
        m_spareInfo[i]->setVisible(exists);
        if (exists == false) {
            // Rev 4.0's pin 14 reads the shift registers: whatever a profile said, it's not used
            m_spareCombos[i]->setCurrentIndex(0);
            m_spareBars[i]->setVisible(false);
        }
    }
    m_bulkUpdate = bulk;
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_axState[i]->setVisible(rev40);
        m_axState[i]->clear();
    }
    m_a2a3Text->setVisible(rev40);
    for (int i = 0; i < 2; ++i) {
        m_a2a3Names[i]->setVisible(rev40);
        m_a2a3Bars[i]->setVisible(rev40);
    }
    m_as5600->setVisible(rev40 == false);
    m_as5600i2c->setVisible(rev40);
    setDeviceConnected(m_connected);
    setTexts();
    updateSummary();
    emit boardChanged(HsrBoard::board());
    if (m_bulkUpdate == false) {
        emit pinsChanged();
    }
}

void BoardConfig::setTexts()
{
    bool rev40 = HsrBoard::isRev40();
    m_boardLabel->setText(tr("Board:"));
    m_boardCombo->setToolTip(tr("The board the pages show. It follows the connected device."));
    if (rev40) {
        m_boardGroup->setTitle(tr("HeliSR Rev 4.0 board"));
    } else {
        m_boardGroup->setTitle(tr("HeliSR Rev 3.0 board"));
    }
    m_inText->setText(tr("<b>IN1–IN16</b> (J1, J2): 16 buttons. Wire each switch between its input and GND. "
                         "They are physical inputs 1–16 on the Button Config page."));
    if (rev40) {
        m_axText->setText(tr("<b>AX1–AX4</b> (J11–J14): I²C ports for AS5600 sensors, each on its own channel of the board's "
                             "I²C switch. Choose them as axis sources on the Axes Config page, and set each sensor's start "
                             "and stop with the helper on the right. Live readings (0–%1):").arg(HSR_RAW_MAX));
        m_a2a3Text->setText(tr("<b>A2, A3</b>: Pro Micro pins with no connector (solder a wire to use one): analog axis "
                               "sources for pots or Hall sensors. An axis that uses one turns it on. Live readings:"));
        m_a2a3Names[0]->setText(tr("Pin %1").arg("A2"));
        m_a2a3Names[1]->setText(tr("Pin %1").arg("A3"));
    } else {
        m_axText->setText(tr("<b>AX1–AX4</b> (J11–J14): analog inputs for pots, Hall sensors or AS5600 sensors. "
                             "Choose them as axis sources on the Axes Config page. Live readings (0–%1):").arg(HSR_RAW_MAX));
    }
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        QString name = QStringLiteral("AX%1 (%2)").arg(i + 1).arg(AX_CONNECTOR[i]);
        if (rev40 == false && i == 0) name += ", PROG1";
        if (rev40 == false && i == 3) name += ", PROG4";
        m_axNames[i]->setText(name);
    }

    m_spareGroup->setTitle(tr("Spare Pro Micro pins"));
    if (rev40) {
        m_spareText->setText(tr("These pins aren't broken out on the board: solder a wire to the Pro Micro's pin to use one. "
                                "Buttons to GND use the pin's internal pull-up; buttons to VCC need a 10 kΩ pull-down. "
                                "Only pins 4, 6, 8, 9 and 10 read analog (and A2 and A3, on the left), and only 5, 6, 9 "
                                "and 10 do PWM. Pin 14 reads the shift registers on this board."));
    } else {
        m_spareText->setText(tr("These pins aren't broken out on the board: solder a wire to the Pro Micro's pin to use one. "
                                "Buttons to GND use the pin's internal pull-up; buttons to VCC need a 10 kΩ pull-down. "
                                "Only pins 4, 6, 8, 9 and 10 read analog, and only 5, 6, 9 and 10 do PWM."));
    }
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        m_spareNames[i]->setText(HsrBoard::spareName(i));
        int current = m_spareCombos[i]->currentIndex();
        if (current >= 0) {
            fillPinCombo(i);
        }
    }
    m_summaryGroup->setTitle(tr("Summary"));
    m_as5600->retranslateUi();
    m_as5600i2c->retranslateUi();
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
    QString sources = HsrBoard::isRev40() ? tr("Axis sources: AX1–AX4 (AS5600), A2, A3 + %1 spare pin(s)").arg(spareAxes)
                                          : tr("Axis sources: AX1–AX4 + %1 spare pin(s)").arg(spareAxes);
    m_summary->setText(tr("Physical inputs: 16 (IN1–IN16) + %1 spare pin(s) + %2 axis range(s)").arg(spareButtons).arg(ranges)
                       + "<br>" + rangesText
                       + "<br>" + sources
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
            m_spareBars[i]->setValue(hsr_params_analog(&p, uint8_t(source)));
        }
    }
    if (HsrBoard::isRev40()) {
        for (int i = 0; i < 2; ++i) {
            m_a2a3Bars[i]->setValue(hsr_params_analog(&p, uint8_t(A2A3_SOURCE[i])));
        }
    } else {
        // the PROG helper watches for presses even while its page is hidden
        m_as5600->updateReading(p, m_connected);
    }
}

void BoardConfig::setDeviceConnected(bool connected)
{
    m_connected = connected;
    m_boardCombo->setEnabled(connected == false);      // a connected device decides
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_axBars[i]->setEnabled(connected);
        if (connected == false) {
            m_axState[i]->clear();
        }
    }
    for (int i = 0; i < 2; ++i) {
        m_a2a3Bars[i]->setEnabled(connected);
    }
    if (connected == false && HsrBoard::isRev40() == false) {
        m_as5600->updateReading(gEnv.pDeviceConfig->paramsReport, false);
    }
    m_as5600i2c->setDeviceConnected(connected && HsrBoard::isRev40()
                                    && gEnv.pDeviceConfig->info.board_id == HSR_BOARD_REV40);
}

void BoardConfig::sensorConfigReceived(bool isSuccess)
{
    m_as5600i2c->sensorConfigReceived(isSuccess);
}

void BoardConfig::sensorStatusReceived()
{
    if (HsrBoard::isRev40() == false) {
        return;
    }
    const hsr_sensor_status_t &s = gEnv.pDeviceConfig->sensorStatus;
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        QString text = As5600I2cHelper::stateText(s.port[i].state);
        if (m_axState[i]->text() != text) {
            m_axState[i]->setText(text);
        }
    }
    m_as5600i2c->sensorStatusReceived();
}

void BoardConfig::sensorConfigSent(bool isSuccess)
{
    m_as5600i2c->sensorConfigSent(isSuccess);
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
        // a pin the board doesn't have (Rev 4.0's pin 14) reads as not used
        m_pins[i] = HsrBoard::spareExists(i) ? gEnv.pDeviceConfig->config.pins[i] : pin_func_t(PIN_NOT_USED);
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
