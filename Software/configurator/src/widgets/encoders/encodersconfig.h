#ifndef ENCODERSCONFIG_H
#define ENCODERSCONFIG_H

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
    int m_encodersInput_A_count;
    int m_encodersInput_B_count;
    QString m_notDefined;
};

#endif // ENCODERSCONFIG_H
