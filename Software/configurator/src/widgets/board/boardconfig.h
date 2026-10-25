#ifndef BOARDCONFIG_H
#define BOARDCONFIG_H

#include <QWidget>
#include <QVector>
#include "common_types.h"

QT_BEGIN_NAMESPACE
class QComboBox;
class QGroupBox;
class QLabel;
class QProgressBar;
QT_END_NAMESPACE

class As5600Helper;

// The "Board" page: what the HeliSR board's fixed inputs are, what each spare
// Pro Micro pin is used for, and a summary of what the setup adds up to.
// Replaces FreeJoy's Blue Pill pin page; the other pages follow the spare pin
// choices made here (through pinsChanged()).
class BoardConfig : public QWidget
{
    Q_OBJECT

public:
    explicit BoardConfig(QWidget *parent = nullptr);

    void readFromConfig();
    void writeToConfig();
    void retranslateUi();
    void resetAllPins();

    //! the spare pin functions chosen on this page (HSR_SPARE_PINS of them)
    const pin_func_t *pins() const;
    bool limitIsReached() const;

    //! live readings from the device's params report
    void updateLiveData();
    void setDeviceConnected(bool connected);

public slots:
    void setA2bCounts(const QVector<int> &counts);

signals:
    void pinsChanged();
    void limitReached(bool limit);
    //! the AS5600 helper measured a sensor's range: raw readings 0-4092
    void applyCalibration(int analogSource, int rawMin, int rawMax);

private:
    void setTexts();
    void fillPinCombo(int spareIndex);
    void pinComboChanged(int spareIndex);
    void updateSummary();

    pin_func_t m_pins[HSR_SPARE_PINS] = {};
    QVector<int> m_a2bCounts = QVector<int>(HSR_MAX_AXES, 0);
    bool m_limit = false;
    bool m_connected = false;
    bool m_bulkUpdate = false;

    QGroupBox *m_boardGroup;
    QLabel *m_inText;
    QLabel *m_axText;
    QLabel *m_axNames[HSR_AX_INPUTS];
    QProgressBar *m_axBars[HSR_AX_INPUTS];

    QGroupBox *m_spareGroup;
    QLabel *m_spareText;
    QLabel *m_spareNames[HSR_SPARE_PINS];
    QComboBox *m_spareCombos[HSR_SPARE_PINS];
    QLabel *m_spareInfo[HSR_SPARE_PINS];
    QProgressBar *m_spareBars[HSR_SPARE_PINS];

    QGroupBox *m_summaryGroup;
    QLabel *m_summary;

    As5600Helper *m_as5600;
};

#endif // BOARDCONFIG_H
