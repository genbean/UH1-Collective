#ifndef CONFIGTOFILE_H
#define CONFIGTOFILE_H

#include <QObject>

class QSettings;
#include "common_types.h"

// Profiles: the whole device setup in an INI file, so a setup can be kept,
// shared and loaded onto another board (for example the UH-1 collective's).
class ConfigToFile : public QObject
{
    Q_OBJECT
public:
    //! false if the file isn't a HeliSR profile (devC is left as it was)
    static bool loadDeviceConfigFromFile(QWidget *parent, const QString &fileName, dev_config_t &devC);
    static void saveDeviceConfigToFile(const QString &fileName, dev_config_t &devC);

private:
    static void sanitize(dev_config_t &devC);
};

#endif // CONFIGTOFILE_H
