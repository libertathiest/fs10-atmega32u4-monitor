# First handheld generation (retired)

The earlier ATmega32U4 handheld enclosure, superseded by `ATmega32U4-Enclosure.*` in
`hardware/FreeCAD enclosure/`. Its build and export scripts were archived here on 2026-10-12; the
model, its backup and its STEP exports followed on 2026-11-03, which is the whole generation in one
place.

What told them apart, measured from the two models before the move:

| | `-Enclosure` (live) | `-Handheld` (here) |
| --- | --- | --- |
| objects with solids | 22 | 21 |
| display | `Display_OLED`, 24 solids | `Disp_PCB` + `Disp_Glass`, the older TFT stack |
| openings | merged `Openings`, 3 solids | separate, e.g. `Opening_USB` |
| Back_Shell | 44984.0 mm3 | 44907.4 mm3 |
| Front_Shell | 44286.0 mm3 | 44365.1 mm3 |

Both carried the same 131-row Parameters sheet, so one was cloned from the other and then diverged.
`-Handheld` had the newer file timestamp (29 Oct 16:20 against 16:14) only because it had been open
in FreeCAD and saved; no script writes it. `build_atmega32u4_enclosure.py` and
`export_atmega32u4_enclosure.py` both work on `ATmega32U4-Enclosure.FCStd`.

The STEP files here are from 8 October, two generations behind the `-Enclosure` exports.
