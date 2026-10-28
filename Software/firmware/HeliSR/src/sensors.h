/*
  sensors.h - HeliSR Rev 4.0: the AS5600s on AX1-AX4, through the PCA9546A

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HELISR_SENSORS_H
#define HELISR_SENSORS_H

#include <stdint.h>
#include "shared/helisr_protocol.h"

// Load the sensor settings (EEPROM, else defaults), start the bus at their
// clock, and visit every port once, so the first pass has readings.
void sensors_begin(void);

// Visit the next port: one port per call, in turn.
void sensors_poll(void);

// AX port n's angle, scaled to the analog sources' 0-HSR_RAW_MAX. A port that
// stops answering keeps its last reading (0 until it has answered once).
uint16_t sensors_value(uint8_t n);

void sensors_status(hsr_sensor_status_t *s);
const hsr_sensor_config_t *sensors_config(void);

// Check, save and apply new settings (the sensors get their new ranges on
// their next visits). HSR_OK, or HSR_ERR_VALUE with nothing changed.
uint8_t sensors_set_config(const hsr_sensor_config_t *c);

#endif
