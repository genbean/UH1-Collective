/*
  board.cpp - HeliSR Rev 3.0 hardware: shift registers, analog inputs, spare pins

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Board wiring (PCB/HeliSR_Rev3.0/README.md):
    74HC165 latch (SH/LD) = Pro Micro pin 3 (PD0), data (U2 QH) = pin 2 (PD1),
    clock = pin 15 (PB1). Inputs have 10 k pull-ups; a closed switch reads 0.
    AX1-AX4 = A3, A2, A1, A0.
*/

#include <Arduino.h>
#include <util/atomic.h>
#include "board.h"

// Spare pins by index (Arduino pin numbers).
static const uint8_t SPARE_PIN[HSR_SPARE_PINS] = { 1, 0, 4, 5, 6, 7, 8, 9, 10, 14, 16 };

// Analog sources 0-8: AX1-AX4, then spare pins 4, 6, 8, 9, 10.
static const uint8_t ANALOG_PIN[HSR_ANALOG_SOURCES] = { A3, A2, A1, A0, A6, A7, A8, A9, A10 };
static const uint8_t ANALOG_SPARE_INDEX[HSR_ANALOG_SOURCES] = { 0xFF, 0xFF, 0xFF, 0xFF, 2, 4, 6, 7, 8 };

// Input number (1-16) for each bit in the order it leaves the chain
// (HeliSR_Rev3.0_Input_Map.csv): IN5-IN16 come out first, then IN1-IN4.
static const uint8_t BIT_TO_INPUT[HSR_SR_INPUTS] = { 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4 };

static uint16_t spare_button_mask;   // spare pins that are buttons
static uint16_t spare_vcc_mask;      // ...of which active high

// ------------------------------------------------------------------ ADC --
// The ADC runs from its interrupt: 16 samples per source (after one discarded
// sample on each channel change), then on to the next active source.

static uint8_t adc_sources[HSR_ANALOG_SOURCES];   // active source numbers
static uint8_t adc_channel[HSR_ANALOG_SOURCES];   // their ADC channels
static uint8_t adc_count;
static volatile uint16_t adc_value[HSR_ANALOG_SOURCES];

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

// ------------------------------------------------------------------ init --

void board_init(const dev_config_t *cfg)
{
	// 74HC165 lines
	DDRD |= (1 << PD0);       // latch out, idle high
	PORTD |= (1 << PD0);
	DDRD &= ~(1 << PD1);      // data in, no pull-up (driven by U2)
	PORTD &= ~(1 << PD1);
	DDRB |= (1 << PB1);       // clock out, idle low
	PORTB &= ~(1 << PB1);

	// Spare pins
	spare_button_mask = spare_vcc_mask = 0;
	for (uint8_t i = 0; i < HSR_SPARE_PINS; i++)
	{
		uint8_t pin = SPARE_PIN[i];
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

	// Analog sources: AX1-AX4 always (the board has connectors for them),
	// spare analog pins only when set to AXIS_ANALOG.
	adc_count = 0;
	for (uint8_t s = 0; s < HSR_ANALOG_SOURCES; s++)
	{
		uint8_t spare = ANALOG_SPARE_INDEX[s];
		if (spare != 0xFF && cfg->pins[spare] != PIN_AXIS_ANALOG) continue;
		adc_sources[adc_count] = s;
		adc_channel[adc_count] = analogPinToChannel(ANALOG_PIN[s] - A0);
		adc_count++;
	}
	adc_start();
}

// --------------------------------------------------------------- inputs --

uint16_t board_read_inputs(void)
{
	PORTD &= ~(1 << PD0);              // parallel load
	delayMicroseconds(1);
	PORTD |= (1 << PD0);               // shift mode; U2's H input is now on QH
	delayMicroseconds(1);

	uint16_t closed = 0;
	for (uint8_t bit = 0; bit < HSR_SR_INPUTS; bit++)
	{
		if (!(PIND & (1 << PD1)))      // pulled to GND = closed
			closed |= 1u << (BIT_TO_INPUT[bit] - 1);
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
		uint8_t high = digitalRead(SPARE_PIN[i]);
		if ((spare_vcc_mask & m) ? high : !high) pressed |= m;
	}
	return pressed;
}

void board_read_analog(uint16_t out[HSR_ANALOG_SOURCES])
{
	ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
	{
		for (uint8_t s = 0; s < HSR_ANALOG_SOURCES; s++) out[s] = adc_value[s];
	}
}

// ---------------------------------------------------------------- LEDs ---

void board_set_led(uint8_t spare_index, uint8_t on)
{
	if (spare_index < HSR_SPARE_PINS) digitalWrite(SPARE_PIN[spare_index], on ? HIGH : LOW);
}

void board_set_pwm(uint8_t spare_index, uint8_t duty_percent)
{
	if (spare_index >= HSR_SPARE_PINS) return;
	if (!(HSR_SPARE_PWM_MASK & (1u << spare_index)))
	{
		board_set_led(spare_index, duty_percent >= 50);
		return;
	}
	if (duty_percent > 100) duty_percent = 100;
	analogWrite(SPARE_PIN[spare_index], (uint16_t)duty_percent * 255 / 100);
}
