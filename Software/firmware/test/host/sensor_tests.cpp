/*
  sensor_tests.cpp - HeliSR Rev 4.0's AS5600 code (sensors.cpp), run against a
  simulated I2C bus: the board's PCA9546A switch and an AS5600 on each of its
  channels. No Rev 4.0 board has been built yet, so this is what checks the
  sequences the firmware sends: the channel of each port, the registers, the
  byte order, the 1 ms waits, the read-back, and what happens when a sensor or
  the switch goes missing or the bus sticks.

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  The model follows the datasheets as the firmware reads them (AS5600
  ams-OSRAM DS000365, PCA9546A TI SCPS148I), not a real chip: it shows the
  firmware does what it means to, not that the chips agree.
*/

#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <string>
#include <vector>
#include "sim.h"
#include "../../HeliSR/src/i2c.h"
#include "../../HeliSR/src/sensors.h"

extern unsigned long host_millis;

// ------------------------------------------------------------- the model --

struct FakeAs5600
{
	bool present = true;
	bool takes_range = true;        // false: ZPOS/MPOS writes don't stick
	bool holds_bus = false;         // holds SDA low while its channel is connected
	uint16_t zpos = 0, mpos = 0;    // volatile registers, 0 after power-up
	uint16_t raw = 0;
	uint8_t status = 0x20;          // MD: magnet detected
	uint8_t agc = 128;

	uint16_t angle() const
	{
		if (zpos == mpos) return raw;
		uint16_t span = (uint16_t)((mpos - zpos) & 4095);
		uint16_t d = (uint16_t)((raw - zpos) & 4095);
		if (d > span) d = (d - span < (4096 - span) / 2) ? span : 0;   // past an end: held there
		return (uint16_t)((uint32_t)d * 4095 / span);
	}
	void power_cycle() { zpos = mpos = 0; }
	uint8_t reg(uint8_t r) const
	{
		switch (r)
		{
		case 0x01: return (uint8_t)(zpos >> 8);
		case 0x02: return (uint8_t)zpos;
		case 0x03: return (uint8_t)(mpos >> 8);
		case 0x04: return (uint8_t)mpos;
		case 0x0B: return status;
		case 0x0C: return (uint8_t)(raw >> 8);
		case 0x0D: return (uint8_t)raw;
		case 0x0E: return (uint8_t)(angle() >> 8);
		case 0x0F: return (uint8_t)angle();
		case 0x1A: return agc;
		default:   return 0;
		}
	}
};

struct FakeBus
{
	bool switch_present = true;
	uint8_t control = 0;            // PCA9546A control register: channels connected
	FakeAs5600 chip[4];             // by PCA9546A channel
	int recoveries = 0, begins = 0, khz = 0;
	int multi_channel = 0;          // transfers with more than one channel connected
	int burns = 0;                  // writes to the AS5600's BURN register (0xFF)
	std::vector<std::string> log;
	unsigned long zpos_written_at[4];
	int zpos_writes[4], mpos_writes[4];
	int mpos_too_soon = 0;          // MPOS written less than 1 ms after ZPOS

	void reset()
	{
		*this = FakeBus();
		for (int c = 0; c < 4; c++) { zpos_written_at[c] = 0; zpos_writes[c] = mpos_writes[c] = 0; }
	}
	bool stuck() const
	{
		for (int c = 0; c < 4; c++)
			if ((control & (1 << c)) && chip[c].present && chip[c].holds_bus) return true;
		return false;
	}
	// the one chip connected, or NULL (none, or nobody home)
	FakeAs5600 *connected(int *channel)
	{
		int n = 0, ch = -1;
		for (int c = 0; c < 4; c++) if (control & (1 << c)) { n++; ch = c; }
		if (n > 1) multi_channel++;
		if (n != 1 || !chip[ch].present) return NULL;
		*channel = ch;
		return &chip[ch];
	}
} bus;

static char text[96];

void i2c_begin(uint8_t khz) { bus.begins++; bus.khz = khz; }

void i2c_recover(void)
{
	bus.recoveries++;
	bus.control = 0;                // /RESET: every channel off
	bus.log.push_back("recover");
}

uint8_t i2c_write(uint8_t addr, const uint8_t *data, uint8_t len)
{
	if (bus.stuck()) return I2C_BUS_ERROR;
	snprintf(text, sizeof(text), "W%02X", addr);
	std::string s = text;
	for (int i = 0; i < len; i++) { snprintf(text, sizeof(text), " %02X", data[i]); s += text; }
	bus.log.push_back(s);

	if (addr == 0x70)
	{
		if (!bus.switch_present) return I2C_NACK;
		if (len != 1) return I2C_NACK;
		bus.control = data[0];
		return I2C_OK;
	}
	int ch;
	FakeAs5600 *a = (addr == 0x36) ? bus.connected(&ch) : NULL;
	if (!a) return I2C_NACK;
	if (len < 1) return I2C_OK;
	uint8_t r = data[0];
	if (r == 0xFF && len > 1) bus.burns++;
	if (len == 3 && (r == 0x01 || r == 0x03))
	{
		uint16_t v = (uint16_t)(((data[1] & 0x0F) << 8) | data[2]);
		if (r == 0x01) { bus.zpos_writes[ch]++; bus.zpos_written_at[ch] = host_millis; }
		else
		{
			bus.mpos_writes[ch]++;
			if (host_millis - bus.zpos_written_at[ch] < 1) bus.mpos_too_soon++;
		}
		if (a->takes_range) (r == 0x01 ? a->zpos : a->mpos) = v;
	}
	return I2C_OK;
}

uint8_t i2c_read(uint8_t addr, uint8_t reg, uint8_t *buf, uint8_t len)
{
	if (bus.stuck()) return I2C_BUS_ERROR;
	snprintf(text, sizeof(text), "R%02X %02X x%d", addr, reg, len);
	bus.log.push_back(text);
	int ch;
	FakeAs5600 *a = (addr == 0x36) ? bus.connected(&ch) : NULL;
	if (!a) return I2C_NACK;
	for (int i = 0; i < len; i++) buf[i] = a->reg((uint8_t)(reg + i));
	return I2C_OK;
}

void delay(unsigned long ms) { host_millis += ms; }

// ----------------------------------------------------------------- helpers --

static const int CHANNEL_OF[4] = { 2, 1, 3, 0 };    // AX1-AX4, from the board's README

static FakeAs5600 &chip_of(int port) { return bus.chip[CHANNEL_OF[port]]; }

static hsr_sensor_status_t status_now()
{
	hsr_sensor_status_t s;
	sensors_status(&s);
	return s;
}

// visit every port `rotations` times, 2 ms apart
static void rotate(int rotations)
{
	for (int i = 0; i < rotations * 4; i++) { sensors_poll(); host_millis += 2; }
}

static void fresh_start()
{
	memset(host_eeprom, 0xFF, sizeof(host_eeprom));
	bus.reset();
	host_millis = 5000;
}

static uint16_t scaled(uint16_t angle) { return (uint16_t)(((uint32_t)angle * HSR_RAW_MAX + 2047) / 4095); }

static hsr_sensor_config_t config_with(int port, uint16_t z, uint16_t m)
{
	hsr_sensor_config_t c = *sensors_config();
	c.range[port].zpos = z;
	c.range[port].mpos = m;
	return c;
}

// ------------------------------------------------------------------- tests --

static void t_sensor_layout()
{
	scenario("Rev 4.0 messages: sizes and places");
	CHECK_EQ(sizeof(hsr_build_tag_t), 20);
	CHECK_EQ(sizeof(hsr_sensor_config_t), 18);
	CHECK_EQ(sizeof(hsr_sensor_status_t), 42);
	CHECK_EQ(sizeof(params_report_t), HSR_PARAMS_SIZE);
	CHECK_EQ(offsetof(params_report_t, analog_inputs), 34);
	CHECK_EQ(offsetof(params_report_t, phy_button_data), 52);     // where Rev 3.0's live data has it
	CHECK_EQ(offsetof(params_report_t, analog_inputs_a2a3), 69);   // after the rest
	CHECK_EQ(HSR_CMD_SENSOR_STATUS, 9);
	CHECK_EQ(HSR_CMD_SENSOR_CONFIG, 10);
	CHECK(hsr_spare_exists(HSR_BOARD_REV30, 9) && !hsr_spare_exists(HSR_BOARD_REV40, 9));
	CHECK(hsr_spare_exists(HSR_BOARD_REV40, 10) && !hsr_spare_exists(HSR_BOARD_REV40, 11));
	CHECK(hsr_source_exists(HSR_BOARD_REV30, 8) && !hsr_source_exists(HSR_BOARD_REV30, HSR_SOURCE_A2));
	CHECK(hsr_source_exists(HSR_BOARD_REV40, HSR_SOURCE_A3) && !hsr_source_exists(HSR_BOARD_REV40, 11));
}

static void t_sensor_defaults()
{
	scenario("AS5600: factory settings, and each port on its own channel");
	fresh_start();
	for (int p = 0; p < 4; p++) chip_of(p).raw = (uint16_t)(1000 * p + 123);
	sensors_begin();
	CHECK_EQ(bus.khz, 100);
	const hsr_sensor_config_t *c = sensors_config();
	CHECK_EQ(c->version, HSR_SENSOR_CONFIG_VERSION);
	for (int p = 0; p < 4; p++) CHECK(c->range[p].zpos == 0 && c->range[p].mpos == 0);

	// the first visits connect AX1-AX4's channels in turn, one at a time
	std::vector<std::string> selects;
	for (const std::string &l : bus.log) if (l.compare(0, 3, "W70") == 0) selects.push_back(l);
	CHECK(selects.size() == 4 && selects[0] == "W70 04" && selects[1] == "W70 02" && selects[2] == "W70 08" && selects[3] == "W70 01");
	CHECK_EQ(bus.multi_channel, 0);

	rotate(3);
	for (int p = 0; p < 4; p++) CHECK_EQ(sensors_value(p), scaled((uint16_t)(1000 * p + 123)));
	hsr_sensor_status_t s = status_now();
	CHECK_EQ(s.i2c_khz, 100);
	for (int p = 0; p < 4; p++)
	{
		CHECK_EQ(s.port[p].state, HSR_SENSOR_OK);
		CHECK_EQ(s.port[p].raw_angle, 1000 * p + 123);
		CHECK_EQ(s.port[p].agc, 128);
		CHECK_EQ(s.port[p].errors, 0);
		CHECK(s.port[p].flags & HSR_SENSOR_RANGE_OK);      // whole circle: 0 and 0, read back
	}
	CHECK_EQ(s.bus_resets, 0);
	CHECK_EQ(bus.burns, 0);

	// the readings span the analog sources' range
	chip_of(0).raw = 4095; chip_of(1).raw = 0; chip_of(2).raw = 2048;
	rotate(1);
	CHECK_EQ(sensors_value(0), HSR_RAW_MAX);
	CHECK_EQ(sensors_value(1), 0);
	CHECK_EQ(sensors_value(2), scaled(2048));
	CHECK_EQ(scaled(2048), 2046);
}

static void t_sensor_range()
{
	scenario("AS5600: start and stop written to ZPOS and MPOS, 1 ms apart, kept in EEPROM");
	fresh_start();
	sensors_begin();
	rotate(2);
	int z0 = bus.zpos_writes[CHANNEL_OF[0]];

	hsr_sensor_config_t c = config_with(0, 1000, 3000);
	c.range[3].zpos = 3900;                 // AX4 across 0: 3900 up to 200 is 396 counts
	c.range[3].mpos = 200;
	CHECK_EQ(sensors_set_config(&c), HSR_OK);
	CHECK(!(status_now().port[0].flags & HSR_SENSOR_RANGE_OK));
	rotate(1);
	CHECK(chip_of(0).zpos == 1000 && chip_of(0).mpos == 3000);
	CHECK(chip_of(3).zpos == 3900 && chip_of(3).mpos == 200);
	CHECK(chip_of(1).zpos == 0 && chip_of(1).mpos == 0);
	CHECK_EQ(bus.zpos_writes[CHANNEL_OF[0]], z0 + 1);
	CHECK_EQ(bus.zpos_writes[CHANNEL_OF[1]], 1);            // AX2's range didn't change: not rewritten
	CHECK_EQ(bus.mpos_too_soon, 0);
	hsr_sensor_status_t s = status_now();
	CHECK(s.port[0].flags & HSR_SENSOR_RANGE_OK);
	CHECK(s.port[3].flags & HSR_SENSOR_RANGE_OK);

	// the byte order: ZPOS high (bits 11-8) first
	bool seen = false;
	for (const std::string &l : bus.log) seen |= l == "W36 01 03 E8";     // 1000 = 0x3E8
	CHECK(seen);

	// the axis gets ANGLE, which runs across the range
	chip_of(0).raw = 2000;
	rotate(1);
	CHECK_EQ(sensors_value(0), scaled(chip_of(0).angle()));
	CHECK_NEAR(sensors_value(0), HSR_RAW_MAX / 2, 2);

	// a restart: the sensors power up with 0 and 0, and get the saved range again
	for (int ch = 0; ch < 4; ch++) bus.chip[ch].power_cycle();
	sensors_begin();
	rotate(1);
	CHECK(chip_of(0).zpos == 1000 && chip_of(0).mpos == 3000);
	CHECK(chip_of(3).zpos == 3900 && chip_of(3).mpos == 200);
	CHECK_EQ(sensors_config()->range[0].mpos, 3000);
	CHECK_EQ(bus.mpos_too_soon, 0);
	CHECK_EQ(bus.burns, 0);

	// back to the whole circle
	c = config_with(0, 0, 0);
	CHECK_EQ(sensors_set_config(&c), HSR_OK);
	rotate(1);
	CHECK(chip_of(0).zpos == 0 && chip_of(0).mpos == 0);
	c = config_with(0, 1234, 1234);         // the same start and stop is the whole circle too
	CHECK_EQ(sensors_set_config(&c), HSR_OK);
	rotate(1);
	CHECK(chip_of(0).zpos == 0 && chip_of(0).mpos == 0);
	CHECK(status_now().port[0].flags & HSR_SENSOR_RANGE_OK);
}

static void t_sensor_bad_config()
{
	scenario("AS5600: settings out of range are refused, and nothing changes");
	fresh_start();
	sensors_begin();
	hsr_sensor_config_t good = config_with(1, 100, 2100);
	CHECK_EQ(sensors_set_config(&good), HSR_OK);
	uint8_t ee[1024];
	memcpy(ee, host_eeprom, sizeof(ee));

	hsr_sensor_config_t c = good; c.i2c_khz = 40;
	CHECK_EQ(sensors_set_config(&c), HSR_ERR_VALUE);
	c = good; c.i2c_khz = 0;
	CHECK_EQ(sensors_set_config(&c), HSR_ERR_VALUE);
	c = good; c.version = 2;
	CHECK_EQ(sensors_set_config(&c), HSR_ERR_VALUE);
	c = config_with(2, 1000, 1000 + HSR_AS5600_MIN_SPAN - 1);     // under 18 degrees
	CHECK_EQ(sensors_set_config(&c), HSR_ERR_VALUE);
	c = config_with(2, 4000, (4000 + HSR_AS5600_MIN_SPAN - 2) & 4095);     // under 18 degrees, across 0
	CHECK_EQ(sensors_set_config(&c), HSR_ERR_VALUE);
	c = config_with(2, 4096, 100);
	CHECK_EQ(sensors_set_config(&c), HSR_ERR_VALUE);
	CHECK(memcmp(ee, host_eeprom, sizeof(ee)) == 0);
	CHECK(memcmp(sensors_config(), &good, sizeof(good)) == 0);

	c = config_with(2, 1000, 1000 + HSR_AS5600_MIN_SPAN);         // exactly 18 degrees is fine
	CHECK_EQ(sensors_set_config(&c), HSR_OK);

	// a damaged EEPROM block: the factory settings
	host_eeprom[964 + 2] ^= 0x55;
	sensors_begin();
	CHECK_EQ(sensors_config()->range[1].mpos, 0);
	CHECK_EQ(sensors_config()->i2c_khz, 100);
}

static void t_sensor_clock()
{
	scenario("AS5600: the I2C clock follows the settings, also after a restart");
	fresh_start();
	sensors_begin();
	int begins = bus.begins;
	hsr_sensor_config_t c = *sensors_config();
	c.i2c_khz = 25;
	CHECK_EQ(sensors_set_config(&c), HSR_OK);
	CHECK_EQ(bus.khz, 25);
	CHECK_EQ(bus.begins, begins + 1);
	CHECK_EQ(status_now().i2c_khz, 25);
	CHECK_EQ(sensors_set_config(&c), HSR_OK);     // unchanged: the bus isn't restarted
	CHECK_EQ(bus.begins, begins + 1);
	sensors_begin();
	CHECK_EQ(bus.khz, 25);
	c.i2c_khz = 10;
	CHECK_EQ(sensors_set_config(&c), HSR_OK);
	CHECK_EQ(bus.khz, 10);
}

static void t_sensor_unplugged()
{
	scenario("AS5600: a sensor unplugged and plugged back in");
	fresh_start();
	sensors_begin();
	hsr_sensor_config_t c = config_with(1, 500, 2500);
	sensors_set_config(&c);
	chip_of(1).raw = 1500;
	rotate(3);
	uint16_t held = sensors_value(1);
	CHECK_NEAR(held, HSR_RAW_MAX / 2, 2);

	chip_of(1).present = false;
	rotate(2);
	hsr_sensor_status_t s = status_now();
	CHECK_EQ(s.port[1].state, HSR_SENSOR_NO_SENSOR);
	CHECK(!(s.port[1].flags & HSR_SENSOR_RANGE_OK));
	CHECK(s.port[1].errors >= 2);
	CHECK_EQ(sensors_value(1), held);                   // the axis keeps its last reading
	CHECK_EQ(s.port[0].state, HSR_SENSOR_OK);           // the other ports carry on
	CHECK_EQ(s.port[0].errors, 0);
	CHECK_EQ(s.bus_resets, 0);                          // nothing at an address isn't a stuck bus

	// back, freshly powered: it gets its range on the first visit
	chip_of(1).power_cycle();
	chip_of(1).present = true;
	chip_of(1).raw = 2500;
	rotate(1);
	CHECK(chip_of(1).zpos == 500 && chip_of(1).mpos == 2500);
	s = status_now();
	CHECK_EQ(s.port[1].state, HSR_SENSOR_OK);
	CHECK(s.port[1].flags & HSR_SENSOR_RANGE_OK);
	CHECK_EQ(s.port[1].raw_angle, 2500);
	CHECK_EQ(sensors_value(1), HSR_RAW_MAX);
}

static void t_sensor_silent_restart()
{
	scenario("AS5600: a sensor that restarted between visits gets its range back");
	fresh_start();
	sensors_begin();
	hsr_sensor_config_t c = config_with(2, 800, 1800);
	sensors_set_config(&c);
	rotate(2);
	CHECK(chip_of(2).zpos == 800);
	chip_of(2).power_cycle();           // a brown-out: no transfer fails
	rotate(4);                          // ZPOS and MPOS are read back every third visit
	CHECK(chip_of(2).zpos == 800 && chip_of(2).mpos == 1800);
	CHECK(status_now().port[2].flags & HSR_SENSOR_RANGE_OK);
	CHECK_EQ(status_now().port[2].errors, 0);
}

static void t_sensor_wont_take()
{
	scenario("AS5600: a chip that won't take a range is retried every third visit, not on every one");
	fresh_start();
	sensors_begin();
	chip_of(0).takes_range = false;
	hsr_sensor_config_t c = config_with(0, 100, 1100);
	sensors_set_config(&c);
	int before = bus.zpos_writes[CHANNEL_OF[0]];
	rotate(12);
	int writes = bus.zpos_writes[CHANNEL_OF[0]] - before;
	CHECK(writes >= 3 && writes <= 5);
	hsr_sensor_status_t s = status_now();
	CHECK(!(s.port[0].flags & HSR_SENSOR_RANGE_OK));
	CHECK_EQ(s.port[0].state, HSR_SENSOR_OK);           // it still reads
	CHECK_EQ(s.port[0].errors, 0);
}

static void t_sensor_magnet()
{
	scenario("AS5600: the magnet checks (STATUS MD, ML, MH)");
	fresh_start();
	chip_of(0).status = 0x00;
	chip_of(1).status = 0x20 | 0x10;
	chip_of(2).status = 0x20 | 0x08;
	sensors_begin();
	rotate(3);
	hsr_sensor_status_t s = status_now();
	CHECK_EQ(s.port[0].state, HSR_SENSOR_NO_MAGNET);
	CHECK_EQ(s.port[1].state, HSR_SENSOR_MAGNET_WEAK);
	CHECK_EQ(s.port[2].state, HSR_SENSOR_MAGNET_STRONG);
	CHECK_EQ(s.port[3].state, HSR_SENSOR_OK);
	CHECK_EQ(s.port[1].status, 0x30);
	chip_of(0).status = 0x20;
	rotate(3);
	CHECK_EQ(status_now().port[0].state, HSR_SENSOR_OK);
}

static void t_sensor_no_switch()
{
	scenario("AS5600: the PCA9546A missing (a bare Pro Micro): every port says so, resets are rate-limited");
	fresh_start();
	bus.switch_present = false;
	sensors_begin();
	rotate(100);                        // 800 ms
	hsr_sensor_status_t s = status_now();
	for (int p = 0; p < 4; p++)
	{
		CHECK_EQ(s.port[p].state, HSR_SENSOR_NO_SWITCH);
		CHECK_EQ(sensors_value(p), 0);
	}
	CHECK(bus.recoveries >= 3 && bus.recoveries <= 5);  // one per 250 ms
	CHECK_EQ(s.bus_resets, bus.recoveries);

	bus.switch_present = true;          // it answers again
	chip_of(0).raw = 4095;
	rotate(2);
	s = status_now();
	for (int p = 0; p < 4; p++) CHECK_EQ(s.port[p].state, HSR_SENSOR_OK);
	CHECK_EQ(sensors_value(0), HSR_RAW_MAX);
}

static void t_sensor_stuck_bus()
{
	scenario("AS5600: a sensor holding the bus low: the switch is reset, the other ports still read");
	fresh_start();
	sensors_begin();
	rotate(1);
	chip_of(2).holds_bus = true;
	chip_of(0).raw = 3000;
	rotate(40);                         // 320 ms
	hsr_sensor_status_t s = status_now();
	CHECK_EQ(s.port[2].state, HSR_SENSOR_BUS_ERROR);
	CHECK(s.bus_resets >= 1 && s.bus_resets <= 2);  // the stuck port is tried again after 250 ms
	CHECK_EQ(s.port[0].errors, 0);
	CHECK_EQ(s.port[0].state, HSR_SENSOR_OK);
	CHECK_EQ(s.port[3].state, HSR_SENSOR_OK);
	CHECK_EQ(sensors_value(0), scaled(3000));
	chip_of(2).holds_bus = false;
	rotate(40);                         // it's tried again 250 ms after the last reset
	CHECK_EQ(status_now().port[2].state, HSR_SENSOR_OK);
	CHECK_EQ(bus.multi_channel, 0);
}

static void t_a2_a3_sources()
{
	scenario("Rev 4.0: A2 and A3 as axis sources, and in the live data");
	settings_defaults(&g_config);
	g_config.axis_config[0].source_main = HSR_SOURCE_A2;
	g_config.axis_config[1].source_main = HSR_SOURCE_A3;
	Sim s;
	s.begin();
	s.analog[HSR_SOURCE_A2] = HSR_RAW_MAX;
	s.analog[HSR_SOURCE_A3] = 0;
	s.analog[0] = s.analog[1] = HSR_RAW_MAX / 2;    // AX1, AX2: not these axes' sources
	s.step(5);
	CHECK_EQ(s.axis(0), AXIS_MAX_VALUE);
	CHECK_EQ(s.axis(1), AXIS_MIN_VALUE);
	params_report_t p;
	memset(&p, 0xEE, sizeof(p));
	s.analog[HSR_SOURCE_A3] = 1234;
	pipeline_params(&p, s.analog);
	CHECK_EQ(hsr_params_analog(&p, HSR_SOURCE_A2), HSR_RAW_MAX);
	CHECK_EQ(hsr_params_analog(&p, HSR_SOURCE_A3), 1234);
	CHECK_EQ(hsr_params_analog(&p, 0), HSR_RAW_MAX / 2);
	CHECK_EQ(hsr_params_analog(&p, 11), 0);
}

void run_sensor_tests()
{
	t_sensor_layout();
	t_sensor_defaults();
	t_sensor_range();
	t_sensor_bad_config();
	t_sensor_clock();
	t_sensor_unplugged();
	t_sensor_silent_restart();
	t_sensor_wont_take();
	t_sensor_magnet();
	t_sensor_no_switch();
	t_sensor_stuck_bus();
	t_a2_a3_sources();
}
