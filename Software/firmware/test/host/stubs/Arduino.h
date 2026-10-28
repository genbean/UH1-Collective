/*
  Arduino.h - stand-in for the PC test program: only what the logic files use.
  Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.
*/
#ifndef HSR_HOST_ARDUINO_H
#define HSR_HOST_ARDUINO_H

#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#define PROGMEM
#define pgm_read_byte(p)  (*(const uint8_t *)(p))
#define pgm_read_word(p)  (*(const uint16_t *)(p))

#define A0 18

unsigned long millis(void);
unsigned long micros(void);
void delay(unsigned long ms);
int analogRead(uint8_t pin);

#endif
