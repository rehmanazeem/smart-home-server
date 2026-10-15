#include <ESP8266WiFi.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// TCP server
WiFiServer server(8080);

// Pin definitions
const int relay1Pin = D1;  // GPIO5
const int relay2Pin = D2;  // GPIO5
const int btn1Pin = D6;            // GPIO12
const int btn2Pin = D5;            // GPIO14

// Button debounce variables
#define DEBOUNCE_TIME 50 // Debounce time in milliseconds

// Relay state
bool relay1State = false; // Current relay state (false = OFF, true = ON)
bool relay2State = false; // Current relay state (false = OFF, true = ON)

// Struct to store debounce state for each button
struct ButtonState {
  int lastSteadyState = HIGH;       // Previous steady state of the button
  int lastFlickerableState = HIGH;  // Previous flickerable state of the button
  unsigned long lastDebounceTime = 0;  // Last debounce time
};

// Create separate debounce states for each button
ButtonState btn1State;
ButtonState btn2State;

// Function prototypes
void handleButtonPress(int btnInputPin, int outputPin, bool& state, ButtonState& btnState, const char* relayNum);
void handleTCPClient();

void setup() {
  // Pin setup
  pinMode(btn1Pin, INPUT_PULLUP);
  pinMode(btn2Pin, INPUT_PULLUP);
  pinMode(relay1Pin, OUTPUT);
  pinMode(relay2Pin, OUTPUT);

  // Initialize relay state
  digitalWrite(relay1Pin, LOW);  // Relay OFF initially (active LOW)
  digitalWrite(relay2Pin, LOW);  // Relay OFF initially (active LOW)

  // Start Serial communication
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.println("");
  Serial.println("=============================");
  Serial.println("Connecting to WiFi");
  Serial.println("=============================");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("=============================");
  Serial.print("Connected! IP: ");
  Serial.println(WiFi.localIP());
  Serial.println("=============================");

  // Start the TCP server
  server.begin();

}

void loop() {
  // Handle TCP client
  handleTCPClient();

  // Handle button press for the relay
  handleButtonPress(btn1Pin, relay1Pin, relay1State, btn1State, "1");
  handleButtonPress(btn2Pin, relay2Pin, relay2State, btn2State, "2");
}

void handleTCPClient() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client connected.");

    while (client.connected()) {
      if (client.available()) {
        String data = client.readStringUntil('\n');
        data.trim();
        Serial.print("Received: ");
        Serial.println(data);

        int number = data.toInt();
        String response;

        if (data.length() == 0 || (number == 0 && data != "0")) {
          response = "Invalid input.";
        } 
        else if (number == 1) {
          relay1State = !relay1State;
          digitalWrite(relay1Pin, relay1State ? HIGH : LOW);
          response = String("COMMAND {SWITCH : RELAY 1} > CURRENT STATE :") + (relay1State ? "OFF" : "ON");
        } 
        else if (number == 2) {
          relay2State = !relay2State;
          digitalWrite(relay2Pin, relay2State ? HIGH : LOW);  // Relay OFF
          response = String("COMMAND {SWITCH : RELAY 2} > CURRENT STATE :") + (relay2State ? "OFF" : "ON");
        } 
        else if (number == 99) {
          response = "COMMAND {99:EXIT CLIENT}";
          client.println(response);
          Serial.println("Replied: " + response);

          Serial.println("Client disconnected.");
          break;
        } 
        else {
          response = "INVALID COMMAND!";
        }

        client.println(response);
        Serial.println("Replied: " + response);
      }

      // Handle button press for the relay
      handleButtonPress(btn1Pin, relay1Pin, relay1State, btn1State, "1");
      handleButtonPress(btn2Pin, relay2Pin, relay2State, btn2State, "2");
    }
  }
}

// Modular handleButtonPress function with independent debounce state
void handleButtonPress(int btnInputPin, int outputPin, bool& state, ButtonState& btnState, const char* relayNum) {
  // Read the current state of the button
  int buttonState = digitalRead(btnInputPin);

  // Check if the button state has changed
  if (buttonState != btnState.lastFlickerableState) {
    // Reset debounce timer
    btnState.lastDebounceTime = millis();
    btnState.lastFlickerableState = buttonState;
  }

  // If the button state is stable for longer than the debounce time
  if ((millis() - btnState.lastDebounceTime) > DEBOUNCE_TIME) {
    // If the button state has changed
    if (btnState.lastSteadyState == HIGH && buttonState == LOW) {
      // Serial.println(" pressed. Toggling relay state.");
      
      state = !state;  // Toggle relay state
      digitalWrite(outputPin, state ? HIGH : LOW);  // Update relay state
      Serial.println(String("COMMAND {SWITCH : RELAY ") + relayNum + "} > CURRENT STATE :" + (state ? "OFF" : "ON"));
    }

    // Update the last steady state
    btnState.lastSteadyState = buttonState;
  }
}