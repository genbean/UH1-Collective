/*
  sim.h - runs the firmware's logic on the PC, one millisecond per pass

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HSR_SIM_H
#define HSR_SIM_H

#include <stdint.h>
#include <stdio.h>
#include "../../HeliSR/src/shared/helisr_config.h"
#include "../../HeliSR/src/shared/helisr_protocol.h"
#include "../../HeliSR/src/settings.h"
#include "../../HeliSR/src/pipeline.h"
#include "../../HeliSR/src/joy_layout.h"
#include "../../HeliSR/src/logic.h"

// ------------------------------------------------------------- checking --

extern int g_pass, g_fail;
extern const char *g_scenario;

#define CHECK(cond) do { if (cond) g_pass++; else { g_fail++; \
	printf("  FAIL  %s (line %d): %s\n", g_scenario, __LINE__, #cond); } } while (0)

#define CHECK_EQ(a, b) do { long long _a = (long long)(a), _b = (long long)(b); \
	if (_a == _b) g_pass++; else { g_fail++; \
	printf("  FAIL  %s (line %d): %s == %s  (got %lld, want %lld)\n", g_scenario, __LINE__, #a, #b, _a, _b); } } while (0)

#define CHECK_NEAR(a, b, tol) do { long long _a = (long long)(a), _b = (long long)(b); \
	if (_a >= _b - (tol) && _a <= _b + (tol)) g_pass++; else { g_fail++; \
	printf("  FAIL  %s (line %d): %s ~ %s +-%d  (got %lld, want %lld)\n", g_scenario, __LINE__, #a, #b, (int)(tol), _a, _b); } } while (0)

// ------------------------------------------------------------ simulator --

struct Sim
{
	uint16_t now;
	uint16_t sr;                        // bit n = IN(n+1) closed
	uint16_t spare;                     // bit n = spare pin n pressed
	uint16_t analog[HSR_ANALOG_SOURCES];
	hsr_test_result_t r;                // results of the last pass (as the device returns them)
	JoyLayout L;

	// Start the logic from g_config, at the given time.
	void begin(uint16_t start_ms = 1000);
	// Run passes, one millisecond apart.
	void step(int ms = 1);

	void in(int n, bool closed) { if (closed) sr |= (uint16_t)(1u << (n - 1)); else sr &= (uint16_t)~(1u << (n - 1)); }

	bool log(int j) const { return (r.log_buttons[j >> 3] >> (j & 7)) & 1; }
	bool phy(int p) const { return (r.phy_buttons[p >> 3] >> (p & 7)) & 1; }
	int16_t axis(int i) const { return r.axes[i]; }
	uint8_t pov(int k) const { return r.povs[k]; }
	bool led(int i) const { return (r.leds >> i) & 1; }
	int report(uint8_t *out) const { return pipeline_report(&L, out); }

	// Step until pred() is true; return the ms it took, or -1 after max_ms.
	template <class F> int until(F pred, int max_ms)
	{
		for (int t = 0; t <= max_ms; t++)
		{
			if (pred()) return t;
			step();
		}
		return -1;
	}
	// Step for ms and return true if pred() held on every pass.
	template <class F> bool holds(F pred, int ms)
	{
		for (int t = 0; t < ms; t++)
		{
			step();
			if (!pred()) return false;
		}
		return true;
	}
};

// Start a scenario: factory settings, and a heading.
void scenario(const char *name);

// The stand-in EEPROM (stubs/avr/eeprom.h).
extern uint8_t host_eeprom[1024];

// Trace for replaying on the Pro Micro (hsr-lockstep.ps1); NULL = off.
extern FILE *g_trace;

#endif
