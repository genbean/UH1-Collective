/*
  HeliSR - game controller firmware for a Pro Micro on the HeliSR board

  Based on FreeJoy (https://github.com/FreeJoy-Team/FreeJoy) v1.7.3b1.
  Copyright (C) 2020  Yury Vostrenkov
  Modified for the ATmega32U4 Pro Micro and the HeliSR Rev 3.0 board, 2026.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  Build as "Arduino Leonardo" (5 V / 16 MHz Pro Micro) with Software/firmware/build.ps1.
  The settings are made with HeliSR Configurator; without it the board is a
  joystick with IN1-IN16 as buttons 1-16 and AX1-AX4 as the X, Y, Z and Rx axes.
*/

#include <avr/wdt.h>
#include "src/board.h"
#include "src/settings.h"
#include "src/process.h"
#include "src/protocol.h"
#include "src/usb_helisr.h"

// A watchdog restart (after saving settings) leaves the watchdog running:
// turn it off before anything else.
uint8_t reset_cause __attribute__((section(".noinit")));
void early_wdt_off(void) __attribute__((naked, used, section(".init3")));
void early_wdt_off(void)
{
	reset_cause = MCUSR;
	MCUSR = 0;
	wdt_disable();
}

void setup()
{
	settings_make_unique_id();      // uses analogRead: before board_init()
	board_init(&g_config);
	process_init();
	HeliUSB().setReportSource(process_report());
}

void loop()
{
	static uint32_t last_sent;

	protocol_poll();

	uint32_t now = millis();
	if (protocol_busy(now) || protocol_test_mode()) return;

	uint16_t t0 = micros();
	process_run(now);
	uint16_t took = (uint16_t)micros() - t0;
	extern uint16_t pass_max_us;
	if (took > pass_max_us) pass_max_us = took;

	// Send the report every exchange period whether or not it changed, as
	// FreeJoy does: a program that opens the joystick later still gets the
	// current state straight away.
	uint8_t period = g_config.exchange_period_ms ? g_config.exchange_period_ms : 1;
	if (now - last_sent >= period && HeliUSB().sendJoystick(process_report()) >= 0)
		last_sent = now;
}
