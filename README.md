# Patient Security Management System (PSMS)

## 🏥 Overview

The Patient Security Management System is an IoT-based solution for monitoring environmental conditions and security in healthcare facilities. It uses ESP8266 microcontrollers with multiple sensors to collect real-time data, processes it on a Raspberry Pi server, and stores it securely on Google Cloud Platform.

## ✨ Features

- **Real-time Environmental Monitoring**
  - Temperature and humidity tracking
  - Air quality measurement (MQ-135 sensor)
  - Door/movement detection with ultrasonic sensors

- **Multi-Device Support**
  - Support for multiple ESP8266 sensor nodes
  - Individual device tracking and management
  - Centralized data collection

- **Alert System**
  - Threshold-based alerts for environmental conditions
  - Door intrusion detection
  - Real-time notification system

- **Cloud Integration**
  - Google Cloud Firestore for scalable data storage
  - Cloud Storage for backups
  - Remote data access and analytics

- **REST API**
  - Easy integration with dashboards
  - Mobile app compatibility
  - Third-party service integration

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PSMS Architecture                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  ESP8266 Node 1  │         │  ESP8266 Node 2  │         │  ESP8266 Node N  │
│                  │         │                  │         │                  │
│  • MQ-135        │         │  • MQ-135        │         │  • MQ-135        │
│  • DHT11/22      │         │  • DHT11/22      │         │  • DHT11/22      │
│  • HC-SR04       │         │  • HC-SR04       │         │  • HC-SR04       │
│  • WiFi          │         │  • WiFi          │         │  • WiFi          │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
         └────────────────┬───────────┴────────────────────────────┘
                          │ HTTP POST (WiFi)
                          ↓
                ┌──────────────────────┐
                │   Raspberry Pi       │
                │   Backend Server     │
                │                      │
                │  • Flask REST API    │
                │  • SQLite Database   │
                │  • Alert Processing  │
                │  • Cloud Sync        │
                └──────────┬───────────┘
                           │ HTTPS
                           ↓
                ┌──────────────────────┐
                │  Google Cloud        │
                │  Platform            │
                │                      │
                │  • Firestore DB      │
                │  • Cloud Storage     │
                │  • Analytics         │
                └──────────────────────┘
```

## 📁 Repository Structure

```
psms-demo-g2/
├── esp8266_firmware/          # ESP8266 Arduino firmware
│   ├── psms_sensor_node.ino   # Main firmware code
│   └── README.md              # Firmware setup guide
│
├── raspberry_pi_server/       # Raspberry Pi backend
│   ├── app.py                 # Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment configuration
│   └── README.md              # Server setup guide
│
├── cloud_integration/         # Google Cloud integration
│   ├── cloud_sync.py          # Cloud sync module
│   └── README.md              # Cloud setup guide
│
├── hardware_config/           # Hardware documentation
│   └── circuit_diagram.md     # Circuit diagrams and assembly
│
├── docs/                      # Additional documentation
│   └── deployment_guide.md    # Deployment instructions
│
└── README.md                  # This file
```

## 🚀 Quick Start

### Hardware Required

**Per Sensor Node:**
- ESP8266 (NodeMCU or similar)
- MQ-135 Air Quality Sensor
- DHT11 or DHT22 Temperature/Humidity Sensor
- HC-SR04 Ultrasonic Sensor
- Breadboard and jumper wires
- 5V power supply

**Server:**
- Raspberry Pi 3B+ or newer (Pi 4 recommended)
- MicroSD card (16GB minimum, 32GB recommended)
- Power supply for Raspberry Pi

### Software Required
- Arduino IDE (for ESP8266 programming)
- Python 3.7+ (for Raspberry Pi server)
- Google Cloud Platform account (optional, for cloud features)

## 📋 Installation Steps

### Step 1: Hardware Setup
1. Follow the circuit diagram in `hardware_config/circuit_diagram.md`
2. Connect sensors to ESP8266 as specified
3. Ensure stable power supply

### Step 2: ESP8266 Firmware
1. Open `esp8266_firmware/psms_sensor_node.ino` in Arduino IDE
2. Install required libraries:
   - ESP8266WiFi
   - DHT sensor library
   - ArduinoJson
3. Update WiFi credentials and server IP
4. Upload to ESP8266
5. See `esp8266_firmware/README.md` for details

### Step 3: Raspberry Pi Server
1. Install Raspberry Pi OS
2. Clone this repository
3. Install Python dependencies:
   ```bash
   cd raspberry_pi_server
   pip install -r requirements.txt
   ```
4. Configure `.env` file
5. Run the server:
   ```bash
   python app.py
   ```
6. See `raspberry_pi_server/README.md` for details

### Step 4: Google Cloud Integration (Optional)
1. Create Google Cloud project
2. Enable Firestore and Cloud Storage APIs
3. Create service account and download credentials
4. Configure cloud sync in server
5. See `cloud_integration/README.md` for complete guide

## 🔧 Configuration

### ESP8266 Configuration
Edit `esp8266_firmware/psms_sensor_node.ino`:

```cpp
// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server URL
const char* serverUrl = "http://RASPBERRY_PI_IP:5000/api/sensor-data";

// Device identification
String deviceId = "ESP8266_PSMS_001";
String location = "Room_101";
```

### Server Configuration
Edit `raspberry_pi_server/.env`:

```bash
FLASK_PORT=5000
CLOUD_SYNC_ENABLED=false
AIR_QUALITY_THRESHOLD=600
TEMP_HIGH_THRESHOLD=30.0
```

## 📊 API Endpoints

### Health Check
```
GET /api/health
```

### Submit Sensor Data
```
POST /api/sensor-data
Content-Type: application/json
```

### Get Latest Data
```
GET /api/latest-data
GET /api/latest-data?device_id=ESP8266_PSMS_001
```

### Get Alerts
```
GET /api/alerts
GET /api/alerts?active=true
```

### Get Devices
```
GET /api/devices
```

### Get Statistics
```
GET /api/statistics
```

## 🔔 Alert Types

The system monitors and alerts for:

1. **Poor Air Quality**: MQ-135 reading above threshold
2. **High Temperature**: Temperature exceeds maximum
3. **Low Temperature**: Temperature below minimum
4. **High Humidity**: Humidity exceeds maximum
5. **Door Intrusion**: Ultrasonic sensor detects movement

## 📈 Monitoring

### View Sensor Data
```bash
# Latest readings
curl http://localhost:5000/api/latest-data

# Active alerts
curl http://localhost:5000/api/alerts?active=true

# Statistics
curl http://localhost:5000/api/statistics
```

### Database Access
```bash
# SQLite database
sqlite3 raspberry_pi_server/psms_data.db

# Query recent data
SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
```

## 🔒 Security Considerations

1. **Network Security**
   - Use strong WiFi passwords
   - Consider VPN for remote access
   - Enable firewall on Raspberry Pi

2. **Data Security**
   - Secure Google Cloud credentials
   - Use HTTPS for production
   - Regular security updates

3. **Physical Security**
   - Protect hardware from tampering
   - Use enclosures for sensors
   - Secure power supplies

## 🐛 Troubleshooting

### ESP8266 Won't Connect
- Verify WiFi credentials
- Check 2.4GHz network availability
- Ensure server IP is correct
- Check Serial Monitor for errors

### No Data Received
- Verify server is running
- Check network connectivity
- Confirm firewall allows port 5000
- Review server logs

### Sensor Reading Errors
- Check sensor connections
- Verify power supply
- Allow MQ-135 warm-up time (24-48 hours)
- Test sensors individually

## 📚 Documentation

Detailed documentation for each component:

- **[ESP8266 Firmware Guide](esp8266_firmware/README.md)** - Complete firmware setup and configuration
- **[Raspberry Pi Server Guide](raspberry_pi_server/README.md)** - Server installation and management
- **[Cloud Integration Guide](cloud_integration/README.md)** - Google Cloud Platform setup
- **[Hardware Setup Guide](hardware_config/circuit_diagram.md)** - Circuit diagrams and assembly

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests.

## 📄 License

This project is available for educational and non-commercial use.

## 🙏 Acknowledgments

- ESP8266 Community
- Adafruit for sensor libraries
- Google Cloud Platform
- Raspberry Pi Foundation

## 📞 Support

For questions and support:
- Open an issue in the repository
- Check the documentation in each component folder
- Review troubleshooting sections

## 🎯 Future Enhancements

- [ ] Web dashboard for real-time monitoring
- [ ] Mobile application (iOS/Android)
- [ ] Email/SMS alert notifications
- [ ] Machine learning for predictive analytics
- [ ] Multi-tenancy support
- [ ] Advanced data visualization
- [ ] Integration with hospital management systems
- [ ] Voice alerts via smart speakers

## 📊 System Requirements Summary

### Minimum Requirements
- ESP8266 development board
- 3 sensors per node (MQ-135, DHT11, HC-SR04)
- Raspberry Pi 3B+ with 1GB RAM
- 16GB SD card
- Stable internet connection

### Recommended Setup
- ESP8266 (multiple nodes)
- DHT22 for better accuracy
- Raspberry Pi 4 with 4GB RAM
- 32GB SD card (Class 10)
- UPS backup for continuous operation
- Google Cloud Platform integration

## 💰 Cost Estimate

- ESP8266 Node: $25-40 per location
- Raspberry Pi Setup: $60-100
- Cloud Costs: $0-10/month (depending on usage)
- **Total Initial Investment**: $100-200
- **Monthly Operating Cost**: $0-10 (cloud only)

---

**Note**: This is a monitoring and alerting system. For critical medical applications, please consult with certified medical device manufacturers and comply with healthcare regulations.
