#ifndef DEVICECONFIG_H
#define DEVICECONFIG_H

#include "common_defines.h"
#include "common_types.h"

class DeviceConfig
{
public:
    DeviceConfig();

    void resetConfig();

    dev_config_t config;
    params_report_t paramsReport;
    hsr_info_t info;            // from the connected device's INFO reply

    // Rev 4.0 boards: the AS5600 settings kept on the board (not part of a
    // profile), and their live status
    hsr_sensor_config_t sensorConfig;
    hsr_sensor_status_t sensorStatus;
};

#endif // DEVICECONFIG_H
