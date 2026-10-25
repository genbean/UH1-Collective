/*
  random_settings.h - random settings and inputs for the comparison with
  FreeJoy and for the random part of the Pro Micro lockstep trace

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HSR_RANDOM_SETTINGS_H
#define HSR_RANDOM_SETTINGS_H

#include <stdint.h>

struct Rng
{
	uint32_t s;
	uint32_t next() { s ^= s << 13; s ^= s >> 17; s ^= s << 5; return s; }
	int range(int lo, int hi) { return lo + (int)(next() % (uint32_t)(hi - lo + 1)); }
	bool chance(int percent) { return range(0, 99) < percent; }
};

// Random settings in g_config, avoiding the cases where HeliSR deliberately
// differs from FreeJoy (see freejoy_compare.cpp).
void random_settings(Rng &R);

// The next pass's random inputs: occasional flips, sometimes bouncing, and
// analog wander with occasional jumps (sources 0-7).
void random_inputs(Rng &R, uint32_t &raw27, uint16_t *analog);

// Run n random scenarios of ms passes through HeliSR's logic only (for the
// lockstep trace; the comparison with FreeJoy has its own loop).
void run_random_scenarios(int n, int ms);

#endif
