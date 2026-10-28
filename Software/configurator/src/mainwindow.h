#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QSettings>
#include <QTranslator>

#include "hiddevice.h"

#include "advancedsettings.h"
#include "axesconfig.h"
#include "axescurvesconfig.h"
#include "boardconfig.h"
#include "buttonconfig.h"
#include "debugwindow.h"
#include "encodersconfig.h"
#include "ledconfig.h"
#include "switchbutton.h"

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();
    void setDefaultStyleSheet();

    // used by the page round-trip test (uitest.cpp) as well
    bool isInitialized() const { return m_initialized; }
    //! show this board; followDevice = false: keep it even when a device of another board connects
    void showBoard(int boardId, bool followDevice);
    BoardConfig *boardConfig() const { return m_boardConfig; }
    void UiReadFromConfig();
    //! removeOemName: also clear Windows' cached name for the config's VID/PID
    void UiWriteToConfig(bool removeName = true);

private slots:
    void showConnectDeviceInfo();
    void hideConnectDeviceInfo();
    void deviceInfoReceived(bool compatible);
    void getParamsPacket();

    void configReceived(bool success);
    void configSent(bool success);

    void hidDeviceList(const QStringList &deviceNames);
    void hidDeviceListChanged(int index);

    //! spare pins or axis ranges changed: the pages that depend on them follow
    void scheduleBoardUpdate();
    void applyCalibration(int analogSource, int rawMin, int rawMax);

    void languageChanged(const QString &language);
    void setFont();

    void finalInitialization();

    void on_pushButton_ResetAllPins_clicked();

    void on_pushButton_ReadConfig_clicked();
    void on_pushButton_WriteConfig_clicked();

    void on_pushButton_SaveToFile_clicked();
    void on_pushButton_LoadFromFile_clicked();

    void on_pushButton_ShowDebug_clicked();

    void on_pushButton_TestButton_clicked();
    void on_pushButton_TestButton_2_clicked();

    void on_pushButton_Wiki_clicked();

    void themeChanged(bool dark);

    void on_toolButton_ConfigsDir_clicked();

protected:
    void keyPressEvent(QKeyEvent *event) override;
    void keyReleaseEvent(QKeyEvent *event) override;

private:
    Ui::MainWindow *ui;

    QThread *m_thread;
    HidDevice *m_hidDeviceWorker;

    BoardConfig *m_boardConfig;
    ButtonConfig *m_buttonConfig;
    LedConfig *m_ledConfig;
    EncodersConfig *m_encoderConfig;
    AxesConfig *m_axesConfig;
    AxesCurvesConfig *m_axesCurvesConfig;
    AdvancedSettings *m_advSettings;

    DebugWindow *m_debugWindow = nullptr;
    bool m_debugIsEnable;

    bool m_deviceReady = false;         // a compatible device is open
    bool m_transferring = false;        // reading or writing its settings
    bool m_boardUpdatePending = false;
    bool m_initialized = false;         // the pages have been filled once
    bool m_followDeviceBoard = true;    // the pages show the connected device's board

    QString m_buttonDefaultStyle;

    QString m_cfgDirPath;
    void curCfgFileChanged(const QString &fileName);
    QStringList cfgFilesList(const QString &dirPath);
    QIcon pixmapToIcon(QPixmap pixmap, const QColor &color);
    void updateColor();

    void applyBoardUpdate();
    void updateReadWriteButtons();
    QString firmwareVersionText() const;

    void removeOemName();

    void loadAppConfig();
    void saveAppConfig();
};
#endif // MAINWINDOW_H
