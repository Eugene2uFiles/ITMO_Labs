/*
 * Arduino принимает строку от BLE-модуля и выводит смесь в Serial Monitor.
 * Формат строки от приложения:
 *   MIX:2.50,1.25,1.25,0.00;SUGAR:1.50
 */

#include <SoftwareSerial.h>
#include <stdlib.h>
#include <string.h>

// Сначала задаю пины и скорость обмена.
static const uint8_t BLE_RX_PIN = 10;
static const uint8_t BLE_TX_PIN = 11;
static const unsigned long USB_BAUD = 9600;
static const unsigned long BLE_BAUD = 9600;

// Если символ конца строки не пришёл, строка обработается по времени.
static const unsigned long LINE_TIMEOUT_MS = 700;
static const size_t LINE_BUFFER_SIZE = 96;

// Создаю serial-порт для BLE-модуля.
SoftwareSerial bluetooth(BLE_RX_PIN, BLE_TX_PIN);

// Хранение данных заварки.
struct TeaMix {
  float teaGrams[4];
  float sugarGrams;
};


static char lineBuffer[LINE_BUFFER_SIZE];
static size_t lineLength = 0;
static unsigned long lastByteAt = 0;

static void resetLineBuffer();
static bool parseNumber(const char *text, float &value);
static bool parseMixLine(char *line, TeaMix &mix);
static void printMix(const TeaMix &mix);
static void processCompletedLine();
static void processIncomingByte(char symbol);

// При старте включаю USB Serial и связь с BLE-модулем.
void setup() {
  Serial.begin(USB_BAUD);
  bluetooth.begin(BLE_BAUD);
  resetLineBuffer();
  delay(1000);

  Serial.println(F("Tea mixer BLE receiver ready"));
  Serial.print(F("BLE RX pin: "));
  Serial.println(BLE_RX_PIN);
  Serial.print(F("BLE UART baud: "));
  Serial.println(BLE_BAUD);
}

// Основной цикл постоянно проверяет, пришли ли данные.
void loop() {
  // 1. Читаю всё, что пришло от BLE.
  while (bluetooth.available() > 0) {
    processIncomingByte(static_cast<char>(bluetooth.read()));
  }

  // 2. Строка пришла без \n, считываю через паузу.
  if (
    lineLength > 0
    && lastByteAt > 0
    && millis() - lastByteAt >= LINE_TIMEOUT_MS
  ) {
    Serial.println(F("BLE: таймаут строки, обработка без \\n"));
    processCompletedLine();
  }

  // 3. Ручная проверка.
  while (Serial.available() > 0) {
    bluetooth.write(Serial.read());
  }
}

// Очищаю буфер.
static void resetLineBuffer() {
  lineLength = 0;
  lineBuffer[0] = '\0';
  lastByteAt = 0;
}

// Перевожу кусок текста в число.
static bool parseNumber(const char *text, float &value) {
  if (text == NULL || *text == '\0') {
    return false;
  }

  char *endPointer = NULL;
  value = strtod(text, &endPointer);
  return endPointer != text && *endPointer == '\0';
}

// Разбираю строку
static bool parseMixLine(char *line, TeaMix &mix) {
  static const char MIX_PREFIX[] = "MIX:";
  static const char SUGAR_SEPARATOR[] = ";SUGAR:";

  if (strncmp(line, MIX_PREFIX, strlen(MIX_PREFIX)) != 0) {
    return false;
  }

  char *sugarSeparator = strstr(line, SUGAR_SEPARATOR);
  if (sugarSeparator == NULL) {
    return false;
  }

  // Разделяю строку на части
  *sugarSeparator = '\0';
  char *sugarText = sugarSeparator + strlen(SUGAR_SEPARATOR);

  // По очереди достаю 4 значения чая.
  char *savePointer = NULL;
  char *token = strtok_r(line + strlen(MIX_PREFIX), ",", &savePointer);
  for (uint8_t index = 0; index < 4; index++) {
    if (token == NULL || !parseNumber(token, mix.teaGrams[index])) {
      return false;
    }
    token = strtok_r(NULL, ",", &savePointer);
  }

  if (token != NULL) {
    return false;
  }

  return parseNumber(sugarText, mix.sugarGrams);
}

// Печатаю готовую смесь в строку.
static void printMix(const TeaMix &mix) {
  Serial.println(F("--- BLE: получена смесь ---"));
  for (uint8_t index = 0; index < 4; index++) {
    Serial.print(F("Чай "));
    Serial.print(index + 1);
    Serial.print(F(": "));
    Serial.print(mix.teaGrams[index], 2);
    Serial.println(F(" г"));
  }
  Serial.print(F("Сахар: "));
  Serial.print(mix.sugarGrams, 2);
  Serial.println(F(" г"));
}

// Сюда попадаем, когда строка полностью собрана.
static void processCompletedLine() {
  if (lineLength == 0) {
    return;
  }

  lineBuffer[lineLength] = '\0';
  Serial.print(F("BLE строка: "));
  Serial.println(lineBuffer);

  TeaMix mix;
  if (parseMixLine(lineBuffer, mix)) {
    printMix(mix);
    bluetooth.print(F("OK\n"));
  } else {
    Serial.println(F("Ошибка формата BLE-строки"));
    bluetooth.print(F("ERR\n"));
  }

  resetLineBuffer();
}

// Каждый принятый символ сначала попадает сюда.
static void processIncomingByte(char symbol) {
  Serial.print(F("RX byte="));
  Serial.print(static_cast<uint8_t>(symbol));
  Serial.print(F(" char="));

  if (symbol >= 32 && symbol <= 126) {
    Serial.println(symbol);
  } else if (symbol == '\n') {
    Serial.println(F("\\n"));
  } else if (symbol == '\r') {
    Serial.println(F("\\r"));
  } else {
    Serial.println(F("?"));
  }

  // \r пропускаю, а \n считаю концом строки.
  if (symbol == '\r') {
    return;
  }

  if (symbol == '\n') {
    processCompletedLine();
    return;
  }

  if (lineLength + 1 >= LINE_BUFFER_SIZE) {
    Serial.println(F("Ошибка: буфер BLE переполнен"));
    bluetooth.print(F("ERR:OVERFLOW\n"));
    resetLineBuffer();
    return;
  }

  lineBuffer[lineLength++] = symbol;
  lineBuffer[lineLength] = '\0';
  lastByteAt = millis();
}
