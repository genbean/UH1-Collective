/*
  logic.h - state shared by the button, encoder, axis and LED logic

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy),
  application/Inc/common_types.h, buttons.h, analog.h, encoders.h.
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Differences from FreeJoy that apply throughout:
    - times are 16-bit milliseconds (FreeJoy: 32-bit), to save RAM; every
      interval the logic measures is well under a minute;
    - inputs before debouncing are kept as bits, not one byte each.
*/

#ifndef HELISR_LOGIC_H
#define HELISR_LOGIC_H

#include <stdint.h>
#include "shared/helisr_config.h"
#include "settings.h"

typedef struct
{
	uint16_t time_last;
	uint8_t  pin_state:      1;
	uint8_t  prev_pin_state: 1;
	uint8_t  current_state:  1;
	uint8_t  changed:        1;
} phys_state_t;

typedef struct
{
	uint16_t time_last;
	uint8_t  curr_physical_state: 1;
	uint8_t  prev_physical_state: 1;
	uint8_t  on_state:            1;
	uint8_t  off_state:           1;
	uint8_t  current_state:       1;
	uint8_t  delay_act:           2;
} log_state_t;

enum
{
	BUTTON_ACTION_IDLE = 0,
	BUTTON_ACTION_DELAY,
	BUTTON_ACTION_PRESS,
	BUTTON_ACTION_BLOCK,
};

extern uint8_t      raw_bits[HSR_MAX_PHYS / 8];   // physical inputs before debouncing
extern phys_state_t phys_state[HSR_MAX_PHYS];
extern log_state_t  log_state[HSR_MAX_BUTTONS];
extern uint8_t      shifts_state;

static inline uint8_t bit_get(const uint8_t *bits, uint8_t n) { return (bits[n >> 3] >> (n & 7)) & 1; }
static inline void bit_put(uint8_t *bits, uint8_t n, uint8_t v)
{
	if (v) bits[n >> 3] |= (uint8_t)(1 << (n & 7));
	else   bits[n >> 3] &= (uint8_t)~(1 << (n & 7));
}

// ------------------------------------------------------------ buttons.cpp --

void buttons_init(void);
// Axis-to-button ranges from the scaled axes, into raw_bits from
// HSR_PHYS_A2B_FIRST. Returns the index after the last range button.
uint8_t a2b_get(const analog_data_t *scaled);
void buttons_debounce(uint16_t now, uint8_t a2b_end);
void encoders_process(uint16_t now);
void buttons_logical(uint16_t now);
// Report data: out = reported buttons packed in order, log/phy = by number,
// pov = HID hat values (0-7, 0xFF centred), one per used hat in order.
void buttons_get(uint8_t *out, uint8_t *log, uint8_t *phy, uint8_t *pov, uint8_t *shift);
int16_t encoder_count(uint8_t n, int16_t lo, int16_t hi);   // clamps it to lo..hi

// --------------------------------------------------------------- axes.cpp --

void axes_init(void);
void axes_process(const uint16_t *analog, uint16_t now);
extern analog_data_t raw_axis_data[HSR_MAX_AXES];
extern analog_data_t scaled_axis_data[HSR_MAX_AXES];
// What the PC receives for axis i: its scaled value, or 0 if it isn't enabled.
static inline analog_data_t axis_out(uint8_t i) { return g_config.axis_config[i].out_enabled ? scaled_axis_data[i] : 0; }

// --------------------------------------------------------------- leds.cpp --

void leds_init(void);
void leds_process(uint16_t now);
// LED outputs: returns bit n = spare pin n's single LED on; pwm[c] = channel c's duty (%).
uint16_t leds_get(uint8_t *pwm);

#endif
