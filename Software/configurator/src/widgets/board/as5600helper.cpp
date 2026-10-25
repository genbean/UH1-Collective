#include "as5600helper.h"
#include <QComboBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QProgressBar>
#include <QPushButton>
#include <QVBoxLayout>

// Raw readings are 0-HSR_RAW_MAX. An unprogrammed AS5600 with PGO low holds OUT
// high; PROG pulls it to GND through 1 kΩ.
static const int LEVEL_HIGH = HSR_RAW_MAX * 9 / 10;
static const int LEVEL_LOW = HSR_RAW_MAX / 8;
static const int MIN_PRESS_MS = 100;        // the datasheet's minimum
static const int CHECK_MS = 1000;
static const int FAIL_MS = 2000;
static const int GOOD_RANGE = HSR_RAW_MAX / 3;

As5600Helper::As5600Helper(QWidget *parent)
    : QGroupBox(parent)
{
    QVBoxLayout *layout = new QVBoxLayout(this);
    m_intro = new QLabel(this);
    m_intro->setWordWrap(true);
    layout->addWidget(m_intro);

    QHBoxLayout *row = new QHBoxLayout;
    m_sensor = new QComboBox(this);
    m_sensor->addItem("AX1 (PROG1)", 0);
    m_sensor->addItem("AX4 (PROG4)", 3);
    row->addWidget(m_sensor);
    m_start = new QPushButton(this);
    row->addWidget(m_start);
    layout->addLayout(row);

    m_bar = new QProgressBar(this);
    m_bar->setRange(0, HSR_RAW_MAX);
    m_bar->setFormat("%v");
    layout->addWidget(m_bar);

    for (QLabel *&step : m_steps) {
        step = new QLabel(this);
        step->setWordWrap(true);
        layout->addWidget(step);
    }
    m_status = new QLabel(this);
    m_status->setWordWrap(true);
    m_status->setMinimumHeight(60);
    m_status->setAlignment(Qt::AlignLeft | Qt::AlignTop);
    layout->addWidget(m_status);

    m_apply = new QPushButton(this);
    m_apply->setEnabled(false);
    layout->addWidget(m_apply);
    layout->addStretch(1);

    connect(m_start, &QPushButton::clicked, this, [this] {
        setStep(m_step == Idle ? CheckUnprogrammed : Idle);
    });
    connect(m_sensor, qOverload<int>(&QComboBox::currentIndexChanged), this, [this] {
        setStep(Idle);
        updateStepLabels();
    });
    connect(m_apply, &QPushButton::clicked, this, [this] {
        emit applyCalibration(source(), m_min, m_max);
    });

    retranslateUi();
}

int As5600Helper::source() const
{
    return m_sensor->currentData().toInt();
}

QString As5600Helper::progName() const
{
    return source() == 0 ? QStringLiteral("PROG1") : QStringLiteral("PROG4");
}

void As5600Helper::retranslateUi()
{
    setTitle(tr("AS5600 programming helper"));
    m_intro->setText(tr("Burns an AS5600's start and stop angles once, through its OUT pin and the board's PROG button, "
                        "so the whole reading covers your travel. Prepare the module first (keep R4, remove R1, wire DIR): "
                        "see the board's README. It can only be done once per chip."));
    m_apply->setText(tr("Use the measured range as the calibration"));
    updateStepLabels();
    setStep(m_step);
}

void As5600Helper::updateStepLabels()
{
    const QString texts[4] = {
        tr("1. Connect the sensor. Unprogrammed, it reads near the top wherever it is."),
        tr("2. Move to the START position, then hold %1 for about a second and let go.").arg(progName()),
        tr("3. Move to the STOP position (more than 18° away, in the DIR direction), then hold %1 again.").arg(progName()),
        tr("4. Move through the whole range to check the result."),
    };
    int done = 0;
    switch (m_step) {
    case AtStart: case HoldingStart: done = 1; break;
    case AtStop: case HoldingStop: done = 2; break;
    case Verify: case Failed: done = 3; break;
    case Done: done = 4; break;
    default: break;
    }
    int current = (m_step == Idle || m_step == Done) ? -1 : qMin(done, 3);
    for (int i = 0; i < 4; ++i) {
        QString mark = i < done ? QStringLiteral("✔ ") : QString();
        m_steps[i]->setText(mark + texts[i]);
        QFont f = m_steps[i]->font();
        f.setBold(i == current);
        m_steps[i]->setFont(f);
    }
}

void As5600Helper::setStatus(const QString &text, const QString &color)
{
    // called on every reading while the result is shown: only touch what changed
    QString style = color.isEmpty() ? QString() : QStringLiteral("color: white; background-color: %1; padding: 4px;").arg(color);
    if (m_status->text() != text) {
        m_status->setText(text);
    }
    if (m_status->styleSheet() != style) {
        m_status->setStyleSheet(style);
    }
}

void As5600Helper::setStep(Step step)
{
    m_step = step;
    m_stepTimer.start();
    m_start->setText(step == Idle ? tr("Start") : tr("Stop"));
    m_sensor->setEnabled(step == Idle || step == Done || step == Failed);
    m_apply->setEnabled(step == Done);
    switch (step) {
    case Idle:
        setStatus(tr("Press Start when the sensor is connected and the device is plugged in."));
        break;
    case CheckUnprogrammed:
        setStatus(tr("Checking the reading..."));
        break;
    case AtStart:
        setStatus(tr("Waiting for %1 at the start position.").arg(progName()));
        break;
    case AtStop:
        setStatus(tr("Start angle stored. Waiting for %1 at the stop position.").arg(progName()));
        break;
    case Verify:
        m_min = HSR_RAW_MAX;
        m_max = 0;
        m_sawLow = false;
        setStatus(tr("Both angles sent. Now move the sensor through its range."));
        break;
    default:
        break;
    }
    updateStepLabels();
}

void As5600Helper::updateReading(const params_report_t &params, bool connected)
{
    if (connected == false) {
        m_bar->setEnabled(false);
        if (m_step != Idle && m_step != Done && m_step != Failed) {
            setStep(Idle);
            setStatus(tr("The device was disconnected. Start again once it's back."), "rgb(200, 128, 0)");
        }
        return;
    }
    m_bar->setEnabled(true);
    int v = params.analog_inputs[source()];
    m_bar->setValue(v);

    switch (m_step) {
    case CheckUnprogrammed:
        if (v < LEVEL_HIGH) {
            setStep(AtStart);
            setStatus(tr("The reading isn't held at the top (%1). The chip may be programmed already, PGO may not be low "
                         "(keep R4), or this isn't an AS5600. You can still go on: waiting for %2 at the start position.")
                          .arg(v).arg(progName()), "rgb(200, 128, 0)");
        } else if (m_stepTimer.elapsed() > CHECK_MS) {
            setStep(AtStart);
        }
        break;

    case AtStart:
    case AtStop:
        if (v < LEVEL_LOW) {
            m_pressTimer.start();
            setStep(m_step == AtStart ? HoldingStart : HoldingStop);
            setStatus(tr("%1 is held...").arg(progName()));
        }
        break;

    case HoldingStart:
    case HoldingStop:
        if (v > LEVEL_HIGH) {
            qint64 ms = m_pressTimer.elapsed();
            bool start = m_step == HoldingStart;
            if (ms < MIN_PRESS_MS) {
                setStep(start ? AtStart : AtStop);
                setStatus(tr("That press was too short (%1 ms): the chip needs at least %2 ms. Hold %3 again for about a second.")
                              .arg(ms).arg(MIN_PRESS_MS).arg(progName()), "rgb(200, 128, 0)");
            } else {
                setStep(start ? AtStop : Verify);
            }
        }
        break;

    case Verify:
    case Done:
        m_min = qMin(m_min, v);
        m_max = qMax(m_max, v);
        if (m_step == Verify) {
            if (m_max - m_min > GOOD_RANGE) {
                setStep(Done);
            } else if (m_max < LEVEL_LOW && m_stepTimer.elapsed() > FAIL_MS) {
                setStep(Failed);
                setStatus(tr("The reading stays at 0 wherever the sensor is: the chip reports that the burn failed "
                             "(or %1 is still held). A failed chip needs I²C programming or replacing.").arg(progName()),
                          "rgb(200, 0, 0)");
                break;
            }
        }
        if (m_step == Done) {
            setStatus(tr("Programmed: the reading follows the sensor. Seen so far: %1 to %2. Sweep the whole range, "
                         "then use it as the calibration (the Axes Config page shows it; write the config to keep it).")
                          .arg(m_min).arg(m_max), "rgb(0, 128, 0)");
        }
        break;

    default:
        break;
    }
}
