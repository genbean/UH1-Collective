#ifndef AXES_H
#define AXES_H

#include <QWidget>
#include "axesextended.h"
#include "axestobuttonsslider.h"

#include "deviceconfig.h"
#include "global.h"

const QVector <deviceEnum_guiName_t> &axesList();

namespace Ui {
class Axes;
}

class Axes : public QWidget
{
    Q_OBJECT

public:
    explicit Axes(int axisNumber, QWidget *parent = nullptr);
    ~Axes();

    void readFromConfig();
    void writeToConfig();

    void retranslateUi();

    void updateAxisRaw();
    void updateAxisOut();

    //! offer the analog sources these spare pin settings provide
    void setAvailableSources(const pin_func_t *pins);
    //! axis-to-button ranges set on this axis
    int a2bCount() const;
    //! set the calibration from raw readings if this axis uses that analog source
    bool applyCalibration(int analogSource, int rawMin, int rawMax);

signals:
    void a2bCountChanged(int count, int previousCount);

private slots:
    void calibMinMaxValueChanged(int value);
    void calibrationStarted(int rawValue);

    void a2bSpinBoxChanged(int count);

    void outputValueChanged(bool isChecked);

    void on_pushButton_StartCalib_clicked(bool checked);
    void on_pushButton_SetCenter_clicked();
    void on_checkBox_Center_stateChanged(int state);

    void on_pushButton_ResetCalib_clicked();

    void on_checkBox_ShowExtend_stateChanged(int state);

private:
    Ui::Axes *ui;
    const int m_kMinA2bButtons = 1;//2
    bool m_calibrationStarted;
    bool m_outputEnabled;
    int m_a2bButtonsCount;
    int m_lastA2bCount;
    int m_axisNumber;
    const QString m_kStartCalStr = tr("Calibrate");
    const QString m_kStopCalStr = tr("Stop && Save");
    AxesExtended *m_axesExtend;

    QVector<int> m_mainSource_enumIndex;

};

#endif // AXES_H
