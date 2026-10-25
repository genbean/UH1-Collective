#include "avrflasher.h"
#include <QCoreApplication>
#include <QDateTime>
#include <QDir>
#include <QFileInfo>
#include <QStandardPaths>
#include <QThread>
#include <QDebug>

#ifdef Q_OS_WIN
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>
#endif

static const int POLL_MS = 100;

AvrFlasher::AvrFlasher(QObject *parent)
    : QObject(parent)
{
    m_pollTimer.setInterval(POLL_MS);
    connect(&m_pollTimer, &QTimer::timeout, this, &AvrFlasher::pollPorts);
}

QStringList AvrFlasher::serialPorts()
{
    QStringList ports;
#ifdef Q_OS_WIN
    HKEY key;
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"HARDWARE\\DEVICEMAP\\SERIALCOMM", 0, KEY_READ, &key) == ERROR_SUCCESS) {
        for (DWORD i = 0;; ++i) {
            wchar_t name[256];
            wchar_t data[64];
            DWORD nameLen = 256, dataLen = sizeof(data), type = 0;
            if (RegEnumValueW(key, i, name, &nameLen, nullptr, &type, reinterpret_cast<BYTE *>(data), &dataLen) != ERROR_SUCCESS) {
                break;
            }
            if (type == REG_SZ) {
                ports.append(QString::fromWCharArray(data, int(dataLen / sizeof(wchar_t))).remove(QChar('\0')));
            }
        }
        RegCloseKey(key);
    }
#else
    QDir dev("/dev");
    for (const QString &name : dev.entryList(QStringList() << "ttyACM*" << "cu.usbmodem*", QDir::System)) {
        ports.append("/dev/" + name);
    }
#endif
    ports.sort();
    return ports;
}

bool AvrFlasher::findAvrdude(QString *exe, QString *conf)
{
#ifdef Q_OS_WIN
    const QString exeName = "avrdude.exe";
#else
    const QString exeName = "avrdude";
#endif
    // bundled with the app (the installer puts it here)
    QString dir = QCoreApplication::applicationDirPath() + "/avrdude/";
    if (QFileInfo::exists(dir + exeName) && QFileInfo::exists(dir + "avrdude.conf")) {
        *exe = dir + exeName;
        *conf = dir + "avrdude.conf";
        return true;
    }
    // the Arduino IDE's copy (Arduino15/packages/arduino/tools/avrdude/<version>/)
    QStringList roots;
#ifdef Q_OS_WIN
    roots << QStandardPaths::writableLocation(QStandardPaths::GenericDataLocation) + "/Arduino15";
#elif defined(Q_OS_MAC)
    roots << QDir::homePath() + "/Library/Arduino15";
#else
    roots << QDir::homePath() + "/.arduino15";
#endif
    for (const QString &root : roots) {
        QDir tools(root + "/packages/arduino/tools/avrdude");
        QStringList versions = tools.entryList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
        for (int i = versions.size() - 1; i >= 0; --i) {
            QString base = tools.filePath(versions[i]);
            if (QFileInfo::exists(base + "/bin/" + exeName) && QFileInfo::exists(base + "/etc/avrdude.conf")) {
                *exe = base + "/bin/" + exeName;
                *conf = base + "/etc/avrdude.conf";
                return true;
            }
        }
    }
    // avrdude on the PATH, with its own config
    QString onPath = QStandardPaths::findExecutable("avrdude");
    if (onPath.isEmpty() == false) {
        *exe = onPath;
        conf->clear();
        return true;
    }
    return false;
}

bool AvrFlasher::touch1200(const QString &port)
{
#ifdef Q_OS_WIN
    QString path = "\\\\.\\" + port;
    HANDLE h = CreateFileW(reinterpret_cast<LPCWSTR>(path.utf16()), GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                           OPEN_EXISTING, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE) {
        return false;
    }
    DCB dcb = {};
    dcb.DCBlength = sizeof(dcb);
    bool ok = GetCommState(h, &dcb);
    if (ok) {
        dcb.BaudRate = 1200;
        dcb.ByteSize = 8;
        dcb.Parity = NOPARITY;
        dcb.StopBits = ONESTOPBIT;
        dcb.fDtrControl = DTR_CONTROL_ENABLE;
        ok = SetCommState(h, &dcb);
    }
    if (ok) {
        EscapeCommFunction(h, SETDTR);
        Sleep(50);
        EscapeCommFunction(h, CLRDTR);
    }
    CloseHandle(h);
    return ok;
#else
    int fd = ::open(port.toLocal8Bit().constData(), O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0) {
        return false;
    }
    termios tio;
    bool ok = tcgetattr(fd, &tio) == 0;
    if (ok) {
        cfsetispeed(&tio, B1200);
        cfsetospeed(&tio, B1200);
        ok = tcsetattr(fd, TCSANOW, &tio) == 0;
    }
    int dtr = TIOCM_DTR;
    ioctl(fd, TIOCMBIC, &dtr);
    ::close(fd);
    return ok;
#endif
}

bool AvrFlasher::isBusy() const
{
    return m_busy;
}

void AvrFlasher::prepare()
{
    QStringList ports = serialPorts();
    m_before = QSet<QString>(ports.begin(), ports.end());
    m_gone.clear();
}

void AvrFlasher::flashWhenBootloaderAppears(const QString &hexFile, int timeoutMs)
{
    m_hexFile = hexFile;
    m_busy = true;
    m_deadline = QDateTime::currentMSecsSinceEpoch() + timeoutMs;
    emit progress(0);
    emit status(tr("Waiting for the bootloader..."));
    m_pollTimer.start();
}

void AvrFlasher::cancel()
{
    m_pollTimer.stop();
    if (m_process) {
        m_process->kill();
    }
    m_busy = false;
}

void AvrFlasher::pollPorts()
{
    QStringList now = serialPorts();
    QSet<QString> present(now.begin(), now.end());
    for (const QString &p : m_before) {
        if (present.contains(p) == false) {
            m_gone.insert(p);
        }
    }
    for (const QString &p : now) {
        // a new port, or one that went away and came back (the same port number reused)
        if (m_before.contains(p) == false || m_gone.contains(p)) {
            m_pollTimer.stop();
            qDebug() << "Bootloader port:" << p;
            // the port needs a moment before it accepts connections
            QTimer::singleShot(300, this, [this, p] { runAvrdude(p); });
            return;
        }
    }
    if (QDateTime::currentMSecsSinceEpoch() > m_deadline) {
        m_pollTimer.stop();
        m_busy = false;
        emit finished(false, tr("The bootloader didn't appear. Try again, or double-tap the Pro Micro's RST "
                                "and flash within 8 seconds."));
    }
}

void AvrFlasher::runAvrdude(const QString &port)
{
    QString exe, conf;
    if (findAvrdude(&exe, &conf) == false) {
        m_busy = false;
        emit finished(false, tr("avrdude wasn't found. It comes with HeliSR Configurator's installer "
                                "(in the avrdude folder next to the app) and with the Arduino IDE."));
        return;
    }
    QStringList args;
    if (conf.isEmpty() == false) {
        args << "-C" << conf;
    }
    args << "-p" << "atmega32u4" << "-c" << "avr109" << "-P" << port << "-b" << "57600" << "-D"
         << "-U" << "flash:w:" + QDir::toNativeSeparators(m_hexFile) + ":i";

    m_output.clear();
    m_verifying = false;
    m_process = new QProcess(this);
    m_process->setProcessChannelMode(QProcess::MergedChannels);
    connect(m_process, &QProcess::readyRead, this, [this] {
        parseOutput(QString::fromLocal8Bit(m_process->readAll()));
    });
    connect(m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished), this,
            [this](int code, QProcess::ExitStatus exitStatus) {
        bool ok = exitStatus == QProcess::NormalExit && code == 0;
        qDebug().noquote() << m_output;
        m_process->deleteLater();
        m_process = nullptr;
        m_busy = false;
        if (ok) {
            emit progress(100);
            emit finished(true, tr("Firmware written and verified."));
        } else {
            QString last = m_output.trimmed().section('\n', -3);
            emit finished(false, tr("avrdude failed (%1):\n%2").arg(code).arg(last));
        }
    });
    emit status(tr("Writing on %1...").arg(port));
    qDebug() << "Running" << exe << args;
    m_process->start(exe, args);
    if (m_process->waitForStarted(5000) == false) {
        m_process->deleteLater();
        m_process = nullptr;
        m_busy = false;
        emit finished(false, tr("avrdude couldn't be started: %1").arg(exe));
    }
}

// avrdude draws "Writing | ##########... | 100%" and then "Reading | ..." (the
// verify), one # per 2 %. Writing counts as 0-80 % here, verifying as 80-100 %.
void AvrFlasher::parseOutput(const QString &text)
{
    m_output += text;
    int w = m_output.lastIndexOf("Writing |");
    int r = m_output.lastIndexOf("Reading |");
    if (r > w && w >= 0) {
        int hashes = m_output.mid(r).count('#');
        emit progress(80 + qMin(hashes, 50) * 20 / 50);
        if (m_verifying == false) {
            m_verifying = true;
            emit status(tr("Verifying..."));
        }
    } else if (w >= 0) {
        int hashes = m_output.mid(w).count('#');
        emit progress(qMin(hashes, 50) * 80 / 50);
    }
}
