#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>

const char* const WIFI_SSID = "esp32_hotspot";
const char* const WIFI_PASSWORD = "pass_1234";
const IPAddress PI_IP(192, 168, 4, 2);
const char* const BOOT_SYNC_URL = "http://192.168.4.2:5000/api/boot-sync";
const char* const FLASK_BUTTON_URL = "http://192.168.4.2:5000/api/button-event";

constexpr uint8_t LED_18_PIN = 18;
constexpr uint8_t LED_19_PIN = 19;
constexpr uint8_t BUTTON_PIN = 21;

WiFiServer server(80);

void notifyBoot() {
  HTTPClient http;
  http.begin(BOOT_SYNC_URL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"device\":\"ESP32\",\"status\":\"rebooted\"}";
  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    http.getString();
  }
  http.end();
}

void notifyFlask(const String& stateStr) {
  HTTPClient http;
  http.begin(FLASK_BUTTON_URL);
  http.addHeader("Content-Type", "application/json");

  String eventText = "GPIO 21 Button " + stateStr;
  String payload = "{\"device\":\"ESP32\",\"pin\":21,\"state\":\"" + stateStr +
                   "\",\"event\":\"" + eventText + "\",\"source\":\"Physical Button\",\"device_id\":\"HW-GPIO21\"}";

  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    http.getString();
  }
  http.end();
}

void checkLedState() {
  WiFiClient client = server.available();
  if (!client) {
    return;
  }

  String request = "";
  while (client.connected() && !client.available()) {
    delay(1);
  }

  if (!client.connected()) {
    client.stop();
    return;
  }

  while (client.available()) {
    char c = client.read();
    request += c;
    if (request.length() > 1024) {
      break;
    }
  }

  String responseState = "OFF";

  if (request.indexOf("/api/gpio18/toggle") >= 0) {
    bool ledState = digitalRead(LED_18_PIN);
    digitalWrite(LED_18_PIN, !ledState);
    responseState = digitalRead(LED_18_PIN) ? "ON" : "OFF";
  } else if (request.indexOf("/api/gpio19/toggle") >= 0) {
    bool ledState = digitalRead(LED_19_PIN);
    digitalWrite(LED_19_PIN, !ledState);
    responseState = digitalRead(LED_19_PIN) ? "ON" : "OFF";
  }

  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.println();
  client.print("{\"status\":\"success\",\"state\":\"");
  client.print(responseState);
  client.print("\"}");
  client.println();

  client.stop();
}

void setup() {
  Serial.begin(115200);

  pinMode(LED_18_PIN, OUTPUT);
  pinMode(LED_19_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  digitalWrite(LED_18_PIN, HIGH);
  digitalWrite(LED_19_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_18_PIN, LOW);
  digitalWrite(LED_19_PIN, LOW);

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
  WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);

  Serial.printf("[WIFI] Hotspot Active! ESP32 IP: %s\n", WiFi.softAPIP().toString().c_str());

  notifyBoot();

  server.begin();
  server.setNoDelay(true);
}

void loop() {
  static bool lastButtonState = digitalRead(BUTTON_PIN);

  bool currentButtonState = digitalRead(BUTTON_PIN);
  if (currentButtonState != lastButtonState) {
    delay(20);
    currentButtonState = digitalRead(BUTTON_PIN);
    if (currentButtonState != lastButtonState) {
      lastButtonState = currentButtonState;
      notifyFlask(currentButtonState == LOW ? "Pressed" : "Released");
    }
  }

  checkLedState();
  delay(50);
}
