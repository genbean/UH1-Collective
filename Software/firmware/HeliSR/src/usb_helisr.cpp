/*
  usb_helisr.cpp - the HeliSR USB functions: a joystick and a settings channel

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.
  Descriptor handling follows the Arduino AVR core's HID library
  (Copyright (c) 2015, Arduino LLC, LGPL 2.1 or later).
*/

#include "usb_helisr.h"
#include "settings.h"
#include "shared/helisr_protocol.h"
#include <string.h>

#if defined(USBCON)

// HID class codes (the Arduino HID library's names)
#define HID_GET_REPORT          0x01
#define HID_GET_IDLE            0x02
#define HID_GET_PROTOCOL        0x03
#define HID_SET_REPORT          0x09
#define HID_SET_IDLE            0x0A
#define HID_SET_PROTOCOL        0x0B
#define HID_DESCRIPTOR_TYPE     0x21
#define HID_REPORT_DESC_TYPE    0x22
#define HID_REPORT_PROTOCOL     1

// ---------------------------------------------------- report descriptors --

static const uint8_t SETTINGS_DESC[] PROGMEM = {
	0x06, 0x00, 0xFF,           // Usage Page (Vendor 0xFF00)
	0x09, 0x01,                 // Usage (1)
	0xA1, 0x01,                 // Collection (Application)
	0x85, HSR_REPORT_CFG,       //   Report ID
	0x15, 0x00,                 //   Logical Minimum (0)
	0x26, 0xFF, 0x00,           //   Logical Maximum (255)
	0x75, 0x08,                 //   Report Size (8)
	0x95, HSR_PACKET_SIZE - 1,  //   Report Count (63)
	0x09, 0x02,                 //   Usage (2)
	0x81, 0x02,                 //   Input (Data, Var, Abs)
	0x09, 0x03,                 //   Usage (3)
	0x91, 0x02,                 //   Output (Data, Var, Abs)
	0xC0                        // End Collection
};

static const uint8_t JOY_HEAD[] PROGMEM = {
	0x05, 0x01,                 // Usage Page (Generic Desktop)
	0x09, 0x04,                 // Usage (Joystick)
	0xA1, 0x01,                 // Collection (Application)
	0x85, HSR_REPORT_JOY,       //   Report ID
};

static const uint8_t JOY_AXES[] PROGMEM = {
	0x05, 0x01,                 //   Usage Page (Generic Desktop)
	0x16, 0x01, 0x80,           //   Logical Minimum (-32767)
	0x26, 0xFF, 0x7F,           //   Logical Maximum (32767)
	0x75, 0x10,                 //   Report Size (16)
};

static const uint8_t JOY_POVS[] PROGMEM = {
	0x05, 0x01,                 //   Usage Page (Generic Desktop)
	0x15, 0x00,                 //   Logical Minimum (0)
	0x25, 0x07,                 //   Logical Maximum (7)
	0x35, 0x00,                 //   Physical Minimum (0)
	0x46, 0x3B, 0x01,           //   Physical Maximum (315)
	0x65, 0x14,                 //   Unit (degrees)
	0x75, 0x08,                 //   Report Size (8)
};

// Axis usages for axis_config 0-7: X, Y, Z, Rx, Ry, Rz, Slider, Slider.
static const uint8_t AXIS_USAGE[HSR_MAX_AXES] PROGMEM = { 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x36 };

// Sends (send = 1) or just measures (send = 0) the joystick report descriptor,
// built from the layout. Returns its length, or -1 on a USB error.
int HeliUSB_::joystickDescriptor(uint8_t send)
{
	int total = 0;
	uint8_t err = 0;

	auto put = [&](const void *d, uint8_t len, uint8_t pgm) {
		if (send && USB_SendControl(pgm ? TRANSFER_PGM : 0, d, len) < 0) err = 1;
		total += len;
	};
	auto put2 = [&](uint8_t a, uint8_t b) {
		uint8_t d[2] = { a, b };
		put(d, 2, 0);
	};

	put(JOY_HEAD, sizeof(JOY_HEAD), 1);

	if (joy.buttons)
	{
		put2(0x05, 0x09);                   // Usage Page (Button)
		put2(0x19, 0x01);                   // Usage Minimum (1)
		put2(0x29, joy.buttons);            // Usage Maximum
		put2(0x15, 0x00);                   // Logical Minimum (0)
		put2(0x25, 0x01);                   // Logical Maximum (1)
		put2(0x75, 0x01);                   // Report Size (1)
		put2(0x95, joy.buttons);            // Report Count
		put2(0x81, 0x02);                   // Input (Data, Var, Abs)
		if (joy.buttons & 7)
		{
			put2(0x75, 0x01);               // padding to a whole byte
			put2(0x95, 8 - (joy.buttons & 7));
			put2(0x81, 0x03);               // Input (Const)
		}
	}

	if (joy.axes)
	{
		put(JOY_AXES, sizeof(JOY_AXES), 1);
		put2(0x95, joy.axes);               // Report Count
		for (uint8_t i = 0; i < joy.axes; i++)
			put2(0x09, pgm_read_byte(&AXIS_USAGE[joy.axis_index[i]]));
		put2(0x81, 0x02);                   // Input (Data, Var, Abs)
	}

	if (joy.povs)
	{
		put(JOY_POVS, sizeof(JOY_POVS), 1);
		put2(0x95, joy.povs);               // Report Count
		for (uint8_t i = 0; i < joy.povs; i++)
			put2(0x09, 0x39);               // Usage (Hat switch)
		put2(0x81, 0x42);                   // Input (Data, Var, Abs, Null state)
		put2(0x65, 0x00);                   // Unit (none)
	}

	uint8_t end = 0xC0;                     // End Collection
	put(&end, 1, 0);

	return err ? -1 : total;
}

// ------------------------------------------------------------- the module --

HeliUSB_::HeliUSB_(void) : PluggableUSBModule(3, 2, epType), currentReport(0), protocol(HID_REPORT_PROTOCOL), idle(1)
{
	// Endpoint order matters. The core's start-of-frame interrupt calls
	// USB_Flush(CDC_TX) every millisecond, CDC_TX being endpoint 3, even when
	// the USB serial port is compiled out (Arduino AVR core 1.8.8). Without the
	// serial port this module's endpoints are 1-3, so endpoint 3 must be one
	// where that flush is harmless: the settings IN endpoint, which is always
	// written and released in one go. On an OUT endpoint the flush throws away
	// a received packet; on the joystick it could split a report.
	epType[0] = EP_TYPE_INTERRUPT_IN;       // joystick
	epType[1] = EP_TYPE_INTERRUPT_OUT;      // settings, PC to device
	epType[2] = EP_TYPE_INTERRUPT_IN;       // settings, device to PC

	// The PC asks for the descriptors as soon as the core attaches USB, which
	// is before setup() runs, so the settings are loaded here.
	settings_begin();
	joy_plan(&joy, &g_config);
	joyDescLength = joystickDescriptor(0);

	PluggableUSB().plug(this);
}

// One HID interface: interface, HID class and endpoint descriptors, sent a
// few bytes at a time from one small buffer. This runs inside the USB
// interrupt, so it's kept light on stack.
static int sendHidInterface(uint8_t iface, uint16_t report_len, uint8_t ep_in, uint8_t ep_out)
{
	uint8_t d[9] = { 9, 4, iface, 0, (uint8_t)(ep_out ? 2 : 1), USB_DEVICE_CLASS_HUMAN_INTERFACE, 0, 0, 0 };
	if (USB_SendControl(0, d, 9) < 0) return -1;
	uint8_t h[9] = { 9, HID_DESCRIPTOR_TYPE, 0x11, 0x01, 0, 1, HID_REPORT_DESC_TYPE, lowByte(report_len), highByte(report_len) };
	if (USB_SendControl(0, h, 9) < 0) return -1;
	uint8_t e[7] = { 7, 5, USB_ENDPOINT_IN(ep_in), USB_ENDPOINT_TYPE_INTERRUPT, USB_EP_SIZE, 0, 1 };
	if (USB_SendControl(0, e, 7) < 0) return -1;
	if (ep_out)
	{
		e[2] = USB_ENDPOINT_OUT(ep_out);
		if (USB_SendControl(0, e, 7) < 0) return -1;
	}
	return 1;
}

int HeliUSB_::getInterface(uint8_t *interfaceCount)
{
	*interfaceCount += 2;
	if (sendHidInterface(pluggedInterface, joyDescLength, pluggedEndpoint, 0) < 0) return -1;
	return sendHidInterface(pluggedInterface + 1, sizeof(SETTINGS_DESC), pluggedEndpoint + 2, pluggedEndpoint + 1);
}

static int sendString(const char *s, uint8_t maxlen)
{
	uint8_t len = strnlen(s, maxlen);
	uint8_t head[2] = { (uint8_t)(2 + 2 * len), 3 };   // length, STRING descriptor
	if (USB_SendControl(0, head, 2) < 0) return -1;
	for (uint8_t i = 0; i < len; i++)
	{
		uint8_t c = (uint8_t)s[i];
		uint8_t utf16[2] = { (uint8_t)((c >= 0x20 && c < 0x7F) ? c : '?'), 0 };
		if (USB_SendControl(0, utf16, 2) < 0) return -1;
	}
	return 1;
}

int HeliUSB_::getDescriptor(USBSetup &setup)
{
	// HID report descriptors, asked per interface.
	if (setup.bmRequestType == REQUEST_DEVICETOHOST_STANDARD_INTERFACE && setup.wValueH == HID_REPORT_DESC_TYPE)
	{
		if (setup.wIndex == pluggedInterface)
		{
			protocol = HID_REPORT_PROTOCOL;
			return joystickDescriptor(1);
		}
		if (setup.wIndex == (uint16_t)(pluggedInterface + 1))
			return USB_SendControl(TRANSFER_PGM, SETTINGS_DESC, sizeof(SETTINGS_DESC));
		return 0;
	}

	if (setup.bmRequestType != (REQUEST_DEVICETOHOST | REQUEST_STANDARD | REQUEST_DEVICE)) return 0;

	// Device descriptor, with the USB IDs from the settings.
	if (setup.wValueH == USB_DEVICE_DESCRIPTOR_TYPE)
	{
		uint16_t vid = g_config.vid ? g_config.vid : HSR_DEFAULT_VID;
		uint16_t pid = g_config.pid ? g_config.pid : HSR_DEFAULT_PID;
#ifdef CDC_ENABLED
		DeviceDescriptor d = D_DEVICE(0xEF, 0x02, 0x01, 64, vid, pid, HSR_FIRMWARE_VERSION, IMANUFACTURER, IPRODUCT, ISERIAL, 1);
#else
		DeviceDescriptor d = D_DEVICE(0x00, 0x00, 0x00, 64, vid, pid, HSR_FIRMWARE_VERSION, IMANUFACTURER, IPRODUCT, ISERIAL, 1);
#endif
		return USB_SendControl(0, &d, sizeof(d));
	}

	// Product and manufacturer names. The language list and the serial number
	// are left to the core (the serial number comes from getShortName()).
	if (setup.wValueH == USB_STRING_DESCRIPTOR_TYPE)
	{
		if (setup.wValueL == IPRODUCT)
		{
			if (g_config.device_name[0] == 0) return sendString(HSR_DEFAULT_NAME, HSR_NAME_LEN);
			return sendString(g_config.device_name, HSR_NAME_LEN);
		}
		if (setup.wValueL == IMANUFACTURER)
			return sendString(HSR_MANUFACTURER, 32);
	}
	return 0;
}

bool HeliUSB_::setup(USBSetup &setup)
{
	if (setup.wIndex != pluggedInterface && setup.wIndex != (uint16_t)(pluggedInterface + 1)) return false;

	uint8_t request = setup.bRequest;
	if (setup.bmRequestType == REQUEST_DEVICETOHOST_CLASS_INTERFACE)
	{
		if (request == HID_GET_PROTOCOL) return USB_SendControl(0, &protocol, 1) >= 0;
		if (request == HID_GET_IDLE) return USB_SendControl(0, &idle, 1) >= 0;
		// GET_REPORT for the joystick's input report: Windows may ask for the
		// current state when a program opens the device.
		if (request == HID_GET_REPORT && setup.wIndex == pluggedInterface && setup.wValueH == 1 &&
		    setup.wValueL == HSR_REPORT_JOY && currentReport)
			return USB_SendControl(0, currentReport, joy.report_size + 1) >= 0;
		return false;
	}
	if (setup.bmRequestType == REQUEST_HOSTTODEVICE_CLASS_INTERFACE)
	{
		if (request == HID_SET_PROTOCOL) { protocol = setup.wValueL; return true; }
		if (request == HID_SET_IDLE) { idle = setup.wValueH; return true; }
	}
	return false;
}

// USB serial number: "HSR" and the board's unique ID in hex.
uint8_t HeliUSB_::getShortName(char *name)
{
	uint32_t id = settings_unique_id();
	name[0] = 'H'; name[1] = 'S'; name[2] = 'R';
	for (uint8_t i = 0; i < 8; i++)
	{
		uint8_t d = (id >> (28 - 4 * i)) & 0x0F;
		name[3 + i] = d < 10 ? '0' + d : 'A' + d - 10;
	}
	return 11;
}

// ---------------------------------------------------------------- traffic --

int HeliUSB_::sendJoystick(const uint8_t *report)
{
	// One USB_Send for the whole report, so nothing can release half of it.
	uint8_t ep = pluggedEndpoint;
	if (USB_SendSpace(ep) < joy.report_size + 1) return -1;
	return USB_Send(ep | TRANSFER_RELEASE, report, joy.report_size + 1);
}

int HeliUSB_::sendSettings(const uint8_t *packet)
{
	uint8_t ep = pluggedEndpoint + 2;
	if (USB_SendSpace(ep) < HSR_PACKET_SIZE) return -1;
	return USB_Send(ep | TRANSFER_RELEASE, packet, HSR_PACKET_SIZE);
}

uint8_t HeliUSB_::readSettings(uint8_t *packet)
{
	uint8_t ep = pluggedEndpoint + 1;
	if (!USB_Available(ep)) return 0;
	return USB_Recv(ep, packet, HSR_PACKET_SIZE) == HSR_PACKET_SIZE;
}

HeliUSB_ &HeliUSB(void)
{
	static HeliUSB_ obj;
	return obj;
}

// Create the module during static initialisation, before main() attaches USB.
static HeliUSB_ &heli_usb_instance __attribute__((used)) = HeliUSB();

#endif
