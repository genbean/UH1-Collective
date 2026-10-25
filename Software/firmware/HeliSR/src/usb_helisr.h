/*
  usb_helisr.h - the HeliSR USB functions: a joystick and a settings channel

  Part of HeliSR. Copyright (C) 2026 HeliSR contributors.
  Licensed under the GNU General Public License v3 or later; see LICENSE.

  One Arduino PluggableUSB module with two HID interfaces:
    interface A: the joystick, laid out from the settings (only the buttons,
                 axes and hats in use), one interrupt IN endpoint;
    interface B: the settings channel, 64-byte reports both ways over an
                 interrupt IN and an interrupt OUT endpoint.
  The Arduino HID library isn't used: it has no OUT endpoint and ignores data
  the PC sends. The module also answers the device descriptor and the product
  and manufacturer strings, so the USB IDs and name come from the settings.
*/

#ifndef HELISR_USB_H
#define HELISR_USB_H

#include <Arduino.h>
#include "PluggableUSB.h"
#include "shared/helisr_config.h"
#include "joy_layout.h"

class HeliUSB_ : public PluggableUSBModule
{
public:
	HeliUSB_(void);

	const JoyLayout &layout(void) const { return joy; }

	// The current joystick report (report ID first), for the PC's GET_REPORT requests.
	void setReportSource(const uint8_t *report) { currentReport = report; }

	// Non-blocking: return -1 if the endpoint is still busy with the last report.
	int sendJoystick(const uint8_t *report);          // report ID + layout().report_size bytes
	int sendSettings(const uint8_t *packet);          // HSR_PACKET_SIZE bytes, report ID first

	// 1 if a settings packet (HSR_PACKET_SIZE bytes) was read into packet.
	uint8_t readSettings(uint8_t *packet);

protected:
	int getInterface(uint8_t *interfaceCount);
	int getDescriptor(USBSetup &setup);
	bool setup(USBSetup &setup);
	uint8_t getShortName(char *name);

private:
	int joystickDescriptor(uint8_t send);

	uint8_t epType[3];
	JoyLayout joy;
	uint16_t joyDescLength;
	const uint8_t *currentReport;
	uint8_t protocol;
	uint8_t idle;
};

HeliUSB_ &HeliUSB(void);

#endif
