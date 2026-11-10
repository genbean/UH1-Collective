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

class As5600I2cHelper;

// The "Board" page: the HeliSR Rev 4.0 board's fixed inputs, what each spare
// Pro Micro pin is used for, a summary of what the setup adds up to, and the
// AS5600 helper. Replaces FreeJoy's Blue Pill pin page; the other pages follow
// the spare pin choices made here (through pinsChanged()).
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

    //! the AS5600 settings and status from the device
    void sensorConfigReceived(bool isSuccess);
    void sensorStatusReceived();
    void sensorConfigSent(bool isSuccess);
    void sensorDebugReceived(bool isSuccess);

public slots:
    void setA2bCounts(const QVector<int> &counts);

signals:
    void pinsChanged();
    void limitReached(bool limit);
    //! a helper measured or set a sensor's range: raw readings 0-4092
    void applyCalibration(int analogSource, int rawMin, int rawMax);
    //! save these AS5600 settings on the board
    void writeSensorConfig(const hsr_sensor_config_t &config);
    //! read this AX port's sensor in full a few times a second (-1: stop)
    void sensorDebugPort(int port);
    //! start this port's counters again
    void clearSensorCounters(int port);

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
    QLabel *m_axState[HSR_AX_INPUTS];       // each AS5600's state
    QLabel *m_a2a3Text;                     // A2 and A3
    QLabel *m_a2a3Names[2];
    QProgressBar *m_a2a3Bars[2];

    QGroupBox *m_spareGroup;
    QLabel *m_spareText;
    QLabel *m_spareNames[HSR_SPARE_PINS];
    QComboBox *m_spareCombos[HSR_SPARE_PINS];
    QLabel *m_spareInfo[HSR_SPARE_PINS];
    QProgressBar *m_spareBars[HSR_SPARE_PINS];

    QGroupBox *m_summaryGroup;
    QLabel *m_summary;

    As5600I2cHelper *m_as5600i2c;
};

#endif // BOARDCONFIG_H
