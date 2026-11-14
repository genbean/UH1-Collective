/*
  BoardTest - HeliSR Rev 4.0 assembly check, for solder bridges and opens
  around the PCA9546A I2C switch (U3), the AX ports and their pull-ups.

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Not the HeliSR firmware: flash it, read its report on the USB serial port
  (any baud rate), then flash HeliSR again. Nothing needs to be plugged into
  the AX ports. It drives the I2C lines by hand (open drain, through the
  board's pull-ups), so it still works when a bridge has the bus stuck:
    - with each channel, and each pair of channels, connected through the
      switch: are SDA and SCL high when released, does each go low when
      driven, and does the other follow it (a bridge between them)?
    - the switch's control register read back after each selection;
    - the same for channel 0 (AX4) with /RESET (A1) left to its pull-up, to
      tell a bridge to /RESET (U3 pins 3-4) from one to VCC.
  Each test starts from a /RESET pulse, so a stuck channel can't carry over.
*/

#include <Arduino.h>

static const uint8_t SDA_PIN = 2, SCL_PIN = 3, RST_PIN = A1;
static const uint8_t SR_DATA = 14, SR_CLOCK = 15, SR_LOAD = A0;
static const uint8_t SWITCH_ADDR = 0x70;
static const char *const PORT_OF_CHANNEL[4] = {"AX4", "AX2", "AX1", "AX3"};

struct Lines
{
	bool sda, scl;              // released
	bool sda_low, scl_follows;  // SDA driven low: did it go low, did SCL go with it
	bool scl_low, sda_follows;  // SCL driven low
};

static void release(uint8_t pin) { pinMode(pin, INPUT); }
static void drive_low(uint8_t pin) { digitalWrite(pin, LOW); pinMode(pin, OUTPUT); }
static void half() { delayMicroseconds(25); }       // about 20 kHz

static bool scl_high()
{
	release(SCL_PIN);
	for (uint16_t i = 0; i < 1000; i++)
	{
		if (digitalRead(SCL_PIN)) return true;
		delayMicroseconds(1);
	}
	return false;
}

static void i2c_start() { release(SDA_PIN); release(SCL_PIN); half(); drive_low(SDA_PIN); half(); drive_low(SCL_PIN); half(); }
static void i2c_stop() { drive_low(SDA_PIN); half(); scl_high(); half(); release(SDA_PIN); half(); }

static bool i2c_bit_out(bool b)
{
	if (b) release(SDA_PIN); else drive_low(SDA_PIN);
	half();
	bool ok = scl_high();
	half();
	drive_low(SCL_PIN);
	return ok;
}

static bool i2c_bit_in()
{
	release(SDA_PIN);
	half();
	scl_high();
	half();
	bool b = digitalRead(SDA_PIN);
	drive_low(SCL_PIN);
	return b;
}

// true if acknowledged
static bool i2c_byte_out(uint8_t v)
{
	for (int8_t i = 7; i >= 0; i--) i2c_bit_out(v & (1 << i));
	return !i2c_bit_in();
}

static uint8_t i2c_byte_in(bool ack)
{
	uint8_t v = 0;
	for (uint8_t i = 0; i < 8; i++) v = (uint8_t)((v << 1) | i2c_bit_in());
	i2c_bit_out(!ack);
	return v;
}

static bool switch_write(uint8_t control)
{
	i2c_start();
	bool ok = i2c_byte_out(SWITCH_ADDR << 1) && i2c_byte_out(control);
	i2c_stop();
	return ok;
}

// -1: no answer
static int switch_read()
{
	i2c_start();
	if (!i2c_byte_out((SWITCH_ADDR << 1) | 1)) { i2c_stop(); return -1; }
	uint8_t v = i2c_byte_in(false);
	i2c_stop();
	return v;
}

static void reset_switch()
{
	digitalWrite(RST_PIN, LOW);
	pinMode(RST_PIN, OUTPUT);
	delayMicroseconds(50);
	digitalWrite(RST_PIN, HIGH);
	delayMicroseconds(50);
}

static Lines probe()
{
	Lines l;
	release(SDA_PIN); release(SCL_PIN);
	delayMicroseconds(100);
	l.sda = digitalRead(SDA_PIN);
	l.scl = digitalRead(SCL_PIN);
	drive_low(SDA_PIN);
	delayMicroseconds(20);
	l.sda_low = !digitalRead(SDA_PIN);
	l.scl_follows = !digitalRead(SCL_PIN);
	release(SDA_PIN);
	delayMicroseconds(100);
	drive_low(SCL_PIN);
	delayMicroseconds(20);
	l.scl_low = !digitalRead(SCL_PIN);
	l.sda_follows = !digitalRead(SDA_PIN);
	release(SCL_PIN);
	delayMicroseconds(100);
	return l;
}

static bool lines_good(const Lines &l)
{
	return l.sda && l.scl && l.sda_low && l.scl_low && !l.scl_follows && !l.sda_follows;
}

static void print_lines(const Lines &l)
{
	Serial.print(F(" | released SDA ")); Serial.print(l.sda ? F("high") : F("LOW"));
	Serial.print(F(" SCL ")); Serial.print(l.scl ? F("high") : F("LOW"));
	Serial.print(F(" | SDA driven: ")); Serial.print(l.sda_low ? F("low") : F("STAYS HIGH"));
	if (l.scl_follows) Serial.print(F(", SCL FOLLOWS"));
	Serial.print(F(" | SCL driven: ")); Serial.print(l.scl_low ? F("low") : F("STAYS HIGH"));
	if (l.sda_follows) Serial.print(F(", SDA FOLLOWS"));
}

static void print_mask(uint8_t mask)
{
	Serial.print(F("0x0")); Serial.print(mask, HEX); Serial.print(F(" ("));
	bool first = true;
	for (uint8_t c = 0; c < 4; c++)
	{
		if (!(mask & (1 << c))) continue;
		if (!first) Serial.print('+');
		Serial.print(F("ch")); Serial.print(c); Serial.print(' '); Serial.print(PORT_OF_CHANNEL[c]);
		first = false;
	}
	if (first) Serial.print(F("none"));
	Serial.print(')');
}

static uint8_t faults;

// one channel selection: connect, read back, probe the lines
static void test_mask(uint8_t mask)
{
	reset_switch();
	Lines before = probe();
	bool acked = switch_write(mask);
	int back = switch_read();
	Lines l = probe();
	bool good = lines_good(before) && acked && back == mask && lines_good(l);
	if (!good) faults++;
	Serial.print(good ? F("ok    ") : F("FAULT "));
	print_mask(mask);
	Serial.print(F(": ack ")); Serial.print(acked ? F("yes") : F("NO"));
	Serial.print(F(", read back "));
	if (back < 0) Serial.print(F("NO ANSWER")); else { Serial.print(F("0x0")); Serial.print(back, HEX); }
	print_lines(l);
	if (!lines_good(before)) { Serial.print(F(" | before selecting:")); print_lines(before); }
	Serial.println();
}

// channel 0 with /RESET floating on its 10k pull-up (R11): a bridge from
// AX4_SDA or AX4_SCL to /RESET then resets the switch when the line is
// driven low, and the control register reads 0
static void test_reset_bridge()
{
	reset_switch();
	switch_write(0x01);
	int before = switch_read();
	release(RST_PIN);
	delayMicroseconds(100);
	bool rst_high = digitalRead(RST_PIN);
	drive_low(SDA_PIN); delayMicroseconds(20); release(SDA_PIN); delayMicroseconds(100);
	int after_sda = switch_read();
	digitalWrite(RST_PIN, HIGH); pinMode(RST_PIN, OUTPUT);
	reset_switch();
	switch_write(0x01);
	release(RST_PIN);
	delayMicroseconds(100);
	drive_low(SCL_PIN); delayMicroseconds(20); release(SCL_PIN); delayMicroseconds(100);
	int after_scl = switch_read();
	digitalWrite(RST_PIN, HIGH); pinMode(RST_PIN, OUTPUT);
	bool good = rst_high && before == 0x01 && after_sda == 0x01 && after_scl == 0x01;
	if (!good) faults++;
	Serial.print(good ? F("ok    ") : F("FAULT "));
	Serial.print(F("/RESET on its pull-up with ch0 connected: /RESET "));
	Serial.print(rst_high ? F("high") : F("LOW"));
	Serial.print(F(", control 0x")); Serial.print(before, HEX);
	Serial.print(F(", after SDA low 0x")); Serial.print(after_sda, HEX);
	Serial.print(F(", after SCL low 0x")); Serial.print(after_scl, HEX);
	Serial.println(F(" (0x1 each: no bridge to /RESET)"));
}

void setup()
{
	MCUCR = (1 << JTD);         // A0-A3 are JTAG pins on clones with JTAG on: turn it off
	MCUCR = (1 << JTD);
	TWCR = 0;                   // the TWI off: pins 2 and 3 by hand
	pinMode(SR_DATA, INPUT);
	digitalWrite(SR_CLOCK, LOW); pinMode(SR_CLOCK, OUTPUT);
	digitalWrite(SR_LOAD, HIGH); pinMode(SR_LOAD, OUTPUT);
	digitalWrite(RST_PIN, HIGH); pinMode(RST_PIN, OUTPUT);
	release(SDA_PIN); release(SCL_PIN);
	Serial.begin(115200);
}

void loop()
{
	while (!Serial) { }
	delay(500);
	faults = 0;
	Serial.println(F("=== HeliSR Rev 4.0 board test: I2C switch and AX ports (nothing plugged in) ==="));
	for (uint8_t mask = 0; mask < 16; mask++) test_mask(mask);
	test_reset_bridge();
	Serial.print(F("=== ")); Serial.print(faults); Serial.println(F(" fault(s) ==="));
	delay(3000);
}
