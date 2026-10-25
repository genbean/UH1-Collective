/*
  pipeline.h - one pass of the logic, from raw inputs to report data

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  No USB and no board access (apart from the LED outputs), so the same code
  runs in the firmware, in the PC test program, and in the firmware's test
  build driven by the PC.
*/

#ifndef HELISR_PIPELINE_H
#define HELISR_PIPELINE_H

#include <stdint.h>
#include "shared/helisr_config.h"
#include "joy_layout.h"

// (Re)start the logic from the current settings (g_config).
void pipeline_init(void);

// One pass. sr_inputs: bit n = IN(n+1) closed; spare_buttons: bit n = spare
// pin n pressed; analog: the 9 analog sources (0-HSR_RAW_MAX); now: ms.
void pipeline_step(uint16_t sr_inputs, uint16_t spare_buttons, const uint16_t *analog, uint16_t now);

// The joystick report (without its report ID). Returns its size.
uint8_t pipeline_report(const JoyLayout *L, uint8_t *out);

// Live data for the configurator.
void pipeline_params(params_report_t *p, const uint16_t *analog);

#endif
