/*
  settings.h - the device settings: factory defaults and EEPROM storage

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HELISR_SETTINGS_H
#define HELISR_SETTINGS_H

#include <stdint.h>
#include "shared/helisr_config.h"

extern dev_config_t g_config;

// Load the settings from EEPROM, or the factory defaults if there are none or
// they don't check out. Safe to call before setup(): the USB descriptors need
// the settings as soon as the PC starts enumerating.
void settings_begin(void);

void settings_defaults(dev_config_t *cfg);
uint8_t settings_load(void);        // 1 = loaded from EEPROM
void settings_save(void);
uint8_t settings_from_eeprom(void);

// Random per-board number, made on first start and kept in EEPROM. Used as the
// USB serial number so Windows can tell two HeliSR boards apart.
// settings_make_unique_id() uses analogRead(): call it in setup(), after the
// core's init() and before board_init() takes over the ADC.
void settings_make_unique_id(void);
uint32_t settings_unique_id(void);

#endif
