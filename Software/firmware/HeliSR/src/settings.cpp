/*
  settings.cpp - the device settings: factory defaults and EEPROM storage

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy).
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  EEPROM layout (1024 bytes):
    0-1   magic 'H','S'
    2-3   size of dev_config_t
    4-5   CRC-16 of the settings
    6-    dev_config_t
    1020-1023  unique board ID
*/

#include <Arduino.h>
#include <avr/eeprom.h>
#include <string.h>
#include "settings.h"
#include "shared/helisr_protocol.h"
#include "shared/helisr_defaults.h"

dev_config_t g_config;

static uint8_t loaded_from_eeprom;

#define EE_MAGIC        ((uint16_t *)0)
#define EE_SIZE         ((uint16_t *)2)
#define EE_CRC          ((uint16_t *)4)
#define EE_CONFIG       ((void *)6)
#define EE_UNIQUE_ID    ((uint32_t *)1020)
#define MAGIC           0x5348      // "HS"

static_assert(6 + sizeof(dev_config_t) <= 1020, "settings don't fit in EEPROM");

void settings_defaults(dev_config_t *cfg)
{
	hsr_config_defaults(cfg);
}

uint8_t settings_load(void)
{
	if (eeprom_read_word(EE_MAGIC) != MAGIC || eeprom_read_word(EE_SIZE) != sizeof(dev_config_t))
		return 0;
	eeprom_read_block(&g_config, EE_CONFIG, sizeof(dev_config_t));
	if (hsr_crc16((const uint8_t *)&g_config, sizeof(dev_config_t)) != eeprom_read_word(EE_CRC) ||
	    g_config.config_version != HSR_CONFIG_VERSION)
		return 0;
	return 1;
}

void settings_save(void)
{
	// eeprom_update_* only writes bytes that changed, which saves time and wear.
	eeprom_update_block(&g_config, EE_CONFIG, sizeof(dev_config_t));
	eeprom_update_word(EE_SIZE, sizeof(dev_config_t));
	eeprom_update_word(EE_CRC, hsr_crc16((const uint8_t *)&g_config, sizeof(dev_config_t)));
	eeprom_update_word(EE_MAGIC, MAGIC);
	loaded_from_eeprom = 1;
}

void settings_begin(void)
{
	loaded_from_eeprom = settings_load();
	if (!loaded_from_eeprom) settings_defaults(&g_config);
}

uint8_t settings_from_eeprom(void)
{
	return loaded_from_eeprom;
}

static uint32_t unique_id;

void settings_make_unique_id(void)
{
	uint32_t id = eeprom_read_dword(EE_UNIQUE_ID);
	if (id == 0xFFFFFFFFUL || id == 0)
	{
		// Mix the floating ADC's noise with the timer: different on every board.
		id = 0x48535231UL;
		for (uint8_t i = 0; i < 32; i++)
		{
			id = (id << 5) ^ (id >> 27) ^ (uint32_t)analogRead(A0 + (i & 3)) ^ micros();
		}
		if (id == 0xFFFFFFFFUL || id == 0) id = 0x1234ABCDUL;
		eeprom_update_dword(EE_UNIQUE_ID, id);
	}
	unique_id = id;
}

uint32_t settings_unique_id(void)
{
	return unique_id ? unique_id : eeprom_read_dword(EE_UNIQUE_ID);
}
