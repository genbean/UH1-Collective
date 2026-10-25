/*
  joy_layout.cpp - which buttons, axes and hats the joystick report carries

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <string.h>
#include "joy_layout.h"

void joy_plan(JoyLayout *L, const dev_config_t *cfg)
{
	memset(L, 0, sizeof(*L));

	L->buttons = hsr_reported_buttons(cfg);
	for (uint8_t m = hsr_pov_mask(cfg); m; m >>= 1) L->povs += m & 1;
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
		if (cfg->axis_config[i].out_enabled) L->axis_index[L->axes++] = i;

	// A joystick with no inputs at all isn't valid HID: keep one button.
	if (!L->buttons && !L->axes && !L->povs) L->buttons = 1;

	L->report_size = (L->buttons + 7) / 8 + 2 * L->axes + L->povs;
}
