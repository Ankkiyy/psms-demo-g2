/*
 * Patient Security Management System (PSMS)
 * ESP8266 Sensor Node Firmware
 * 
 * Sensors:
 * - MQ-135: Air Quality Sensor (Analog Pin A0)
 * - DHT11/DHT22: Temperature & Humidity Sensor (Digital Pin D4)
 * - HC-SR04: Ultrasonic Sensor for Door Monitoring (Trigger: D5, Echo: D6)
 * 
 * Features:
 * - WiFi connectivity
 * - HTTP POST to Raspberry Pi server
 * - Real-time sensor data transmission
 * - Alert detection for threshold violations
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* serverUrl = "http://RASPBERRY_PI_IP:5000/api/sensor-data";

// Sensor Pins
#define MQ135_PIN A0          // MQ-135 Air Quality Sensor (Analog)
#define DHT_PIN D4            // DHT11/DHT22 Temperature & Humidity Sensor
#define TRIG_PIN D5           // HC-SR04 Ultrasonic Trigger Pin
#define ECHO_PIN D6           // HC-SR04 Ultrasonic Echo Pin
#define LED_PIN D7            // Status LED

// Sensor Configuration
#define DHTTYPE DHT11         // Change to DHT22 if using DHT22 sensor
DHT dht(DHT_PIN, DHTTYPE);

// Timing Configuration
unsigned long previousMillis = 0;
const long interval = 10000;  // Send data every 10 seconds

// Device Configuration
String deviceId = "ESP8266_PSMS_001";
String location = "Room_101";

// Threshold Configuration
const int AIR_QUALITY_THRESHOLD = 600;  // MQ-135 threshold for poor air quality
const float TEMP_HIGH_THRESHOLD = 30.0;  // Temperature high threshold (°C)
const float TEMP_LOW_THRESHOLD = 18.0;   // Temperature low threshold (°C)
const float HUMIDITY_HIGH_THRESHOLD = 70.0; // Humidity high threshold (%)
const int DOOR_DISTANCE_THRESHOLD = 50;  // Distance threshold for door monitoring (cm)

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n=== PSMS Sensor Node Starting ===");
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("=== Setup Complete ===\n");
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Reconnecting...");
    connectToWiFi();
  }
  
  // Read and send sensor data at intervals
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Blink LED to indicate reading
    digitalWrite(LED_PIN, HIGH);
    
    // Read all sensors
    float temperature = readTemperature();
    float humidity = readHumidity();
    int airQuality = readAirQuality();
    int distance = readDistance();
    
    // Check for alerts
    String alertType = checkAlerts(temperature, humidity, airQuality, distance);
    
    // Send data to server
    sendSensorData(temperature, humidity, airQuality, distance, alertType);
    
    digitalWrite(LED_PIN, LOW);
  }
  
  delay(100);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(LED_PIN, HIGH);
    delay(1000);
    digitalWrite(LED_PIN, LOW);
  } else {
    Serial.println("\nWiFi Connection Failed!");
  }
}

float readTemperature() {
  float temp = dht.readTemperature();
  if (isnan(temp)) {
    Serial.println("Failed to read temperature from DHT sensor!");
    return -999.0;
  }
  Serial.print("Temperature: ");
  Serial.print(temp);
  Serial.println(" °C");
  return temp;
}

float readHumidity() {
  float hum = dht.readHumidity();
  if (isnan(hum)) {
    Serial.println("Failed to read humidity from DHT sensor!");
    return -999.0;
  }
  Serial.print("Humidity: ");
  Serial.print(hum);
  Serial.println(" %");
  return hum;
}

int readAirQuality() {
  int airQualityValue = analogRead(MQ135_PIN);
  Serial.print("Air Quality (MQ-135): ");
  Serial.println(airQualityValue);
  return airQualityValue;
}

int readDistance() {
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read echo pulse
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // Timeout after 30ms
  
  // Calculate distance in cm
  int distance = duration * 0.034 / 2;
  
  // Validate reading
  if (distance == 0 || distance > 400) {
    Serial.println("Ultrasonic: Out of range");
    return -1;
  }
  
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  return distance;
}

String checkAlerts(float temp, float hum, int airQuality, int distance) {
  String alertType = "none";
  
  // Check air quality
  if (airQuality > AIR_QUALITY_THRESHOLD) {
    alertType = "poor_air_quality";
    Serial.println("ALERT: Poor air quality detected!");
  }
  
  // Check temperature
  if (temp > TEMP_HIGH_THRESHOLD) {
    alertType = "high_temperature";
    Serial.println("ALERT: High temperature detected!");
  } else if (temp < TEMP_LOW_THRESHOLD && temp > -999.0) {
    alertType = "low_temperature";
    Serial.println("ALERT: Low temperature detected!");
  }
  
  // Check humidity
  if (hum > HUMIDITY_HIGH_THRESHOLD) {
    alertType = "high_humidity";
    Serial.println("ALERT: High humidity detected!");
  }
  
  // Check door intrusion
  if (distance > 0 && distance < DOOR_DISTANCE_THRESHOLD) {
    alertType = "door_intrusion";
    Serial.println("ALERT: Unattended door activity detected!");
  }
  
  return alertType;
}

void sendSensorData(float temp, float hum, int airQuality, int distance, String alertType) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot send data: WiFi not connected");
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  
  Serial.println("\nSending data to server...");
  
  // Create JSON payload
  StaticJsonDocument<512> doc;
  doc["device_id"] = deviceId;
  doc["location"] = location;
  doc["timestamp"] = millis();
  
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["temperature"] = temp;
  sensors["humidity"] = hum;
  sensors["air_quality"] = airQuality;
  sensors["distance"] = distance;
  
  doc["alert_type"] = alertType;
  doc["alert_active"] = (alertType != "none");
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Payload: " + jsonString);
  
  // Send HTTP POST request
  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println("Response: " + response);
  } else {
    Serial.print("Error sending data. Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
  Serial.println();
}
