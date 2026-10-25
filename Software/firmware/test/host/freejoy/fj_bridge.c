/*
  fj_bridge.c - the FreeJoy side of the comparison: sets up FreeJoy's
  configuration and state, runs its functions in the same order as HeliSR's
  pipeline, and stands in for the STM32 hardware those files call.

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <string.h>
#include "common_types.h"
#include "buttons.h"
#include "analog.h"
#include "encoders.h"
#include "axis_to_buttons.h"
#include "tle5011.h"
#include "tle5012.h"
#include "mcp320x.h"
#include "mlx90363.h"
#include "mlx90393.h"
#include "as5048a.h"
#include "ads1115.h"
#include "as5600.h"
#include "fj_bridge.h"

/* ------------------------------------------- FreeJoy's state (extern) -- */

extern uint8_t raw_buttons_data[MAX_BUTTONS_NUM];
extern physical_buttons_state_t physical_buttons_state[MAX_BUTTONS_NUM];
extern logical_buttons_state_t logical_buttons_state[MAX_BUTTONS_NUM];
extern uint8_t phy_buttons_data[MAX_BUTTONS_NUM / 8];
extern uint8_t log_buttons_data[MAX_BUTTONS_NUM / 8];
extern button_data_t out_buttons_data[MAX_BUTTONS_NUM / 8];
extern pov_data_t pov_data[MAX_POVS_NUM];
extern uint8_t pov_pos[MAX_POVS_NUM];
extern uint8_t shifts_state;
extern uint8_t a2b_first, a2b_last;
extern sensor_t sensors[MAX_AXIS_NUM];
extern uint16_t adc_data[MAX_AXIS_NUM];
extern analog_data_t scaled_axis_data[MAX_AXIS_NUM];
extern analog_data_t raw_axis_data[MAX_AXIS_NUM];
extern analog_data_t out_axis_data[MAX_AXIS_NUM];
extern analog_data_t filter_buffer[MAX_AXIS_NUM][FILTER_BUF_SIZE];
extern analog_data_t deadband_buffer[MAX_AXIS_NUM][DEADBAND_BUF_SIZE];
extern logical_buttons_state_t axis_buttons[MAX_AXIS_NUM][3];
extern int32_t axis_trim_value[MAX_AXIS_NUM];
extern uint8_t adc_cnt, sensors_cnt;
extern encoder_state_t encoders_state[MAX_ENCODERS_NUM];

static dev_config_t cfg;
static int64_t now;

/* ------------------------------------------- stand-ins for the STM32 -- */

volatile int64_t Ticks;
volatile uint32_t TimingDelay;
pin_config_t pin_config[USED_PINS_NUM];
static TIM_TypeDef tim1; TIM_TypeDef *TIM1 = &tim1;
static ADC_TypeDef adc1; ADC_TypeDef *ADC1 = &adc1;
static DMA_Channel_TypeDef dma1; DMA_Channel_TypeDef *DMA1_Channel1 = &dma1;

int64_t GetMillis(void) { return now; }
void ShiftRegistersGet(uint8_t *b, dev_config_t *c, uint8_t *p) { (void)b; (void)c; (void)p; }

uint8_t GPIO_ReadInputDataBit(GPIO_TypeDef *g, uint16_t p) { (void)g; (void)p; return 1; }
void GPIO_WriteBit(GPIO_TypeDef *g, uint16_t p, int v) { (void)g; (void)p; (void)v; }
void ADC_Init(ADC_TypeDef *a, ADC_InitTypeDef *i) { (void)a; (void)i; }
void ADC_Cmd(ADC_TypeDef *a, int s) { (void)a; (void)s; }
void ADC_DMACmd(ADC_TypeDef *a, int s) { (void)a; (void)s; }
void ADC_RegularChannelConfig(ADC_TypeDef *a, uint8_t c, uint8_t r, uint8_t t) { (void)a; (void)c; (void)r; (void)t; }
void ADC_ResetCalibration(ADC_TypeDef *a) { (void)a; }
int ADC_GetResetCalibrationStatus(ADC_TypeDef *a) { (void)a; return 0; }
void ADC_StartCalibration(ADC_TypeDef *a) { (void)a; }
int ADC_GetCalibrationStatus(ADC_TypeDef *a) { (void)a; return 0; }
void ADC_SoftwareStartConvCmd(ADC_TypeDef *a, int s) { (void)a; (void)s; }
void DMA_DeInit(DMA_Channel_TypeDef *d) { (void)d; }
void DMA_Init(DMA_Channel_TypeDef *d, DMA_InitTypeDef *i) { (void)d; (void)i; }
void DMA_Cmd(DMA_Channel_TypeDef *d, int s) { (void)d; (void)s; }
void DMA_ClearFlag(uint32_t f) { (void)f; }
int DMA_GetFlagStatus(uint32_t f) { (void)f; return 1; }
void DMA_SetCurrDataCounter(DMA_Channel_TypeDef *d, uint16_t n) { (void)d; (void)n; }
void RCC_AHBPeriphClockCmd(uint32_t p, int s) { (void)p; (void)s; }
void RCC_APB2PeriphClockCmd(uint32_t p, int s) { (void)p; (void)s; }
void RCC_GetClocksFreq(RCC_ClocksTypeDef *c) { memset(c, 0, sizeof(*c)); }
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *t) { (void)t; }
void TIM_TimeBaseInit(TIM_TypeDef *t, TIM_TimeBaseInitTypeDef *i) { (void)t; (void)i; }
void TIM_Cmd(TIM_TypeDef *t, int s) { (void)t; (void)s; }
void TIM_EncoderInterfaceConfig(TIM_TypeDef *t, uint16_t m, uint16_t a, uint16_t b) { (void)t; (void)m; (void)a; (void)b; }

int TLE5011_GetAngle(sensor_t *s, float *a) { (void)s; (void)a; return -1; }
int TLE5012_GetAngle(sensor_t *s, float *a) { (void)s; (void)a; return -1; }
uint16_t MCP320x_GetData(sensor_t *s, uint8_t c) { (void)s; (void)c; return 0; }
void MLX90363_Start(sensor_t *s) { (void)s; }
int MLX90363_GetData(uint16_t *d, sensor_t *s, uint8_t c) { (void)d; (void)s; (void)c; return -1; }
void MLX90393_Start(uint8_t m, sensor_t *s) { (void)m; (void)s; }
int MLX90393_GetData(uint16_t *d, sensor_t *s, uint8_t c) { (void)d; (void)s; (void)c; return -1; }
int AS5048A_GetData(uint16_t *d, sensor_t *s, uint8_t c) { (void)d; (void)s; (void)c; return -1; }
void ADS1115_Init(sensor_t *s) { (void)s; }
int16_t ADS1115_GetData(sensor_t *s, uint8_t c) { (void)s; (void)c; return 0; }
void AS5600_Init(sensor_t *s, uint16_t a, uint16_t b) { (void)s; (void)a; (void)b; }
int16_t AS5600_GetScaledData(sensor_t *s) { (void)s; return 0; }

/* ----------------------------------------------------------- set-up -- */

void fjb_reset(void)
{
	memset(&cfg, 0, sizeof(cfg));
	for (int j = 0; j < MAX_BUTTONS_NUM; j++) cfg.buttons[j].physical_num = -1;
	for (int i = 0; i < 5; i++) cfg.shift_config[i].button = -1;
	for (int i = 0; i < MAX_AXIS_NUM; i++)
	{
		cfg.axis_config[i].source_main = -1;
		cfg.axis_config[i].button1 = cfg.axis_config[i].button2 = cfg.axis_config[i].button3 = -1;
		cfg.axis_config[i].prescaler = 100;
	}

	memset(raw_buttons_data, 0, sizeof(raw_buttons_data));
	memset(physical_buttons_state, 0, sizeof(physical_buttons_state));
	memset(logical_buttons_state, 0, sizeof(logical_buttons_state));
	memset(phy_buttons_data, 0, sizeof(phy_buttons_data));
	memset(log_buttons_data, 0, sizeof(log_buttons_data));
	memset(out_buttons_data, 0, sizeof(out_buttons_data));
	memset(pov_data, 0, sizeof(pov_data));
	memset(pov_pos, 0, sizeof(pov_pos));
	shifts_state = 0;
	a2b_first = a2b_last = 0;
	memset(sensors, 0, sizeof(sensors));
	memset(adc_data, 0, sizeof(adc_data));
	memset(scaled_axis_data, 0, sizeof(scaled_axis_data));
	memset(raw_axis_data, 0, sizeof(raw_axis_data));
	memset(out_axis_data, 0, sizeof(out_axis_data));
	memset(filter_buffer, 0, sizeof(filter_buffer));
	memset(deadband_buffer, 0, sizeof(deadband_buffer));
	memset(axis_buttons, 0, sizeof(axis_buttons));
	memset(axis_trim_value, 0, sizeof(axis_trim_value));
	adc_cnt = sensors_cnt = 0;
	memset(encoders_state, 0, sizeof(encoders_state));
}

void fjb_set_common(uint16_t debounce_ms, uint16_t a2b_debounce_ms, uint8_t encoder_press_ms,
                    uint16_t timer1_ms, uint16_t timer2_ms, uint16_t timer3_ms)
{
	cfg.button_debounce_ms = debounce_ms;
	cfg.a2b_debounce_ms = a2b_debounce_ms;
	cfg.encoder_press_time_ms = encoder_press_ms;
	cfg.button_timer1_ms = timer1_ms;
	cfg.button_timer2_ms = timer2_ms;
	cfg.button_timer3_ms = timer3_ms;
}

void fjb_set_button(int j, int8_t physical_num, uint8_t type, uint8_t shift, uint8_t inverted,
                    uint8_t disabled, uint8_t delay_timer, uint8_t press_timer)
{
	button_t *b = &cfg.buttons[j];
	b->physical_num = physical_num;
	b->type = type;
	b->shift_modificator = shift;
	b->is_inverted = inverted;
	b->is_disabled = disabled;
	b->delay_timer = delay_timer;
	b->press_timer = press_timer;
}

void fjb_set_shift(int i, int8_t button) { cfg.shift_config[i].button = button; }

void fjb_set_a2b(int axis, const uint8_t *points, uint8_t buttons_cnt)
{
	memcpy(cfg.axes_to_buttons[axis].points, points, 13);
	cfg.axes_to_buttons[axis].buttons_cnt = buttons_cnt;
}

void fjb_set_encoder_mode(int freejoy_encoder, uint8_t mode) { cfg.encoders[freejoy_encoder] = mode; }

void fjb_set_axis(int i, const fjb_axis_t *a)
{
	axis_config_t *c = &cfg.axis_config[i];
	c->calib_min = a->calib_min; c->calib_center = a->calib_center; c->calib_max = a->calib_max;
	c->out_enabled = a->out_enabled; c->inverted = a->inverted; c->is_centered = a->is_centered;
	c->function = a->function; c->filter = a->filter;
	memcpy(c->curve_shape, a->curve, 11);
	c->resolution = a->resolution; c->channel = a->channel;
	c->deadband_size = a->deadband_size; c->is_dynamic_deadband = a->is_dynamic_deadband;
	c->source_main = a->source_main; c->source_secondary = a->source_secondary; c->offset_angle = a->offset_angle;
	c->button1 = a->button1; c->button2 = a->button2; c->button3 = a->button3;
	c->divider = a->divider; c->prescaler = a->prescaler;
	c->button1_type = a->button1_type; c->button2_type = a->button2_type; c->button3_type = a->button3_type;
}

/* The part of FreeJoy's AppConfigInit (config.c) that the button code relies
   on: POV direction buttons are marked disabled, so they're reported only
   through their hat. */
static void app_config_init(dev_config_t *c)
{
	for (uint8_t i = 0; i < MAX_BUTTONS_NUM; i++)
	{
		uint8_t t = c->buttons[i].type;
		if ((t >= POV1_UP && t <= POV1_LEFT) || (t >= POV2_UP && t <= POV2_LEFT) ||
		    (t >= POV3_UP && t <= POV3_LEFT) || (t >= POV4_UP && t <= POV4_LEFT))
			c->buttons[i].is_disabled = 1;
	}
}

void fjb_start(void)
{
	// analog sources 0-7 are FreeJoy's pins PA0-PA7
	for (int i = 0; i < MAX_AXIS_NUM; i++)
	{
		int8_t s = cfg.axis_config[i].source_main;
		if (s >= 0 && s < 8) cfg.pins[s] = AXIS_ANALOG;
	}
	app_config_init(&cfg);
	EncodersInit(&cfg);
	RadioButtons_Init(&cfg);
	SequentialButtons_Init(&cfg);
	AxesInit(&cfg);
}

/* ------------------------------------------------------------- run -- */

void fjb_step(int64_t now_ms, uint32_t raw27, const uint16_t *analog8)
{
	now = now_ms;
	for (int i = 0; i < 27; i++) raw_buttons_data[i] = (raw27 >> i) & 1;
	uint8_t pos = 27;
	a2b_first = pos;
	AxisToButtonsGet(raw_buttons_data, &cfg, &pos);
	a2b_last = pos;

	EncoderProcess(logical_buttons_state, &cfg);
	ButtonsDebounceProcess(&cfg);
	ButtonsReadLogical(&cfg);

	for (int k = 0; k < sensors_cnt; k++)
		if (sensors[k].type == ANALOG && sensors[k].source >= 0)
			adc_data[sensors[k].curr_channel] = analog8[sensors[k].source];
	AxesProcess(&cfg);
}

void fjb_get(uint8_t *log16, uint8_t *phy16, uint8_t *out16, uint8_t *pov4, int16_t *axes8, uint8_t *shift)
{
	ButtonsGet(out16, log16, phy16, shift);
	POVsGet(pov4);
	AnalogGet(axes8, NULL, NULL);
}

void fjb_get_axes_detail(int16_t *raw8, int16_t *scaled8)
{
	memcpy(raw8, raw_axis_data, 16);
	memcpy(scaled8, scaled_axis_data, 16);
}

void fjb_get_button_detail(int j, int *curr, int *prev, int *on, int *off, int *cur, int *act, int *time_last)
{
	logical_buttons_state_t *s = &logical_buttons_state[j];
	*curr = s->curr_physical_state; *prev = s->prev_physical_state; *on = s->on_state; *off = s->off_state;
	*cur = s->current_state; *act = s->delay_act; *time_last = (int)s->time_last;
}
