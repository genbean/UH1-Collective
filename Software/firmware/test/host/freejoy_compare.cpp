/*
  freejoy_compare.cpp - runs HeliSR's logic and FreeJoy's original code side
  by side on random settings and random inputs, and reports any difference

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Kept out of the random settings, because HeliSR deliberately differs there
  (see the headers of buttons.cpp and axes.cpp):
    - SWITCH_CENTER (HeliSR only);
    - sequential buttons in three or more groups (FreeJoy's start-up bug);
    - an axis-to-button debounce different from the button debounce (FreeJoy
      applies it one input off);
    - analog source 8 (FreeJoy has 8 analog pins).
  Built with HSR_RAW_MAX = 4095, FreeJoy's analog range.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sim.h"
#include "freejoy/fj_bridge.h"
#include "random_settings.h"

#define CFG g_config

static void load_into_freejoy()
{
	fjb_reset();
	fjb_set_common(CFG.button_debounce_ms, CFG.a2b_debounce_ms, CFG.encoder_press_time_ms,
	               CFG.button_timer1_ms, CFG.button_timer2_ms, CFG.button_timer3_ms);
	for (int j = 0; j < HSR_MAX_BUTTONS; j++)
	{
		const button_t *b = &CFG.buttons[j];
		fjb_set_button(j, b->physical_num, b->type, b->shift_modificator, b->is_inverted, b->is_disabled, b->delay_timer, b->press_timer);
	}
	for (int i = 0; i < HSR_MAX_SHIFTS; i++) fjb_set_shift(i, CFG.shift_config[i].button);
	for (int i = 0; i < HSR_MAX_AXES; i++) fjb_set_a2b(i, CFG.axes_to_buttons[i].points, CFG.axes_to_buttons[i].buttons_cnt);
	// FreeJoy's slow encoders are numbered from 1 (0 is its timer encoder)
	for (int k = 0; k < HSR_MAX_ENCODERS; k++) fjb_set_encoder_mode(k + 1, CFG.encoders[k]);
	for (int i = 0; i < HSR_MAX_AXES; i++)
	{
		const axis_config_t *a = &CFG.axis_config[i];
		fjb_axis_t f;
		f.calib_min = a->calib_min; f.calib_center = a->calib_center; f.calib_max = a->calib_max;
		f.out_enabled = a->out_enabled; f.inverted = a->inverted; f.is_centered = a->is_centered;
		f.function = a->function; f.filter = a->filter;
		memcpy(f.curve, a->curve_shape, 11);
		f.resolution = a->resolution;
		f.channel = (a->source_main == SOURCE_ENCODER) ? a->channel + 1 : a->channel;
		f.deadband_size = a->deadband_size; f.is_dynamic_deadband = a->is_dynamic_deadband;
		f.source_main = a->source_main; f.source_secondary = a->source_secondary; f.offset_angle = a->offset_angle;
		f.button1 = a->button1; f.button2 = a->button2; f.button3 = a->button3;
		f.divider = a->divider; f.prescaler = a->prescaler;
		f.button1_type = a->button1_type; f.button2_type = a->button2_type; f.button3_type = a->button3_type;
		fjb_set_axis(i, &f);
	}
	fjb_start();
}

int g_verbose;

static void explain(const uint8_t *log, const uint8_t *flog, const int16_t *faxes, uint16_t now)
{
	for (int j = 0; j < HSR_MAX_BUTTONS; j++)
	{
		int a = (log[j >> 3] >> (j & 7)) & 1, b = (flog[j >> 3] >> (j & 7)) & 1;
		if (a == b) continue;
		const button_t *bt = &CFG.buttons[j];
		const log_state_t *st = &log_state[j];
		int c, p, on, off, cur, act, tl;
		fjb_get_button_detail(j, &c, &p, &on, &off, &cur, &act, &tl);
		printf("        button %d: phys %d type %d shift %d inv %d dis %d delay %d press %d\n", j, bt->physical_num, bt->type,
		       bt->shift_modificator, bt->is_inverted, bt->is_disabled, bt->delay_timer, bt->press_timer);
		printf("          HeliSR  curr %d prev %d on %d off %d cur %d act %d t %d (now %u)\n", st->curr_physical_state,
		       st->prev_physical_state, st->on_state, st->off_state, st->current_state, st->delay_act, st->time_last, now);
		printf("          FreeJoy curr %d prev %d on %d off %d cur %d act %d t %d\n", c, p, on, off, cur, act, tl);
	}
	int16_t fraw[8], fscaled[8];
	fjb_get_axes_detail(fraw, fscaled);
	for (int i = 0; i < 8; i++)
	{
		if (axis_out(i) == faxes[i] && scaled_axis_data[i] == fscaled[i]) continue;
		const axis_config_t *a = &CFG.axis_config[i];
		bool linear = true;
		for (int p = 0; p < 11; p++) linear = linear && a->curve_shape[p] == (int8_t)(p * 20 - 100);
		printf("        axis %d: src %d ch %d calib %d/%d/%d out %d inv %d cent %d fn %d/%d filt %d %s res %d db %d dyn %d off %d"
		       " btn %d:%d %d:%d %d:%d div %d presc %d\n",
		       i, a->source_main, a->channel, a->calib_min, a->calib_center, a->calib_max, a->out_enabled, a->inverted, a->is_centered,
		       a->function, a->source_secondary, a->filter, linear ? "linear" : "curve", a->resolution, a->deadband_size,
		       a->is_dynamic_deadband, a->offset_angle, a->button1, a->button1_type, a->button2, a->button2_type, a->button3,
		       a->button3_type, a->divider, a->prescaler);
		printf("          raw %d vs %d, scaled %d vs %d, out %d vs %d\n", raw_axis_data[i], fraw[i], scaled_axis_data[i], fscaled[i],
		       axis_out(i), faxes[i]);
	}
}

static void hexbits(const uint8_t *b, int n, char *out)
{
	for (int i = 0; i < n; i++) sprintf(out + 2 * i, "%02X", b[i]);
}

// Run one random scenario; returns 0 if every pass matched.
static int run_one(uint32_t seed, int ms)
{
	Rng R{ seed * 2654435761u + 1 };
	random_settings(R);
	load_into_freejoy();
	pipeline_init();
	JoyLayout L;
	joy_plan(&L, &CFG);
	uint8_t pov_mask = hsr_pov_mask(&CFG);

	uint32_t raw = 0;
	uint16_t analog[HSR_ANALOG_SOURCES];
	for (int s = 0; s < HSR_ANALOG_SOURCES; s++) analog[s] = (s < 8) ? (uint16_t)R.range(0, HSR_RAW_MAX) : 0;

	for (int t = 1; t <= ms; t++)
	{
		uint16_t now = (uint16_t)(1000 + t);

		random_inputs(R, raw, analog);
		pipeline_step((uint16_t)(raw & 0xFFFF), (uint16_t)(raw >> 16), analog, now);
		fjb_step(1000 + t, raw, analog);

		uint8_t log[8], phy[8], out[8], pov[4], shift;
		buttons_get(out, log, phy, pov, &shift);
		uint8_t flog[16], fphy[16], fout[16], fpov[4]; int16_t faxes[8]; uint8_t fshift;
		fjb_get(flog, fphy, fout, fpov, faxes, &fshift);

		char what[160] = "";
		char a[40], b[40];
		if (memcmp(phy, fphy, 8)) { hexbits(phy, 8, a); hexbits(fphy, 8, b); snprintf(what, sizeof(what), "physical %s vs %s", a, b); }
		else if (memcmp(log, flog, 8)) { hexbits(log, 8, a); hexbits(flog, 8, b); snprintf(what, sizeof(what), "logical %s vs %s", a, b); }
		else if (shift != fshift) snprintf(what, sizeof(what), "shift %u vs %u", shift, fshift);
		else
		{
			int nbytes = (L.buttons + 7) / 8;
			uint8_t mask = (L.buttons & 7) ? (uint8_t)((1 << (L.buttons & 7)) - 1) : 0xFF;
			for (int k = 0; k < nbytes && !what[0]; k++)
			{
				uint8_t m = (k == nbytes - 1) ? mask : 0xFF;
				if ((out[k] & m) != (fout[k] & m))
					snprintf(what, sizeof(what), "reported buttons byte %d: %02X vs %02X", k, out[k] & m, fout[k] & m);
			}
			int n = 0;
			for (int g = 0; g < 4 && !what[0]; g++)
				if (pov_mask & (1 << g))
				{
					if (pov[n] != fpov[g]) snprintf(what, sizeof(what), "hat %d: %u vs %u", g + 1, pov[n], fpov[g]);
					n++;
				}
			for (int i = 0; i < 8 && !what[0]; i++)
			{
				int d = axis_out(i) - faxes[i];
				if (d < -1 || d > 1) snprintf(what, sizeof(what), "axis %d: %d vs %d", i, axis_out(i), faxes[i]);
			}
		}
		if (what[0])
		{
			g_fail++;
			printf("  FAIL  seed %u, pass %d: %s (HeliSR vs FreeJoy)\n", seed, t, what);
			if (g_verbose) explain(log, flog, faxes, now);
			return 1;
		}
	}
	g_pass++;
	return 0;
}

void run_freejoy_comparison()
{
	int scenarios = 400;
	const int ms = 3000;
	if (getenv("HSR_SCENARIOS")) scenarios = atoi(getenv("HSR_SCENARIOS"));
	if (getenv("HSR_SEED"))         // one seed, with details of the first difference
	{
		g_verbose = 1;
		run_one((uint32_t)atoi(getenv("HSR_SEED")), ms);
		return;
	}
	g_scenario = "FreeJoy comparison";
	printf("FreeJoy comparison: %d random settings x %d ms, HeliSR and FreeJoy's own code in lockstep\n", scenarios, ms);
	int failed = 0;
	for (int s = 1; s <= scenarios; s++) failed += run_one((uint32_t)s, ms);
	printf("  %d of %d scenarios identical\n", scenarios - failed, scenarios);
}
