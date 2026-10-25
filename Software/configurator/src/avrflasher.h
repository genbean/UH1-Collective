#ifndef AVRFLASHER_H
#define AVRFLASHER_H

#include <QObject>
#include <QProcess>
#include <QSet>
#include <QStringList>
#include <QTimer>

// Writes a .hex file to a Pro Micro through its Caterina bootloader with
// avrdude. The bootloader shows up as a new serial port for about 8 seconds
// after the board resets into it, so flashing is: note the serial ports, get
// the board into its bootloader (HeliSR's bootloader command, a 1200-baud
// touch on an Arduino sketch's port, or a double tap on RST), wait for the new
// port, and run avrdude on it.
class AvrFlasher : public QObject
{
    Q_OBJECT

public:
    explicit AvrFlasher(QObject *parent = nullptr);

    //! serial ports present now ("COM4", "/dev/ttyACM0" ...)
    static QStringList serialPorts();
    //! avrdude and its config: bundled next to the app, else the Arduino IDE's
    static bool findAvrdude(QString *exe, QString *conf);
    //! open a port at 1200 baud and drop DTR: an Arduino sketch's cue to start the bootloader
    static bool touch1200(const QString &port);

    bool isBusy() const;

    //! remember the ports present now; call before the board resets
    void prepare();
    //! wait up to timeoutMs for the bootloader's port, then write the file
    void flashWhenBootloaderAppears(const QString &hexFile, int timeoutMs);
    void cancel();

signals:
    void status(const QString &text);
    void progress(int percent);
    void finished(bool success, const QString &message);

private:
    void pollPorts();
    void runAvrdude(const QString &port);
    void parseOutput(const QString &text);

    QSet<QString> m_before;     // ports present before the reset
    QSet<QString> m_gone;       // of those, ports that went away since (may come back as the bootloader)
    QString m_hexFile;
    QTimer m_pollTimer;
    qint64 m_deadline = 0;
    QProcess *m_process = nullptr;
    QString m_output;
    bool m_verifying = false;
    bool m_busy = false;
};

#endif // AVRFLASHER_H
