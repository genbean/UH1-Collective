#ifndef ENCODERSCONFIG_H
#define ENCODERSCONFIG_H

#include <QVector>
#include <QWidget>

#include "deviceconfig.h"
#include "encoders.h"
#include "global.h"

namespace Ui {
class EncodersConfig;
}

class EncodersConfig : public QWidget
{
    Q_OBJECT

public:
    explicit EncodersConfig(QWidget *parent = nullptr);
    ~EncodersConfig();

    void readFromConfig();
    void writeToConfig();

    void retranslateUi();

public slots:
    void encoderInputChanged(int encoder_A, int encoder_B);

private:
    Ui::EncodersConfig *ui;

    QList<Encoders *> m_encodersPtrList;
    QVector<int> m_inputsA;         // button numbers (from 1) set to ENCODER_INPUT_A, in order
    QVector<int> m_inputsB;         // ... ENCODER_INPUT_B
    QString m_notDefined;
};

#endif // ENCODERSCONFIG_H
