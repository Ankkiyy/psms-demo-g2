# ESP8266 Firmware - PSMS Sensor Node

## Overview
This firmware enables the ESP8266 microcontroller to read data from multiple sensors and transmit it to the Raspberry Pi server for the Patient Security Management System.

## Hardware Requirements

### Microcontroller
- ESP8266 (NodeMCU, Wemos D1 Mini, or similar)

### Sensors
1. **MQ-135 Air Quality Sensor**
   - Detects air quality and harmful gases
   - Connected to analog pin A0

2. **DHT11 or DHT22 Temperature & Humidity Sensor**
   - Measures ambient temperature and humidity
   - Connected to digital pin D4

3. **HC-SR04 Ultrasonic Sensor**
   - Detects presence near unattended doors
   - Trigger pin: D5
   - Echo pin: D6

### Additional Components
- LED (optional) for status indication - D7
- 10kΩ resistor for MQ-135 (if needed)
- Breadboard and jumper wires
- 5V power supply

## Pin Connections

| Component | Pin | ESP8266 Pin |
|-----------|-----|-------------|
| MQ-135 (Analog Out) | A0 | A0 |
| MQ-135 (VCC) | 5V | VIN/5V |
| MQ-135 (GND) | GND | GND |
| DHT11/22 (Data) | D4 | GPIO2 |
| DHT11/22 (VCC) | 3.3V | 3.3V |
| DHT11/22 (GND) | GND | GND |
| HC-SR04 (Trig) | D5 | GPIO14 |
| HC-SR04 (Echo) | D6 | GPIO12 |
| HC-SR04 (VCC) | 5V | VIN/5V |
| HC-SR04 (GND) | GND | GND |
| Status LED | D7 | GPIO13 |

## Software Requirements

### Arduino IDE Setup
1. Install Arduino IDE (version 1.8.x or 2.x)
2. Add ESP8266 board support:
   - Go to File → Preferences
   - Add to "Additional Board Manager URLs":
     ```
     http://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Go to Tools → Board → Board Manager
   - Search for "esp8266" and install "ESP8266 by ESP8266 Community"

### Required Libraries
Install these libraries via Arduino IDE Library Manager (Sketch → Include Library → Manage Libraries):

1. **ESP8266WiFi** (included with ESP8266 board package)
2. **ESP8266HTTPClient** (included with ESP8266 board package)
3. **DHT sensor library** by Adafruit (version 1.4.4+)
4. **Adafruit Unified Sensor** (dependency for DHT)
5. **ArduinoJson** by Benoit Blanchon (version 6.x)

### Installation Command (PlatformIO alternative)
If using PlatformIO, add to `platformio.ini`:
```ini
[env:nodemcuv2]
platform = espressif8266
board = nodemcuv2
framework = arduino
lib_deps = 
    adafruit/DHT sensor library@^1.4.4
    adafruit/Adafruit Unified Sensor@^1.1.6
    bblanchon/ArduinoJson@^6.21.3
```

## Configuration

### 1. WiFi Configuration
Edit these lines in `psms_sensor_node.ino`:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

### 2. Server Configuration
Set your Raspberry Pi server IP address:
```cpp
const char* serverUrl = "http://RASPBERRY_PI_IP:5000/api/sensor-data";
```
Example: `http://192.168.1.100:5000/api/sensor-data`

### 3. Device Configuration
Customize device identification:
```cpp
String deviceId = "ESP8266_PSMS_001";  // Unique device ID
String location = "Room_101";           // Room/location identifier
```

### 4. Threshold Configuration
Adjust alert thresholds as needed:
```cpp
const int AIR_QUALITY_THRESHOLD = 600;      // MQ-135 threshold
const float TEMP_HIGH_THRESHOLD = 30.0;     // Temperature high (°C)
const float TEMP_LOW_THRESHOLD = 18.0;      // Temperature low (°C)
const float HUMIDITY_HIGH_THRESHOLD = 70.0; // Humidity high (%)
const int DOOR_DISTANCE_THRESHOLD = 50;     // Distance threshold (cm)
```

## Flashing the Firmware

### Using Arduino IDE
1. Open `psms_sensor_node.ino` in Arduino IDE
2. Select board: Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)
3. Select port: Tools → Port → (select your ESP8266 port)
4. Configure:
   - Upload Speed: 115200
   - CPU Frequency: 80 MHz
   - Flash Size: 4MB (FS:2MB OTA:~1019KB)
5. Click Upload button

### Using PlatformIO
```bash
pio run --target upload
```

## Testing

### Serial Monitor
1. Open Serial Monitor (Tools → Serial Monitor)
2. Set baud rate to 115200
3. You should see:
   - WiFi connection status
   - IP address
   - Sensor readings every 10 seconds
   - HTTP response codes

### Expected Output
```
=== PSMS Sensor Node Starting ===
Connecting to WiFi: YourNetwork
........
WiFi Connected!
IP Address: 192.168.1.50

Temperature: 25.30 °C
Humidity: 55.00 %
Air Quality (MQ-135): 342
Distance: 150 cm

Sending data to server...
Payload: {"device_id":"ESP8266_PSMS_001","location":"Room_101",...}
HTTP Response code: 200
Response: {"status":"success"}
```

## Troubleshooting

### WiFi Connection Issues
- Verify SSID and password
- Check WiFi signal strength
- Ensure 2.4GHz network (ESP8266 doesn't support 5GHz)

### Sensor Reading Errors
- **DHT11/22**: Check wiring, ensure proper power supply
- **MQ-135**: Allow 24-48 hours for initial heating/calibration
- **HC-SR04**: Ensure no obstacles within 2cm-400cm range

### HTTP Request Failures
- Verify Raspberry Pi server is running
- Check server IP address and port
- Ensure ESP8266 and Pi are on same network
- Check firewall settings on Raspberry Pi

### Upload Errors
- Hold FLASH button during upload (some boards)
- Try different USB cable
- Reduce upload speed to 57600

## Data Format

The sensor node sends JSON data in this format:
```json
{
  "device_id": "ESP8266_PSMS_001",
  "location": "Room_101",
  "timestamp": 123456789,
  "sensors": {
    "temperature": 25.3,
    "humidity": 55.0,
    "air_quality": 342,
    "distance": 150
  },
  "alert_type": "none",
  "alert_active": false
}
```

## Power Consumption
- Active (WiFi + Sensors): ~80mA @ 5V
- Consider using deep sleep mode for battery operation
- Recommended: 5V 1A power supply

## Security Notes
- Change default WiFi credentials
- Use HTTPS if transmitting sensitive data
- Consider implementing device authentication tokens
- Regularly update firmware for security patches

## Next Steps
1. Flash the firmware to your ESP8266
2. Monitor serial output to verify operation
3. Set up the Raspberry Pi server to receive data
4. Configure Google Cloud integration for data storage
