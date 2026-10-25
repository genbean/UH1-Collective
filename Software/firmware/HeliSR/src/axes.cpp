/*
  axes.cpp - axis processing: filter, dead bands, calibration, curve,
  resolution, inversion, prescaler, trim and centre buttons, axis functions

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy)
  v1.7.3b1: application/Src/analog.c.
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026:
    - sources are the board's 9 analog inputs (12-bit, 0-4092) and slow
      encoders; FreeJoy's SPI/I2C sensors and STM32 ADC/DMA code are gone;
    - integer maths, except the resolution step, which keeps FreeJoy's float
      calculation so the results match FreeJoy's exactly;
    - filter coefficients in flash (PROGMEM);
    - the dynamic dead band's variance can't overflow (FreeJoy's 32-bit sum
      wraps on big movements);
    - guards against division by zero for degenerate calibrations;
    - the lower trim limit is MIN - value (FreeJoy wrote value + MIN);
    - axes whose value nothing uses are skipped.
  HSR_FREEJOY_EXACT (PC comparison builds only) brings back FreeJoy's two
  bugs above, so the comparison with FreeJoy's code can demand identical results.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <Arduino.h>
#include <string.h>
#include "logic.h"
#include "settings.h"

#define CFG g_config

#define FILTER_BUF_SIZE     20
#define DEADBAND_BUF_SIZE   8

analog_data_t raw_axis_data[HSR_MAX_AXES];
analog_data_t scaled_axis_data[HSR_MAX_AXES];

static analog_data_t filter_buffer[HSR_MAX_AXES][FILTER_BUF_SIZE];
static analog_data_t deadband_buffer[HSR_MAX_AXES][DEADBAND_BUF_SIZE];
static int32_t axis_trim_value[HSR_MAX_AXES];
static uint8_t axis_needed;                 // bit i: axis i's value is used somewhere

// The three buttons each axis can have (trim up/down/reset, centre, prescaler, function)
typedef struct
{
	uint16_t time_last;
	uint8_t  current_state: 1;
	uint8_t  prev_state:    1;
} axis_button_t;
static axis_button_t axis_buttons[HSR_MAX_AXES][3];

// FIR filter coefficients for levels 1-7 (sum 100 each), as in FreeJoy.
static const int8_t FILTER_COEF[7][FILTER_BUF_SIZE] PROGMEM = {
	{ 40, 30, 15, 10,  5,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 },
	{ 30, 20, 10, 10, 10,  6,  6,  4,  2,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0 },
	{ 25, 20, 10, 10,  8,  6,  6,  4,  2,  2,  2,  2,  2,  1,  0,  0,  0,  0,  0,  0 },
	{ 20, 15, 10,  8,  8,  6,  6,  6,  4,  2,  2,  2,  2,  2,  2,  2,  2,  1,  0,  0 },
	{ 15, 13, 11, 10, 10,  9,  7,  4,  3,  2,  2,  2,  2,  2,  2,  2,  1,  1,  1,  1 },
	{ 12, 10,  8,  8,  8,  7,  7,  6,  6,  5,  4,  4,  3,  3,  2,  2,  2,  1,  1,  1 },
	{  8,  8,  7,  7,  7,  6,  6,  6,  6,  6,  5,  5,  5,  5,  5,  3,  2,  1,  1,  1 },
};

// ---------------------------------------------------------------- mapping --

static int32_t map2(int32_t x, int32_t in_min, int32_t in_max, int32_t out_min, int32_t out_max)
{
	if (x < in_min) return out_min;
	if (x > in_max) return out_max;
	if (in_max == in_min) return out_min;
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Calibration with a centre and a centre dead zone. Each half is mapped on its
// own, which keeps (x - in) * (out half-range) below 2^31.
static int32_t map3(int32_t x, int32_t in_min, int32_t in_center, int32_t in_max,
                    int32_t out_min, int32_t out_center, int32_t out_max, uint8_t deadband_size)
{
	int32_t dead_zone_right = ((in_max - in_center) * deadband_size) >> 10;
	int32_t dead_zone_left = ((in_center - in_min) * deadband_size) >> 10;

	if (x < in_min) return out_min;
	if (x > in_max) return out_max;
	if ((x > in_center && (x - in_center) < dead_zone_right) ||
	    (x < in_center && (in_center - x) < dead_zone_left) || x == in_center)
		return out_center;

	if (x < in_center)
	{
		int32_t d = in_center - dead_zone_left - in_min;
		if (d <= 0) return out_min;
		return (x - in_min) * (out_center - out_min) / d + out_min;
	}
	int32_t d = in_max - in_center - dead_zone_right;
	if (d <= 0) return out_max;
	return (x - in_center - dead_zone_right) * (out_max - out_center) / d + out_center;
}

// FreeJoy's calculation, float included: an integer version differs by a
// count now and then (float rounding, truncation towards zero), which a
// prescaler or an axis-to-button boundary can turn into a visible difference.
static int32_t set_resolution(int32_t value, uint8_t resolution)
{
	if (resolution >= 16) return value;
	uint32_t fullscale = AXIS_SPAN;
	int32_t steps = fullscale >> (16 - resolution);
	float step = (float)fullscale / steps;
	int32_t index = (value - AXIS_MIN_VALUE) >> (16 - resolution);
	return (int32_t)(step * index + AXIS_MIN_VALUE);
}

static analog_data_t filter(analog_data_t value, analog_data_t *buf, uint8_t level)
{
	if (level == FILTER_NO || level > FILTER_LEVEL_7) return value;
	const int8_t *coef = FILTER_COEF[level - 1];
	int32_t acc = (int32_t)value * (int8_t)pgm_read_byte(&coef[0]);
	for (uint8_t i = FILTER_BUF_SIZE - 1; i > 0; i--)
	{
		buf[i] = buf[i - 1];
		acc += (int32_t)buf[i] * (int8_t)pgm_read_byte(&coef[i]);
	}
	buf[0] = (analog_data_t)(acc / 100);
	return buf[0];
}

static uint8_t dynamic_deadband_holding(analog_data_t value, analog_data_t *buf, uint8_t deadband_size)
{
	int32_t mean = 0;
	for (uint8_t i = 0; i < DEADBAND_BUF_SIZE; i++) mean += buf[i];
	mean /= DEADBAND_BUF_SIZE;

	uint32_t threshold = 3UL * deadband_size;
#ifndef HSR_FREEJOY_EXACT
	// floor(sum of squares / 8) without overflow: the squares' eighths and
	// their remainders are summed apart (each square is at most 65534^2).
	uint32_t eighths = 0, rest = 0;
	for (uint8_t i = 0; i < DEADBAND_BUF_SIZE; i++)
	{
		int32_t d = buf[i] - mean;
		uint32_t sq = (uint32_t)(d < 0 ? -d : d) * (uint32_t)(d < 0 ? -d : d);
		eighths += sq >> 3;
		rest += sq & 7;
	}
	uint8_t holding = eighths + (rest >> 3) <= threshold * threshold;
#else
	// FreeJoy's 32-bit signed sum, which wraps
	uint32_t sum = 0;
	for (uint8_t i = 0; i < DEADBAND_BUF_SIZE; i++)
	{
		int32_t d = buf[i] - mean;
		sum += (uint32_t)d * (uint32_t)d;
	}
	uint8_t holding = !((int32_t)sum / DEADBAND_BUF_SIZE > (int32_t)(threshold * threshold));
#endif

	for (uint8_t i = DEADBAND_BUF_SIZE - 1; i > 0; i--) buf[i] = buf[i - 1];
	buf[0] = value;

	return holding;
}

static int32_t shape(const axis_config_t *a, int32_t value)
{
	uint8_t linear = 1;
	for (uint8_t p = 0; p < 11; p++)
		if (a->curve_shape[p] != (int8_t)(p * 20 - 100)) { linear = 0; break; }
	if (linear) return value;

	const int32_t step = AXIS_SPAN / 10;                 // 11 points, 10 segments
	uint8_t index = (uint8_t)((value - AXIS_MIN_VALUE) / step);
	if (index > 9) index = 9;
	int32_t in_min = AXIS_MIN_VALUE + (int32_t)index * step;
	int32_t in_max = AXIS_MIN_VALUE + (int32_t)(index + 1) * step;
	int32_t out_min = (int32_t)a->curve_shape[index] * AXIS_SPAN / 200 + AXIS_CENTER_VALUE;
	int32_t out_max = (int32_t)a->curve_shape[index + 1] * AXIS_SPAN / 200 + AXIS_CENTER_VALUE;
	return map2(value, in_min, in_max, out_min, out_max);
}

static int32_t clamp_axis(int32_t v)
{
	if (v > AXIS_MAX_VALUE) return AXIS_MAX_VALUE;
	if (v < AXIS_MIN_VALUE) return AXIS_MIN_VALUE;
	return v;
}

// --------------------------------------------------------------- process --

void axes_init(void)
{
	memset(raw_axis_data, 0, sizeof(raw_axis_data));
	memset(scaled_axis_data, 0, sizeof(scaled_axis_data));
	memset(filter_buffer, 0, sizeof(filter_buffer));
	memset(deadband_buffer, 0, sizeof(deadband_buffer));
	memset(axis_trim_value, 0, sizeof(axis_trim_value));
	memset(axis_buttons, 0, sizeof(axis_buttons));

	// An axis must be processed if it's reported, feeds another axis's
	// function, axis-to-button ranges or a PWM output, or has a source,
	// function or buttons of its own (FreeJoy processes every axis; one with no
	// source still reports a constant through its calibration).
	axis_needed = 0;
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
	{
		const axis_config_t *a = &CFG.axis_config[i];
		if (a->out_enabled || a->source_main != SOURCE_NO || a->function != NO_FUNCTION ||
		    a->button1 >= 0 || a->button2 >= 0 || a->button3 >= 0 || CFG.axes_to_buttons[i].buttons_cnt)
			axis_needed |= 1 << i;
		if (a->function != NO_FUNCTION) axis_needed |= 1 << (a->source_secondary & 7);
	}
	for (uint8_t c = 0; c < HSR_MAX_PWM; c++)
		if (CFG.led_pwm_config[c].is_axis) axis_needed |= 1 << CFG.led_pwm_config[c].axis_num;
}

static uint8_t button_type(const axis_config_t *a, uint8_t n)
{
	return n == 0 ? a->button1_type : n == 1 ? a->button2_type : a->button3_type;
}

static int8_t button_num(const axis_config_t *a, uint8_t n)
{
	return n == 0 ? a->button1 : n == 1 ? a->button2 : a->button3;
}

void axes_process(const uint16_t *analog, uint16_t now)
{
	// Each axis's result before the functions stage: clamped to the axis
	// range by then, so 16 bits (FreeJoy keeps int32; the values are the same).
	int16_t tmp[HSR_MAX_AXES];

	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
	{
		const axis_config_t *a = &CFG.axis_config[i];
		int8_t source = a->source_main;
		if (!(axis_needed & (1 << i)))
		{
			tmp[i] = 0;
			continue;
		}

		// Source
		if (source >= 0 && source < HSR_ANALOG_SOURCES)
		{
			int32_t v = analog[source];
			if (a->offset_angle > 0)   // move the wrap point of a 360-degree sensor
			{
				v -= (int32_t)a->offset_angle * 170;
				if (v < 0) v += HSR_RAW_MAX;              // FreeJoy wraps by its maximum (4095)
				else if (v > HSR_RAW_MAX) v -= HSR_RAW_MAX;
			}
			raw_axis_data[i] = map2(v, 0, HSR_RAW_MAX, AXIS_MIN_VALUE, AXIS_MAX_VALUE);
		}
		else if (source == SOURCE_ENCODER)
		{
			int32_t v = encoder_count(a->channel, a->calib_min, a->calib_max);
			if (a->offset_angle > 0)
			{
				v -= (int32_t)a->offset_angle * 170;
				if (v < 0) v += 32767;
				else if (v > 32767) v -= 32767;
			}
			raw_axis_data[i] = (analog_data_t)v;
		}

		// Filtering
		int32_t x = filter(raw_axis_data[i], filter_buffer[i], a->filter);

		// Dead band and scaling
		if (!a->is_dynamic_deadband)
		{
			x = map3(x, a->calib_min, a->calib_center, a->calib_max,
			              AXIS_MIN_VALUE, AXIS_CENTER_VALUE, AXIS_MAX_VALUE, a->deadband_size);
		}
		else
		{
			x = map3(x, a->calib_min, a->calib_center, a->calib_max,
			              AXIS_MIN_VALUE, AXIS_CENTER_VALUE, AXIS_MAX_VALUE, 0);
			int32_t diff = x - scaled_axis_data[i];
			if (diff < 0) diff = -diff;
			if (diff < 9L * a->deadband_size &&                       // 3 * 3 * deadband = 3 sigma
			    dynamic_deadband_holding(x, deadband_buffer[i], a->deadband_size))
				x = scaled_axis_data[i];
		}

		// Curve, resolution, inversion
		x = shape(a, x);
		x = set_resolution(x, a->resolution + 1);
		if (a->inverted) x = -x;

		// Prescaler: always, or while a prescaler button is held. As in FreeJoy,
		// the buttons' states here are still the previous pass's.
		if (a->prescaler != 100)
		{
			uint8_t has_btn = 0, held = 0;
			for (uint8_t n = 0; n < 3; n++)
			{
				if (button_num(a, n) >= 0 && button_type(a, n) == AXIS_BUTTON_PRESCALER_EN)
				{
					has_btn = 1;
					if (axis_buttons[i][n].current_state) held = 1;
				}
			}
			if (!has_btn || held)
			{
				if (a->is_centered) x = x * a->prescaler / 100;
				else x = (x - AXIS_MIN_VALUE) * a->prescaler / 100 + AXIS_MIN_VALUE;
			}
		}

		// Buttons: new states (the logical buttons'), then trim and centre,
		// with FreeJoy's rules: buttons 1 and 3 can trim, at most one step up
		// and one down per pass; the first press steps at once, holding
		// repeats every 50 ms after 0.5 s.
		uint8_t inc = 0, dec = 0, rst = 0, cent = 0;
		for (uint8_t n = 0; n < 3; n++)
		{
			axis_button_t *ab = &axis_buttons[i][n];
			int8_t num = button_num(a, n);
			ab->prev_state = ab->current_state;
			if (num < 0 || num >= HSR_MAX_BUTTONS) continue;
			ab->current_state = log_state[num].current_state;
			uint8_t type = button_type(a, n);
			if (type == AXIS_BUTTON_UP && n != 1) inc |= 1 << n;
			else if (type == AXIS_BUTTON_DOWN && n != 1) dec |= 1 << n;
			else if (type == AXIS_BUTTON_RESET) rst |= 1 << n;
			else if (type == AXIS_BUTTON_CENTER) cent |= 1 << n;
		}

		axis_button_t *b0 = &axis_buttons[i][0], *b1 = &axis_buttons[i][1], *b2 = &axis_buttons[i][2];
		if (inc || dec || rst)
		{
			int32_t trim_step = AXIS_FULLSCALE / (a->divider ? a->divider : 1);
			for (int8_t dir = 1; dir >= -1; dir -= 2)
			{
				uint8_t m = (dir > 0) ? inc : dec;
				if ((m & 1) && b0->current_state > b0->prev_state)
				{
					b0->time_last = now + 500;
					axis_trim_value[i] += dir * trim_step;
				}
				else if ((m & 1) && b0->prev_state && (int16_t)(now - b0->time_last) > 50)
				{
					b0->time_last = now;
					axis_trim_value[i] += dir * trim_step;
				}
				else if ((m & 4) && b2->current_state > b2->prev_state)
				{
					b2->time_last = now + 500;
					axis_trim_value[i] += dir * trim_step;
				}
				else if ((m & 4) && b2->prev_state && (int16_t)(now - b2->time_last) > 50)
				{
					b2->time_last = now;
					axis_trim_value[i] += dir * trim_step;
				}
			}
			if (((rst & 1) && b0->current_state) || ((rst & 2) && b1->current_state) || ((rst & 4) && b2->current_state))
				axis_trim_value[i] = 0;
		}
		if (((cent & 1) && b0->current_state) || ((cent & 2) && b1->current_state) || ((cent & 4) && b2->current_state))
			axis_trim_value[i] = -x;

		if (x + axis_trim_value[i] > AXIS_MAX_VALUE)
		{
			axis_trim_value[i] = AXIS_MAX_VALUE - x;
			x = AXIS_MAX_VALUE;
		}
		else if (x + axis_trim_value[i] < AXIS_MIN_VALUE)
		{
#ifndef HSR_FREEJOY_EXACT
			axis_trim_value[i] = AXIS_MIN_VALUE - x;
#else
			axis_trim_value[i] = x + AXIS_MIN_VALUE;   // FreeJoy's version
#endif
			x = AXIS_MIN_VALUE;
		}
		else
			x += axis_trim_value[i];
		tmp[i] = (int16_t)x;    // always within the axis range here
	}

	// Functions combining two axes
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
	{
		const axis_config_t *a = &CFG.axis_config[i];
		if (a->function != NO_FUNCTION)
		{
			uint8_t has_btn = 0, held = 0;
			for (uint8_t n = 0; n < 3; n++)
			{
				if (button_type(a, n) == AXIS_BUTTON_FUNC_EN)
				{
					has_btn = 1;
					if (axis_buttons[i][n].current_state) held = 1;
				}
			}
			if (!has_btn || held)
			{
				int32_t x = tmp[i];
				int32_t other = tmp[a->source_secondary & 7];
				switch (a->function)
				{
				case FUNCTION_PLUS:
					x = a->is_centered ? x + other : x + other - AXIS_MIN_VALUE;
					break;
				case FUNCTION_MINUS:
					x = a->is_centered ? x / 2 - other / 2 : x - other + AXIS_MIN_VALUE;
					break;
				case FUNCTION_EQUAL:
					x = other;
					break;
				}
				tmp[i] = (int16_t)clamp_axis(x);
			}
		}

		scaled_axis_data[i] = tmp[i];
	}
}
