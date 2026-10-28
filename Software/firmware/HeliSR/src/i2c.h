/*
  i2c.h - HeliSR Rev 4.0: the ATmega32U4's TWI as an I2C master, and freeing a
  stuck bus with the PCA9546A's /RESET

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Every call waits for the bus (no interrupts), each step with a time limit
  scaled to the clock, so a stuck line can't hang the firmware. sensors.cpp
  uses only these functions, and the PC tests stand in for them.
*/

#ifndef HELISR_I2C_H
#define HELISR_I2C_H

#include <stdint.h>

enum
{
	I2C_OK = 0,
	I2C_NACK,           // no acknowledge: nothing at that address, or it refused a byte
	I2C_BUS_ERROR,      // a step timed out or arbitration was lost: a line is held low
};

// TWI on pins 2 (SDA) and 3 (SCL) at this clock (kHz).
void i2c_begin(uint8_t khz);

// Write len bytes to the device at addr (7-bit).
uint8_t i2c_write(uint8_t addr, const uint8_t *data, uint8_t len);

// Write the register number, then read len bytes from there (repeated start).
uint8_t i2c_read(uint8_t addr, uint8_t reg, uint8_t *buf, uint8_t len);

// Free the bus: pulse the PCA9546A's /RESET (every channel off), clock out a
// byte that something on the Pro Micro's side is still sending, send a STOP,
// and start the TWI again.
void i2c_recover(void);

#endif
