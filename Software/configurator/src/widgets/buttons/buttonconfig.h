#ifndef BUTTONCONFIG_H
#define BUTTONCONFIG_H

#include <QWidget>

#include "buttonlogical.h"
#include "buttonphysical.h"

#include "common_defines.h"
#include "common_types.h"

#include "deviceconfig.h"
#include "global.h"
#include "helisrboard.h"

//#define DYNAMIC_CREATION
#ifdef DYNAMIC_CREATION
    //#define DYNAMIC_CREATION_ALL
#endif
namespace Ui {
class ButtonConfig;
}

class ButtonConfig : public QWidget
{
    Q_OBJECT

public:
    explicit ButtonConfig(QWidget *parent = nullptr);
    ~ButtonConfig();

    void readFromConfig();
    void writeToConfig();
    void buttonStateChanged();

    void retranslateUi();

signals:
    void encoderInputChanged(int ecoder_A, int ecoder_B);
    void logicalButtonsCreated();

public slots:
    //! the physical inputs that exist with the current board settings
    void setPhysicalInputs(const QVector<HsrBoard::PhysInput> &inputs);

private slots:
    void functionTypeChanged(button_type_t current, button_type_t previous, int buttonIndex);
    void setPhysicButton(int buttonIndex);
    void typeLimit(button_type_t current, button_type_t previous);

#ifdef DYNAMIC_CREATION
private slots:
    void logScrollValueChanged(int value);
    void createLogButtons(int count);
protected:
    void resizeEvent(QResizeEvent *event) override;
#endif

    void on_checkBox_AutoPhysBut_toggled(bool checked);

private:
    Ui::ButtonConfig *ui;
    void physButtonsCreator(const QVector<HsrBoard::PhysInput> &inputs);
    QString m_defaultShiftStyle;

    int m_logicButtonInFocus;
    bool m_autoPhysButEnabled;

    bool m_shiftActive[HSR_MAX_SHIFTS] = {};

    void logicaButtonsCreator();

    void spinBoxStep(int value);

    QList<ButtonLogical *> m_logicButtonPtrList;
    QList<ButtonPhysical *> m_PhysButtonPtrList;
    ButtonPhysical *m_physByNumber[HSR_MAX_PHYS] = {};

    struct pinTypeLimit_t
    {
        button_type_t type;
        int maxCount;
    };

    static const int m_typeLimCount = 2;
    const pinTypeLimit_t m_ButtonsTypeLimit[m_typeLimCount] =
    {
        {ENCODER_INPUT_A,        HSR_MAX_ENCODERS},
        {ENCODER_INPUT_B,        HSR_MAX_ENCODERS},
    };
};

#endif // BUTTONCONFIG_H
