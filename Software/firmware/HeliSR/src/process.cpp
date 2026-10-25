/*
  process.cpp - one pass of the firmware: read the board, run the pipeline,
  build the joystick report

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <Arduino.h>
#include <string.h>
#include "process.h"
#include "pipeline.h"
#include "board.h"
#include "usb_helisr.h"
#include "shared/helisr_protocol.h"

static uint16_t analog[HSR_ANALOG_SOURCES];
static uint8_t report[1 + HSR_MAX_REPORT_SIZE];     // report ID, then the report

void process_init(void)
{
	pipeline_init();
}

void process_run(uint32_t now_ms)
{
	uint16_t sr = board_read_inputs();
	uint16_t spare = board_read_spare_buttons();
	board_read_analog(analog);
	pipeline_step(sr, spare, analog, (uint16_t)now_ms);

	// Built in place: the report goes out every exchange period anyway, so
	// there's no copy to compare with (saves stack).
	report[0] = HSR_REPORT_JOY;
	pipeline_report(&HeliUSB().layout(), &report[1]);
}

const uint8_t *process_report(void)
{
	return report;
}

void process_params(params_report_t *p)
{
	pipeline_params(p, analog);
}
