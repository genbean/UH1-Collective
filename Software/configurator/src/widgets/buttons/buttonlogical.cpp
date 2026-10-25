#include "buttonlogical.h"
#include "ui_buttonlogical.h"

#include "widgets/debugwindow.h"
#include "converter.h"

int ButtonLogical::m_currentFocus = -1;
bool ButtonLogical::m_autoPhysButEnabled = false;

ButtonLogical::ButtonLogical(int buttonIndex, QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::ButtonLogical)
{
    ui->setupUi(this);
    m_buttonIndex = buttonIndex;
    m_functionPrevType = BUTTON_NORMAL;
    m_currentState = false;
    m_debugState = false;
    ui->label_LogicalButtonNumber->setNum(m_buttonIndex + 1);
    ui->comboBox_PhysicalInput->addItem("-", -1);
    ui->comboBox_PhysicalInput->installEventFilter(this);
}

ButtonLogical::~ButtonLogical()
{
    delete ui;
}

void ButtonLogical::retranslateUi()
{
    ui->retranslateUi(this);
}

void ButtonLogical::initialization()
{
    // add gui text
    m_logicFunc_enumIndex.reserve(m_logicFunctionList.size());
    for (int i = 0; i < m_logicFunctionList.size(); i++) {
//        // Encoder only for first 30 buttons  // if uncomment DONT FORGET EDIT MainWindow::oldConfigHandler() !!!!!!!!
//        if (m_buttonNumber > 29 &&
//                (m_logicFunctionList[i].deviceEnumIndex == ENCODER_INPUT_A ||
//                 m_logicFunctionList[i].deviceEnumIndex == ENCODER_INPUT_B)) {
//            continue;
//        }
        ui->comboBox_ButtonFunction->addItem(m_logicFunctionList[i].guiName);
        m_logicFunc_enumIndex.push_back(m_logicFunctionList[i].deviceEnumIndex);
        if (m_logicFunctionList[i].deviceEnumIndex == SWITCH_CENTER) {
            ui->comboBox_ButtonFunction->setItemData(i, tr("On while its input and the next input (for example IN5 and IN6) "
                                                           "are both off: the middle position of an ON-OFF-ON switch."),
                                                     Qt::ToolTipRole);
        }
    }
    for (int i = 0; i < SHIFT_COUNT; i++) {
        ui->comboBox_ShiftIndex->addItem(m_shiftList[i].guiName);
    }
    for (int i = 0; i < TIMER_COUNT; i++) {
        ui->comboBox_DelayTimerIndex->addItem(m_timerList[i].guiName);
        ui->comboBox_PressTimerIndex->addItem(m_timerList[i].guiName);
    }

    connect(ui->comboBox_ButtonFunction, SIGNAL(currentIndexChanged(int)),
            this, SLOT(functionIndexChanged(int)));
    connect(ui->comboBox_PhysicalInput, qOverload<int>(&QComboBox::currentIndexChanged),
            this, &ButtonLogical::physicalInputChanged);
    physicalInputChanged(ui->comboBox_PhysicalInput->currentIndex());
}

void ButtonLogical::setPhysicalInputs(const QVector<HsrBoard::PhysInput> &inputs)
{
    QComboBox *cb = ui->comboBox_PhysicalInput;
    int current = cb->currentData().toInt();
    {
        QSignalBlocker blocker(cb);
        cb->clear();
        cb->addItem("-", -1);
        for (const HsrBoard::PhysInput &in : inputs) {
            cb->addItem(in.name, in.phys);
        }
        int index = cb->findData(current);
        cb->setCurrentIndex(index < 0 ? 0 : index);
    }
    physicalInputChanged(cb->currentIndex());
}

void ButtonLogical::functionIndexChanged(int index)
{
    int type = m_logicFunctionList[index].deviceEnumIndex;
    emit functionTypeChanged(type, m_functionPrevType, m_buttonIndex);
    m_functionPrevType = type;
}

void ButtonLogical::physicalInputChanged(int index)
{
    if (ui->comboBox_PhysicalInput->itemData(index).toInt() >= 0) {
        ui->checkBox_IsInvert->setEnabled(true);
        ui->checkBox_IsDisable->setEnabled(true);
        ui->comboBox_ButtonFunction->setEnabled(true);
        ui->comboBox_ShiftIndex->setEnabled(true);
        ui->comboBox_DelayTimerIndex->setEnabled(true);
        ui->comboBox_PressTimerIndex->setEnabled(true);
    } else {
        ui->checkBox_IsInvert->setEnabled(false);
        ui->checkBox_IsDisable->setEnabled(false);
        ui->comboBox_ButtonFunction->setEnabled(false);
        ui->comboBox_ShiftIndex->setEnabled(false);
        ui->comboBox_DelayTimerIndex->setEnabled(false);
        ui->comboBox_PressTimerIndex->setEnabled(false);
    }
}

void ButtonLogical::setButtonState(bool state)
{
    if (state != m_currentState) {
        setAutoFillBackground(true);

        if (state) {
            QPalette pal(window()->palette());
            pal.setColor(QPalette::Window, QColor(0, 128, 0));
            setPalette(pal);

            m_lastAct.start();
            m_currentState = state;
        } else {
            // sometimes state dont have time to render. e.g. encoder press time 10ms and monitor refresh time 17ms(60fps)
            if (m_lastAct.hasExpired(30)) {
                setPalette(window()->palette());
                m_currentState = state;
            }
        }
    }
    // debug shows real state without a timer for rendering
    if (state != m_debugState) {
        if (state) {
            if (gEnv.pDebugWindow) {
                gEnv.pDebugWindow->logicalButtonState(ui->label_LogicalButtonNumber->text().toInt(), true);
            }
        } else {
            if (gEnv.pDebugWindow) {
                gEnv.pDebugWindow->logicalButtonState(ui->label_LogicalButtonNumber->text().toInt(), false);
            }
        }
        m_debugState = state;
    }
}

void ButtonLogical::setPhysicButton(int phys)
{
    int index = ui->comboBox_PhysicalInput->findData(phys);
    if (index >= 0) {
        ui->comboBox_PhysicalInput->setCurrentIndex(index);
    }
}

int ButtonLogical::currentFocus() const
{
    return m_currentFocus;
}

void ButtonLogical::setAutoPhysBut(bool enabled)
{
    m_autoPhysButEnabled = enabled;
}


void ButtonLogical::disableButtonType(button_type_t type, bool disable)
{
    int CBoxIndex = Converter::EnumToIndex(type, m_logicFunc_enumIndex);
    if (disable == false){
        ui->comboBox_ButtonFunction->setItemData(CBoxIndex, 1 | 32, Qt::UserRole - 1);
    } else {
        ui->comboBox_ButtonFunction->setItemData(CBoxIndex, 0, Qt::UserRole - 1);
    }
}

button_type_t ButtonLogical::currentButtonType()
{
    return m_logicFunc_enumIndex[ui->comboBox_ButtonFunction->currentIndex()];
}


bool ButtonLogical::eventFilter(QObject *obj, QEvent *event)
{
    Q_UNUSED(obj)
    if (m_autoPhysButEnabled) {
        if (event->type() == QEvent::FocusIn) {
            ui->comboBox_PhysicalInput->setStyleSheet("background-color: rgba(0, 120, 215, 200); color: rgb(255, 255, 255)");
            m_currentFocus = m_buttonIndex;
        } else if (event->type() == QEvent::FocusOut){
            ui->comboBox_PhysicalInput->setStyleSheet("");
            m_currentFocus = -1;
        }
    }
    return false;
}

void ButtonLogical::readFromConfig()
{
    button_t *button = &gEnv.pDeviceConfig->config.buttons[m_buttonIndex];
    // physical
    int index = ui->comboBox_PhysicalInput->findData(int(button->physical_num));
    ui->comboBox_PhysicalInput->setCurrentIndex(index < 0 ? 0 : index);
    // isDisable
    ui->checkBox_IsDisable->setChecked(button->is_disabled);
    // isInvert
    ui->checkBox_IsInvert->setChecked(button->is_inverted);

    // logical button function
    ui->comboBox_ButtonFunction->setCurrentIndex(Converter::EnumToIndex(button->type, m_logicFunc_enumIndex));
    // shift
    for (int i = 0; i < SHIFT_COUNT; i++) {
        if (button->shift_modificator == m_shiftList[i].deviceEnumIndex) {
            ui->comboBox_ShiftIndex->setCurrentIndex(i);
            break;
        }
    }
    // delay timer
    for (int i = 0; i < TIMER_COUNT; i++) {
        if (button->delay_timer == m_timerList[i].deviceEnumIndex) {
            ui->comboBox_DelayTimerIndex->setCurrentIndex(i);
            break;
        }
    }
    // toggle timer
    for (int i = 0; i < TIMER_COUNT; i++) {
        if (button->press_timer == m_timerList[i].deviceEnumIndex) {
            ui->comboBox_PressTimerIndex->setCurrentIndex(i);
            break;
        }
    }
}

void ButtonLogical::writeToConfig()
{
    button_t *button = &gEnv.pDeviceConfig->config.buttons[m_buttonIndex];

    button->physical_num = int8_t(ui->comboBox_PhysicalInput->currentData().toInt());
    button->is_disabled = ui->checkBox_IsDisable->isChecked();
    button->is_inverted = ui->checkBox_IsInvert->isChecked();

    button->type = m_logicFunc_enumIndex[ui->comboBox_ButtonFunction->currentIndex()];
    button->shift_modificator = m_shiftList[ui->comboBox_ShiftIndex->currentIndex()].deviceEnumIndex;
    button->delay_timer = m_timerList[ui->comboBox_DelayTimerIndex->currentIndex()].deviceEnumIndex;
    button->press_timer = m_timerList[ui->comboBox_PressTimerIndex->currentIndex()].deviceEnumIndex;
}
