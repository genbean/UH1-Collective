#ifndef AXESCONFIG_H
#define AXESCONFIG_H

#include "axes.h"
#include <QWidget>

#include "deviceconfig.h"
#include "global.h"

namespace Ui {
class AxesConfig;
}

class QCheckBox;

class AxesConfig : public QWidget
{
    Q_OBJECT

public:
    explicit AxesConfig(QWidget *parent = nullptr);
    ~AxesConfig();

    void readFromConfig();
    void writeToConfig();

    void retranslateUi();

    void axesValueChanged();

    //! axis-to-button ranges per axis, as set on the page
    QVector<int> a2bCounts() const;
    //! number of axes that took the calibration
    int applyCalibration(int analogSource, int rawMin, int rawMax);

signals:
    void axisRawValueChanged(int);
    void axisOutValueChanged(int);
    void a2bCountChanged(int count);

public slots:
    void setAvailableSources(const pin_func_t *pins);
private slots:
    void a2bCountCalc(int count, int previousCount);
    void hideAxis(int index, bool hide);
    //    void axesValueChanged(int value);

private:
    Ui::AxesConfig *ui;
    int m_a2bButtonsCount;

    QList<Axes *> m_axesPtrList;
    QList<QCheckBox *> m_hideChBoxes;
};

#endif // AXESCONFIG_H
