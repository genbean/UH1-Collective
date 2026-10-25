/*
  helisr_defaults.h - factory settings, shared by the HeliSR firmware and HeliSR Configurator

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy).
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  The firmware loads these when its EEPROM holds no valid settings, and the
  configurator's "Reset all" loads the same ones, so the two always agree.
*/

#ifndef HELISR_DEFAULTS_H
#define HELISR_DEFAULTS_H

#include <string.h>
#include "helisr_config.h"
#include "helisr_protocol.h"

static inline void hsr_config_defaults(dev_config_t *cfg)
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
		a->source_main = (i < HSR_AX_INPUTS) ? (axis_source_t)i : (axis_source_t)SOURCE_NO;
		for (uint8_t p = 0; p < 11; p++) a->curve_shape[p] = (int8_t)(p * 20 - 100);
		a->resolution = 15;
		a->button1 = a->button2 = a->button3 = -1;
		a->divider = 50;
		a->prescaler = 100;
		a->button1_type = AXIS_BUTTON_DOWN;
		a->button2_type = AXIS_BUTTON_RESET;
		a->button3_type = AXIS_BUTTON_UP;
	}

	// Buttons: IN1-IN16 are buttons 1-16; the rest are unassigned.
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
		cfg->buttons[i].physical_num = (i < HSR_SR_INPUTS) ? (int8_t)(HSR_PHYS_SR_FIRST + i) : -1;

	for (uint8_t i = 0; i < HSR_MAX_AXES; i++) cfg->axes_to_buttons[i].points[1] = 255;
	for (uint8_t i = 0; i < HSR_MAX_SHIFTS; i++) cfg->shift_config[i].button = -1;
	for (uint8_t i = 0; i < HSR_MAX_ENCODERS; i++) cfg->encoders[i] = ENCODER_CONF_2x;
	for (uint8_t i = 0; i < HSR_MAX_LEDS; i++)
	{
		cfg->leds[i].input_num = -1;
		cfg->leds[i].timer = 15;        // steady
	}
	for (uint8_t i = 0; i < HSR_MAX_PWM; i++) cfg->led_pwm_config[i].duty_cycle = 50;
	for (uint8_t i = 0; i < 4; i++) cfg->led_timer_ms[i] = 50 * (i + 1);
}

#endif
