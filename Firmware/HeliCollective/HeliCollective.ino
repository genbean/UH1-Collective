// Heli Collective firmware for the HeliSR Rev 3.0 board
// Pro Micro 5V/16 MHz (ATmega32U4), built as "Arduino Leonardo".
//
// The PC sees a USB game controller with:
//   - 16 buttons: IN1-IN16 on J1/J2 are buttons 1-16
//   - 3 optional "centre/off" buttons (17-19) for the toggles' OFF positions
//   - axes: AX1 (collective) = Z, AX4 (throttle) = Rx, AX2 = Ry, AX3 = Rz
//     (AX2/AX3 are spare in head Rev 2-4 and are left out unless enabled below)
//
// Board wiring (PCB/HeliSR_Rev3.0/README.md):
//   74HC165 x2: latch (SH/LD) = pin 3 (PD0), data (QH of U2) = pin 2 (PD1),
//               clock = pin 15 (PB1). Inputs have 10k pull-ups, switches go to GND,
//               so a closed switch reads 0.
//   AX1 = A3, AX2 = A2, AX3 = A1, AX4 = A0. AS5600s are programmed with the
//   PROG buttons (OUT-pin "Option B"), so they already span the full 0-5 V.
//
// Open the Serial Monitor (any baud) to see live inputs and raw axis readings.

#include <HID.h>

// ---------------------------------------------------------------- settings --

#define USE_AX2 0                 // 1 = report AX2 as Ry
#define USE_AX3 0                 // 1 = report AX3 as Rz
#define VIRTUAL_CENTER_BUTTONS 1  // 1 = buttons 17-19 for the toggles' OFF positions

const uint8_t DEBOUNCE_MS = 5;    // a switch must be steady this long to count

struct AxisConfig {
  uint8_t pin;
  bool invert;      // flip the direction in the firmware
  int16_t rawMin;   // raw reading (0-4092) that maps to 0
  int16_t rawMax;   // raw reading that maps to full scale (4095)
};

// Raw readings are 0-4092 (16 x 10-bit samples / 4). The AS5600 rails leave
// a few counts at each end, so a little is trimmed to reach 0 and full scale.
// Watch the Serial Monitor's "raw" numbers at each stop and set these if needed.
AxisConfig axes[] = {
  { A3, false, 20, 4072 },  // AX1 collective -> Z
  { A0, false, 20, 4072 },  // AX4 throttle   -> Rx (0 at cutoff, full at full open)
#if USE_AX2
  { A2, false, 20, 4072 },  // AX2            -> Ry
#endif
#if USE_AX3
  { A1, false, 20, 4072 },  // AX3            -> Rz
#endif
};
const uint8_t AXIS_COUNT = sizeof(axes) / sizeof(axes[0]);

// ------------------------------------------------------------------ pins --

const uint8_t PIN_SR_LATCH = 3;   // PD0 -> both 74HC165 SH/LD
const uint8_t PIN_SR_DATA  = 2;   // PD1 <- U2 QH
const uint8_t PIN_SR_CLOCK = 15;  // PB1 -> both 74HC165 CLK

// Input number (1-16) for each bit in the order it leaves the chain, from the
// "Shift order" column of HeliSR_Rev3.0_Input_Map.csv: IN5-IN16 come out
// first, then IN1-IN4.
const uint8_t BIT_TO_INPUT[16] = { 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4 };

// -------------------------------------------------------- HID descriptor --

const uint8_t REPORT_ID = 3;
const uint8_t BUTTON_COUNT = 24;  // 3 bytes; 20-24 are always off

static const uint8_t hidReportDescriptor[] PROGMEM = {
  0x05, 0x01,        // Usage Page (Generic Desktop)
  0x09, 0x04,        // Usage (Joystick)
  0xA1, 0x01,        // Collection (Application)
  0x85, REPORT_ID,   //   Report ID
  0x05, 0x09,        //   Usage Page (Button)
  0x19, 0x01,        //   Usage Minimum (1)
  0x29, BUTTON_COUNT,//   Usage Maximum (24)
  0x15, 0x00,        //   Logical Minimum (0)
  0x25, 0x01,        //   Logical Maximum (1)
  0x75, 0x01,        //   Report Size (1)
  0x95, BUTTON_COUNT,//   Report Count (24)
  0x81, 0x02,        //   Input (Data, Var, Abs)
  0x05, 0x01,        //   Usage Page (Generic Desktop)
  0x15, 0x00,        //   Logical Minimum (0)
  0x26, 0xFF, 0x0F,  //   Logical Maximum (4095)
  0x75, 0x10,        //   Report Size (16)
  0x95, AXIS_COUNT,  //   Report Count
  0x09, 0x32,        //   Usage (Z)   AX1
  0x09, 0x33,        //   Usage (Rx)  AX4
#if USE_AX2
  0x09, 0x34,        //   Usage (Ry)  AX2
#endif
#if USE_AX3
  0x09, 0x35,        //   Usage (Rz)  AX3
#endif
  0x81, 0x02,        //   Input (Data, Var, Abs)
  0xC0               // End Collection
};

struct __attribute__((packed)) JoystickReport {
  uint8_t buttons[BUTTON_COUNT / 8];
  uint16_t axis[AXIS_COUNT];
};

// ----------------------------------------------------------------- state --

JoystickReport report;
JoystickReport lastSent;

uint16_t inputs = 0;              // debounced, bit (n-1) = INn closed
uint16_t rawInputs = 0;
uint8_t steadyMs[16];

int16_t axisRaw[AXIS_COUNT];
int32_t axisFiltered[AXIS_COUNT]; // x16 fixed point
uint16_t axisOut[AXIS_COUNT];

// ------------------------------------------------------------ the inputs --

// Load both 74HC165s and clock out 16 bits. Returns bit (n-1) set when INn is closed.
uint16_t readShiftRegisters() {
  digitalWrite(PIN_SR_LATCH, LOW);   // parallel load
  delayMicroseconds(5);
  digitalWrite(PIN_SR_LATCH, HIGH);  // shift mode; U2's H input is now on QH
  delayMicroseconds(5);

  uint16_t closed = 0;
  for (uint8_t bit = 0; bit < 16; bit++) {
    if (digitalRead(PIN_SR_DATA) == LOW) {  // pulled to GND = switch closed
      closed |= 1u << (BIT_TO_INPUT[bit] - 1);
    }
    digitalWrite(PIN_SR_CLOCK, HIGH);  // rising edge shifts the next bit onto QH
    delayMicroseconds(2);
    digitalWrite(PIN_SR_CLOCK, LOW);
    delayMicroseconds(2);
  }
  return closed;
}

// A change only counts once the new reading has held for DEBOUNCE_MS.
void debounceInputs(uint16_t sample, uint8_t elapsedMs) {
  for (uint8_t i = 0; i < 16; i++) {
    uint16_t mask = 1u << i;
    if ((sample & mask) == (inputs & mask)) {
      steadyMs[i] = 0;
    } else if ((steadyMs[i] += elapsedMs) >= DEBOUNCE_MS) {
      inputs ^= mask;
      steadyMs[i] = 0;
    }
  }
}

bool inputClosed(uint8_t n) {
  return inputs & (1u << (n - 1));
}

// ------------------------------------------------------------- the axes --

int16_t readAxisRaw(uint8_t pin) {
  uint16_t sum = 0;
  for (uint8_t i = 0; i < 16; i++) sum += analogRead(pin);
  return sum >> 2;  // 0-4092
}

void updateAxes() {
  for (uint8_t a = 0; a < AXIS_COUNT; a++) {
    int16_t raw = readAxisRaw(axes[a].pin);
    axisRaw[a] = raw;

    // Light smoothing: each update moves 1/4 of the way to the new reading.
    axisFiltered[a] += ((int32_t)raw * 16 - axisFiltered[a]) / 4;
    int32_t smooth = axisFiltered[a] / 16;

    int32_t span = axes[a].rawMax - axes[a].rawMin;
    int32_t v = (smooth - axes[a].rawMin) * 4095 / span;
    v = constrain(v, 0, 4095);
    if (axes[a].invert) v = 4095 - v;

    // Ignore 1-count jitter, but always let the ends through.
    if (abs(v - (int32_t)axisOut[a]) >= 2 || v == 0 || v == 4095) {
      axisOut[a] = v;
    }
  }
}

// ---------------------------------------------------------------- report --

void setButton(uint8_t number, bool on) {  // number is 1-based
  uint8_t i = number - 1;
  if (on) report.buttons[i / 8] |= 1 << (i % 8);
}

void buildReport() {
  memset(&report, 0, sizeof(report));
  for (uint8_t n = 1; n <= 16; n++) setButton(n, inputClosed(n));

#if VIRTUAL_CENTER_BUTTONS
  setButton(17, !inputClosed(3) && !inputClosed(4));  // LDG LT EXT/RETR in the middle (OFF)
  setButton(18, !inputClosed(5) && !inputClosed(6));  // SL ON/STOW in the middle (OFF)
  setButton(19, !inputClosed(7));                     // LDG LT ON/OFF at OFF
#endif

  for (uint8_t a = 0; a < AXIS_COUNT; a++) report.axis[a] = axisOut[a];
}

// ----------------------------------------------------------------- debug --

void printDebug() {
  const uint8_t lineMax = 100;
  if (!Serial || Serial.availableForWrite() < 32) return;  // nobody listening

  char line[lineMax];
  char* p = line;
  p += sprintf(p, "IN1-16 ");
  for (uint8_t n = 1; n <= 16; n++) {
    *p++ = inputClosed(n) ? '1' : '.';
    if (n % 4 == 0) *p++ = ' ';
  }
  for (uint8_t a = 0; a < AXIS_COUNT && p - line < lineMax - 24; a++) {
    p += sprintf(p, " | A%u raw %4d out %4u", a, axisRaw[a], axisOut[a]);
  }
  *p = 0;
  Serial.println(line);
}

// ------------------------------------------------------------------ main --

void setup() {
  pinMode(PIN_SR_LATCH, OUTPUT);
  pinMode(PIN_SR_CLOCK, OUTPUT);
  pinMode(PIN_SR_DATA, INPUT);
  digitalWrite(PIN_SR_LATCH, HIGH);
  digitalWrite(PIN_SR_CLOCK, LOW);

  static HIDSubDescriptor node(hidReportDescriptor, sizeof(hidReportDescriptor));
  HID().AppendDescriptor(&node);

  Serial.begin(115200);

  // ADC clock 16 MHz / 32 = 500 kHz (default is /128): ~28 us a sample, so the
  // 16-sample average of an axis takes under half a millisecond.
  ADCSRA = (ADCSRA & ~0x07) | 0x05;

  for (uint8_t a = 0; a < AXIS_COUNT; a++) {
    int16_t raw = readAxisRaw(axes[a].pin);
    axisFiltered[a] = (int32_t)raw * 16;
  }
  inputs = readShiftRegisters();
  memset(&lastSent, 0xFF, sizeof(lastSent));  // force the first report out
}

void loop() {
  static uint32_t lastTickMs = 0;
  static uint32_t lastDebugMs = 0;

  uint32_t now = millis();
  uint8_t elapsedMs = min(now - lastTickMs, 255UL);
  lastTickMs = now;

  rawInputs = readShiftRegisters();
  debounceInputs(rawInputs, elapsedMs);
  updateAxes();
  buildReport();

  if (memcmp(&report, &lastSent, sizeof(report)) != 0) {
    if (HID().SendReport(REPORT_ID, &report, sizeof(report)) >= 0) {
      lastSent = report;
    }
  }

  if (now - lastDebugMs >= 100) {
    lastDebugMs = now;
    printDebug();
  }
}
