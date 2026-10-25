/*
  helisr_config.h - settings layout shared by the HeliSR firmware and HeliSR Configurator

  HeliSR: game controller firmware for a Pro Micro on the HeliSR board.
  Based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy), firmware v1.7.3b1,
  commit fc697108124f9ffc4ca3f3b1c6bdb2f21f94d52d, file application/Inc/common_types.h.
    Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  This one file is compiled into both the firmware (avr-gcc) and the configurator
  (a PC compiler), so the two can never disagree about where a setting lives.
  The structs are byte-packed and every bit-field byte uses one type only, so
  GCC and MSVC/MinGW lay them out the same way. HSR_CONFIG_SIZE and the offset
  checks at the end catch any difference at compile time.
*/

#ifndef HELISR_CONFIG_H
#define HELISR_CONFIG_H

#include <stdint.h>

/* ------------------------------------------------------------- versions -- */

#define HSR_FIRMWARE_VERSION      0x0100   // 1.0.0, shown in the configurator
#define HSR_CONFIG_VERSION        2        // bump whenever dev_config_t or its defaults change
#define HSR_BOARD_ID              0x30     // HeliSR Rev 3.0

/* --------------------------------------------------------------- limits -- */

#define HSR_SR_INPUTS             16       // IN1-IN16 on J1/J2 (two 74HC165s)
#define HSR_SPARE_PINS            11       // Pro Micro pins the board leaves free
#define HSR_AX_INPUTS             4        // AX1-AX4 on J11-J14
#define HSR_ANALOG_SOURCES        9        // AX1-AX4, then the 5 analog-capable spare pins
#define HSR_MAX_AXES              8        // X, Y, Z, Rx, Ry, Rz, Slider 1, Slider 2
#define HSR_MAX_BUTTONS           64       // logical buttons reported to the PC
#define HSR_MAX_PHYS              64       // physical inputs, including axis-to-button ranges
#define HSR_MAX_POVS              4
#define HSR_MAX_ENCODERS          8
#define HSR_MAX_SHIFTS            5
#define HSR_MAX_LEDS              HSR_SPARE_PINS
#define HSR_MAX_PWM               4
#define HSR_A2B_POINTS            13       // 12 ranges per axis
#define HSR_NAME_LEN              26       // USB product name, NUL-padded

/* Physical input numbers (button_t.physical_num):
     0-15   IN1-IN16
     16-26  spare pins set to BUTTON_GND / BUTTON_VCC, by spare pin index
     27-63  axis-to-button ranges, in axis order */
#define HSR_PHYS_SR_FIRST         0
#define HSR_PHYS_SPARE_FIRST      (HSR_PHYS_SR_FIRST + HSR_SR_INPUTS)
#define HSR_PHYS_A2B_FIRST        (HSR_PHYS_SPARE_FIRST + HSR_SPARE_PINS)
#define HSR_MAX_A2B_BUTTONS       (HSR_MAX_PHYS - HSR_PHYS_A2B_FIRST)

/* Spare pins, by index, with their Pro Micro silkscreen labels:
     0 TX   1 RX   2 "4"  3 "5"  4 "6"  5 "7"  6 "8"  7 "9"  8 "10"  9 "14"  10 "16"
   Analog sources 4-8 are spare pins 2, 4, 6, 7 and 8 (Arduino A6-A10). */
#define HSR_SPARE_ANALOG_MASK     0x01D4   // pins 4, 6, 8, 9, 10
#define HSR_SPARE_PWM_MASK        0x0198   // pins 5, 6, 9, 10

/* Raw analog readings are 12-bit (16 x 10-bit samples / 4). The PC test
   program overrides this to FreeJoy's 4095 when comparing with FreeJoy. */
#ifndef HSR_RAW_MAX
#define HSR_RAW_MAX               4092
#endif

/* Output axis values, as in FreeJoy. FreeJoy runs on a 32-bit CPU; on the
   AVR an int is 16 bits, so anything wider than int16 is spelled out as int32. */
#define AXIS_MIN_VALUE            (-32767)
#define AXIS_MAX_VALUE            (32767)
#define AXIS_CENTER_VALUE         0
#define AXIS_FULLSCALE            ((int32_t)AXIS_MAX_VALUE - AXIS_MIN_VALUE + 1)    // 65535
#define AXIS_SPAN                 ((int32_t)AXIS_MAX_VALUE - AXIS_MIN_VALUE)        // 65534

#pragma pack(push, 1)

/* ----------------------------------------------------------------- pins -- */

enum
{
	PIN_NOT_USED = 0,
	PIN_BUTTON_GND,         // switch to GND, internal pull-up
	PIN_BUTTON_VCC,         // switch to VCC, needs an external pull-down
	PIN_AXIS_ANALOG,        // analog-capable pins only
	PIN_LED_SINGLE,         // on/off output, driven by a button
	PIN_LED_PWM,            // PWM-capable pins only
};
typedef uint8_t pin_func_t;

/* ----------------------------------------------------------------- axes -- */

enum
{
	FILTER_NO = 0,
	FILTER_LEVEL_1,
	FILTER_LEVEL_2,
	FILTER_LEVEL_3,
	FILTER_LEVEL_4,
	FILTER_LEVEL_5,
	FILTER_LEVEL_6,
	FILTER_LEVEL_7,
};
typedef uint8_t filter_t;

typedef int16_t analog_data_t;

enum
{
	NO_FUNCTION = 0,
	FUNCTION_PLUS,
	FUNCTION_MINUS,
	FUNCTION_EQUAL,
};

enum
{
	AXIS_BUTTON_FUNC_EN = 0,
	AXIS_BUTTON_PRESCALER_EN,
	AXIS_BUTTON_CENTER,
	AXIS_BUTTON_RESET,
	AXIS_BUTTON_DOWN,
	AXIS_BUTTON_UP,
};

enum
{
	SOURCE_EXTERNAL = -4,   // kept for FreeJoy compatibility, unused
	SOURCE_ENCODER = -3,    // axis driven by buttons (buttons-to-axis)
	SOURCE_NO = -1,
	// 0-8: analog sources (AX1-AX4, spare analog pins)
};
typedef int8_t axis_source_t;

typedef struct
{
	analog_data_t   calib_min;
	analog_data_t   calib_center;
	analog_data_t   calib_max;
	uint8_t         out_enabled:  1;
	uint8_t         inverted:     1;
	uint8_t         is_centered:  1;
	uint8_t         function:     2;
	uint8_t         filter:       3;
	int8_t          curve_shape[11];
	uint8_t         resolution:   4;
	uint8_t         channel:      4;
	uint8_t         deadband_size: 7;
	uint8_t         is_dynamic_deadband: 1;
	axis_source_t   source_main;
	uint8_t         source_secondary: 3;
	uint8_t         offset_angle: 5;    // unused on the HeliSR
	int8_t          button1;
	int8_t          button2;
	int8_t          button3;
	uint8_t         divider;
	uint8_t         reserved0;          // FreeJoy's i2c_address
	uint8_t         button1_type: 3;
	uint8_t         button2_type: 2;
	uint8_t         button3_type: 3;
	uint8_t         prescaler;
	uint8_t         reserved1;
} axis_config_t;

/* -------------------------------------------------------------- buttons -- */

enum
{
	BUTTON_NORMAL = 0,
	BUTTON_TOGGLE,
	TOGGLE_SWITCH,
	TOGGLE_SWITCH_ON,
	TOGGLE_SWITCH_OFF,

	POV1_UP,
	POV1_RIGHT,
	POV1_DOWN,
	POV1_LEFT,
	POV1_CENTER,
	POV2_UP,
	POV2_RIGHT,
	POV2_DOWN,
	POV2_LEFT,
	POV2_CENTER,
	POV3_UP,
	POV3_RIGHT,
	POV3_DOWN,
	POV3_LEFT,
	POV4_UP,
	POV4_RIGHT,
	POV4_DOWN,
	POV4_LEFT,

	ENCODER_INPUT_A,
	ENCODER_INPUT_B,

	RADIO_BUTTON1,
	RADIO_BUTTON2,
	RADIO_BUTTON3,
	RADIO_BUTTON4,

	SEQUENTIAL_TOGGLE,
	SEQUENTIAL_BUTTON,

	SWITCH_CENTER,          // HeliSR addition: on while this input and the next are both off
};
typedef uint8_t button_type_t;

enum
{
	BUTTON_TIMER_OFF = 0,
	BUTTON_TIMER_1,
	BUTTON_TIMER_2,
	BUTTON_TIMER_3,
};
typedef uint8_t button_timer_t;

typedef struct
{
	int8_t          physical_num;       // -1 = none
	uint8_t         type: 5;
	uint8_t         shift_modificator: 3;
	uint8_t         is_inverted: 1;
	uint8_t         is_disabled: 1;
	uint8_t         delay_timer: 3;
	uint8_t         press_timer: 3;
} button_t;

/* ------------------------------------------------- encoders, a2b, shifts -- */

enum
{
	ENCODER_CONF_1x = 0,
	ENCODER_CONF_2x,
	ENCODER_CONF_4x,
};
typedef uint8_t encoder_t;

typedef struct
{
	uint8_t         points[HSR_A2B_POINTS];
	uint8_t         buttons_cnt;
} axis_to_buttons_t;

typedef struct
{
	int8_t          button;
} shift_modificator_t;

/* ----------------------------------------------------------------- LEDs -- */

enum
{
	LED_NORMAL = 0,
	LED_INVERTED,
};

typedef struct
{
	uint8_t         duty_cycle;
	uint8_t         axis_num: 3;
	uint8_t         is_axis: 1;
	uint8_t         reserved: 4;
} led_pwm_config_t;

typedef struct
{
	int8_t          input_num;
	uint8_t         type: 3;
	uint8_t         timer: 4;           // blink timer 0-3 (led_timer_ms); 15 (FreeJoy's signed -1) = steady
	uint8_t         reserved: 1;
} led_config_t;

/* --------------------------------------------------- device settings ------ */

typedef struct
{
	uint16_t            config_version;                 // HSR_CONFIG_VERSION
	char                device_name[HSR_NAME_LEN];
	uint16_t            button_debounce_ms;
	uint8_t             encoder_press_time_ms;
	uint8_t             exchange_period_ms;
	pin_func_t          pins[HSR_SPARE_PINS];

	axis_config_t       axis_config[HSR_MAX_AXES];

	button_t            buttons[HSR_MAX_BUTTONS];
	uint16_t            button_timer1_ms;
	uint16_t            button_timer2_ms;
	uint16_t            button_timer3_ms;
	uint16_t            a2b_debounce_ms;

	axis_to_buttons_t   axes_to_buttons[HSR_MAX_AXES];
	shift_modificator_t shift_config[HSR_MAX_SHIFTS];
	uint16_t            vid;
	uint16_t            pid;

	led_pwm_config_t    led_pwm_config[HSR_MAX_PWM];   // spare pins 5, 6, 9, 10 in that order
	led_config_t        leds[HSR_MAX_LEDS];            // by spare pin index
	uint16_t            led_timer_ms[4];

	encoder_t           encoders[HSR_MAX_ENCODERS];
	uint8_t             button_polling_interval_ticks;
	uint8_t             encoder_polling_interval_ticks;
} dev_config_t;

/* ------------------------------------------------- live data for the app -- */

typedef struct
{
	uint16_t        firmware_version;
	analog_data_t   raw_axis_data[HSR_MAX_AXES];        // each axis's source, before processing
	analog_data_t   axis_data[HSR_MAX_AXES];            // what the PC receives
	uint16_t        analog_inputs[HSR_ANALOG_SOURCES];  // raw 12-bit readings, 0-4092
	uint8_t         phy_button_data[HSR_MAX_PHYS / 8];
	uint8_t         log_button_data[HSR_MAX_BUTTONS / 8];
	uint8_t         shift_button_data;
} params_report_t;

#pragma pack(pop)

/* ------------------------------------------------- shared rules ---------- */

/* Hat number (1-4) of a POV direction button type, or 0. As in FreeJoy, POV
   direction buttons are reported only through their hat; POV centre buttons
   are ordinary buttons. */
static inline uint8_t hsr_pov_of(uint8_t type)
{
	if (type >= POV1_UP && type <= POV1_LEFT) return 1;
	if (type >= POV2_UP && type <= POV2_LEFT) return 2;
	if (type >= POV3_UP && type <= POV3_LEFT) return 3;
	if (type >= POV4_UP && type <= POV4_LEFT) return 4;
	return 0;
}

/* Whether a logical button appears in the joystick report. Reported buttons
   are packed in order: the first reported logical button is button 1. */
static inline uint8_t hsr_button_reported(const button_t *b)
{
	return b->physical_num >= 0 && !b->is_disabled && !hsr_pov_of(b->type);
}

static inline uint8_t hsr_reported_buttons(const dev_config_t *cfg)
{
	uint8_t n = 0;
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++) n += hsr_button_reported(&cfg->buttons[i]);
	return n;
}

/* Hats in use (bit 0 = hat 1): those with a direction button on an input.
   Used hats are reported in order, so hat 2 alone is the report's only hat. */
static inline uint8_t hsr_pov_mask(const dev_config_t *cfg)
{
	uint8_t mask = 0;
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
	{
		uint8_t pov = hsr_pov_of(cfg->buttons[i].type);
		if (pov && cfg->buttons[i].physical_num >= 0) mask |= (uint8_t)(1 << (pov - 1));
	}
	return mask;
}

/* ----------------------------------------------------- layout checks ------ */

#define HSR_CONFIG_SIZE   652
#define HSR_PARAMS_SIZE   69

#if defined(__cplusplus)
  #define HSR_STATIC_ASSERT(c, m) static_assert(c, m)
#else
  #define HSR_STATIC_ASSERT(c, m) _Static_assert(c, m)
#endif

HSR_STATIC_ASSERT(sizeof(axis_config_t) == 30, "axis_config_t layout");
HSR_STATIC_ASSERT(sizeof(button_t) == 3, "button_t layout");
HSR_STATIC_ASSERT(sizeof(axis_to_buttons_t) == 14, "axis_to_buttons_t layout");
HSR_STATIC_ASSERT(sizeof(led_pwm_config_t) == 2, "led_pwm_config_t layout");
HSR_STATIC_ASSERT(sizeof(led_config_t) == 2, "led_config_t layout");
HSR_STATIC_ASSERT(sizeof(dev_config_t) == HSR_CONFIG_SIZE, "dev_config_t layout");
HSR_STATIC_ASSERT(sizeof(params_report_t) == HSR_PARAMS_SIZE, "params_report_t layout");

#endif
