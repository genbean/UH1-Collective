/*
  protocol.cpp - the settings channel: answers HeliSR Configurator's commands

  Part of HeliSR, based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy),
  application/Src/usb_endp.c.
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 and Rev 4.0 boards, 2026.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#include <Arduino.h>
#include <avr/wdt.h>
#include <stddef.h>
#include <string.h>
#include "protocol.h"
#include "process.h"
#include "pipeline.h"
#include "logic.h"
#include "settings.h"
#include "usb_helisr.h"
#include "shared/helisr_protocol.h"
#if HSR_BOARD_REV == 40
#include "sensors.h"
#endif

#define CONFIG_CHUNKS   ((sizeof(dev_config_t) + HSR_PACKET_DATA - 1) / HSR_PACKET_DATA)
#define PARAMS_PARTS    ((sizeof(params_report_t) + HSR_PACKET_DATA - 1) / HSR_PACKET_DATA)
#define BUSY_MS         2000

// One buffer for the command and its reply: the reply is built in place once
// the command has been read.
static uint8_t pkt[HSR_PACKET_SIZE];
static uint32_t busy_until;
static uint16_t commands, replies_dropped;
static uint8_t test_mode;
uint16_t pass_max_us;           // set by the sketch's loop

// Which board this build is for, where the configurator finds it in the .hex
// before flashing. INFO reads its board ID from here, which keeps the tag in
// the build.
static const hsr_build_tag_t build_tag PROGMEM =
	{ HSR_BUILD_MAGIC, HSR_BOARD_ID, (uint8_t)(F_CPU / 1000000UL), HSR_FIRMWARE_VERSION };

// Send a reply, waiting up to 50 ms for the endpoint. data may point into pkt.
static void reply(uint8_t status, const void *data, uint8_t len)
{
	if (data && len) memmove(&pkt[HSR_PACKET_HEADER], data, len);
	memset(&pkt[HSR_PACKET_HEADER + len], 0, HSR_PACKET_DATA - len);
	pkt[0] = HSR_REPORT_CFG;    // pkt[1] (command) and pkt[2] (index) stay as received
	pkt[3] = status;

	uint32_t start = millis();
	while (HeliUSB().sendSettings(pkt) < 0)
	{
		if (millis() - start >= 50) { replies_dropped++; return; }
	}
}

// Bytes of stack never used since start-up: start-up paints the free RAM
// between the variables and the stack (init1 below), and the paint is
// counted from the variables' end upwards.
extern uint8_t _end;
extern uint8_t __stack;
#define STACK_PAINT 0xC5

void stack_paint(void) __attribute__((naked, used, section(".init1")));
void stack_paint(void)
{
	__asm volatile(
		"    ldi r30, lo8(_end)\n"
		"    ldi r31, hi8(_end)\n"
		"    ldi r24, %0\n"
		"    ldi r25, hi8(__stack)\n"
		"    rjmp 2f\n"
		"1:  st Z+, r24\n"
		"2:  cpi r30, lo8(__stack)\n"
		"    cpc r31, r25\n"
		"    brlo 1b\n"
		"    breq 1b\n" :: "i"(STACK_PAINT));
}

static uint16_t stack_free(void)
{
	const uint8_t *p = &_end;
	uint16_t n = 0;
	while (p <= &__stack && *p == STACK_PAINT) { p++; n++; }
	return n;
}

// Restart through the watchdog so the PC enumerates the device again with
// the new name, USB IDs and joystick layout.
static void restart(void)
{
	delay(20);                  // let the reply leave
	USBDevice.detach();
	delay(50);
	wdt_enable(WDTO_15MS);
	for (;;) { }
}

// Start the Pro Micro's bootloader, as the Arduino core does after its
// 1200-baud "touch": leave the magic key in RAM and reset through the watchdog.
static void enter_bootloader(void)
{
	delay(20);
	USBDevice.detach();
	delay(50);
	uint16_t key_pos = MAGIC_KEY_POS;
#if defined(__AVR_ATmega32U4__)
	if (pgm_read_word(FLASHEND - 1) == NEW_LUFA_SIGNATURE) key_pos = RAMEND - 1;
#endif
	cli();
	*(volatile uint16_t *)key_pos = MAGIC_KEY;
	wdt_enable(WDTO_120MS);
	for (;;) { }
}

// The commands with sizeable local variables live in their own functions, so
// only the running command's variables are on the stack (noinline). That
// matters most for TEST_STEP, which runs the whole logic from here.

static void __attribute__((noinline)) cmd_info(void)
{
	hsr_info_t info;
	memset(&info, 0, sizeof(info));
	info.firmware_version = HSR_FIRMWARE_VERSION;
	info.protocol_version = HSR_PROTOCOL_VERSION;
	info.board_id = pgm_read_byte(&build_tag.board_id);
	info.config_version = HSR_CONFIG_VERSION;
	info.config_size = sizeof(dev_config_t);
	info.cpu_mhz = F_CPU / 1000000UL;
#ifdef CDC_ENABLED
	info.usb_serial_port = 1;
#endif
	info.unique_id = settings_unique_id();
	info.config_from_eeprom = settings_from_eeprom();
	info.stack_free = stack_free();
	info.commands = commands;
	info.replies_dropped = replies_dropped;
	info.pass_max_us = pass_max_us;
	reply(HSR_OK, &info, sizeof(info));
}

static void __attribute__((noinline)) cmd_params(uint8_t index)
{
	if (index >= PARAMS_PARTS) { reply(HSR_ERR_INDEX, 0, 0); return; }
	params_report_t p;
	process_params(&p);
	uint16_t offset = (uint16_t)index * HSR_PACKET_DATA;
	uint8_t len = min((uint16_t)HSR_PACKET_DATA, (uint16_t)(sizeof(p) - offset));
	reply(HSR_OK, (uint8_t *)&p + offset, len);
}

#if HSR_BOARD_REV == 40
static void __attribute__((noinline)) cmd_sensor_status(void)
{
	hsr_sensor_status_t s;
	sensors_status(&s);
	reply(HSR_OK, &s, sizeof(s));
}

// index 0: read; index 1: the new settings, saved and applied at once.
static void __attribute__((noinline)) cmd_sensor_config(uint8_t index, const uint8_t *data)
{
	uint8_t status = HSR_OK;
	if (index == 1)
	{
		hsr_sensor_config_t c;
		memcpy(&c, data, sizeof(c));
		status = sensors_set_config(&c);
	}
	else if (index != 0)
		status = HSR_ERR_INDEX;
	reply(status, sensors_config(), sizeof(hsr_sensor_config_t));
}

// Built in the packet, so nothing is copied onto the stack.
static void __attribute__((noinline)) cmd_sensor_debug(uint8_t index, uint8_t *data)
{
	uint8_t n = index & (uint8_t)~HSR_SENSOR_DEBUG_CLEAR;
	if (n >= HSR_AX_INPUTS) { reply(HSR_ERR_INDEX, 0, 0); return; }
	sensors_debug(n, index & HSR_SENSOR_DEBUG_CLEAR, (hsr_sensor_debug_t *)data);
	reply(HSR_OK, data, sizeof(hsr_sensor_debug_t));
}
#endif

#ifdef HSR_TEST_STEP
// One logic pass with the PC's inputs; the inputs are read from the packet
// and the results written over them, so nothing is copied onto the stack.
static void __attribute__((noinline)) cmd_test_step(uint8_t *data)
{
	const hsr_test_step_t *in = (const hsr_test_step_t *)data;
	pipeline_step(in->sr_inputs, in->spare_buttons, (const uint16_t *)(data + offsetof(hsr_test_step_t, analog)), in->now);

	hsr_test_result_t *r = (hsr_test_result_t *)data;
	memset(r, 0, sizeof(*r));
	buttons_get(NULL, r->log_buttons, r->phy_buttons, r->povs, &r->shifts);
	for (uint8_t i = 0; i < HSR_MAX_AXES; i++) r->axes[i] = axis_out(i);
	r->leds = leds_get(r->pwm);
	reply(HSR_OK, r, sizeof(*r));
}
#endif

static void handle(uint32_t now)
{
	uint8_t index = pkt[2];
	uint8_t *data = &pkt[HSR_PACKET_HEADER];

	switch (pkt[1])
	{
	case HSR_CMD_INFO:
		cmd_info();
		break;

	case HSR_CMD_READ:
	case HSR_CMD_WRITE:
	{
		if (index >= CONFIG_CHUNKS) { reply(HSR_ERR_INDEX, 0, 0); break; }
		uint16_t offset = (uint16_t)index * HSR_PACKET_DATA;
		uint8_t len = min((uint16_t)HSR_PACKET_DATA, (uint16_t)(sizeof(dev_config_t) - offset));
		busy_until = now + BUSY_MS;
		if (pkt[1] == HSR_CMD_READ)
			reply(HSR_OK, (uint8_t *)&g_config + offset, len);
		else
		{
			memcpy((uint8_t *)&g_config + offset, data, len);
			reply(HSR_OK, 0, 0);
		}
		break;
	}

	case HSR_CMD_COMMIT:
	{
		uint16_t crc = data[0] | ((uint16_t)data[1] << 8);
		if (crc != hsr_crc16((const uint8_t *)&g_config, sizeof(dev_config_t)))
			reply(HSR_ERR_CRC, 0, 0);
		else if (g_config.config_version != HSR_CONFIG_VERSION)
			reply(HSR_ERR_VERSION, 0, 0);
		else
		{
			settings_save();
			reply(HSR_OK, 0, 0);
			restart();
		}
		break;
	}

	case HSR_CMD_RELOAD:
		if (!settings_load()) settings_defaults(&g_config);
		busy_until = now;
		reply(HSR_OK, 0, 0);
		break;

	case HSR_CMD_DEFAULTS:
		settings_defaults(&g_config);
		busy_until = now + BUSY_MS;
		reply(HSR_OK, 0, 0);
		break;

	case HSR_CMD_PARAMS:
		cmd_params(index);
		break;

	case HSR_CMD_BOOTLOADER:
		if (strncmp((const char *)data, "bootloader run", 14) == 0)
		{
			reply(HSR_OK, 0, 0);
			enter_bootloader();
		}
		reply(HSR_ERR_COMMAND, 0, 0);
		break;

#if HSR_BOARD_REV == 40
	case HSR_CMD_SENSOR_STATUS:
		cmd_sensor_status();
		break;

	case HSR_CMD_SENSOR_CONFIG:
		cmd_sensor_config(index, data);
		break;

	case HSR_CMD_SENSOR_DEBUG:
		cmd_sensor_debug(index, data);
		break;
#endif

#ifdef HSR_TEST_STEP
	case HSR_CMD_TEST_APPLY:
		pipeline_init();
		test_mode = 1;
		reply(HSR_OK, 0, 0);
		break;

	case HSR_CMD_TEST_STEP:
		cmd_test_step(data);
		break;
#endif

	default:
		reply(HSR_ERR_COMMAND, 0, 0);
		break;
	}
}

uint8_t protocol_test_mode(void)
{
	return test_mode;
}

void protocol_poll(void)
{
	while (HeliUSB().readSettings(pkt))
	{
		commands++;
		if (pkt[0] == HSR_REPORT_CFG) handle(millis());
	}
}

uint8_t protocol_busy(uint32_t now_ms)
{
	return (int32_t)(busy_until - now_ms) > 0;
}
