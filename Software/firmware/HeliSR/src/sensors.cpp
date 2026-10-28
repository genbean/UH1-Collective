/*
  sensors.cpp - HeliSR Rev 4.0: the AS5600s on AX1-AX4, through the PCA9546A

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Every AS5600 is at 0x36, so each AX port has its own channel on the PCA9546A
  I2C switch (0x70), and the firmware talks to one port at a time
  (PCB/HeliSR_Rev4.0/README.md). One port per pass keeps a pass short: about
  170 clock periods of transfers, so 1.7 ms at 100 kHz and 17 ms at 10 kHz.
  A visit:
    1. connects the port's channel (and only it);
    2. if the sensor needs its range (new, back after an error, or the settings
       changed): writes ZPOS, then MPOS, then CONF = 0, 1 ms apart as the AS5600
       datasheet asks for its volatile registers, and reads them back. CONF 0
       is the chip's own power-up setting (normal power, no hysteresis, 16x
       slow filter, no fast filter, no watchdog), written so that a chip with
       other settings burnt in still reads the same. Nothing is ever burnt;
    3. reads ANGLE, which runs 0-4095 across that range: the axis value;
    4. makes one more read, in turn: STATUS and RAW ANGLE (for the helper and
       the magnet checks), AGC, or ZPOS to CONF again, which catches a sensor
       that restarted (and lost its range) without a failed transfer.
  A failed transfer marks the port and leaves its last angle in place. A stuck
  bus is freed at once with the switch's /RESET (i2c_recover), and the port
  that stuck it is left alone for 250 ms, so the others carry on; a switch
  that doesn't answer is reset at most every 250 ms.

  sensors_poll() only uses i2c.h, so the PC tests run it against a simulated
  bus (test/host/sensor_tests.cpp).
*/

#include "shared/helisr_config.h"
#if HSR_BOARD_REV == 40

#include <Arduino.h>
#include <avr/eeprom.h>
#include <string.h>
#include "sensors.h"
#include "i2c.h"

#define SWITCH_ADDR     0x70
#define AS5600_ADDR     0x36
#define REG_ZPOS        0x01    // ZPOS (2 bytes), then MPOS (2 bytes)
#define REG_MPOS        0x03
#define REG_CONF        0x07    // after MANG; bits 13-0
#define CONF_WANTED     0x0000
#define REG_STATUS      0x0B    // STATUS, then RAW ANGLE (2 bytes)
#define REG_ANGLE       0x0E
#define REG_AGC         0x1A
#define STATUS_MD       0x20    // magnet detected
#define STATUS_ML       0x10    // too weak
#define STATUS_MH       0x08    // too strong

#define RECOVER_MS      250

// EEPROM, after the space settings.cpp uses (6-657; the unique ID is at 1020)
#define EE_MAGIC        ((uint16_t *)960)
#define EE_CRC          ((uint16_t *)962)
#define EE_CONFIG       ((void *)964)
#define MAGIC           0x3453      // "S4"

// PCA9546A channel of AX1-AX4: the board's routing, not the port order.
static const uint8_t PORT_CHANNEL[HSR_AX_INPUTS] PROGMEM = { 2, 1, 3, 0 };

static hsr_sensor_config_t cfg;
static hsr_sensor_port_t port[HSR_AX_INPUTS];
static uint8_t need_range;          // bit n: port n's sensor must get its start and stop
static uint8_t next_port, turn;
static uint8_t bus_resets;
static uint8_t recovered;           // a recovery has run (last_recover_ms is set)
static uint16_t last_recover_ms;

static void defaults(hsr_sensor_config_t *c)
{
	memset(c, 0, sizeof(*c));
	c->version = HSR_SENSOR_CONFIG_VERSION;
	c->i2c_khz = HSR_I2C_KHZ_DEFAULT;
}

static uint8_t valid(const hsr_sensor_config_t *c)
{
	if (c->version != HSR_SENSOR_CONFIG_VERSION || !hsr_i2c_khz_valid(c->i2c_khz)) return 0;
	for (uint8_t n = 0; n < HSR_AX_INPUTS; n++)
		if (!hsr_sensor_range_valid(&c->range[n])) return 0;
	return 1;
}

static void load(void)
{
	if (eeprom_read_word(EE_MAGIC) == MAGIC)
	{
		eeprom_read_block(&cfg, EE_CONFIG, sizeof(cfg));
		if (hsr_crc16((const uint8_t *)&cfg, sizeof(cfg)) == eeprom_read_word(EE_CRC) && valid(&cfg)) return;
	}
	defaults(&cfg);
}

static void save(void)
{
	eeprom_update_block(&cfg, EE_CONFIG, sizeof(cfg));
	eeprom_update_word(EE_CRC, hsr_crc16((const uint8_t *)&cfg, sizeof(cfg)));
	eeprom_update_word(EE_MAGIC, MAGIC);
}

// The start and stop to write: the whole circle is both 0.
static void range_of(uint8_t n, uint16_t *z, uint16_t *m)
{
	*z = cfg.range[n].zpos;
	*m = cfg.range[n].mpos;
	if (*z == *m) *z = *m = 0;
}

static uint8_t recovered_lately(void)
{
	return recovered && (uint16_t)((uint16_t)millis() - last_recover_ms) < RECOVER_MS;
}

// always = 0: not if there was one in the last RECOVER_MS.
static void recover(uint8_t always)
{
	uint16_t now = (uint16_t)millis();
	if (!always && recovered_lately()) return;
	recovered = 1;
	last_recover_ms = now;
	i2c_recover();
	if (bus_resets < 255) bus_resets++;
}

// A transfer on port n failed: its sensor may have gone or restarted, so it
// gets its range again once it answers.
static void port_failed(uint8_t n, uint8_t res, uint8_t state)
{
	hsr_sensor_port_t *p = &port[n];
	if (p->errors < 0xFFFF) p->errors++;
	p->flags &= (uint8_t)~HSR_SENSOR_RANGE_OK;
	need_range |= (uint8_t)(1 << n);
	if (res == I2C_BUS_ERROR)
	{
		p->state = HSR_SENSOR_BUS_ERROR;
		recover(1);
	}
	else
		p->state = state;
}

static uint8_t write_reg2(uint8_t reg, uint16_t v)
{
	uint8_t b[3] = { reg, (uint8_t)(v >> 8), (uint8_t)v };
	return i2c_write(AS5600_ADDR, b, 3);
}

// Read ZPOS, MPOS (and MANG) and CONF back and compare them with the settings:
// sets or clears RANGE_OK, and with rewrite set asks for them to be written
// again if they differ (a chip that won't take them is retried every third
// visit, not on each).
static uint8_t check_range(uint8_t n, uint8_t rewrite)
{
	uint8_t b[8];
	uint8_t res = i2c_read(AS5600_ADDR, REG_ZPOS, b, 8);
	if (res != I2C_OK) return res;
	uint16_t z, m;
	range_of(n, &z, &m);
	if ((uint16_t)(((b[0] & 0x0F) << 8) | b[1]) == z && (uint16_t)(((b[2] & 0x0F) << 8) | b[3]) == m &&
	    (uint16_t)(((b[6] & 0x3F) << 8) | b[7]) == CONF_WANTED)
		port[n].flags |= HSR_SENSOR_RANGE_OK;
	else
	{
		port[n].flags &= (uint8_t)~HSR_SENSOR_RANGE_OK;
		if (rewrite) need_range |= (uint8_t)(1 << n);
	}
	return I2C_OK;
}

static uint8_t write_range(uint8_t n)
{
	uint16_t z, m;
	range_of(n, &z, &m);
	uint8_t res = write_reg2(REG_ZPOS, z);
	if (res != I2C_OK) return res;
	delay(1);
	res = write_reg2(REG_MPOS, m);
	if (res != I2C_OK) return res;
	delay(1);
	res = write_reg2(REG_CONF, CONF_WANTED);
	if (res != I2C_OK) return res;
	delay(1);
	need_range &= (uint8_t)~(1 << n);
	return check_range(n, 0);
}

static uint8_t state_of(uint8_t status)
{
	if (!(status & STATUS_MD)) return HSR_SENSOR_NO_MAGNET;
	if (status & STATUS_MH) return HSR_SENSOR_MAGNET_STRONG;
	if (status & STATUS_ML) return HSR_SENSOR_MAGNET_WEAK;
	return HSR_SENSOR_OK;
}

void sensors_poll(void)
{
	uint8_t n = next_port;
	next_port = (uint8_t)((n + 1) & 3);
	if (next_port == 0 && ++turn >= 3) turn = 0;
	hsr_sensor_port_t *p = &port[n];
	if (p->state == HSR_SENSOR_BUS_ERROR && recovered_lately()) return;    // it stuck the bus: not yet

	uint8_t channel = (uint8_t)(1 << pgm_read_byte(&PORT_CHANNEL[n]));
	uint8_t res = i2c_write(SWITCH_ADDR, &channel, 1);
	if (res != I2C_OK)
	{
		port_failed(n, res, HSR_SENSOR_NO_SWITCH);
		if (res == I2C_NACK) recover(0);        // the switch may be stuck: reset it
		return;
	}

	// a sensor that wasn't answering: its range now, and its status this visit
	uint8_t back = p->state == HSR_SENSOR_STARTING || p->state >= HSR_SENSOR_NO_SENSOR;
	if (need_range & (1 << n))
	{
		res = write_range(n);
		if (res != I2C_OK) { port_failed(n, res, HSR_SENSOR_NO_SENSOR); return; }
	}

	uint8_t b[3];
	res = i2c_read(AS5600_ADDR, REG_ANGLE, b, 2);
	if (res != I2C_OK) { port_failed(n, res, HSR_SENSOR_NO_SENSOR); return; }
	p->angle = (uint16_t)(((b[0] & 0x0F) << 8) | b[1]);

	switch (back ? 0 : (turn + n) % 3)
	{
	case 0:
		res = i2c_read(AS5600_ADDR, REG_STATUS, b, 3);
		if (res == I2C_OK)
		{
			p->status = b[0];
			p->raw_angle = (uint16_t)(((b[1] & 0x0F) << 8) | b[2]);
			p->state = state_of(b[0]);
		}
		break;
	case 1:
		res = i2c_read(AS5600_ADDR, REG_AGC, b, 1);
		if (res == I2C_OK) p->agc = b[0];
		break;
	default:
		res = check_range(n, 1);
		break;
	}
	if (res != I2C_OK) port_failed(n, res, HSR_SENSOR_NO_SENSOR);
}

void sensors_begin(void)
{
	load();
	memset(port, 0, sizeof(port));
	need_range = 0x0F;
	next_port = turn = 0;
	bus_resets = recovered = 0;
	i2c_begin(cfg.i2c_khz);
	for (uint8_t n = 0; n < HSR_AX_INPUTS; n++) sensors_poll();
}

uint16_t sensors_value(uint8_t n)
{
	if (n >= HSR_AX_INPUTS) return 0;
	return (uint16_t)(((uint32_t)port[n].angle * HSR_RAW_MAX + 2047) / 4095);
}

void sensors_status(hsr_sensor_status_t *s)
{
	s->i2c_khz = cfg.i2c_khz;
	s->bus_resets = bus_resets;
	memcpy(s->port, port, sizeof(port));
}

const hsr_sensor_config_t *sensors_config(void)
{
	return &cfg;
}

uint8_t sensors_set_config(const hsr_sensor_config_t *c)
{
	if (!valid(c)) return HSR_ERR_VALUE;
	for (uint8_t n = 0; n < HSR_AX_INPUTS; n++)
	{
		if (c->range[n].zpos != cfg.range[n].zpos || c->range[n].mpos != cfg.range[n].mpos)
		{
			need_range |= (uint8_t)(1 << n);
			port[n].flags &= (uint8_t)~HSR_SENSOR_RANGE_OK;
		}
	}
	uint8_t khz = cfg.i2c_khz;
	cfg = *c;
	save();
	if (cfg.i2c_khz != khz) i2c_begin(cfg.i2c_khz);
	return HSR_OK;
}

#endif
