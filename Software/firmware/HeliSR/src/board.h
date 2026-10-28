/*
  board.h - HeliSR board hardware: shift registers, analog inputs, AS5600s
  (Rev 4.0), spare pins

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HELISR_BOARD_H
#define HELISR_BOARD_H

#include <stdint.h>
#include "shared/helisr_config.h"

// Set up the shift-register lines, the spare pins (per the settings), the
// free-running ADC and, on Rev 4.0, the I2C bus and its sensors.
void board_init(const dev_config_t *cfg);

// Rev 4.0: read the next AS5600 (one port per call). Nothing to do on Rev 3.0,
// whose ADC runs from its interrupt.
#if HSR_BOARD_REV == 40
void board_poll(void);
#else
static inline void board_poll(void) { }
#endif

// IN1-IN16: bit n set = IN(n+1) closed (pulled to GND).
uint16_t board_read_inputs(void);

// Spare pins set to BUTTON_GND / BUTTON_VCC: bit n set = spare pin n pressed.
uint16_t board_read_spare_buttons(void);

// Latest 12-bit readings (0-4092) of the board's analog sources; unused sources read 0.
void board_read_analog(uint16_t out[HSR_BOARD_SOURCES]);

// Spare pin n, set to LED_SINGLE / LED_PWM.
void board_set_led(uint8_t spare_index, uint8_t on);
void board_set_pwm(uint8_t spare_index, uint8_t duty_percent);

#endif
