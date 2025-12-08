# Google Cloud Platform Integration Guide

## Overview
This guide explains how to integrate the Patient Security Management System (PSMS) with Google Cloud Platform for data storage, backup, and analytics.

## Architecture

```
┌────────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  ESP8266       │────→│  Raspberry Pi   │────→│  Google Cloud        │
│  Sensors       │WiFi │  Flask Server   │HTTP │  Platform            │
└────────────────┘     └─────────────────┘     └──────────────────────┘
                              │                         │
                              ↓                         ↓
                       ┌─────────────┐         ┌────────────────┐
                       │  SQLite DB  │         │  Firestore DB  │
                       │  (Local)    │         │  (Cloud)       │
                       └─────────────┘         └────────────────┘
                                                        │
                                                ┌────────────────┐
                                                │ Cloud Storage  │
                                                │ (Backups)      │
                                                └────────────────┘
```

## Benefits of Cloud Integration

1. **Data Persistence**: Protect against local hardware failures
2. **Scalability**: Handle multiple devices and locations
3. **Analytics**: Use BigQuery for advanced data analysis
4. **Accessibility**: Access data from anywhere
5. **Backup**: Automatic cloud backups
6. **Integration**: Connect to other Google Cloud services

## Prerequisites

- Google Cloud Platform account
- Credit card (free tier available)
- Basic understanding of cloud services
- Raspberry Pi with internet connection

## Setup Instructions

### Part 1: Google Cloud Console Setup

#### Step 1: Create a New Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click "New Project"
4. Enter project details:
   - **Project name**: `psms-iot-system` (or your choice)
   - **Organization**: (if applicable)
5. Click "Create"
6. Note your **Project ID** (e.g., `psms-iot-system-12345`)

#### Step 2: Enable Required APIs

Navigate to **APIs & Services** → **Library** and enable:

1. **Cloud Firestore API**
   - Real-time NoSQL database
   - For storing sensor data

2. **Cloud Storage API**
   - Object storage
   - For backup files

3. **Cloud Logging API** (optional)
   - For application logs

Or use gcloud CLI:
```bash
gcloud services enable firestore.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable logging.googleapis.com
```

#### Step 3: Set Up Cloud Firestore

1. Navigate to **Firestore** in the console
2. Click "Create Database"
3. Choose mode:
   - **Production mode** (recommended): Secure by default
   - **Test mode**: Open for development (30 days)
4. Select location:
   - Choose region closest to your Raspberry Pi
   - Examples: `us-central1`, `europe-west1`, `asia-south1`
5. Click "Create Database"

#### Step 4: Create a Service Account

1. Navigate to **IAM & Admin** → **Service Accounts**
2. Click "Create Service Account"
3. Enter details:
   - **Name**: `psms-backend-service`
   - **Description**: `Service account for PSMS backend server`
4. Click "Create and Continue"
5. Grant roles:
   - **Cloud Datastore User** (for Firestore)
   - **Storage Object Admin** (for Cloud Storage)
6. Click "Continue" then "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" → "Create new key"
10. Choose **JSON** format
11. Click "Create" - JSON file will download
12. **Keep this file secure!** It contains credentials

#### Step 5: Create Cloud Storage Bucket

1. Navigate to **Cloud Storage** → **Buckets**
2. Click "Create Bucket"
3. Enter details:
   - **Name**: `psms-backup-bucket` (must be globally unique)
   - Add your project ID if needed: `psms-backup-bucket-12345`
4. Choose location:
   - **Region**: Same as Firestore for consistency
5. Choose storage class:
   - **Standard**: For frequently accessed data
   - **Nearline**: For monthly access (cheaper)
6. Set access control:
   - **Uniform**: Recommended for simplicity
7. Click "Create"

### Part 2: Raspberry Pi Configuration

#### Step 1: Transfer Service Account Key

Transfer the JSON key file to your Raspberry Pi:

**Method 1: Using SCP (from your computer)**
```bash
scp ~/Downloads/psms-iot-system-*.json pi@RASPBERRY_PI_IP:~/psms-demo-g2/raspberry_pi_server/
```

**Method 2: Using USB Drive**
1. Copy JSON file to USB drive
2. Insert USB into Raspberry Pi
3. Mount and copy:
```bash
sudo mount /dev/sda1 /mnt/usb
cp /mnt/usb/psms-iot-system-*.json ~/psms-demo-g2/raspberry_pi_server/
sudo umount /mnt/usb
```

**Method 3: Copy-paste content**
```bash
nano ~/psms-demo-g2/raspberry_pi_server/service-account-key.json
# Paste the JSON content
# Ctrl+X, Y, Enter to save
```

#### Step 2: Set File Permissions
```bash
cd ~/psms-demo-g2/raspberry_pi_server
chmod 600 service-account-key.json
```

#### Step 3: Install Google Cloud Libraries
```bash
# Activate virtual environment
source venv/bin/activate

# Install libraries
pip install google-cloud-firestore google-cloud-storage google-auth
```

#### Step 4: Update Environment Configuration

Edit `.env` file:
```bash
nano .env
```

Update these variables:
```bash
# Enable cloud sync
CLOUD_SYNC_ENABLED=true

# Google Cloud Configuration
GCP_PROJECT_ID=psms-iot-system-12345
GOOGLE_APPLICATION_CREDENTIALS=/home/pi/psms-demo-g2/raspberry_pi_server/service-account-key.json
FIRESTORE_COLLECTION=psms_sensor_data
GCS_BUCKET_NAME=psms-backup-bucket-12345
```

Save and exit (Ctrl+X, Y, Enter)

#### Step 5: Test Cloud Connection
```bash
cd ~/psms-demo-g2/cloud_integration
python cloud_sync.py
```

Expected output:
```
=== Google Cloud Integration Test ===

Configuration:
  Project ID: psms-iot-system-12345
  Credentials: /home/pi/.../service-account-key.json
  Firestore Collection: psms_sensor_data
  Storage Bucket: psms-backup-bucket-12345
  Libraries Available: True

Testing connection...
  Firestore: ✓
  Storage: ✓
```

### Part 3: Verify Integration

#### Test 1: Send Test Data
```bash
# Run the Flask server
cd ~/psms-demo-g2/raspberry_pi_server
python app.py
```

In another terminal, send test data:
```bash
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "TEST_DEVICE",
    "location": "Test_Room",
    "timestamp": 1234567890,
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

#### Test 2: Verify in Firestore

1. Go to **Firestore** in Google Cloud Console
2. Navigate to `psms_sensor_data` collection
3. You should see the test document

#### Test 3: Check Logs
```bash
# Check Flask server logs for sync messages
# Look for: "Data synced to Firestore: TEST_DEVICE_..."
```

## Data Structure in Firestore

### Collection: `psms_sensor_data`

Document structure:
```json
{
  "local_record_id": 1,
  "device_id": "ESP8266_PSMS_001",
  "location": "Room_101",
  "device_timestamp": 1234567890,
  "server_timestamp": "2024-01-01T12:00:00Z",
  "sensors": {
    "temperature": 25.3,
    "humidity": 55.0,
    "air_quality": 342,
    "distance": 150
  },
  "alert_type": "none",
  "alert_active": false,
  "synced_at": "2024-01-01T12:00:01.123Z"
}
```

Document ID format: `{device_id}_{timestamp}`
Example: `ESP8266_PSMS_001_1234567890`

## Querying Data from Cloud

### Using Google Cloud Console

1. Go to Firestore
2. Select `psms_sensor_data` collection
3. Use filters:
   - Field: `device_id`, Operator: `==`, Value: `ESP8266_PSMS_001`
   - Field: `alert_active`, Operator: `==`, Value: `true`

### Using Python (on Raspberry Pi)

```python
from google.cloud import firestore

db = firestore.Client()

# Get all records for a device
device_id = "ESP8266_PSMS_001"
docs = db.collection('psms_sensor_data')\
    .where('device_id', '==', device_id)\
    .order_by('server_timestamp', direction=firestore.Query.DESCENDING)\
    .limit(10)\
    .stream()

for doc in docs:
    data = doc.to_dict()
    print(f"Temperature: {data['sensors']['temperature']}°C")
```

### Using gcloud CLI

```bash
# List recent documents
gcloud firestore documents list psms_sensor_data --limit=10

# Query specific device
gcloud firestore documents query psms_sensor_data \
  --filter="device_id=ESP8266_PSMS_001" \
  --limit=10
```

## Cost Estimation

### Free Tier (Always Free)
- **Firestore**: 
  - 1 GiB storage
  - 50,000 reads/day
  - 20,000 writes/day
  - 20,000 deletes/day

- **Cloud Storage**:
  - 5 GB storage
  - 5,000 Class A operations/month
  - 50,000 Class B operations/month

### Estimated Usage (10 Devices, 10-second intervals)
- **Writes**: 10 devices × 6 writes/min × 1,440 min/day = **86,400 writes/day**
  - Above free tier, cost: ~$0.18/day or ~$5.40/month

- **Storage**: ~100KB/day/device = 30MB/month/device
  - 10 devices = 300MB/month (well within free tier)

### Cost Reduction Strategies

1. **Reduce Write Frequency**
   - Change from 10s to 30s intervals: 3× reduction
   - Only sync on alert or significant changes

2. **Batch Writes**
   - Group multiple readings into single write
   - Use batch operations

3. **Use Cloud Storage for Archives**
   - Move old data (>30 days) to cheaper storage
   - Use lifecycle policies

4. **Implement Data Aggregation**
   - Store averages instead of all readings
   - Keep only alerts and anomalies in real-time DB

Example optimized configuration:
```bash
# In ESP8266 firmware, change:
const long interval = 30000;  # 30 seconds instead of 10

# In app.py, add batching logic
# Only sync to cloud every 10 readings or on alerts
```

## Security Best Practices

### 1. Service Account Key Security
```bash
# Set restrictive permissions
chmod 600 service-account-key.json

# Never commit to git
echo "service-account-key.json" >> .gitignore

# Rotate keys periodically (every 90 days)
# Create new key, update config, delete old key
```

### 2. Firestore Security Rules

In Firestore console, set rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Only allow authenticated writes
    match /psms_sensor_data/{document} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

### 3. Network Security
```bash
# On Raspberry Pi, allow only necessary outbound connections
sudo ufw allow out to any port 443  # HTTPS for Google APIs
```

### 4. API Key Restrictions
1. Go to **APIs & Services** → **Credentials**
2. Restrict API keys to:
   - Specific APIs (Firestore, Storage)
   - IP addresses (your Raspberry Pi's public IP)

## Monitoring and Alerts

### Cloud Monitoring Setup

1. Navigate to **Monitoring** in Google Cloud Console
2. Create alerts for:
   - High write rate (cost control)
   - Failed operations
   - Storage quota usage

### Example Alert Policy
```yaml
Alert Name: High Firestore Write Rate
Condition: Firestore writes > 100,000/day
Notification: Email to admin@example.com
```

### View Logs
```bash
# Install gcloud CLI on Raspberry Pi
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize
gcloud init

# View logs
gcloud logging read "resource.type=cloud_firestore" --limit=50
```

## Data Export and Backup

### Export Firestore Data

```bash
# Export entire collection to Cloud Storage
gcloud firestore export gs://psms-backup-bucket-12345/firestore-backup/

# Schedule automatic exports (daily at 2 AM)
# Create Cloud Scheduler job in console
```

### Download Backup Locally

```bash
# Install gsutil (included with gcloud)
gsutil -m cp -r gs://psms-backup-bucket-12345/backups ~/psms-backups/
```

## Advanced Features

### BigQuery Integration (Analytics)

1. Export Firestore data to BigQuery
2. Run SQL queries for insights:

```sql
SELECT 
  device_id,
  AVG(sensors.temperature) as avg_temp,
  COUNT(*) as reading_count
FROM `psms_sensor_data`
WHERE DATE(server_timestamp) = CURRENT_DATE()
GROUP BY device_id
```

### Cloud Functions (Serverless Alerts)

Create functions triggered by Firestore writes:

```python
# functions/main.py
def alert_on_high_temp(data, context):
    temp = data['value']['fields']['sensors']['mapValue']['fields']['temperature']['doubleValue']
    if temp > 30:
        # Send email/SMS alert
        send_alert(f"High temperature: {temp}°C")
```

### Data Studio Dashboard

1. Connect Data Studio to Firestore/BigQuery
2. Create real-time dashboards
3. Share with team

## Troubleshooting

### Error: "Permission Denied"
- Verify service account has correct roles
- Check credentials path in .env file
- Ensure file permissions: `chmod 600 service-account-key.json`

### Error: "Project ID not found"
- Verify PROJECT_ID in .env matches Google Cloud
- Check service account key JSON for correct project

### Error: "Collection not found"
- Create collection by writing first document
- Firestore collections are created on first write

### Slow Sync Performance
- Check internet connection speed
- Consider batching writes
- Use Cloud Monitoring to check API latency

### Cost Exceeds Expectations
- Review **Billing** reports in console
- Check for unexpected write spikes
- Implement rate limiting on ESP8266

## Alternative Cloud Providers

While this guide focuses on Google Cloud Platform, the system can be adapted for:

### AWS (Amazon Web Services)
- Use DynamoDB instead of Firestore
- Use S3 instead of Cloud Storage
- Modify `cloud_sync.py` with boto3 library

### Azure (Microsoft)
- Use Azure Cosmos DB
- Use Azure Blob Storage
- Modify with azure-storage-blob library

### Self-Hosted Options
- InfluxDB for time-series data
- MongoDB for document storage
- MinIO for S3-compatible storage

## Support and Resources

- **Google Cloud Documentation**: https://cloud.google.com/docs
- **Firestore Pricing**: https://cloud.google.com/firestore/pricing
- **Python Client Libraries**: https://cloud.google.com/python/docs
- **Community Support**: Stack Overflow, Google Cloud Community

## Next Steps

1. ✅ Complete cloud setup
2. ✅ Test with real sensor data
3. ⬜ Set up monitoring and alerts
4. ⬜ Create Data Studio dashboard
5. ⬜ Implement automated backups
6. ⬜ Scale to multiple devices
7. ⬜ Add advanced analytics
