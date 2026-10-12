# ATmega32U4 (FS10 power supply and monitor) - export the handheld enclosure for printing
#
# Run this (Macro > Macros... > Execute) once the design is final.  It writes STEP files only,
# next to ATmega32U4-Enclosure.FCStd:
#   ATmega32U4-Enclosure.step                  assembly: front shell, back shell
#   ATmega32U4-Enclosure-Front_Shell.step       print face-down
#   ATmega32U4-Enclosure-Back_Shell.step
#   ATmega32U4-Enclosure-Board_model.step       full-detail board model (all components)
#   ATmega32U4-Enclosure-Display_coupon.step    head of the front half only - quick display fit test
#   ATmega32U4-Enclosure-Board_fitcheck.step    simplified board for test prints: real outline,
#                                      holes, edge connectors + SW2, tall parts as blocks

import os
import FreeCAD as App
import Import
import Part

doc = App.ActiveDocument
if doc is None or doc.getObject("Back_Shell") is None:
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.path.expanduser("~/Documents/FS10-ATmega32U4/hardware/FreeCAD enclosure")
    doc = App.openDocument(os.path.join(here, "ATmega32U4-Enclosure.FCStd"))
out = os.path.dirname(doc.FileName)

parts = [doc.getObject(n) for n in ("Front_Shell", "Back_Shell")]
missing = [n for n, o in zip(("Front_Shell", "Back_Shell"), parts) if o is None]
if doc.getObject("Button_Plunger") is not None:      # only if a button is switched on
    parts.append(doc.getObject("Button_Plunger"))
if missing:
    raise RuntimeError(f"run build_atmega32u4_handheld.py first - missing {missing}")

openings = doc.getObject("Openings")
if openings is None or len(openings.Group) < 3:
    App.Console.PrintError("WARNING: connector openings missing - run build_atmega32u4_handheld.py first\n")

written = []
step = os.path.join(out, "ATmega32U4-Enclosure.step")
Import.export(parts, step)
written.append(step)
def write_step(shape, f):
    """Exact solid (no mesh) - the printer's slicer meshes it."""
    shape.exportStep(f)
    written.append(f)


for o in parts:
    write_step(o.Shape, os.path.join(out, f"ATmega32U4-Enclosure-{o.Name}.step"))
board = doc.getObject("Board_Solid")
if board is not None:                 # full-detail board, colours kept
    f = os.path.join(out, "ATmega32U4-Enclosure-Board_model.step")
    Import.export([board], f)
    written.append(f)

# fit-check board: the real board outline + holes, the edge connectors and SW2
# exactly as modelled, every other tall part as a clean block, nothing below the
# board - prints face-up flat on the bed with no supports.
if board is not None:
    import Part
    from FreeCAD import Vector as V
    solids = board.Shape.Solids
    pcb = max((x for x in solids if abs(x.BoundBox.ZLength - 1.6) < 0.2), key=lambda x: x.Volume)
    pb = pcb.BoundBox
    btn = None
    sp = doc.getObject("Button_Plunger")
    if sp is not None:
        btn = sp.Shape.BoundBox.Center
    keep = [pcb]
    for x in solids:
        if x.isSame(pcb):
            continue
        b = x.BoundBox
        edge = b.YMin < pb.YMin - 0.05                    # USB, DC jack, power switch
        is_sw2 = btn is not None and abs(b.Center.x - btn.x) < 4 and abs(b.Center.y - btn.y) < 4
        if edge:                                          # front profile through the wall + body inside
            pts = [q for q in x.tessellate(0.1)[0] if q.y < pb.YMin]
            if pts:
                xs, zs = [q.x for q in pts], [q.z for q in pts]
                keep.append(Part.makeBox(max(xs) - min(xs), pb.YMin - b.YMin, max(zs) - max(min(zs), pb.ZMin),
                                         V(min(xs), b.YMin, max(min(zs), pb.ZMin))))
            keep.append(Part.makeBox(b.XLength, b.YMax - pb.YMin, b.ZMax - pb.ZMax, V(b.XMin, pb.YMin, pb.ZMax)))
        elif is_sw2 or b.ZMax > pb.ZMax + 2.5:            # SW2 / tall part: clean block of its outline
            keep.append(Part.makeBox(b.XLength, b.YLength, b.ZMax - pb.ZMax,
                                     V(b.XMin, b.YMin, pb.ZMax)))
    fit = keep[0]
    for x in keep[1:]:
        try:
            fit = fit.fuse(x)
        except Exception:
            fit = Part.makeCompound([fit, x])
    fit = fit.common(Part.makeBox(400, 400, 100, V(-200, -200, pb.ZMin)))   # nothing below the board
    fit = fit.removeSplitter()
    write_step(fit, os.path.join(out, "ATmega32U4-Enclosure-Board_fitcheck.step"))
    App.Console.PrintMessage(f"ATmega32U4 export: fit-check board from {len(keep)} parts, "
                             f"{fit.BoundBox.XLength:.1f} x {fit.BoundBox.YLength:.1f} x {fit.BoundBox.ZLength:.1f} mm\n")

# display test coupon: just the head of the front half - window, bevel,
# polycarbonate pocket, rails and snap clips.  Prints face-down, quickly.
front = doc.getObject("Front_Shell")
disp = doc.getObject("Disp_PCB") or doc.getObject("Display_reference")   # display board outline
if disp is None:
    App.Console.PrintError("WARNING: no display model found - display coupon not written\n")
if front is not None and disp is not None:
    import Part
    from FreeCAD import Vector as V
    db, fb = disp.Shape.BoundBox, front.Shape.BoundBox
    cut = Part.makeBox(fb.XLength + 2, fb.YMax - (db.YMin - 6) + 1, fb.ZLength + 2,
                       V(fb.XMin - 1, db.YMin - 6, fb.ZMin - 1))
    coupon = front.Shape.common(cut)
    write_step(coupon, os.path.join(out, "ATmega32U4-Enclosure-Display_coupon.step"))
    App.Console.PrintMessage(f"ATmega32U4 export: display coupon {coupon.BoundBox.XLength:.0f} x "
                             f"{coupon.BoundBox.YLength:.0f} x {coupon.BoundBox.ZLength:.0f} mm\n")

for f in written:
    App.Console.PrintMessage(f"ATmega32U4 export: {os.path.basename(f)}  ({os.path.getsize(f) / 1e6:.1f} MB)\n")
App.Console.PrintMessage(f"ATmega32U4 export: done -> {out}\n")
