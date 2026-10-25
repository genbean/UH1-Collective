/*
  process.h - turns the board's inputs into buttons, axes and hats

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  The logic itself is FreeJoy's, ported in buttons.cpp, axes.cpp and leds.cpp.
*/

#ifndef HELISR_PROCESS_H
#define HELISR_PROCESS_H

#include <stdint.h>
#include "shared/helisr_config.h"

void process_init(void);

// Read the inputs, run the logic and build the joystick report.
void process_run(uint32_t now_ms);

// The joystick report with its report ID first, laid out per HeliUSB().layout().
const uint8_t *process_report(void);

void process_params(params_report_t *p);

#endif
