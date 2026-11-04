# FS10 ATmega32U4 OLED USB passthrough repair

Build shown on the startup screen: **2026-09-23 12:41**.

Based on the exact `FS10_ATMEGA32U4OLED_FW_2026-09-13_1935.ino` source. The original file was not modified. This is a firmware test build; it has not been uploaded or tested against a physical FS10 or the PC application.

## Changes

- USB mode forwards PC commands and FS10 replies without inserting private display queries. The old private-query logic could discard the next PC reply after an unanswered private query.
- FS10 reply bytes stay in the existing 32-byte buffer until USB accepts them. PC commands no longer reuse that buffer. UART writes wait for transmit space without blocking the loop.
- The sketch writes to the native AVR CDC endpoint without requiring DTR. It no longer depends on the local Arduino `CDC.cpp` patch. The installed Arduino core and bootloader were not changed.
- Endpoint writes are limited to available space, within a short interrupt-protected copy, and avoid the AVR core's full-packet zero-length-packet wait.
- The existing OLED parser observes the raw replies while those same bytes go to the PC. USB display updates remain allowed when the PC has not recently sent a command. Queued bridge traffic takes priority over a scheduled OLED refresh.
- An unset switch-point value is now excluded from percentage calculation until its reply arrives, avoiding the prior signed overflow when range replies arrived first.

Standalone polling, valid-value parsing, OLED layout, USB detection, 9600-baud RS232 settings, alarms, the two-beep boot chirp, and both disabled TFT reference blocks were preserved. No boot I2C diagnostic was added to this September 13 baseline.

## Display behavior in USB mode

The PC owns the instrument conversation. The OLED shows the same fields as standalone mode, populated from the replies the PC requests. Fields the PC does not request retain their previous value or `--`; this build deliberately does not interleave extra queries. Testing with the real PC application is needed to establish which fields it supplies.

## Validation

Compiled with Arduino CLI for **FCI FS10 Flow Switch Power Supply** (`arduino:avr:fs10monitor`), Arduino AVR core 1.8.8:

- Flash: 25,988 / 28,672 bytes (90%).
- Static RAM: 1,121 / 2,560 bytes. The OLED additionally allocates 1,024 bytes, leaving approximately 415 bytes for stack and other dynamic use.
- Host tests extract the actual bridge/parser/mode functions from the sketch and run with address and undefined-behavior sanitizers.
- Reproduced three failures in the original bridge: private-query reply loss, short-write loss, and non-DTR-host reply loss with stock-core behavior.
- Revised bridge passed simultaneous binary traffic, no-DTR delivery, full/failed/partial USB writes, UART backpressure, unconfigured USB, all endpoint capacities 0–64, idle operation, and bounded buffering.
- The actual parser updated all seven display fields while preserving the raw PC response byte stream; missing switch-point data stayed unset.
- USB/power transitions reset the pending reply, and pending USB traffic deferred scheduled display refreshes.
- A FIFO model running the installed AVR core's exact `USB_Send` implementation completed all 2,145 combinations of send length and endpoint space without entering its wait loop.
- Source comparisons confirmed preservation of standalone polling/loop, screen layout, boot chirp, and both disabled TFT blocks. The percentage guard is the only parsing/calculation change.

The host tests do not simulate electrical USB/UART behavior or prove hardware operation. Buffers remain finite: a host that stops consuming indefinitely can eventually overflow the UART input buffer; no hardware flow control was added.

## Try it

1. Open the `.ino` inside this sketch folder in Arduino IDE. Select the existing **FCI FS10 Flow Switch Power Supply** board and the unit's normal USB port.
2. Upload normally. Do not burn or replace the bootloader. Confirm **2026-09-23 12:41** on the splash screen.
3. Close Serial Monitor if open, then connect using the normal FS10 PC software. Confirm instrument replies reach the software and corresponding values appear on the OLED.
4. Unplug USB and confirm standalone readings still update. Reconnect and test the PC connection again.

The `.hex` included here is the compiled application only, without a bootloader. The `.ino` is the normal Arduino IDE starting point.

Source SHA-256: `2b56bae86b54040c72cc9812404b4591d56c6c33d2dd37729da88e5cf3d2bae7`

New sketch SHA-256: `3319ac5ff3646b22becd1c000370e26e1080adcc2c01c39c1b859e0a1b5667e7`
