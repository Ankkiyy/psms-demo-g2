# PSMS Quick Start Guide

Get your Patient Security Management System up and running in 30 minutes!

## Prerequisites
- ESP8266 with sensors assembled
- Raspberry Pi with Raspberry Pi OS installed
- Both devices on the same WiFi network
- Computer with Arduino IDE

## 5-Step Quick Setup

### Step 1: Setup ESP8266 (5 minutes)

```bash
# 1. Open Arduino IDE
# 2. Install board: File → Preferences
#    Add URL: http://arduino.esp8266.com/stable/package_esp8266com_index.json
# 3. Tools → Board Manager → Install "esp8266"
# 4. Install libraries: Sketch → Include Library → Manage Libraries
#    Install: "DHT sensor library", "Adafruit Unified Sensor", "ArduinoJson"
```

**Configure firmware:**
```cpp
// Edit esp8266_firmware/psms_sensor_node.ino
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://RASPBERRY_PI_IP:5000/api/sensor-data";
```

**Upload:**
```
1. Connect ESP8266 via USB
2. Select Board: NodeMCU 1.0
3. Select Port
4. Click Upload
```

### Step 2: Setup Raspberry Pi Server (10 minutes)

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Clone repository
cd ~
git clone https://github.com/Ankkiyy/psms-demo-g2.git
cd psms-demo-g2/raspberry_pi_server

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Set CLOUD_SYNC_ENABLED=false for quick start

# Run server
python app.py
```

### Step 3: Test Connection (5 minutes)

**On Raspberry Pi:**
```bash
# In another terminal, test the server
curl http://localhost:5000/api/health

# Expected: {"status":"healthy",...}
```

**Check ESP8266:**
```
1. Open Serial Monitor in Arduino IDE (115200 baud)
2. Look for: "HTTP Response code: 200"
3. If you see "Error code: -1", check server IP and firewall
```

### Step 4: View Data (5 minutes)

```bash
# Check latest sensor readings
curl http://localhost:5000/api/latest-data | python -m json.tool

# View devices
curl http://localhost:5000/api/devices | python -m json.tool

# Check database
sqlite3 psms_data.db "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5;"
```

### Step 5: Setup Auto-Start (5 minutes)

```bash
# Create systemd service
sudo nano /etc/systemd/system/psms-server.service
```

Paste:
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

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable psms-server
sudo systemctl start psms-server
```

## ✅ Verification

Your system is working if:
- [ ] ESP8266 shows "HTTP Response code: 200" in Serial Monitor
- [ ] `curl http://localhost:5000/api/latest-data` returns sensor data
- [ ] Database has records: `sqlite3 psms_data.db "SELECT COUNT(*) FROM sensor_data;"`
- [ ] Service is running: `systemctl status psms-server`

## 🎉 Success!

Your PSMS is now operational! Data is being collected every 10 seconds.

## Next Steps

1. **Add more devices**: Upload firmware to additional ESP8266 boards with unique device IDs
2. **Enable cloud sync**: Follow `cloud_integration/README.md` to setup Google Cloud
3. **Adjust thresholds**: Edit `.env` file to customize alert levels
4. **Monitor system**: Use `./test_api.sh` to test all endpoints
5. **Review docs**: Check `docs/deployment_guide.md` for production deployment

## Common Issues

### ESP8266 won't connect to WiFi
```
- Check SSID and password
- Ensure 2.4GHz network (ESP8266 doesn't support 5GHz)
- Check Serial Monitor for error messages
```

### Server returns "Connection refused"
```bash
# Check if server is running
sudo systemctl status psms-server

# Check firewall
sudo ufw allow 5000

# Check from ESP8266 network
ping RASPBERRY_PI_IP
```

### No data in database
```bash
# Check server logs
sudo journalctl -u psms-server -f

# Verify ESP8266 is sending data (Serial Monitor)
# Ensure device IDs don't have special characters
```

## Getting Help

- 📖 Full documentation: `README.md`
- 🔧 Hardware setup: `hardware_config/circuit_diagram.md`
- 🚀 Deployment guide: `docs/deployment_guide.md`
- ☁️ Cloud integration: `cloud_integration/README.md`

## Testing

Run the comprehensive test suite:
```bash
cd ~/psms-demo-g2/raspberry_pi_server
./test_api.sh
```

## Monitoring Commands

```bash
# View live sensor data
watch -n 2 'curl -s http://localhost:5000/api/latest-data | python -m json.tool'

# View active alerts
curl http://localhost:5000/api/alerts?active=true | python -m json.tool

# System statistics
curl http://localhost:5000/api/statistics | python -m json.tool

# Server logs
sudo journalctl -u psms-server -f
```

---

**Ready for production?** See `docs/deployment_guide.md` for complete deployment instructions.
