/*
  leds.cpp - single LEDs and PWM outputs on the spare pins

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy)
  v1.7.3b1: application/Src/leds.c (LEDs_LogicalProcess) and periphery.c
  (PWM_SetFromAxis).
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026:
  LEDs and PWM channels are tied to spare pins (no LED matrix, no RGB LEDs, no
  host-controlled LEDs).
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <Arduino.h>
#include "logic.h"
#include "settings.h"
#include "board.h"

#define CFG g_config

// Spare pin index of each PWM channel (pins 5, 6, 9, 10).
static const uint8_t PWM_SPARE[HSR_MAX_PWM] PROGMEM = { 3, 4, 7, 8 };

static uint8_t leds_state[HSR_MAX_LEDS];
static uint16_t blink_last[4];
static uint8_t pwm_duty[HSR_MAX_PWM];

void leds_init(void)
{
	for (uint8_t i = 0; i < HSR_MAX_LEDS; i++) leds_state[i] = 0;
	for (uint8_t c = 0; c < HSR_MAX_PWM; c++) pwm_duty[c] = 0xFF;   // force the first write
}

uint16_t leds_get(uint8_t *pwm)
{
	uint16_t bits = 0;
	for (uint8_t i = 0; i < HSR_MAX_LEDS; i++)
		if (CFG.pins[i] == PIN_LED_SINGLE && leds_state[i]) bits |= 1u << i;
	for (uint8_t c = 0; c < HSR_MAX_PWM; c++) pwm[c] = (pwm_duty[c] == 0xFF) ? 0 : pwm_duty[c];
	return bits;
}

void leds_process(uint16_t now)
{
	// Single LEDs: follow a logical button (with its inversion), steady or blinking.
	for (uint8_t i = 0; i < HSR_MAX_LEDS; i++)
	{
		if (CFG.pins[i] != PIN_LED_SINGLE) continue;
		const led_config_t *led = &CFG.leds[i];
		int8_t n = led->input_num;
		if (n < 0 || n >= HSR_MAX_BUTTONS) continue;

		uint8_t state = log_state[n].current_state ^ CFG.buttons[n].is_inverted;
		uint8_t active = (led->type == LED_INVERTED) ? !state : state;
		uint8_t timer = led->timer;
		if (timer > 3 || !active)
			leds_state[i] = active;
		else if ((uint16_t)(now - blink_last[timer]) > CFG.led_timer_ms[timer])
		{
			leds_state[i] = !leds_state[i];
			blink_last[timer] = now;
		}
		board_set_led(i, leds_state[i]);
	}

	// PWM: a fixed duty cycle, or scaled by an axis.
	for (uint8_t c = 0; c < HSR_MAX_PWM; c++)
	{
		uint8_t spare = pgm_read_byte(&PWM_SPARE[c]);
		if (CFG.pins[spare] != PIN_LED_PWM) continue;
		const led_pwm_config_t *pwm = &CFG.led_pwm_config[c];
		uint8_t duty = pwm->duty_cycle > 100 ? 100 : pwm->duty_cycle;
		if (pwm->is_axis)
			duty = (uint8_t)(((int32_t)scaled_axis_data[pwm->axis_num] + 32767) / 655 * duty / 100);
		if (duty != pwm_duty[c])
		{
			pwm_duty[c] = duty;
			board_set_pwm(spare, duty);
		}
	}
}
