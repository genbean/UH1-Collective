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
	memset(cfg, 0, sizeof(*cfg));

	cfg->config_version = HSR_CONFIG_VERSION;
	strncpy(cfg->device_name, HSR_DEFAULT_NAME, HSR_NAME_LEN);
	cfg->button_debounce_ms = 20;
	cfg->encoder_press_time_ms = 20;
	cfg->exchange_period_ms = 5;
	cfg->button_timer1_ms = 50;
	cfg->button_timer2_ms = 200;
	cfg->button_timer3_ms = 300;
	cfg->a2b_debounce_ms = 50;
	cfg->button_polling_interval_ticks = 1;
	cfg->encoder_polling_interval_ticks = 1;
	cfg->vid = HSR_DEFAULT_VID;
	cfg->pid = HSR_DEFAULT_PID;

	// Axes: AX1-AX4 drive X, Y, Z and Rx; the other four outputs are off.
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
	{
		axis_config_t *a = &cfg->axis_config[i];
		a->calib_min = AXIS_MIN_VALUE;
		a->calib_center = AXIS_CENTER_VALUE;
		a->calib_max = AXIS_MAX_VALUE;
		a->out_enabled = (i < HSR_AX_INPUTS);
		a->source_main = (i < HSR_AX_INPUTS) ? (axis_source_t)i : SOURCE_NO;
		for (uint8_t p = 0; p < 11; p++) a->curve_shape[p] = (int8_t)(p * 20 - 100);
		a->resolution = 15;
		a->button1 = a->button2 = a->button3 = -1;
		a->divider = 50;
		a->button1_type = AXIS_BUTTON_DOWN;
		a->button2_type = AXIS_BUTTON_RESET;
		a->button3_type = AXIS_BUTTON_UP;
	}

	// Buttons: IN1-IN16 are buttons 1-16; the rest are unassigned.
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
		cfg->buttons[i].physical_num = (i < HSR_SR_INPUTS) ? (int8_t)(HSR_PHYS_SR_FIRST + i) : -1;

	for (uint8_t i = 0; i < HSR_MAX_SHIFTS; i++) cfg->shift_config[i].button = -1;
	for (uint8_t i = 0; i < HSR_MAX_LEDS; i++) cfg->leds[i].input_num = -1;
	for (uint8_t i = 0; i < HSR_MAX_PWM; i++) cfg->led_pwm_config[i].duty_cycle = 50;
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
