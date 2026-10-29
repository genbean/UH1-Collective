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
class As5600I2cHelper;

// The "Board" page: which HeliSR board, what its fixed inputs are, what each
// spare Pro Micro pin is used for, and a summary of what the setup adds up to.
// Replaces FreeJoy's Blue Pill pin page; the other pages follow the spare pin
// choices made here (through pinsChanged()). The board follows the connected
// device; without one it can be chosen here. Rev 3.0 gets the PROG-button
// AS5600 helper, Rev 4.0 the I2C one.
class BoardConfig : public QWidget
{
    Q_OBJECT

public:
    explicit BoardConfig(QWidget *parent = nullptr);

    void readFromConfig();
    void writeToConfig();
    void retranslateUi();
    void resetAllPins();

    //! show this board (HSR_BOARD_REV30 or HSR_BOARD_REV40); the other pages follow
    void setBoard(int boardId);
    //! the spare pin functions chosen on this page (HSR_SPARE_PINS of them)
    const pin_func_t *pins() const;
    bool limitIsReached() const;

    //! live readings from the device's params report
    void updateLiveData();
    void setDeviceConnected(bool connected);

    //! Rev 4.0 boards: the AS5600 settings and status from the device
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
    //! the board shown changed (chosen here, or to follow a device)
    void boardChanged(int boardId);
    //! Rev 4.0: save these AS5600 settings on the board
    void writeSensorConfig(const hsr_sensor_config_t &config);
    //! Rev 4.0: read this AX port's sensor in full a few times a second (-1: stop)
    void sensorDebugPort(int port);
    //! Rev 4.0: start this port's counters again
    void clearSensorCounters(int port);

private:
    void setTexts();
    void applyBoard();
    void fillPinCombo(int spareIndex);
    void pinComboChanged(int spareIndex);
    void updateSummary();

    pin_func_t m_pins[HSR_SPARE_PINS] = {};
    QVector<int> m_a2bCounts = QVector<int>(HSR_MAX_AXES, 0);
    bool m_limit = false;
    bool m_connected = false;
    bool m_bulkUpdate = false;

    QGroupBox *m_boardGroup;
    QLabel *m_boardLabel;
    QComboBox *m_boardCombo;
    QLabel *m_inText;
    QLabel *m_axText;
    QLabel *m_axNames[HSR_AX_INPUTS];
    QProgressBar *m_axBars[HSR_AX_INPUTS];
    QLabel *m_axState[HSR_AX_INPUTS];       // Rev 4.0: each AS5600's state
    QLabel *m_a2a3Text;                     // Rev 4.0: A2 and A3
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

    As5600Helper *m_as5600;
    As5600I2cHelper *m_as5600i2c;
};

#endif // BOARDCONFIG_H
