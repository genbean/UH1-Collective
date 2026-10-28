/*
  i2c.cpp - HeliSR Rev 4.0: the ATmega32U4's TWI as an I2C master, and freeing a
  stuck bus with the PCA9546A's /RESET

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Pins (PCB/HeliSR_Rev4.0/README.md): SDA = pin 2 (PD1), SCL = pin 3 (PD0),
  each with a 10 k pull-up on the board; PCA9546A /RESET = A1 (PF6), with a
  10 k pull-up, so it is only ever pulled low (never driven high).
*/

#include "shared/helisr_config.h"
#if HSR_BOARD_REV == 40

#include <Arduino.h>
#include <util/twi.h>
#include "i2c.h"
#include "shared/helisr_protocol.h"

static uint8_t clock_khz = HSR_I2C_KHZ_DEFAULT;
static uint16_t step_limit_us;      // longest wait for one byte or condition

static void twi_on(void)
{
	// The internal pull-ups as well as the board's 10 k: a bare Pro Micro's bus
	// then idles high too, and an empty bus answers NACK instead of hanging.
	DDRD &= ~((1 << PD0) | (1 << PD1));
	PORTD |= (1 << PD0) | (1 << PD1);

	// SCL = F_CPU / (16 + 2 * TWBR * prescaler)
	uint16_t div = (uint16_t)(F_CPU / 1000UL / clock_khz) - 16;
	if (div / 2 <= 255) { TWSR = 0; TWBR = (uint8_t)(div / 2); }
	else                { TWSR = (1 << TWPS0); TWBR = (uint8_t)(div / 8); }   // prescaler 4
	TWCR = (1 << TWEN);
}

void i2c_begin(uint8_t khz)
{
	clock_khz = khz ? khz : HSR_I2C_KHZ_DEFAULT;
	// four byte times (9 clocks each), and some margin
	step_limit_us = (uint16_t)(36000UL / clock_khz) + 200;
	twi_on();
}

// Wait for the TWI to finish its step. 0 = timed out.
static uint8_t twi_wait(void)
{
	uint16_t t0 = (uint16_t)micros();
	while (!(TWCR & (1 << TWINT)))
		if ((uint16_t)((uint16_t)micros() - t0) > step_limit_us) return 0;
	return 1;
}

// Start (or repeated start), a byte out, a byte in: the TWI status after the
// step, or 0 if it timed out.
static uint8_t twi_start(void)
{
	TWCR = (1 << TWINT) | (1 << TWSTA) | (1 << TWEN);
	return twi_wait() ? TW_STATUS : 0;
}

static uint8_t twi_send(uint8_t b)
{
	TWDR = b;
	TWCR = (1 << TWINT) | (1 << TWEN);
	return twi_wait() ? TW_STATUS : 0;
}

static uint8_t twi_receive(uint8_t ack, uint8_t *b)
{
	TWCR = (1 << TWINT) | (1 << TWEN) | (ack ? (1 << TWEA) : 0);
	if (!twi_wait()) return 0;
	*b = TWDR;
	return TW_STATUS;
}

static void twi_stop(void)
{
	TWCR = (1 << TWINT) | (1 << TWSTO) | (1 << TWEN);
	uint16_t t0 = (uint16_t)micros();
	while (TWCR & (1 << TWSTO))
		if ((uint16_t)((uint16_t)micros() - t0) > step_limit_us) break;
}

// Something went wrong mid-transfer: let go of the bus. The next start turns
// the TWI on again.
static uint8_t twi_fail(uint8_t status)
{
	if (status == TW_MT_SLA_NACK || status == TW_MT_DATA_NACK || status == TW_MR_SLA_NACK)
	{
		twi_stop();
		return I2C_NACK;
	}
	TWCR = 0;
	return I2C_BUS_ERROR;
}

static uint8_t twi_begin(uint8_t addr_rw)
{
	uint8_t st = twi_start();
	if (st != TW_START && st != TW_REP_START) return twi_fail(st);
	st = twi_send(addr_rw);
	if (st != TW_MT_SLA_ACK && st != TW_MR_SLA_ACK) return twi_fail(st);
	return I2C_OK;
}

uint8_t i2c_write(uint8_t addr, const uint8_t *data, uint8_t len)
{
	uint8_t res = twi_begin((uint8_t)(addr << 1));
	if (res != I2C_OK) return res;
	while (len--)
	{
		uint8_t st = twi_send(*data++);
		if (st != TW_MT_DATA_ACK) return twi_fail(st);
	}
	twi_stop();
	return I2C_OK;
}

uint8_t i2c_read(uint8_t addr, uint8_t reg, uint8_t *buf, uint8_t len)
{
	uint8_t res = twi_begin((uint8_t)(addr << 1));
	if (res != I2C_OK) return res;
	uint8_t st = twi_send(reg);
	if (st != TW_MT_DATA_ACK) return twi_fail(st);
	res = twi_begin((uint8_t)((addr << 1) | 1));
	if (res != I2C_OK) return res;
	while (len)
	{
		len--;
		st = twi_receive(len != 0, buf++);      // acknowledge all but the last byte
		if (st != (len ? TW_MR_DATA_ACK : TW_MR_DATA_NACK)) return twi_fail(st);
	}
	twi_stop();
	return I2C_OK;
}

// Open-drain by hand: low = output low; released = input with the pull-up.
static void line(volatile uint8_t *ddr, volatile uint8_t *port, uint8_t bit, uint8_t high)
{
	if (high) { *ddr &= ~(1 << bit); *port |= (1 << bit); }
	else      { *port &= ~(1 << bit); *ddr |= (1 << bit); }
}

void i2c_recover(void)
{
	TWCR = 0;                                   // the TWI lets go of pins 2 and 3

	// /RESET low turns every channel off, so nothing behind the switch can hold
	// the bus. The datasheet asks for 6 ns; R11 pulls it back up.
	PORTF &= ~(1 << PF6);
	DDRF |= (1 << PF6);
	delayMicroseconds(10);
	DDRF &= ~(1 << PF6);
	delayMicroseconds(10);

	// If SDA is still low, a chip is part-way through sending a byte: clock it
	// out (at most 9 clocks). Then a START and a STOP, which every chip on the
	// bus takes as the end of whatever it was doing.
	uint8_t half = (uint8_t)(500 / clock_khz);  // half a clock period, us
	if (half < 5) half = 5;
	for (uint8_t i = 0; i < 9 && !(PIND & (1 << PD1)); i++)
	{
		line(&DDRD, &PORTD, PD0, 0);
		delayMicroseconds(half);
		line(&DDRD, &PORTD, PD0, 1);
		delayMicroseconds(half);
	}
	line(&DDRD, &PORTD, PD1, 0);                // START: SDA falls while SCL is high
	delayMicroseconds(half);
	line(&DDRD, &PORTD, PD1, 1);                // STOP: SDA rises while SCL is high
	delayMicroseconds(half);

	twi_on();
}

#endif
