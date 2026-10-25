/*
  random_settings.cpp - random settings and inputs (see random_settings.h)

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <stdio.h>
#include <string.h>
#include "sim.h"
#include "random_settings.h"

#define CFG g_config

void random_settings(Rng &R)
{
	settings_defaults(&CFG);
	static const uint16_t debounces[] = { 0, 5, 20, 50 };
	CFG.button_debounce_ms = debounces[R.range(0, 3)];
	CFG.a2b_debounce_ms = CFG.button_debounce_ms;
	CFG.encoder_press_time_ms = (uint8_t)R.range(5, 60);
	CFG.button_timer1_ms = (uint16_t)R.range(10, 300);
	CFG.button_timer2_ms = (uint16_t)R.range(10, 300);
	CFG.button_timer3_ms = (uint16_t)R.range(10, 300);

	int encoders_a = 0;
	for (int j = 0; j < HSR_MAX_BUTTONS; j++)
	{
		button_t *b = &CFG.buttons[j];
		memset(b, 0, sizeof(*b));
		b->physical_num = R.chance(35) ? -1 : (R.chance(80) ? R.range(0, 26) : R.range(HSR_PHYS_A2B_FIRST, HSR_PHYS_A2B_FIRST + 8));
		uint8_t type = R.chance(40) ? BUTTON_NORMAL : (uint8_t)R.range(0, SEQUENTIAL_BUTTON);
		if (type == ENCODER_INPUT_A && ++encoders_a > HSR_MAX_ENCODERS) type = BUTTON_NORMAL;
		if (type == SEQUENTIAL_BUTTON) b->physical_num = (int8_t)R.range(0, 1);
		// An encoder input with no input assigned makes FreeJoy read
		// raw_buttons_data[-1]; nothing meaningful to compare.
		if ((type == ENCODER_INPUT_A || type == ENCODER_INPUT_B) && b->physical_num < 0) b->physical_num = (int8_t)R.range(0, 26);
		b->type = type;
		b->shift_modificator = R.chance(85) ? 0 : R.range(1, 5);
		b->is_inverted = R.chance(15);
		b->is_disabled = R.chance(5);
		b->delay_timer = R.chance(75) ? 0 : R.range(1, 3);
		b->press_timer = R.chance(75) ? 0 : R.range(1, 3);
	}
	for (int i = 0; i < HSR_MAX_SHIFTS; i++) CFG.shift_config[i].button = R.chance(30) ? (int8_t)R.range(0, 63) : -1;

	for (int i = 0; i < HSR_MAX_AXES; i++)
	{
		axis_to_buttons_t *a2b = &CFG.axes_to_buttons[i];
		memset(a2b, 0, sizeof(*a2b));
		if (i < 3 && R.chance(40))
		{
			a2b->buttons_cnt = (uint8_t)R.range(1, 5);
			int p = R.range(0, 30);
			for (int k = 0; k <= a2b->buttons_cnt; k++)
			{
				a2b->points[k] = (uint8_t)p;
				p += R.range(10, 60);
				if (p > 255) p = 255;
			}
		}
	}
	for (int k = 0; k < HSR_MAX_ENCODERS; k++) CFG.encoders[k] = (uint8_t)R.range(0, 2);

	for (int i = 0; i < HSR_MAX_AXES; i++)
	{
		axis_config_t *a = &CFG.axis_config[i];
		memset(a, 0, sizeof(*a));
		int r = R.range(0, 99);
		a->source_main = r < 15 ? SOURCE_NO : r < 85 ? (int8_t)R.range(0, 7) : SOURCE_ENCODER;
		a->channel = (uint8_t)R.range(0, 7);
		a->calib_min = (int16_t)R.range(-32767, -1000);
		a->calib_max = (int16_t)R.range(1000, 32767);
		a->calib_center = (int16_t)R.range(a->calib_min + 1, a->calib_max - 1);
		a->out_enabled = R.chance(80);
		a->inverted = R.chance(30);
		a->is_centered = R.chance(30);
		a->function = R.chance(80) ? NO_FUNCTION : R.range(1, 3);
		a->filter = R.chance(60) ? FILTER_NO : R.range(1, 7);
		bool linear = R.chance(60);
		for (int p = 0; p < 11; p++) a->curve_shape[p] = linear ? (int8_t)(p * 20 - 100) : (int8_t)R.range(-100, 100);
		a->resolution = R.chance(60) ? 15 : R.range(4, 14);
		a->deadband_size = R.chance(60) ? 0 : R.range(1, 127);
		a->is_dynamic_deadband = R.chance(20);
		a->source_secondary = R.range(0, 7);
		a->offset_angle = (a->source_main >= 0 && R.chance(20)) ? R.range(1, 23) : 0;
		a->button1 = R.chance(70) ? -1 : (int8_t)R.range(0, 63);
		a->button2 = R.chance(70) ? -1 : (int8_t)R.range(0, 63);
		a->button3 = R.chance(70) ? -1 : (int8_t)R.range(0, 63);
		a->button1_type = R.range(0, 5);
		a->button2_type = R.range(0, 3);
		a->button3_type = R.range(0, 5);
		a->divider = (uint8_t)R.range(1, 100);
		a->prescaler = R.chance(60) ? 100 : (uint8_t)R.range(0, 200);
	}
	// FreeJoy's encoder code reads buttons[-1] for unused encoder slots: the
	// three bytes before the button table, axis 7's button types, prescaler
	// and spare byte. A button-3 type of 2 or more makes that stray "input
	// number" 64 or more, so it can't match a real input and suppress a click.
	CFG.axis_config[7].button3_type = R.range(2, 5);
}


void random_inputs(Rng &R, uint32_t &raw, uint16_t *analog)
{
	for (int i = 0; i < 27; i++)
		if (R.range(0, 149) == 0) raw ^= 1u << i;
	if (R.range(0, 299) == 0) raw ^= 1u << R.range(0, 26);
	for (int s = 0; s < 8; s++)
	{
		int v = analog[s] + R.range(-30, 30);
		if (R.range(0, 499) == 0) v = R.range(0, HSR_RAW_MAX);
		analog[s] = (uint16_t)(v < 0 ? 0 : v > HSR_RAW_MAX ? HSR_RAW_MAX : v);
	}
}

void run_random_scenarios(int n, int ms)
{
	for (int k = 1; k <= n; k++)
	{
		char name[48];
		snprintf(name, sizeof(name), "random settings %d", k);
		Rng R{ (uint32_t)k * 2654435761u + 1 };
		scenario(name);
		random_settings(R);
		Sim s;
		s.begin();
		uint32_t raw = 0;
		for (int a = 0; a < 8; a++) s.analog[a] = (uint16_t)R.range(0, HSR_RAW_MAX);
		for (int t = 0; t < ms; t++)
		{
			random_inputs(R, raw, s.analog);
			s.sr = (uint16_t)(raw & 0xFFFF);
			s.spare = (uint16_t)(raw >> 16);
			s.step();
		}
	}
}
