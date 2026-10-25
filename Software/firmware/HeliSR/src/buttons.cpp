/*
  buttons.cpp - debouncing, logical buttons, shifts, hats, axis-to-button
  ranges and encoders

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy)
  v1.7.3b1: application/Src/buttons.c, axis_to_buttons.c and encoders.c.
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026:
    - one pass over the logical buttons instead of FreeJoy's physical x logical
      double loop (64 x 64 is too slow on a 16 MHz AVR), in FreeJoy's order
      (by physical input, shifted mappings first), worked out at start-up;
    - 16-bit timestamps; raw inputs as bits;
    - no matrix or fast (timer) encoder; slow encoders are numbered from 0;
    - new SWITCH_CENTER type (on while this input and the next are both off);
    - a delayed button whose delay has run out always gets one press, even if
      a slow pass skipped past the press window;
    - sequential buttons start on the last button of every group (FreeJoy's
      start-up loop missed groups when there were three or more);
    - range checks where FreeJoy indexed with -1 (unused encoder pins).
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <Arduino.h>
#include <string.h>
#include "logic.h"
#include "settings.h"

#define CFG g_config

uint8_t      raw_bits[HSR_MAX_PHYS / 8];
phys_state_t phys_state[HSR_MAX_PHYS];
log_state_t  log_state[HSR_MAX_BUTTONS];
uint8_t      shifts_state;

static uint8_t pov_pos[HSR_MAX_POVS];             // direction bits: up 8, right 4, down 2, left 1
static uint8_t pov_mask;                          // hats in use
static uint8_t shift_any;                         // any shift button configured
static uint8_t phys_has_shift[HSR_MAX_PHYS / 8];  // inputs that some shifted button uses
static uint8_t order[HSR_MAX_BUTTONS];            // logical buttons in FreeJoy's processing order
static uint8_t order_cnt;

// ------------------------------------------------------------------ timers --

static uint16_t timer_ms(uint8_t timer, uint16_t otherwise)
{
	switch (timer)
	{
	case BUTTON_TIMER_1: return CFG.button_timer1_ms;
	case BUTTON_TIMER_2: return CFG.button_timer2_ms;
	case BUTTON_TIMER_3: return CFG.button_timer3_ms;
	default:             return otherwise;
	}
}

static void process_timer(log_state_t *st, uint16_t now, uint8_t num)
{
	const button_t *b = &CFG.buttons[num];
	uint16_t press = timer_ms(b->press_timer, 100);
	if (press == 0) press = 100;
	uint16_t delay = timer_ms(b->delay_timer, 0);

	// Centre POV buttons have a forced delay
	if (delay == 0 && (b->type == POV1_CENTER || b->type == POV2_CENTER)) delay = 100;

	uint16_t elapsed = now - st->time_last;
#ifndef HSR_FREEJOY_EXACT
	if (st->delay_act == BUTTON_ACTION_DELAY && elapsed > delay)
#else
	// FreeJoy's: a button that wasn't processed during its press window (its
	// input's shift layer was off) stays in DELAY for good
	if (st->delay_act == BUTTON_ACTION_DELAY && elapsed > delay && elapsed < (uint32_t)press + delay)
#endif
		st->delay_act = BUTTON_ACTION_PRESS;
	else if (st->delay_act == BUTTON_ACTION_PRESS && elapsed > (uint32_t)press + delay)
		st->delay_act = BUTTON_ACTION_IDLE;
	else if (st->delay_act == BUTTON_ACTION_BLOCK && elapsed > 100)   // blocking needed for Alps hats
		st->delay_act = BUTTON_ACTION_IDLE;
}

static void block_center(uint8_t center_type, uint16_t now)
{
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
	{
		if (CFG.buttons[i].type == center_type)
		{
			log_state[i].delay_act = BUTTON_ACTION_BLOCK;
			log_state[i].current_state = 0;
			log_state[i].time_last = now;
		}
	}
}

// ---------------------------------------------------------- logical state --

static void process_state(log_state_t *st, uint16_t now, uint8_t num)
{
	uint8_t type = CFG.buttons[num].type;
	process_timer(st, now, num);

	switch (type)
	{
	case BUTTON_NORMAL:
	case POV1_CENTER:
	case POV2_CENTER:
	case SWITCH_CENTER:
		if (st->delay_act == BUTTON_ACTION_DELAY)
		{
		}
		else if (st->delay_act == BUTTON_ACTION_PRESS)
			st->current_state = st->on_state;
		else if (st->curr_physical_state > st->prev_physical_state && st->delay_act != BUTTON_ACTION_BLOCK)
		{
			st->delay_act = BUTTON_ACTION_DELAY;
			st->time_last = now;
			st->on_state = st->curr_physical_state;
		}
		else if (st->delay_act == BUTTON_ACTION_BLOCK)
			st->current_state = 0;
		else
			st->current_state = st->curr_physical_state;
		break;

	case BUTTON_TOGGLE:
		if (st->delay_act == BUTTON_ACTION_DELAY)
		{
		}
		else if (st->delay_act == BUTTON_ACTION_PRESS)
			st->current_state = st->on_state;
		else if (st->curr_physical_state > st->prev_physical_state)
		{
			st->delay_act = BUTTON_ACTION_DELAY;
			st->time_last = now;
			st->on_state = !st->current_state;
			st->off_state = st->on_state;
		}
		break;

	case TOGGLE_SWITCH:
	case TOGGLE_SWITCH_ON:
	case TOGGLE_SWITCH_OFF:
	{
		uint8_t trigger;
		if (type == TOGGLE_SWITCH) trigger = st->curr_physical_state != st->prev_physical_state;
		else if (type == TOGGLE_SWITCH_ON) trigger = st->curr_physical_state > st->prev_physical_state;
		else trigger = st->curr_physical_state < st->prev_physical_state;

		if (st->delay_act == BUTTON_ACTION_DELAY)
		{
		}
		else if (st->delay_act == BUTTON_ACTION_PRESS)
			st->current_state = st->on_state;
		else if (trigger)
		{
			st->delay_act = BUTTON_ACTION_DELAY;
			st->time_last = now;
			st->on_state = 1;
			st->off_state = 0;
		}
		else
			st->current_state = st->off_state;
		break;
	}

	case POV1_UP: case POV1_RIGHT: case POV1_DOWN: case POV1_LEFT:
	case POV2_UP: case POV2_RIGHT: case POV2_DOWN: case POV2_LEFT:
	case POV3_UP: case POV3_RIGHT: case POV3_DOWN: case POV3_LEFT:
	case POV4_UP: case POV4_RIGHT: case POV4_DOWN: case POV4_LEFT:
	{
		uint8_t group = hsr_pov_of(type) - 1;
		uint8_t first = (group == 0) ? POV1_UP : (group == 1) ? POV2_UP : (group == 2) ? POV3_UP : POV4_UP;
		uint8_t bit = 3 - (type - first);   // up 3, right 2, down 1, left 0

		// block the centre button when a direction changes
		if (st->curr_physical_state != st->prev_physical_state)
		{
			if (group == 0) block_center(POV1_CENTER, now);
			else if (group == 1) block_center(POV2_CENTER, now);
		}

		if (st->delay_act == BUTTON_ACTION_DELAY)
		{
		}
		else if (st->delay_act == BUTTON_ACTION_PRESS)
			st->current_state = st->on_state;
		else if (st->curr_physical_state > st->prev_physical_state)
		{
			st->delay_act = BUTTON_ACTION_DELAY;
			st->time_last = now;
			st->on_state = st->curr_physical_state;
			st->off_state = !st->on_state;
		}
		else
			st->current_state = st->curr_physical_state;

		pov_pos[group] = (pov_pos[group] & ~(1 << bit)) | (st->current_state << bit);

		// turn the centre button off while a direction is pressed
		if (pov_pos[group])
		{
			if (group == 0) block_center(POV1_CENTER, now);
			else if (group == 1) block_center(POV2_CENTER, now);
		}
		break;
	}

	case RADIO_BUTTON1:
	case RADIO_BUTTON2:
	case RADIO_BUTTON3:
	case RADIO_BUTTON4:
		if (st->delay_act == BUTTON_ACTION_DELAY)
		{
		}
		else if (st->delay_act == BUTTON_ACTION_PRESS)
		{
			st->current_state = st->on_state;
			for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
				if (CFG.buttons[i].type == type && i != num)
					log_state[i].current_state = log_state[i].off_state;
		}
		else if (st->curr_physical_state)
		{
			st->delay_act = BUTTON_ACTION_DELAY;
			st->time_last = now;
			st->on_state = 1;
			st->off_state = 0;
		}
		break;

	case SEQUENTIAL_TOGGLE:
	case SEQUENTIAL_BUTTON:
		if (st->delay_act == BUTTON_ACTION_DELAY)
		{
		}
		else if (st->delay_act == BUTTON_ACTION_PRESS)
			st->current_state = st->on_state;
		else if (st->curr_physical_state > st->prev_physical_state)
		{
			// disable the enabled button of this group and enable the next one
			int8_t phys = CFG.buttons[num].physical_num;
			uint8_t is_last = 1, is_set_found = 0;
			for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
			{
				if (CFG.buttons[i].physical_num != phys || CFG.buttons[i].type != type) continue;
				log_state_t *s = &log_state[i];
				if (s->on_state == 1 && s->delay_act == BUTTON_ACTION_IDLE)
				{
					s->on_state = 0;
					s->off_state = 0;
					if (type == SEQUENTIAL_TOGGLE) s->current_state = 0;
					is_set_found = 1;
				}
				else if (is_set_found)
				{
					s->delay_act = BUTTON_ACTION_DELAY;
					s->time_last = now;
					s->on_state = 1;
					s->off_state = 0;
					is_last = 0;
					break;
				}
			}
			// the enabled one was last: wrap round to the first
			if (is_last && is_set_found)
			{
				for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
				{
					if (CFG.buttons[i].physical_num != phys || CFG.buttons[i].type != type) continue;
					log_state[i].delay_act = BUTTON_ACTION_DELAY;
					log_state[i].time_last = now;
					log_state[i].on_state = 1;
					log_state[i].off_state = 0;
					break;
				}
			}
		}
		else if (type == SEQUENTIAL_BUTTON && !st->curr_physical_state)
			st->current_state = st->off_state;
		break;

	default:        // encoder inputs: driven by encoders_process()
		break;
	}
}

static void update_physical(log_state_t *st, uint8_t num)
{
	const button_t *b = &CFG.buttons[num];
	uint8_t p = b->physical_num;
	st->prev_physical_state = st->curr_physical_state;
	if (b->type == SWITCH_CENTER)
		st->curr_physical_state = !phys_state[p].current_state &&
		                          (p + 1 >= HSR_MAX_PHYS || !phys_state[p + 1].current_state);
	else
		st->curr_physical_state = phys_state[p].current_state;
}

static void disable(log_state_t *st)
{
	st->delay_act = BUTTON_ACTION_IDLE;
	st->on_state = 0;
	st->off_state = 0;
	st->current_state = 0;
	st->curr_physical_state = 0;
	st->time_last = 0;
}

void buttons_logical(uint16_t now)
{
	for (uint8_t k = 0; k < order_cnt; k++)
	{
		uint8_t j = order[k];
		const button_t *b = &CFG.buttons[j];
		int8_t p = b->physical_num;
		log_state_t *st = &log_state[j];

		if (shift_any && bit_get(phys_has_shift, p))
		{
			// This input has shifted buttons: each mapping is live only in its own layer.
			uint8_t live = b->shift_modificator ? (shifts_state >> (b->shift_modificator - 1)) & 1
			                                    : (shifts_state == 0);
			if (live)
			{
				update_physical(st, j);
				process_state(st, now, j);
			}
			else if (st->current_state)
			{
				disable(st);
				process_state(st, now, j);
			}
		}
		else
		{
			update_physical(st, j);
			process_state(st, now, j);
		}
	}

	shifts_state = 0;
	for (uint8_t i = 0; i < HSR_MAX_SHIFTS; i++)
	{
		int8_t s = CFG.shift_config[i].button;
		if (s >= 0 && s < HSR_MAX_BUTTONS) shifts_state |= log_state[s].current_state << i;
	}
}

// --------------------------------------------------------------- debounce --

void buttons_debounce(uint16_t now, uint8_t a2b_end)
{
	for (uint8_t i = 0; i < HSR_MAX_PHYS; i++)
	{
		uint16_t debounce = (i >= HSR_PHYS_A2B_FIRST && i < a2b_end) ? CFG.a2b_debounce_ms : CFG.button_debounce_ms;
		phys_state_t *ps = &phys_state[i];
		ps->prev_pin_state = ps->pin_state;
		ps->pin_state = bit_get(raw_bits, i);
		uint16_t elapsed = now - ps->time_last;

		if (!ps->changed && ps->pin_state != ps->prev_pin_state)
		{
			ps->time_last = now;
			ps->changed = 1;
		}
		else if (ps->changed && ps->pin_state == ps->prev_pin_state && elapsed > debounce)
		{
			ps->changed = 0;
			ps->current_state = ps->pin_state;
		}
		else if (ps->changed && elapsed > debounce)
			ps->changed = 0;
	}
}

// --------------------------------------------------------- axis to buttons --

uint8_t a2b_get(const analog_data_t *scaled)
{
	uint8_t pos = HSR_PHYS_A2B_FIRST;
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
	{
		const axis_to_buttons_t *a2b = &CFG.axes_to_buttons[i];
		uint8_t cnt = a2b->buttons_cnt;
		if (cnt == 0) continue;
		if (cnt > HSR_A2B_POINTS - 1) cnt = HSR_A2B_POINTS - 1;

		int32_t value = ((int32_t)scaled[i] - AXIS_MIN_VALUE) * 255;
		uint8_t found = 0;
		for (uint8_t j = 0; j < cnt && pos < HSR_MAX_PHYS; j++, pos++)
		{
			int32_t lo = (int32_t)a2b->points[j] * AXIS_FULLSCALE;
			int32_t hi = (int32_t)a2b->points[j + 1] * AXIS_FULLSCALE;
			uint8_t pressed = !found && (j == 0 ? value >= lo : value > lo) && value <= hi;
			if (pressed) found = 1;
			bit_put(raw_bits, pos, pressed);
		}
	}
	for (uint8_t i = pos; i < HSR_MAX_PHYS; i++) bit_put(raw_bits, i, 0);
	return pos;
}

// --------------------------------------------------------------- encoders --

typedef struct
{
	uint16_t time_last;
	int16_t  cnt;
	uint8_t  state;
	int8_t   pin_a;         // logical button numbers
	int8_t   pin_b;
	int8_t   dir;
	int8_t   last_dir;
} encoder_state_t;

static encoder_state_t encoders_state[HSR_MAX_ENCODERS];
static uint8_t encoders_cnt;

static const int8_t ENC_TABLE[3][16] PROGMEM = {
	{ 0, 0, 0, 0,  -1, 0, 0, 0,  1, 0, 0, 0,  0, 0, 0, 0 },     // 1x
	{ 0, 0, 0, 0,  -1, 0, 0, 1,  1, 0, 0, -1, 0, 0, 0, 0 },     // 2x
	{ 0, 1, -1, 0, -1, 0, 0, 1,  1, 0, 0, -1, 0, -1, 1, 0 },    // 4x
};

static void encoders_init(void)
{
	int8_t prev_a = -1, prev_b = -1;
	encoders_cnt = 0;
	memset(encoders_state, 0, sizeof(encoders_state));
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS && encoders_cnt < HSR_MAX_ENCODERS; i++)
	{
		if (CFG.buttons[i].type != ENCODER_INPUT_A || (int8_t)i <= prev_a) continue;
		for (uint8_t j = 0; j < HSR_MAX_BUTTONS; j++)
		{
			if (CFG.buttons[j].type == ENCODER_INPUT_B && (int8_t)j > prev_b)
			{
				encoder_state_t *e = &encoders_state[encoders_cnt++];
				e->pin_a = i;
				e->pin_b = j;
				e->dir = e->last_dir = 1;
				prev_a = i;
				prev_b = j;
				break;
			}
		}
	}
}

static uint8_t raw_of(int8_t button)
{
	int8_t p = CFG.buttons[button].physical_num;
	return (p >= 0 && p < HSR_MAX_PHYS) ? bit_get(raw_bits, p) : 0;
}

// Press an encoder's button, unless it belongs to a shift layer that isn't
// active, or an active shifted encoder uses the same input.
static void encoder_fire(int8_t button, const int8_t *ignore, uint8_t n_ignore)
{
	const button_t *b = &CFG.buttons[button];
	if (b->shift_modificator)
	{
		if (shifts_state & (1 << (b->shift_modificator - 1))) log_state[button].current_state = 1;
		return;
	}
	for (uint8_t k = 0; k < n_ignore; k++)
		if (ignore[k] == b->physical_num) return;
	log_state[button].current_state = 1;
}

void encoders_process(uint16_t now)
{
	if (encoders_cnt == 0) return;

	// inputs used by encoders in an active shift layer
	int8_t ignore_a[HSR_MAX_ENCODERS], ignore_b[HSR_MAX_ENCODERS];
	uint8_t na = 0, nb = 0;
	for (uint8_t k = 0; k < encoders_cnt; k++)
	{
		const button_t *a = &CFG.buttons[encoders_state[k].pin_a];
		const button_t *b = &CFG.buttons[encoders_state[k].pin_b];
		if (a->shift_modificator && (shifts_state & (1 << (a->shift_modificator - 1)))) ignore_a[na++] = a->physical_num;
		if (b->shift_modificator && (shifts_state & (1 << (b->shift_modificator - 1)))) ignore_b[nb++] = b->physical_num;
	}

	for (uint8_t i = 0; i < encoders_cnt; i++)
	{
		encoder_state_t *e = &encoders_state[i];
		e->state <<= 2;
		if (raw_of(e->pin_a)) e->state |= 0x01;
		if (raw_of(e->pin_b)) e->state |= 0x02;

		if ((e->state & 0x03) != ((e->state >> 2) & 0x03))
		{
			uint8_t conf = CFG.encoders[i] <= ENCODER_CONF_4x ? CFG.encoders[i] : (uint8_t)ENCODER_CONF_1x;
			int8_t stt = (int8_t)pgm_read_byte(&ENC_TABLE[conf][e->state & 0x0F]);
			if (stt != 0)
			{
				uint16_t elapsed = now - e->time_last;
				e->dir = stt > 0 ? 1 : -1;
				if (elapsed > 50 || e->dir == e->last_dir)
				{
					if (stt > 0) encoder_fire(e->pin_a, ignore_a, na);         // CW
					else encoder_fire(e->pin_b, ignore_b, nb);                 // CCW
					e->last_dir = e->dir;
					e->time_last = now;
					int32_t c = (int32_t)e->cnt + stt;
					if (c >= AXIS_MIN_VALUE && c <= AXIS_MAX_VALUE) e->cnt = (int16_t)c;
				}
				else
				{
					// direction flipped within 50 ms: contact bounce, keep going the old way
					e->time_last = now;
					if ((e->last_dir > 0 && e->cnt < AXIS_MAX_VALUE) || (e->last_dir < 0 && e->cnt > AXIS_MIN_VALUE))
						e->cnt += e->last_dir;
					if (e->last_dir > 0) encoder_fire(e->pin_a, ignore_a, na);
					else encoder_fire(e->pin_b, ignore_b, nb);
				}
			}
		}
		else
			e->state >>= 2;

		// release the encoder buttons after their press time
		uint16_t press_a = timer_ms(CFG.buttons[e->pin_a].press_timer, CFG.encoder_press_time_ms);
		uint16_t press_b = timer_ms(CFG.buttons[e->pin_b].press_timer, CFG.encoder_press_time_ms);
		uint16_t elapsed = now - e->time_last;
		if (elapsed > press_a) log_state[e->pin_a].current_state = 0;
		if (elapsed > press_b) log_state[e->pin_b].current_state = 0;
	}
}

int16_t encoder_count(uint8_t n, int16_t lo, int16_t hi)
{
	if (n >= encoders_cnt) return 0;
	encoder_state_t *e = &encoders_state[n];
	if (e->cnt > hi) e->cnt = hi;
	if (e->cnt < lo) e->cnt = lo;
	return e->cnt;
}

// ------------------------------------------------------------------- init --

void buttons_init(void)
{
	memset(raw_bits, 0, sizeof(raw_bits));
	memset(phys_state, 0, sizeof(phys_state));
	memset(log_state, 0, sizeof(log_state));
	memset(pov_pos, 0, sizeof(pov_pos));
	memset(phys_has_shift, 0, sizeof(phys_has_shift));
	shifts_state = 0;

	shift_any = 0;
	for (uint8_t i = 0; i < HSR_MAX_SHIFTS; i++)
		if (CFG.shift_config[i].button >= 0) shift_any = 1;

	pov_mask = hsr_pov_mask(&CFG);
	for (uint8_t j = 0; j < HSR_MAX_BUTTONS; j++)
	{
		const button_t *b = &CFG.buttons[j];
		if (b->physical_num >= 0 && b->physical_num < HSR_MAX_PHYS && b->shift_modificator)
			bit_put(phys_has_shift, b->physical_num, 1);
	}

	// FreeJoy's order: input by input; on an input with shifted mappings (when
	// shifts are configured), the shifted logical buttons first, then the rest.
	// Buttons sharing state (hat bits, radio and sequential groups) depend on it.
	order_cnt = 0;
	for (uint8_t p = 0; p < HSR_MAX_PHYS; p++)
	{
		uint8_t split = shift_any && bit_get(phys_has_shift, p);
		for (uint8_t pass = 0; pass < (split ? 2 : 1); pass++)
			for (uint8_t j = 0; j < HSR_MAX_BUTTONS; j++)
			{
				const button_t *b = &CFG.buttons[j];
				if (b->physical_num != (int8_t)p) continue;
				if (split && (pass == 0) != (b->shift_modificator != 0)) continue;
				order[order_cnt++] = j;
			}
	}

	// radio buttons: the first of each group starts on
	for (uint8_t r = 0; r < 4; r++)
	{
		for (uint8_t j = 0; j < HSR_MAX_BUTTONS; j++)
		{
			if (CFG.buttons[j].type == RADIO_BUTTON1 + r)
			{
				log_state[j].on_state = 1;
				log_state[j].current_state = 1;
				break;
			}
		}
	}

	// sequential toggles: the first of each group starts on; sequential
	// buttons: the last of each group is marked, so the first press gives the first
	for (uint8_t j = 0; j < HSR_MAX_BUTTONS; j++)
	{
		const button_t *b = &CFG.buttons[j];
		if (b->type != SEQUENTIAL_TOGGLE && b->type != SEQUENTIAL_BUTTON) continue;
		if (b->physical_num < 0) continue;      // FreeJoy only looks at buttons with an input
		uint8_t first = 1, last = 1;
		for (uint8_t k = 0; k < HSR_MAX_BUTTONS; k++)
		{
			if (k == j || CFG.buttons[k].type != b->type || CFG.buttons[k].physical_num != b->physical_num) continue;
			if (k < j) first = 0;
			else last = 0;
		}
		if (b->type == SEQUENTIAL_TOGGLE && first)
		{
			log_state[j].on_state = 1;
			log_state[j].current_state = 1;
		}
		if (b->type == SEQUENTIAL_BUTTON && last) log_state[j].on_state = 1;
	}

	encoders_init();
}

// ----------------------------------------------------------------- report --

void buttons_get(uint8_t *out, uint8_t *log, uint8_t *phy, uint8_t *pov, uint8_t *shift)
{
	if (out) memset(out, 0, HSR_MAX_BUTTONS / 8);
	if (log) memset(log, 0, HSR_MAX_BUTTONS / 8);
	uint8_t k = 0;
	for (uint8_t i = 0; i < HSR_MAX_BUTTONS; i++)
	{
		const button_t *b = &CFG.buttons[i];
		uint8_t s = log_state[i].current_state ^ b->is_inverted;
		if (hsr_button_reported(b))
		{
			if (out && s) bit_put(out, k, 1);
			k++;
		}
		if (log && s) bit_put(log, i, 1);
	}

	if (phy)
	{
		memset(phy, 0, HSR_MAX_PHYS / 8);
		for (uint8_t i = 0; i < HSR_MAX_PHYS; i++)
			if (phys_state[i].current_state) bit_put(phy, i, 1);
	}

	if (pov)
	{
		// direction bits -> HID hat value (0 = up, clockwise in 45-degree steps)
		static const uint8_t HAT[16] PROGMEM = {
			0xFF, 6, 4, 5, 2, 0xFF, 3, 0xFF, 0, 7, 0xFF, 0xFF, 1, 0xFF, 0xFF, 0xFF };
		uint8_t n = 0;
		for (uint8_t g = 0; g < HSR_MAX_POVS; g++)
			if (pov_mask & (1 << g)) pov[n++] = pgm_read_byte(&HAT[pov_pos[g] & 0x0F]);
	}

	if (shift) *shift = shifts_state;
}
