/*
  tests.cpp - scenario tests of the firmware's button, axis, encoder and LED
  logic, run on the PC

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  Timings follow FreeJoy's rules (defaults: debounce 20 ms, press timer
  100 ms, timers 50/200/300 ms, axis-to-button debounce 50 ms):
    - a switch change is first seen on pass 1 and accepted on the first pass
      more than 20 ms later: pass 22;
    - a normal button then goes on one pass later (DELAY -> PRESS), pass 23,
      and stays on for at least the press time;
    - a release is accepted on pass 22 and, once the press time is over, the
      button follows at once.
*/

#include <stddef.h>
#include <string.h>
#include "sim.h"

#define CFG g_config
#define B(j) CFG.buttons[j]
#define AX(i) CFG.axis_config[i]

static uint16_t raw_for(int32_t axis_value)    // analog reading that gives this raw axis value
{
	return (uint16_t)(((int32_t)axis_value - AXIS_MIN_VALUE) * HSR_RAW_MAX / AXIS_SPAN);
}

// ------------------------------------------------------------------ layout --

static void t_layout()
{
	scenario("settings layout on this compiler (the configurator uses the same one)");
	CHECK_EQ(sizeof(dev_config_t), HSR_CONFIG_SIZE);
	CHECK_EQ(offsetof(dev_config_t, axis_config), 43);
	CHECK_EQ(offsetof(dev_config_t, buttons), 283);
	CHECK_EQ(offsetof(dev_config_t, axes_to_buttons), 483);
	CHECK_EQ(offsetof(dev_config_t, vid), 600);
	CHECK_EQ(offsetof(dev_config_t, led_pwm_config), 604);
	CHECK_EQ(offsetof(dev_config_t, leds), 612);
	CHECK_EQ(offsetof(dev_config_t, encoders), 642);
	CHECK_EQ(sizeof(hsr_info_t), 23);
	CHECK_EQ(sizeof(hsr_test_step_t), 24);
	CHECK_EQ(sizeof(hsr_test_result_t), 43);

	// bit-field positions, as the firmware (avr-gcc) lays them out
	button_t b;
	uint8_t braw[3] = { 5, (uint8_t)(31 | (3 << 5)), (uint8_t)(1 | (1 << 1) | (2 << 2) | (3 << 5)) };
	memcpy(&b, braw, 3);
	CHECK(b.physical_num == 5 && b.type == 31 && b.shift_modificator == 3);
	CHECK(b.is_inverted == 1 && b.is_disabled == 1 && b.delay_timer == 2 && b.press_timer == 3);

	axis_config_t a;
	uint8_t araw[30];
	memset(araw, 0, sizeof(araw));
	araw[6] = 1 | (1 << 1) | (1 << 2) | (2 << 3) | (5 << 5);
	araw[18] = 9 | (4 << 4);
	araw[19] = 100 | (1 << 7);
	araw[20] = (uint8_t)-3;
	araw[21] = 6 | (17 << 3);
	araw[27] = 4 | (3 << 3) | (5 << 5);
	memcpy(&a, araw, 30);
	CHECK(a.out_enabled == 1 && a.inverted == 1 && a.is_centered == 1 && a.function == 2 && a.filter == 5);
	CHECK(a.resolution == 9 && a.channel == 4 && a.deadband_size == 100 && a.is_dynamic_deadband == 1);
	CHECK(a.source_main == -3 && a.source_secondary == 6 && a.offset_angle == 17);
	CHECK(a.button1_type == 4 && a.button2_type == 3 && a.button3_type == 5);

	led_config_t l;
	uint8_t lraw[2] = { 7, (uint8_t)(1 | (15 << 3)) };
	memcpy(&l, lraw, 2);
	CHECK(l.input_num == 7 && l.type == 1 && l.timer == 15);
	led_pwm_config_t p;
	uint8_t praw[2] = { 40, (uint8_t)(6 | (1 << 3)) };
	memcpy(&p, praw, 2);
	CHECK(p.duty_cycle == 40 && p.axis_num == 6 && p.is_axis == 1);
}

// ---------------------------------------------------------------- buttons --

static void t_defaults()
{
	scenario("factory settings: IN1-16 are buttons 1-16, AX1-4 are X Y Z Rx");
	Sim s; s.begin();
	CHECK_EQ(s.L.buttons, 16);
	CHECK_EQ(s.L.axes, 4);
	CHECK_EQ(s.L.povs, 0);
	CHECK_EQ(s.L.report_size, 10);
	s.step(30);
	CHECK(!s.log(4));
	s.in(5, true);
	int t = s.until([&] { return s.log(4); }, 100);
	CHECK_EQ(t, 23);
	uint8_t rep[HSR_MAX_REPORT_SIZE];
	s.report(rep);
	CHECK_EQ(rep[0], 0x10);
	CHECK_EQ(rep[1], 0x00);
	s.step(200);
	s.in(5, false);
	t = s.until([&] { return !s.log(4); }, 100);
	CHECK_EQ(t, 22);
}

static void t_debounce()
{
	scenario("debounce: a 10 ms blip is ignored, a 30 ms press counts");
	Sim s; s.begin();
	s.step(10);
	s.in(1, true); s.step(10); s.in(1, false);
	CHECK(s.holds([&] { return !s.log(0) && !s.phy(0); }, 200));
	s.in(1, true); s.step(30); s.in(1, false);
	CHECK(s.phy(0) && s.log(0));

	scenario("debounce: longer setting delays acceptance");
	CFG.button_debounce_ms = 60;
	s.begin();
	s.step(10);
	s.in(1, true);
	CHECK_EQ(s.until([&] { return s.phy(0); }, 200), 62);
}

static void t_inverted()
{
	scenario("inverted button: on at rest, off while pressed");
	B(0).is_inverted = 1;
	Sim s; s.begin();
	s.step(5);
	CHECK(s.log(0));
	s.in(1, true);
	CHECK(s.until([&] { return !s.log(0); }, 100) > 0);
}

static void t_timers()
{
	scenario("delay timer 1 (50 ms): the press shows 50 ms late");
	B(0).delay_timer = BUTTON_TIMER_1;
	Sim s; s.begin();
	s.step(5);
	s.in(1, true);
	int t = s.until([&] { return s.log(0); }, 200);
	CHECK_EQ(t, 73);        // accepted on pass 22, then 51 ms of delay

	scenario("press timer 2 (200 ms): a 30 ms tap lasts about 200 ms");
	settings_defaults(&CFG);
	B(0).press_timer = BUTTON_TIMER_2;
	s.begin();
	s.step(5);
	s.in(1, true); s.step(30); s.in(1, false);
	CHECK(s.log(0));
	t = s.until([&] { return !s.log(0); }, 400);
	CHECK_NEAR(t + 30, 222, 2);   // on at 22, off when 200 ms have passed
}

static void t_toggle()
{
	scenario("latching toggle: press on, press off");
	B(0).type = BUTTON_TOGGLE;
	Sim s; s.begin();
	s.step(5);
	s.in(1, true); s.step(150); s.in(1, false); s.step(150);
	CHECK(s.log(0));
	s.in(1, true); s.step(150); s.in(1, false); s.step(150);
	CHECK(!s.log(0));
}

static void t_toggle_switch()
{
	scenario("toggle switch: a 100 ms pulse on each flip");
	B(0).type = TOGGLE_SWITCH;
	Sim s; s.begin();
	s.step(5);
	s.in(1, true);
	CHECK_EQ(s.until([&] { return s.log(0); }, 100), 23);
	CHECK_NEAR(s.until([&] { return !s.log(0); }, 300), 101, 2);
	CHECK(s.holds([&] { return !s.log(0); }, 300));    // held: off
	s.in(1, false);
	CHECK_EQ(s.until([&] { return s.log(0); }, 100), 23);
	CHECK_NEAR(s.until([&] { return !s.log(0); }, 300), 101, 2);

	scenario("toggle switch ON: pulse only when closing");
	settings_defaults(&CFG);
	B(0).type = TOGGLE_SWITCH_ON;
	s.begin(); s.step(5);
	s.in(1, true);
	CHECK(s.until([&] { return s.log(0); }, 100) > 0);
	s.step(300);
	s.in(1, false);
	CHECK(s.holds([&] { return !s.log(0); }, 300));

	scenario("toggle switch OFF: pulse only when opening");
	settings_defaults(&CFG);
	B(0).type = TOGGLE_SWITCH_OFF;
	s.begin(); s.step(5);
	s.in(1, true);
	CHECK(s.holds([&] { return !s.log(0); }, 300));
	s.in(1, false);
	CHECK(s.until([&] { return s.log(0); }, 100) > 0);
}

static void t_switch_center()
{
	scenario("3-position switch centre (HeliSR addition): on while IN3 and IN4 are both open");
	B(0).physical_num = 2;
	B(0).type = SWITCH_CENTER;
	Sim s; s.begin();
	s.step(5);
	CHECK(s.log(0));
	s.step(150);                     // past the start-up press time (100 ms)
	s.in(3, true);
	CHECK_EQ(s.until([&] { return !s.log(0); }, 100), 22);
	s.in(3, false);
	CHECK(s.until([&] { return s.log(0); }, 100) > 0);
	s.step(200);
	s.in(4, true);
	CHECK(s.until([&] { return !s.log(0); }, 100) > 0);
}

static void t_pov()
{
	scenario("hat from four buttons, with a centre button");
	B(0).type = POV1_UP; B(1).type = POV1_RIGHT; B(2).type = POV1_DOWN; B(3).type = POV1_LEFT;
	B(4).type = POV1_CENTER;        // IN5: the hat's push
	Sim s; s.begin();
	CHECK_EQ(s.L.povs, 1);
	CHECK_EQ(s.L.buttons, 12);      // the four directions aren't buttons
	s.step(5);
	CHECK_EQ(s.pov(0), 0xFF);
	struct { int a, b; uint8_t hat; } dirs[] = {
		{ 1, 0, 0 }, { 1, 2, 1 }, { 2, 0, 2 }, { 2, 3, 3 }, { 3, 0, 4 }, { 3, 4, 5 }, { 4, 0, 6 }, { 4, 1, 7 } };
	for (auto &d : dirs)
	{
		s.sr = 0; s.step(150);
		s.in(d.a, true);
		if (d.b) s.in(d.b, true);
		s.step(150);
		CHECK_EQ(s.pov(0), d.hat);
	}
	s.sr = 0; s.step(150);
	CHECK_EQ(s.pov(0), 0xFF);

	// centre push alone: forced 100 ms delay, then on
	s.in(5, true);
	int t = s.until([&] { return s.log(4); }, 300);
	CHECK_NEAR(t, 122, 2);
	// a direction blocks the centre button
	s.in(1, true);
	CHECK(s.until([&] { return !s.log(4); }, 100) >= 0);
	CHECK(s.holds([&] { return !s.log(4); }, 200));
	CHECK_EQ(s.pov(0), 0);
}

static void t_radio()
{
	scenario("radio buttons: one of three on, the first at start");
	for (int j = 0; j < 3; j++) B(j).type = RADIO_BUTTON1;
	Sim s; s.begin();
	s.step(5);
	CHECK(s.log(0) && !s.log(1) && !s.log(2));
	s.in(2, true); s.step(150); s.in(2, false); s.step(150);
	CHECK(!s.log(0) && s.log(1) && !s.log(2));
	s.in(3, true); s.step(150); s.in(3, false); s.step(150);
	CHECK(!s.log(0) && !s.log(1) && s.log(2));
}

static void t_sequential()
{
	scenario("sequential toggle: one input steps through three buttons");
	for (int j = 0; j < 3; j++) { B(j).physical_num = 0; B(j).type = SEQUENTIAL_TOGGLE; }
	Sim s; s.begin();
	s.step(5);
	CHECK(s.log(0) && !s.log(1) && !s.log(2));
	int expect[] = { 1, 2, 0, 1 };
	for (int k : expect)
	{
		s.in(1, true); s.step(150); s.in(1, false); s.step(150);
		CHECK(s.log(k) && s.log((k + 1) % 3) == false && s.log((k + 2) % 3) == false);
	}

	scenario("sequential button: each press pulses the next button");
	settings_defaults(&CFG);
	for (int j = 0; j < 3; j++) { B(j).physical_num = 0; B(j).type = SEQUENTIAL_BUTTON; }
	s.begin();
	s.step(5);
	CHECK(!s.log(0) && !s.log(1) && !s.log(2));
	int order[] = { 0, 1, 2, 0 };
	for (int k : order)
	{
		s.in(1, true); s.step(60);
		CHECK(s.log(k) && !s.log((k + 1) % 3) && !s.log((k + 2) % 3));
		s.in(1, false); s.step(200);
		CHECK(!s.log(0) && !s.log(1) && !s.log(2));
	}

	scenario("sequential buttons: three groups each start correctly (FreeJoy start-up fixed)");
	settings_defaults(&CFG);
	for (int g = 0; g < 3; g++)
		for (int k = 0; k < 2; k++) { B(g * 2 + k).physical_num = g; B(g * 2 + k).type = SEQUENTIAL_BUTTON; }
	s.begin();
	s.step(5);
	for (int g = 0; g < 3; g++)
	{
		s.in(g + 1, true); s.step(60);
		CHECK(s.log(g * 2) && !s.log(g * 2 + 1));       // first press: the group's first button
		s.in(g + 1, false); s.step(200);
	}
}

static void t_shift()
{
	scenario("shift layer: IN2 is button 2, or button 21 while shift (IN16) is held");
	CFG.shift_config[0].button = 15;
	B(20).physical_num = 1;
	B(20).shift_modificator = 1;
	Sim s; s.begin();
	s.step(5);
	s.in(2, true); s.step(150);
	CHECK(s.log(1) && !s.log(20));
	s.in(2, false); s.step(150);
	s.in(16, true); s.step(150);
	CHECK(s.r.shifts == 1);
	s.in(2, true); s.step(150);
	CHECK(!s.log(1) && s.log(20));
	s.in(16, false); s.step(150);
	CHECK(s.r.shifts == 0);
	CHECK(!s.log(20));
}

static void t_a2b()
{
	scenario("axis to buttons: X split into three ranges");
	CFG.axes_to_buttons[0].buttons_cnt = 3;
	CFG.axes_to_buttons[0].points[0] = 0;
	CFG.axes_to_buttons[0].points[1] = 85;
	CFG.axes_to_buttons[0].points[2] = 170;
	CFG.axes_to_buttons[0].points[3] = 255;
	for (int k = 0; k < 3; k++) B(20 + k).physical_num = HSR_PHYS_A2B_FIRST + k;
	Sim s; s.begin();
	uint16_t raw[] = { 0, HSR_RAW_MAX / 2, HSR_RAW_MAX };
	for (int k = 0; k < 3; k++)
	{
		s.analog[0] = raw[k];
		s.step(100);
		CHECK(s.log(20 + k) && s.log(20 + (k + 1) % 3) == false && s.log(20 + (k + 2) % 3) == false);
	}
	// a 30 ms excursion is inside the 50 ms axis-to-button debounce
	s.analog[0] = 0; s.step(100);
	s.analog[0] = HSR_RAW_MAX; s.step(30); s.analog[0] = 0;
	CHECK(s.holds([&] { return s.log(20) && !s.log(22); }, 150));
	// sweep: always exactly one range
	bool one = true;
	for (int v = 0; v <= HSR_RAW_MAX; v += 97)
	{
		s.analog[0] = (uint16_t)v; s.step(60);
		one = one && (s.log(20) + s.log(21) + s.log(22) == 1);
	}
	CHECK(one);
}

static void t_encoders()
{
	static const uint8_t cw[4] = { 1, 3, 2, 0 };     // A, A+B, B, none
	static const uint8_t ccw[4] = { 2, 3, 1, 0 };
	struct { uint8_t conf; int per_cycle; } modes[] = { { ENCODER_CONF_1x, 1 }, { ENCODER_CONF_2x, 2 }, { ENCODER_CONF_4x, 4 } };
	for (auto &m : modes)
	{
		char name[96];
		snprintf(name, sizeof(name), "encoder on IN1/IN2 (%dx): buttons pulse, axis counts", m.per_cycle);
		scenario(name);
		B(0).type = ENCODER_INPUT_A;
		B(1).type = ENCODER_INPUT_B;
		CFG.encoders[0] = m.conf;
		AX(4).source_main = SOURCE_ENCODER;
		AX(4).channel = 0;
		AX(4).out_enabled = 1;
		Sim s; s.begin();
		CHECK_EQ(s.L.axes, 5);
		s.step(10);
		bool a_seen = false, b_seen = false;
		for (int c = 0; c < 10; c++)
			for (int k = 0; k < 4; k++)
			{
				s.sr = cw[k];
				for (int t = 0; t < 5; t++) { s.step(); a_seen |= s.log(0); b_seen |= s.log(1); }
			}
		CHECK(a_seen && !b_seen);
		CHECK_EQ(s.axis(4), 10 * m.per_cycle);
		s.step(100);
		CHECK(!s.log(0));
		a_seen = b_seen = false;
		for (int c = 0; c < 20; c++)
			for (int k = 0; k < 4; k++)
			{
				s.sr = ccw[k];
				for (int t = 0; t < 5; t++) { s.step(); a_seen |= s.log(0); b_seen |= s.log(1); }
			}
		CHECK(b_seen && !a_seen);
		CHECK_EQ(s.axis(4), -10 * m.per_cycle);
		settings_defaults(&CFG);
	}
}

// ------------------------------------------------------------------- axes --

static void t_axes_basic()
{
	scenario("axis: linear mapping of the 12-bit reading");
	Sim s; s.begin();
	s.analog[0] = 0; s.step();
	CHECK_EQ(s.axis(0), -32767);
	s.analog[0] = HSR_RAW_MAX; s.step();
	CHECK_EQ(s.axis(0), 32767);
	s.analog[0] = HSR_RAW_MAX / 2; s.step();
	CHECK_NEAR(s.axis(0), 0, 16);

	scenario("axis: calibration narrows the range, centre and dead zone");
	settings_defaults(&CFG);
	AX(0).calib_min = -16384; AX(0).calib_center = 0; AX(0).calib_max = 16384;
	AX(0).deadband_size = 100;      // (32767 * 100) >> 10 = 3199 each side
	s.begin();
	s.analog[0] = raw_for(-16384); s.step();
	CHECK_NEAR(s.axis(0), -32767, 20);
	s.analog[0] = raw_for(-20000); s.step();
	CHECK_EQ(s.axis(0), -32767);
	s.analog[0] = raw_for(1500); s.step();
	CHECK_EQ(s.axis(0), 0);
	s.analog[0] = raw_for(8000); s.step();
	// right half: (8000 - 1599) * 32767 / (16384 - 1599)
	CHECK_NEAR(s.axis(0), (8000 - 1599) * 32767 / (16384 - 1599), 40);

	scenario("axis: inversion");
	settings_defaults(&CFG);
	AX(1).inverted = 1;
	s.begin();
	s.analog[1] = 0; s.step();
	CHECK_EQ(s.axis(1), 32767);

	scenario("axis: an axis that isn't enabled reports 0");
	settings_defaults(&CFG);
	AX(2).out_enabled = 0;
	s.begin();
	s.analog[2] = HSR_RAW_MAX; s.step();
	CHECK_EQ(s.axis(2), 0);
	CHECK_EQ(s.L.axes, 3);

	scenario("axis: spare pin 4 as an analog source (Ry)");
	settings_defaults(&CFG);
	CFG.pins[2] = PIN_AXIS_ANALOG;
	AX(4).source_main = 4;
	AX(4).out_enabled = 1;
	s.begin();
	s.analog[4] = HSR_RAW_MAX; s.step();
	CHECK_EQ(s.axis(4), 32767);
}

static void t_axes_shape()
{
	scenario("axis: curve (flat at 0, then half slope)");
	for (int p = 0; p < 11; p++) AX(0).curve_shape[p] = 0;
	Sim s; s.begin();
	for (int v = 0; v <= HSR_RAW_MAX; v += 500) { s.analog[0] = (uint16_t)v; s.step(); CHECK_EQ(s.axis(0), 0); }
	for (int p = 0; p < 11; p++) AX(0).curve_shape[p] = (int8_t)((p * 20 - 100) / 2);
	s.begin();
	s.analog[0] = HSR_RAW_MAX; s.step();
	CHECK_NEAR(s.axis(0), 32767 / 2, 2);

	scenario("axis: resolution 8 bits");
	settings_defaults(&CFG);
	AX(0).resolution = 7;           // stored as bits - 1
	s.begin();
	s.analog[0] = HSR_RAW_MAX / 2; s.step();
	// FreeJoy's float step: index (v + 32767) >> 8, times 65534.0f / 255, plus
	// MIN, truncated towards zero. Mid-scale index 127 -> -128.5 -> -128; full
	// scale index 255 -> 32766.996 -> 32766 (FreeJoy's rounding, kept).
	int32_t mid = (int32_t)(HSR_RAW_MAX / 2) * AXIS_SPAN / HSR_RAW_MAX + AXIS_MIN_VALUE;    // the raw axis value
	CHECK_EQ(s.axis(0), (int32_t)((65534.0f / 255) * ((mid - AXIS_MIN_VALUE) >> 8) + AXIS_MIN_VALUE));
	s.analog[0] = HSR_RAW_MAX; s.step();
	CHECK_EQ(s.axis(0), (int32_t)((65534.0f / 255) * 255 - 32767));

	scenario("axis: prescaler 50 %, from minimum and centred, and only while a button is held");
	settings_defaults(&CFG);
	AX(0).prescaler = 50;
	AX(1).prescaler = 50; AX(1).is_centered = 1;
	AX(2).prescaler = 50; AX(2).button1 = 0; AX(2).button1_type = AXIS_BUTTON_PRESCALER_EN;
	s.begin();
	s.analog[0] = s.analog[1] = s.analog[2] = HSR_RAW_MAX; s.step(5);
	CHECK_EQ(s.axis(0), 0);
	CHECK_EQ(s.axis(1), 16383);
	CHECK_EQ(s.axis(2), 32767);
	s.in(1, true); s.step(40);
	CHECK_EQ(s.axis(2), 0);

	scenario("axis: filter level 7 smooths a step (FreeJoy's filter feeds back its outputs)");
	settings_defaults(&CFG);
	AX(0).filter = FILTER_LEVEL_7;
	s.begin();
	// Level 7 creeps up on its target: ~0.6 s to within 0.1 %, and integer
	// rounding finally stops it ~13 counts short (FreeJoy's algorithm).
	s.analog[0] = 0; s.step(1000);
	CHECK_NEAR(s.axis(0), -32767, 20);
	s.analog[0] = HSR_RAW_MAX; s.step();
	int32_t first = s.axis(0);
	CHECK(first > -32767 && first < -20000);
	bool rising = true; int32_t prev = first;
	for (int k = 0; k < 100; k++) { s.step(); rising = rising && s.axis(0) >= prev; prev = s.axis(0); }
	CHECK(rising);
	CHECK(s.axis(0) > 0);
	s.step(1000);
	CHECK_NEAR(s.axis(0), 32767, 20);

	scenario("axis: dynamic dead band holds through small jitter");
	settings_defaults(&CFG);
	AX(0).is_dynamic_deadband = 1;
	AX(0).deadband_size = 20;
	s.begin();
	s.analog[0] = 2000; s.step(50);
	int32_t held = s.axis(0);
	bool steady = true;
	for (int k = 0; k < 200; k++) { s.analog[0] = (uint16_t)(2000 + (k % 3) - 1); s.step(); steady = steady && s.axis(0) == held; }
	CHECK(steady);
	s.analog[0] = 3500; s.step(30);
	CHECK(s.axis(0) > held + 20000);

	scenario("axis: offset angle moves the wrap point");
	settings_defaults(&CFG);
	AX(0).offset_angle = 6;          // 6 * 170 = 1020 counts
	s.begin();
	s.analog[0] = 1020; s.step();
	CHECK_EQ(s.axis(0), -32767);
	s.analog[0] = 1000; s.step();
	CHECK(s.axis(0) > 30000);
}

static void t_axes_buttons()
{
	scenario("axis trim: up on IN3, down on IN1, reset on IN2 (divider 50)");
	AX(0).button1 = 0;               // AXIS_BUTTON_DOWN (default type)
	AX(0).button2 = 1;               // AXIS_BUTTON_RESET
	AX(0).button3 = 2;               // AXIS_BUTTON_UP
	Sim s; s.begin();
	s.analog[0] = HSR_RAW_MAX / 2; s.step(10);
	int32_t base = s.axis(0);
	int32_t step = AXIS_FULLSCALE / 50;
	s.in(3, true); s.step(60); s.in(3, false); s.step(150);
	CHECK_EQ(s.axis(0), base + step);
	s.in(1, true); s.step(60); s.in(1, false); s.step(150);
	s.in(1, true); s.step(60); s.in(1, false); s.step(150);
	CHECK_EQ(s.axis(0), base - step);
	s.in(2, true); s.step(60); s.in(2, false); s.step(150);
	CHECK_EQ(s.axis(0), base);
	// held: one step, then repeats every ~51 ms after 0.5 s
	s.in(3, true); s.step(22 + 2 + 500 + 51 * 4); s.in(3, false); s.step(150);
	CHECK_NEAR(s.axis(0), base + step * 5, step);

	scenario("axis centre button: makes the current position the centre");
	settings_defaults(&CFG);
	AX(0).button1 = 0; AX(0).button1_type = AXIS_BUTTON_CENTER;
	s.begin();
	s.analog[0] = 3000; s.step(10);
	CHECK(s.axis(0) > 10000);
	s.in(1, true); s.step(40); s.in(1, false); s.step(150);
	CHECK_EQ(s.axis(0), 0);

	scenario("axis functions: plus, minus (centred), equal");
	settings_defaults(&CFG);
	AX(1).function = FUNCTION_PLUS; AX(1).source_secondary = 0;
	AX(2).function = FUNCTION_MINUS; AX(2).source_secondary = 0; AX(2).is_centered = 1;
	AX(3).function = FUNCTION_EQUAL; AX(3).source_secondary = 0;
	s.begin();
	s.analog[0] = raw_for(-16384);
	s.analog[1] = raw_for(10000);
	s.analog[2] = raw_for(10000);
	s.step(3);
	int32_t x = s.axis(0);
	CHECK_NEAR(s.axis(1), 10000 + x + 32767, 20);
	CHECK_NEAR(s.axis(2), 10000 / 2 - x / 2, 20);
	CHECK_EQ(s.axis(3), x);
}

// ------------------------------------------------------- report and LEDs --

static void t_report()
{
	scenario("report: buttons packed in order, then axes, then hats");
	B(0).type = POV1_UP; B(1).type = POV1_RIGHT; B(2).type = POV1_DOWN; B(3).type = POV1_LEFT;
	B(5).physical_num = -1;          // a gap: buttons after it move up one
	Sim s; s.begin();
	CHECK_EQ(s.L.buttons, 11);
	CHECK_EQ(s.L.report_size, 2 + 8 + 1);
	s.in(1, true);                   // hat up
	s.in(5, true);                   // logical 4 = reported button 1
	s.in(7, true);                   // logical 6 = reported button 2 (logical 5 has no input)
	s.analog[0] = HSR_RAW_MAX;
	s.step(150);
	uint8_t rep[HSR_MAX_REPORT_SIZE];
	int n = s.report(rep);
	CHECK_EQ(n, 11);
	CHECK_EQ(rep[0], 0x03);
	CHECK_EQ(rep[1], 0x00);
	CHECK_EQ(rep[2], 0xFF); CHECK_EQ(rep[3], 0x7F);       // X = +32767
	CHECK_EQ(rep[4], 0x01); CHECK_EQ(rep[5], 0x80);       // Y = -32767
	CHECK_EQ(rep[10], 0);                                 // hat up
}

static void t_leds()
{
	scenario("single LED on TX follows button 1; inverted; blinking");
	CFG.pins[0] = PIN_LED_SINGLE;
	CFG.leds[0].input_num = 0;
	Sim s; s.begin();
	s.step(5);
	CHECK(!s.led(0));
	s.in(1, true); s.step(40);
	CHECK(s.led(0));
	CFG.leds[0].type = LED_INVERTED;
	s.begin(); s.step(5);
	CHECK(s.led(0));
	CFG.leds[0].type = LED_NORMAL;
	CFG.leds[0].timer = 0;           // led_timer_ms[0] = 50
	s.begin(); s.step(5);
	s.in(1, true); s.step(40);
	int changes = 0; bool last = s.led(0);
	for (int t = 0; t < 520; t++) { s.step(); if (s.led(0) != last) { changes++; last = s.led(0); } }
	CHECK_NEAR(changes, 10, 1);

	scenario("PWM on pin 5: fixed 40 %, and scaled by X");
	settings_defaults(&CFG);
	CFG.pins[3] = PIN_LED_PWM;
	CFG.led_pwm_config[0].duty_cycle = 40;
	s.begin(); s.step(2);
	CHECK_EQ(s.r.pwm[0], 40);
	CFG.led_pwm_config[0].is_axis = 1;
	CFG.led_pwm_config[0].axis_num = 0;
	s.begin();
	s.analog[0] = HSR_RAW_MAX; s.step(3);
	CHECK_EQ(s.r.pwm[0], 40);
	s.analog[0] = 0; s.step(3);
	CHECK_EQ(s.r.pwm[0], 0);
}

// --------------------------------------------------------- settings, time --

static void t_settings()
{
	scenario("settings: save, load, and reject a bad checksum or old version");
	settings_save();
	dev_config_t saved = CFG;
	CFG.button_debounce_ms = 99;
	CHECK_EQ(settings_load(), 1);
	CHECK(memcmp(&CFG, &saved, sizeof(CFG)) == 0);
	host_eeprom[100] ^= 0x55;
	CHECK_EQ(settings_load(), 0);
	host_eeprom[100] ^= 0x55;
	CHECK_EQ(settings_load(), 1);
	CFG.config_version = HSR_CONFIG_VERSION - 1;
	settings_save();
	CHECK_EQ(settings_load(), 0);
}

static void t_time_wrap()
{
	scenario("16-bit time: presses across the 65.5 s wrap work");
	B(1).type = TOGGLE_SWITCH;
	Sim s; s.begin(65520);
	s.step(5);
	s.in(1, true); s.in(2, true);
	CHECK_EQ(s.until([&] { return s.log(0); }, 100), 23);
	CHECK(s.log(1));
	CHECK(s.now < 1000);             // wrapped
	CHECK_NEAR(s.until([&] { return !s.log(1); }, 300), 100, 2);
	s.in(1, false);
	CHECK_EQ(s.until([&] { return !s.log(0); }, 300) >= 0, true);
}

// ------------------------------------------- FreeJoy bugs fixed in HeliSR --
// (Not in comparison builds, which bring the bugs back to match FreeJoy.)

#if !defined(HSR_FREEJOY_EXACT) || defined(HSR_FORCE_FIX_TESTS)
static void t_fixes()
{
	scenario("fix: a delayed button skipped by its shift layer doesn't stay stuck (FreeJoy: stuck for good)");
	CFG.shift_config[0].button = 15;             // IN16 is shift 1
	B(0).delay_timer = BUTTON_TIMER_3;           // IN1, 300 ms delay
	B(20).physical_num = 0;                      // IN1 in shift layer 1
	B(20).shift_modificator = 1;
	Sim s; s.begin();
	s.step(5);
	s.in(1, true); s.step(100);                  // button 1 is in its delay
	s.in(16, true); s.step(600);                 // shift held: button 1 isn't processed past its window
	s.in(16, false); s.in(1, false); s.step(600);
	s.in(1, true);
	CHECK(s.until([&] { return s.log(0); }, 600) > 0);

	scenario("fix: trim stops at the bottom without jumping back (FreeJoy wrote value + MIN)");
	settings_defaults(&CFG);
	AX(0).button1 = 0;                           // trim down on IN1
	AX(0).button3 = 2;                           // trim up on IN3
	s.begin();
	s.analog[0] = raw_for(10000); s.step(10);
	int32_t step = AXIS_FULLSCALE / 50;
	for (int k = 0; k < 40; k++) { s.in(1, true); s.step(60); s.in(1, false); s.step(80); }
	CHECK_EQ(s.axis(0), -32767);
	CHECK(s.holds([&] { return s.axis(0) == -32767; }, 200));
	s.in(3, true); s.step(60); s.in(3, false); s.step(80);
	CHECK_NEAR(s.axis(0), -32767 + step, 20);

	scenario("fix: dynamic dead band over spread-out history doesn't overflow (FreeJoy's sum wraps)");
	settings_defaults(&CFG);
	AX(0).is_dynamic_deadband = 1;
	AX(0).deadband_size = 127;
	s.begin();
	// History: samples near -30000, then (after a jump, which isn't recorded)
	// samples near +30000. With four of each, the squared deviations sum to
	// about 7.2e9, past 2^31: FreeJoy's sum wraps negative and it holds the
	// axis while it's moving.
	for (int k = 0; k < 40; k++) { s.analog[0] = (uint16_t)(raw_for(-30000) + (k & 1)); s.step(); }
	s.analog[0] = raw_for(30000); s.step();
	for (int k = 0; k < 4; k++) { s.analog[0] = (uint16_t)(raw_for(30000) + (k & 1)); s.step(); }
	// A slow, real movement, in steps that stay inside the 9 x 127 window
	// where the dead band can hold.
	int32_t before = s.axis(0);
	for (int k = 1; k <= 2; k++) { s.analog[0] = raw_for(30000 - 300 * k); s.step(); }
	CHECK(s.axis(0) < before - 400);             // followed (FreeJoy holds it here, then jumps)
}
#endif

void run_unit_tests()
{
	t_layout();
	t_defaults();
	t_debounce();
	t_inverted();
	t_timers();
	t_toggle();
	t_toggle_switch();
	t_switch_center();
	t_pov();
	t_radio();
	t_sequential();
	t_shift();
	t_a2b();
	t_encoders();
	t_axes_basic();
	t_axes_shape();
	t_axes_buttons();
	t_report();
	t_leds();
	t_settings();
	t_time_wrap();
#if !defined(HSR_FREEJOY_EXACT) || defined(HSR_FORCE_FIX_TESTS)
	t_fixes();
#endif
}
