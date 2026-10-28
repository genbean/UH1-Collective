/*
  pipeline.cpp - one pass of the logic, from raw inputs to report data

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  The order follows FreeJoy's: the physical inputs (axis-to-button ranges come
  from the previous pass's axes), encoders, debounce, logical buttons, axes
  (whose buttons use the logical states), LEDs.
*/

#include <string.h>
#include "pipeline.h"
#include "logic.h"

void pipeline_init(void)
{
	buttons_init();
	axes_init();
	leds_init();
}

void pipeline_step(uint16_t sr_inputs, uint16_t spare_buttons, const uint16_t *analog, uint16_t now)
{
	for (uint8_t i = 0; i < HSR_SR_INPUTS; i++) bit_put(raw_bits, HSR_PHYS_SR_FIRST + i, (sr_inputs >> i) & 1);
	for (uint8_t i = 0; i < HSR_SPARE_PINS; i++) bit_put(raw_bits, HSR_PHYS_SPARE_FIRST + i, (spare_buttons >> i) & 1);
	uint8_t a2b_end = a2b_get(scaled_axis_data);

	encoders_process(now);
	buttons_debounce(now, a2b_end);
	buttons_logical(now);
	axes_process(analog, now);
	leds_process(now);
}

uint8_t pipeline_report(const JoyLayout *L, uint8_t *out)
{
	uint8_t buttons[HSR_MAX_BUTTONS / 8];
	uint8_t povs[HSR_MAX_POVS];
	buttons_get(buttons, NULL, NULL, povs, NULL);

	uint8_t pos = (L->buttons + 7) / 8;
	memcpy(out, buttons, pos);
	for (uint8_t i = 0; i < L->axes; i++)
	{
		analog_data_t v = axis_out(L->axis_index[i]);
		out[pos++] = (uint8_t)v;
		out[pos++] = (uint8_t)((uint16_t)v >> 8);
	}
	for (uint8_t i = 0; i < L->povs; i++) out[pos++] = povs[i];
	return pos;
}

void pipeline_params(params_report_t *p, const uint16_t *analog)
{
	p->firmware_version = HSR_FIRMWARE_VERSION;
	memcpy(p->raw_axis_data, raw_axis_data, sizeof(raw_axis_data));
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++) p->axis_data[i] = axis_out(i);
	memcpy(p->analog_inputs, analog, sizeof(p->analog_inputs));
#if HSR_BOARD_SOURCES > 9
	memcpy(p->analog_inputs_a2a3, analog + 9, sizeof(p->analog_inputs_a2a3));
#else
	memset(p->analog_inputs_a2a3, 0, sizeof(p->analog_inputs_a2a3));
#endif
	buttons_get(NULL, p->log_button_data, p->phy_button_data, NULL, &p->shift_button_data);
}
