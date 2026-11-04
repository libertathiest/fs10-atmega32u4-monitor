// FS10 OLED bridge: stable USB CDC <-> RS232 bridge plus a compact status display.
// Requires the local Arduino AVR CDC.cpp patch that removes the DTR gate
// from Serial_::write() for CP2102-like behavior with the FS10 PC software.

#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Wire.h>
#include <ctype.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

constexpr uint32_t FS10_BAUD = 9600;
constexpr bool DEMO_MODE = false;  // Set to false for production
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
constexpr uint16_t USB_PRIVATE_DR_MS = 1500;
constexpr uint16_t USB_PRIVATE_QUIET_MS = 180;
constexpr uint16_t USB_PC_IDLE_MS = 5000;
constexpr uint8_t STANDALONE_CONFIG_MAX_PASSES = 4;
constexpr uint16_t OLED_POWERUP_DELAY_MS = 250;
constexpr uint16_t STARTUP_SPLASH_MS = 2500;

Adafruit_SH1106G display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);

static uint32_t ledUntilMs = 0;
static uint32_t lastDisplayMs = 0;
static uint32_t lastBridgeActivityMs = 0;
static uint32_t lastStandaloneMeasMs = 0;
static uint32_t lastStandaloneConfigMs = 0;
static uint32_t lastUsbPrivateDrMs = 0;
static uint32_t lastPcBridgeActivityMs = 0;
static uint32_t lastFs10DataMs = 0;
static uint32_t relayUnknownSinceMs = 0;
static uint32_t secondBeepMs = 0;
static uint16_t secondBeepFreq = 0;
static bool displayDirty = true;
static bool oledReady = false;
static bool attachUsbGraphMessageShown = false;
static bool cableMissingShown = false;
static bool supplyMissingShown = false;
static bool pcIdleShown = false;
static bool usbPrivateReplyActive = false;
static bool usbPrivateReplySawData = false;
static bool usbSerialRefreshPending = true;
static bool conditionStateValid = false;
static bool lastUsbPresentState = false;
static bool lastSupplyPresentState = false;
static int8_t shownUsbMode = -1;
static uint8_t standaloneConfigIndex = 0;
static uint8_t standaloneConfigPasses = 0;
static char lineBuffer[LINE_MAX];
static uint8_t bridgeBuffer[BRIDGE_CHUNK_MAX];
static uint8_t lineIndex = 0;
static uint32_t demoTickMs = 0;
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
 return (PINB & _BV(4)) != 0;
}

static void initSupplySense() {
  DDRB &= ~_BV(SUPPLY_24V_BIT);
  PORTB &= ~_BV(SUPPLY_24V_BIT);
}

static bool supply24Present() {
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
  if (min10 == LONG_MIN || max10 == LONG_MIN || max10 == min10) return false;
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
  bool moved = false;
  uint8_t count = 0;

  while (Serial.available() > 0 && count < sizeof(bridgeBuffer)) {
    uint8_t value = (uint8_t)Serial.read();
    bridgeBuffer[count++] = value;
  }

  if (count > 0) {
    Serial1.write(bridgeBuffer, count);
    lastBridgeActivityMs = millis();
    lastPcBridgeActivityMs = lastBridgeActivityMs;
    moved = true;
  }

  return moved;
}

static bool bridgeFs10ToUsb(bool *usbWriteFailed) {
  bool moved = false;
  uint8_t count = 0;

  while (Serial1.available() > 0 && count < sizeof(bridgeBuffer)) {
    uint8_t value = (uint8_t)Serial1.read();
    watchFs10Byte((char)value);
    if (usbPrivateReplyActive) {
      if (value == '\r' || value == '\n') {
        if (usbPrivateReplySawData) {
          usbPrivateReplyActive = false;
          usbPrivateReplySawData = false;
        }
      } else {
        usbPrivateReplySawData = true;
      }
    } else {
      bridgeBuffer[count++] = value;
    }
  }

  if (count > 0) {
    size_t written = Serial.write(bridgeBuffer, count);
    if (written != count) *usbWriteFailed = true;
    lastBridgeActivityMs = millis();
    lastFs10DataMs = lastBridgeActivityMs;
    moved = true;
  }

  return moved;
}

static bool serviceUsbPrivatePolling() {
  uint32_t now = millis();
  if (usbPrivateReplyActive) return false;
  if ((uint32_t)(now - lastBridgeActivityMs) < USB_PRIVATE_QUIET_MS) return false;

  if (usbSerialRefreshPending) {
    Serial1.print(F("*032"));
    usbSerialRefreshPending = false;
  } else {
    if ((uint32_t)(now - lastUsbPrivateDrMs) < USB_PRIVATE_DR_MS) return false;
    Serial1.print(F("*227"));
    lastUsbPrivateDrMs = now;
  }
  Serial1.write('\r');
  usbPrivateReplyActive = true;
  usbPrivateReplySawData = false;
  lastBridgeActivityMs = now;
  return true;
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

// Retained below for reference while the OLED rendering layer is validated.
#if 0
static void drawHeader() {
  tft.fillRect(0, 0, 320, 32, headerBgColor());
  tft.setTextSize(2);
  tft.setTextColor(FS10_WHITE, headerBgColor());
  if (usbPresent()) {
    tft.setCursor(10, 8);
    tft.print(F("USB BRIDGE PASSTHRU"));
    shownUsbMode = 1;
  } else {
    tft.setCursor(10, 8);
    tft.print(F("STAND ALONE MONITOR"));
    shownUsbMode = 0;
  }
}

static void drawStaticScreen() {
  tft.fillScreen(FS10_BLACK);
  drawHeader();
  tft.drawFastHLine(0, 33, 320, FS10_DARKGREY);
  tft.setTextSize(1);
  tft.setTextColor(FS10_WHITE, FS10_BLACK);
  tft.setCursor(8, 226);
  tft.print(F("FW build 2026-07-23 14:00"));
  tft.setTextSize(1);
  tft.setTextColor(FS10_DARKGREY, FS10_BLACK);
  tft.drawRect(READOUT_X, 58, READOUT_W, READOUT_H, FS10_DARKGREY);
  tft.drawRect(READOUT_X, 98, READOUT_W, READOUT_H, FS10_DARKGREY);
  tft.drawRect(READOUT_X, 138, READOUT_W, READOUT_H, FS10_DARKGREY);
  tft.drawRect(READOUT_X, 178, READOUT_W, READOUT_H, FS10_DARKGREY);
  tft.setTextSize(2);
  tft.setTextColor(FS10_WHITE, FS10_BLACK);
  tft.setCursor(READOUT_LABEL_X, 68);
  tft.print(F("Flow"));
  tft.setCursor(READOUT_LABEL_X, 108);
  tft.print(F("Temp"));
  tft.setTextSize(1);
  tft.setCursor(READOUT_LABEL_X, 149);
  tft.print(F("Switch"));
  tft.setCursor(READOUT_LABEL_X, 160);
  tft.print(F("Pt."));
  tft.setTextSize(2);
  tft.setCursor(READOUT_LABEL_X, 188);
  tft.print(F("dR"));
  for (uint8_t i = 0; i < 4; i++) {
    tft.drawRect(GRAPH_X + i, GRAPH_Y + i, GRAPH_SIZE - (i * 2), GRAPH_SIZE - (i * 2), FS10_GRAPH_BORDER);
  }
}

static void clearShownValues() {
  shownFlowValue[0] = '\0';
  shownTempValue[0] = '\0';
  shownSpValue[0] = '\0';
  shownDrValue[0] = '\0';
  shownSerialValue[0] = '\0';
  shownSwitchStatus = -2;
  lastValidSwitchStatus = -1;
  graphCount = 0;
  graphDrawnCount = 0;
  shownGraphSwitchPct = -1;
  displayDirty = true;
}

static void drawAttachUsbGraphMessage() {
  tft.fillRect(GRAPH_X + 4, GRAPH_Y + 4, GRAPH_SIZE - 8, GRAPH_SIZE - 8, FS10_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(FS10_WHITE, FS10_BLACK);
  tft.setCursor(GRAPH_X + 21, GRAPH_Y + 36);
  tft.print(F("Attach USB"));
  tft.setCursor(GRAPH_X + 14, GRAPH_Y + 68);
  tft.print(F("to PC to"));
  tft.setCursor(GRAPH_X + 9, GRAPH_Y + 100);
  tft.print(F("program FS10"));
  attachUsbGraphMessageShown = true;
}

static void drawCheckCableGraphMessage() {
  cableMissingShown = true;
  drawHeader();
  tft.fillRect(GRAPH_X + 4, GRAPH_Y + 4, GRAPH_SIZE - 8, GRAPH_SIZE - 8, FS10_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(FS10_WHITE, FS10_BLACK);
  tft.setCursor(GRAPH_X + 22, GRAPH_Y + 50);
  tft.print(F("Check FS10"));
  tft.setCursor(GRAPH_X + 46, GRAPH_Y + 82);
  tft.print(F("cable"));
}

static void drawSupplyGraphMessage() {
  supplyMissingShown = true;
  drawHeader();
  tft.fillRect(GRAPH_X + 4, GRAPH_Y + 4, GRAPH_SIZE - 8, GRAPH_SIZE - 8, FS10_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(FS10_WHITE, FS10_BLACK);
  tft.setCursor(GRAPH_X + 24, GRAPH_Y + 42);
  tft.print(F("Plug in"));
  tft.setCursor(GRAPH_X + 20, GRAPH_Y + 74);
  tft.print(F("24V supply"));
  tft.setCursor(GRAPH_X + 26, GRAPH_Y + 106);
  tft.print(F("for FS10"));
}

static void drawPcIdleGraphMessage() {
  pcIdleShown = true;
  tft.fillRect(GRAPH_X + 4, GRAPH_Y + 4, GRAPH_SIZE - 8, GRAPH_SIZE - 8, FS10_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(FS10_WHITE, FS10_BLACK);
  tft.setCursor(GRAPH_X + 28, GRAPH_Y + 42);
  tft.print(F("Check PC"));
  tft.setCursor(GRAPH_X + 16, GRAPH_Y + 74);
  tft.print(F("FS10 soft"));
  tft.setCursor(GRAPH_X + 42, GRAPH_Y + 106);
  tft.print(F("ware"));
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

static void initDisplay() {
  tft.init(240, 320);
  tft.setSPISpeed(16000000UL);
  tft.setRotation(1);
  applyTftColorOrder();
  tft.invertDisplay(false);
  clearShownValues();
  cableMissingShown = false;
  supplyMissingShown = false;
  pcIdleShown = false;
  drawStaticScreen();
  attachUsbGraphMessageShown = false;
}

static void redrawMonitorScreen() {
  clearShownValues();
  cableMissingShown = false;
  supplyMissingShown = false;
  pcIdleShown = false;
  drawStaticScreen();
  attachUsbGraphMessageShown = false;
}

static void drawValueRow(uint16_t y, const char *value, char *shown, size_t shownSize, uint16_t color) {
  if (strcmp(value, shown) == 0) return;

  tft.fillRect(READOUT_VALUE_X, y + 8, 58, 19, FS10_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(color, FS10_BLACK);
  tft.setCursor(READOUT_VALUE_X, y + 9);
  tft.print(value);

  strncpy(shown, value, shownSize - 1);
  shown[shownSize - 1] = '\0';
}

#endif

static void drawHeader();
static void drawStaticScreen();
static void clearShownValues();
static void drawCheckCableGraphMessage();
static void drawSupplyGraphMessage();
static void drawPcIdleGraphMessage();
static void clearReadings();
static void initDisplay();
static void redrawMonitorScreen();
static void drawSwitchStatus();
static void updateDisplayIfDue();

static int8_t getSwitchStatus() {
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
      drawCheckCableGraphMessage();
    }
    return true;
  }

  relayUnknownSinceMs = 0;
  if (cableMissingShown) {
    if (usbPresent()) usbSerialRefreshPending = true;
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
      drawSupplyGraphMessage();
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
  if (!usbPresent()) {
    pcIdleShown = false;
    return false;
  }

  uint32_t now = millis();
  if ((uint32_t)(now - lastPcBridgeActivityMs) >= USB_PC_IDLE_MS) {
    if (!pcIdleShown) drawPcIdleGraphMessage();
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
      attachUsbGraphMessageShown = false;
      usbPrivateReplyActive = false;
      usbPrivateReplySawData = false;
      lineIndex = 0;
      lastBridgeActivityMs = now;
      lastPcBridgeActivityMs = now;
    }

    if (usbChanged) {
      standaloneConfigIndex = 0;
      standaloneConfigPasses = 0;
      usbSerialRefreshPending = usbNow;
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

#if 0
static bool getDisplayedPercent(const char *text, uint8_t *pctOut) {
  long value = 0;
  if (!parseDisplayedInteger(text, &value)) return false;
  if (value < 0) value = 0;
  if (value > 100) value = 100;
  *pctOut = (uint8_t)value;
  return true;
}

static int16_t percentToGraphY(uint8_t pct) {
  uint16_t inner = GRAPH_PLOT_SIZE - 1;
  return GRAPH_Y + GRAPH_PLOT_INSET + inner - ((uint32_t)pct * inner) / 100;
}

static void drawFullGraph(int16_t switchPct) {
  tft.fillRect(GRAPH_X + 4, GRAPH_Y + 4, GRAPH_SIZE - 8, GRAPH_SIZE - 8, FS10_BLACK);

  if (switchPct >= 0) {
    int16_t ySwitch = percentToGraphY(switchPct);
    tft.drawFastHLine(GRAPH_X + GRAPH_PLOT_INSET, ySwitch, GRAPH_HISTORY_MAX, FS10_SWITCH_COLOR);
    tft.drawFastHLine(GRAPH_X + GRAPH_PLOT_INSET, ySwitch + 1, GRAPH_HISTORY_MAX, FS10_SWITCH_COLOR);
  }

  int16_t previousY = -1;
  for (uint8_t i = 0; i < graphCount; i++) {
    uint16_t x = GRAPH_X + GRAPH_PLOT_INSET + i;
    int16_t y = percentToGraphY(graphHistory[i]);
    if (previousY >= 0) {
      tft.drawLine(x - 1, previousY, x, y, FS10_GREEN);
      tft.drawLine(x - 1, previousY + 1, x, y + 1, FS10_GREEN);
    } else {
      tft.drawPixel(x, y, FS10_GREEN);
      tft.drawPixel(x, y + 1, FS10_GREEN);
    }
    previousY = y;
  }
  graphDrawnCount = graphCount;
  shownGraphSwitchPct = switchPct;
}

static void drawLatestGraphSegment(int16_t switchPct) {
  if (graphCount == 0) return;
  if (switchPct != shownGraphSwitchPct || graphDrawnCount > graphCount) {
    drawFullGraph(switchPct);
    return;
  }
  if (graphDrawnCount == 0) {
    uint16_t x = GRAPH_X + GRAPH_PLOT_INSET;
    int16_t y = percentToGraphY(graphHistory[0]);
    tft.drawPixel(x, y, FS10_GREEN);
    tft.drawPixel(x, y + 1, FS10_GREEN);
    graphDrawnCount = 1;
  }
  while (graphDrawnCount < graphCount) {
    uint8_t i = graphDrawnCount;
    uint16_t x = GRAPH_X + GRAPH_PLOT_INSET + i;
    int16_t previousY = percentToGraphY(graphHistory[i - 1]);
    int16_t y = percentToGraphY(graphHistory[i]);
    tft.drawLine(x - 1, previousY, x, y, FS10_GREEN);
    tft.drawLine(x - 1, previousY + 1, x, y + 1, FS10_GREEN);
    graphDrawnCount++;
  }
}

static void drawGraphColumn() {
  uint8_t flowPct = 0;
  if (!getDisplayedPercent(flowValue, &flowPct)) return;

  bool rolled = false;
  for (uint8_t step = 0; step < GRAPH_STEP_PIXELS; step++) {
    if (graphCount < GRAPH_HISTORY_MAX) {
      graphHistory[graphCount++] = flowPct;
    } else {
      graphCount = 0;
      graphDrawnCount = 0;
      graphHistory[graphCount++] = flowPct;
      rolled = true;
    }
  }

  uint8_t switchPct = 0;
  int16_t nextSwitchPct = getDisplayedPercent(spValue, &switchPct) ? switchPct : -1;
  if (rolled) {
    drawFullGraph(nextSwitchPct);
  } else {
    drawLatestGraphSegment(nextSwitchPct);
  }
}

static void drawBoldStatusText(uint16_t x, uint16_t y, const __FlashStringHelper *text,
                               uint16_t color) {
  tft.setTextSize(3);
  tft.setTextColor(color, relayHeaderBgColor());
  tft.setCursor(x, y);
  tft.print(text);
}

static void drawSwitchStatus() {
  int8_t status = getSwitchStatus();
  if (status == shownSwitchStatus) return;
  int8_t previousStatus = shownSwitchStatus;

  if (status >= 0 && previousStatus >= 0 && status != previousStatus) {
    tft.fillRect(248, 0, 72, 32, relayHeaderBgColor());
  } else if (status < 0 || previousStatus < 0) {
    tft.fillRect(248, 0, 72, 32, relayHeaderBgColor());
  }

  if (status < 0) {
    drawBoldStatusText(260, 5, F("--"), FS10_DARKGREY);
  } else if (status == 0) {
    drawBoldStatusText(260, 5, F("LO"), FS10_STATUS_LO);
  } else {
    drawBoldStatusText(260, 5, F("HI"), FS10_STATUS_HI);
  }

  if (status >= 0) {
    if (lastValidSwitchStatus == 0 && status == 1) {
      startTransitionBeep(true);
    } else if (lastValidSwitchStatus == 1 && status == 0) {
      startTransitionBeep(false);
    }
    lastValidSwitchStatus = status;
  }
  (void)previousStatus;

  shownSwitchStatus = status;
}

static void updateDisplayIfDue() {
  uint32_t now = millis();
  if (!displayDirty && strcmp(serialValue, shownSerialValue) == 0) return;
  if (now - lastDisplayMs < DISPLAY_TICK_MS) return;
  if (!serialBridgeQuiet()) return;

  lastDisplayMs = now;
  drawValueRow(58, flowValue, shownFlowValue, sizeof(shownFlowValue), FS10_GREEN);
  drawValueRow(98, tempValue, shownTempValue, sizeof(shownTempValue), FS10_CYAN);
  drawValueRow(138, spValue, shownSpValue, sizeof(shownSpValue), FS10_SWITCH_COLOR);
  drawValueRow(178, drValue, shownDrValue, sizeof(shownDrValue), FS10_WHITE);
  drawGraphColumn();

  if (strcmp(serialValue, shownSerialValue) != 0) {
    tft.fillRect(0, 216, 320, 24, FS10_BLACK);
    tft.setTextSize(1);
    tft.setTextColor(FS10_WHITE, FS10_BLACK);
    tft.setCursor(8, 226);
    tft.print(F("FW build 2026-07-23 14:00"));
    tft.setTextSize(2);
    tft.setCursor(184, 222);
    tft.print(F("SN "));
    tft.print(serialValue);
    strncpy(shownSerialValue, serialValue, sizeof(shownSerialValue) - 1);
    shownSerialValue[sizeof(shownSerialValue) - 1] = '\0';
  }

  displayDirty = false;
}

#endif

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

static void drawCheckCableGraphMessage() {
  cableMissingShown = true;
  renderDisplay();
}

static void drawSupplyGraphMessage() {
  supplyMissingShown = true;
  renderDisplay();
}

static void drawPcIdleGraphMessage() {
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
  display.print(F("2026-09-13 19:35"));
  display.display();
  delay(STARTUP_SPLASH_MS);
}

static void initDisplay() {
  Wire.begin();
  delay(OLED_POWERUP_DELAY_MS);
  oledReady = display.begin(OLED_I2C_ADDRESS, true);
  showStartupSplash();
  clearShownValues();
  cableMissingShown = false;
  supplyMissingShown = false;
  pcIdleShown = false;
  attachUsbGraphMessageShown = false;
  drawStaticScreen();
  renderDisplay();
}

static void redrawMonitorScreen() {
  clearShownValues();
  cableMissingShown = false;
  supplyMissingShown = false;
  pcIdleShown = false;
  attachUsbGraphMessageShown = false;
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

  lastDisplayMs = now;
  renderDisplay();
  displayDirty = false;
}

static void injectDemoData() {
  // Inject simulated FS10 response lines for display testing
  if (DEMO_MODE) {
    uint32_t now = millis();
    if ((uint32_t)(now - demoTickMs) >= 2000) {
      demoTickMs = now;

      // Simulate item responses: 107=min, 108=max, 112=relay limit, 227=dR, 238=temp, 032=serial
      static uint8_t demoStep = 0;
      char demoBuf[32];
      switch (demoStep++ % 6) {
        case 0:
          parseLine("107 = 0.0");  // Min flow
          break;
        case 1:
          parseLine("108 = 100.0");  // Max flow
          break;
        case 2:
          parseLine("112 = 45.5");  // Relay limit (switch point)
          break;
        case 3:
          parseLine("227 = 12.3");  // dR ohm norm
          break;
        case 4:
          parseLine("238 = 22.5");  // Ref temp
          break;
        case 5:
          parseLine("032 = 4567");  // Serial number
          break;
      }

      // Simulate flow percent changing
      static int8_t flowDir = 1;
      static long demoFlow = 300;  // 30.0%
      demoFlow += (flowDir * 50);
      if (demoFlow >= 1000) flowDir = -1;
      if (demoFlow <= 100) flowDir = 1;
      snprintf(demoBuf, sizeof(demoBuf), "FLOW %% = %ld.%ld", demoFlow / 10, demoFlow % 10);
      parseLine(demoBuf);
    }
  }
}

void setup() {
  initUsbPresentSense();
  initSupplySense();
  initRelaySense();
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GRN_PIN, OUTPUT);
  pinMode(LED_BLU_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  // Configure PANEL_BUTTON_BIT (PD7) as input with pull-up
  DDRD &= ~_BV(PANEL_BUTTON_BIT);   // Set PD7 as input (clear bit)
  PORTD |= _BV(PANEL_BUTTON_BIT);   // Enable internal pull-up
  digitalWrite(BUZZER_PIN, LOW);
  setRgbLed(false, false, false);
  playBootChirp();

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
  if (DEMO_MODE) injectDemoData();
  serviceConditionChange();
  updateHeaderModeIfNeeded();
  bool supplyFault = serviceSupplyCheck();
  bool cableFault = false;
  if (!supplyFault) cableFault = serviceCableCheck();

  if (supplyFault) {
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
  if (attachUsbGraphMessageShown) redrawMonitorScreen();

  bool usbWriteFailed = false;
  bool pcToFs10 = bridgeUsbToFs10();
  bool fs10ToPc = bridgeFs10ToUsb(&usbWriteFailed);
  bool pcIdleFault = false;
  if (!cableFault) pcIdleFault = servicePcIdleCheck();
  if (!pcToFs10 && !fs10ToPc && !usbWriteFailed && !cableFault && !pcIdleFault) {
    serviceUsbPrivatePolling();
  }

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

  if (!cableFault && !pcIdleFault) updateDisplayIfDue();
  if (!cableFault && serialBridgeQuiet()) drawSwitchStatus();
  serviceTransitionBeep();
}
