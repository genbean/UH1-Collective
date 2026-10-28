#include "encodersconfig.h"
#include "ui_encodersconfig.h"
#include <algorithm>

// HeliSR has no hardware-timer ("fast") encoder: all encoders are polled
// ones, numbered from 0 as in the firmware.

EncodersConfig::EncodersConfig(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::EncodersConfig)
{
    ui->setupUi(this);
    m_notDefined = tr("Not defined");
    ui->groupBox_FastEncoder->hide();

    ui->layoutV_Encoders->setAlignment(Qt::AlignTop);
    // encoders spawn
    for (int i = 0; i < MAX_ENCODERS_NUM; i++)
    {
        Encoders * encoder = new Encoders(i, this);
        ui->layoutV_Encoders->addWidget(encoder);
        m_encodersPtrList.append(encoder);
    }
}

EncodersConfig::~EncodersConfig()
{
    delete ui;
}

void EncodersConfig::retranslateUi()
{
    ui->retranslateUi(this);
    for (int i = 0; i < m_encodersPtrList.size(); ++i) {
        m_encodersPtrList[i]->retranslateUi();
    }
}

// The buttons set to encoder input A and B, each kept in button order: the
// n-th A and the n-th B make encoder n, as in the firmware. FreeJoy kept only
// the first eight of each in the rows, so while settings load one button at a
// time (and a ninth A briefly exists) it read past the rows and crashed; the
// full lists don't.
void EncodersConfig::encoderInputChanged(int encoder_A, int encoder_B)
{
    auto update = [](QVector<int> &inputs, int change) {
        if (change > 0) {
            inputs.insert(std::lower_bound(inputs.begin(), inputs.end(), change), change);
        } else if (change < 0) {
            inputs.removeOne(-change);
        }
    };
    update(m_inputsA, encoder_A);
    update(m_inputsB, encoder_B);
    for (int i = 0; i < m_encodersPtrList.size(); ++i) {
        m_encodersPtrList[i]->setInputA(i < m_inputsA.size() ? m_inputsA[i] : 0);
        m_encodersPtrList[i]->setInputB(i < m_inputsB.size() ? m_inputsB[i] : 0);
    }
}

void EncodersConfig::readFromConfig()
{
    for (int i = 0; i < MAX_ENCODERS_NUM; i++)
    {
        m_encodersPtrList[i]->readFromConfig();
    }
}

void EncodersConfig::writeToConfig()
{
    for (int i = 0; i < MAX_ENCODERS_NUM; i++)
    {
        m_encodersPtrList[i]->writeToConfig();
    }
}
