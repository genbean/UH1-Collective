#ifndef AS5600HELPER_H
#define AS5600HELPER_H

#include <QElapsedTimer>
#include <QGroupBox>
#include "common_types.h"

QT_BEGIN_NAMESPACE
class QComboBox;
class QLabel;
class QProgressBar;
class QPushButton;
QT_END_NAMESPACE

// Guides the one-time programming of an AS5600 on AX1 (PROG1) or AX4 (PROG4):
// the chip's own OUT-pin programming (datasheet "Option B"), with the board's
// PROG button pulling OUT to GND. The helper can't press the button; it
// watches the live reading to see each press and to check the result.
class As5600Helper : public QGroupBox
{
    Q_OBJECT

public:
    explicit As5600Helper(QWidget *parent = nullptr);

    void updateReading(const params_report_t &params, bool connected);
    void retranslateUi();

signals:
    //! measured range of the programmed sensor, in raw readings (0-4092)
    void applyCalibration(int analogSource, int rawMin, int rawMax);

private:
    enum Step {
        Idle,
        CheckUnprogrammed,
        AtStart,
        HoldingStart,
        AtStop,
        HoldingStop,
        Verify,
        Done,
        Failed,
    };

    void setStep(Step step);
    void setStatus(const QString &text, const QString &color = QString());
    void updateStepLabels();
    int source() const;
    QString progName() const;

    Step m_step = Idle;
    QElapsedTimer m_stepTimer;      // time in the current step
    QElapsedTimer m_pressTimer;     // length of a PROG press
    int m_min = 0;
    int m_max = 0;
    bool m_sawLow = false;

    QLabel *m_intro;
    QComboBox *m_sensor;
    QProgressBar *m_bar;
    QPushButton *m_start;
    QLabel *m_steps[4];
    QLabel *m_status;
    QPushButton *m_apply;
};

#endif // AS5600HELPER_H
