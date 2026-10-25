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
};

#endif // DEVICECONFIG_H
