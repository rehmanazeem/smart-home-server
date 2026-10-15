#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "secrets.h"
#include <EEPROM.h>

// Pin definitions
const int relay1Pin = D1;
const int relay2Pin = D2;
const int btn1Pin = D6;
const int btn2Pin = D5;

// Button debounce variables
#define DEBOUNCE_TIME 50 // ms
#define EEPROM_SIZE 2    // 1 byte per relay

// Relay state
bool relay1State = false;
bool relay2State = false;

// Struct to store debounce state for each button
struct ButtonState {
  int lastSteadyState = HIGH;
  int lastFlickerableState = HIGH;
  unsigned long lastDebounceTime = 0;
};
ButtonState btn1State;
ButtonState btn2State;

// WiFi and MQTT clients
WiFiClientSecure espClient;
PubSubClient client(espClient);

// Function prototypes
void handleButtonPress(int btnInputPin, int outputPin, bool& state, ButtonState& btnState, const char* relayNum, const char* topic);
void callback(char* topic, byte* payload, unsigned int length);
void reconnect();
void saveRelayStates();

void setup() {
  pinMode(btn1Pin, INPUT_PULLUP);
  pinMode(btn2Pin, INPUT_PULLUP);
  pinMode(relay1Pin, OUTPUT);
  pinMode(relay2Pin, OUTPUT);

  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.println("\nConnecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nConnected! IP: ");
  Serial.println(WiFi.localIP());

  // For HiveMQ Cloud, skip certificate validation (for demo; for production, use proper CA cert)
  espClient.setInsecure();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  EEPROM.begin(EEPROM_SIZE);
  relay1State = EEPROM.read(0);
  relay2State = EEPROM.read(1);
  digitalWrite(relay1Pin, relay1State ? HIGH : LOW);
  digitalWrite(relay2Pin, relay2State ? HIGH : LOW);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  handleButtonPress(btn1Pin, relay1Pin, relay1State, btn1State, "1", "home/relay1/state");
  handleButtonPress(btn2Pin, relay2Pin, relay2State, btn2State, "2", "home/relay2/state");
}

// MQTT callback: handle incoming set commands
void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  msg.trim();

  Serial.print("MQTT message received on topic [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(msg);

  if (String(topic) == "home/relay1/set") {
    bool prevState = relay1State;
    if (msg == "ON") relay1State = true;
    else if (msg == "OFF") relay1State = false;
    else if (msg == "TOGGLE") relay1State = !relay1State;
    digitalWrite(relay1Pin, relay1State ? HIGH : LOW);
    saveRelayStates(); // <-- Save to EEPROM
    if (prevState != relay1State) {
      client.publish("home/relay1/state", relay1State ? "ON" : "OFF", true);
      Serial.print("MQTT: relay1 changed from ");
      Serial.print(prevState ? "ON" : "OFF");
      Serial.print(" to ");
      Serial.println(relay1State ? "ON" : "OFF");
    }
    else if (prevState == relay1State) {
      Serial.println("No change");
    }
  }
  if (String(topic) == "home/relay2/set") {
    bool prevState = relay2State;
    if (msg == "ON") relay2State = true;
    else if (msg == "OFF") relay2State = false;
    else if (msg == "TOGGLE") relay2State = !relay2State;
    digitalWrite(relay2Pin, relay2State ? HIGH : LOW);
    saveRelayStates(); // <-- Save to EEPROM
    if (prevState != relay2State) {
      client.publish("home/relay2/state", relay2State ? "ON" : "OFF", true);
      Serial.print("MQTT: relay2 changed from ");
      Serial.print(prevState ? "ON" : "OFF");
      Serial.print(" to ");
      Serial.println(relay2State ? "ON" : "OFF");
    }
    else if (prevState == relay2State) {
      Serial.println("No change");
    }
  }
}

// MQTT reconnect logic
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP8266Relay", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      client.subscribe("home/relay1/set");
      client.subscribe("home/relay2/set");
      // Publish initial states
      client.publish("home/relay1/state", relay1State ? "ON" : "OFF", true);
      client.publish("home/relay2/state", relay2State ? "ON" : "OFF", true);
      Serial.println("Subscribed to topics and published initial states.");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// Modular handleButtonPress function with MQTT state publish
void handleButtonPress(int btnInputPin, int outputPin, bool& state, ButtonState& btnState, const char* relayNum, const char* topic) {
  int buttonState = digitalRead(btnInputPin);

  if (buttonState != btnState.lastFlickerableState) {
    btnState.lastDebounceTime = millis();
    btnState.lastFlickerableState = buttonState;
  }

  if ((millis() - btnState.lastDebounceTime) > DEBOUNCE_TIME) {
    if (btnState.lastSteadyState == HIGH && buttonState == LOW) {
      state = !state;
      digitalWrite(outputPin, state ? HIGH : LOW);
      saveRelayStates(); // <-- Save to EEPROM
      Serial.print("BUTTON: Relay ");
      Serial.print(relayNum);
      Serial.print(" toggled to ");
      Serial.println(state ? "ON" : "OFF");
      client.publish(topic, state ? "ON" : "OFF", true);
    }
    btnState.lastSteadyState = buttonState;
  }
}

void saveRelayStates() {
  EEPROM.write(0, relay1State);
  EEPROM.write(1, relay2State);
  EEPROM.commit();
}