#include "helisrboard.h"
#include <QCoreApplication>

namespace
{
    const char *const SPARE_LABELS[HSR_SPARE_PINS] = {"TX", "RX", "4", "5", "6", "7", "8", "9", "10", "14", "16"};
    const int PWM_SPARE[HSR_MAX_PWM] = {3, 4, 7, 8};                                   // pins 5, 6, 9, 10
    const int ANALOG_SPARE[HSR_ANALOG_SOURCES] = {-1, -1, -1, -1, 2, 4, 6, 7, 8};       // pins 4, 6, 8, 9, 10
    const char *const AXIS_SHORT[HSR_MAX_AXES] = {"X", "Y", "Z", "Rx", "Ry", "Rz", "S1·", "S2·"};

    QString tr(const char *text)
    {
        return QCoreApplication::translate("HsrBoard", text);
    }
}

QString HsrBoard::spareLabel(int spareIndex)
{
    if (spareIndex < 0 || spareIndex >= HSR_SPARE_PINS) return QString();
    return SPARE_LABELS[spareIndex];
}

QString HsrBoard::spareName(int spareIndex)
{
    return tr("Pin %1").arg(spareLabel(spareIndex));
}

bool HsrBoard::spareIsAnalog(int spareIndex)
{
    return spareIndex >= 0 && spareIndex < HSR_SPARE_PINS && (HSR_SPARE_ANALOG_MASK & (1u << spareIndex));
}

bool HsrBoard::spareIsPwm(int spareIndex)
{
    return spareIndex >= 0 && spareIndex < HSR_SPARE_PINS && (HSR_SPARE_PWM_MASK & (1u << spareIndex));
}

int HsrBoard::pwmChannelOfSpare(int spareIndex)
{
    for (int c = 0; c < HSR_MAX_PWM; ++c) {
        if (PWM_SPARE[c] == spareIndex) return c;
    }
    return -1;
}

int HsrBoard::spareOfPwmChannel(int channel)
{
    return (channel >= 0 && channel < HSR_MAX_PWM) ? PWM_SPARE[channel] : -1;
}

int HsrBoard::analogSourceOfSpare(int spareIndex)
{
    for (int s = HSR_AX_INPUTS; s < HSR_ANALOG_SOURCES; ++s) {
        if (ANALOG_SPARE[s] == spareIndex) return s;
    }
    return -1;
}

int HsrBoard::spareOfAnalogSource(int source)
{
    return (source >= 0 && source < HSR_ANALOG_SOURCES) ? ANALOG_SPARE[source] : -1;
}

QString HsrBoard::analogSourceName(int source)
{
    if (source >= 0 && source < HSR_AX_INPUTS) return QStringLiteral("AX%1").arg(source + 1);
    return spareName(spareOfAnalogSource(source));
}

bool HsrBoard::analogSourceAvailable(int source, const pin_func_t *pins)
{
    if (source >= 0 && source < HSR_AX_INPUTS) return true;
    int spare = spareOfAnalogSource(source);
    return spare >= 0 && pins[spare] == PIN_AXIS_ANALOG;
}

QString HsrBoard::axisName(int axis)
{
    static const char *const names[HSR_MAX_AXES] = {"X", "Y", "Z", "Rx", "Ry", "Rz", "Slider 1", "Slider 2"};
    if (axis < 0 || axis >= HSR_MAX_AXES) return QString();
    return axis < 6 ? QString(names[axis]) : QCoreApplication::translate("Axes", names[axis]);
}

QVector<HsrBoard::PhysInput> HsrBoard::physicalInputs(const pin_func_t *pins, const int *a2bCounts)
{
    QVector<PhysInput> list;
    for (int i = 0; i < HSR_SR_INPUTS; ++i) {
        QString name = QStringLiteral("IN%1").arg(i + 1);
        list.append({HSR_PHYS_SR_FIRST + i, name, name});
    }
    for (int i = 0; i < HSR_SPARE_PINS; ++i) {
        if (pins[i] == PIN_BUTTON_GND || pins[i] == PIN_BUTTON_VCC) {
            list.append({HSR_PHYS_SPARE_FIRST + i, spareName(i), spareLabel(i)});
        }
    }
    // axis ranges are numbered on from 27 in axis order, as the firmware does
    int pos = HSR_PHYS_A2B_FIRST;
    for (int a = 0; a < HSR_MAX_AXES; ++a) {
        int cnt = qBound(0, a2bCounts[a], HSR_A2B_POINTS - 1);
        for (int j = 0; j < cnt && pos < HSR_MAX_PHYS; ++j, ++pos) {
            list.append({pos, tr("%1 range %2").arg(axisName(a)).arg(j + 1),
                         QString(AXIS_SHORT[a]) + QString::number(j + 1)});
        }
    }
    return list;
}

QString HsrBoard::physicalInputName(int phys, const pin_func_t *pins, const int *a2bCounts)
{
    for (const PhysInput &in : physicalInputs(pins, a2bCounts)) {
        if (in.phys == phys) return in.name;
    }
    return QString();
}
