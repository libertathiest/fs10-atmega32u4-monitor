# FS10 ATmega32U4 OLED firmware

Startup build: **2026-09-23 13:12**.

Maintenance comments and [maintenance notes](MAINTENANCE.md) were added on
2026-09-23. They explain wiring, mode/fault behavior, USB buffer ownership,
startup, build dependencies and review follow-ups. This documentation pass
preserves the executable build and splash identifier; it does not require an upload.

This revision starts from the cleaned **13:01** firmware and keeps the working USB passthrough repair. All simulated-data code, its switch, timer, and function call have been removed. The sketch contains only normal instrument operation.

## Startup display change

The installed Adafruit SH110X 2.1.15 initializer sends DISPLAYON before the application has transferred its first frame. That can briefly expose old or uninitialized display memory. It is a plausible cause of the reported intermittent startup garble, not a hardware-confirmed diagnosis.

The new startup sequence is:

1. Preserve the existing two-beep boot chirp.
2. Allow 750 ms for display power to settle, increased from 250 ms.
3. Initialize the controller with the same register settings, keeping the panel off. Preserve the driver's additional 100 ms settling interval.
4. Draw the existing FCI FS10 / ATMEGA32U4 OLED / build-date splash into the same framebuffer.
5. Transfer all 1,024 visible image bytes while the panel remains off. This first transfer uses 100 kHz and respects the AVR Wire buffer limit.
6. Turn the panel on only after the complete transfer succeeds, show the splash for the unchanged 2,500 ms, then show the normal monitor screen.

`FS10OledStartup.h` provides the startup-specific helper. Keep it beside the `.ino` file. Normal display refreshes still use the existing Adafruit implementation and speed. The installed Arduino and display libraries were not modified. The helper's initialization settings are adapted from Adafruit's BSD-licensed driver; its license is included in `LICENSE-Adafruit.txt`.

The display-off, initialize, load screen, then display-on ordering is consistent with [SH1106 module startup guidance, section 4.2](https://cdn-shop.adafruit.com/product-files/5228/5223-ds.pdf). That document is supporting controller-family guidance, not identification of the exact installed module.

## What this can and cannot establish

The four-wire display connection provides power, ground, SDA, and SCL; there is no MCU-controlled reset line. The reset argument in the previous code could not generate a physical reset because its reset pin was set to -1. The settling delay is not a measurement of supply stability.

If a startup command or frame transfer fails, the firmware does not intentionally enable the display; instrument and USB operation continue. This does not add continuous display recovery or retries. Firmware also cannot control the panel before the MCU begins executing it. Intermittent power, wiring, or reset-circuit faults may still need hardware investigation if the symptom persists.

## Validation

- Compilation passed for **FCI FS10 Flow Switch Power Supply** (`arduino:avr:fs10monitor`) with Arduino AVR core 1.8.8, Adafruit SH110X 2.1.15, and the installed GFX/BusIO libraries.
- Flash: 25,662 / 28,672 bytes. Static RAM: 1,120 / 2,560 bytes, plus the existing 1,024-byte OLED framebuffer at runtime.
- All ten existing USB bridge regression checks passed.
- Source comparisons confirmed that USB forwarding, parsing, standalone polling, normal screen rendering, mode transitions, and boot chirps are unchanged.
- A host model exercised the actual startup helper and sketch startup functions. It verified a complete 1,024-byte frame before DISPLAYON, Wire transactions no larger than 32 bytes, preservation of the splash duration, initialization failure, and failure at each of the 50 startup transfers.
- These are software/build checks. This revision has not been uploaded or tested on the physical unit by Codex.
- The documentation pass was compiled again: executable source tokens are unchanged,
  and its application `.hex` is byte-for-byte identical to the original 13:12 image
  (SHA-256 `1c2ed44f5956e2f297448e000ac93520366525964c1347e0ee9faf6b15452840`).

## Reported hardware results

The user confirmed that the repaired USB passthrough works well. After the startup
change, USB power cycling and switching 24V with its source already connected were
reported satisfactory. Intermittent garble when plugging in the 24V source remains
a possible hardware/startup interaction; the buck converter was not proved faulty.
The user accepted the present startup behavior. These are user-reported tests,
separate from the software checks above.

## Uploading this revision

Open this folder's `.ino` in Arduino IDE and upload normally with the existing board selection and port. No bootloader change is needed. Confirm the splash says **2026-09-23 13:12** and remains visible for 2.5 seconds.

Because the reported fault is intermittent, try several cold power-ups and check that the first visible image is a clean splash followed by the normal display. If garble remains, note whether it precedes the boot beeps, occurs during the splash, or remains on the normal screen.

The previous working firmware remains preserved. The included `.hex` is the application only, without a bootloader.
