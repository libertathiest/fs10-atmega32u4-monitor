#pragma once

#include <Adafruit_SH110X.h>

// Initialization settings adapted from Adafruit SH110X 2.1.15.
// Copyright (c) 2012, Adafruit Industries. All rights reserved.
// SPDX-License-Identifier: BSD-3-Clause
// See LICENSE-Adafruit.txt for the license and disclaimer.
// The panel stays off until the sketch has loaded its first complete frame.
// Hardware-specific helper for this 128x64 SH1106 I2C module (column offset 2).
// Uses protected Adafruit fields: recheck it after display-library upgrades.
// The 1,024-byte framebuffer is allocated by _init() and reused at runtime.
class FS10OledDisplay : public Adafruit_SH1106G {
public:
  using Adafruit_SH1106G::Adafruit_SH1106G;

  bool beginBlank(uint8_t address) {
    // The four-wire module has no MCU-controlled reset connection.
    if (!Adafruit_GrayOLED::_init(address, false)) return false;
    _page_start_offset = 2;

    // Preserve the working driver's configuration, without its early DISPLAYON
    // or built-in bitmap. This command list fits the AVR Wire transmit buffer.
    static const uint8_t commands[] = {
        SH110X_DISPLAYOFF,
        SH110X_SETDISPLAYCLOCKDIV, 0x80,
        SH110X_SETMULTIPLEX, 0x3F,
        SH110X_SETDISPLAYOFFSET, 0x00,
        SH110X_SETSTARTLINE,
        SH110X_DCDC, 0x8B,
        SH110X_SEGREMAP + 1,
        SH110X_COMSCANDEC,
        SH110X_SETCOMPINS, 0x12,
        SH110X_SETCONTRAST, 0xFF,
        SH110X_SETPRECHARGE, 0x1F,
        SH110X_SETVCOMDETECT, 0x40,
        0x33,
        SH110X_NORMALDISPLAY,
        SH110X_MEMORYMODE, 0x10,
        SH110X_DISPLAYALLON_RESUME,
    };
    if (!oled_commandList(commands, sizeof(commands))) return false;
    delay(100); // Keep the driver's charge-pump settling interval.
    return true;
  }

  bool writeStartupFrame() {
    if (!buffer || !i2c_dev) return false;
    const uint16_t capacity = i2c_dev->maxBufferSize();
    if (capacity < 2) return false;
    const uint8_t dataPrefix = 0x40;
    bool ok = true;

    // Use the normal 100 kHz idle bus rate for the first frame only.
    // Later refreshes use the unchanged library display() implementation.
    i2c_dev->setSpeed(i2c_postclk);
    for (uint8_t page = 0; page < (HEIGHT + 7) / 8 && ok; ++page) {
      uint8_t commands[] = {
          0x00, (uint8_t)(SH110X_SETPAGEADDR + page),
          (uint8_t)(0x10 + (_page_start_offset >> 4)),
          (uint8_t)(_page_start_offset & 0x0F)};
      ok = i2c_dev->write(commands, sizeof(commands));
      uint16_t remaining = WIDTH;
      uint8_t *pixels = buffer + (uint16_t)page * WIDTH;
      while (ok && remaining > 0) {
        // Include the 0x40 control prefix in Wire's transaction size limit.
        uint16_t count = min(remaining, (uint16_t)(capacity - 1));
        ok = i2c_dev->write(pixels, count, true, &dataPrefix, 1);
        pixels += count;
        remaining -= count;
      }
    }
    return ok;
  }
};
