# Hand edits to HeliSR Rev 4.0: vias that could bridge to another net's pad, moved or removed.
EDITS = [
    # bare GND stitching vias under parts or beside other nets' pads: out (the pours stay joined elsewhere)
    ("del_via", 17.450, 17.150),   # under C3, between its VCC and GND pads
    ("del_via", 20.750, 16.250),   # under R10, 0.33 from its SCL pad
    ("del_via", 28.050, 32.750),   # 0.44 from SW1's RST pad
    ("del_via", 2.650, 14.150),    # 0.37 from C1's VCC pad
    ("del_via", 11.750, 30.950),   # 0.26 from J2.7 (IN14)
    ("del_via", 26.350, 22.150),   # 0.28 from U3.9 (AX1_SDA)
    ("del_via", 30.450, 19.450),   # under U3, 0.47 from C2's VCC pad
    ("del_via", 25.050, 0.950),    # 0.33 from R6's VCC pad
    ("del_via", 36.050, 25.750),   # under R4/J12, 0.40 from R4's VCC pad
    ("del_via", 38.350, 11.850),   # 0.33 from R8's VCC pad

    # GND via 0.26 from U2.9 (SR_DATA): out, with its two tracks (C4's GND is on the back pour)
    ("del_via", 19.599, 20.007),
    ("del_trk", "GND", "F", 15.010, 20.007, 19.599, 20.007),
    ("del_trk", "GND", "B", 21.371, 20.007, 19.599, 20.007),
    ("del_trk", "GND", "B", 24.825, 16.553, 21.371, 20.007),

    # VCC via 0.29 from J13's GND mounting pad: 0.4 mm down
    ("del_via", 26.352, 2.987),
    ("del_trk", "VCC", "F", 26.087, 2.987, 26.352, 2.987),
    ("del_trk", "VCC", "B", 26.352, 3.395, 26.352, 2.987),
    ("del_trk", "VCC", "B", 25.700, 2.987, 26.352, 2.987),
    ("add_via", "VCC", 26.352, 3.395),
    ("trk", "VCC", "F", 0.3, [(26.087, 2.987), (26.352, 3.252), (26.352, 3.395)]),
    ("trk", "VCC", "B", 0.3, [(25.700, 2.987), (25.944, 2.987), (26.352, 3.395)]),

    # SR_LOAD via 0.22 from U1.2 (SR_CLK): up and right, clear of U1.2 and the GND track
    ("del_via", 5.881, 17.924),
    ("del_trk", "SR_LOAD", "F", 5.255, 18.550, 5.881, 17.924),
    ("del_trk", "SR_LOAD", "F", 5.255, 19.295, 5.255, 18.550),
    ("del_trk", "SR_LOAD", "B", 12.785, 17.924, 5.881, 17.924),
    ("add_via", "SR_LOAD", 5.900, 17.424),
    ("trk", "SR_LOAD", "F", 0.2, [(5.255, 19.295), (5.255, 18.069), (5.900, 17.424)]),
    ("trk", "SR_LOAD", "B", 0.2, [(12.785, 17.924), (6.400, 17.924), (5.900, 17.424)]),

    # AX1_SCL via 0.30 from R1.2 (AX1_SDA): 0.45 up; AX1_SDA's front run above it moves up to 26.5 to make room
    ("del_trk", "AX1_SDA", "F", 26.265, 26.915, 22.450, 26.915),
    ("trk", "AX1_SDA", "F", 0.2, [(26.265, 26.915), (25.850, 26.500), (22.865, 26.500), (22.450, 26.915)]),
    ("del_via", 23.755, 27.598),
    ("del_trk", "AX1_SCL", "F", 23.658, 27.598, 23.755, 27.598),
    ("del_trk", "AX1_SCL", "B", 24.630, 27.598, 23.755, 27.598),
    ("del_trk", "AX1_SCL", "B", 24.630, 27.598, 24.630, 24.139),
    ("add_via", "AX1_SCL", 23.755, 27.150),
    ("trk", "AX1_SCL", "F", 0.2, [(23.658, 27.598), (23.755, 27.501), (23.755, 27.150)]),
    ("trk", "AX1_SCL", "B", 0.2, [(24.630, 27.598), (24.630, 27.150), (24.630, 24.139)]),
    ("trk", "AX1_SCL", "B", 0.2, [(24.630, 27.150), (23.755, 27.150)]),

    # VCC via 0.20 from R2.2 (AX1_SCL): up-left into the gap between R2 and AX1_SDA's front run
    ("del_via", 26.114, 27.706),
    ("del_trk", "VCC", "F", 25.354, 28.467, 26.114, 27.706),
    ("del_trk", "VCC", "B", 26.114, 27.706, 26.157, 27.706),
    ("del_trk", "VCC", "B", 26.157, 27.706, 27.195, 26.669),
    ("del_trk", "VCC", "B", 26.114, 27.706, 26.114, 30.239),
    ("add_via", "VCC", 25.600, 27.150),
    ("trk", "VCC", "F", 0.3, [(25.354, 28.467), (25.600, 28.221), (25.600, 27.150)]),
    ("trk", "VCC", "B", 0.3, [(27.195, 26.669), (26.081, 26.669), (25.600, 27.150), (26.114, 27.664), (26.114, 30.239)]),

    # IN10 via 0.27 from J2.2 (IN9): 0.27 up
    ("del_via", 16.842, 28.267),
    ("del_trk", "IN10", "F", 16.763, 28.267, 16.842, 28.267),
    ("del_trk", "IN10", "B", 18.723, 28.267, 16.842, 28.267),
    ("add_via", "IN10", 16.842, 28.000),
    ("trk", "IN10", "F", 0.2, [(16.763, 28.267), (16.842, 28.188), (16.842, 28.000)]),
    ("trk", "IN10", "B", 0.2, [(18.723, 28.267), (18.456, 28.000), (16.842, 28.000)]),

    # AX4_SCL via by J14 (0.34 from its GND mounting pad, 0.46 from R11's MUX_RST pad): down into the open
    # spot between R11 and the mounting pad, back to R8 round R11's corner
    ("del_via", 36.256, 13.250),
    ("del_trk", "AX4_SCL", "F", 36.256, 13.250, 35.275, 11.900),
    ("del_trk", "AX4_SCL", "B", 36.256, 13.250, 34.237, 11.600),
    ("del_trk", "AX4_SCL", "F", 35.413, 12.037, 35.413, 16.735),
    ("trk", "AX4_SCL", "F", 0.2, [(35.413, 12.037), (35.413, 13.863), (35.413, 16.735)]),
    ("trk", "AX4_SCL", "F", 0.2, [(35.413, 13.863), (36.250, 14.700)]),
    ("add_via", "AX4_SCL", 36.250, 14.700),
    ("trk", "AX4_SCL", "B", 0.2, [(36.250, 14.700), (36.000, 14.450), (36.000, 13.000), (35.300, 12.300), (34.237, 12.300)]),

    # AX4_SCL via by U3 (0.37 from U3.6, AX2_SDA): 0.14 right
    ("del_via", 33.813, 18.334),
    ("del_trk", "AX4_SCL", "F", 35.413, 16.735, 33.813, 18.334),
    ("del_trk", "AX4_SCL", "B", 33.813, 18.334, 33.813, 18.124),
    ("del_trk", "AX4_SCL", "B", 33.813, 18.124, 32.844, 18.124),
    ("add_via", "AX4_SCL", 33.950, 18.334),
    ("trk", "AX4_SCL", "F", 0.2, [(35.413, 16.735), (33.950, 18.198), (33.950, 18.334)]),
    ("trk", "AX4_SCL", "B", 0.2, [(33.950, 18.334), (33.950, 18.124), (32.844, 18.124)]),

    # GND stitching to join the pours again, at spots clear of every SMD courtyard and 0.45 mm from every pad
    ("add_via", "GND", 15.850, 18.750),
    ("add_via", "GND", 32.450, 32.750),
    ("add_via", "GND", 2.650, 13.650),
    ("add_via", "GND", 24.850, 17.550),    # joins the back pour round C4 (it lost the via under R10) to the front GND track

    # SR_LOAD via 0.28 from C3's VCC pad and 0.45 from U1.9: C3 0.3 mm right, the via 0.08 down-right
    ("move", "C3", 17.600, 16.820, 0),
    ("del_via", 14.674, 16.036),
    ("del_trk", "SR_LOAD", "F", 14.949, 15.761, 14.674, 16.036),
    ("del_trk", "SR_LOAD", "B", 14.674, 16.036, 12.785, 17.924),
    ("add_via", "SR_LOAD", 14.720, 16.100),
    ("trk", "SR_LOAD", "F", 0.2, [(14.949, 15.761), (14.720, 15.990), (14.720, 16.100)]),
    ("trk", "SR_LOAD", "B", 0.2, [(14.720, 16.100), (12.896, 17.924), (12.785, 17.924)]),

    # IN10 via 0.20 from U2.12 (IN11): down-right, with IN9's front run to RN2.9 swung out round it
    ("del_via", 24.886, 20.653),
    ("del_trk", "IN10", "F", 25.535, 19.295, 24.886, 19.944),
    ("del_trk", "IN10", "F", 24.886, 19.944, 24.886, 20.653),
    ("del_trk", "IN10", "B", 23.601, 20.653, 24.886, 20.653),
    ("add_via", "IN10", 25.050, 20.950),
    ("trk", "IN10", "F", 0.2, [(25.535, 19.295), (25.535, 20.465), (25.050, 20.950)]),
    ("trk", "IN10", "B", 0.2, [(23.601, 20.653), (24.753, 20.653), (25.050, 20.950)]),
    ("del_trk", "IN9", "F", 26.805, 19.664, 24.649, 21.820),
    ("del_trk", "IN9", "F", 24.649, 21.820, 24.020, 21.820),
    ("trk", "IN9", "F", 0.2, [(26.805, 19.664), (26.805, 20.900), (25.885, 21.820), (24.020, 21.820)]),

    # AX3_SDA via 0.25 from U2.1 (SR_LOAD) and the SR_DATA via beside it: the two swap sides under U2/U3.
    # AX3_SDA drops at x 30.3 (0.55 from U2.1 and C2) to a via 0.75 from C2, then under U3 to pin 11;
    # SR_DATA drops between U2.2 and U2.1 to a via at 29.05,17.35 and leaves U3 between pins 11 and 12.
    # The short GND link from U2.15 to C2 goes (both ends stay on GND by other tracks and the pour).
    ("del_trk", "GND", "F", 28.075, 18.806, 29.348, 17.534),
    ("del_trk", "GND", "F", 29.348, 17.534, 29.978, 17.534),
    ("del_trk", "GND", "F", 29.978, 17.534, 31.850, 15.662),
    ("del_via", 29.675, 15.873),
    ("del_trk", "AX3_SDA", "F", 31.059, 14.287, 29.675, 15.671),
    ("del_trk", "AX3_SDA", "F", 29.675, 15.671, 29.675, 15.873),
    ("del_trk", "AX3_SDA", "B", 29.675, 15.873, 29.036, 16.512),
    ("del_trk", "AX3_SDA", "B", 29.036, 16.512, 29.036, 16.941),
    ("del_trk", "AX3_SDA", "B", 29.036, 16.941, 28.538, 17.439),
    ("del_trk", "AX3_SDA", "B", 28.538, 17.439, 28.501, 17.476),
    ("del_trk", "AX3_SDA", "B", 28.501, 17.476, 28.501, 18.525),
    ("del_trk", "AX3_SDA", "B", 28.501, 18.525, 28.301, 18.725),
    ("del_trk", "AX3_SDA", "B", 28.301, 18.725, 27.225, 18.725),
    ("add_via", "AX3_SDA", 30.300, 16.750),
    ("trk", "AX3_SDA", "F", 0.2, [(31.059, 14.287), (30.300, 15.046), (30.300, 16.750)]),
    ("trk", "AX3_SDA", "B", 0.2, [(30.300, 16.750), (30.300, 18.100), (29.675, 18.725), (27.225, 18.725)]),
    ("del_via", 29.688, 16.832),
    ("del_trk", "SR_DATA", "F", 28.712, 15.856, 29.688, 16.832),
    ("del_trk", "SR_DATA", "B", 29.688, 16.832, 29.688, 17.917),
    ("del_trk", "SR_DATA", "B", 29.688, 17.917, 28.479, 19.126),
    ("del_trk", "SR_DATA", "B", 28.479, 19.126, 28.211, 19.394),
    ("del_trk", "SR_DATA", "B", 28.211, 19.394, 25.043, 19.394),
    ("del_trk", "SR_DATA", "B", 25.043, 19.394, 23.007, 19.394),
    ("add_via", "SR_DATA", 29.050, 17.350),
    ("trk", "SR_DATA", "F", 0.2, [(28.712, 15.856), (28.712, 17.012), (29.050, 17.350)]),
    ("trk", "SR_DATA", "B", 0.2, [(29.050, 17.350), (28.310, 18.090), (25.600, 18.090), (24.296, 19.394), (23.007, 19.394)]),
]
