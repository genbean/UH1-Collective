/*
  sim.cpp - runs the firmware's logic on the PC, plus the few board and
  Arduino functions the logic files call

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <string.h>
#include "sim.h"

int g_pass, g_fail;
const char *g_scenario = "";
FILE *g_trace;

// ---------------------------------------------- stand-ins for the board --

uint8_t host_eeprom[1024];
unsigned long millis(void) { return 0; }
unsigned long micros(void) { return 12345; }
int analogRead(uint8_t pin) { return pin * 7; }

void board_set_led(uint8_t, uint8_t) { }
void board_set_pwm(uint8_t, uint8_t) { }

// -------------------------------------------------------------- tracing --

static void hex(FILE *f, const void *p, size_t n)
{
	const uint8_t *b = (const uint8_t *)p;
	for (size_t i = 0; i < n; i++) fprintf(f, "%02X", b[i]);
}

void scenario(const char *name)
{
	g_scenario = name;
	printf("%s\n", name);
	settings_defaults(&g_config);
}

void Sim::begin(uint16_t start_ms)
{
	pipeline_init();
	joy_plan(&L, &g_config);
	now = start_ms;
	sr = spare = 0;
	memset(analog, 0, sizeof(analog));
	memset(&r, 0, sizeof(r));
	if (g_trace)
	{
		fprintf(g_trace, "scenario %s\nconfig ", g_scenario);
		hex(g_trace, &g_config, sizeof(g_config));
		fprintf(g_trace, "\n");
	}
}

void Sim::step(int ms)
{
	while (ms-- > 0)
	{
		now++;
		pipeline_step(sr, spare, analog, now);

		memset(&r, 0, sizeof(r));
		buttons_get(NULL, r.log_buttons, r.phy_buttons, r.povs, &r.shifts);
		for (uint8_t i = 0; i < HSR_MAX_AXES; i++) r.axes[i] = axis_out(i);
		r.leds = leds_get(r.pwm);

		if (g_trace)
		{
			hsr_test_step_t in;
			in.now = now;
			in.sr_inputs = sr;
			in.spare_buttons = spare;
			memcpy(in.analog, analog, sizeof(in.analog));
			fprintf(g_trace, "step ");
			hex(g_trace, &in, sizeof(in));
			fprintf(g_trace, " ");
			hex(g_trace, &r, sizeof(r));
			fprintf(g_trace, "\n");
		}
	}
}
