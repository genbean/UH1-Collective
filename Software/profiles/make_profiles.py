"""Makes the example profiles in this folder from the factory-settings profile.

    python make_profiles.py

The template, "Default (16 buttons, 4 axes).cfg", is the factory settings as
HeliSR Configurator saves them. If the firmware's defaults change, make it
again first with:  HeliSRConfigurator --save-defaults "Default (16 buttons, 4 axes).cfg"

Each example changes only what it needs; every other setting stays at the
factory value. docs/profiles.md describes them.
"""
import configparser
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = "Default (16 buttons, 4 axes).cfg"

# button types (firmware/HeliSR/src/shared/helisr_config.h)
NORMAL, TOGGLE, SWITCH_ON_OFF, SWITCH_ON, SWITCH_OFF = 0, 1, 2, 3, 4
POV1_UP, POV1_RIGHT, POV1_DOWN, POV1_LEFT = 5, 6, 7, 8
ENCODER_A, ENCODER_B = 23, 24
SWITCH_CENTER = 31
# axes: X Y Z Rx Ry Rz Slider1 Slider2
X, Y, Z, RX, RY, RZ = range(6)
# analog sources
AX1, AX2, AX3, AX4 = range(4)


def IN(n):
    """Physical input number of INn."""
    return n - 1


def load():
    c = configparser.RawConfigParser()
    c.optionxform = str                     # keep the keys' case
    c.read(os.path.join(HERE, TEMPLATE), encoding="utf-8")
    return c


def save(c, name):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        c.write(f, space_around_delimiters=False)
    print("wrote", name)


def clear_buttons(c):
    for i in range(64):
        c["ButtonsConfig_%d" % i]["ButtonPhysicNumber"] = "-1"


def button(c, n, phys, kind=NORMAL, shift=0, inverted=0):
    """Logical button n (from 1)."""
    g = c["ButtonsConfig_%d" % (n - 1)]
    g["ButtonPhysicNumber"] = str(phys)
    g["ButtonType"] = str(kind)
    g["ShiftMod"] = str(shift)
    g["Inverted"] = str(inverted)


def axis(c, a, source, enabled=1, filter_level=0):
    g = c["AxesConfig_%d" % a]
    g["SourceMain"] = str(source)
    g["OutEnabled"] = str(enabled)
    g["Filter"] = str(filter_level)


def axis_off(c, a):
    axis(c, a, -1, enabled=0)


# ------------------------------------------------------- the UH-1 collective --
# The Huey head (Head/Rev4, controls as in Head/README.md) on a HeliSR Rev 3.0
# board, the collective's AS5600 on AX1 and the throttle's on AX4. The Rev 4
# throttle runs from an idle stop to full open: no cutoff range.
c = load()
c["DeviceUsbConfig"]["DeviceName"] = "UH-1 Collective"
axis_off(c, X)
axis_off(c, Y)
axis_off(c, RX)
axis(c, Z, AX1, filter_level=1)             # collective
axis(c, RZ, AX4, filter_level=1)            # throttle

clear_buttons(c)
button(c, 1, IN(1))                         # GOV RPM INCR
button(c, 2, IN(2))                         # GOV RPM DECR
button(c, 3, IN(3))                         # LDG LT EXT
button(c, 4, IN(4))                         # LDG LT RETR
button(c, 5, IN(3), SWITCH_CENTER)          # LDG LT EXT/RETR switch at OFF
button(c, 6, IN(5))                         # SL ON
button(c, 7, IN(6))                         # SL STOW
button(c, 8, IN(5), SWITCH_CENTER)          # SL switch at OFF
button(c, 9, IN(7))                         # LDG LT ON
button(c, 10, IN(7), inverted=1)            # LDG LT OFF
button(c, 11, IN(9))                        # SEARCH CONT EXT
button(c, 12, IN(10))                       # SEARCH CONT RETR
button(c, 13, IN(11))                       # SEARCH CONT L
button(c, 14, IN(12))                       # SEARCH CONT R
button(c, 15, IN(13))                       # STOP REL
button(c, 16, IN(14))                       # starter trigger
save(c, "UH-1 collective (HeliSR head).cfg")

# -------------------------------------------------------------- button box --
# A generic panel showing the button types: 3-position switches with their
# centre, pulse outputs for a 2-position switch, a latching button, two
# encoders, a hat and a shift layer. No axes.
c = load()
c["DeviceUsbConfig"]["DeviceName"] = "HeliSR Button Box"
for a in (X, Y, Z, RX):
    axis_off(c, a)

clear_buttons(c)
button(c, 1, IN(1))                         # switch A up
button(c, 2, IN(2))                         # switch A down
button(c, 3, IN(1), SWITCH_CENTER)          # switch A centre
button(c, 4, IN(3))                         # switch B up
button(c, 5, IN(4))                         # switch B down
button(c, 6, IN(3), SWITCH_CENTER)          # switch B centre
button(c, 7, IN(5), SWITCH_ON)              # switch C: a pulse when turned on
button(c, 8, IN(5), SWITCH_OFF)             # switch C: a pulse when turned off
button(c, 9, IN(6), TOGGLE)                 # push button, latching
button(c, 10, IN(7), ENCODER_A)             # encoder 1
button(c, 11, IN(8), ENCODER_B)
button(c, 12, IN(9), ENCODER_A)             # encoder 2
button(c, 13, IN(10), ENCODER_B)
button(c, 14, IN(11), POV1_UP)              # hat
button(c, 15, IN(12), POV1_RIGHT)
button(c, 16, IN(13), POV1_DOWN)
button(c, 17, IN(14), POV1_LEFT)
button(c, 18, IN(15))                       # shift 1
button(c, 19, IN(16))                       # IN16 alone
button(c, 20, IN(16), shift=1)              # IN16 with shift 1 held
c["ShiftConfig"]["Shift0"] = "17"           # logical button 18 is shift 1
for e in (0, 1):
    c["EncodersConfig_%d" % e]["EncType"] = "0"     # 1x: one press per click
save(c, "Button box (switches, encoders, hat).cfg")
