#ifndef AS5600I2CHELPER_H
#define AS5600I2CHELPER_H

#include <QGroupBox>
#include <QStringList>
#include "common_types.h"

QT_BEGIN_NAMESPACE
class QComboBox;
class QGroupBox;
class QLabel;
class QProgressBar;
class QPushButton;
QT_END_NAMESPACE

// HeliSR Rev 4.0: sets each AS5600's start and stop over I2C. Move the control
// to one end and click Set start, move it to the other end and click Set stop:
// the board saves the two raw angles and writes them to the sensor's ZPOS and
// MPOS every time it starts (nothing is burnt into the chip). The helper
// follows the raw angle between the clicks, so it knows which way the travel
// went. Also sets the I2C clock. Replaces Rev 3.0's PROG-button helper.
// Diagnostics (off until ticked, and only while the helper shows, as each full
// read holds the board up for a few ms): every register of the port's sensor,
// decoded, with its counters and hints on the magnet and the cable.
class As5600I2cHelper : public QGroupBox
{
    Q_OBJECT

public:
    explicit As5600I2cHelper(QWidget *parent = nullptr);

    void retranslateUi();
    //! a Rev 4.0 device is connected and understood
    void setDeviceConnected(bool connected);
    void sensorConfigReceived(bool isSuccess);
    void sensorStatusReceived();
    void sensorConfigSent(bool isSuccess);
    void sensorDebugReceived(bool isSuccess);

    //! "OK", "no sensor" ... for a port's state (HSR_SENSOR_...)
    static QString stateText(int state);
    //! a SENSOR_DEBUG reply decoded, line by line; saved: the board's settings for that port
    //! (null: not compared)
    static QStringList debugLines(const hsr_sensor_debug_t &d, const hsr_sensor_range_t *saved);
    //! what the readings suggest is wrong (magnet, supply, burnt chip), if anything
    static QStringList debugHints(const hsr_sensor_debug_t &d);

signals:
    //! save these settings on the board
    void writeSensorConfig(const hsr_sensor_config_t &config);
    //! read this port's sensor in full a few times a second (-1: stop)
    void sensorDebugPort(int port);
    void clearSensorCounters(int port);
    //! the sensor's whole output (0 to HSR_RAW_MAX) as the calibration of the axes using it
    void applyCalibration(int analogSource, int rawMin, int rawMax);

protected:
    void showEvent(QShowEvent *event) override;
    void hideEvent(QHideEvent *event) override;

private:
    int port() const;
    void updateDebugPort();
    void showDebug();
    bool portReadable() const;
    void send(const hsr_sensor_config_t &config, const QString &doneText, const QString &doneColor);
    void cancelRange();
    void updateControls();
    void showRange();
    void setStatus(const QString &text, const QString &color = QString());

    bool m_connected = false;
    bool m_haveConfig = false;
    bool m_haveStatus = false;
    bool m_sending = false;
    QString m_doneText;
    QString m_doneColor;

    // between Set start and Set stop: the raw angle followed through its wrap
    bool m_tracking = false;
    int m_startRaw = 0;
    int m_lastRaw = 0;
    int m_travel = 0;

    QLabel *m_intro;
    QLabel *m_clockLabel;
    QComboBox *m_clock;
    QLabel *m_clockNote;
    QComboBox *m_port;
    QLabel *m_state;
    QLabel *m_rawLabel;
    QProgressBar *m_raw;
    QLabel *m_outLabel;
    QProgressBar *m_out;
    QLabel *m_range;
    QPushButton *m_setStart;
    QPushButton *m_setStop;
    QPushButton *m_wholeCircle;
    QLabel *m_status;
    QPushButton *m_apply;

    int m_debugPortSent = -2;           // what sensorDebugPort last said
    bool m_haveDebug = false;           // a reply for the current port
    bool m_debugFailed = false;
    QGroupBox *m_debugBox;
    QLabel *m_debugText;
    QLabel *m_debugHints;
    QPushButton *m_clearCounters;
    QPushButton *m_copyDebug;
};

#endif // AS5600I2CHELPER_H
