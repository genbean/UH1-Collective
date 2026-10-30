/*
  helisr_protocol.h - USB messages between the HeliSR firmware and HeliSR Configurator

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy).
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 and Rev 4.0 boards, 2026.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  The device has two HID interfaces:
    - the joystick (report ID HSR_REPORT_JOY), which games read;
    - the settings channel, a vendor-defined collection with one 64-byte
      report each way (report ID HSR_REPORT_CFG), which only the configurator uses.

  Every settings packet is:
    [0] report ID   [1] command   [2] index / argument   [3] status   [4..63] data (60 bytes)
  The device answers each command with a packet carrying the same command
  number. Status is HSR_OK or an HSR_ERR_ code.

  Both boards speak protocol 1. Rev 4.0 adds the three SENSOR commands, which
  Rev 3.0 answers with HSR_ERR_COMMAND: INFO's board_id says which to expect.
*/

#ifndef HELISR_PROTOCOL_H
#define HELISR_PROTOCOL_H

#include <stdint.h>

#define HSR_PROTOCOL_VERSION    1

#define HSR_REPORT_JOY          1
#define HSR_REPORT_CFG          2

#define HSR_PACKET_SIZE         64
#define HSR_PACKET_DATA         60
#define HSR_PACKET_HEADER       4

/* Vendor ID and product ID, until the project has its own (pid.codes).
   SparkFun's Pro Micro IDs: 0x1B4F 0x9206 (application). */
#define HSR_DEFAULT_VID         0x1B4F
#define HSR_DEFAULT_PID         0x9206

#define HSR_MANUFACTURER        "HeliSR"
#define HSR_DEFAULT_NAME        "HeliSR"

enum
{
	HSR_CMD_INFO = 1,       // -> hsr_info_t
	HSR_CMD_READ,           // index = chunk number (0-based) -> settings bytes
	HSR_CMD_WRITE,          // index = chunk number, data = settings bytes -> ack
	HSR_CMD_COMMIT,         // data = uint16 CRC of the whole block -> ack, then the device restarts
	HSR_CMD_RELOAD,         // discard unsaved writes, reload from EEPROM -> ack
	HSR_CMD_DEFAULTS,       // load the factory settings (not saved until COMMIT) -> ack
	HSR_CMD_PARAMS,         // start live data for 5 s; index = part (0 or 1) -> params bytes
	HSR_CMD_BOOTLOADER,     // data = "bootloader run" -> ack, then the bootloader starts

	// Rev 4.0 only: the AS5600s on AX1-AX4
	HSR_CMD_SENSOR_STATUS,  // -> hsr_sensor_status_t
	HSR_CMD_SENSOR_CONFIG,  // index 0: read; index 1: data = hsr_sensor_config_t, saved
	                        // and applied at once (no restart) -> hsr_sensor_config_t
	HSR_CMD_SENSOR_DEBUG,   // index = port 0-3, | HSR_SENSOR_DEBUG_CLEAR to clear its counters
	                        // after reading them -> hsr_sensor_debug_t

	// Test builds only (HSR_TEST_STEP): the PC drives the logic in lockstep
	HSR_CMD_TEST_APPLY = 0x70,  // restart the logic from the settings in RAM and enter
	                            // test mode (the board's own inputs are ignored) -> ack
	HSR_CMD_TEST_STEP,          // data = hsr_test_step_t -> hsr_test_result_t
};

enum
{
	HSR_OK = 0,
	HSR_ERR_COMMAND,        // unknown command
	HSR_ERR_INDEX,          // chunk out of range
	HSR_ERR_CRC,            // COMMIT: checksum doesn't match
	HSR_ERR_VERSION,        // COMMIT: config_version doesn't match the firmware
	HSR_ERR_BUSY,           // a write is in progress from another command
	HSR_ERR_VALUE,          // SENSOR_CONFIG: a value out of range; nothing changed
};

#pragma pack(push, 1)
typedef struct
{
	uint16_t    firmware_version;   // HSR_FIRMWARE_VERSION
	uint8_t     protocol_version;   // HSR_PROTOCOL_VERSION
	uint8_t     board_id;           // HSR_BOARD_ID
	uint16_t    config_version;     // HSR_CONFIG_VERSION
	uint16_t    config_size;        // sizeof(dev_config_t)
	uint8_t     cpu_mhz;            // 16 or 8
	uint8_t     usb_serial_port;    // 1 if the build includes the Arduino USB serial port
	uint32_t    unique_id;          // random, made on first start, kept in EEPROM
	uint8_t     config_from_eeprom; // 0 if the settings are factory defaults
	uint16_t    stack_free;         // RAM the stack has never reached since start-up (bytes)
	uint16_t    commands;           // settings packets received since start-up
	uint16_t    replies_dropped;    // replies not sent because the endpoint stayed busy
	uint16_t    pass_max_us;        // longest input-processing pass since start-up
} hsr_info_t;
#pragma pack(pop)

/* Every firmware build carries this tag in its flash, so the configurator can
   tell which board a .hex file is for before it flashes it. INFO takes its
   board_id from the tag too, which keeps the tag in the build. */
#define HSR_BUILD_MAGIC         "HeliSR firmware"   // 15 characters and the NUL

#pragma pack(push, 1)
typedef struct
{
	char        magic[16];          // HSR_BUILD_MAGIC
	uint8_t     board_id;           // HSR_BOARD_REV30 / HSR_BOARD_REV40
	uint8_t     cpu_mhz;
	uint16_t    firmware_version;   // HSR_FIRMWARE_VERSION
} hsr_build_tag_t;
#pragma pack(pop)

/* ------------------------------------------------ Rev 4.0: AS5600 sensors --
   Each AX port has its own channel on the board's PCA9546A I2C switch, and an
   AS5600 behind it. The start and stop angles are written to each sensor's
   working (volatile) ZPOS and MPOS registers every time the firmware starts,
   from settings kept in EEPROM apart from dev_config_t: they belong to the
   sensor's mounting, not to a profile, as Rev 3.0's burnt-in angles do. CONF
   is set to the chip's power-up 0 with them. Nothing is ever burnt into a
   chip. */

#define HSR_SENSOR_CONFIG_VERSION   1
#define HSR_I2C_KHZ_DEFAULT         100     // also 50, 25 and 10, for long cables
#define HSR_AS5600_MIN_SPAN         205     // the AS5600's smallest range: 18 degrees in 4096ths

enum
{
	HSR_SENSOR_STARTING = 0,    // not read yet
	HSR_SENSOR_OK,              // reading, magnet in range
	HSR_SENSOR_NO_MAGNET,       // the AS5600 answers but sees no magnet (STATUS MD = 0)
	HSR_SENSOR_MAGNET_WEAK,     // magnet too far or too weak (ML)
	HSR_SENSOR_MAGNET_STRONG,   // magnet too close or too strong (MH)
	HSR_SENSOR_NO_SENSOR,       // nothing answers at 0x36 on this port
	HSR_SENSOR_NO_SWITCH,       // the PCA9546A doesn't answer: no port can be read
	HSR_SENSOR_BUS_ERROR,       // the bus stuck (a line held low) while on this port
};

#define HSR_SENSOR_RANGE_OK     0x01    // hsr_sensor_port_t.flags: the sensor holds the saved
                                        // start and stop, and CONF 0 (read back and checked)

#pragma pack(push, 1)
typedef struct
{
	uint16_t    zpos;           // start: the RAW ANGLE (0-4095) at one end of the travel
	uint16_t    mpos;           // stop: at the other end, in the direction the angle rises;
	                            // zpos == mpos: the whole circle (both written as 0)
} hsr_sensor_range_t;

typedef struct
{
	uint8_t             version;        // HSR_SENSOR_CONFIG_VERSION
	uint8_t             i2c_khz;        // 100, 50, 25 or 10
	hsr_sensor_range_t  range[4];       // AX1-AX4
} hsr_sensor_config_t;

typedef struct
{
	uint8_t     state;          // HSR_SENSOR_...
	uint8_t     flags;          // HSR_SENSOR_RANGE_OK
	uint8_t     status;         // the AS5600's STATUS register (MD 0x20, ML 0x10, MH 0x08)
	uint8_t     agc;            // its AGC: 0-255 on 5 V, best near the middle
	uint16_t    raw_angle;      // RAW ANGLE, 0-4095: what the start and stop are set from
	uint16_t    angle;          // ANGLE, 0-4095 across the range: what the axis gets
	uint16_t    errors;         // failed transfers on this port since start-up
} hsr_sensor_port_t;

typedef struct
{
	uint8_t             i2c_khz;        // the clock in use
	uint8_t             bus_resets;     // bus recoveries since start-up (stops at 255)
	hsr_sensor_port_t   port[4];        // AX1-AX4
} hsr_sensor_status_t;

/* SENSOR_DEBUG: one port's sensor read in full when asked, apart from the
   passes (four reads: 3 ms at 100 kHz, 30 ms at 10 kHz, so not for polling
   fast), and the port's counters. The registers are as the chip sent them,
   unused bits included. */
#define HSR_SENSOR_DEBUG_CLEAR  0x80

typedef struct
{
	// since start-up or the last clear; each stops at 255
	uint8_t     range_writes;   // times ZPOS, MPOS and CONF were written
	uint8_t     range_lost;     // times the read-back found them gone with no failed transfer:
	                            // the sensor restarted (a brown-out on its cable)
	uint8_t     magnet_faults;  // times STATUS went from a good magnet to none, weak or strong
	uint8_t     last_failure;   // HSR_SENSOR_NO_SENSOR / _NO_SWITCH / _BUS_ERROR of the last
	                            // failed transfer, 0 if none
	uint8_t     agc_min;        // the lowest and highest AGC read (255 and 0 until read):
	uint8_t     agc_max;        // a magnet that wobbles or moves spreads them
} hsr_sensor_counters_t;

typedef struct
{
	uint8_t     port;           // 0-3: AX1-AX4
	uint8_t     result;         // HSR_SENSOR_OK if every register was read, else
	                            // _NO_SWITCH, _NO_SENSOR or _BUS_ERROR (the rest is 0)
	uint8_t     switch_control; // the PCA9546A's control register, read back after connecting
	                            // the port: 1 << the port's channel
	uint8_t     conf_regs[9];   // the AS5600's 0x00-0x08: ZMCO (bits 1-0: times ZPOS/MPOS
	                            // were burnt), ZPOS, MPOS, MANG, CONF (high bytes first)
	uint8_t     out_regs[5];    // 0x0B-0x0F: STATUS, RAW ANGLE, ANGLE
	uint8_t     mag_regs[3];    // 0x1A-0x1C: AGC, MAGNITUDE (12 bits)
	hsr_sensor_counters_t counters;
} hsr_sensor_debug_t;
#pragma pack(pop)

/* A start and stop the firmware accepts. */
static inline uint8_t hsr_sensor_range_valid(const hsr_sensor_range_t *r)
{
	if (r->zpos > 4095 || r->mpos > 4095) return 0;
	if (r->zpos == r->mpos) return 1;
	uint16_t span = (uint16_t)((r->mpos - r->zpos) & 4095);
	return span >= HSR_AS5600_MIN_SPAN;
}

static inline uint8_t hsr_i2c_khz_valid(uint8_t khz)
{
	return khz == 100 || khz == 50 || khz == 25 || khz == 10;
}

/* Test builds: one logic pass with given inputs and time, and its results. */
#pragma pack(push, 1)
typedef struct
{
	uint16_t    now;                            // ms
	uint16_t    sr_inputs;                      // bit n = IN(n+1) closed
	uint16_t    spare_buttons;                  // bit n = spare pin n pressed
	uint16_t    analog[9];                      // raw readings of analog sources 0-8 (Rev 3.0's)
} hsr_test_step_t;

typedef struct
{
	uint8_t     log_buttons[8];                 // logical buttons (after inversion)
	uint8_t     phy_buttons[8];                 // debounced physical inputs
	int16_t     axes[8];                        // output axes
	uint8_t     povs[4];                        // hat values, used hats in order
	uint8_t     shifts;
	uint16_t    leds;                           // single LEDs by spare pin
	uint8_t     pwm[4];                         // PWM duty per channel (%)
} hsr_test_result_t;
#pragma pack(pop)

#if defined(__cplusplus)
static_assert(sizeof(hsr_build_tag_t) == 20, "hsr_build_tag_t layout");
static_assert(sizeof(hsr_sensor_config_t) == 18, "hsr_sensor_config_t layout");
static_assert(sizeof(hsr_sensor_status_t) == 42, "hsr_sensor_status_t layout");
static_assert(sizeof(hsr_sensor_debug_t) == 26, "hsr_sensor_debug_t layout");
#endif

/* CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF), over the whole dev_config_t. */
static inline uint16_t hsr_crc16(const uint8_t *data, uint16_t len)
{
	uint16_t crc = 0xFFFF;
	while (len--)
	{
		crc ^= (uint16_t)(*data++) << 8;
		for (uint8_t i = 0; i < 8; i++)
			crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
	}
	return crc;
}

#endif
