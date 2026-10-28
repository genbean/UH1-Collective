/*
  board.cpp - HeliSR board hardware: shift registers, analog inputs, AS5600s
  (Rev 4.0), spare pins

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Rev 3.0 wiring (PCB/HeliSR_Rev3.0/README.md):
    74HC165 latch (SH/LD) = Pro Micro pin 3 (PD0), data (U2 QH) = pin 2 (PD1),
    clock = pin 15 (PB1). Inputs have 10 k pull-ups; a closed switch reads 0.
    AX1-AX4 = A3, A2, A1, A0.
  Rev 4.0 wiring (PCB/HeliSR_Rev4.0/README.md):
    74HC165 load (SH/LD) = A0 (PF7), data (U2 QH) = pin 14 (PB3), clock = pin 15
    (PB1); the chain itself is Rev 3.0's, so the bits come out in the same order.
    I2C on pins 2 (SDA) and 3 (SCL), PCA9546A /RESET on A1 (PF6): sensors.cpp.
    A2 and A3 are free, as analog sources 9 and 10.
*/

#include <Arduino.h>
#include <util/atomic.h>
#include "board.h"
#if HSR_BOARD_REV == 40
#include "sensors.h"
#endif

// Spare pins by index (Arduino pin numbers). Rev 4.0 has no spare pin 9 (pin 14).
static const uint8_t SPARE_PIN[HSR_SPARE_PINS] PROGMEM = { 1, 0, 4, 5, 6, 7, 8, 9, 10, 14, 16 };

// Analog sources read by the ADC, with their pins; 0xFF = not an ADC input on this board.
//   Rev 3.0: AX1-AX4, then spare pins 4, 6, 8, 9, 10.
//   Rev 4.0: AX1-AX4 are the AS5600s; then the same spare pins, then A2 and A3.
#if HSR_BOARD_REV == 40
static const uint8_t ANALOG_PIN[HSR_BOARD_SOURCES] PROGMEM = { 0xFF, 0xFF, 0xFF, 0xFF, A6, A7, A8, A9, A10, A2, A3 };
static const uint8_t ANALOG_SPARE_INDEX[HSR_BOARD_SOURCES] PROGMEM = { 0xFF, 0xFF, 0xFF, 0xFF, 2, 4, 6, 7, 8, 0xFF, 0xFF };
#else
static const uint8_t ANALOG_PIN[HSR_BOARD_SOURCES] PROGMEM = { A3, A2, A1, A0, A6, A7, A8, A9, A10 };
static const uint8_t ANALOG_SPARE_INDEX[HSR_BOARD_SOURCES] PROGMEM = { 0xFF, 0xFF, 0xFF, 0xFF, 2, 4, 6, 7, 8 };
#endif

// Input number (1-16) for each bit in the order it leaves the chain
// (HeliSR_Rev3.0_Input_Map.csv, and Rev 4.0's, which is the same):
// IN5-IN16 come out first, then IN1-IN4.
static const uint8_t BIT_TO_INPUT[HSR_SR_INPUTS] PROGMEM = { 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4 };

// The shift registers' load and data lines.
#if HSR_BOARD_REV == 40
#define SR_LOAD_PORT    PORTF
#define SR_LOAD_DDR     DDRF
#define SR_LOAD_BIT     PF7
#define SR_DATA_PIN     PINB
#define SR_DATA_PORT    PORTB
#define SR_DATA_DDR     DDRB
#define SR_DATA_BIT     PB3
#else
#define SR_LOAD_PORT    PORTD
#define SR_LOAD_DDR     DDRD
#define SR_LOAD_BIT     PD0
#define SR_DATA_PIN     PIND
#define SR_DATA_PORT    PORTD
#define SR_DATA_DDR     DDRD
#define SR_DATA_BIT     PD1
#endif

static uint16_t spare_button_mask;   // spare pins that are buttons
static uint16_t spare_vcc_mask;      // ...of which active high

// ------------------------------------------------------------------ ADC --
// The ADC runs from its interrupt: 16 samples per source (after one discarded
// sample on each channel change), then on to the next active source.

static uint8_t adc_sources[HSR_BOARD_SOURCES];   // active source numbers
static uint8_t adc_channel[HSR_BOARD_SOURCES];   // their ADC channels
static uint8_t adc_count;
static volatile uint16_t adc_value[HSR_BOARD_SOURCES];

static uint8_t adc_pos, adc_samples, adc_discard;
static uint16_t adc_sum;

static void adc_select(uint8_t channel)
{
	ADCSRB = (ADCSRB & ~(1 << MUX5)) | (((channel >> 3) & 1) << MUX5);
	ADMUX = (1 << REFS0) | (channel & 0x07);   // AVcc reference
}

ISR(ADC_vect)
{
	uint16_t v = ADC;
	if (adc_discard)
	{
		adc_discard = 0;
	}
	else
	{
		adc_sum += v;
		if (++adc_samples == 16)
		{
			adc_value[adc_sources[adc_pos]] = adc_sum >> 2;
			adc_sum = 0;
			adc_samples = 0;
			if (++adc_pos >= adc_count) adc_pos = 0;
			adc_select(adc_channel[adc_pos]);
			adc_discard = 1;
		}
	}
	ADCSRA |= (1 << ADSC);
}

static void adc_start(void)
{
	ADCSRA = 0;
	if (adc_count == 0) return;
	adc_pos = adc_samples = 0;
	adc_sum = 0;
	adc_discard = 1;
	adc_select(adc_channel[0]);
	// enable, interrupt, clock 16 MHz / 64 = 250 kHz (8 MHz / 32 on 8 MHz boards)
#if F_CPU >= 16000000L
	ADCSRA = (1 << ADEN) | (1 << ADIE) | (1 << ADPS2) | (1 << ADPS1);
#else
	ADCSRA = (1 << ADEN) | (1 << ADIE) | (1 << ADPS2) | (1 << ADPS0);
#endif
	ADCSRA |= (1 << ADSC);
}

// Whether the board samples analog source s with these settings: AX1-AX4
// always on Rev 3.0 (the board has connectors for them), spare analog pins when
// set to AXIS_ANALOG, and Rev 4.0's A2 and A3 when an axis uses them.
static uint8_t adc_wanted(const dev_config_t *cfg, uint8_t s)
{
	if (pgm_read_byte(&ANALOG_PIN[s]) == 0xFF) return 0;
	uint8_t spare = pgm_read_byte(&ANALOG_SPARE_INDEX[s]);
	if (spare != 0xFF) return cfg->pins[spare] == PIN_AXIS_ANALOG;
#if HSR_BOARD_REV == 40
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++)
		if (cfg->axis_config[i].source_main == (axis_source_t)s) return 1;
	return 0;
#else
	return 1;
#endif
}

// ------------------------------------------------------------------ init --

void board_init(const dev_config_t *cfg)
{
#if HSR_BOARD_REV == 40
	// A0 and A1 (PF7, PF6) are also JTAG's TDI and TDO, and A2 and A3 its TMS
	// and TCK. SparkFun ships the Pro Micro with JTAG off in its fuses, but a
	// clone may leave it on, which keeps them from working as plain I/O: turn
	// JTAG off. JTD must be written twice within four cycles.
	uint8_t mcucr = MCUCR | (1 << JTD);
	ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
	{
		MCUCR = mcucr;
		MCUCR = mcucr;
	}
#endif

	// 74HC165 lines
	SR_LOAD_DDR |= (1 << SR_LOAD_BIT);      // load out, idle high
	SR_LOAD_PORT |= (1 << SR_LOAD_BIT);
	SR_DATA_DDR &= ~(1 << SR_DATA_BIT);     // data in, no pull-up (driven by U2)
	SR_DATA_PORT &= ~(1 << SR_DATA_BIT);
	DDRB |= (1 << PB1);                     // clock out, idle low
	PORTB &= ~(1 << PB1);

	// Spare pins
	spare_button_mask = spare_vcc_mask = 0;
	for (uint8_t i = 0; i < HSR_SPARE_PINS; i++)
	{
		if (!hsr_spare_exists(HSR_BOARD_ID, i)) continue;    // Rev 4.0's pin 14 is the data line
		uint8_t pin = pgm_read_byte(&SPARE_PIN[i]);
		switch (cfg->pins[i])
		{
		case PIN_BUTTON_GND:
			pinMode(pin, INPUT_PULLUP);
			spare_button_mask |= 1u << i;
			break;
		case PIN_BUTTON_VCC:
			pinMode(pin, INPUT);
			spare_button_mask |= 1u << i;
			spare_vcc_mask |= 1u << i;
			break;
		case PIN_AXIS_ANALOG:
			pinMode(pin, (HSR_SPARE_ANALOG_MASK & (1u << i)) ? INPUT : INPUT_PULLUP);
			break;
		case PIN_LED_SINGLE:
		case PIN_LED_PWM:
			pinMode(pin, OUTPUT);
			digitalWrite(pin, LOW);
			break;
		default:
			pinMode(pin, INPUT_PULLUP);   // unused: don't leave it floating
			break;
		}
	}

#if HSR_BOARD_REV == 40
	// A2 and A3: analog inputs while an axis uses them, else pulled up like an unused spare pin
	pinMode(A2, adc_wanted(cfg, HSR_SOURCE_A2) ? INPUT : INPUT_PULLUP);
	pinMode(A3, adc_wanted(cfg, HSR_SOURCE_A3) ? INPUT : INPUT_PULLUP);
#endif

#ifdef HSR_TEST_AX_PULLUPS
	// Test builds only: pull AX1-AX4 up, so unconnected inputs read full scale.
	// Proves the ADC is sampling on a bare Pro Micro.
	for (uint8_t s = 0; s < HSR_AX_INPUTS; s++)
		if (pgm_read_byte(&ANALOG_PIN[s]) != 0xFF) pinMode(pgm_read_byte(&ANALOG_PIN[s]), INPUT_PULLUP);
#endif

	adc_count = 0;
	for (uint8_t s = 0; s < HSR_BOARD_SOURCES; s++)
	{
		if (!adc_wanted(cfg, s)) continue;
		adc_sources[adc_count] = s;
		adc_channel[adc_count] = analogPinToChannel(pgm_read_byte(&ANALOG_PIN[s]) - A0);
		adc_count++;
	}
	adc_start();

#if HSR_BOARD_REV == 40
	sensors_begin();
#endif
}

#if HSR_BOARD_REV == 40
void board_poll(void)
{
	sensors_poll();
}
#endif

// --------------------------------------------------------------- inputs --

uint16_t board_read_inputs(void)
{
	SR_LOAD_PORT &= ~(1 << SR_LOAD_BIT);    // parallel load
	delayMicroseconds(1);
	SR_LOAD_PORT |= (1 << SR_LOAD_BIT);     // shift mode; U2's H input is now on QH
	delayMicroseconds(1);

	uint16_t closed = 0;
	for (uint8_t bit = 0; bit < HSR_SR_INPUTS; bit++)
	{
		if (!(SR_DATA_PIN & (1 << SR_DATA_BIT)))    // pulled to GND = closed
			closed |= 1u << (pgm_read_byte(&BIT_TO_INPUT[bit]) - 1);
		PORTB |= (1 << PB1);           // rising edge shifts the next bit onto QH
		delayMicroseconds(1);
		PORTB &= ~(1 << PB1);
		delayMicroseconds(1);
	}
	return closed;
}

uint16_t board_read_spare_buttons(void)
{
	uint16_t pressed = 0;
	for (uint8_t i = 0; i < HSR_SPARE_PINS; i++)
	{
		uint16_t m = 1u << i;
		if (!(spare_button_mask & m)) continue;
		uint8_t high = digitalRead(pgm_read_byte(&SPARE_PIN[i]));
		if ((spare_vcc_mask & m) ? high : !high) pressed |= m;
	}
	return pressed;
}

void board_read_analog(uint16_t out[HSR_BOARD_SOURCES])
{
	ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
	{
		for (uint8_t s = 0; s < HSR_BOARD_SOURCES; s++) out[s] = adc_value[s];
	}
#if HSR_BOARD_REV == 40
	for (uint8_t s = 0; s < HSR_AX_INPUTS; s++) out[s] = sensors_value(s);
#endif
}

// ---------------------------------------------------------------- LEDs ---

void board_set_led(uint8_t spare_index, uint8_t on)
{
	if (hsr_spare_exists(HSR_BOARD_ID, spare_index))
		digitalWrite(pgm_read_byte(&SPARE_PIN[spare_index]), on ? HIGH : LOW);
}

void board_set_pwm(uint8_t spare_index, uint8_t duty_percent)
{
	if (!hsr_spare_exists(HSR_BOARD_ID, spare_index)) return;
	if (!(HSR_SPARE_PWM_MASK & (1u << spare_index)))
	{
		board_set_led(spare_index, duty_percent >= 50);
		return;
	}
	if (duty_percent > 100) duty_percent = 100;
	analogWrite(pgm_read_byte(&SPARE_PIN[spare_index]), (uint16_t)duty_percent * 255 / 100);
}
