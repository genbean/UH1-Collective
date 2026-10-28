/*
  main.cpp - HeliSR PC test program
    hsr_host_tests                 run the scenario tests
    hsr_host_tests --trace FILE    also write a trace for hsr-lockstep.ps1,
                                   which replays it on a Pro Micro
    hsr_host_tests --random N      also run N random scenarios (3 s each),
                                   e.g. to add them to the trace

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sim.h"
#include "random_settings.h"

void run_unit_tests();
void run_sensor_tests();
#ifdef HSR_WITH_FREEJOY
void run_freejoy_comparison();
#endif

int main(int argc, char **argv)
{
	int random_n = 0;
	for (int i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "--trace") && i + 1 < argc)
		{
			g_trace = fopen(argv[++i], "w");
			if (!g_trace) { printf("can't write %s\n", argv[i]); return 2; }
		}
		else if (!strcmp(argv[i], "--random") && i + 1 < argc)
			random_n = atoi(argv[++i]);
	}

	run_unit_tests();
	run_sensor_tests();
	if (random_n) run_random_scenarios(random_n, 3000);
#ifdef HSR_WITH_FREEJOY
	run_freejoy_comparison();
#endif

	if (g_trace) fclose(g_trace);
	printf("\n%d checks passed, %d failed\n", g_pass, g_fail);
	return g_fail ? 1 : 0;
}
