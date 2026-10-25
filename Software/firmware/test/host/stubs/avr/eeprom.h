/*
  avr/eeprom.h - stand-in for the PC test program: a 1 KB array.
  Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
*/
#ifndef HSR_HOST_EEPROM_H
#define HSR_HOST_EEPROM_H

#include <stdint.h>
#include <string.h>

extern uint8_t host_eeprom[1024];

static inline uint16_t eeprom_read_word(const uint16_t *a) { uint16_t v; memcpy(&v, host_eeprom + (uintptr_t)a, 2); return v; }
static inline uint32_t eeprom_read_dword(const uint32_t *a) { uint32_t v; memcpy(&v, host_eeprom + (uintptr_t)a, 4); return v; }
static inline void eeprom_read_block(void *d, const void *a, size_t n) { memcpy(d, host_eeprom + (uintptr_t)a, n); }
static inline void eeprom_update_word(uint16_t *a, uint16_t v) { memcpy(host_eeprom + (uintptr_t)a, &v, 2); }
static inline void eeprom_update_dword(uint32_t *a, uint32_t v) { memcpy(host_eeprom + (uintptr_t)a, &v, 4); }
static inline void eeprom_update_block(const void *s, void *a, size_t n) { memcpy(host_eeprom + (uintptr_t)a, s, n); }

#endif
