#include "buttonconfig.h"
#include "ui_buttonconfig.h"
#include <QTimer>
#include <QSettings>
#include <QDebug>

#ifdef DYNAMIC_CREATION
    #include <QScrollArea>
    #include <QScrollBar>
#endif

static const int TICKS_NS = 500;

ButtonConfig::ButtonConfig(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::ButtonConfig)
{
    ui->setupUi(this);
    m_logicButtonInFocus = -1;
    // the HeliSR firmware polls its inputs on every pass: no polling intervals to set
    ui->frame_7->hide();
    // shifts are logical buttons; IN1-IN16 always exist, so they're always available
    for (QSpinBox *sb : {ui->spinBox_Shift1, ui->spinBox_Shift2, ui->spinBox_Shift3, ui->spinBox_Shift4, ui->spinBox_Shift5}) {
        sb->setMaximum(HSR_MAX_BUTTONS);
        sb->setEnabled(true);
    }

    // dynamic creation with scroll
#ifdef DYNAMIC_CREATION
    connect(ui->scrollArea_LogButtons->verticalScrollBar(), &QScrollBar::valueChanged, this, &ButtonConfig::logScrollValueChanged);
#else
    for (int i = 0; i < MAX_BUTTONS_NUM; i++) {
        ButtonLogical *logicalButtonsWidget = new ButtonLogical(i, this);
        ui->layoutV_LogicalButton->addWidget(logicalButtonsWidget);
        m_logicButtonPtrList.append(logicalButtonsWidget);
        connect(m_logicButtonPtrList[i], &ButtonLogical::functionTypeChanged,
                this, &ButtonConfig::functionTypeChanged);
    }
    gEnv.pAppSettings->beginGroup("OtherSettings");
    ui->checkBox_AutoPhysBut->setChecked(gEnv.pAppSettings->value("AutoSetPhysButton", true).toBool());
    gEnv.pAppSettings->endGroup();
    on_checkBox_AutoPhysBut_toggled(ui->checkBox_AutoPhysBut->isChecked());
#endif
    logicaButtonsCreator();

    connect(ui->spinBox_ButtonsPolling, qOverload<int>(&QSpinBox::valueChanged), this, &ButtonConfig::spinBoxStep);
    connect(ui->spinBox_EncoderPolling, qOverload<int>(&QSpinBox::valueChanged), this, &ButtonConfig::spinBoxStep);

    Q_ASSERT(ui->groupBox_LogicalButtons->objectName() == QStringLiteral("groupBox_LogicalButtons"));
    Q_ASSERT(ui->groupBox_PhysicalButtons->objectName() == QStringLiteral("groupBox_PhysicalButtons"));
}

ButtonConfig::~ButtonConfig()
{
    gEnv.pAppSettings->beginGroup("OtherSettings");
    gEnv.pAppSettings->setValue("AutoSetPhysButton", ui->checkBox_AutoPhysBut->isChecked());
    gEnv.pAppSettings->endGroup();
    delete ui;
}

void ButtonConfig::retranslateUi()
{
    ui->retranslateUi(this);
    for (int i = 0; i < m_logicButtonPtrList.size(); ++i) {
        m_logicButtonPtrList[i]->retranslateUi();
    }
}


#ifdef DYNAMIC_CREATION
void ButtonConfig::createLogButtons(int count)
{
    int size = m_logicButtonPtrList.size();
    for (int i = 0; i < count; i++) {
        if (size == MAX_BUTTONS_NUM) {
            break;
        }
        ButtonLogical *logical_buttons_widget = new ButtonLogical(size, this);
        ui->layoutV_LogicalButton->addWidget(logical_buttons_widget);
        m_logicButtonPtrList.append(logical_buttons_widget);
        //m_logicButtonPtrList[tmp]->setMinimumHeight(30);
        m_logicButtonPtrList[size]->initialization();

        connect(m_logicButtonPtrList[size], SIGNAL(functionIndexChanged(int, int, int)),
                this, SLOT(functionTypeChanged(int, int, int)));
        size++;
    }
}
void ButtonConfig::logScrollValueChanged(int value)
{
    // dynamic creation with scroll
    QScrollBar *scroll = ui->scrollArea_LogButtons->verticalScrollBar();
    int size = m_logicButtonPtrList.size();
    if (size != MAX_BUTTONS_NUM && (value / float(scroll->maximum())) >= 1.0f)
    {
        createLogButtons(4);
    }
}
void ButtonConfig::resizeEvent(QResizeEvent *event)
{
    Q_UNUSED(event)
    // dynamic creation with scroll
    QScrollBar *scroll = ui->scrollArea_LogButtons->verticalScrollBar();
    int size = m_logicButtonPtrList.size();
    if (isVisible() && scroll->isVisible() == false && size != MAX_BUTTONS_NUM)
    {
        createLogButtons(4);
    }
}
#endif
// dynamic creation of widgets. its decrease app startup time
void ButtonConfig::logicaButtonsCreator()
{
    static int tmp = 0;     //
    static QElapsedTimer timer;
    if (tmp >= MAX_BUTTONS_NUM) {
        qDebug() << "LogicaButtonsCreator() finished in"<<timer.elapsed()<<"ms";
        emit logicalButtonsCreated();
        return;
    }
    // как я понял таймер срабатывает после полной загрузки приложения(оно отобразится)
    // т.к. в LogicaButtonsCreator заходит при инициализации, но срабатывает после запуска приложения
    QTimer::singleShot(10, this, [&] {
        if (tmp == 0) {
            timer.start();
        }
        // dynamic creation with scroll
#ifdef DYNAMIC_CREATION
        createLogButtons(8);
        tmp += 8;
        ui->layoutV_LogicalButton->activate();
        // stop creating after QScrollBar is visible
        // 30 its ButtonLogical height
        #ifndef DYNAMIC_CREATION_ALL
        if (tmp * 30 > window()->height()) {
            qDebug() << "LogicaButtonsCreator() finished in"<<timer.elapsed()<<"ms";
            emit logicalButtonsCreated();
            return;
        }
        gEnv.pAppSettings->beginGroup("OtherSettings");
        ui->checkBox_AutoPhysBut->setChecked(gEnv.pAppSettings->value("AutoSetPhysButton", true).toBool());
        gEnv.pAppSettings->endGroup();
        on_checkBox_AutoPhysBut_toggled(ui->checkBox_AutoPhysBut->isChecked());
        #endif
#else
        // MAX_BUTTONS_NUM(128)/8 = 16 ДОЛЖНО ДЕЛИТЬСЯ БЕЗ ОСТАТКА
        for (int i = 0; i < MAX_BUTTONS_NUM; i++) // old value =8 // useless atm
        {
            m_logicButtonPtrList[tmp]->initialization();
            tmp++;
        }
#endif
        logicaButtonsCreator();
    });
}

// single step for spinbox
void ButtonConfig::spinBoxStep(int value)
{
    int remainder = value % TICKS_NS;
    QSpinBox *sb = qobject_cast<QSpinBox*>(sender());
    if (sb == nullptr || remainder == 0) return;

    value = (value / TICKS_NS) * TICKS_NS;
    if (remainder > TICKS_NS / 2) {
        sb->setValue(value + TICKS_NS);
    } else {
        sb->setValue(value);
    }
}

// set physical button for focused logical button
void ButtonConfig::setPhysicButton(int buttonIndex)
{
    if (m_autoPhysButEnabled) {
        int buttonInFocus = m_logicButtonPtrList[0]->currentFocus();
        if (buttonInFocus >= 0) {
            m_logicButtonPtrList[buttonInFocus]->setPhysicButton(buttonIndex);
        }
    }
}

void ButtonConfig::on_checkBox_AutoPhysBut_toggled(bool checked)
{
    m_autoPhysButEnabled = checked;
    m_logicButtonPtrList[0]->setAutoPhysBut(checked);
}

void ButtonConfig::physButtonsCreator(const QVector<HsrBoard::PhysInput> &inputs)
{
    for (ButtonPhysical *&p : m_physByNumber) {
        p = nullptr;
    }
    // delete all
    while (!m_PhysButtonPtrList.empty()) {
        QWidget *widget = m_PhysButtonPtrList.takeLast();
        ui->layoutG_PhysicalButton->removeWidget(widget);
        widget->deleteLater();
    }
    // add
    int row = 0;
    int column = 0;
    ui->layoutG_PhysicalButton->setAlignment(Qt::AlignTop);
    for (const HsrBoard::PhysInput &in : inputs) {
        if (column >= 8) // phys buttons column
        {
            row++;
            column = 0;
        }
        ButtonPhysical *physicalButtonWidget = new ButtonPhysical(in.phys, in.shortName, in.name, this);
        ui->layoutG_PhysicalButton->addWidget(physicalButtonWidget, row, column);
        m_PhysButtonPtrList.append(physicalButtonWidget);
        if (in.phys >= 0 && in.phys < HSR_MAX_PHYS) {
            m_physByNumber[in.phys] = physicalButtonWidget;
        }
        column++;
        connect(physicalButtonWidget, &ButtonPhysical::physButtonPressed, this, &ButtonConfig::setPhysicButton);
    }
}

void ButtonConfig::functionTypeChanged(button_type_t current, button_type_t previous, int buttonIndex)
{
    if (current == ENCODER_INPUT_A) {
        emit encoderInputChanged(buttonIndex + 1, 0);
    } else if (current == ENCODER_INPUT_B) {
        emit encoderInputChanged(0, buttonIndex + 1);
    }

    if (previous == ENCODER_INPUT_A) {
        emit encoderInputChanged((buttonIndex + 1) * -1, 0); // send negative number
    } else if (previous == ENCODER_INPUT_B) {
        emit encoderInputChanged(0, (buttonIndex + 1) * -1);
    }
    typeLimit(current, previous);
}

void ButtonConfig::typeLimit(button_type_t current, button_type_t previous)
{
    static int limitCountArray[m_typeLimCount]{};
    static bool limitIsEnable[m_typeLimCount]{};

    for (int i = 0; i < m_typeLimCount; ++i)
    {
        if (current == m_ButtonsTypeLimit[i].type)
        {
            limitCountArray[i]++;
        }
        if (previous == m_ButtonsTypeLimit[i].type)
        {
            limitCountArray[i]--;
        }

        if (limitCountArray[i] >= m_ButtonsTypeLimit[i].maxCount && limitIsEnable[i] == false)
        {
            limitIsEnable[i] = true;
            for (int j = 0; j < m_logicButtonPtrList.size(); ++j)
            {
                if (m_logicButtonPtrList[j]->currentButtonType() != current)
                {
                    m_logicButtonPtrList[j]->disableButtonType(current, true);
                }
            }
        }

        if (limitIsEnable[i] == true && limitCountArray[i] < m_ButtonsTypeLimit[i].maxCount)
        {
            limitIsEnable[i] = false;
            for (int j = 0; j < m_logicButtonPtrList.size(); ++j)
            {
                m_logicButtonPtrList[j]->disableButtonType(previous, false);
            }
        }
    }
}

void ButtonConfig::setPhysicalInputs(const QVector<HsrBoard::PhysInput> &inputs)
{
    for (int i = 0; i < m_logicButtonPtrList.size(); ++i) {
        m_logicButtonPtrList[i]->setPhysicalInputs(inputs);
    }
    physButtonsCreator(inputs);
}

void ButtonConfig::buttonStateChanged()
{
    const params_report_t *paramsRep = &gEnv.pDeviceConfig->paramsReport;

    // logical buttons state
    for (int i = 0; i < m_logicButtonPtrList.size() && i < HSR_MAX_BUTTONS; ++i) {
        m_logicButtonPtrList[i]->setButtonState(paramsRep->log_button_data[i / 8] & (1 << (i % 8)));
    }

    // physical inputs state
    for (int i = 0; i < HSR_MAX_PHYS; ++i) {
        if (m_physByNumber[i]) {
            m_physByNumber[i]->setButtonState(paramsRep->phy_button_data[i / 8] & (1 << (i % 8)));
        }
    }

    // shift state
    QLabel *shiftLabels[HSR_MAX_SHIFTS] = {ui->text_shift1_logicalButton, ui->text_shift2_logicalButton,
                                           ui->text_shift3_logicalButton, ui->text_shift4_logicalButton,
                                           ui->text_shift5_logicalButton};
    for (int i = 0; i < HSR_MAX_SHIFTS; ++i) {
        bool active = paramsRep->shift_button_data & (1 << i);
        if (active == m_shiftActive[i]) {
            continue;
        }
        if (m_defaultShiftStyle.isNull()) {
            m_defaultShiftStyle = shiftLabels[i]->styleSheet();
        }
        shiftLabels[i]->setStyleSheet(active ? m_defaultShiftStyle + "background-color: rgb(0, 128, 0);" : m_defaultShiftStyle);
        m_shiftActive[i] = active;
    }
}

void ButtonConfig::readFromConfig()
{
    dev_config_t *devc = &gEnv.pDeviceConfig->config;

    // dynamic creation with scroll
#ifdef DYNAMIC_CREATION
    for (int i = MAX_BUTTONS_NUM; i > 0; --i) {
        if (gEnv.pDeviceConfig->config.buttons[i -1].physical_num != -1) {
            int size = m_logicButtonPtrList.size();
            int count = i - size;
            createLogButtons(count);
            ui->layoutV_LogicalButton->activate();
            break;
        }
    }
#endif

    // logical buttons
    for (int i = 0; i < m_logicButtonPtrList.size(); i++) {
        m_logicButtonPtrList[i]->readFromConfig();
    }
    // other
    ui->spinBox_Shift1->setValue(devc->shift_config[0].button + 1);
    ui->spinBox_Shift2->setValue(devc->shift_config[1].button + 1);
    ui->spinBox_Shift3->setValue(devc->shift_config[2].button + 1);
    ui->spinBox_Shift4->setValue(devc->shift_config[3].button + 1);
    ui->spinBox_Shift5->setValue(devc->shift_config[4].button + 1);

    ui->spinBox_Timer1->setValue(devc->button_timer1_ms);
    ui->spinBox_Timer2->setValue(devc->button_timer2_ms);
    ui->spinBox_Timer3->setValue(devc->button_timer3_ms);

    ui->spinBox_DebounceTimer->setValue(devc->button_debounce_ms);
    ui->spinBox_A2bDebounce->setValue(devc->a2b_debounce_ms);

    ui->spinBox_EncoderPressTimer->setValue(devc->encoder_press_time_ms);

    ui->spinBox_ButtonsPolling->setValue(devc->button_polling_interval_ticks * TICKS_NS);
    ui->spinBox_EncoderPolling->setValue(devc->encoder_polling_interval_ticks * TICKS_NS);
}

void ButtonConfig::writeToConfig()
{
    dev_config_t *devc = &gEnv.pDeviceConfig->config;
    devc->shift_config[0].button = ui->spinBox_Shift1->value() - 1;
    devc->shift_config[1].button = ui->spinBox_Shift2->value() - 1;
    devc->shift_config[2].button = ui->spinBox_Shift3->value() - 1;
    devc->shift_config[3].button = ui->spinBox_Shift4->value() - 1;
    devc->shift_config[4].button = ui->spinBox_Shift5->value() - 1;

    devc->button_timer1_ms = ui->spinBox_Timer1->value();
    devc->button_timer2_ms = ui->spinBox_Timer2->value();
    devc->button_timer3_ms = ui->spinBox_Timer3->value();

    devc->button_debounce_ms = ui->spinBox_DebounceTimer->value();
    devc->a2b_debounce_ms = ui->spinBox_A2bDebounce->value();

    devc->encoder_press_time_ms = ui->spinBox_EncoderPressTimer->value();

    devc->button_polling_interval_ticks = ui->spinBox_ButtonsPolling->value() / TICKS_NS;
    devc->encoder_polling_interval_ticks = ui->spinBox_EncoderPolling->value() / TICKS_NS;

    // logical buttons
    for (int i = 0; i < m_logicButtonPtrList.size(); ++i) {
        m_logicButtonPtrList[i]->writeToConfig();
    }
}
