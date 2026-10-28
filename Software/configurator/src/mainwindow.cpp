#include <QThread>
#include <QTimer>
#include <QSettings>
#include <QFileDialog>
#include <QDesktopServices>
#include <QMessageBox>
#include <QSpinBox>
#include <QCheckBox>
#include <QKeyEvent>
#include <QPainter>

#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "mousewheelguard.h"
#include "configtofile.h"
#include "selectfolder.h"

#include "common_types.h"
#include "global.h"
#include "deviceconfig.h"
#include "helisrboard.h"
#include "version.h"
#include "shared/helisr_defaults.h"

#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    qDebug()<<"main + member initialize time ="<< gEnv.pApp_start_time->elapsed() << "ms";
    QElapsedTimer timer;
    timer.start();

    ui->setupUi(this);

    QMainWindow::setWindowIcon(QIcon(":/Images/icon-32.png"));

    // app version
    setWindowTitle(tr("HeliSR Configurator") + " v" + APP_VERSION);

    // load application config
    loadAppConfig();

    m_thread = new QThread;
    m_hidDeviceWorker = new HidDevice();

    qDebug()<<"before add widgets ="<< timer.restart() << "ms";
                                            //////////////// ADD WIDGETS ////////////////
    // add board widget (replaces FreeJoy's pin page)
    m_boardConfig = new BoardConfig(this);
    ui->layoutV_tabPinConfig->addWidget(m_boardConfig);
    qDebug()<<"board config load time ="<< timer.restart() << "ms";
    // add button widget
    m_buttonConfig = new ButtonConfig(this);
    ui->layoutV_tabButtonConfig->addWidget(m_buttonConfig);
    qDebug()<<"button config load time ="<< timer.restart() << "ms";
    // add axes widget
    m_axesConfig = new AxesConfig(this);
    ui->layoutV_tabAxesConfig->addWidget(m_axesConfig);
    qDebug()<<"axes config load time ="<< timer.restart() << "ms";
    // add axes curves widget
    m_axesCurvesConfig = new AxesCurvesConfig(this);
    ui->layoutV_tabAxesCurvesConfig->addWidget(m_axesCurvesConfig);
    qDebug()<<"curves config load time ="<< timer.restart() << "ms";
    // add encoders widget
    m_encoderConfig = new EncodersConfig(this);
    ui->layoutV_tabEncodersConfig->addWidget(m_encoderConfig);
    qDebug()<<"encoder config load time ="<< timer.restart() << "ms";
    // add led widget
    m_ledConfig = new LedConfig(this);
    ui->layoutV_tabLedConfig->addWidget(m_ledConfig);
    qDebug()<<"led config load time ="<< timer.restart() << "ms";
    // add advanced settings widget
    m_advSettings = new AdvancedSettings(this);
    ui->layoutV_tabAdvSettings->addWidget(m_advSettings);
    qDebug()<<"advanced settings load time ="<< timer.restart() << "ms";


    // strong focus for mouse wheel
    // без протекта можно при прокручивании страницы случайно навести на комбобокс и изменить его колесом мыши
    // при установке setFocusPolicy(Qt::StrongFocus) и протекта на комбобокс придётся нажать, для прокручивания колесом
    for (auto &&child: this->findChildren<QSpinBox *>())
    {
        child->setFocusPolicy(Qt::StrongFocus);
        child->installEventFilter(new MouseWheelGuard(child));
    }

    for (auto &&child: this->findChildren<QComboBox *>())
    {
        child->setFocusPolicy(Qt::StrongFocus);
        child->installEventFilter(new MouseWheelGuard(child));
    }
    // хз так или сверху исключать?
    ui->comboBox_HidDeviceList->setFocusPolicy(Qt::WheelFocus);
    ui->comboBox_Configs->setFocusPolicy(Qt::WheelFocus);
    for (auto &&comBox: m_boardConfig->findChildren<QComboBox *>())
    {
            comBox->setFocusPolicy(Qt::WheelFocus);
    }
    for (auto &&comBox: m_axesCurvesConfig->findChildren<QComboBox *>())
    {
        comBox->setFocusPolicy(Qt::WheelFocus);
    }
    for (auto &&comBox: m_ledConfig->findChildren<QComboBox *>())
    {
        comBox->setFocusPolicy(Qt::WheelFocus);
    }

                                            //////////////// SIGNASL-SLOTS ////////////////
    // spare pins or axis ranges changed
    connect(m_boardConfig, &BoardConfig::pinsChanged, this, &MainWindow::scheduleBoardUpdate);
    connect(m_axesConfig, &AxesConfig::a2bCountChanged, this, &MainWindow::scheduleBoardUpdate);
    // too many axis ranges
    connect(m_boardConfig, &BoardConfig::limitReached, this, &MainWindow::updateReadWriteButtons);
    // AS5600 helper measured a range
    connect(m_boardConfig, &BoardConfig::applyCalibration, this, &MainWindow::applyCalibration);
    // Rev 4.0: the AS5600 settings live on the board, apart from the profile
    connect(m_boardConfig, &BoardConfig::writeSensorConfig, this, [this](const hsr_sensor_config_t &config) {
        m_hidDeviceWorker->writeSensorConfig(config);
    });
    connect(m_hidDeviceWorker, &HidDevice::sensorConfigReceived, m_boardConfig, &BoardConfig::sensorConfigReceived);
    connect(m_hidDeviceWorker, &HidDevice::sensorConfigSent, m_boardConfig, &BoardConfig::sensorConfigSent);
    connect(m_hidDeviceWorker, &HidDevice::sensorStatusReceived, m_boardConfig, &BoardConfig::sensorStatusReceived);
    // encoder changed
    connect(m_buttonConfig, &ButtonConfig::encoderInputChanged, m_encoderConfig, &EncodersConfig::encoderInputChanged);
    // language changed
    connect(m_advSettings, &AdvancedSettings::languageChanged, this, &MainWindow::languageChanged);
    // theme changed
    connect(m_advSettings, &AdvancedSettings::themeChanged, this, &MainWindow::themeChanged);
    // font changed
    connect(m_advSettings, &AdvancedSettings::fontChanged, this, &MainWindow::setFont);

    // flasher: restart the device into its bootloader (the worker picks the request up)
    connect(m_advSettings->flasher(), &Flasher::enterBootloaderRequested, this, [this] {
        m_hidDeviceWorker->enterBootloader();
    });
    connect(m_hidDeviceWorker, &HidDevice::bootloaderStarted, m_advSettings->flasher(), &Flasher::bootloaderStarted);
    // set selected hid device
    connect(ui->comboBox_HidDeviceList, SIGNAL(currentIndexChanged(int)),
                this, SLOT(hidDeviceListChanged(int)));


    // HID worker
    m_hidDeviceWorker->moveToThread(m_thread);
    connect(m_thread, &QThread::started, m_hidDeviceWorker, &HidDevice::processData);

    connect(m_hidDeviceWorker, &HidDevice::paramsPacketReceived, this, &MainWindow::getParamsPacket);
    connect(m_hidDeviceWorker, &HidDevice::deviceConnected, this, &MainWindow::showConnectDeviceInfo);
    connect(m_hidDeviceWorker, &HidDevice::deviceDisconnected, this, &MainWindow::hideConnectDeviceInfo);
    connect(m_hidDeviceWorker, &HidDevice::deviceInfoReceived, this, &MainWindow::deviceInfoReceived);
    connect(m_hidDeviceWorker, &HidDevice::hidDeviceList, this, &MainWindow::hidDeviceList);


    // read config from device
    connect(m_hidDeviceWorker, &HidDevice::configReceived, this, &MainWindow::configReceived);
    // write config to device
    connect(m_hidDeviceWorker, &HidDevice::configSent, this, &MainWindow::configSent);


    // load default config // loading will occur after loading buttons config
    // комбобоксы у кнопок заполняются после старта приложения и конфиг должен
    // запускаться сигналом от кнопок
    connect(m_buttonConfig, &ButtonConfig::logicalButtonsCreated, this, &MainWindow::finalInitialization);

    // set theme
    gEnv.pAppSettings->beginGroup("StyleSettings");
    QString style = gEnv.pAppSettings->value("StyleSheet", "dark").toString();
    gEnv.pAppSettings->endGroup();
    if (style == "dark") {
        themeChanged(true);
    } else {
        themeChanged(false);
    }

    updateReadWriteButtons();
    m_thread->start();

    qDebug()<<"after widgets load time ="<< timer.elapsed() << "ms";
    qDebug()<<"without style startup time ="<< gEnv.pApp_start_time->elapsed() << "ms";
}

MainWindow::~MainWindow()
{
    saveAppConfig();
    m_hidDeviceWorker->setIsFinish(true);
    m_thread->quit();
    m_thread->wait();
    delete m_hidDeviceWorker;
    m_thread->deleteLater();
    delete ui;
}




                                              ///////////////////// device reports /////////////////////
// device opened; INFO follows
void MainWindow::showConnectDeviceInfo()
{
    ui->label_DeviceStatus->setText(tr("Connected"));
    ui->label_DeviceStatus->setStyleSheet("color: white; background-color: rgb(0, 128, 0);");
}

// device disconnected
void MainWindow::hideConnectDeviceInfo()
{
    ui->label_DeviceStatus->setText(tr("Disconnected"));
    ui->label_DeviceStatus->setStyleSheet("color: white; background-color: rgb(160, 0, 0);");
    m_deviceReady = false;
    m_transferring = false;
    updateReadWriteButtons();
    m_advSettings->flasher()->deviceConnected(false);
    m_boardConfig->setDeviceConnected(false);
    // debug window
    if (m_debugWindow) {
        m_debugWindow->resetPacketsCount();
    }
    // disable curve point
    QTimer::singleShot(3000, this, [&] {   // не лучший способ
        if (ui->pushButton_ReadConfig->isEnabled() == false) {
            m_axesCurvesConfig->deviceStatus(false);
        }
    });
}

QString MainWindow::firmwareVersionText() const
{
    uint16_t v = gEnv.pDeviceConfig->info.firmware_version;
    return QStringLiteral("v%1.%2.%3").arg(v >> 8).arg((v >> 4) & 0xF).arg(v & 0xF);
}

// the device answered INFO: its firmware, and whether its settings match this app's
void MainWindow::deviceInfoReceived(bool compatible)
{
    const hsr_info_t &info = gEnv.pDeviceConfig->info;
    m_advSettings->flasher()->deviceConnected(true, &info);
    m_deviceReady = compatible;
    if (compatible && m_followDeviceBoard) {
        // the pages show what this board has; a change rebuilds them once
        m_boardConfig->setBoard(info.board_id);
        applyBoardUpdate();
    }
    m_boardConfig->setDeviceConnected(compatible);
    if (compatible) {
        ui->label_DeviceStatus->setStyleSheet("color: white; background-color: rgb(0, 128, 0);");
        ui->label_DeviceStatus->setText(tr("Device firmware") + " " + firmwareVersionText() + ", "
                                        + HsrBoard::revisionName(info.board_id));
    } else {
        ui->label_DeviceStatus->setStyleSheet("color: white; background-color: rgb(168, 168, 0);");
        if (info.firmware_version) {
            ui->label_DeviceStatus->setText(tr("Firmware %1 doesn't match this app: flash it (Advanced Settings)")
                                                .arg(firmwareVersionText()));
        } else {
            ui->label_DeviceStatus->setText(tr("No answer from the device"));
        }
    }
    updateReadWriteButtons();
}

// add/delete hid devices to/from combobox
void MainWindow::hidDeviceList(const QStringList &deviceNames)
{
    ui->comboBox_HidDeviceList->clear();
    ui->comboBox_HidDeviceList->addItems(deviceNames);
}

// received live data
void MainWindow::getParamsPacket()
{
    // update button state without delay
    if(ui->tab_ButtonConfig->isVisible() == true || m_debugWindow) {
        m_buttonConfig->buttonStateChanged();
    }

    static QElapsedTimer timer;

    if (timer.isValid() == false) {
        timer.start();
    }
    else if (timer.elapsed() > 17)    // update UI every 17ms(~60fps)
    {
        // always: the AS5600 helper watches for PROG presses even when its page is hidden
        m_boardConfig->updateLiveData();
        if(ui->tab_LED->isVisible() == true) {
            m_ledConfig->setLedsState();
        }
        if(ui->tab_AxesConfig->isVisible() == true) {
            m_axesConfig->axesValueChanged();
        }
        if(ui->tab_AxesCurves->isVisible() == true) {
            m_axesCurvesConfig->updateAxesCurves();
        }
        timer.restart();
    }
    // debug info
    if (m_debugWindow) {
        m_debugWindow->devicePacketReceived();
    }
}


                                            /////////////////////    BOARD    /////////////////////
// Several changes can arrive at once (every axis's range count while a config
// loads), so the dependent pages are rebuilt once, from the event loop.
void MainWindow::scheduleBoardUpdate()
{
    if (m_boardUpdatePending == false) {
        m_boardUpdatePending = true;
        QTimer::singleShot(0, this, &MainWindow::applyBoardUpdate);
    }
}

void MainWindow::applyBoardUpdate()
{
    if (m_boardUpdatePending == false) {
        return;
    }
    m_boardUpdatePending = false;
    const pin_func_t *pins = m_boardConfig->pins();
    QVector<int> a2b = m_axesConfig->a2bCounts();
    m_boardConfig->setA2bCounts(a2b);
    m_buttonConfig->setPhysicalInputs(HsrBoard::physicalInputs(pins, a2b.constData()));
    m_axesConfig->setAvailableSources(pins);
    m_ledConfig->setPins(pins);
}

void MainWindow::showBoard(int boardId, bool followDevice)
{
    m_followDeviceBoard = followDevice;
    m_boardConfig->setBoard(boardId);
    applyBoardUpdate();
}

void MainWindow::applyCalibration(int analogSource, int rawMin, int rawMax)
{
    int n = m_axesConfig->applyCalibration(analogSource, rawMin, rawMax);
    QString source = HsrBoard::analogSourceName(analogSource);
    if (n == 0) {
        QMessageBox::information(this, tr("Calibration"),
                                 tr("No axis uses %1 yet. Choose it as an axis source on the Axes Config page, then apply again.").arg(source));
    } else {
        QMessageBox::information(this, tr("Calibration"),
                                 tr("The calibration of %1 axis/axes using %2 is set. Write the config to the device to keep it.")
                                     .arg(n).arg(source));
    }
}


                                            /////////////////////    CONFIG SLOTS    /////////////////////
void MainWindow::UiReadFromConfig()
{
    // read board config (spare pins)
    m_boardConfig->readFromConfig();
    // the axis sources and LED rows must match the pins just read
    applyBoardUpdate();
    // read axes config
    m_axesConfig->readFromConfig();
    // read axes curves config
    m_axesCurvesConfig->readFromConfig();
    // read encoder config
    m_encoderConfig->readFromConfig();
    // read LED config
    m_ledConfig->readFromConfig();
    // read adv.settings config
    m_advSettings->readFromConfig();
    // the buttons' input lists must match the pins and ranges just read
    applyBoardUpdate();
    // read button config
    m_buttonConfig->readFromConfig();
}

void MainWindow::UiWriteToConfig(bool removeName)
{
    applyBoardUpdate();
    // write board config
    m_boardConfig->writeToConfig();
    // write axes config
    m_axesConfig->writeToConfig();
    // write axes curves config
    m_axesCurvesConfig->writeToConfig();
    // write encoder config
    m_encoderConfig->writeToConfig();
    // write LED config
    m_ledConfig->writeToConfig();
    // write adv.settings config
    m_advSettings->writeToConfig();
    // write button config
    m_buttonConfig->writeToConfig();
    if (removeName) {
        removeOemName();
    }
}

// remove device name from registry. sometimes windows does not update the name in gaming devices and has to be deleted in the registry
void MainWindow::removeOemName()
{
#ifdef Q_OS_WIN
        qDebug()<<"Remove device OEMName from registry";
        QString path("HKEY_CURRENT_USER\\System\\CurrentControlSet\\Control\\MediaProperties\\PrivateProperties\\Joystick\\OEM\\VID_%1&PID_%2");
        QString path2("HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\MediaProperties\\PrivateProperties\\Joystick\\OEM\\VID_%1&PID_%2");
        QString vid = QString::number(gEnv.pDeviceConfig->config.vid, 16).toUpper().rightJustified(4, '0');
        QString pid = QString::number(gEnv.pDeviceConfig->config.pid, 16).toUpper().rightJustified(4, '0');
        QSettings(path.arg(vid, pid), QSettings::NativeFormat).remove("OEMName");
        QSettings(path2.arg(vid, pid), QSettings::NativeFormat).remove("OEMName");
#endif
}


// load default config
void MainWindow::finalInitialization()
{
    // load config files
    QStringList filesList = cfgFilesList(m_cfgDirPath);
    if (filesList.isEmpty() == false) {
        ui->comboBox_Configs->clear();
        ui->comboBox_Configs->addItems(filesList);
        gEnv.pAppSettings->beginGroup("Configs");
        QString lastCfg(gEnv.pAppSettings->value("LastCfg").toString());
        gEnv.pAppSettings->endGroup();
        bool found = false;
        for (int i = 0; i < filesList.size(); ++i) {
            if (filesList[i] == lastCfg) {
                curCfgFileChanged(lastCfg);
                ui->comboBox_Configs->setCurrentIndex(i);
                found = true;
                break;
            }
        }
        if (found == false) {
            curCfgFileChanged(ui->comboBox_Configs->currentText());
        }
    }  else {
        UiReadFromConfig();
    }

    // select config comboBox // should be after "// load config files"
    connect(ui->comboBox_Configs, &QComboBox::currentTextChanged, this, &MainWindow::curCfgFileChanged);
    m_initialized = true;
}

// current cfg file changed
void MainWindow::curCfgFileChanged(const QString &fileName)
{
    QString filePath = m_cfgDirPath + '/' + fileName + ".cfg";
    gEnv.pDeviceConfig->resetConfig();
    ConfigToFile::loadDeviceConfigFromFile(this, filePath, gEnv.pDeviceConfig->config);
    UiReadFromConfig();
}
// get config file list
QStringList MainWindow::cfgFilesList(const QString &dirPath)
{
    QDir dir(dirPath);
    QStringList cfgs = dir.entryList(QStringList() << "*.cfg", QDir::Files);
    for (auto &line : cfgs) {
        line.remove(line.size() - 4, 4);// 4 = ".cfg" characters count
    }
    cfgs.sort(Qt::CaseInsensitive);
    return cfgs;
}


// slot after receiving the config
void MainWindow::configReceived(bool success)
{
    m_buttonDefaultStyle = ui->pushButton_ReadConfig->styleSheet();
    static QString button_default_text = ui->pushButton_ReadConfig->text();    //????????????????????????

    if (success == true)
    {
        UiReadFromConfig();
        // curves pointer activated
        m_axesCurvesConfig->deviceStatus(true);

        ui->label_DeviceStatus->setText(tr("Device firmware") + " " + firmwareVersionText() + " ✔");

        ui->pushButton_ReadConfig->setText(tr("Received"));
        ui->pushButton_ReadConfig->setStyleSheet(m_buttonDefaultStyle + "color: rgb(235, 235, 235); background-color: rgb(0, 128, 0);");
    } else {
        ui->pushButton_ReadConfig->setText(tr("Error"));
        ui->pushButton_ReadConfig->setStyleSheet(m_buttonDefaultStyle + "color: rgb(235, 235, 235); background-color: rgb(200, 0, 0);");
    }
    QTimer::singleShot(1500, this, [&] {
        ui->pushButton_ReadConfig->setStyleSheet(m_buttonDefaultStyle);
        ui->pushButton_ReadConfig->setText(button_default_text);
        m_transferring = false;
        updateReadWriteButtons();
    });
}

// slot after sending the config
void MainWindow::configSent(bool success)
{
    m_buttonDefaultStyle = ui->pushButton_ReadConfig->styleSheet();
    static QString button_default_text = ui->pushButton_WriteConfig->text();    //???
    // curves pointer activated
    m_axesCurvesConfig->deviceStatus(true);

    if (success == true)
    {
        // the device saved the settings and restarts with them
        ui->pushButton_WriteConfig->setText(tr("Sent"));
        ui->pushButton_WriteConfig->setStyleSheet(m_buttonDefaultStyle + "color: white; background-color: rgb(0, 128, 0);");
    } else {
        ui->pushButton_WriteConfig->setText(tr("Error"));
        ui->pushButton_WriteConfig->setStyleSheet(m_buttonDefaultStyle + "color: white; background-color: rgb(200, 0, 0);");
    }
    QTimer::singleShot(1500, this, [&] {
        ui->pushButton_WriteConfig->setStyleSheet(m_buttonDefaultStyle);
        ui->pushButton_WriteConfig->setText(button_default_text);
        m_transferring = false;
        updateReadWriteButtons();
    });

    removeOemName();
}

void MainWindow::updateReadWriteButtons()
{
    bool ready = m_deviceReady && m_transferring == false;
    ui->pushButton_ReadConfig->setEnabled(ready);
    ui->pushButton_WriteConfig->setEnabled(ready && m_boardConfig->limitIsReached() == false);
}



                                            /////////////////////    APP SETTINGS   /////////////////////

// slot language change
void MainWindow::languageChanged(const QString &language)
{
    qDebug()<<"Retranslate UI";

    auto trFunc = [&](const QString &file) {
        if (gEnv.pTranslator->load(file) == false) {
            qWarning()<<"failed to load translate file";
            return false;
        }
        qApp->installTranslator(gEnv.pTranslator);
        ui->retranslateUi(this);
        return true;
    };

    if (language == "english")
    {
        if (gEnv.pTranslator->load(":/NO_FILE_IS_OK!!_DEFAULT_TRANSLATE") == true) {
            qWarning()<<"failed to load translate file";
            return;
        }
        qApp->installTranslator(gEnv.pTranslator);
        ui->retranslateUi(this);
    }
    else if (language == "russian")
    {
        if (trFunc(":/FreeJoyQt_ru") == false) return;
    }
    else if (language == "schinese")
    {
        if (trFunc(":/FreeJoyQt_zh_CN") == false) return;
    }
    else if (language == "deutsch")
    {
        if (trFunc(":/FreeJoyQt_de_DE") == false) return;
    }
    else
    {
        return;
    }

    m_boardConfig->retranslateUi();
    m_buttonConfig->retranslateUi();
    m_ledConfig->retranslateUi();
    m_encoderConfig->retranslateUi();
    m_axesConfig->retranslateUi();
    m_axesCurvesConfig->retranslateUi();
    m_advSettings->retranslateUi();
    if(m_debugWindow){
        m_debugWindow->retranslateUi();
        ui->pushButton_ShowDebug->setText(tr("Hide debug"));
    }
    qDebug()<<"done";
}

// set font
void MainWindow::setFont()
{
    QWidgetList list = QApplication::allWidgets();
    for (QWidget *widget : list) {
        widget->setFont(QApplication::font());
        widget->update();
    }
}

// load app config
void MainWindow::loadAppConfig()
{
    QSettings *appS = gEnv.pAppSettings;
    qDebug()<<"Loading application config";
    // load window settings
    appS->beginGroup("WindowSettings");
    this->restoreGeometry(appS->value("Geometry").toByteArray());
    appS->endGroup();
    // load tab index
    appS->beginGroup("TabIndexSettings");
    ui->tabWidget->setCurrentIndex(appS->value("CurrentIndex", 0).toInt());
    appS->endGroup();
    // load debug window
    appS->beginGroup("OtherSettings");
    m_debugIsEnable = appS->value("DebugEnable", "false").toBool();
    if (m_debugIsEnable){
        on_pushButton_ShowDebug_clicked();
        if (this->isMaximized() == false){
            resize(width(), height() - 120 - ui->layoutG_MainLayout->verticalSpacing());
        }
    }
    appS->endGroup();
    // load configs dir path
    appS->beginGroup("Configs");
    m_cfgDirPath = appS->value("Path", gEnv.pAppSettings->fileName().remove("HeliSRSettings.conf") + "configs").toString();
    appS->endGroup();
    // the board the pages showed last (before the pages are made)
    appS->beginGroup("BoardSettings");
    HsrBoard::setBoard(appS->value("Board", HSR_BOARD_REV30).toInt());
    appS->endGroup();

    //debug tab, only for debug build
    #ifdef QT_DEBUG
    #else
        ui->tabWidget->removeTab(ui->tabWidget->indexOf(ui->tab_Debug));
    #endif
    qDebug()<<"Finished loading application config";
}

// save app config
void MainWindow::saveAppConfig()
{
    QSettings *appS = gEnv.pAppSettings;
    qDebug()<<"Saving application config";
    // save tab index
    appS->beginGroup("TabIndexSettings");
    appS->setValue("CurrentIndex",    ui->tabWidget->currentIndex());
    appS->endGroup();
    // save window settings
    appS->beginGroup("WindowSettings");
    appS->setValue("Geometry",   this->saveGeometry());
    appS->endGroup();
    // save font settings
    appS->beginGroup("FontSettings");
    appS->setValue("FontSize", QApplication::font().pointSize());
    appS->endGroup();
    // save debug
    appS->beginGroup("OtherSettings");
    appS->setValue("DebugEnable", m_debugIsEnable);
    appS->endGroup();
    // save configs dir path
    appS->beginGroup("Configs");
    appS->setValue("Path", m_cfgDirPath);
    appS->setValue("LastCfg", ui->comboBox_Configs->currentText());
    appS->endGroup();
    // save the board shown
    appS->beginGroup("BoardSettings");
    appS->setValue("Board", HsrBoard::board());
    appS->endGroup();
    qDebug()<<"done";
}


                                                    ////////////////// buttons //////////////////
// comboBox selected device
void MainWindow::hidDeviceListChanged(int index)
{
    m_hidDeviceWorker->setSelectedDevice(index);
}

// reset all: the factory settings
void MainWindow::on_pushButton_ResetAllPins_clicked()
{
    qDebug()<<"Reset all started";
    gEnv.pDeviceConfig->resetConfig();
    UiReadFromConfig();
    qDebug()<<"done";
}

// read config from device
void MainWindow::on_pushButton_ReadConfig_clicked()
{
    qDebug()<<"Read config started";
    m_transferring = true;
    updateReadWriteButtons();

    m_hidDeviceWorker->getConfigFromDevice();
}

// write config to device
void MainWindow::on_pushButton_WriteConfig_clicked()
{
    qDebug()<<"Write config started";
    m_transferring = true;
    updateReadWriteButtons();

    UiWriteToConfig();
    m_hidDeviceWorker->sendConfigToDevice();
}

// load from file
void MainWindow::on_pushButton_LoadFromFile_clicked()
{
    qDebug()<<"Load from file started";
    QString fileName = QFileDialog::getOpenFileName(this,
        tr("Open Config"), m_cfgDirPath + "/", tr("Config Files (*.cfg)"));
    if (fileName.isEmpty()) return;

    dev_config_t loaded;
    hsr_config_defaults(&loaded);
    if (ConfigToFile::loadDeviceConfigFromFile(this, fileName, loaded)) {
        gEnv.pDeviceConfig->config = loaded;
        UiReadFromConfig();
    }
    qDebug()<<"done";
}

// save to file
void MainWindow::on_pushButton_SaveToFile_clicked()
{
    qDebug()<<"Save to file started";

    QString tmpStr(ui->comboBox_Configs->currentText());
    if (tmpStr == "") {
        tmpStr = QString::fromLatin1(gEnv.pDeviceConfig->config.device_name,
                                     int(qstrnlen(gEnv.pDeviceConfig->config.device_name, HSR_NAME_LEN)));
    }

    QString fileName = QFileDialog::getSaveFileName(this, tr("Save Config"),
                                                    m_cfgDirPath + "/" + tmpStr, tr("Config Files (*.cfg)"));
    if (fileName.isEmpty()) return;
    QFileInfo file(fileName);
    UiWriteToConfig();
    ConfigToFile::saveDeviceConfigToFile(file.absoluteFilePath(), gEnv.pDeviceConfig->config);

    QTimer::singleShot(200, this, [this, file]{
        QSignalBlocker bl(ui->comboBox_Configs);
        ui->comboBox_Configs->clear();
        ui->comboBox_Configs->addItems(cfgFilesList(m_cfgDirPath));
        bl.unblock();

        QString fileName(file.fileName());
        fileName.remove(fileName.size() - 4, 4); // 4 = ".cfg" characters count
        ui->comboBox_Configs->setCurrentText(fileName);
    });
    qDebug()<<"done";
}

// select configs dir path
void MainWindow::on_toolButton_ConfigsDir_clicked()
{
    SelectFolder dialog(m_cfgDirPath, this);
    if (dialog.exec() == QDialog::Accepted) {
        m_cfgDirPath = dialog.folderPath();
        QSignalBlocker bl(ui->comboBox_Configs);
        ui->comboBox_Configs->clear();
        bl.unblock();
        ui->comboBox_Configs->addItems(cfgFilesList(m_cfgDirPath));
    }
}

// Show debug widget
void MainWindow::on_pushButton_ShowDebug_clicked()
{
    if (m_debugWindow == nullptr)
    {
        m_debugWindow = new DebugWindow(this);
        gEnv.pDebugWindow = m_debugWindow;
        ui->layoutV_DebugWindow->addWidget(m_debugWindow);
        m_debugWindow->hide();
    }

    if (m_debugWindow->isVisible() == false)
    {
        m_debugWindow->setMinimumHeight(120);
        if (this->isMaximized() == false){
            resize(width(), height() + 120 + ui->layoutG_MainLayout->verticalSpacing());
        }
        m_debugWindow->setVisible(true);
        m_debugIsEnable = true;
        ui->pushButton_ShowDebug->setText(tr("Hide debug"));    // dont forget in MainWindow::languageChanged
    } else {
        m_debugWindow->setVisible(false);
        m_debugWindow->setMinimumHeight(0);
        if (this->isMaximized() == false){
            resize(width(), height() - 120 - ui->layoutG_MainLayout->verticalSpacing());    // and in LoadAppConfig()
        }
        m_debugIsEnable = false;
        ui->pushButton_ShowDebug->setText(tr("Show debug"));
    }
}

// Wiki
void MainWindow::on_pushButton_Wiki_clicked()
{
    QDesktopServices::openUrl(QUrl(PROJECT_DOCS_URL));
}



void MainWindow::keyPressEvent(QKeyEvent *event)
{
    if (event->key() == Qt::Key_Control) {
        m_axesCurvesConfig->setExclusive(false);
    }
}

void MainWindow::keyReleaseEvent(QKeyEvent *event)
{
    if (event->key() == Qt::Key_Control) {
        m_axesCurvesConfig->setExclusive(true);
    }
}


//! QPixmap gray-scale image (an alpha map) to colored QIcon
QIcon MainWindow::pixmapToIcon(QPixmap pixmap, const QColor &color)
{
    // initialize painter to draw on a pixmap and set composition mode
    QPainter painter(&pixmap);
    painter.setCompositionMode(QPainter::CompositionMode_SourceIn);
    // set color
    painter.setBrush(color);
    painter.setPen(color);
    // paint rect
    painter.drawRect(pixmap.rect());
    // here is our new colored icon
    return QIcon(pixmap);
}

void MainWindow::updateColor()
{
    QColor col = QApplication::palette().color(QPalette::Text);
    ui->toolButton_ConfigsDir->setIcon(pixmapToIcon(QPixmap(":/Images/setings.png"), col));
}


////////////////////////////////////////////////// debug tab //////////////////////////////////////////////////
// test buttons in debug tab
#ifdef QT_DEBUG
static dev_config_t testCfg;
#endif
void MainWindow::on_pushButton_TestButton_clicked()
{
#ifdef QT_DEBUG
    on_pushButton_LoadFromFile_clicked();
    testCfg = gEnv.pDeviceConfig->config;
    on_pushButton_WriteConfig_clicked();
#endif
}


void MainWindow::on_pushButton_TestButton_2_clicked()
{
#ifdef QT_DEBUG
    on_pushButton_ReadConfig_clicked();
    QElapsedTimer timer;
    timer.start();
    while (3000 > timer.elapsed()) {
        if (gEnv.readFinished) {
            qDebug()<<"compare before write to file";
            int cmp = memcmp(&testCfg, &gEnv.pDeviceConfig->config, sizeof(dev_config_t));
            if (cmp == 0) {
                qDebug()<<"equal";
            } else {
                qDebug()<<"ERROR. NOT EQUAL! memcmp ="<< cmp;
                return;
            }
            on_pushButton_SaveToFile_clicked();
            on_pushButton_LoadFromFile_clicked();
            qDebug()<<"final compare";
            cmp = memcmp(&testCfg, &gEnv.pDeviceConfig->config, sizeof(dev_config_t));
            if (cmp == 0) {
                qDebug()<<"equal";
            } else {
                qDebug()<<"ERROR. NOT EQUAL! memcmp ="<< cmp;
            }
            break;
        }
        QThread::msleep(50);
    }
#endif
}
