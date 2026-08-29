# FS10 Standalone Monitor (ATmega32U4)

A standalone USB monitor and configuration tool for the FCI FS10 Flow Switch, built around the **ATmega32U4** on an Arduino Leonardo–compatible board. It talks to the FS10 over a UART passthrough and shows flow switch condition both graphically and as text on an onboard TFT display — an independent, personal-project replacement for the legacy (uncertified) FCI power accessory.

This was designed, laid out, and manufactured end-to-end: schematic capture and PCB layout in KiCad, enclosure design in FreeCAD, and production through JLCPCB. Physical units are built and in active use.

## Hardware

- **MCU:** ATmega32U4 (Arduino Leonardo form factor, 68.6×53.4mm outline)
- **Display:** 2.4" 240×320 SPI TFT, ILI9341 driver (Adafruit_GFX + Adafruit_ILI9341)
- **Power:** UART passthrough with power arbitration between USB and an external 24V supply; ships with a UL/ETL/CE/FCC-certified wall adapter
- **Enclosure:** Hammond 1593-series compatible, modeled in FreeCAD (STL + parametric source included)
- **PCB:** Designed in KiCad (originally imported from EasyEDA Pro); manufactured and assembled via JLCPCB

## Repo layout

```
firmware/   Arduino sketch (.ino) — display driver, UART passthrough, UI
hardware/   KiCad project (schematic/PCB), FreeCAD enclosure, JLCPCB gerbers + BOM
Assets/     Schematic PDF, design docs, product flyer, front label preview
notes/      Supporting reference material
```

## Status

Completed. Units are built, deployed, and in day-to-day field use.

---
*This is an independently developed project, not an official FCI-branded product.*
