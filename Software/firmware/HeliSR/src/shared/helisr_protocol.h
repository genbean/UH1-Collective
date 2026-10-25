/*
  helisr_protocol.h - USB messages between the HeliSR firmware and HeliSR Configurator

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy).
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  The device has two HID interfaces:
    - the joystick (report ID HSR_REPORT_JOY), which games read;
    - the settings channel, a vendor-defined collection with one 64-byte
      report each way (report ID HSR_REPORT_CFG), which only the configurator uses.

  Every settings packet is:
    [0] report ID   [1] command   [2] index / argument   [3] status   [4..63] data (60 bytes)
  The device answers each command with a packet carrying the same command
  number. Status is HSR_OK or an HSR_ERR_ code.
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

/* Test builds: one logic pass with given inputs and time, and its results. */
#pragma pack(push, 1)
typedef struct
{
	uint16_t    now;                            // ms
	uint16_t    sr_inputs;                      // bit n = IN(n+1) closed
	uint16_t    spare_buttons;                  // bit n = spare pin n pressed
	uint16_t    analog[9];                      // HSR_ANALOG_SOURCES raw readings
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
