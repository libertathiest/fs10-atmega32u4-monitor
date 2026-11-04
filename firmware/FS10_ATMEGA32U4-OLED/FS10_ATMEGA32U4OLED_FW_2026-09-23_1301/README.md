# FS10 ATmega32U4 OLED firmware

Startup build: **2026-09-23 13:01**.

Based on the USB repair revision from **2026-09-23 12:41**, which the user confirmed works well on the device.

This cleanup removes the obsolete display implementation and its two disabled code blocks, renames three status helpers to match the OLED behavior, and removes an unused flag and its unreachable branch. The sketch is 337 lines shorter. The previous working revision is preserved.

The USB bridge, standalone polling, reading parser, OLED layout, sensing, alarms, and boot chirps retain the same logic. Only the startup build timestamp changes on screen.

Validation:

- Active-source comparison found no changes beyond the status helper renames, removal of constant-false legacy state, and build timestamp.
- All ten existing USB bridge regression checks passed.
- Compilation passed for `arduino:avr:fs10monitor` with Arduino AVR core 1.8.8.
- Flash: 25,966 / 28,672 bytes. Static RAM: 1,120 / 2,560 bytes, plus the existing 1,024-byte OLED framebuffer at runtime.
- This cleanup revision has not been uploaded by Codex or independently tested on hardware.

Open the `.ino` in Arduino IDE, use the existing **FCI FS10 Flow Switch Power Supply** board selection and USB port, and upload normally. Confirm **2026-09-23 13:01** on the startup screen. No bootloader change is required. The included `.hex` contains the application only.

As in the working USB revision, the OLED displays values supplied in the PC's requested replies while connected to USB. Unrequested fields retain their previous value or `--`. Standalone operation continues to request its own readings.
