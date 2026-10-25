/*
  protocol.h - the settings channel: answers HeliSR Configurator's commands

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
*/

#ifndef HELISR_PROTOCOL_HANDLER_H
#define HELISR_PROTOCOL_HANDLER_H

#include <stdint.h>

// Handle any packets the configurator has sent.
void protocol_poll(void);

// 1 while the configurator is reading or writing settings: the inputs aren't
// processed then, as FreeJoy does, so a half-written block is never used.
uint8_t protocol_busy(uint32_t now_ms);

// Test builds: 1 once the PC has put the logic in test mode.
uint8_t protocol_test_mode(void);

#endif
