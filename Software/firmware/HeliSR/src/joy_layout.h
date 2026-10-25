/*
  joy_layout.h - which buttons, axes and hats the joystick report carries

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HELISR_JOY_LAYOUT_H
#define HELISR_JOY_LAYOUT_H

#include <stdint.h>
#include "shared/helisr_config.h"

struct JoyLayout
{
	uint8_t buttons;                    // number of buttons reported (0-64)
	uint8_t axes;                       // number of axes reported (0-8)
	uint8_t axis_index[HSR_MAX_AXES];   // which axis_config entry each reported axis is
	uint8_t povs;                       // number of hats (0-4)
	uint8_t report_size;                // bytes after the report ID
};

#define HSR_MAX_REPORT_SIZE  ((HSR_MAX_BUTTONS + 7) / 8 + 2 * HSR_MAX_AXES + HSR_MAX_POVS)

// Plan the report from the settings: the reported buttons packed in order,
// the enabled axes in order, the used hats in order.
void joy_plan(JoyLayout *L, const dev_config_t *cfg);

#endif
