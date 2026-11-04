# FS10 OLED firmware maintenance notes

Executable build: **2026-09-23 13:12**. Documentation added: **2026-09-23**.
The documentation pass adds comments only to the source and helper. The build
identifier and splash date still identify the same executable behavior.

## Files and build

Keep the matching `.ino`, `FS10OledStartup.h` and `LICENSE-Adafruit.txt` together.
The helper contains adapted Adafruit initialization settings and depends on
protected library fields, so library upgrades require a compile and startup test.
The supplied `.hex` contains the application only; it does not include a bootloader.

Verified toolchain:

| Component | Version or setting |
| --- | --- |
| Board | FCI FS10 Flow Switch Power Supply, `arduino:avr:fs10monitor` |
| Processor / pin mapping | ATmega32U4, 16 MHz, Leonardo variant |
| Arduino AVR core | 1.8.8 |
| Adafruit SH110X | 2.1.15 |
| Adafruit GFX | 1.12.6 |
| Adafruit BusIO | 1.17.4 |
| FS10 UART | `Serial1`, 9600 baud, 8 data bits, no parity, 1 stop bit |
| PC connection | `Serial`, native USB CDC |

`fs10monitor` is a locally installed custom board definition, not a standard
Arduino package entry. A new workstation needs the corresponding board definition
and libraries. It uses the Leonardo variant and the USB product name
`FCI FS10 Flow Switch Power Supply`. Selecting a generic board can change the USB
identity even if compilation succeeds. Do not burn a bootloader as part of an
ordinary firmware update.

Compile from this sketch directory:

```sh
arduino-cli compile --fqbn arduino:avr:fs10monitor .
```

`Serial.begin(115200)` does not set the FS10 communication speed. Only
`Serial1.begin(FS10_BAUD, SERIAL_8N1)` configures that UART. The USB bridge's reply
writer calls the native AVR endpoint API directly, so it does not need a local
`CDC.cpp` DTR-gate patch. Review the endpoint code when changing Arduino cores.

## Hardware assumptions

| Connection | Firmware use |
| --- | --- |
| OLED J13 | 1 GND, 2 +5V, 3 PD1/SDA, 4 PD0/SCL |
| OLED | SH1106, 128 x 64, I2C address `0x3C`, column offset 2 |
| OLED reset | No reset wire; `OLED_RESET = -1` cannot physically reset it |
| PB4 | USB_PRESENT from the external VUSB divider; internal pull-up off |
| PB7 | 24V-present digital sense; internal pull-up off |
| PF1 / PF0 | NC / NO relay-contact sense, internal pull-ups on |
| PB5 / Arduino 9 | Buzzer |
| PF4 / A3, PF5 / A2, PF6 / A1 | Red, green, blue LED cathodes; LOW turns on |
| PD7 | Panel switch input with pull-up; the single-page display does not read it |

The 24V indication is a logic-level presence check, not a calibrated voltage or
ripple measurement. Relay inputs PF1:PF0 of `01` mean LO and `10` mean HI;
`00` or `11` are unknown. The cable check uses that contact pattern, not an RS232
response test. The invalid state is returned immediately; the cable indication
and unplug beep are delayed by 600 ms.

## Operating modes and fault behavior

The physical USB_PRESENT signal selects who owns commands. A plugged-in USB cable
selects USB mode even if no PC program has opened the port or asserted DTR.

| Condition | What the firmware does |
| --- | --- |
| 24V present, USB absent, contacts valid | Receives FS10 replies and originates standalone queries |
| 24V present, USB absent, contacts invalid | Continues receiving UART bytes; pauses standalone queries |
| 24V present, USB present | Forwards PC commands and FS10 replies; OLED observes replies |
| 24V present, USB present, contacts invalid | Still forwards both directions; PC handles missing replies |
| 24V absent, with or without USB | Returns before forwarding or standalone receive/polling |

When 24V is absent, USB can remain enumerated because the controller has USB power.
The sketch stops reading PC commands, so they can queue and eventually make a host
write wait. Unplugging only the FS10 cable with 24V present leaves forwarding active;
the PC can send and then time out awaiting a reply. These firmware paths are
confirmed. The exact PC application's send/receive timeout behavior is not known
without its logs or source.

On a detected USB or supply transition, the sketch clears its pending USB reply
count and partial display-parser line. It does not explicitly drain the USB
endpoint, PC driver queues or core UART receive buffer. Commands accepted while
24V was off can therefore remain queued when power returns. Changing this policy
is a communication-behavior change, not cosmetic cleanup.

The five-second PC-idle indication measures time since PC bytes were forwarded.
It does not diagnose FS10 reply age or suspend the bridge. Fault handling keeps
the same screen layout; supply/cable faults clear readings to `--`.

## Rules for maintaining the bridge

- Keep PC and FS10 traffic byte-for-byte intact. The display parser normalizes a
  separate copy only. Do not send debugging messages to `Serial` or `Serial1`.
- The PC owns all requests in USB mode. Do not inject background display queries
  or hide presumed replies: this previously swallowed legitimate PC responses.
- `bridgeBuffer` belongs only to FS10-to-PC pending replies. Retry partial or
  temporarily unavailable USB writes without discarding those bytes. The PC-to-FS10
  path checks UART transmit space and forwards at most 32 bytes per loop.
- Preserve the short atomic endpoint space-check/write sequence in
  `writeUsbAvailable()`. Filling a USB bank exactly or allowing the SOF interrupt
  to release it between the check and write can reintroduce a blocking core path.
- Finite UART buffers cannot absorb an indefinitely stalled PC. This repair does
  not add RS232 flow control or guarantee lossless operation through any length
  of host outage.
- Scheduled OLED refreshes wait for 100 ms of serial quiet, no pending USB traffic
  and the 500 ms display interval. Startup and fault-triggered refreshes are
  synchronous exceptions. Keep display work out of the transport byte loops.

USB mode can only display fields the PC actually requests. A missing field is not
a reason to inject another request. Standalone mode requests `*107`, `*108`, `*112`,
`*238`, `*227` and `*032` during configuration, then uses `*meas` for measurements.
Configuration polling is bounded to four passes and can finish early once the
required values are present. Commands terminate with carriage return.

The display watcher stores at most 63 characters, then parses that prefix on
CR/LF; excess characters are not retained for display. This limit does not truncate
the bytes forwarded to the PC. `LONG_MIN` denotes an unknown numeric value; all
range-dependent calculations must check it before doing arithmetic.

## OLED startup and memory

The sequence is: two boot beeps, 750 ms supply allowance, controller initialization
with display off, 100 ms driver settling time, complete splash transfer at 100 kHz,
display on, 2.5-second splash, normal screen. The transfer includes the control byte
within Wire's buffer limit. Startup is deliberately blocking; normal communication
servicing starts after `setup()` finishes. Keep the splash.

If initialization or the first frame transfer fails, the code does not intentionally
turn the display on and normal communication can continue. There is no continuous
OLED recovery. Software cannot control the panel before the MCU starts, and the
delays do not prove that the supply has settled.

The user reported satisfactory USB and switch-controlled 24V startup after this
change and accepted it. Intermittent garble when plugging in the 24V source was not
proved to be a firmware fault or a defective buck converter. No further startup
timing change was requested.

The build uses 25,662 bytes of application flash and 1,120 bytes of static SRAM.
The OLED also allocates a 1,024-byte framebuffer at runtime. Subtracting those from
2,560 bytes leaves only about 416 bytes for the stack and other heap use; this is
not a measured free-RAM or worst-case stack figure. Avoid another framebuffer,
large local arrays or dynamic strings. Keep fixed command/display strings in `F()`.

## Review follow-ups, left unchanged

- `lastFs10DataMs` is assigned but never read. It is a candidate for removal; it
  currently provides no reply-timeout detection.
- Tenths formatting loses the sign for values between -1.0 and 0.0: for example,
  `setTenthsDisplayValue(..., -5)` formats `0.5`. This is a display-formatting edge
  case, not a change to forwarded instrument bytes.
- Numeric accumulation/scaling and percentage arithmetic do not fully guard
  32-bit overflow on out-of-range input. Add explicit bounds if hardening the
  parser; do not assume a host test's 64-bit `long` matches AVR's 32-bit `long`.

These are source-review findings, not reported failures on the current unit. Any
behavioral repair should have its own dated revision and focused validation.

## Validation when making the next functional revision

Compile with the intended board/core/library versions and review both flash and
runtime SRAM needs. Exercise the bridge's stalled/partial-write cases and startup
failure paths. Then test on the actual unit: standalone measurements, normal PC
communication, USB connected with no PC program, 24V removal/restoration with USB
attached, cable removal/restoration, the two boot beeps and visible splash.

Keep software-model checks separate from physical test results. The existing
working revision and application image should remain available for rollback.
