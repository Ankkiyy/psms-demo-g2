# GitHub Copilot Instructions for Patient Security Management System (PSMS)

## Project Overview

This is an IoT-based Patient Security Management System for monitoring environmental conditions and security in healthcare facilities. The system uses ESP8266 microcontrollers with sensors, a Raspberry Pi backend server, and Google Cloud Platform for data storage.

## System Architecture

- **ESP8266 Sensor Nodes**: IoT devices with MQ-135 (air quality), DHT11/22 (temperature/humidity), and HC-SR04 (ultrasonic) sensors
- **Raspberry Pi Server**: Flask-based REST API with SQLite database for local storage
- **Google Cloud Platform**: Firestore for cloud data storage and Cloud Storage for backups
- **Communication**: WiFi-based HTTP POST from ESP8266 to server, HTTPS to GCP

## Technology Stack

### Hardware/Firmware
- **Platform**: ESP8266 (NodeMCU)
- **Language**: Arduino C++ (.ino files)
- **Libraries**: ESP8266WiFi, DHT sensor library, ArduinoJson
- **IDE**: Arduino IDE

### Backend Server
- **Platform**: Raspberry Pi (Debian-based Linux)
- **Language**: Python 3.7+
- **Framework**: Flask 3.0.0
- **Database**: SQLite3 (local), Google Cloud Firestore (cloud)
- **Key Libraries**: flask-cors, google-cloud-firestore, google-cloud-storage, python-dotenv

### Cloud Services
- Google Cloud Firestore (NoSQL database)
- Google Cloud Storage (backups)
- Service account authentication

## Coding Standards and Conventions

### Arduino/ESP8266 Firmware (`esp8266_firmware/`)

**Style Guidelines:**
- Use camelCase for variables: `deviceId`, `serverUrl`, `airQuality`
- Use UPPER_CASE for constants: `WIFI_SSID`, `SERVER_URL`
- Use descriptive function names: `connectToWiFi()`, `readSensorData()`
- Comment sensor pin assignments clearly
- Include error handling for sensor failures
- Use Serial.print() for debugging only, comment out in production

**Best Practices:**
- Always check WiFi connection status before sending data
- Implement retry logic for failed HTTP requests
- Use delay() appropriately to avoid flooding the server
- Validate sensor readings before transmission
- Include device identification in all transmissions
- Handle sensor warm-up time (especially MQ-135)

### Python/Flask Backend (`raspberry_pi_server/`)

**Style Guidelines:**
- Follow PEP 8 style guide
- Use snake_case for variables and functions: `device_id`, `sensor_data`, `get_latest_data()`
- Use descriptive names: `process_sensor_data()`, `check_alert_thresholds()`
- Type hints are encouraged for function parameters and returns
- Docstrings for all public functions using Google-style format

**Best Practices:**
- Always validate incoming JSON data
- Use environment variables for configuration (via .env file)
- Implement proper error handling with appropriate HTTP status codes
- Log all database operations
- Use transactions for related database operations
- Sanitize all user inputs
- Include CORS headers for API endpoints
- Use connection pooling for cloud services

**Database Conventions:**
- Use lowercase with underscores for table names: `sensor_data`, `alerts`, `devices`
- Use lowercase with underscores for column names: `device_id`, `air_quality`, `created_at`
- Always include timestamp fields
- Use proper indexes for frequently queried fields
- Include foreign key constraints where applicable

### Cloud Integration (`cloud_integration/`)

**Best Practices:**
- Always check for service account credentials before cloud operations
- Use batch operations for multiple writes to reduce API calls
- Implement exponential backoff for retries
- Handle authentication errors gracefully
- Validate data before sending to cloud
- Log all cloud operations for debugging

## Project Structure

```
psms-demo-g2/
├── .github/                    # GitHub configuration
│   └── copilot-instructions.md # This file
├── esp8266_firmware/          # ESP8266 Arduino firmware
│   ├── psms_sensor_node.ino   # Main firmware
│   └── README.md
├── raspberry_pi_server/       # Raspberry Pi backend
│   ├── app.py                 # Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template
│   └── README.md
├── cloud_integration/         # Google Cloud integration
│   ├── cloud_sync.py          # Cloud sync module
│   └── README.md
├── hardware_config/           # Hardware documentation
│   └── circuit_diagram.md
└── docs/                      # Additional documentation
    └── deployment_guide.md
```

## API Endpoints

When working with the Flask API, be aware of these endpoints:

- `GET /api/health` - Health check (returns status)
- `POST /api/sensor-data` - Submit sensor data from ESP8266
- `GET /api/latest-data` - Get latest readings (optional device_id filter)
- `GET /api/alerts` - Retrieve alerts (optional active filter)
- `GET /api/devices` - List registered devices
- `GET /api/statistics` - System statistics

## Data Format

**Sensor Data JSON Structure:**
```json
{
  "device_id": "ESP8266_PSMS_001",
  "location": "Room_101",
  "timestamp": 1234567890,
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

## Alert Thresholds

Default thresholds (configurable via .env):
- **Air Quality**: > 600 ppm (poor air quality)
- **Temperature**: > 30°C (high) or < 18°C (low)
- **Humidity**: > 70% (high)
- **Distance**: < 50 cm (door intrusion)

Alert types: `none`, `poor_air_quality`, `high_temperature`, `low_temperature`, `high_humidity`, `door_intrusion`

## Testing and Validation

### ESP8266 Testing
- Use Serial Monitor (115200 baud) for debugging
- Test each sensor individually before integration
- Verify WiFi connection before sensor testing
- Check HTTP response codes from server

### Backend Testing
- Use `test_api.sh` script for API testing
- Test with curl commands for individual endpoints
- Verify database operations with sqlite3 CLI
- Check logs for errors: `journalctl -u psms-server -f`

### Integration Testing
- Monitor end-to-end data flow: ESP8266 → Server → Database → Cloud
- Verify alert generation with threshold violations
- Test multiple device scenarios
- Validate cloud synchronization (if enabled)

## Building and Deployment

### ESP8266 Firmware
1. Install Arduino IDE and ESP8266 board support
2. Install required libraries via Library Manager
3. Update WiFi credentials and server URL in code
4. Set device ID and location
5. Upload to ESP8266 via USB
6. Monitor Serial output for verification

### Raspberry Pi Server
1. Install Python 3.7+ and pip
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure
4. Run server: `python app.py`
5. For production: Use systemd service for auto-start

### Cloud Integration (Optional)
1. Create Google Cloud project
2. Enable Firestore and Cloud Storage APIs
3. Create service account and download credentials JSON
4. Place credentials in secure location
5. Update .env with credentials path
6. Enable cloud sync: `CLOUD_SYNC_ENABLED=true`

## Security Considerations

### Critical Security Requirements
- **Never commit credentials**: Use .env files (excluded via .gitignore)
- **Secure service account keys**: Set proper file permissions (chmod 600)
- **WiFi security**: Use WPA2/WPA3 encryption
- **API security**: Implement authentication for production use
- **Input validation**: Always validate and sanitize inputs
- **HTTPS**: Use HTTPS for production (Let's Encrypt)
- **Firewall**: Configure UFW on Raspberry Pi

### Healthcare Data Compliance
- This is a monitoring system, not a medical device
- Be aware of HIPAA requirements if storing patient data
- Implement data retention policies
- Consider GDPR for EU deployments
- Document all security measures

## Common Tasks and Patterns

### Adding a New Sensor
1. Update ESP8266 firmware to read new sensor
2. Add sensor data to JSON payload
3. Update Flask API to handle new field
4. Add database column for new sensor data
5. Update cloud sync if needed
6. Document sensor specifications

### Adding a New Alert Type
1. Define threshold in .env file
2. Add check logic in Flask API
3. Update alert_type enum/validation
4. Update database schema if needed
5. Document alert conditions

### Modifying API Endpoint
1. Update Flask route in app.py
2. Update documentation in README.md
3. Update test_api.sh script
4. Test endpoint with curl
5. Document changes

## Error Handling Patterns

### ESP8266
- WiFi connection failures: Retry with exponential backoff
- HTTP errors: Log and retry with max attempts
- Sensor failures: Return default/error values, log issue
- Use built-in LED for status indication

### Python/Flask
- Database errors: Rollback transaction, log error, return 500
- Validation errors: Return 400 with error message
- Authentication errors: Return 401/403 as appropriate
- Cloud sync errors: Log and continue (don't block API)

## Environment Configuration

### Required .env Variables
```bash
FLASK_PORT=5000                    # Server port
CLOUD_SYNC_ENABLED=false           # Enable/disable cloud sync
GOOGLE_APPLICATION_CREDENTIALS=    # Path to GCP credentials
AIR_QUALITY_THRESHOLD=600          # Alert threshold
TEMP_HIGH_THRESHOLD=30.0           # High temperature alert
TEMP_LOW_THRESHOLD=18.0            # Low temperature alert
HUMIDITY_HIGH_THRESHOLD=70.0       # High humidity alert
DISTANCE_INTRUSION_THRESHOLD=50    # Door intrusion threshold (cm)
```

## Dependencies and Versions

### Python Dependencies
- Flask 3.0.0 (web framework)
- flask-cors 4.0.0 (CORS support)
- google-cloud-firestore 2.14.0 (Firestore client)
- google-cloud-storage 2.14.0 (Cloud Storage client)
- google-auth 2.25.2 (authentication)
- python-dotenv 1.0.0 (environment variables)
- pytz 2023.3 (timezone handling)

### Arduino Libraries
- ESP8266WiFi (built-in with ESP8266 board package)
- DHT sensor library by Adafruit
- ArduinoJson (for JSON serialization)

## Documentation Standards

- Keep README.md files up to date in each directory
- Document all configuration options
- Include example code snippets
- Add troubleshooting sections for common issues
- Update API documentation when endpoints change
- Include circuit diagrams for hardware changes

## Git Workflow

- Use descriptive commit messages
- Keep commits focused and atomic
- Don't commit .env files or credentials
- Don't commit compiled binaries
- Review .gitignore before committing
- Test changes before committing

## Performance Considerations

- ESP8266: Use appropriate delays between sensor readings (10-30 seconds)
- Server: Implement caching for frequently accessed data
- Database: Use indexes on device_id and timestamp columns
- Cloud: Use batch operations to reduce API calls
- Network: Handle retries gracefully to avoid flooding

## Maintenance and Monitoring

- Monitor disk space (SQLite database growth)
- Check system logs regularly
- Verify all devices are reporting
- Review alert patterns
- Update dependencies periodically
- Test backups and restore procedures

## Getting Help

- Check component-specific README files
- Review troubleshooting sections in documentation
- Check Serial Monitor output for ESP8266 issues
- Review Flask logs for server errors
- Verify network connectivity
- Consult hardware_config/circuit_diagram.md for wiring issues

## When Making Changes

1. **Understand the context**: Review related code and documentation
2. **Follow existing patterns**: Match the style and structure of existing code
3. **Test thoroughly**: Verify changes work as expected
4. **Update documentation**: Keep docs in sync with code changes
5. **Consider security**: Validate inputs, handle errors, protect credentials
6. **Think about scale**: Consider impact on multiple devices
7. **Maintain compatibility**: Don't break existing integrations
