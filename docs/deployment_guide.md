# PSMS Deployment Guide

## Complete End-to-End Deployment

This guide walks you through deploying a complete Patient Security Management System from scratch.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Phase 1: Hardware Assembly](#phase-1-hardware-assembly)
3. [Phase 2: ESP8266 Setup](#phase-2-esp8266-setup)
4. [Phase 3: Raspberry Pi Setup](#phase-3-raspberry-pi-setup)
5. [Phase 4: Cloud Integration](#phase-4-cloud-integration)
6. [Phase 5: Testing and Validation](#phase-5-testing-and-validation)
7. [Phase 6: Production Deployment](#phase-6-production-deployment)
8. [Maintenance and Monitoring](#maintenance-and-monitoring)

## Pre-Deployment Checklist

### Materials and Tools
- [ ] All hardware components (see hardware list)
- [ ] Soldering iron and solder (if needed)
- [ ] Multimeter for testing
- [ ] Computer with Arduino IDE installed
- [ ] Raspberry Pi with SD card and power supply
- [ ] WiFi network with stable internet
- [ ] Google Cloud account (credit card for verification)

### Software Preparation
- [ ] Arduino IDE installed
- [ ] Python 3.7+ installed on Raspberry Pi
- [ ] Git installed
- [ ] Google Cloud SDK (optional)

### Network Preparation
- [ ] WiFi SSID and password ready
- [ ] Static IP for Raspberry Pi (recommended)
- [ ] Port 5000 available on Raspberry Pi
- [ ] Firewall rules documented

## Phase 1: Hardware Assembly

### Step 1.1: Prepare Workspace
```
1. Clear workspace with good lighting
2. Anti-static mat recommended
3. Organize components by type
4. Keep documentation accessible
```

### Step 1.2: Assemble First Sensor Node

Follow this order to minimize troubleshooting:

**A. Test ESP8266 Board**
```cpp
// Upload simple blink test
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}
void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}
```

**B. Connect and Test DHT Sensor**
1. Connect VCC to 3.3V
2. Connect Data to D4
3. Connect GND to GND
4. Upload DHT test sketch
5. Verify readings in Serial Monitor

**C. Connect and Test MQ-135**
1. Connect VCC to 5V (VIN)
2. Connect GND to GND
3. Connect AOUT to A0
4. Allow 24-48 hours for warm-up
5. Read analog values

**D. Connect and Test HC-SR04**
1. Connect VCC to 5V
2. Connect GND to GND
3. Connect Trig to D5
4. Connect Echo to D6 (with voltage divider)
5. Test distance readings

**E. Add Status LED**
1. Connect LED anode to D7 via 220Ω resistor
2. Connect LED cathode to GND
3. Test with simple blink

### Step 1.3: Document Configuration
```
Node ID: ESP8266_PSMS_001
Location: Room 101
MAC Address: [Find from Serial Monitor]
Sensors Installed:
  - MQ-135: A0
  - DHT22: D4
  - HC-SR04: D5 (Trig), D6 (Echo)
  - LED: D7
```

### Step 1.4: Create Enclosure
1. Drill ventilation holes for MQ-135
2. Mount sensors securely
3. Label enclosure with node ID
4. Ensure cables strain relief

## Phase 2: ESP8266 Setup

### Step 2.1: Install Arduino IDE Libraries

**Method 1: Library Manager**
```
1. Open Arduino IDE
2. Sketch → Include Library → Manage Libraries
3. Search and install:
   - "DHT sensor library" by Adafruit
   - "Adafruit Unified Sensor"
   - "ArduinoJson" by Benoit Blanchon (v6.x)
```

**Method 2: Manual Installation**
```bash
cd ~/Arduino/libraries/
git clone https://github.com/adafruit/DHT-sensor-library.git
git clone https://github.com/adafruit/Adafruit_Sensor.git
git clone https://github.com/bblanchon/ArduinoJson.git
```

### Step 2.2: Configure Firmware

Open `esp8266_firmware/psms_sensor_node.ino` and update:

```cpp
// WiFi Configuration
const char* ssid = "YourHospitalWiFi";
const char* password = "YourSecurePassword";

// Server Configuration (use Raspberry Pi IP)
const char* serverUrl = "http://192.168.1.100:5000/api/sensor-data";

// Device Configuration
String deviceId = "ESP8266_PSMS_001";  // Unique per device
String location = "Room_101";           // Physical location

// Threshold Configuration (adjust based on requirements)
const int AIR_QUALITY_THRESHOLD = 600;
const float TEMP_HIGH_THRESHOLD = 30.0;
const float TEMP_LOW_THRESHOLD = 18.0;
const float HUMIDITY_HIGH_THRESHOLD = 70.0;
const int DOOR_DISTANCE_THRESHOLD = 50;
```

### Step 2.3: Upload Firmware

```
1. Connect ESP8266 via USB
2. Select board: Tools → Board → NodeMCU 1.0 (ESP-12E)
3. Select port: Tools → Port → /dev/ttyUSB0 (Linux) or COM3 (Windows)
4. Set upload speed: 115200
5. Click Upload
6. Wait for "Done uploading"
```

### Step 2.4: Verify Operation

```
1. Open Serial Monitor (Ctrl+Shift+M)
2. Set baud rate to 115200
3. Press RESET on ESP8266
4. Verify output:
   ✓ WiFi connection successful
   ✓ IP address assigned
   ✓ Sensor readings appear
   ✓ No error messages
```

Expected output:
```
=== PSMS Sensor Node Starting ===
Connecting to WiFi: YourHospitalWiFi
........
WiFi Connected!
IP Address: 192.168.1.50

Temperature: 24.5 °C
Humidity: 52.0 %
Air Quality (MQ-135): 345
Distance: 175 cm

Sending data to server...
Error sending data. Error code: -1  # Normal if server not running yet
```

## Phase 3: Raspberry Pi Setup

### Step 3.1: Initial Raspberry Pi Setup

**Install Raspberry Pi OS**
```bash
# Using Raspberry Pi Imager
1. Download from https://www.raspberrypi.org/software/
2. Select "Raspberry Pi OS (64-bit)" or Lite version
3. Select SD card
4. Configure WiFi and SSH (Advanced options)
5. Write to SD card
```

**First Boot**
```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Default password: raspberry

# Change default password
passwd

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Set timezone
sudo timedatectl set-timezone America/New_York  # Adjust for your location

# Set static IP (optional but recommended)
sudo nano /etc/dhcpcd.conf
# Add:
# interface wlan0
# static ip_address=192.168.1.100/24
# static routers=192.168.1.1
# static domain_name_servers=192.168.1.1 8.8.8.8
```

### Step 3.2: Install Dependencies

```bash
# Install Python and tools
sudo apt-get install -y python3 python3-pip python3-venv git sqlite3

# Install system libraries
sudo apt-get install -y build-essential libssl-dev libffi-dev
```

### Step 3.3: Clone and Setup Repository

```bash
# Clone repository
cd ~
git clone https://github.com/Ankkiyy/psms-demo-g2.git
cd psms-demo-g2/raspberry_pi_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3.4: Configure Server

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Update `.env`:
```bash
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# Start with cloud sync disabled
CLOUD_SYNC_ENABLED=false

# Adjust thresholds as needed
AIR_QUALITY_THRESHOLD=600
TEMP_HIGH_THRESHOLD=30.0
TEMP_LOW_THRESHOLD=18.0
HUMIDITY_HIGH_THRESHOLD=70.0
DISTANCE_THRESHOLD=50
```

### Step 3.5: Test Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run server
python app.py

# Expected output:
# * Running on http://0.0.0.0:5000
# Database initialized successfully
# Starting PSMS Server on 0.0.0.0:5000
```

**Test from another terminal:**
```bash
curl http://localhost:5000/api/health
# Expected: {"status":"healthy",...}
```

### Step 3.6: Setup as System Service

```bash
# Create service file
sudo nano /etc/systemd/system/psms-server.service
```

Add content:
```ini
[Unit]
Description=PSMS Backend Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/psms-demo-g2/raspberry_pi_server
Environment="PATH=/home/pi/psms-demo-g2/raspberry_pi_server/venv/bin"
ExecStart=/home/pi/psms-demo-g2/raspberry_pi_server/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable psms-server
sudo systemctl start psms-server
sudo systemctl status psms-server
```

### Step 3.7: Configure Firewall

```bash
# Install UFW if not present
sudo apt-get install -y ufw

# Allow SSH
sudo ufw allow 22

# Allow Flask server
sudo ufw allow 5000

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Phase 4: Cloud Integration

### Step 4.1: Create Google Cloud Project

```bash
# Using web console at https://console.cloud.google.com/
1. Create new project: "psms-iot-system"
2. Note the Project ID: psms-iot-system-xxxxx
3. Enable billing (credit card required)
```

### Step 4.2: Enable APIs

```bash
# Install gcloud CLI (optional, can use web console)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Enable required APIs
gcloud services enable firestore.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### Step 4.3: Setup Firestore

```
1. Navigate to Firestore in Cloud Console
2. Click "Create Database"
3. Choose "Production mode"
4. Select region (e.g., us-central1)
5. Click "Create"
```

### Step 4.4: Create Service Account

```
1. Go to IAM & Admin → Service Accounts
2. Create Service Account:
   Name: psms-backend-service
   Roles: 
     - Cloud Datastore User
     - Storage Object Admin
3. Create key (JSON format)
4. Download: psms-iot-system-xxxxx-xxxxxxxxx.json
```

### Step 4.5: Transfer Credentials to Raspberry Pi

```bash
# From your computer
scp ~/Downloads/psms-iot-system-*.json pi@192.168.1.100:~/psms-demo-g2/raspberry_pi_server/service-account-key.json

# On Raspberry Pi
cd ~/psms-demo-g2/raspberry_pi_server
chmod 600 service-account-key.json
```

### Step 4.6: Create Storage Bucket

```bash
# Using gcloud
gcloud storage buckets create gs://psms-backup-bucket-xxxxx \
  --location=us-central1

# Or use web console: Storage → Create Bucket
```

### Step 4.7: Update Server Configuration

```bash
nano ~/psms-demo-g2/raspberry_pi_server/.env
```

Update:
```bash
CLOUD_SYNC_ENABLED=true
GCP_PROJECT_ID=psms-iot-system-xxxxx
GOOGLE_APPLICATION_CREDENTIALS=/home/pi/psms-demo-g2/raspberry_pi_server/service-account-key.json
FIRESTORE_COLLECTION=psms_sensor_data
GCS_BUCKET_NAME=psms-backup-bucket-xxxxx
```

### Step 4.8: Test Cloud Connection

```bash
cd ~/psms-demo-g2/cloud_integration
python cloud_sync.py

# Expected output:
# Firestore: ✓
# Storage: ✓
```

### Step 4.9: Restart Server

```bash
sudo systemctl restart psms-server
sudo systemctl status psms-server
```

## Phase 5: Testing and Validation

### Test 5.1: End-to-End Data Flow

```bash
# Monitor server logs
sudo journalctl -u psms-server -f

# ESP8266 should send data every 10 seconds
# Look for log entries:
# "Sensor data saved: ID=X, Device=ESP8266_PSMS_001"
# "Data synced to Firestore: ..."
```

### Test 5.2: Verify Data in Database

```bash
# Local SQLite database
sqlite3 ~/psms-demo-g2/raspberry_pi_server/psms_data.db

sqlite> SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5;
sqlite> SELECT * FROM devices;
sqlite> .quit
```

### Test 5.3: Verify Data in Cloud

```
1. Open Firestore in Cloud Console
2. Navigate to psms_sensor_data collection
3. Verify documents are being created
4. Check timestamps are recent
```

### Test 5.4: API Testing

```bash
# Latest data
curl http://192.168.1.100:5000/api/latest-data | jq

# Specific device
curl http://192.168.1.100:5000/api/latest-data?device_id=ESP8266_PSMS_001 | jq

# Alerts
curl http://192.168.1.100:5000/api/alerts | jq

# Devices
curl http://192.168.1.100:5000/api/devices | jq

# Statistics
curl http://192.168.1.100:5000/api/statistics | jq
```

### Test 5.5: Alert Testing

**Trigger temperature alert:**
```
1. Hold DHT sensor to warm it up
2. Watch for "ALERT: High temperature detected!" in ESP8266 serial monitor
3. Verify alert in database: SELECT * FROM alerts WHERE resolved=0;
4. Check API: curl http://192.168.1.100:5000/api/alerts?active=true
```

**Trigger door alert:**
```
1. Wave hand in front of ultrasonic sensor
2. Move within threshold distance (< 50cm)
3. Verify "ALERT: Unattended door activity detected!"
4. Check alerts in system
```

## Phase 6: Production Deployment

### Deploy 6.1: Scale to Multiple Nodes

For each additional node:
```
1. Assemble hardware (Phase 1)
2. Upload firmware with unique device_id and location
3. Test connectivity
4. Mount in designated location
5. Document in inventory
```

Inventory template:
```
Device ID: ESP8266_PSMS_002
Location: Room 102
MAC: XX:XX:XX:XX:XX:XX
Installation Date: 2024-01-15
Installed By: John Doe
Notes: Door sensor facing entrance
```

### Deploy 6.2: Physical Installation

**Sensor Node Placement:**
```
1. MQ-135: Mount at breathing height (1.2-1.5m)
2. DHT sensor: Away from direct sunlight/HVAC
3. Ultrasonic: Above door frame, centered on path
4. Power: Use proper power supply, cable management
5. Enclosure: Secure mounting, tamper-resistant
```

**Cable Management:**
```
1. Use cable ties for organization
2. Protect cables from foot traffic
3. Label power supplies
4. Document cable routes
```

### Deploy 6.3: Network Optimization

```bash
# On Raspberry Pi, check connection quality
ping -c 100 192.168.1.50  # ESP8266 IP

# Optimize WiFi
# Use 2.4GHz network with good coverage
# Consider WiFi repeater if signal weak
# Monitor signal strength: iwconfig wlan0
```

### Deploy 6.4: Backup Strategy

```bash
# Automatic database backup script
cat > /home/pi/backup_database.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/pi/psms-backups"
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp /home/pi/psms-demo-g2/raspberry_pi_server/psms_data.db \
   $BACKUP_DIR/psms_data_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "psms_data_*.db" -mtime +30 -delete

echo "Backup completed: psms_data_$DATE.db"
EOF

chmod +x /home/pi/backup_database.sh

# Schedule daily backup at 2 AM
crontab -e
# Add: 0 2 * * * /home/pi/backup_database.sh
```

### Deploy 6.5: Monitoring Setup

```bash
# Install monitoring tools
sudo apt-get install -y htop iotop

# Create monitoring script
cat > /home/pi/check_psms.sh << 'EOF'
#!/bin/bash
echo "=== PSMS System Status ==="
echo "Date: $(date)"
echo ""

# Service status
echo "Service Status:"
systemctl is-active psms-server && echo "✓ Server running" || echo "✗ Server stopped"

# Disk space
echo ""
echo "Disk Usage:"
df -h /home | tail -1

# Memory
echo ""
echo "Memory Usage:"
free -h | grep Mem

# Recent errors
echo ""
echo "Recent Errors (last 10):"
sudo journalctl -u psms-server --no-pager -p err -n 10

# Database stats
echo ""
echo "Database Statistics:"
sqlite3 /home/pi/psms-demo-g2/raspberry_pi_server/psms_data.db \
  "SELECT COUNT(*) || ' total readings' FROM sensor_data;"
sqlite3 /home/pi/psms-demo-g2/raspberry_pi_server/psms_data.db \
  "SELECT COUNT(*) || ' active alerts' FROM alerts WHERE resolved=0;"
EOF

chmod +x /home/pi/check_psms.sh

# Run daily report
crontab -e
# Add: 0 8 * * * /home/pi/check_psms.sh | mail -s "PSMS Daily Report" admin@example.com
```

## Maintenance and Monitoring

### Daily Tasks
- [ ] Check system status dashboard
- [ ] Review active alerts
- [ ] Verify all devices reporting

### Weekly Tasks
- [ ] Review system logs
- [ ] Check disk space
- [ ] Verify backup completion
- [ ] Test alert notifications

### Monthly Tasks
- [ ] Update system packages
- [ ] Review sensor calibration
- [ ] Test failover procedures
- [ ] Generate usage reports

### Quarterly Tasks
- [ ] Hardware inspection
- [ ] Clean sensors (especially MQ-135)
- [ ] Replace batteries (if used)
- [ ] Review and update thresholds

### Commands for Maintenance

```bash
# Check service status
sudo systemctl status psms-server

# View live logs
sudo journalctl -u psms-server -f

# Restart service
sudo systemctl restart psms-server

# Check disk space
df -h

# Check memory
free -h

# System updates
sudo apt-get update && sudo apt-get upgrade

# Python package updates
source ~/psms-demo-g2/raspberry_pi_server/venv/bin/activate
pip list --outdated
```

## Troubleshooting Common Issues

### Issue: ESP8266 Not Sending Data
```
1. Check Serial Monitor for errors
2. Verify WiFi connection
3. Ping Raspberry Pi from network
4. Check server is running: systemctl status psms-server
5. Test with curl from another device
```

### Issue: High Cloud Costs
```
1. Review Firestore usage in Console
2. Reduce polling interval on ESP8266
3. Implement data aggregation
4. Use batch writes instead of individual
```

### Issue: Database Growing Too Large
```
1. Implement data retention policy
2. Archive old data to Cloud Storage
3. Create cleanup script:

sqlite3 psms_data.db "DELETE FROM sensor_data WHERE timestamp < datetime('now', '-90 days');"
```

## Success Metrics

Track these KPIs:
- [ ] Device uptime (target: >99%)
- [ ] Data transmission success rate (target: >95%)
- [ ] Alert response time (target: <1 minute)
- [ ] System availability (target: >99.5%)
- [ ] Cloud sync success rate (target: >98%)

## Deployment Checklist

Use this final checklist before going live:

- [ ] All hardware assembled and tested
- [ ] Firmware uploaded to all ESP8266 nodes
- [ ] Raspberry Pi server running as service
- [ ] Database initialized and accessible
- [ ] Cloud integration tested and working
- [ ] All API endpoints responding correctly
- [ ] Alerts triggering as expected
- [ ] Backup system in place
- [ ] Monitoring and logging configured
- [ ] Documentation updated with local specifics
- [ ] Team trained on system operation
- [ ] Emergency contact list created
- [ ] Maintenance schedule established

## Next Steps After Deployment

1. Create web dashboard for visualization
2. Develop mobile app for remote monitoring
3. Implement email/SMS notifications
4. Add data analytics and reporting
5. Scale to additional locations
6. Integrate with existing hospital systems

---

**Congratulations!** Your PSMS system is now deployed and operational. Regular monitoring and maintenance will ensure reliable long-term operation.
