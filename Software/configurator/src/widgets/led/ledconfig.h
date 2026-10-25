#ifndef LEDCONFIG_H
#define LEDCONFIG_H

#include <QWidget>
#include "common_types.h"
#include "global.h"

class LED;
class QFrame;

namespace Ui {
class LedConfig;
}

// LEDs live on the spare Pro Micro pins: one on/off LED per pin set to "LED",
// and the four PWM channels on pins 5, 6, 9 and 10.
class LedConfig : public QWidget
{
    Q_OBJECT

public:
    explicit LedConfig(QWidget *parent = nullptr);
    ~LedConfig();

    void setLedsState();

    void readFromConfig();
    void writeToConfig();

    void retranslateUi();

public slots:
    //! the spare pin functions from the Board page
    void setPins(const pin_func_t *pins);

private:
    Ui::LedConfig *ui;

    QList<LED *> m_ledPtrList;      // by spare pin index
    QFrame *m_pwmFrames[HSR_MAX_PWM];

    void setEnabledTimers(bool enabled);
};

#endif // LEDCONFIG_H
