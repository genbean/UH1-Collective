/**
  ******************************************************************************
  * @file           : common_defines.h
  * @brief          : The device limits and USB protocol, taken from the firmware.
  ******************************************************************************
  *
  * The limits come from the firmware's shared headers. FreeJoy's names are kept
  * as aliases so the pages that didn't change still read as they did.
  */

#ifndef __COMMON_DEFINES_H__
#define __COMMON_DEFINES_H__

#include "shared/helisr_config.h"
#include "shared/helisr_protocol.h"

#define MAX_AXIS_NUM                HSR_MAX_AXES
#define MAX_BUTTONS_NUM             HSR_MAX_BUTTONS
#define MAX_POVS_NUM                HSR_MAX_POVS
#define MAX_ENCODERS_NUM            HSR_MAX_ENCODERS
#define MAX_LEDS_NUM                HSR_MAX_LEDS

#endif 	/* __COMMON_DEFINES_H__ */
