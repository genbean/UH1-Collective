/*
  fj_bridge.h - drives FreeJoy's original button, encoder, axis-to-button and
  axis code (compiled for the PC) so its results can be compared with HeliSR's.
  Uses only plain types, so it can be included from both sides.

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HSR_FJ_BRIDGE_H
#define HSR_FJ_BRIDGE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct
{
	int16_t calib_min, calib_center, calib_max;
	uint8_t out_enabled, inverted, is_centered, function, filter;
	int8_t  curve[11];
	uint8_t resolution, channel, deadband_size, is_dynamic_deadband;
	int8_t  source_main;
	uint8_t source_secondary, offset_angle;
	int8_t  button1, button2, button3;
	uint8_t divider, button1_type, button2_type, button3_type, prescaler;
} fjb_axis_t;

void fjb_reset(void);
void fjb_set_common(uint16_t debounce_ms, uint16_t a2b_debounce_ms, uint8_t encoder_press_ms,
                    uint16_t timer1_ms, uint16_t timer2_ms, uint16_t timer3_ms);
void fjb_set_button(int j, int8_t physical_num, uint8_t type, uint8_t shift, uint8_t inverted,
                    uint8_t disabled, uint8_t delay_timer, uint8_t press_timer);
void fjb_set_shift(int i, int8_t button);
void fjb_set_a2b(int axis, const uint8_t *points, uint8_t buttons_cnt);
void fjb_set_encoder_mode(int freejoy_encoder, uint8_t mode);
void fjb_set_axis(int i, const fjb_axis_t *a);
void fjb_start(void);

// One pass: raw physical inputs 0-26 (bit n), the 8 analog sources (0-4095), time.
void fjb_step(int64_t now_ms, uint32_t raw27, const uint16_t *analog8);

// Results (FreeJoy's sizes: 128 buttons): logical, physical, reported
// buttons as bits; hat values per hat group; output axes; shift state.
void fjb_get(uint8_t *log16, uint8_t *phy16, uint8_t *out16, uint8_t *pov4, int16_t *axes8, uint8_t *shift);

// For diagnosing a difference: raw and scaled axes, and logical button j's state.
void fjb_get_axes_detail(int16_t *raw8, int16_t *scaled8);
void fjb_get_button_detail(int j, int *curr, int *prev, int *on, int *off, int *cur, int *act, int *time_last);

#ifdef __cplusplus
}
#endif

#endif
