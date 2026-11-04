// FS10 OLED bridge: stable USB CDC <-> RS232 bridge plus a compact status display.
// USB mode is a transparent PC-controlled bridge; the OLED observes replies.
// Native AVR CDC endpoint writes support PC software that does not assert DTR.
// No local Arduino CDC.cpp patch is required.
//
// Target: custom 16 MHz ATmega32U4 board, Arduino AVR Leonardo pin mapping.
// Serial = native USB CDC; Serial1 = FS10 UART at 9600 baud, 8N1.
// USB_PRESENT selects PC ownership even when no PC application has opened it.
// With USB absent, the firmware owns polling. See MAINTENANCE.md for the mode
// table, wiring, build dependencies, startup sequence and known limitations.
// Comments updated 2026-09-23; executable build/splash remains 13:12.

#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Wire.h>
#include <ctype.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <util/atomic.h>
#include "FS10OledStartup.h"

constexpr uint32_t FS10_BAUD = 9600;
// J13 optional OLED header: pin 3 is PD1/SDA, pin 4 is PD0/SCL.
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;
constexpr uint8_t OLED_WIDTH = 128;
constexpr uint8_t OLED_HEIGHT = 64;
constexpr int8_t OLED_RESET = -1;
constexpr uint8_t BUZZER_PIN = 9; // PB5, BUZZER_CTRL
constexpr uint8_t LED_RED_PIN = A3; // PF4, common-anode RGB LED cathode
constexpr uint8_t LED_GRN_PIN = A2; // PF5, common-anode RGB LED cathode
constexpr uint8_t LED_BLU_PIN = A1; // PF6, common-anode RGB LED cathode
constexpr uint8_t PANEL_BUTTON_BIT = 7; // PD7, PANEL_SW_D7 on custom board
constexpr uint8_t RELAY_HI_BIT = 1; // PF1, NC relay contact sense
constexpr uint8_t RELAY_LO_BIT = 0; // PF0, NO relay contact sense
constexpr uint8_t SUPPLY_24V_BIT = 7; // PB7, 24V-present sense
constexpr uint8_t LINE_MAX = 64;
constexpr uint8_t BRIDGE_CHUNK_MAX = 32;
constexpr uint16_t DISPLAY_TICK_MS = 500;
constexpr uint16_t DISPLAY_QUIET_MS = 100;
constexpr uint16_t STANDALONE_MEAS_MS = 500;
constexpr uint16_t STANDALONE_CONFIG_MS = 250;
constexpr uint16_t STANDALONE_CABLE_FAULT_MS = 600;
constexpr uint16_t USB_PC_IDLE_MS = 5000;
constexpr uint8_t STANDALONE_CONFIG_MAX_PASSES = 4;
constexpr uint16_t OLED_POWERUP_DELAY_MS = 750;
constexpr uint16_t STARTUP_SPLASH_MS = 2500;

FS10OledDisplay display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);

static uint32_t ledUntilMs = 0;
static uint32_t lastDisplayMs = 0;
static uint32_t lastBridgeActivityMs = 0;
static uint32_t lastStandaloneMeasMs = 0;
static uint32_t lastStandaloneConfigMs = 0;
static uint32_t lastPcBridgeActivityMs = 0;
static uint32_t lastFs10DataMs = 0;
static uint32_t relayUnknownSinceMs = 0;
static uint32_t secondBeepMs = 0;
static uint16_t secondBeepFreq = 0;
static bool displayDirty = true;
static bool oledReady = false;
static bool cableMissingShown = false;
static bool supplyMissingShown = false;
static bool pcIdleShown = false;
static bool conditionStateValid = false;
static bool lastUsbPresentState = false;
static bool lastSupplyPresentState = false;
static int8_t shownUsbMode = -1;
static uint8_t standaloneConfigIndex = 0;
static uint8_t standaloneConfigPasses = 0;
static char lineBuffer[LINE_MAX];
// FS10 -> PC pending bytes only. Never reuse this buffer for PC -> FS10 traffic.
static uint8_t bridgeBuffer[BRIDGE_CHUNK_MAX];
static uint8_t usbTxPending = 0;
static uint8_t lineIndex = 0;
static char flowValue[20] = "--";
static char tempValue[20] = "--";
static char spValue[20] = "--";
static char drValue[20] = "--";
static char serialValue[20] = "--";
static char minValue[20] = "--";
static char maxValue[20] = "--";
static int8_t shownSwitchStatus = -2;
static int8_t lastValidSwitchStatus = -1;
static long custFlowMin10 = LONG_MIN;
static long custFlowMax10 = LONG_MIN;
static long relayLimit10 = LONG_MIN;

static void initUsbPresentSense() {
  DDRB &= ~_BV(4);  // PB4 / USB_PRESENT input
  PORTB &= ~_BV(4); // External VUSB divider drives this line.
}

static bool usbPresent() {
 // Physical VUSB sense, not USB enumeration, DTR or proof of PC communication.
 return (PINB & _BV(4)) != 0;
}

static void initSupplySense() {
  DDRB &= ~_BV(SUPPLY_24V_BIT);
  PORTB &= ~_BV(SUPPLY_24V_BIT);
}

static bool supply24Present() {
  // Digital presence indication only; it does not measure voltage or ripple.
  return (PINB & _BV(SUPPLY_24V_BIT)) != 0;
}

static void initRelaySense() {
  DDRF &= ~(_BV(RELAY_LO_BIT) | _BV(RELAY_HI_BIT));
  PORTF |= _BV(RELAY_LO_BIT) | _BV(RELAY_HI_BIT);
}

static void setRgbLed(bool red, bool green, bool blue) {
  digitalWrite(LED_RED_PIN, red ? LOW : HIGH);
  digitalWrite(LED_GRN_PIN, green ? LOW : HIGH);
  digitalWrite(LED_BLU_PIN, blue ? LOW : HIGH);
}

static void flashRgbLed(bool red, bool green, bool blue, uint16_t ms) {
  setRgbLed(red, green, blue);
  ledUntilMs = millis() + ms;
}

static void startTransitionBeep(bool loToHi) {
  tone(BUZZER_PIN, loToHi ? 560 : 870, 105);
  secondBeepFreq = loToHi ? 870 : 560;
  secondBeepMs = millis() + 145;
}

static void startUnplugBeep() {
  tone(BUZZER_PIN, 450, 180);
  secondBeepFreq = 450;
  secondBeepMs = millis() + 260;
}

static void playBootChirp() {
  // Audible proof that the controller started, even if the OLED is not fitted
  // or has a wiring problem.  This is deliberately different from the alarm.
  tone(BUZZER_PIN, 480, 160);
  delay(240);
  tone(BUZZER_PIN, 480, 160);
  delay(160);
  noTone(BUZZER_PIN);
}

static void serviceTransitionBeep() {
  if (secondBeepFreq == 0) return;
  if ((int32_t)(millis() - secondBeepMs) < 0) return;
  tone(BUZZER_PIN, secondBeepFreq, 105);
  secondBeepFreq = 0;
}

static char printableChar(char c) {
  if (c >= 'a' && c <= 'z') return c - 32;
  if (c >= 32 && c <= 126) return c;
  return ' ';
}

static bool updateField(const char *line, const char *key, char *dest, size_t destSize) {
  const char *p = strstr(line, key);
  if (p == NULL) return false;

  p += strlen(key);
  while (*p == ' ' || *p == ':' || *p == '=') p++;
  if (*p == '\0') return false;

  size_t i = 0;
  while (*p != '\0' && *p != ',' && *p != ';' && i < destSize - 1) {
    dest[i++] = *p++;
  }
  while (i > 0 && dest[i - 1] == ' ') i--;
  dest[i] = '\0';
  return i > 0;
}

constexpr uint8_t FORMAT_INT = 0;
constexpr uint8_t FORMAT_INT_PERCENT = 1;
constexpr uint8_t FORMAT_TEMP_TENTHS = 2;

#define ITEM_CUST_FLOW_MIN     107
#define ITEM_CUST_FLOW_MAX     108
#define ITEM_RELAY_LIMIT       112
#define ITEM_SERIAL_NUMBER      32
#define ITEM_DR_OHM_NORM       227
#define ITEM_FLOW_UNITS        233
#define ITEM_FLOW_PERCENT      234
#define ITEM_FLOW_PERCENT_ALT  235
#define ITEM_REF_TEMP          238

static bool copyRawNumericValue(const char *p, char *raw, size_t rawSize) {
  while (*p == ' ' || *p == ':' || *p == '=' || *p == '>') p++;
  if (*p == '\0') return false;

  size_t i = 0;
  bool sawDigit = false;
  while (*p != '\0' && i < rawSize - 1) {
    char c = *p;
    if ((c >= '0' && c <= '9') || c == '-' || c == '+') {
      sawDigit = true;
      raw[i++] = c;
    } else if (c == '.') {
      raw[i++] = c;
    } else if (c == 'E') {
      raw[i++] = c;
    } else {
      break;
    }
    p++;
  }
  if (!sawDigit) return false;
  raw[i] = '\0';
  return true;
}

static bool formatIntegerPercent(const char *raw, char *dest, size_t destSize) {
  long value = atol(raw);
  snprintf(dest, destSize, "%ld %%", value);
  return true;
}

static bool formatIntegerValue(const char *raw, char *dest, size_t destSize) {
  long value = atol(raw);
  snprintf(dest, destSize, "%ld", value);
  return true;
}

static bool formatTempTenths(const char *raw, char *dest, size_t destSize) {
  const char *dot = strchr(raw, '.');
  if (dot != NULL) {
    long whole = atol(raw);
    char tenth = '0';
    if (dot[1] >= '0' && dot[1] <= '9') tenth = dot[1];
    snprintf(dest, destSize, "%ld.%c", whole, tenth);
    return true;
  }

  long tempRaw = atol(raw);
  long whole = tempRaw / 10;
  long frac = labs(tempRaw % 10);
  snprintf(dest, destSize, "%ld.%ld", whole, frac);
  return true;
}

static bool parseScaledTenths(const char *p, long *value10Out) {
  // Display-only parser: normal instrument replies are scaled to tenths without
  // floats. This parser does not validate arbitrary-size numbers (see notes).
  while (*p == ' ' || *p == '=') p++;

  bool neg = false;
  if (*p == '-' || *p == '+') {
    neg = (*p == '-');
    p++;
  }

  long mantissa = 0;
  uint8_t decimals = 0;
  bool afterDot = false;
  bool sawDigit = false;

  while ((*p >= '0' && *p <= '9') || *p == '.') {
    if (*p == '.') {
      if (afterDot) break;
      afterDot = true;
      p++;
      continue;
    }

    sawDigit = true;
    mantissa = (mantissa * 10) + (*p - '0');
    if (afterDot) decimals++;
    p++;
  }

  if (!sawDigit) return false;

  int8_t exponent = 0;
  if (*p == 'E' || *p == 'e') {
    p++;
    bool expNeg = false;
    if (*p == '-' || *p == '+') {
      expNeg = (*p == '-');
      p++;
    }
    while (*p >= '0' && *p <= '9') {
      exponent = (exponent * 10) + (*p - '0');
      p++;
    }
    if (expNeg) exponent = -exponent;
  }

  int8_t scale = exponent + 1 - decimals; // +1 converts final value to tenths.
  long value10 = mantissa;
  while (scale > 0) {
    value10 *= 10;
    scale--;
  }
  while (scale < 0) {
    long divisor = 10;
    value10 = (value10 + (divisor / 2)) / divisor;
    scale++;
  }

  *value10Out = neg ? -value10 : value10;
  return true;
}

static bool parseItemLine(const char *line, int *itemOut, long *value10Out) {
  const char *sep = NULL;
  for (const char *p = line; *p != '\0'; p++) {
    if (*p == '=' || *p == '>') {
      sep = p;
      break;
    }
  }
  if (sep == NULL) return false;

  const char *itemEnd = sep;
  const char *itemStart = itemEnd;
  while (itemStart > line && isdigit((unsigned char)*(itemStart - 1))) itemStart--;
  if (itemStart == itemEnd) {
    itemStart = line;
    while (*itemStart == ' ') itemStart++;
    itemEnd = itemStart;
    while (isdigit((unsigned char)*itemEnd)) itemEnd++;
  }
  if (itemStart == itemEnd) return false;

  char itemBuf[8];
  uint8_t len = itemEnd - itemStart;
  if (len >= sizeof(itemBuf)) len = sizeof(itemBuf) - 1;
  memcpy(itemBuf, itemStart, len);
  itemBuf[len] = '\0';

  char *afterItem = NULL;
  long item = strtol(itemBuf, &afterItem, 10);
  if (afterItem == itemBuf) return false;

  long value10;
  if (!parseScaledTenths(sep + 1, &value10)) return false;

  *itemOut = (int)item;
  *value10Out = value10;
  return true;
}

static bool setPercentValue(char *dest, size_t destSize, long pct) {
  char next[20];
  snprintf(next, sizeof(next), "%ld %%", pct);
  if (strcmp(dest, next) == 0) return false;
  strncpy(dest, next, destSize - 1);
  dest[destSize - 1] = '\0';
  return true;
}

static bool setIntegerDisplayValue(char *dest, size_t destSize, long value) {
  char next[20];
  snprintf(next, sizeof(next), "%ld", value);
  if (strcmp(dest, next) == 0) return false;
  strncpy(dest, next, destSize - 1);
  dest[destSize - 1] = '\0';
  return true;
}

static bool setTenthsDisplayValue(char *dest, size_t destSize, long value10) {
  char next[20];
  snprintf(next, sizeof(next), "%ld.%ld", value10 / 10, labs(value10 % 10));
  if (strcmp(dest, next) == 0) return false;
  strncpy(dest, next, destSize - 1);
  dest[destSize - 1] = '\0';
  return true;
}

static bool computePercent(long value10, long min10, long max10, long *pctOut) {
  // Replies may arrive in any order; wait for the value as well as its range.
  if (value10 == LONG_MIN || min10 == LONG_MIN || max10 == LONG_MIN ||
      max10 == min10) return false;
  long span = max10 - min10;
  long pos = value10 - min10;
  long pct = ((pos * 100L) + (span / 2L)) / span;
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  *pctOut = pct;
  return true;
}

static bool updateSwitchPointPercent() {
  long pct;
  if (!computePercent(relayLimit10, custFlowMin10, custFlowMax10, &pct)) return false;
  return setPercentValue(spValue, sizeof(spValue), pct);
}

static bool updateFlowPercentDirect(long value10) {
  long pct = (value10 >= 0) ? ((value10 + 5) / 10) : ((value10 - 5) / 10);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return setPercentValue(flowValue, sizeof(flowValue), pct);
}

static bool serialBridgeQuiet() {
  return (uint32_t)(millis() - lastBridgeActivityMs) >= DISPLAY_QUIET_MS;
}

static void sendStandaloneCommand(const __FlashStringHelper *cmd) {
  // Only standalone polling may originate commands. Never call from USB mode.
  Serial1.print(cmd);
  Serial1.write('\r');
  lastBridgeActivityMs = millis();
}

static bool standaloneConfigComplete() {
  long pct = 0;
  return serialValue[0] != '-' && tempValue[0] != '-' && drValue[0] != '-' &&
         computePercent(relayLimit10, custFlowMin10, custFlowMax10, &pct);
}

static void sendStandaloneConfigItem(uint8_t index) {
  switch (index) {
    case 0:
      sendStandaloneCommand(F("*107"));
      break;
    case 1:
      sendStandaloneCommand(F("*108"));
      break;
    case 2:
      sendStandaloneCommand(F("*112"));
      break;
    case 3:
      sendStandaloneCommand(F("*238"));
      break;
    case 4:
      sendStandaloneCommand(F("*227"));
      break;
    case 5:
    default:
      sendStandaloneCommand(F("*032"));
      break;
  }
}

static bool parseFs10ItemLine(const char *line) {
  int item;
  long value10;
  if (!parseItemLine(line, &item, &value10)) return false;

  bool changed = false;
  switch (item) {
    case ITEM_SERIAL_NUMBER:
      changed |= setIntegerDisplayValue(serialValue, sizeof(serialValue), (value10 + 5) / 10);
      break;
    case ITEM_CUST_FLOW_MIN:
      if (custFlowMin10 != value10) {
        custFlowMin10 = value10;
        changed |= setTenthsDisplayValue(minValue, sizeof(minValue), value10);
      }
      break;
    case ITEM_CUST_FLOW_MAX:
      if (custFlowMax10 != value10) {
        custFlowMax10 = value10;
        changed |= setTenthsDisplayValue(maxValue, sizeof(maxValue), value10);
      }
      break;
    case ITEM_RELAY_LIMIT:
      if (relayLimit10 != value10) {
        relayLimit10 = value10;
        changed = true;
      }
      break;
    case ITEM_DR_OHM_NORM:
      changed |= setTenthsDisplayValue(drValue, sizeof(drValue), value10);
      break;
    case ITEM_FLOW_UNITS:
      break;
    case ITEM_FLOW_PERCENT:
    case ITEM_FLOW_PERCENT_ALT:
      changed |= updateFlowPercentDirect(value10);
      break;
    case ITEM_REF_TEMP: {
      char raw[20];
      snprintf(raw, sizeof(raw), "%ld.%ld", value10 / 10, labs(value10 % 10));
      changed |= formatTempTenths(raw, tempValue, sizeof(tempValue));
      break;
    }
    default:
      break;
  }

  if (changed) changed |= updateSwitchPointPercent();
  return changed;
}

static bool copyNumericValue(const char *p, char *dest, size_t destSize, uint8_t format) {
  char raw[20];
  if (!copyRawNumericValue(p, raw, sizeof(raw))) return false;

  switch (format) {
    case FORMAT_INT_PERCENT:
      return formatIntegerPercent(raw, dest, destSize);
    case FORMAT_TEMP_TENTHS:
      return formatTempTenths(raw, dest, destSize);
    case FORMAT_INT:
    default:
      return formatIntegerValue(raw, dest, destSize);
  }
}

static bool updateNumericField(const char *line, const char *key, char *dest, size_t destSize,
                               uint8_t format) {
  const char *p = strstr(line, key);
  if (p == NULL) return false;
  return copyNumericValue(p + strlen(key), dest, destSize, format);
}

static void parseLine(const char *line) {
  bool changed = false;
  changed |= parseFs10ItemLine(line);
  changed |= updateNumericField(line, "FLOW %", flowValue, sizeof(flowValue), FORMAT_INT_PERCENT);
  changed |= updateNumericField(line, "FLOW", flowValue, sizeof(flowValue), FORMAT_INT_PERCENT);
  changed |= updateNumericField(line, "TEMP", tempValue, sizeof(tempValue), FORMAT_TEMP_TENTHS);
  changed |= updateField(line, "SERIAL NUM", serialValue, sizeof(serialValue));
  changed |= updateField(line, "SERIAL", serialValue, sizeof(serialValue));
  changed |= updateField(line, "SN", serialValue, sizeof(serialValue));

  if (changed) {
    displayDirty = true;
  }
}

static void watchFs10Byte(char c) {
  // Normalize a separate display copy; forwarding retains the original bytes.
  // Keep at most 63 characters and parse that prefix at CR/LF. An unrecognized
  // reply or truncated display line must not be filtered from the PC stream.
  char printable = printableChar(c);

  if (c == '\r' || c == '\n') {
    if (lineIndex > 0) {
      lineBuffer[lineIndex] = '\0';
      parseLine(lineBuffer);
      lineIndex = 0;
    }
  } else if (lineIndex < LINE_MAX - 1) {
    lineBuffer[lineIndex++] = printable;
  }
}

static bool bridgeUsbToFs10() {
  uint8_t count = 0;

  // Leave incoming PC bytes queued until the UART has room. The reply buffer
  // belongs exclusively to the other direction, including between loop calls.
  while (count < BRIDGE_CHUNK_MAX && Serial.available() > 0 &&
         Serial1.availableForWrite() > 0) {
    Serial1.write((uint8_t)Serial.read());
    ++count;
  }

  if (count > 0) {
    lastBridgeActivityMs = millis();
    lastPcBridgeActivityMs = lastBridgeActivityMs;
  }
  return count > 0;
}

static int writeUsbAvailable(const uint8_t *data, uint8_t count) {
  // AVR-core-specific endpoint API bypasses Serial's possible DTR write gate.
  // Keep debug prints off Serial: any extra bytes corrupt the PC protocol.
  int written = 0;
  // Arduino AVR USB_Send() can otherwise wait 250 ms for a full endpoint.
  // Keep the space check and this small copy together so the USB SOF interrupt
  // cannot release the bank between them. Leave one byte unused to avoid the
  // core's extra zero-length-packet wait when a bank is filled exactly.
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    if (USBDevice.configured() && count > 0) {
      uint8_t space = USB_SendSpace(CDC_TX);
      if (space > 1) {
        if (count >= space) count = space - 1;
        written = USB_Send(CDC_TX | TRANSFER_RELEASE, data, count);
      }
    }
  }
  return written;
}

static bool flushUsbReply(bool *usbWriteFailed) {
  if (usbTxPending == 0) return false;
  int written = writeUsbAvailable(bridgeBuffer, usbTxPending);
  if (written < 0) {
    *usbWriteFailed = true;
    return false;
  }
  if (written == 0) return false; // Host backpressure: retry on the next loop.

  usbTxPending -= (uint8_t)written;
  memmove(bridgeBuffer, bridgeBuffer + written, usbTxPending);
  lastBridgeActivityMs = millis();
  return true;
}

static bool bridgeFs10ToUsb(bool *usbWriteFailed) {
  // Retain pending replies until USB accepts them; observe each UART byte once.
  // The hardware UART buffer is finite: indefinite host stalls are not lossless.
  bool moved = flushUsbReply(usbWriteFailed);
  uint8_t count = 0;

  while (Serial1.available() > 0 && usbTxPending < sizeof(bridgeBuffer) &&
         count < BRIDGE_CHUNK_MAX) {
    uint8_t value = (uint8_t)Serial1.read();
    bridgeBuffer[usbTxPending++] = value;
    watchFs10Byte((char)value); // Observe every reply without changing its bytes.
    ++count;
  }
  if (count > 0) {
    lastBridgeActivityMs = millis();
    lastFs10DataMs = lastBridgeActivityMs;
    moved = true;
  }
  if (flushUsbReply(usbWriteFailed)) moved = true;
  return moved;
}

static bool readFs10Standalone() {
  bool moved = false;
  while (Serial1.available() > 0) {
    watchFs10Byte((char)Serial1.read());
    lastBridgeActivityMs = millis();
    lastFs10DataMs = lastBridgeActivityMs;
    moved = true;
  }
  return moved;
}

static bool serviceStandalonePolling() {
  uint32_t now = millis();

  if (!standaloneConfigComplete() &&
      standaloneConfigPasses < STANDALONE_CONFIG_MAX_PASSES &&
      (standaloneConfigIndex == 0 ||
       (uint32_t)(now - lastStandaloneConfigMs) >= STANDALONE_CONFIG_MS) &&
      serialBridgeQuiet()) {
    sendStandaloneConfigItem(standaloneConfigIndex);
    standaloneConfigIndex++;
    if (standaloneConfigIndex >= 6) {
      standaloneConfigIndex = 0;
      standaloneConfigPasses++;
    }
    lastStandaloneConfigMs = now;
    lastStandaloneMeasMs = now;
    return true;
  }

  if ((uint32_t)(now - lastStandaloneMeasMs) >= STANDALONE_MEAS_MS && serialBridgeQuiet()) {
    sendStandaloneCommand(F("*meas"));
    lastStandaloneMeasMs = now;
    return true;
  }
  return false;
}

static void drawHeader();
static void drawStaticScreen();
static void clearShownValues();
static void showCableStatus();
static void showSupplyStatus();
static void showPcIdleStatus();
static void clearReadings();
static void initDisplay();
static void redrawMonitorScreen();
static void drawSwitchStatus();
static void updateDisplayIfDue();

static int8_t getSwitchStatus() {
  // Contact pair PF1:PF0 = 01 -> LO, 10 -> HI, 00/11 -> unknown.
  // This is a relay-contact indication, not an RS232 request/response test.
  uint8_t relayPins = PINF;
  uint8_t pf1 = (relayPins & _BV(1)) != 0;
  uint8_t pf0 = (relayPins & _BV(0)) != 0;
  uint8_t raw = (pf1 << 1) | pf0;
  if (raw == 1) return 0;
  if (raw == 2) return 1;
  return -1;
}

static bool serviceCableCheck() {
  uint32_t now = millis();

  if (getSwitchStatus() < 0) {
    if (relayUnknownSinceMs == 0) relayUnknownSinceMs = now;
    if (!cableMissingShown &&
        (uint32_t)(now - relayUnknownSinceMs) >= STANDALONE_CABLE_FAULT_MS) {
      startUnplugBeep();
      clearReadings();
      clearShownValues();
      drawStaticScreen();
      showCableStatus();
    }
    return true;
  }

  relayUnknownSinceMs = 0;
  if (cableMissingShown) {
    redrawMonitorScreen();
    displayDirty = true;
  }
  return false;
}

static bool serviceSupplyCheck() {
  if (!supply24Present()) {
    if (!supplyMissingShown) {
      clearReadings();
      clearShownValues();
      drawStaticScreen();
      showSupplyStatus();
    }
    return true;
  }

  if (supplyMissingShown) {
    redrawMonitorScreen();
    displayDirty = true;
  }
  return false;
}

static bool servicePcIdleCheck() {
  // Measures PC bytes forwarded, not FS10 reply age or whether the COM port is
  // open. The idle indication does not stop either direction of the USB bridge.
  if (!usbPresent()) {
    pcIdleShown = false;
    return false;
  }

  uint32_t now = millis();
  if ((uint32_t)(now - lastPcBridgeActivityMs) >= USB_PC_IDLE_MS) {
    if (!pcIdleShown) showPcIdleStatus();
    return true;
  }

  if (pcIdleShown) {
    redrawMonitorScreen();
    displayDirty = true;
  }
  return false;
}

static void serviceConditionChange() {
  bool usbNow = usbPresent();
  bool supplyNow = supply24Present();
  if (conditionStateValid &&
      usbNow == lastUsbPresentState &&
      supplyNow == lastSupplyPresentState) {
    return;
  }

  uint32_t now = millis();
  if (conditionStateValid) {
    bool usbChanged = usbNow != lastUsbPresentState;
    bool supplyChanged = supplyNow != lastSupplyPresentState;

    if (usbChanged || supplyChanged) {
      pcIdleShown = false;
      usbTxPending = 0; // Do not carry queued replies into a new power/USB session.
      // Only the sketch's pending buffer is cleared here. USB endpoint/host
      // queues and Serial1's core receive buffer are not explicitly drained.
      lineIndex = 0;
      lastBridgeActivityMs = now;
      lastPcBridgeActivityMs = now;
    }

    if (usbChanged) {
      standaloneConfigIndex = 0;
      standaloneConfigPasses = 0;
      redrawMonitorScreen();
    } else if (supplyChanged) {
      redrawMonitorScreen();
    }
  }

  conditionStateValid = true;
  lastUsbPresentState = usbNow;
  lastSupplyPresentState = supplyNow;
}

static void updateHeaderModeIfNeeded() {
  int8_t usbMode = usbPresent() ? 1 : 0;
  if (usbMode == shownUsbMode || cableMissingShown || supplyMissingShown || pcIdleShown) return;
  drawHeader();
  shownSwitchStatus = -2;
  displayDirty = true;
}

static void drawHeader() {
  shownUsbMode = usbPresent() ? 1 : 0;
  displayDirty = true;
}

static void printFormField(uint8_t y, const __FlashStringHelper *label,
                           const char *value, uint8_t valueChars) {
  display.setCursor(0, y);
  display.print(label);
  for (uint8_t i = 0; i < valueChars && value[i] != '\0'; ++i) {
    display.write(value[i]);
  }
}

static void drawFlowStateBox(int8_t status) {
  // This is a process-state indication derived from the NO/NC contact inputs,
  // not a claimed measurement of the relay coil itself.
  constexpr int16_t BOX_X = 86;
  constexpr int16_t BOX_Y = 0;
  constexpr int16_t BOX_W = 36;
  constexpr int16_t BOX_H = 64;

  display.drawRect(BOX_X, BOX_Y, BOX_W, BOX_H, SH110X_WHITE);
  display.setTextSize(1);
  display.setCursor(BOX_X + 4, 5);
  display.print(F("FLOW"));
  display.setTextSize(2);
  display.setCursor(BOX_X + 6, 20);
  if (status == 1) display.print(F("HI"));
  else if (status == 0) display.print(F("LO"));
  else display.print(F("--"));
  display.setTextSize(1);
  display.setCursor(BOX_X + 6, 44);
  display.print(usbPresent() ? F("USB") : F("SA"));
}

static void renderDisplay() {
  if (!oledReady) return;

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);

  // Single, always-on blank form. Supply, cable, and PC conditions may stop
  // values from arriving, but they never replace this page.
  int8_t status = getSwitchStatus();
  printFormField(0,  F("FLOW: "), flowValue, 9);
  printFormField(8,  F("TEMP: "), tempValue, 9);
  printFormField(16, F("SW PT: "), spValue, 8);
  printFormField(24, F("dR: "), drValue, 11);
  printFormField(32, F("MIN: "), minValue, 10);
  printFormField(40, F("MAX: "), maxValue, 10);
  printFormField(48, F("SN: "), serialValue, 11);
  display.setCursor(0, 56);
  display.print(F("24V: "));
  display.print(supply24Present() ? F("OK") : F("--"));
  drawFlowStateBox(status);

  display.display();
}

static void drawStaticScreen() {
  displayDirty = true;
}

static void clearShownValues() {
  shownSwitchStatus = -2;
  lastValidSwitchStatus = -1;
  displayDirty = true;
}

static void showCableStatus() {
  cableMissingShown = true;
  renderDisplay();
}

static void showSupplyStatus() {
  supplyMissingShown = true;
  renderDisplay();
}

static void showPcIdleStatus() {
  pcIdleShown = true;
  renderDisplay();
}

static void clearReadings() {
  strcpy(flowValue, "--");
  strcpy(tempValue, "--");
  strcpy(spValue, "--");
  strcpy(drValue, "--");
  strcpy(serialValue, "--");
  strcpy(minValue, "--");
  strcpy(maxValue, "--");
  custFlowMin10 = LONG_MIN;
  custFlowMax10 = LONG_MIN;
  relayLimit10 = LONG_MIN;
  standaloneConfigIndex = 0;
  standaloneConfigPasses = 0;
  displayDirty = true;
}

static void showStartupSplash() {
  if (!oledReady) return;

  display.clearDisplay();
  display.setTextColor(SH110X_WHITE);
  display.setTextSize(2);
  display.setCursor(16, 0);
  display.print(F("FCI FS10"));
  display.setTextSize(1);
  display.setCursor(18, 19);
  display.print(F("ATMEGA32U4 OLED"));
  display.setCursor(37, 34);
  display.print(F("FW BUILD"));
  display.setCursor(16, 46);
  display.print(F("2026-09-23 13:12"));
  // Load every visible pixel before enabling the panel. If a transfer fails,
  // leave it off and let normal instrument/USB operation continue.
  if (!display.writeStartupFrame()) {
    oledReady = false;
    return;
  }
  const uint8_t displayOn = SH110X_DISPLAYON;
  oledReady = display.oled_commandList(&displayOn, 1);
  if (!oledReady) return;
  delay(STARTUP_SPLASH_MS);
}

static void initDisplay() {
  Wire.begin();
  // A settling allowance, not a measurement of the OLED supply voltage.
  delay(OLED_POWERUP_DELAY_MS);
  oledReady = display.beginBlank(OLED_I2C_ADDRESS);
  showStartupSplash();
  clearShownValues();
  cableMissingShown = false;
  supplyMissingShown = false;
  pcIdleShown = false;
  drawStaticScreen();
  renderDisplay();
}

static void redrawMonitorScreen() {
  clearShownValues();
  cableMissingShown = false;
  supplyMissingShown = false;
  pcIdleShown = false;
  drawStaticScreen();
}

static void drawSwitchStatus() {
  int8_t status = getSwitchStatus();
  if (status == shownSwitchStatus) return;

  if (status >= 0) {
    if (lastValidSwitchStatus == 0 && status == 1) {
      startTransitionBeep(true);
    } else if (lastValidSwitchStatus == 1 && status == 0) {
      startTransitionBeep(false);
    }
    lastValidSwitchStatus = status;
  }

  shownSwitchStatus = status;
  displayDirty = true;
}

static void updateDisplayIfDue() {
  uint32_t now = millis();
  if (!displayDirty) return;
  if ((uint32_t)(now - lastDisplayMs) < DISPLAY_TICK_MS) return;
  if (!serialBridgeQuiet()) return;

  // Prioritize pending bridge traffic over a full OLED frame transfer.
  if (usbPresent() && (usbTxPending > 0 || Serial.available() > 0 ||
                       Serial1.available() > 0)) return;

  lastDisplayMs = now;
  renderDisplay();
  displayDirty = false;
}

void setup() {
  // Startup intentionally blocks for the chirp, OLED initialization and splash.
  // Normal bridging/polling begins only when setup returns.
  initUsbPresentSense();
  initSupplySense();
  initRelaySense();
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GRN_PIN, OUTPUT);
  pinMode(LED_BLU_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  // The single-page display does not read this button. Keep its fitted input
  // electrically defined with the pull-up enabled.
  DDRD &= ~_BV(PANEL_BUTTON_BIT);   // Set PD7 as input (clear bit)
  PORTD |= _BV(PANEL_BUTTON_BIT);   // Enable internal pull-up
  digitalWrite(BUZZER_PIN, LOW);
  setRgbLed(false, false, false);
  playBootChirp();

  // Native USB CDC is not a 115200-baud UART; Serial1 below sets the FS10 rate.
  Serial.begin(115200);
  Serial1.begin(FS10_BAUD, SERIAL_8N1);
  lastFs10DataMs = millis();
  lastPcBridgeActivityMs = millis();

  initDisplay();
  if (!usbPresent()) {
    standaloneConfigIndex = 0;
    standaloneConfigPasses = 0;
  }

  flashRgbLed(true, true, false, 200);
}

void loop() {
  serviceConditionChange();
  updateHeaderModeIfNeeded();
  bool supplyFault = serviceSupplyCheck();
  bool cableFault = false;
  if (!supplyFault) cableFault = serviceCableCheck();

  if (supplyFault) {
    // Deliberately preserve existing behavior: 24V loss pauses BOTH bridge
    // directions and polling. USB may remain enumerated from USB power, while
    // unread PC commands queue and may eventually backpressure the host.
    if (ledUntilMs != 0 && (int32_t)(millis() - ledUntilMs) >= 0) {
      setRgbLed(false, false, false);
      ledUntilMs = 0;
    }
    serviceTransitionBeep();
    return;
  }

  if (!usbPresent()) {
    readFs10Standalone();
    if (!cableFault) serviceStandalonePolling();
    if (ledUntilMs != 0 && (int32_t)(millis() - ledUntilMs) >= 0) {
      setRgbLed(false, false, false);
      ledUntilMs = 0;
    }
    if (!cableFault) updateDisplayIfDue();
    if (!cableFault && serialBridgeQuiet()) drawSwitchStatus();
    serviceTransitionBeep();
    return;
  }

  standaloneConfigIndex = 0;
  standaloneConfigPasses = 0;

  bool usbWriteFailed = false;
  // A cable/contact fault does NOT inhibit USB forwarding. The PC can still
  // send commands and handle missing replies itself. This differs from the
  // 24V gate above; changing either policy requires PC-application testing.
  bool pcToFs10 = bridgeUsbToFs10();
  bool fs10ToPc = bridgeFs10ToUsb(&usbWriteFailed);
  if (!cableFault) servicePcIdleCheck();
  // The PC owns requests in USB mode. Standalone polling must not inject
  // commands or suppress any replies while the PC is communicating.

  if (usbWriteFailed) {
    flashRgbLed(true, false, false, 120);
  } else if (pcToFs10) {
    flashRgbLed(true, true, false, 50);
  } else if (fs10ToPc) {
    flashRgbLed(false, false, true, 40);
  }

  if (ledUntilMs != 0 && (int32_t)(millis() - ledUntilMs) >= 0) {
    setRgbLed(false, false, false);
    ledUntilMs = 0;
  }

  if (!cableFault) updateDisplayIfDue();
  if (!cableFault && serialBridgeQuiet()) drawSwitchStatus();
  serviceTransitionBeep();
}
