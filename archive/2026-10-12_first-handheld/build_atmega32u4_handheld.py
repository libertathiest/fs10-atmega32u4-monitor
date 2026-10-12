# ATmega32U4 (FS10 power supply and monitor) - handheld enclosure, same
# style as the FCI SAMD51 Universal Controller handheld (build_handheld.py)
#
# Board stands upright (connectors on the bottom end), the grip hugs the
# board's side edges and the head flares out for a 2.42" OLED.  No knob or
# button: the face has only the display window and the LED window.
# Builds and saves ATmega32U4-Handheld.FCStd.  STEP/STL files come from
# export_atmega32u4_handheld.py, run once the design is final.
#
# Adjusting: open ATmega32U4-Handheld.FCStd, edit the "Parameters" spreadsheet
# (column B), then run this macro again (Macro > Macros... > Execute, or a
# toolbar button).  It reads the spreadsheet and rebuilds the parts in place.
# To restore a default, clear its cell in column B and run the macro.
# The values below are only the defaults used to create the spreadsheet.
#
# Frame: board centred at the origin, X across (66 mm), Y up (100 mm),
# Z = 0 at the PCB bottom.  Original KiCad -> here:  X = ky - 100.45,
# Y = kx - 145.2.

import os
import FreeCAD as App
import Part
import Import
from FreeCAD import Vector as V, Rotation as R, Placement as P

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:                     # FreeCAD's Macro menu may not set __file__
    _ad = App.ActiveDocument
    HERE = (os.path.dirname(_ad.FileName) if _ad is not None and _ad.FileName
            else os.path.expanduser("~/Documents/FS10-ATmega32U4/hardware/FreeCAD enclosure"))
App.Console.PrintMessage("ATmega32U4 handheld: rebuilding...\n")
BOARD_STEP = os.path.join(HERE, "FS10-ATmega32U4.step")
# KiCad board 120..178 x 65.8..134.3 -> centred at the origin, already upright
# (USB / DC / power switch on the bottom edge, M12 lead-in CN1 on the top edge)
BOARD_PL = P(V(-149.0, 100.05, 0), R())

# ---------------------------------------------------------------- parameters
WALL, FLOOR, FACE = 2.5, 2.5, 2.5
FACE_FILLET = 2.0                     # round where the front face meets the sides (0 = sharp)
BACK_FILLET = 1.0                     # round where the back meets the sides (0 = sharp)
LOGO_ON = 1                           # FCI logo on the grip side (0 = none)
LOGO_SIDE = 1                         # +1 right side, -1 left side
LOGO_LEN = 46.0                       # logo length (artwork 86.7 x 14.3, from the FS10 enclosure)
LOGO_Y = 4.25                         # logo centre along the grip
LOGO_Z = 15.25                        # logo centre height (front half: parting line to edge round)
LOGO_EMBOSS = 0.4                     # raised height (negative = engraved)
NAME_ON = 1                           # product name on the other grip side (0 = none)
NAME_LINE1, NAME_LINE2 = "FS10", "Power & Monitor"   # text (edit here)
NAME_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
NAME_LEN = 44.0                       # widest line at most this long
NAME_H = 10.0                         # both lines together at most this tall
NAME_RATIO = 0.55                     # line 2 size relative to line 1
NAME_Y = 4.25                         # centre along the grip
NAME_Z = 15.25                        # centre height
NAME_EMBOSS = 0.4                     # raised height (negative = engraved)
STAMP_ON = 1                          # file name + build date/time on the head side (0 = none)
STAMP_SIDE = -1                       # -1 left side of the head, +1 right
STAMP_Y = 71.5                        # centre along the head
STAMP_Z = 15.25                       # centre height
STAMP_LEN = 48.0                      # at most this long
STAMP_H = 3.0                         # at most this tall
STAMP_EMBOSS = 0.3                    # raised height (negative = engraved)
COLOR_MODE = 2                        # 0 keep my colours, 1 standard scheme, 2 random
FIT = 0.3
CORNER_R = 4.0

BOARD_HW, BOARD_HH = 29.0, 34.25     # half width / height of the PCB (58 x 68.5)
EDGE_GAP = 2.5                        # board edge to wall (clears an 18.5 mm encoder module)
CONN_REACH = 52.65                    # USB/DC/rocker fronts, 2.65 past the board edge
BOARD_END_GAP = 0.2                   # board's connector edge to the inside of the bottom wall:
                                      # the connectors then pass through the wall, flush outside

STANDOFF_H = 6.0                      # PCB screw boss height: PCB bottom 6 mm above the floor
# PCB screw bosses printed on the back floor; M3 x 6 self-tappers down through the board
PCB_BOSS_D = 7.0
PCB_PILOT_D = 2.7                     # pilot for an M3 self-tapper in resin (2.5 for FDM)
PCB_SCREW_L = 6.0                     # screw length under the head
FACE_INNER_Z = 22.0                   # PCB bottom to front-face underside
SPLIT_Z = 8.0                         # front / back half parting line

# display (2.42" OLED module) - landscape
# generic 2.42" SSD1309 I2C module ("2.42OLED-IIC VER:1.1"): 70 x 48 board, wired
# 4-pin header on the left edge (seen from the front); 4 more pads at the top centre.
# The glass FPC wraps through a ~23 mm notch in the bottom edge centre; metal frame
# tabs sit ~18-25 mm each side of centre.  Held by the snap clips (corner holes unused).
DISP_W, DISP_H = 70.0, 48.0            # module PCB (measured)
# DISP_GLASS_T = everything on the front of the module PCB: tape ~0.2 + glass 2.11 + frame 0.3
DISP_PCB_T, DISP_GLASS_T = 1.6, 2.6
DISP_AA_W, DISP_AA_H = 55.01, 27.49      # OLED active area
# Panel drawing (Winstar 2.42" 128x64, 60.5 x 37 glass): pixels centred across, but
# 2.2 mm from the glass top edge and 7.31 from the FPC edge -> centre 2.56 above the
# glass centre (FPC at the bottom).  Assumes the glass is centred on the module.
DISP_AA_OFFSET_X = 0.0                # pixels centre vs module centre (across)
DISP_AA_OFFSET_Y = 2.56               # pixels centre vs module centre, toward the case top
DISP_GLASS_L, DISP_GLASS_H = 60.5, 37.0  # OLED glass panel
DISP_GLASS_DX, DISP_GLASS_DY = 0.0, 0.0  # glass centre vs module centre
SCREEN_X = 0.0                        # the visible screen is centred on the case
DISP_Y0 = 49.0                        # bottom edge of the display PCB (top edge clears the M12 jam nut)
WINDOW_MARGIN = 1.0
CLIP_TOP_SHIFT = -12.0                # top-edge snap clip moved sideways, clear of the M12 body
CLIP_BOT_SHIFT = 18.0                 # bottom-edge clip moved sideways, past the FPC notch
# pocket in the face underside for the 4-pin header's solder stubs (front of the module)
# pockets in the face underside for 4-pin header pins on the front of the module:
# one at the wired side header, one at the top-centre pads (in case they get used)
HDR_POCKET_L, HDR_POCKET_W = 12.0, 4.0  # along the pin row x across it
HDR_POCKET_D = 1.5                    # depth into the face
HDR_X = -31.6                         # side header pin row vs module centre, across (- = left, seen from the front)
HDR_Y = 2.6                           # side header centre vs module centre, toward the case top
HDR_TOP_X = 0.0                       # top header centre vs module centre, across
HDR_FROM_TOP = 2.5                    # top header pin row from the module's top edge
WINDOW_BEVEL = 1.0                    # 45-degree bevel around the window (0 = sharp edge)
# 0.5 mm polycarbonate sheet behind the bezel, held by the display
PC_T = 0.5
PC_W, PC_H = 64.0, 40.0               # cut the sheet to this
PC_FIT = 0.2                          # pocket clearance per side

HEAD_HW = 42.0                        # head interior half width
HEAD_TOP = 103.0                      # head interior top
FLARE_Y0, FLARE_Y1 = 30.0, 40.0       # grip -> head transition

# screws: M3 from the back into pilot holes in the front half
BOSS_D, PILOT_D, CLEAR_D, HEAD_D = 7.0, 2.7, 3.4, 6.2   # 2.7 pilot: M3 self-tapper in resin
BOSS_INSET = 3.3                      # head boss centre from the inside wall (< BOSS_D/2: boss merges into the wall)
EAR_Y = -26.0                         # grip ears (bulge out of the wall)
EAR_D = 9.0

# board mounting holes (H1..H4) in this frame
HOLES = [(-25.299, -30.521), (24.662, -30.24), (24.044, 29.277), (-18.5, 29.5)]   # H1..H4

# front-face features
# RESET1 is an angled tactile on the left board edge: paper-clip hole in the left wall
RESET_ON = 1
# RESET1 = KiCad SW_Tactile_SKHH_Angled at (123.625, 116.95, 90 deg): the plunger
# sits midway between pins 1 and 2, 2.25 mm from pin 1 -> Y -14.65 in this frame
RESET_Y = -14.65                      # actuator centre along the grip
RESET_Z = 4.0                         # actuator centre above the board's TOP surface (ALPS SKHHLUA010: 4.0 +-0.2)
RESET_HOLE_D = 2.0
# LED2 (5 mm RGB, hand-soldered): window in the face
LED_ON = 1
LED_X, LED_Y = 0.0, -2.59           # window centred across the face
LED_HOLE_D = 5.4
# Knob and button: this unit has neither.  Switches kept in the script only
# (not in the spreadsheet) in case a later version adds them.
BUTTON_ON = 0                         # SW2 plunger through the face (0 = none)
BUTTON = (21.5, 15.95)                # SW2 12x12, top at Z 10.1
BUTTON_TOP_Z, BUTTON_D = 10.1, 10.0
# EC11 encoder module (cable to J8): mirrors the plunger, same row
ENCODER = (-BUTTON[0], BUTTON[1])
ENC_ON = 0                             # encoder knob mirroring the SW2 plunger (0 = none)
ENCODER_HOLE_D = 8.0
ANTIROT_DX, ANTIROT_DY = 0.0, 7.0     # anti-rotation tab from shaft centre - check your part
ANTIROT_D = 2.2
ENC_BODY = 12.5                        # EC11 body square, behind the face
ENC_BODY_H = 6.5
# KY-040 style module - MEASURE YOURS and enter the numbers in the spreadsheet
ENC_PCB_W = 18.5                       # module PCB across the case (X)
ENC_PCB_L = 26.0                       # module PCB along the case (Y)
ENC_PCB_T = 1.6
ENC_SHAFT_DX = 0.0                     # shaft from PCB centre, across (X)
ENC_SHAFT_DY = -3.5                    # shaft from PCB centre, along (Y); header end is +Y
ENC_PIN_REACH = 8.5                    # right-angle header pins past the PCB edge (+Y)
KNOB_D, KNOB_H = 18.0, 15.0            # encoder knob (reference only, not printed)
KNOB_GAP = 1.5                         # knob skirt above the front face
KNOB_RIBS = 30                         # grip ribs around the knob

AUX_ON, RJ_ON, AMP_ON, BAT_ON = 0, 0, 0, 0   # 3.5 mm jack, RJ12 jack, amplifier, battery holder

# loose modules taped to the back floor of the head, under the display
TAPE_T = 1.0                           # double-sided tape
AMP_L, AMP_W, AMP_H = 47.0, 35.5, 12.4 # TPA3118 PBTL mono board, largest listed size
AMP_X, AMP_Y = 13.0, 72.0              # its centre (clear of the H2 support base)
BAT_L, BAT_W, BAT_H = 24.0, 21.0, 6.0  # BT1: CR2032 holder with leads
BAT_X, BAT_Y = -25.0, 65.0             # its centre

# M12 field connector through the head's top end wall (FS10 plugs in here):
# Mencom MDC-8FR-PG9, front mount, PG9 thread 15.2 mm, 0.75" hex flange outside,
# 5.8 mm jam nut inside.  Hole is split by the parting line.
MDC_HOLE_D = 15.5                      # PG9 panel hole
MDC_X = 0.0                            # across the case (0 = centred)
MDC_Z_OFFSET = 0.0                     # from the parting line (0 = centred on it)
MDC_NUT_AF = 20.0                      # inside jam nut across flats - check yours
MDC_DEPTH_IN = 20.0                    # connector body depth behind the wall (approx.)

# 3.5 mm audio jack in the same end wall, right of the M12 as held face-up:
# Switchcraft 35PRM3 (docs/datasheets): rear mount, M6x0.75 thread only 3.5 mm
# long, 9.5 mm flange inside, 2.0 mm knurled nut outside.  The wall is thinned
# from the inside around the hole so the nut gets full thread.
AUX_HOLE_D = 6.2                       # M6 thread hole
AUX_X = 25.0                           # across (+ = right of the M12 held face-up)
AUX_Z_OFFSET = 0.0                     # from the parting line (0 = centred on it)
AUX_PANEL_T = 1.4                      # wall left at the jack (thread 3.5 - nut 2.0 - 0.1)
AUX_SPOT_D = 10.5                      # inside recess for the 9.5 mm flange

# 6P6C (RJ12) jack with wire leads for the ST51 serial link (FCI cable 025859-01
# uses positions 1, 2, 3, 6).  623K-style jack: the front face passes through the
# wall flush with the outside, the slightly larger body stops against the inside,
# and printed cradles in both halves capture it.  Sizes are GUESSES - measure.
RJ_X = -25.0                           # across (- = left of the M12 held face-up)
RJ_Z_OFFSET = 0.0                      # jack centre from the parting line
RJ_FACE_W, RJ_FACE_H = 13.0, 10.6      # front face through the wall
RJ_BODY_W, RJ_BODY_H = 14.6, 12.0      # body behind the wall
RJ_DEPTH = 16.5                        # body depth behind the wall (wires exit the back)
RJ_FIT = 0.15                          # clearance per side, cutout and cradle
RJ_CRADLE_T = 1.6                      # cradle wall thickness

# board parts shown in highlight colours
HIGHLIGHT = {"USB-B-TH_USB-109C-B-CU": (0.10, 0.45, 1.00),
             "BarrelJack_GCT_DCJ200-10-A": (1.00, 0.55, 0.00),
             "SW-TH_KCD11-BL": (1.00, 0.10, 0.10),
             "Tactal Switch - SMD": (0.10, 0.85, 0.20)}
OPENING_NAMES = {"USB-B-TH_USB-109C-B-CU": "Opening_USB",
                 "BarrelJack_GCT_DCJ200-10-A": "Opening_DC_Jack",
                 "SW-TH_KCD11-BL": "Opening_Power_Switch"}

# opening = the part's outline within DEPTH of the board's bottom edge,
# plus CLEARANCE per side.  The power switch uses its whole front face so a
# thumb can reach the rocker, not just the tip that pokes past the edge.
OPEN_CLR_USB, OPEN_CLR_DC, OPEN_CLR_SWITCH = 0.5, 0.3, 0.3    # clearance per side (connectors sit flush)


def edge_parts():                     # (clearance, depth) per connector
    return {"USB-B-TH_USB-109C-B-CU": (OPEN_CLR_USB, 0.0),
            "BarrelJack_GCT_DCJ200-10-A": (OPEN_CLR_DC, 0.0),
            "SW-TH_KCD11-BL": (OPEN_CLR_SWITCH, 1.3)}


EDGE_PARTS = edge_parts()

# spreadsheet rows: name -> description (values come from the defaults above)
PARAMS = [
    ("WALL", "side wall thickness"), ("FLOOR", "back floor thickness"),
    ("FACE", "front face thickness"), ("FIT", "sliding clearance"),
    ("FACE_FILLET", "round on the front face edge (0 = sharp)"),
    ("BACK_FILLET", "round on the back edge (0 = sharp)"),
    ("COLOR_MODE", "colours on rebuild: 0 keep mine, 1 standard, 2 random"),
    ("LOGO_ON", "FCI logo on the grip side (1 on, 0 off)"),
    ("LOGO_SIDE", "logo side: 1 right, -1 left"),
    ("LOGO_LEN", "logo length"), ("LOGO_Y", "logo centre along the grip"),
    ("LOGO_Z", "logo centre height"), ("LOGO_EMBOSS", "logo raised height (negative = engraved)"),
    ("NAME_ON", "product name on the opposite grip side (1 on, 0 off)"),
    ("NAME_LEN", "name: widest line at most this long"), ("NAME_H", "name: both lines at most this tall"),
    ("NAME_RATIO", "name: line 2 size relative to line 1"),
    ("NAME_Y", "name centre along the grip"), ("NAME_Z", "name centre height"),
    ("NAME_EMBOSS", "name raised height (negative = engraved)"),
    ("STAMP_ON", "build stamp: file name + date/time (1 on, 0 off)"),
    ("STAMP_SIDE", "build stamp side of the head: -1 left, 1 right"),
    ("STAMP_Y", "build stamp centre along the head"), ("STAMP_Z", "build stamp centre height"),
    ("STAMP_LEN", "build stamp at most this long"), ("STAMP_H", "build stamp at most this tall"),
    ("STAMP_EMBOSS", "build stamp raised height (negative = engraved)"),
    ("CORNER_R", "outside corner radius"), ("EDGE_GAP", "board edge to wall (sides)"),
    ("BOARD_END_GAP", "board connector edge to bottom wall (connectors go through the wall)"),
    ("STANDOFF_H", "PCB screw boss height: PCB bottom above the floor"),
    ("PCB_BOSS_D", "PCB screw boss diameter"), ("PCB_PILOT_D", "PCB screw pilot hole (M3 self-tapper)"),
    ("PCB_SCREW_L", "PCB screw length (sets the pilot depth)"),
    ("FACE_INNER_Z", "PCB bottom to underside of the front face"),
    ("SPLIT_Z", "front/back parting line above PCB bottom"),
    ("DISP_W", "display module width"), ("DISP_H", "display module height"),
    ("DISP_PCB_T", "display PCB thickness"), ("DISP_GLASS_T", "display glass stack"),
    ("DISP_AA_W", "visible screen width"), ("DISP_AA_H", "visible screen height"),
    ("DISP_AA_OFFSET_X", "screen centre vs module centre, away from header"),
    ("DISP_AA_OFFSET_Y", "screen centre vs module centre, toward case top"),
    ("DISP_GLASS_L", "display glass length (across)"), ("DISP_GLASS_H", "display glass height"),
    ("DISP_GLASS_DX", "glass centre vs module centre, across"),
    ("DISP_GLASS_DY", "glass centre vs module centre, toward case top"),
    ("SCREEN_X", "screen centre across the case (0 = centred)"),
    ("DISP_Y0", "display module bottom edge"), ("WINDOW_MARGIN", "window larger than screen, per side"),
    ("WINDOW_BEVEL", "45-degree bevel around the window (0 = sharp)"),
    ("CLIP_TOP_SHIFT", "display top-edge clip moved sideways (clear of the M12)"),
    ("CLIP_BOT_SHIFT", "display bottom-edge clip moved sideways (past the FPC notch)"),
    ("HDR_POCKET_L", "display header pocket length (along the pins)"),
    ("HDR_POCKET_W", "display header pocket width"), ("HDR_POCKET_D", "display header pocket depth into the face"),
    ("HDR_X", "side header pin row vs module centre, across (- = left, from the front)"),
    ("HDR_Y", "side header centre vs module centre, toward the case top"),
    ("HDR_TOP_X", "top header centre vs module centre, across"),
    ("HDR_FROM_TOP", "top header pin row from the module top edge"),
    ("PC_T", "polycarbonate sheet thickness"), ("PC_W", "polycarbonate sheet width"),
    ("PC_H", "polycarbonate sheet height"), ("PC_FIT", "sheet pocket clearance"),
    ("HEAD_HW", "head inside half-width"), ("HEAD_TOP", "head inside top"),
    ("FLARE_Y0", "grip starts to flare"), ("FLARE_Y1", "flare reaches head width"),
    ("BOSS_D", "screw boss diameter"), ("PILOT_D", "screw pilot hole (front half)"),
    ("CLEAR_D", "screw clearance hole (back half)"), ("HEAD_D", "screw head counterbore"),
    ("BOSS_INSET", "head boss centre from inside wall"), ("EAR_Y", "grip ear height"),
    ("EAR_D", "grip ear diameter"),
    ("RESET_ON", "reset pinhole in the left wall (1 on, 0 off)"),
    ("RESET_Y", "reset pinhole along the grip"), ("RESET_Z", "reset pinhole height above the board's top surface"),
    ("RESET_HOLE_D", "reset pinhole diameter"),
    ("LED_ON", "LED window in the face (1 on, 0 off)"), ("LED_HOLE_D", "LED window diameter"),
    ("LED_X", "LED window across (smaller = further left, seen from the front)"),
    ("LED_Y", "LED window along the case (larger = toward the display)"),
    ("TAPE_T", "double-sided tape under the loose modules"),
    ("AMP_L", "TPA3118 module size across"), ("AMP_W", "TPA3118 module size along the case"),
    ("AMP_H", "TPA3118 module height incl. caps / terminals"),
    ("AMP_X", "TPA3118 module centre across"), ("AMP_Y", "TPA3118 module centre along"),
    ("BAT_L", "BT1 battery holder size across"), ("BAT_W", "BT1 battery holder size along"),
    ("BAT_H", "BT1 battery holder height"),
    ("BAT_X", "BT1 battery holder centre across"), ("BAT_Y", "BT1 battery holder centre along"),
    ("OPEN_CLR_USB", "USB opening: clearance per side around the socket face"),
    ("OPEN_CLR_DC", "DC jack opening: clearance per side"),
    ("OPEN_CLR_SWITCH", "power switch opening: clearance per side around its face"),
    ("MDC_HOLE_D", "M12 connector (PG9) hole in the head's top end"),
    ("MDC_X", "M12 connector position across (0 = centred)"),
    ("MDC_Z_OFFSET", "M12 connector height from the parting line (0 = on it)"),
    ("MDC_NUT_AF", "M12 connector jam nut across flats (inside)"),
    ("MDC_DEPTH_IN", "M12 connector body depth behind the wall"),
    ("AUX_HOLE_D", "3.5 mm jack bushing hole"),
    ("AUX_X", "3.5 mm jack position across (+ = right held face-up)"),
    ("AUX_Z_OFFSET", "3.5 mm jack height from the parting line (0 = on it)"),
    ("AUX_PANEL_T", "wall thickness left at the 3.5 mm jack (max 1.5 for 35PRM3)"),
    ("AUX_SPOT_D", "inside recess diameter for the jack flange"),
    ("RJ_X", "RJ12 jack position across (- = left held face-up)"),
    ("RJ_Z_OFFSET", "RJ12 jack centre from the parting line"),
    ("RJ_FACE_W", "RJ12 jack front face width (through the wall)"),
    ("RJ_FACE_H", "RJ12 jack front face height"),
    ("RJ_BODY_W", "RJ12 jack body width behind the wall"),
    ("RJ_BODY_H", "RJ12 jack body height behind the wall"),
    ("RJ_DEPTH", "RJ12 jack body depth behind the wall"),
    ("RJ_FIT", "RJ12 clearance per side (cutout and cradle)"),
    ("RJ_CRADLE_T", "RJ12 cradle wall thickness"),
]

# ---------------------------------------------------------------- document
OUT_FCSTD = os.path.join(HERE, "ATmega32U4-Handheld.FCStd")
doc = App.ActiveDocument
if doc is None or doc.getObject("Back_Shell") is None:
    doc = App.openDocument(OUT_FCSTD) if os.path.exists(OUT_FCSTD) else App.newDocument("ATmega32U4_Handheld")

board_obj = doc.getObject("Board_Solid")
tree = [o for o in doc.RootObjects if o.TypeId == "App::Part"]
if board_obj is None and not tree:
    if App.GuiUp:
        import ImportGui              # keeps the STEP colours
        ImportGui.insert(BOARD_STEP, doc.Name)
    else:
        Import.insert(BOARD_STEP, doc.Name)
    tree = [o for o in doc.RootObjects if o.TypeId == "App::Part"]

sheet = doc.getObject("Parameters")
if sheet is None:
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.set("A1", "Parameter"); sheet.set("B1", "Value (mm)"); sheet.set("C1", "What it sets")
    sheet.setStyle("A1:C1", "bold")
    sheet.setColumnWidth("A", 160); sheet.setColumnWidth("C", 320)
sheet.recompute()                     # pick up cells edited since the last recompute
g = globals()
rows = {}
for r in range(2, 400):
    name = sheet.getContents(f"A{r}").lstrip("'")   # text cells come back as 'NAME
    if not name:
        continue
    if name in rows:                 # duplicate row from an older script: drop it
        for col in "ABC":
            sheet.clear(f"{col}{r}")
    else:
        rows[name] = r
OBSOLETE = ("AUX_NUT_AF", "AUX_BODY_W", "AUX_BODY_H", "AUX_DEPTH_IN",
            "KEY_X", "KEY_Z_OFFSET", "KEY_CUT_W", "KEY_CUT_H", "KEY_PANEL_T", "KEY_DEPTH",
            # no knob or button on this unit
            "BUTTON_D", "ENC_ON", "ENCODER_HOLE_D", "ANTIROT_DX", "ANTIROT_DY", "ANTIROT_D",
            "ENC_PCB_W", "ENC_PCB_L", "ENC_SHAFT_DX", "ENC_SHAFT_DY", "ENC_PIN_REACH",
            "KNOB_D", "KNOB_H", "KNOB_GAP", "KNOB_RIBS",
            # plastic standoffs replaced by printed PCB screw bosses
            "STANDOFF_HOLE_D", "SO_BASE_W", "SO_POCKET_DEPTH", "SO_POCKET_FIT")
for name in OBSOLETE:                 # rows from an older version of this script
    if name in rows:
        r = rows.pop(name)
        for col in "ABC":
            sheet.clear(f"{col}{r}")
CHANGED = {"DISP_W": ((72.0, 63.0), 70.0), "DISP_H": ((43.0, 42.4), 48.0), "PC_W": ((62.0,), 64.0),
           "CLIP_TOP_SHIFT": ((-15.0,), -12.0), "CLIP_BOT_SHIFT": ((12.0,), 18.0),
           "HDR_X": ((0.0,), -31.6), "DISP_GLASS_T": ((2.3,), 2.6), "DISP_AA_OFFSET_Y": ((0.0,), 2.56),
           "DISP_Y0": ((50.0,), 49.0),
           "RESET_Y": ((-16.9,), -14.65), "RESET_Z": ((3.4, 5.6), 4.0),
           "PILOT_D": ((2.5,), 2.7), "PCB_PILOT_D": ((2.5,), 2.7),
           "BOSS_INSET": ((3.5,), 3.3)}   # earlier defaults -> new (measured 70 x 48 OLED)
for name, (olds, new) in CHANGED.items():
    if name in rows:
        try:
            if any(abs(float(sheet.getContents(f"B{rows[name]}")) - old) < 1e-6 for old in olds):
                sheet.set(f"B{rows[name]}", str(new))
        except ValueError:
            pass
sheet.recompute()
next_row = max(rows.values(), default=1) + 1
for name, desc in PARAMS:
    if name in rows and sheet.getContents(f"B{rows[name]}").strip():   # read the user's value
        r = rows[name]
        v = sheet.get(f"B{r}")
        g[name] = float(getattr(v, "Value", v))
    elif name in rows:               # cell cleared: put the default back
        sheet.set(f"B{rows[name]}", str(g[name]))
    else:                            # new row with the default
        r = next_row; next_row += 1
        sheet.set(f"A{r}", name); sheet.set(f"B{r}", str(g[name])); sheet.set(f"C{r}", desc)
doc.recompute()

# derived values
EDGE_PARTS = edge_parts()             # with the spreadsheet's clearances
HEAD_BOSSES = [(sx * (HEAD_HW - BOSS_INSET), y) for y in (FLARE_Y1 + 4.0, HEAD_TOP - BOSS_INSET)
               for sx in (-1, 1)]
# ears sit outside the wall but never reach the PCB edge (+0.5 mm)
ear_x = max(BOARD_HW + EDGE_GAP + 3.5, BOARD_HW + 0.5 + EAR_D / 2)
EAR_BOSSES = [(sx * ear_x, EAR_Y) for sx in (-1, 1)]
ENCODER = (-BUTTON[0], BUTTON[1])
ANTIROT_OFFSET = (ANTIROT_DX, ANTIROT_DY)
Z_IN_BOT = -STANDOFF_H
Z_OUT_BOT = Z_IN_BOT - FLOOR
Z_IN_TOP = FACE_INNER_Z
Z_OUT_TOP = Z_IN_TOP + FACE


def box(x0, y0, z0, x1, y1, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(x, y, z0, z1, d):
    return Part.makeCylinder(d / 2, z1 - z0, V(x, y, z0))


def ycyl(x, z, y0, y1, d):
    """Cylinder along Y (through the head's top end wall)."""
    return Part.makeCylinder(d / 2, y1 - y0, V(x, y0, z), V(0, 1, 0))


def yhex(x, z, af, y0, y1):
    """Hex prism along Y, af = across flats."""
    import math
    rc = af / math.sqrt(3)
    pts = [V(x + rc * math.cos(math.radians(a)), y0, z + rc * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, y1 - y0, 0))


def prism(face, z0, z1):
    f = face.copy(); f.translate(V(0, 0, z0))
    return f.extrude(V(0, 0, z1 - z0))


# ---------------------------------------------------------------- outline
gx = BOARD_HW + EDGE_GAP
gy0 = -(BOARD_HH + BOARD_END_GAP)
pts = [(-gx, gy0), (gx, gy0), (gx, FLARE_Y0), (HEAD_HW, FLARE_Y1), (HEAD_HW, HEAD_TOP),
       (-HEAD_HW, HEAD_TOP), (-HEAD_HW, FLARE_Y1), (-gx, FLARE_Y0), (-gx, gy0)]
inner_face = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in pts]))
r_in = CORNER_R - WALL
inner_face = inner_face.makeOffset2D(-r_in, join=0).makeOffset2D(r_in, join=0)
outer_face = inner_face.makeOffset2D(WALL, join=0)

# ---------------------------------------------------------------- board
def flatten(top):
    """One compound of every component, in place, with per-face colours."""
    shapes, mats = [], ([] if App.GuiUp else None)
    for o in top.OutListRecursive:
        if o.TypeId != "Part::Feature" or o.Shape.isNull():
            continue
        sh = o.Shape.copy()
        sh.Placement = o.getGlobalPlacement()
        shapes.append(sh)
        if mats is None:
            continue
        try:                          # colours are a nicety; never fail the build over them
            nf = len(sh.Faces)
            parent = o.getParentGeoFeatureGroup()
            hl = [c for pre, c in HIGHLIGHT.items() if parent is not None and parent.Label.startswith(pre)]
            if hl:
                mats += [App.Material(DiffuseColor=hl[0])] * nf
            else:
                ma = list(o.ViewObject.ShapeAppearance)
                mats += ma if len(ma) == nf else [ma[0]] * nf
        except Exception as e:
            App.Console.PrintWarning(f"board colours skipped: {e}\n")
            mats = None
    return Part.makeCompound(shapes), (mats or [])


def measure_openings():
    """Edge-connector openings, measured from the board STEP in a hidden scratch
    document so the result never depends on the state of this file."""
    tmp = App.newDocument("zz_fci_openings", hidden=True)
    try:
        Import.insert(BOARD_STEP, tmp.Name)
        found = []
        for prefix, (clr, depth) in EDGE_PARTS.items():
            for o in tmp.Objects:
                if o.TypeId != "App::Part" or not o.Label.startswith(prefix):
                    continue
                osh = Part.getShape(o).transformGeometry(BOARD_PL.toMatrix())   # final frame
                edge = -BOARD_HH
                if not osh.BoundBox.YMin < edge < osh.BoundBox.YMax:   # the placed instance
                    continue
                p = [q for q in osh.tessellate(0.1)[0] if q.y < edge + depth]
                x0, x1 = min(q.x for q in p) - clr, max(q.x for q in p) + clr
                z0, z1 = min(q.z for q in p) - clr, max(q.z for q in p) + clr
                found.append((prefix, Part.makeBox(x1 - x0, 20, z1 - z0, V(x0, edge - 20, z0))))
                break
        return found
    finally:
        App.closeDocument(tmp.Name)
        App.setActiveDocument(doc.Name)


if tree:
    # first run after an import: replace the component tree with one Board solid
    board_top = tree[0]
    board_top.Placement = BOARD_PL
    doc.recompute()
    board_shape, board_mats = flatten(board_top)
    names = [o.Name for o in board_top.OutListRecursive] + [board_top.Name]
    for n in reversed(names):         # removing a container can take its children with it
        if doc.getObject(n) is not None:
            try:
                doc.removeObject(n)
            except Exception:
                pass
    board_obj = doc.getObject("Board_Solid") or doc.addObject("Part::Feature", "Board_Solid")
    board_obj.Label = "Board"
    board_obj.Shape = board_shape
    if App.GuiUp and board_mats:
        try:
            board_obj.ViewObject.ShapeAppearance = board_mats
        except Exception as e:
            App.Console.PrintWarning(f"board colours skipped: {e}\n")
    doc.recompute()

# openings: reuse the stored ones, measure again if any are missing or their
# (clearance, depth) setting has changed
def _spec(pre):
    return repr(EDGE_PARTS[pre])


def _stored(pre):
    oo = doc.getObject(OPENING_NAMES[pre])
    ok = oo is not None and not oo.Shape.isNull() and getattr(oo, "Spec", "") == _spec(pre)
    return oo.Shape if ok else None


cutters = [(pre, _stored(pre)) for pre in OPENING_NAMES if _stored(pre) is not None]
if len(cutters) < len(OPENING_NAMES):
    cutters = measure_openings()
    grp = doc.getObject("Openings") or doc.addObject("App::DocumentObjectGroup", "Openings")
    for prefix, c in cutters:
        oo = doc.getObject(OPENING_NAMES[prefix]) or doc.addObject("Part::Feature", OPENING_NAMES[prefix])
        oo.Shape = c
        if "Spec" not in oo.PropertiesList:
            oo.addProperty("App::PropertyString", "Spec", "Opening", "clearance, depth used to measure it")
        oo.Spec = _spec(prefix)
        grp.addObject(oo)
        if App.GuiUp:
            oo.Visibility = False
    doc.recompute()
if len(cutters) < len(OPENING_NAMES):
    msg = (f"WARNING: only {len(cutters)} of {len(OPENING_NAMES)} connector openings found - "
           "the case will be missing holes\n")
    print(msg, end="")
    App.Console.PrintError(msg)
board_shape = board_obj.Shape

# ---------------------------------------------------------------- shell
def round_edges_at(solid, z, r):
    """Fillet the outer edges lying in the plane z (front face or back)."""
    edges = [e for e in solid.Edges
             if e.BoundBox.ZLength < 1e-6 and abs(e.BoundBox.ZMax - z) < 1e-6]
    return solid.makeFillet(r, edges)


def rounded_outer(with_ears):
    o = prism(outer_face, Z_OUT_BOT, Z_OUT_TOP)
    if with_ears:
        for x, y in EAR_BOSSES:
            o = o.fuse(cyl(x, y, Z_OUT_BOT, Z_OUT_TOP, EAR_D))
        o = o.removeSplitter()
    if BACK_FILLET > 0:              # never round through the floor or wall
        o = round_edges_at(o, Z_OUT_BOT, min(BACK_FILLET, FLOOR - 0.3, WALL - 0.3))
    if FACE_FILLET > 0:              # never round through the face or wall
        o = round_edges_at(o, Z_OUT_TOP, min(FACE_FILLET, FACE - 0.3, WALL - 0.3))
    return o


def rounded_ear(x, y):
    """An ear cylinder with its own top / bottom rounds (used by the fallback)."""
    c = cyl(x, y, Z_OUT_BOT, Z_OUT_TOP, EAR_D)
    for z, r in ((Z_OUT_BOT, min(BACK_FILLET, FLOOR - 0.3, WALL - 0.3)),
                 (Z_OUT_TOP, min(FACE_FILLET, FACE - 0.3, WALL - 0.3))):
        if r > 0:
            c = round_edges_at(c, z, r)
    return c


try:
    outer = rounded_outer(with_ears=True)
    if not outer.isValid():           # rounding into the ear/wall corner can go bad
        raise ValueError("invalid geometry at the ear/wall corner")
except Exception:                     # fall back: round the outline and each ear separately
    outer = rounded_outer(with_ears=False)
    for x, y in EAR_BOSSES:
        outer = outer.fuse(rounded_ear(x, y))
    outer = outer.removeSplitter()
shell = outer.cut(prism(inner_face, Z_IN_BOT, Z_IN_TOP))
for x, y in EAR_BOSSES:                # inner half of each ear is the screw boss
    shell = shell.fuse(cyl(x, y, Z_IN_BOT, Z_IN_TOP, EAR_D))   # floor below is already solid
for x, y in HEAD_BOSSES:
    shell = shell.fuse(cyl(x, y, Z_OUT_BOT, Z_OUT_TOP, BOSS_D))
for name, c in cutters:
    shell = shell.cut(c)
# M12 field connector hole, split by the parting line
mdc_z = SPLIT_Z + MDC_Z_OFFSET
y_wall_in, y_wall_out = HEAD_TOP, HEAD_TOP + WALL
shell = shell.cut(ycyl(MDC_X, mdc_z, y_wall_in - 1, y_wall_out + 1, MDC_HOLE_D))
# 3.5 mm audio jack hole, also split by the parting line
aux_z = SPLIT_Z + AUX_Z_OFFSET
if AUX_ON:
    shell = shell.cut(ycyl(AUX_X, aux_z, y_wall_in - 1, y_wall_out + 1, AUX_HOLE_D))
# RJ12 jack: cutout the size of its front face (no gap), split by the parting line
rj_z = SPLIT_Z + RJ_Z_OFFSET
if RJ_ON:
    shell = shell.cut(box(RJ_X - RJ_FACE_W / 2 - RJ_FIT, y_wall_in - 1, rj_z - RJ_FACE_H / 2 - RJ_FIT,
                          RJ_X + RJ_FACE_W / 2 + RJ_FIT, y_wall_out + 1, rj_z + RJ_FACE_H / 2 + RJ_FIT))
# main board top surface (the STEP's board body is 1.51 thick, bottom at Z 0)
PCB_TOP = max((x for x in board_shape.Solids if abs(x.BoundBox.ZLength - 1.55) < 0.15),
              key=lambda x: x.Volume).BoundBox.ZMax
reset_z = PCB_TOP + RESET_Z
if RESET_ON:                           # paper-clip hole through the left wall at RESET1
    shell = shell.cut(Part.makeCylinder(RESET_HOLE_D / 2, WALL + 6, V(-(gx + WALL + 3), RESET_Y, reset_z), V(1, 0, 0)))
aux_seat = y_wall_in + max(0.0, WALL - AUX_PANEL_T)        # where the flange sits
if AUX_ON and aux_seat > y_wall_in:
    shell = shell.cut(ycyl(AUX_X, aux_z, y_wall_in - 1, aux_seat, AUX_SPOT_D))

back = shell.common(box(-200, -200, Z_OUT_BOT - 1, 200, 200, SPLIT_Z))
front = shell.common(box(-200, -200, SPLIT_Z, 200, 200, Z_OUT_TOP + 1))

# screws: clearance + counterbore in the back, pilot in the front
for x, y in HEAD_BOSSES + EAR_BOSSES:
    back = back.cut(cyl(x, y, Z_OUT_BOT - 1, SPLIT_Z + 1, CLEAR_D))
    back = back.cut(cyl(x, y, Z_OUT_BOT - 1, Z_OUT_BOT + 3.0, HEAD_D))
    front = front.cut(cyl(x, y, SPLIT_Z - 1, Z_IN_TOP - 1.0, PILOT_D))

# PCB screw bosses on the back floor, pilot holes for M3 x PCB_SCREW_L self-tappers
pilot_depth = min(PCB_SCREW_L - 1.6 + 1.0, STANDOFF_H + FLOOR - 0.8)   # 1 mm spare below the tip
cavity = prism(inner_face, Z_IN_BOT - 1, 0.0)
for i, (x, y) in enumerate(HOLES):
    bs = cyl(x, y, Z_IN_BOT - 0.5, 0.0, PCB_BOSS_D)
    if bs.cut(cavity).Volume > 0.01:
        msg = f"WARNING: PCB boss at H{i + 1} runs into the wall - check PCB_BOSS_D\n"
        print(msg, end=""); App.Console.PrintWarning(msg)
    back = back.fuse(bs.common(cavity))
    back = back.cut(cyl(x, y, -pilot_depth, 0.5, PCB_PILOT_D))
if PCB_SCREW_L - 1.6 > pilot_depth - 0.3:
    msg = f"WARNING: PCB_SCREW_L {PCB_SCREW_L} bottoms out - boss + floor too short\n"
    print(msg, end=""); App.Console.PrintWarning(msg)

# locating lip on the front half
LIP_T, LIP_H = 1.2, 3.0
lip_o = inner_face.makeOffset2D(-FIT, join=0)
lip_i = inner_face.makeOffset2D(-FIT - LIP_T, join=0)
lip = prism(lip_o, SPLIT_Z - LIP_H, SPLIT_Z + 0.01).cut(prism(lip_i, SPLIT_Z - LIP_H - 1, SPLIT_Z + 1))
# the lip sits FIT inside the wall, so tie it to the wall with a stepped 45-degree
# ledge (prints without support with the front half face-down)
ledge_w = FIT + LIP_T
for k in range(3):
    w = ledge_w * (3 - k) / 3
    z0 = SPLIT_Z + k * ledge_w / 3
    lip = lip.fuse(prism(inner_face, z0, z0 + ledge_w / 3 + 0.01)
                   .cut(prism(inner_face.makeOffset2D(-w, join=0), z0 - 1, z0 + ledge_w)))
z_notch = SPLIT_Z + ledge_w + 1
for x, y in HEAD_BOSSES:               # clear lip AND ledge, or the boss corner seals into a void
    lip = lip.cut(cyl(x, y, SPLIT_Z - LIP_H - 1, z_notch, BOSS_D + 2))
for x, y in EAR_BOSSES:               # the ears bulge ~1 mm inside the wall
    lip = lip.cut(cyl(x, y, SPLIT_Z - LIP_H - 1, SPLIT_Z, EAR_D + 2 * FIT))
for name, c in cutters:
    bb = c.BoundBox
    lip = lip.cut(box(bb.XMin - 1, bb.YMin, SPLIT_Z - LIP_H - 1, bb.XMax + 1, bb.YMax + 6, z_notch))
# clear the lip where the connector's jam nut sits on the wall
lip = lip.cut(ycyl(MDC_X, mdc_z, y_wall_in - 8, y_wall_in + 1, MDC_NUT_AF * 2 / 3 ** 0.5 + 2))
if AUX_ON:
    lip = lip.cut(ycyl(AUX_X, aux_z, y_wall_in - 8, y_wall_in + 1, AUX_SPOT_D + 2))
if RJ_ON:
    lip = lip.cut(box(RJ_X - RJ_BODY_W / 2 - RJ_CRADLE_T - 1, y_wall_in - 8, rj_z - RJ_BODY_H / 2 - RJ_CRADLE_T - 1,
                      RJ_X + RJ_BODY_W / 2 + RJ_CRADLE_T + 1, y_wall_in + 1, rj_z + RJ_BODY_H / 2 + RJ_CRADLE_T + 1))
if RESET_ON:                          # gap in the lip so the paper clip reaches RESET1
    lip = lip.cut(box(-(gx + WALL + 5), RESET_Y - RESET_HOLE_D / 2 - 1.5, SPLIT_Z - LIP_H - 1,
                      -(gx - 5), RESET_Y + RESET_HOLE_D / 2 + 1.5, SPLIT_Z + 0.5))
front = front.fuse(lip)

# RJ12 cradles.  Back half: pedestal + side walls + two rear stops (gap between
# them for the wires).  Front half: clamp block from the face down onto the
# jack, kept to the strip behind the display (y >= display edge + rails).
bw, bh = RJ_BODY_W / 2 + RJ_FIT, RJ_BODY_H / 2 + RJ_FIT
ct = RJ_CRADLE_T
y_rj_back = y_wall_in - RJ_DEPTH - RJ_FIT
pocket = box(RJ_X - bw, y_rj_back, rj_z - bh, RJ_X + bw, y_wall_in + 0.01, rj_z + bh)
cr_back = box(RJ_X - bw - ct, y_rj_back - ct, Z_IN_BOT - 0.01, RJ_X + bw + ct, y_wall_in + 0.01, SPLIT_Z)
cr_back = cr_back.cut(pocket)
cr_back = cr_back.cut(box(RJ_X - bw + 3.0, y_rj_back - ct - 1, rj_z - bh + 2.0,   # wire exit between the stops
                          RJ_X + bw - 3.0, y_rj_back + 0.01, SPLIT_Z + 1))
if RJ_ON:
    back = back.fuse(cr_back)
y_front_cr = max(y_rj_back - ct, DISP_Y0 + DISP_H + FIT + 1.6 + 1.0)   # clear the display + rails
if RJ_ON and y_front_cr < y_wall_in - 2.0:
    cr_front = box(RJ_X - bw - ct, y_front_cr, SPLIT_Z, RJ_X + bw + ct, y_wall_in + 0.01, Z_IN_TOP + 0.01)
    front = front.fuse(cr_front.cut(pocket))

# display window + pocket rails + snap clips
dcx = SCREEN_X - DISP_AA_OFFSET_X       # module centre so the screen lands on SCREEN_X
dx0, dx1 = dcx - DISP_W / 2, dcx + DISP_W / 2
dy0, dy1 = DISP_Y0, DISP_Y0 + DISP_H
stack = DISP_PCB_T + DISP_GLASS_T
aa_cx, aa_cy = SCREEN_X, (dy0 + dy1) / 2 + DISP_AA_OFFSET_Y
ww, wh = DISP_AA_W + 2 * WINDOW_MARGIN, DISP_AA_H + 2 * WINDOW_MARGIN
window = box(aa_cx - ww / 2, aa_cy - wh / 2, Z_IN_TOP - 1, aa_cx + ww / 2, aa_cy + wh / 2, Z_OUT_TOP + 1)
# 45-degree bevel from the face down to the opening (keeps >= 0.5 mm of
# straight edge above the polycarbonate pocket)
bev = max(0.0, min(WINDOW_BEVEL, FACE - PC_T - 0.1 - 0.5))
if bev > 0:
    def _rect(z, grow):
        x0, x1 = aa_cx - ww / 2 - grow, aa_cx + ww / 2 + grow
        y0, y1 = aa_cy - wh / 2 - grow, aa_cy + wh / 2 + grow
        return Part.makePolygon([V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z), V(x0, y0, z)])
    e = 0.5                           # run the cut a little past the face
    window = window.fuse(Part.makeLoft([_rect(Z_OUT_TOP - bev, 0.0), _rect(Z_OUT_TOP + e, bev + e)], True, True))
RAIL_T, CL = 1.6, 10.0
zr = Z_IN_TOP - stack - 0.2
rails = []
for cx, sx in ((dx0, -1), (dx1, 1)):
    for cy, sy in ((dy0, -1), (dy1, 1)):
        ox, oy = cx + sx * FIT, cy + sy * FIT
        rails.append(box(ox, oy, zr, ox + sx * RAIL_T, oy - sy * CL, Z_IN_TOP))
        rails.append(box(ox, oy, zr, ox - sx * CL, oy + sy * RAIL_T, Z_IN_TOP))
        rails.append(box(ox, oy, zr, ox + sx * RAIL_T, oy + sy * RAIL_T, Z_IN_TOP))   # fill the corner
CW, CT, LIPC = 10.0, 1.4, 0.9
for cy, sy, shift in ((dy0, -1, CLIP_BOT_SHIFT), (dy1, 1, CLIP_TOP_SHIFT)):   # off the FPC / the M12
    oy = cy + sy * FIT
    cx_ = dcx + shift
    rails.append(box(cx_ - CW / 2, oy, Z_IN_TOP - stack - 2.0, cx_ + CW / 2, oy + sy * CT, Z_IN_TOP))
    rails.append(box(cx_ - CW / 2, oy, Z_IN_TOP - stack - 1.2, cx_ + CW / 2, oy - sy * LIPC, zr))
for r in rails:
    front = front.fuse(r)
front = front.cut(window)
pc_pocket = box(aa_cx - PC_W / 2 - PC_FIT, aa_cy - PC_H / 2 - PC_FIT, Z_IN_TOP - 0.01,
                aa_cx + PC_W / 2 + PC_FIT, aa_cy + PC_H / 2 + PC_FIT, Z_IN_TOP + PC_T + 0.1)
front = front.cut(pc_pocket)
hx, hy = dcx + HDR_X, (dy0 + dy1) / 2 + HDR_Y   # side header pins: shallow pocket in the face
front = front.cut(box(hx - HDR_POCKET_W / 2, hy - HDR_POCKET_L / 2, Z_IN_TOP - 1,
                      hx + HDR_POCKET_W / 2, hy + HDR_POCKET_L / 2, Z_IN_TOP + HDR_POCKET_D))
hx, hy = dcx + HDR_TOP_X, dy1 - HDR_FROM_TOP     # top-centre pads: same pocket, along the edge
front = front.cut(box(hx - HDR_POCKET_L / 2, hy - HDR_POCKET_W / 2, Z_IN_TOP - 1,
                      hx + HDR_POCKET_L / 2, hy + HDR_POCKET_W / 2, Z_IN_TOP + HDR_POCKET_D))
pc_sheet = box(aa_cx - PC_W / 2, aa_cy - PC_H / 2, Z_IN_TOP, aa_cx + PC_W / 2, aa_cy + PC_H / 2, Z_IN_TOP + PC_T)

# other front-face holes
if LED_ON:
    front = front.cut(cyl(LED_X, LED_Y, Z_IN_TOP - 3, Z_OUT_TOP + 1, LED_HOLE_D))
if ENC_ON:
    front = front.cut(cyl(*ENCODER, Z_IN_TOP - 3, Z_OUT_TOP + 1, ENCODER_HOLE_D))
    front = front.cut(cyl(ENCODER[0] + ANTIROT_OFFSET[0], ENCODER[1] + ANTIROT_OFFSET[1],
                          Z_IN_TOP - 3, Z_OUT_TOP + 1, ANTIROT_D))
if BUTTON_ON:
    front = front.cut(cyl(*BUTTON, Z_IN_TOP - 3, Z_OUT_TOP + 1, BUTTON_D + 2 * FIT))

# FCI logo (artwork lifted from the FS10 enclosure) on the side of the grip
LOGO_FILE = os.path.join(HERE, "FCI_logo_emboss.brep")
if LOGO_ON and abs(LOGO_EMBOSS) > 0.01 and os.path.exists(LOGO_FILE):
    art = Part.Shape(); art.read(LOGO_FILE)            # wall plane x=0, raised 0.262 toward +x
    sc = LOGO_LEN / art.BoundBox.YLength
    m = App.Matrix(); m.scale(abs(LOGO_EMBOSS) / art.BoundBox.XLength, sc, sc)
    logo = art.transformGeometry(m)
    side = 1 if LOGO_SIDE >= 0 else -1
    if side < 0:
        logo.rotate(V(0, 0, 0), V(0, 0, 1), 180)          # left side: faces -x, still reads correctly
    x_wall = gx + WALL
    inset = 0.05 if LOGO_EMBOSS > 0 else abs(LOGO_EMBOSS)   # emboss: tuck 0.05 into the wall to fuse
    logo.translate(V(side * (x_wall - inset), LOGO_Y, LOGO_Z))
    lb = logo.BoundBox
    y_lo, y_hi = max(gy0 + CORNER_R, EAR_Y + EAR_D / 2 + 1.0), FLARE_Y0 - 1.0
    z_lo, z_hi = SPLIT_Z + 0.5, Z_OUT_TOP - FACE_FILLET - 0.3
    if lb.YMin < y_lo or lb.YMax > y_hi or lb.ZMin < z_lo or lb.ZMax > z_hi:
        msg = (f"WARNING: logo runs off the flat side (fits Y {y_lo:.1f}..{y_hi:.1f}, Z {z_lo:.1f}..{z_hi:.1f};"
               f" logo is Y {lb.YMin:.1f}..{lb.YMax:.1f}, Z {lb.ZMin:.1f}..{lb.ZMax:.1f})\n")
        print(msg, end=""); App.Console.PrintWarning(msg)
    front = front.fuse(logo) if LOGO_EMBOSS > 0 else front.cut(logo)
elif LOGO_ON:
    App.Console.PrintWarning("logo file FCI_logo_emboss.brep not found next to the macro\n")


def text_faces(txt, size):
    """Flat text in the XY plane (x = reading direction, y = up), baseline at y = 0."""
    faces = []
    for char in Part.makeWireString(txt, NAME_FONT, size, 0):
        if char:
            faces.append(Part.Face(char, "Part::FaceMakerBullseye"))
    return Part.makeCompound(faces)


def side_text(lines, ratio, side, x_wall, y, z, max_len, max_h, emboss, fit, label):
    """Text standing on a side wall (normal +/-x): reads along y from outside,
    letters up toward the front face.  lines[1:] are ratio x the size of lines[0].
    Returns the solid (to fuse when emboss > 0, cut when < 0)."""
    blocks = [text_faces(lines[0], 10.0)] + [text_faces(t, 10.0 * ratio) for t in lines[1:]]
    gap = 10.0 * 0.28
    y_cursor = 0.0
    for b in reversed(blocks):                            # stack bottom line first
        b.translate(V(-b.BoundBox.Center.x, y_cursor - b.BoundBox.YMin, 0))
        y_cursor = b.BoundBox.YMax + gap
    block = Part.makeCompound(blocks)
    block.translate(V(0, -block.BoundBox.Center.y, 0))
    bb = block.BoundBox
    block.scale(min(max_len / bb.XLength, max_h / bb.YLength))
    depth = abs(emboss) + (0.05 if emboss > 0 else 0.0)
    solid = block.extrude(V(0, 0, depth))
    m = App.Matrix(0, 0, side, 0,  side, 0, 0, 0,  0, 1, 0, 0)   # proper rotation (no mirror)
    solid = solid.transformGeometry(m)
    solid.translate(V(side * (x_wall - (0.05 if emboss > 0 else abs(emboss))), y, z))
    sb = solid.BoundBox
    (y_lo, y_hi), (z_lo, z_hi) = fit
    if sb.YMin < y_lo or sb.YMax > y_hi or sb.ZMin < z_lo or sb.ZMax > z_hi:
        msg = (f"WARNING: {label} runs off the flat side (fits Y {y_lo:.1f}..{y_hi:.1f}, Z {z_lo:.1f}..{z_hi:.1f};"
               f" it is Y {sb.YMin:.1f}..{sb.YMax:.1f}, Z {sb.ZMin:.1f}..{sb.ZMax:.1f})\n")
        print(msg, end=""); App.Console.PrintWarning(msg)
    return solid


z_fit = (SPLIT_Z + 0.5, Z_OUT_TOP - FACE_FILLET - 0.3)
have_font = os.path.exists(NAME_FONT)
if not have_font and (NAME_ON or STAMP_ON):
    App.Console.PrintWarning(f"font not found: {NAME_FONT}\n")

# product name on the grip side opposite the logo
if NAME_ON and abs(NAME_EMBOSS) > 0.01 and have_font:
    side = -1 if LOGO_SIDE >= 0 else 1
    name = side_text([NAME_LINE1, NAME_LINE2], NAME_RATIO, side, gx + WALL, NAME_Y, NAME_Z,
                     NAME_LEN, NAME_H, NAME_EMBOSS,
                     ((max(gy0 + CORNER_R, EAR_Y + EAR_D / 2 + 1.0), FLARE_Y0 - 1.0), z_fit), "name")
    front = front.fuse(name) if NAME_EMBOSS > 0 else front.cut(name)

# build stamp (file name + date/time of this build) on the side of the head
if STAMP_ON and abs(STAMP_EMBOSS) > 0.01 and have_font:
    import datetime
    fname = os.path.splitext(os.path.basename(doc.FileName or OUT_FCSTD))[0]
    stamp_text = f"{fname}  {datetime.datetime.now():%Y-%m-%d %H:%M}"
    side = 1 if STAMP_SIDE >= 0 else -1
    stamp = side_text([stamp_text], 1.0, side, HEAD_HW + WALL, STAMP_Y, STAMP_Z,
                      STAMP_LEN, STAMP_H, STAMP_EMBOSS,
                      ((FLARE_Y1 + CORNER_R, HEAD_TOP - CORNER_R), z_fit), "build stamp")
    front = front.fuse(stamp) if STAMP_EMBOSS > 0 else front.cut(stamp)
    App.Console.PrintMessage(f"ATmega32U4 handheld: build stamp '{stamp_text}'\n")
front = front.removeSplitter()
back = back.removeSplitter()

# button plunger
FL_D, FL_T = BUTTON_D + 4, 1.5
plunger = cyl(*BUTTON, BUTTON_TOP_Z + 0.3, Z_IN_TOP - 0.2, BUTTON_D - 1)
plunger = plunger.fuse(cyl(*BUTTON, Z_IN_TOP - 0.2 - FL_T, Z_IN_TOP - 0.2, FL_D))
plunger = plunger.fuse(cyl(*BUTTON, Z_IN_TOP - 0.2, Z_OUT_TOP + 1.5, BUTTON_D)).removeSplitter()

gcx, gcy = dcx + DISP_GLASS_DX, (dy0 + dy1) / 2 + DISP_GLASS_DY

GOLD = (0.83, 0.69, 0.22)

def make_oled():
    """Detailed 2.42" OLED module stand-in (reference only).  Panel layers from the
    Winstar 2.42" drawing; PCB features, frame, FPC route and back parts from photos
    of the user's module.  Returns {name: (shape, colour, transparency)}."""
    cx, cy = dcx, (dy0 + dy1) / 2               # module centre
    zb = Z_IN_TOP - stack                       # PCB back
    zf = zb + DISP_PCB_T                        # PCB front
    FR_T = 0.3                                  # steel frame sheet
    zp = Z_IN_TOP - FR_T                        # polarizer top = frame plate bottom
    zg = zp - 2.11                              # glass bottom (substrate 0.7 + cover 1.1 + pol 0.3)
    gt, gb = gcy + DISP_GLASS_H / 2, gcy - DISP_GLASS_H / 2
    gl, gr = gcx - DISP_GLASS_L / 2, gcx + DISP_GLASS_L / 2
    p = {}
    # PCB: FPC notch in the bottom edge, corner holes, frame-tab slots, header pads
    pcb = box(dx0, dy0, zb, dx1, dy1, zf)
    pcb = pcb.cut(box(cx - 11.5, dy0 - 1, zb - 1, cx + 11.5, dy0 + 7.0, zf + 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            pcb = pcb.cut(cyl(cx + sx * (DISP_W / 2 - 2.5), cy + sy * (DISP_H / 2 - 2.5), zb - 1, zf + 1, 3.0))
            pcb = pcb.cut(box(cx + sx * 20.8 - 3.0, cy + sy * 19.3, zb - 1, cx + sx * 20.8 + 3.0, cy + sy * 20.5, zf + 1))
    side = [(dcx + HDR_X, cy + HDR_Y + (k - 1.5) * 2.54) for k in range(4)]
    top = [(dcx + HDR_TOP_X + (k - 1.5) * 2.54, dy1 - HDR_FROM_TOP) for k in range(4)]
    pads = Part.Shape()
    for x, y in side + top:
        pcb = pcb.cut(cyl(x, y, zb - 1, zf + 1, 1.7))
        ring = cyl(x, y, zb - 0.03, zf + 0.03, 1.7).cut(cyl(x, y, zb - 1, zf + 1, 1.0))
        pads = ring if pads.isNull() else pads.fuse(ring)
    p["PCB"] = (pcb, (0.08, 0.08, 0.09), 0)
    # wired side header: pins through the board, 1.5 mm proud on the front, wires off the back
    pins = pads
    for x, y in side:
        pins = pins.fuse(box(x - 0.32, y - 0.32, zb - 3.0, x + 0.32, y + 0.32, zf + 1.5))
    p["Header_Pins"] = (pins, GOLD, 0)
    # glass: substrate (full), cover glass (from the top edge), polarizer
    glass = box(gl, gb, zg, gr, gt, zg + 0.7).fuse(box(gl, gt - 32.8, zg + 0.7, gr, gt, zg + 1.8))
    p["Glass"] = (glass, (0.55, 0.6, 0.65), 50)
    p["Polarizer"] = (box(gcx - 59.5 / 2, gt - 0.5 - 31.8, zg + 1.8, gcx + 59.5 / 2, gt - 0.5, zp),
                      (0.04, 0.04, 0.05), 0)
    p["Active_Area"] = (box(aa_cx - DISP_AA_W / 2, aa_cy - DISP_AA_H / 2, zp, aa_cx + DISP_AA_W / 2,
                            aa_cy + DISP_AA_H / 2, zp + 0.02), (0.1, 0.55, 1.0), 0)
    # steel frame: plate over the glass with a viewing-area opening, skirt down to
    # the PCB, four tabs through the slots folded flat on the back
    fw, fh = 62.0, 40.0
    va_cy = gt - 1.49 - 28.91 / 2
    plate = box(cx - fw / 2, cy - fh / 2, zp, cx + fw / 2, cy + fh / 2, Z_IN_TOP).cut(
        box(gcx - 57.01 / 2, va_cy - 28.91 / 2, zp - 1, gcx + 57.01 / 2, va_cy + 28.91 / 2, Z_IN_TOP + 1))
    skirt = box(cx - fw / 2, cy - fh / 2, zf, cx + fw / 2, cy + fh / 2, zp).cut(
        box(cx - fw / 2 + FR_T, cy - fh / 2 + FR_T, zf - 1, cx + fw / 2 - FR_T, cy + fh / 2 - FR_T, zp + 1))
    frame = plate.fuse(skirt)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = cx + sx * 20.8 - 2.5, cx + sx * 20.8 + 2.5
            yo = cy + sy * 20.0
            frame = frame.fuse(box(x0, yo, zb - FR_T, x1, yo - sy * FR_T, zf))          # through the slot
            frame = frame.fuse(box(x0, yo, zb - FR_T, x1, yo - sy * 2.5, zb))           # folded on the back
    p["Frame"] = (frame.removeSplitter(), (0.74, 0.75, 0.78), 0)
    # FPC: off the glass ledge, under the glass, round through the notch, up the back
    w2, ft, yb = 7.0, 0.15, dy0 + 2.5
    fpc = box(gcx - w2, gb + 0.5, zg + 0.7, gcx + w2, gb + 3.5, zg + 0.7 + ft)          # bonded on the ledge
    fpc = fpc.fuse(box(gcx - w2, yb, zg - ft, gcx + w2, gb + 0.5, zg))
    fpc = fpc.fuse(box(gcx - w2, yb, zb - 0.6, gcx + w2, yb + ft, zg))
    fpc = fpc.fuse(box(gcx - w2, yb, zb - 0.6, gcx + w2, cy + 5.0, zb - 0.6 + ft))
    p["FPC"] = (fpc.removeSplitter(), (0.85, 0.5, 0.1), 0)
    # back parts: FPC connector, L2 inductor, U9, U6, cap row
    parts = box(cx - 10, cy + 4.8, zb - 2.0, cx + 10, cy + 9.0, zb)
    for (u, v, a, b, h) in ((15.8, 7.8, 5.8, 5.8, 3.0), (21.2, 7.2, 3.0, 3.0, 1.2), (-14.0, 9.6, 3.0, 1.6, 1.1)):
        parts = parts.fuse(box(cx + u - a / 2, cy + v - b / 2, zb - h, cx + u + a / 2, cy + v + b / 2, zb))
    for k in range(10):
        u = -10.0 + k * 2.4 if k < 5 else 6.0 + (k - 5) * 2.6
        parts = parts.fuse(box(cx + u - 0.4, cy + 9.6 - 0.8, zb - 0.9, cx + u + 0.4, cy + 9.6 + 0.8, zb))
    p["Back_Parts"] = (parts, (0.25, 0.25, 0.27), 0)
    tape_gap = zg - zf
    if tape_gap < 0:
        msg = f"WARNING: DISP_GLASS_T {DISP_GLASS_T} is less than glass 2.11 + frame 0.3\n"
        print(msg, end=""); App.Console.PrintWarning(msg)
    return p


oled_parts = make_oled()
disp = Part.makeCompound([sh for nm, (sh, _, _) in oled_parts.items() if nm != "Active_Area"])

ex, ey = ENCODER
enc = box(ex - ENC_BODY / 2, ey - ENC_BODY / 2, Z_IN_TOP - ENC_BODY_H, ex + ENC_BODY / 2, ey + ENC_BODY / 2, Z_IN_TOP)
pcx, pcy = ex - ENC_SHAFT_DX, ey - ENC_SHAFT_DY          # module PCB centre
z_pcb = Z_IN_TOP - ENC_BODY_H
enc = enc.fuse(box(pcx - ENC_PCB_W / 2, pcy - ENC_PCB_L / 2, z_pcb - ENC_PCB_T,
                   pcx + ENC_PCB_W / 2, pcy + ENC_PCB_L / 2, z_pcb))
enc = enc.fuse(box(pcx - 6.5, pcy + ENC_PCB_L / 2, z_pcb - ENC_PCB_T - 1.0,      # 5-pin right-angle header
                   pcx + 6.5, pcy + ENC_PCB_L / 2 + ENC_PIN_REACH, z_pcb + 1.5))
enc = enc.fuse(cyl(ex, ey, Z_IN_TOP, Z_OUT_TOP + 5, 7.0))                  # M7 bushing + nut
enc = enc.fuse(cyl(ex, ey, Z_OUT_TOP + 5, Z_OUT_TOP + KNOB_GAP + KNOB_H - 3, 6.0))   # shaft


def make_knob(x, y, z0):
    """Machined-style control knob: skirt, ribbed grip, chamfered and dished top
    with an engraved pointer toward the display (+Y)."""
    import math
    r = KNOB_D / 2
    skirt_h = 2.0
    top = z0 + KNOB_H
    k = cyl(x, y, z0, z0 + skirt_h, KNOB_D + 2.0)
    k = k.fuse(Part.makeCone(r + 1.0, r, 1.0, V(x, y, z0 + skirt_h)))         # flare into the grip
    body = cyl(x, y, z0 + skirt_h, top, KNOB_D)
    top_edges = [e for e in body.Edges if abs(e.BoundBox.ZMax - top) < 1e-6 and e.BoundBox.ZLength < 1e-6]
    body = body.makeChamfer(1.0, top_edges)
    k = k.fuse(body)
    n = max(0, int(KNOB_RIBS))
    for i in range(n):                                                        # grip ribs
        a = 2 * math.pi * i / n
        k = k.cut(cyl(x + (r + 0.25) * math.cos(a), y + (r + 0.25) * math.sin(a),
                      z0 + skirt_h + 1.5, top - 2.0, 1.1))
    k = k.cut(Part.makeCone(r - 2.5, r - 3.0, 0.6, V(x, y, top - 0.6)))     # shallow dish
    k = k.cut(box(x - 0.5, y + 1.5, top - 1.4, x + 0.5, y + r - 2.0, top + 1))  # pointer line
    k = k.cut(cyl(x, y + r - 1.6, top - 1.6, top + 1, 1.0))                  # pointer dot
    k = k.cut(cyl(x, y, z0 - 0.1, top - 2.5, 6.2))                           # 6 mm shaft bore
    k = k.cut(cyl(x, y, z0 - 0.1, max(z0, Z_OUT_TOP + 5.3), 7.8))            # recess over the bushing + nut
    return k.removeSplitter()


knob = make_knob(ex, ey, Z_OUT_TOP + KNOB_GAP)

# taped-down modules on the back floor (Z_IN_BOT is the inside of the floor)
z_tape = Z_IN_BOT + TAPE_T
def make_amp():
    """TPA3118 PBTL mono board, decorated: PCB with corner holes, blue screw
    terminals (power, input, speaker), two electrolytics, two output inductors,
    the chip and a few SMD parts.  Everything stays inside AMP_L x AMP_W x AMP_H."""
    x0, y0 = AMP_X - AMP_L / 2, AMP_Y - AMP_W / 2
    zb = z_tape                                   # bottom of the PCB
    zt = zb + 1.6                                 # top of the PCB
    room = max(2.0, AMP_H - 1.6)                  # component height allowed
    u = lambda f: x0 + f * AMP_L                  # positions as fractions of the board
    v = lambda f: y0 + f * AMP_W
    parts = {}
    pcb = box(x0, y0, zb, x0 + AMP_L, y0 + AMP_W, zt)
    for fx, fy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        hx = x0 + 3.0 if fx == 0 else x0 + AMP_L - 3.0
        hy = y0 + 3.0 if fy == 0 else y0 + AMP_W - 3.0
        pcb = pcb.cut(cyl(hx, hy, zb - 1, zt + 1, 3.1))
    parts["PCB"] = (pcb, (0.05, 0.42, 0.18))

    th = min(10.0, room)
    term = Part.Shape()
    for (cx, cy, n, out) in ((u(0.0) + 3.8, v(0.30), 2, -1),    # power, left edge
                             (u(0.0) + 3.8, v(0.72), 2, -1),    # input, left edge
                             (u(1.0) - 3.8, v(0.50), 2, +1)):   # speaker, right edge
        L = n * 5.08
        t = box(cx - 3.75, cy - L / 2, zt, cx + 3.75, cy + L / 2, zt + th)
        for k in range(n):
            py = cy - L / 2 + 2.54 + k * 5.08
            t = t.cut(cyl(cx + 0.8 * out * -1, py, zt + th - 1.0, zt + th + 1, 3.2))   # screw head well
            t = t.cut(box(cx + out * 3.75 - (1.6 if out > 0 else -1.6), py - 1.5, zt + 1.5,   # wire entry
                          cx + out * 3.75 + out * 1, py + 1.5, zt + 4.5))
            t = t.fuse(cyl(cx + 0.8 * out * -1, py, zt + th - 1.0, zt + th - 0.3, 2.8)
                       .cut(box(cx + 0.8 * out * -1 - 1.4, py - 0.25, zt + th - 0.8,
                                cx + 0.8 * out * -1 + 1.4, py + 0.25, zt + th)))   # slotted screw
        term = t if term.isNull() else term.fuse(t)
    parts["Terminals"] = (term, (0.1, 0.35, 0.85))

    ch = min(10.0, room)
    caps = Part.Shape()
    for cy in (v(0.25), v(0.75)):
        c = cyl(u(0.36), cy, zt, zt + ch, 8.0)
        c = c.cut(box(u(0.36) - 3.0, cy - 0.15, zt + ch - 0.25, u(0.36) + 3.0, cy + 0.15, zt + ch + 1))   # vent
        c = c.cut(box(u(0.36) - 0.15, cy - 3.0, zt + ch - 0.25, u(0.36) + 0.15, cy + 3.0, zt + ch + 1))
        c = c.cut(cyl(u(0.36), cy, zt + ch - 1.6, zt + ch - 1.2, 9).cut(cyl(u(0.36), cy, zt, zt + ch, 7.6)))  # sleeve groove
        caps = c if caps.isNull() else caps.fuse(c)
    parts["Capacitors"] = (caps, (0.12, 0.12, 0.14))

    ih = min(4.5, room)
    ind = Part.Shape()
    for cy in (v(0.27), v(0.73)):
        i_ = box(u(0.68) - 5.0, cy - 5.0, zt, u(0.68) + 5.0, cy + 5.0, zt + ih)
        i_ = i_.cut(cyl(u(0.68), cy, zt + ih - 0.3, zt + ih + 1, 7.0).cut(cyl(u(0.68), cy, zt, zt + ih + 2, 6.4)))
        ind = i_ if ind.isNull() else ind.fuse(i_)
    parts["Inductors"] = (ind, (0.25, 0.25, 0.27))

    chip = box(u(0.52) - 3.05, v(0.5) - 5.5, zt, u(0.52) + 3.05, v(0.5) + 5.5, zt + 1.2)   # HTSSOP-32
    for k in range(16):
        y = v(0.5) - 4.875 + k * 0.65
        for side in (-1, 1):
            chip = chip.fuse(box(u(0.52) + side * 3.05, y - 0.12, zt, u(0.52) + side * 3.9, y + 0.12, zt + 0.25))
    chip = chip.cut(cyl(u(0.52) - 2.0, v(0.5) - 4.2, zt + 1.0, zt + 1.5, 0.8))   # pin-1 dot
    smd = Part.Shape()
    for fx, fy in ((0.52, 0.18), (0.52, 0.82), (0.24, 0.50), (0.60, 0.15), (0.60, 0.85), (0.80, 0.50)):
        r = box(u(fx) - 1.0, v(fy) - 0.6, zt, u(fx) + 1.0, v(fy) + 0.6, zt + 0.6)
        smd = r if smd.isNull() else smd.fuse(r)
    parts["Chip"] = (chip.fuse(smd), (0.08, 0.08, 0.08))
    return parts


amp_parts = make_amp()
amp = Part.makeCompound([p for p, _ in amp_parts.values()])     # envelope used by the checks
# PCB screws (reference): M3 pan heads on top of the board
sup = Part.Shape()
for x, y in HOLES:
    one = cyl(x, y, 1.6, 1.6 + 2.4, 5.6)
    sup = one if sup.isNull() else sup.fuse(one)
bat = box(BAT_X - BAT_L / 2, BAT_Y - BAT_W / 2, z_tape, BAT_X + BAT_L / 2, BAT_Y + BAT_W / 2, z_tape + BAT_H)

# M12 connector (approximate): hex flange + M12 coupling outside, body + jam nut inside
mdc = yhex(MDC_X, mdc_z, 19.05, y_wall_out, y_wall_out + 4.0)
mdc = mdc.fuse(ycyl(MDC_X, mdc_z, y_wall_out + 4.0, y_wall_out + 14.0, 12.0))
mdc = mdc.fuse(ycyl(MDC_X, mdc_z, y_wall_in - MDC_DEPTH_IN, y_wall_out, min(15.0, MDC_HOLE_D - 0.3)))
mdc = mdc.fuse(yhex(MDC_X, mdc_z, MDC_NUT_AF, y_wall_in - 5.8, y_wall_in))

# Switchcraft 35PRM3 from its drawing: thread, flange, body, solder lugs, nut
y_fl = aux_seat - 2.1                                  # back of the flange
aux = ycyl(AUX_X, aux_z, aux_seat, aux_seat + 3.5, min(6.0, AUX_HOLE_D - 0.2))   # thread
aux = aux.fuse(ycyl(AUX_X, aux_z, y_fl, aux_seat, 9.5))                         # flange
aux = aux.fuse(ycyl(AUX_X, aux_z, y_fl - 14.2, y_fl, 7.9))                      # body
aux = aux.fuse(box(AUX_X - 2.0, y_fl - 14.2 - 6.3, aux_z - 3.9,                  # lugs
                   AUX_X + 2.0, y_fl - 14.2, aux_z + 3.9))
aux = aux.fuse(ycyl(AUX_X, aux_z, y_wall_out, y_wall_out + 2.0, 9.5))            # knurled nut

# RJ12 jack (623K style, guessed): face through the wall, body behind it
rj = box(RJ_X - RJ_FACE_W / 2, y_wall_in, rj_z - RJ_FACE_H / 2, RJ_X + RJ_FACE_W / 2, y_wall_out, rj_z + RJ_FACE_H / 2)
rj = rj.fuse(box(RJ_X - RJ_BODY_W / 2, y_wall_in - RJ_DEPTH, rj_z - RJ_BODY_H / 2,
                 RJ_X + RJ_BODY_W / 2, y_wall_in, rj_z + RJ_BODY_H / 2))

# ---- connector face details (looks only) ----
import math
GOLD = (0.83, 0.69, 0.22)

# 3.5 mm jack: plug bore with lead-in, knurled nut
y_tip = aux_seat + 3.5                                   # front of the thread
aux = aux.cut(ycyl(AUX_X, aux_z, y_tip - 15.0, y_tip + 1, 3.6))
aux = aux.cut(Part.makeCone(1.8, 2.2, 0.4, V(AUX_X, y_tip - 0.4, aux_z), V(0, 1, 0)))
for i in range(30):
    a = 2 * math.pi * i / 30
    aux = aux.cut(Part.makeCylinder(0.35, 2.2, V(AUX_X + 4.85 * math.cos(a), y_wall_out - 0.1,
                                                 aux_z + 4.85 * math.sin(a)), V(0, 1, 0)))

# M12 female receptacle: thread rings on the coupling, recessed insert with
# 8 sockets (7 on a ring + centre) and a keyway, gold contacts in the sockets
y_m12 = y_wall_out + 14.0                                # front of the coupling
for k in range(9):
    yk = y_wall_out + 4.6 + k * 1.0
    mdc = mdc.cut(ycyl(MDC_X, mdc_z, yk, yk + 0.45, 13.0).cut(ycyl(MDC_X, mdc_z, yk - 1, yk + 1, 11.4)))
mdc = mdc.cut(ycyl(MDC_X, mdc_z, y_m12 - 6.0, y_m12 + 1, 9.6))               # bore in the coupling
mdc = mdc.fuse(ycyl(MDC_X, mdc_z, y_m12 - 6.0, y_m12 - 1.0, 8.6))            # contact insert
mdc = mdc.cut(box(MDC_X - 0.75, y_m12 - 4.0, mdc_z + 3.8, MDC_X + 0.75, y_m12, mdc_z + 4.8))   # keyway
m12_pins = Part.Shape()
sockets = [(0.0, 0.0)] + [(2.5 * math.cos(math.radians(90 + 360 * i / 7 + 360 / 14)),
                            2.5 * math.sin(math.radians(90 + 360 * i / 7 + 360 / 14))) for i in range(7)]
for dx, dz in sockets:
    mdc = mdc.cut(ycyl(MDC_X + dx, mdc_z + dz, y_m12 - 4.0, y_m12, 1.1))
    c = ycyl(MDC_X + dx, mdc_z + dz, y_m12 - 4.0, y_m12 - 2.6, 0.8)
    m12_pins = c if m12_pins.isNull() else m12_pins.fuse(c)

# RJ12 keystone: 6-position plug opening with latch slot, 6 gold contact springs
RJ_W, RJ_H, RJ_D = 9.7, 6.6, 12.0
RJ_D = min(RJ_D, RJ_DEPTH + WALL - 2.0)
rj = rj.cut(box(RJ_X - RJ_W / 2, y_wall_out - RJ_D, rj_z - RJ_H / 2,
                RJ_X + RJ_W / 2, y_wall_out + 1, rj_z + RJ_H / 2))
rj = rj.cut(box(RJ_X - 1.7, y_wall_out - RJ_D, rj_z - RJ_H / 2 - 1.4,         # latch slot (back side)
                RJ_X + 1.7, y_wall_out + 1, rj_z - RJ_H / 2 + 0.1))
rj_pins = Part.Shape()
for i in range(6):
    x = RJ_X + (i - 2.5) * 1.02
    spring = box(x - 0.18, y_wall_out - RJ_D + 1.0, rj_z + RJ_H / 2 - 0.45,
                 x + 0.18, y_wall_out - 3.0, rj_z + RJ_H / 2)
    rj_pins = spring if rj_pins.isNull() else rj_pins.fuse(spring)


# ---------------------------------------------------------------- output
import colorsys
import random
_hues = [(i * 0.618034 + random.random()) % 1.0 for i in range(32)]   # well-spread, new each run


def add(name, shape, color, transp=0, fixed=False):
    o = doc.getObject(name)
    created = o is None
    if created:
        o = doc.addObject("Part::Feature", name)
    o.Shape = shape                   # rebuilt in place on later runs
    if App.GuiUp:
        mode = int(COLOR_MODE)
        if mode == 2 and not fixed:   # random, high contrast
            color = colorsys.hsv_to_rgb(_hues.pop(0), 0.75, 0.95)
        if created or fixed or mode in (1, 2):  # mode 0: leave the user's colours alone
            o.ViewObject.ShapeAppearance = (App.Material(DiffuseColor=tuple(color)),)
            o.ViewObject.Transparency = transp
    return o


_far = iter(range(1000, 2000, 10))
def nowhere():                                     # stand-in for a switched-off part (each its own spot)
    k = next(_far); return box(k, k, k, k + 1, k + 1, k + 1)
off_names = []
if not BUTTON_ON:
    plunger = nowhere(); off_names += ["Button_Plunger"]
if not ENC_ON:
    enc, knob = nowhere(), nowhere(); off_names += ["Encoder_reference", "Encoder_Knob_reference"]
if not AUX_ON:
    aux = nowhere(); off_names += ["Audio_Jack_reference"]
if not RJ_ON:
    rj, rj_pins = nowhere(), nowhere(); off_names += ["RJ12_Jack_reference", "RJ12_Contacts_reference"]
if not AMP_ON:
    amp, amp_parts = nowhere(), {}; off_names += ["Amplifier_TPA3118"] + [f"Amp_{n}" for n in ("PCB", "Terminals", "Capacitors", "Inductors", "Chip")]
if not BAT_ON:
    bat = nowhere(); off_names += ["Battery_BT1_reference"]
for n in off_names:
    if doc.getObject(n) is not None:
        doc.removeObject(n)

o_back = add("Back_Shell", back, (0.15, 0.15, 0.17))
o_front = add("Front_Shell", front, (0.10, 0.45, 0.85), 0)
if BUTTON_ON:
    o_plunger = add("Button_Plunger", plunger, (0.9, 0.9, 0.9))
if doc.getObject("Display_reference") is not None:            # replaced by the detailed group
    doc.removeObject("Display_reference")
disp_grp = doc.getObject("Display_OLED") or doc.addObject("App::DocumentObjectGroup", "Display_OLED")
for nm, (shp, col, tr) in oled_parts.items():
    disp_grp.addObject(add(f"Disp_{nm}", shp, col, tr, fixed=True))
if ENC_ON:
    o_enc = add("Encoder_reference", enc, (0.7, 0.7, 0.72))
    o_knob = add("Encoder_Knob_reference", knob, (0.13, 0.13, 0.15))
o_pc = add("PC_Window_reference", pc_sheet, (0.85, 0.95, 1.0), 60)
o_mdc = add("M12_Connector_reference", mdc, (0.75, 0.75, 0.78))
if AUX_ON:
    o_aux = add("Audio_Jack_reference", aux, (0.15, 0.15, 0.15))
if doc.getObject("RJ12_Keystone_reference") is not None:      # replaced by the 623K jack
    doc.removeObject("RJ12_Keystone_reference")
if RJ_ON:
    o_rj = add("RJ12_Jack_reference", rj, (0.85, 0.85, 0.82))
o_m12p = add("M12_Contacts_reference", m12_pins, GOLD, fixed=True)
if RJ_ON:
    o_rjp = add("RJ12_Contacts_reference", rj_pins, GOLD, fixed=True)
old = doc.getObject("Amplifier_TPA3118_reference")             # replaced by the decorated group
if old is not None and old.TypeId == "Part::Feature":
    doc.removeObject(old.Name)
if AMP_ON:
    amp_grp = doc.getObject("Amplifier_TPA3118") or doc.addObject("App::DocumentObjectGroup", "Amplifier_TPA3118")
    for nm, (shp, col) in amp_parts.items():
        amp_grp.addObject(add(f"Amp_{nm}", shp, col, fixed=True))
if BAT_ON:
    o_bat = add("Battery_BT1_reference", bat, (0.85, 0.75, 0.2))
if doc.getObject("Board_Supports_reference") is not None:      # replaced by printed bosses
    doc.removeObject("Board_Supports_reference")
o_sup = add("PCB_Screws_reference", sup, (0.75, 0.75, 0.78))

doc.recompute()
if doc.FileName:
    doc.save()
else:
    doc.saveAs(OUT_FCSTD)
# STEP / STL files: run export_atmega32u4_handheld.py when the design is done

# report
ob = outer_face.BoundBox
print(f"Outer: {ob.XLength:.1f} wide (head) x {ob.YLength:.1f} long x {Z_OUT_TOP - Z_OUT_BOT:.1f} thick; "
      f"grip {2 * (gx + WALL):.1f} wide")
checked = 0
for pn, ps in (("Front", front), ("Back", back), ("Plunger", plunger), ("Display", disp), ("Encoder", enc),
               ("M12 connector", mdc), ("Audio jack", aux), ("RJ12 jack", rj),
               ("Amplifier", amp), ("Battery", bat), ("PCB screws", sup)):
    for sol in board_shape.Solids:
        if not ps.BoundBox.intersect(sol.BoundBox):
            continue
        checked += 1
        v = ps.common(sol).Volume
        if v > 0.01:
            c = sol.BoundBox.Center
            msg = f"INTERFERENCE {pn} x board part at ({c.x:.1f}, {c.y:.1f}, {c.z:.1f}): {v:.2f} mm^3"
            print(msg)
            App.Console.PrintWarning(msg + "\n")
print(f"interference check: {checked} part pairs near the shell")
# loose parts against the case itself
for pn, ps in (("Encoder", enc), ("Knob", knob), ("Display", disp), ("Plunger", plunger), ("PC window", pc_sheet),
               ("M12 connector", mdc), ("Audio jack", aux), ("RJ12 jack", rj),
               ("Amplifier", amp), ("Battery", bat), ("PCB screws", sup)):
    for sn, ss in (("Front_Shell", front), ("Back_Shell", back)):
        v = ps.common(ss).Volume
        if v > 0.01:
            msg = f"INTERFERENCE {pn} x {sn}: {v:.2f} mm^3"
            print(msg)
            App.Console.PrintWarning(msg + "\n")   # shows in FreeCAD's Report view
for an, a_, bn, b_ in (("M12 connector", mdc, "Audio jack", aux), ("M12 connector", mdc, "RJ12 jack", rj),
                       ("Audio jack", aux, "RJ12 jack", rj), ("Display", disp, "RJ12 jack", rj),
                       ("Display", disp, "M12 connector", mdc), ("Display", disp, "Audio jack", aux),
                       ("Amplifier", amp, "Battery", bat), ("Amplifier", amp, "Display", disp),
                       ("Battery", bat, "Display", disp), ("Amplifier", amp, "M12 connector", mdc),
                       ("Amplifier", amp, "Audio jack", aux), ("Amplifier", amp, "RJ12 jack", rj),
                       ("Battery", bat, "RJ12 jack", rj), ("Battery", bat, "M12 connector", mdc),
                       ("PCB screws", sup, "Amplifier", amp), ("PCB screws", sup, "Battery", bat)):
    v = a_.common(b_).Volume
    if v > 0.01:
        msg = f"INTERFERENCE {an} x {bn}: {v:.2f} mm^3"
        print(msg); App.Console.PrintWarning(msg + "\n")
# printable parts must be one piece each, and the halves must not overlap
for nm, sh in (("Front_Shell", front), ("Back_Shell", back), ("Button_Plunger", plunger)):
    if len(sh.Solids) != 1:
        msg = f"WARNING: {nm} is {len(sh.Solids)} separate pieces - would print loose\n"
        print(msg, end=""); App.Console.PrintError(msg)
v = front.common(back).Volume
if v > 0.01:
    msg = f"INTERFERENCE Front_Shell x Back_Shell: {v:.2f} mm^3"
    print(msg); App.Console.PrintWarning(msg + "\n")
summary = (f"ATmega32U4 handheld: done - {ob.XLength:.1f} x {ob.YLength:.1f} x {Z_OUT_TOP - Z_OUT_BOT:.1f} mm, "
           f"grip {2 * (gx + WALL):.1f} mm, saved {doc.FileName}")
App.Console.PrintMessage(summary + "\n")
print("done")
