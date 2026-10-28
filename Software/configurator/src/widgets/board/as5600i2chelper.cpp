#include "as5600i2chelper.h"
#include <QComboBox>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QProgressBar>
#include <QPushButton>
#include <QVBoxLayout>
#include "deviceconfig.h"
#include "global.h"

static const char *const AX_CONNECTOR[HSR_AX_INPUTS] = {"J11", "J12", "J13", "J14"};
static const int CLOCKS_KHZ[] = {100, 50, 25, 10};

static const QString GREEN = QStringLiteral("rgb(0, 128, 0)");
static const QString ORANGE = QStringLiteral("rgb(200, 128, 0)");
static const QString RED = QStringLiteral("rgb(200, 0, 0)");

static QString degrees(int raw)
{
    return QString::number(raw * 360.0 / 4096, 'f', 1) + QStringLiteral("°");
}

// the shorter way from one raw angle to the next, through the wrap: -2048..2047
static int step(int from, int to)
{
    int d = (to - from) & 4095;
    return d >= 2048 ? d - 4096 : d;
}

As5600I2cHelper::As5600I2cHelper(QWidget *parent)
    : QGroupBox(parent)
{
    QVBoxLayout *layout = new QVBoxLayout(this);
    m_intro = new QLabel(this);
    m_intro->setWordWrap(true);
    layout->addWidget(m_intro);

    QHBoxLayout *clockRow = new QHBoxLayout;
    m_clockLabel = new QLabel(this);
    clockRow->addWidget(m_clockLabel);
    m_clock = new QComboBox(this);
    for (int khz : CLOCKS_KHZ) {
        m_clock->addItem(QStringLiteral("%1 kHz").arg(khz), khz);
    }
    clockRow->addWidget(m_clock);
    clockRow->addStretch(1);
    layout->addLayout(clockRow);
    m_clockNote = new QLabel(this);
    m_clockNote->setWordWrap(true);
    layout->addWidget(m_clockNote);

    m_port = new QComboBox(this);
    for (int i = 0; i < HSR_AX_INPUTS; ++i) {
        m_port->addItem(QStringLiteral("AX%1 (%2)").arg(i + 1).arg(AX_CONNECTOR[i]), i);
    }
    layout->addWidget(m_port);
    m_state = new QLabel(this);
    m_state->setWordWrap(true);
    layout->addWidget(m_state);

    QGridLayout *bars = new QGridLayout;
    m_rawLabel = new QLabel(this);
    m_raw = new QProgressBar(this);
    m_raw->setRange(0, 4095);
    m_raw->setFormat("%v");
    m_outLabel = new QLabel(this);
    m_out = new QProgressBar(this);
    m_out->setRange(0, 4095);
    m_out->setFormat("%v");
    bars->addWidget(m_rawLabel, 0, 0);
    bars->addWidget(m_raw, 0, 1);
    bars->addWidget(m_outLabel, 1, 0);
    bars->addWidget(m_out, 1, 1);
    bars->setColumnStretch(1, 1);
    layout->addLayout(bars);

    m_range = new QLabel(this);
    m_range->setWordWrap(true);
    layout->addWidget(m_range);

    QHBoxLayout *buttons = new QHBoxLayout;
    m_setStart = new QPushButton(this);
    m_setStop = new QPushButton(this);
    m_wholeCircle = new QPushButton(this);
    buttons->addWidget(m_setStart);
    buttons->addWidget(m_setStop);
    buttons->addWidget(m_wholeCircle);
    layout->addLayout(buttons);

    m_status = new QLabel(this);
    m_status->setWordWrap(true);
    m_status->setMinimumHeight(60);
    m_status->setAlignment(Qt::AlignLeft | Qt::AlignTop);
    layout->addWidget(m_status);

    m_apply = new QPushButton(this);
    layout->addWidget(m_apply);
    layout->addStretch(1);

    connect(m_port, qOverload<int>(&QComboBox::currentIndexChanged), this, [this] {
        cancelRange();
        showRange();
        sensorStatusReceived();
        updateControls();
    });
    // activated: only the user's choice, not the combo following the board
    connect(m_clock, qOverload<int>(&QComboBox::activated), this, [this] {
        hsr_sensor_config_t c = gEnv.pDeviceConfig->sensorConfig;
        int khz = m_clock->currentData().toInt();
        if (khz == c.i2c_khz) return;
        c.i2c_khz = uint8_t(khz);
        send(c, tr("The I²C clock is now %1 kHz.").arg(khz), GREEN);
    });

    connect(m_setStart, &QPushButton::clicked, this, [this] {
        const hsr_sensor_port_t &p = gEnv.pDeviceConfig->sensorStatus.port[port()];
        if (portReadable() == false) {
            setStatus(tr("AX%1 isn't being read (%2), so there's no angle to take.").arg(port() + 1).arg(stateText(p.state)), RED);
            return;
        }
        m_tracking = true;
        m_startRaw = m_lastRaw = p.raw_angle;
        m_travel = 0;
        setStatus(tr("Start taken at %1. Now move the control to its other end and click Set stop.").arg(degrees(m_startRaw)));
        updateControls();
    });

    connect(m_setStop, &QPushButton::clicked, this, [this] {
        const hsr_sensor_port_t &p = gEnv.pDeviceConfig->sensorStatus.port[port()];
        if (m_tracking == false) return;
        if (portReadable() == false) {
            setStatus(tr("AX%1 stopped being read (%2). Set the start again once it's back.").arg(port() + 1).arg(stateText(p.state)), RED);
            cancelRange();
            return;
        }
        int travel = m_travel + step(m_lastRaw, p.raw_angle);
        if (qAbs(travel) < HSR_AS5600_MIN_SPAN) {
            setStatus(tr("The control moved only %1 from the start. The AS5600 needs at least 18°: move further and click "
                         "Set stop again.").arg(degrees(qAbs(travel))), ORANGE);
            return;
        }
        if (qAbs(travel) > 4095) {
            setStatus(tr("The control went more than a whole turn from the start. Set the start again."), RED);
            cancelRange();
            return;
        }
        // the AS5600's range runs from ZPOS up to MPOS, the way its angle rises
        hsr_sensor_config_t c = gEnv.pDeviceConfig->sensorConfig;
        hsr_sensor_range_t &r = c.range[port()];
        QString done;
        QString color = GREEN;
        if (travel > 0) {
            r.zpos = uint16_t(m_startRaw);
            r.mpos = p.raw_angle;
            done = tr("Saved on the board: start %1, stop %2 (%3 of travel). The output now runs from 0 at the start "
                      "to 4095 at the stop.").arg(degrees(r.zpos)).arg(degrees(r.mpos)).arg(degrees(travel));
        } else {
            r.zpos = p.raw_angle;
            r.mpos = uint16_t(m_startRaw);
            done = tr("Saved on the board, the other way round: the angle falls from your start to your stop (the sensor's "
                      "DIR wiring), so the output runs from 4095 at your start to 0 at your stop (%1 of travel). Tick Inverted "
                      "on the axes using AX%2, or wire DIR to the other side and set the range again.")
                       .arg(degrees(-travel)).arg(port() + 1);
            color = ORANGE;
        }
        cancelRange();
        send(c, done, color);
    });

    connect(m_wholeCircle, &QPushButton::clicked, this, [this] {
        cancelRange();
        hsr_sensor_config_t c = gEnv.pDeviceConfig->sensorConfig;
        c.range[port()].zpos = 0;
        c.range[port()].mpos = 0;
        send(c, tr("AX%1 reads the whole circle again: 0 to 4095 over a full turn.").arg(port() + 1), GREEN);
    });

    connect(m_apply, &QPushButton::clicked, this, [this] {
        emit applyCalibration(port(), 0, HSR_RAW_MAX);
    });

    retranslateUi();
}

QString As5600I2cHelper::stateText(int state)
{
    switch (state) {
    case HSR_SENSOR_STARTING: return tr("not read yet");
    case HSR_SENSOR_OK: return tr("OK");
    case HSR_SENSOR_NO_MAGNET: return tr("no magnet");
    case HSR_SENSOR_MAGNET_WEAK: return tr("magnet too weak or too far");
    case HSR_SENSOR_MAGNET_STRONG: return tr("magnet too strong or too close");
    case HSR_SENSOR_NO_SENSOR: return tr("no sensor");
    case HSR_SENSOR_NO_SWITCH: return tr("the board's I²C switch doesn't answer");
    case HSR_SENSOR_BUS_ERROR: return tr("bus stuck: check this port's cable");
    default: return tr("state %1").arg(state);
    }
}

int As5600I2cHelper::port() const
{
    return qBound(0, m_port->currentData().toInt(), HSR_AX_INPUTS - 1);
}

// the raw angle means something: the sensor answers and sees its magnet
bool As5600I2cHelper::portReadable() const
{
    if (m_connected == false || m_haveStatus == false) return false;
    int s = gEnv.pDeviceConfig->sensorStatus.port[port()].state;
    return s == HSR_SENSOR_OK || s == HSR_SENSOR_MAGNET_WEAK || s == HSR_SENSOR_MAGNET_STRONG;
}

void As5600I2cHelper::retranslateUi()
{
    setTitle(tr("AS5600 sensors (I²C)"));
    m_intro->setText(tr("Sets the start and stop of the AS5600 on an AX port, so its whole output covers your travel: move the "
                        "control to one end and click Set start, then to the other end and click Set stop. The board keeps "
                        "them and writes them to the sensor every time it starts; nothing is burnt into the chip, so you can "
                        "set them again at any time. They belong to the board, not to a profile."));
    m_clockLabel->setText(tr("I²C clock:"));
    m_clockNote->setText(tr("100 kHz suits most cables. If a port with a long cable shows errors, try 50 or 25 kHz."));
    m_rawLabel->setText(tr("Raw angle"));
    m_outLabel->setText(tr("Output"));
    m_setStart->setText(tr("Set start"));
    m_setStop->setText(tr("Set stop"));
    m_wholeCircle->setText(tr("Whole circle"));
    m_apply->setText(tr("Use the sensor's whole output as the calibration"));
    if (m_status->text().isEmpty() || m_connected == false) {
        setStatus(m_connected ? QString() : tr("Connect a HeliSR Rev 4.0 board to set its sensors."));
    }
    showRange();
    sensorStatusReceived();
    updateControls();
}

void As5600I2cHelper::setStatus(const QString &text, const QString &color)
{
    m_status->setText(text);
    m_status->setStyleSheet(color.isEmpty() ? QString() : QStringLiteral("color: white; background-color: %1; padding: 4px;").arg(color));
}

void As5600I2cHelper::setDeviceConnected(bool connected)
{
    if (connected == m_connected) return;
    m_connected = connected;
    m_haveStatus = false;
    m_sending = false;
    if (connected == false) {
        m_haveConfig = false;
        if (m_tracking) {
            setStatus(tr("The device was disconnected. Set the start again once it's back."), ORANGE);
        } else {
            setStatus(tr("Connect a HeliSR Rev 4.0 board to set its sensors."));
        }
        cancelRange();
    } else {
        setStatus(QString());
    }
    showRange();
    sensorStatusReceived();
    updateControls();
}

void As5600I2cHelper::sensorConfigReceived(bool isSuccess)
{
    m_haveConfig = isSuccess;
    if (isSuccess == false) {
        setStatus(tr("The board didn't send its sensor settings."), RED);
    }
    const hsr_sensor_config_t &c = gEnv.pDeviceConfig->sensorConfig;
    int index = m_clock->findData(int(c.i2c_khz));
    if (index >= 0) {
        m_clock->setCurrentIndex(index);
    }
    showRange();
    updateControls();
}

void As5600I2cHelper::sensorConfigSent(bool isSuccess)
{
    m_sending = false;
    if (isSuccess) {
        setStatus(m_doneText, m_doneColor);
    } else {
        setStatus(tr("The board didn't save the settings: no answer, or it refused them."), RED);
    }
    sensorConfigReceived(true);     // the reply carried what the board holds now
}

void As5600I2cHelper::send(const hsr_sensor_config_t &config, const QString &doneText, const QString &doneColor)
{
    if (m_connected == false || m_haveConfig == false || m_sending) return;
    m_sending = true;
    m_doneText = doneText;
    m_doneColor = doneColor;
    setStatus(tr("Saving on the board..."));
    updateControls();
    emit writeSensorConfig(config);
}

void As5600I2cHelper::cancelRange()
{
    m_tracking = false;
    updateControls();
}

void As5600I2cHelper::updateControls()
{
    bool ready = m_connected && m_haveConfig && m_sending == false;
    m_clock->setEnabled(ready);
    m_port->setEnabled(m_tracking == false);
    m_setStart->setEnabled(ready);
    m_setStop->setEnabled(ready && m_tracking);
    m_wholeCircle->setEnabled(ready);
    m_apply->setEnabled(m_connected);
    m_raw->setEnabled(m_connected && m_haveStatus);
    m_out->setEnabled(m_connected && m_haveStatus);
}

void As5600I2cHelper::showRange()
{
    if (m_connected == false || m_haveConfig == false) {
        m_range->setText(QString());
        return;
    }
    const hsr_sensor_range_t &r = gEnv.pDeviceConfig->sensorConfig.range[port()];
    if (r.zpos == r.mpos) {
        m_range->setText(tr("Range: the whole circle (no start and stop set)."));
    } else {
        int span = (r.mpos - r.zpos) & 4095;
        m_range->setText(tr("Range: start %1, stop %2 (%3 of travel).").arg(degrees(r.zpos)).arg(degrees(r.mpos)).arg(degrees(span)));
    }
}

void As5600I2cHelper::sensorStatusReceived()
{
    if (m_connected == false) {
        m_state->setText(QString());
        m_rawLabel->setText(tr("Raw angle"));
        return;
    }
    m_haveStatus = true;
    const hsr_sensor_status_t &s = gEnv.pDeviceConfig->sensorStatus;
    const hsr_sensor_port_t &p = s.port[port()];
    QString text = tr("State: %1").arg(stateText(p.state));
    if (portReadable()) {
        text += tr(", AGC %1").arg(p.agc);
        text += (p.flags & HSR_SENSOR_RANGE_OK) ? tr(", range set on the sensor") : tr(", range not set on the sensor yet");
    }
    if (p.errors) {
        text += tr(", %1 failed transfer(s) since start-up").arg(p.errors);
    }
    if (s.bus_resets) {
        text += tr(". Bus reset %1 time(s)").arg(s.bus_resets);
    }
    if (m_state->text() != text) {
        m_state->setText(text);
    }
    m_raw->setValue(p.raw_angle);
    m_out->setValue(p.angle);
    m_rawLabel->setText(tr("Raw angle") + " " + degrees(p.raw_angle));

    if (m_tracking && portReadable()) {
        m_travel += step(m_lastRaw, p.raw_angle);
        m_lastRaw = p.raw_angle;
        setStatus(tr("Start taken at %1; moved %2%3 since. Click Set stop at the other end.")
                      .arg(degrees(m_startRaw)).arg(m_travel < 0 ? "-" : "+").arg(degrees(qAbs(m_travel))));
    }
    updateControls();
}
