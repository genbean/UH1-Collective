#include "deviceconfig.h"
#include "shared/helisr_defaults.h"

DeviceConfig::DeviceConfig()
{
    hsr_config_defaults(&config);
    paramsReport = {};
    info = {};
    sensorConfig = {};
    sensorStatus = {};
    sensorDebug = {};
}

void DeviceConfig::resetConfig()
{
    hsr_config_defaults(&config);
}
