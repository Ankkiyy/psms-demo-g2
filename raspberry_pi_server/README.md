# Raspberry Pi Server - PSMS Backend

## Overview
This is the backend server for the Patient Security Management System (PSMS). It runs on a Raspberry Pi and serves as the central hub for receiving sensor data from ESP8266 devices, storing it locally, and syncing to Google Cloud Platform.

## Features

- **REST API** for sensor data ingestion
- **SQLite Database** for local data storage
- **Google Cloud Firestore** integration for cloud backup
- **Real-time Alert System** for threshold violations
- **Device Management** tracking and monitoring
- **Statistics Dashboard** for system insights

## System Requirements

### Hardware
- Raspberry Pi 3 Model B+ or newer (recommended: Raspberry Pi 4)
- Minimum 1GB RAM (2GB+ recommended)
- 16GB microSD card (32GB+ recommended)
- Stable internet connection for cloud sync

### Software
- Raspberry Pi OS (Debian-based)
- Python 3.7 or higher
- SQLite3 (usually pre-installed)

## Installation

### 1. Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Python and Dependencies
```bash
# Install Python 3 and pip if not already installed
sudo apt-get install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt-get install sqlite3 libsqlite3-dev -y
```

### 3. Clone Repository
```bash
cd ~
git clone https://github.com/Ankkiyy/psms-demo-g2.git
cd psms-demo-g2/raspberry_pi_server
```

### 4. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Python Packages
```bash
pip install -r requirements.txt
```

### 6. Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Update the following in `.env`:
- Set your WiFi network details if needed
- Configure Google Cloud credentials (if using cloud sync)
- Adjust alert thresholds as needed

## Google Cloud Setup (Optional but Recommended)

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID

### 2. Enable Required APIs
```bash
gcloud services enable firestore.googleapis.com
gcloud services enable storage-api.googleapis.com
```

Or enable via Console:
- Firestore API
- Cloud Storage API

### 3. Create Service Account
1. Navigate to IAM & Admin → Service Accounts
2. Create a new service account
3. Grant roles:
   - Cloud Datastore User
   - Storage Object Admin (if using Cloud Storage)
4. Create and download JSON key
5. Copy the key to Raspberry Pi:
```bash
scp service-account-key.json pi@raspberry-pi-ip:~/psms-demo-g2/raspberry_pi_server/
```

### 4. Initialize Firestore Database
1. Go to Firestore in Google Cloud Console
2. Create a new database
3. Choose production mode
4. Select a region (choose closest to your location)

### 5. Create Storage Bucket (Optional)
```bash
gsutil mb -p YOUR_PROJECT_ID -l REGION gs://psms-backup-bucket/
```

### 6. Update Configuration
Edit `.env` file:
```bash
CLOUD_SYNC_ENABLED=true
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/home/pi/psms-demo-g2/raspberry_pi_server/service-account-key.json
FIRESTORE_COLLECTION=psms_sensor_data
GCS_BUCKET_NAME=psms-backup-bucket
```

## Running the Server

### Development Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python app.py
```

The server will start on `http://0.0.0.0:5000`

### Production Mode with Gunicorn
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Run as System Service

Create a systemd service file:
```bash
sudo nano /etc/systemd/system/psms-server.service
```

Add the following content:
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

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable psms-server
sudo systemctl start psms-server
```

Check status:
```bash
sudo systemctl status psms-server
```

View logs:
```bash
sudo journalctl -u psms-server -f
```

## API Endpoints

### Health Check
```
GET /api/health
```

### Submit Sensor Data
```
POST /api/sensor-data
Content-Type: application/json

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

### Get Latest Data
```
GET /api/latest-data
GET /api/latest-data?device_id=ESP8266_PSMS_001
```

### Get Alerts
```
GET /api/alerts
GET /api/alerts?active=true
GET /api/alerts?device_id=ESP8266_PSMS_001
```

### Get Devices
```
GET /api/devices
```

### Get Statistics
```
GET /api/statistics
```

## Testing

### Test Server Locally
```bash
# Using curl
curl http://localhost:5000/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "cloud_sync": false
}
```

### Test from ESP8266 Network
Find your Raspberry Pi IP address:
```bash
hostname -I
```

Test from another device on the same network:
```bash
curl http://RASPBERRY_PI_IP:5000/api/health
```

### Send Test Data
```bash
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "TEST_DEVICE",
    "location": "Test_Room",
    "timestamp": 123456789,
    "sensors": {
      "temperature": 25.0,
      "humidity": 60.0,
      "air_quality": 400,
      "distance": 100
    },
    "alert_type": "none",
    "alert_active": false
  }'
```

## Database

### Location
```
/home/pi/psms-demo-g2/raspberry_pi_server/psms_data.db
```

### Inspect Database
```bash
sqlite3 psms_data.db

# List tables
.tables

# Query sensor data
SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;

# Query alerts
SELECT * FROM alerts WHERE resolved = 0;

# Exit
.quit
```

### Backup Database
```bash
# Manual backup
cp psms_data.db psms_data_backup_$(date +%Y%m%d).db

# Automated backup (add to crontab)
0 2 * * * cp /home/pi/psms-demo-g2/raspberry_pi_server/psms_data.db /home/pi/backups/psms_data_$(date +\%Y\%m\%d).db
```

## Troubleshooting

### Server Won't Start
- Check Python version: `python3 --version`
- Verify virtual environment is activated
- Check for port conflicts: `sudo netstat -tlnp | grep 5000`
- Review logs: `tail -f /var/log/syslog`

### ESP8266 Can't Connect
- Verify Raspberry Pi IP address
- Check firewall: `sudo ufw status`
- Allow port 5000: `sudo ufw allow 5000`
- Test with curl from another device

### Cloud Sync Issues
- Verify service account key path
- Check credentials: `python cloud_sync.py`
- Ensure APIs are enabled in Google Cloud
- Check internet connectivity

### Database Errors
- Check disk space: `df -h`
- Verify permissions: `ls -l psms_data.db`
- Ensure SQLite is installed: `sqlite3 --version`

## Security Considerations

1. **Change Default Credentials**
   - Use strong passwords for system access
   - Secure service account keys

2. **Network Security**
   - Use firewall rules to restrict access
   - Consider using HTTPS with Let's Encrypt
   - Use VPN for remote access

3. **Regular Updates**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   pip install --upgrade -r requirements.txt
   ```

4. **Monitor Logs**
   - Regularly check system logs
   - Set up log rotation
   - Monitor for suspicious activity

## Performance Optimization

### For Large Deployments
1. Use PostgreSQL instead of SQLite
2. Implement Redis caching
3. Use message queue (RabbitMQ/Redis) for async processing
4. Scale horizontally with multiple server instances

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_device_location ON sensor_data(device_id, location);
CREATE INDEX IF NOT EXISTS idx_timestamp_range ON sensor_data(timestamp);
```

## Monitoring

### System Resources
```bash
# CPU and Memory
htop

# Disk usage
df -h

# Service status
sudo systemctl status psms-server
```

### Application Logs
```bash
# Real-time logs
sudo journalctl -u psms-server -f

# Last 100 lines
sudo journalctl -u psms-server -n 100
```

## Next Steps

1. Set up ESP8266 devices with the firmware
2. Configure Google Cloud integration
3. Create a web dashboard for visualization
4. Implement email/SMS alerts
5. Add data analytics and reporting

## Support

For issues and questions:
- Check the main repository README
- Review troubleshooting section
- Check system logs for errors
