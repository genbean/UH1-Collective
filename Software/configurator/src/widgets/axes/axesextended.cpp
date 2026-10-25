#include "axesextended.h"
#include "ui_axesextended.h"

#include "converter.h"
#include "axes.h"

AxesExtended::AxesExtended(int axisNumber, QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::AxesExtended)
{
    ui->setupUi(this);

    m_axisNumber = axisNumber;

    // no I2C sensors on HeliSR (its I2C pins drive the shift registers)
    ui->comboBox_I2cAddress->hide();
    ui->text_i2cAddress->hide();
    // the encoder an "Encoder" axis follows, numbered as on the Encoders page
    ui->spinBox_ChanelEncoder->setRange(1, HSR_MAX_ENCODERS);
    for (QSpinBox *sb : {ui->spinBox_Button1, ui->spinBox_Button2, ui->spinBox_Button3}) {
        sb->setMaximum(HSR_MAX_BUTTONS);
    }
    // function
    m_function_enumIndex.reserve(m_functionList.size());
    for (int i = 0; i < m_functionList.size(); ++i) {
        ui->comboBox_Function->addItem(m_functionList[i].guiName);
        m_function_enumIndex.push_back(m_functionList[i].deviceEnumIndex);
    }
    // button 1 and 3
    m_button_1_3_enumIndex.reserve(m_button_1_3_list.size());
    for (int i = 0; i < m_button_1_3_list.size(); ++i) {
        ui->comboBox_Button1->addItem(m_button_1_3_list[i].guiName);
        ui->comboBox_Button3->addItem(m_button_1_3_list[i].guiName);
        m_button_1_3_enumIndex.push_back(m_button_1_3_list[i].deviceEnumIndex);
    }
    // button 2
    m_button_2_enumIndex.reserve(m_button_2_list.size());
    for (int i = 0; i < m_button_2_list.size(); ++i) {
        ui->comboBox_Button2->addItem(m_button_2_list[i].guiName);
        m_button_2_enumIndex.push_back(m_button_2_list[i].deviceEnumIndex);
    }
    // function axis
    for (int i = 0; i < axesList().size(); ++i) {
        ui->comboBox_AxisSource2->addItem(axesList()[i].guiName);
    }

    ui->comboBox_Button1->setCurrentIndex(AXIS_BUTTON_DOWN);
    ui->comboBox_Button2->setCurrentIndex(AXIS_BUTTON_RESET);
    ui->comboBox_Button3->setCurrentIndex(AXIS_BUTTON_UP);

    // set filter text
    ui->label_Filter->setText(tr("Filter") + " " + m_filterList[ui->sliderH_Filter->value()].guiName);

    // filter changed
    connect(ui->sliderH_Filter, &QSlider::valueChanged, this, &AxesExtended::filterChanged);
    // function changed
    connect(ui->comboBox_Function, qOverload<int>(&QComboBox::currentIndexChanged),
            this, &AxesExtended::functionIndexChanged);
}

AxesExtended::~AxesExtended()
{
    delete ui;
}

void AxesExtended::retranslateUi()
{
    ui->retranslateUi(this);
}

void AxesExtended::filterChanged(int filterLevel)
{
    ui->label_Filter->setText(tr("Filter") + " " + m_filterList[filterLevel].guiName);
}

void AxesExtended::functionIndexChanged(int index)
{
    if (index > 0) {
        ui->comboBox_AxisSource2->setEnabled(true);
    } else {
        ui->comboBox_AxisSource2->setEnabled(false);
    }
}

void AxesExtended::readFromConfig()
{
    axis_config_t *axisCfg = &gEnv.pDeviceConfig->config.axis_config[m_axisNumber];
    // sources, function
    ui->comboBox_AxisSource2->setCurrentIndex(Converter::EnumToIndex(axisCfg->source_secondary, axesList()));
    ui->comboBox_Function->setCurrentIndex(Converter::EnumToIndex(axisCfg->function, m_function_enumIndex));
    // chanel
    ui->spinBox_ChanelEncoder->setValue(axisCfg->channel + 1);
    // buttons
    ui->comboBox_Button1->setCurrentIndex(Converter::EnumToIndex(axisCfg->button1_type, m_button_1_3_enumIndex));
    ui->spinBox_Button1->setValue(axisCfg->button1 + 1);
    ui->comboBox_Button2->setCurrentIndex(Converter::EnumToIndex(axisCfg->button2_type, m_button_2_enumIndex));
    ui->spinBox_Button2->setValue(axisCfg->button2 + 1);
    ui->comboBox_Button3->setCurrentIndex(Converter::EnumToIndex(axisCfg->button3_type, m_button_1_3_enumIndex));
    ui->spinBox_Button3->setValue(axisCfg->button3 + 1);
    // divider, prescaler
    ui->spinBox_StepDiv->setValue(axisCfg->divider);
    ui->spinBox_Prescaler->setValue(axisCfg->prescaler);
    // resolution, offset
    ui->spinBox_Resolution->setValue(axisCfg->resolution + 1);
    ui->spinBox_Offset->setValue(axisCfg->offset_angle * 15);
    //deadband
    ui->checkBox_DynDeadband->setChecked(axisCfg->is_dynamic_deadband);
    ui->spinBox_Deadband->setValue(axisCfg->deadband_size);
    // filter
    ui->sliderH_Filter->setValue(axisCfg->filter);
}

void AxesExtended::writeToConfig()
{
    axis_config_t *axisCfg = &gEnv.pDeviceConfig->config.axis_config[m_axisNumber];
    // sources, function
    axisCfg->source_secondary = axesList()[ui->comboBox_AxisSource2->currentIndex()].deviceEnumIndex;
    axisCfg->function = m_functionList[ui->comboBox_Function->currentIndex()].deviceEnumIndex;
    // chanel
    axisCfg->channel = ui->spinBox_ChanelEncoder->value() - 1;
    // buttons
    axisCfg->button1_type = m_button_1_3_list[ui->comboBox_Button1->currentIndex()].deviceEnumIndex;
    axisCfg->button1 = ui->spinBox_Button1->value() - 1;
    axisCfg->button2_type = m_button_2_list[ui->comboBox_Button2->currentIndex()].deviceEnumIndex;
    axisCfg->button2 = ui->spinBox_Button2->value() - 1;
    axisCfg->button3_type = m_button_1_3_list[ui->comboBox_Button3->currentIndex()].deviceEnumIndex;
    axisCfg->button3 = ui->spinBox_Button3->value() - 1;
    // divider, prescaler
    axisCfg->divider = ui->spinBox_StepDiv->value();
    axisCfg->prescaler = ui->spinBox_Prescaler->value();
    // resolution, offset
    axisCfg->resolution = ui->spinBox_Resolution->value() - 1;
    axisCfg->offset_angle = ui->spinBox_Offset->value() / 15;
    // deadband
    axisCfg->is_dynamic_deadband = ui->checkBox_DynDeadband->isChecked();
    axisCfg->deadband_size = ui->spinBox_Deadband->value();
    // filter
    axisCfg->filter = ui->sliderH_Filter->value();
}
