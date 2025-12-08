"""
Google Cloud Platform Integration Module for PSMS

This module handles synchronization of sensor data from the local
Raspberry Pi database to Google Cloud Firestore.

Features:
- Automatic data sync to Cloud Firestore
- Batch uploads for efficiency
- Error handling and retry logic
- Support for Cloud Storage backup
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if Google Cloud libraries are available
try:
    from google.cloud import firestore
    from google.cloud import storage
    from google.oauth2 import service_account
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
    logger.warning("Google Cloud libraries not installed. Cloud sync will be disabled.")

# Configuration from environment variables
PROJECT_ID = os.getenv('GCP_PROJECT_ID', '')
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
FIRESTORE_COLLECTION = os.getenv('FIRESTORE_COLLECTION', 'psms_sensor_data')
STORAGE_BUCKET = os.getenv('GCS_BUCKET_NAME', '')

# Initialize clients (lazy initialization)
_firestore_client = None
_storage_client = None


def get_firestore_client():
    """Get or create Firestore client."""
    global _firestore_client
    
    if not CLOUD_AVAILABLE:
        raise RuntimeError("Google Cloud libraries not available")
    
    if _firestore_client is None:
        if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_PATH
            )
            _firestore_client = firestore.Client(
                project=PROJECT_ID,
                credentials=credentials
            )
        else:
            # Use default credentials (for Cloud Run, GCE, etc.)
            _firestore_client = firestore.Client(project=PROJECT_ID)
        
        logger.info("Firestore client initialized")
    
    return _firestore_client


def get_storage_client():
    """Get or create Cloud Storage client."""
    global _storage_client
    
    if not CLOUD_AVAILABLE:
        raise RuntimeError("Google Cloud libraries not available")
    
    if _storage_client is None:
        if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_PATH
            )
            _storage_client = storage.Client(
                project=PROJECT_ID,
                credentials=credentials
            )
        else:
            # Use default credentials
            _storage_client = storage.Client(project=PROJECT_ID)
        
        logger.info("Cloud Storage client initialized")
    
    return _storage_client


def sync_to_firestore(record_id: int, data: Dict[str, Any]) -> bool:
    """
    Sync sensor data to Google Cloud Firestore.
    
    Args:
        record_id: Local database record ID
        data: Sensor data dictionary
        
    Returns:
        True if sync successful, False otherwise
    """
    if not CLOUD_AVAILABLE:
        logger.warning("Cloud sync skipped: libraries not available")
        return False
    
    try:
        db = get_firestore_client()
        
        # Prepare document data
        doc_data = {
            'local_record_id': record_id,
            'device_id': data.get('device_id'),
            'location': data.get('location'),
            'device_timestamp': data.get('timestamp'),
            'server_timestamp': firestore.SERVER_TIMESTAMP,
            'sensors': data.get('sensors', {}),
            'alert_type': data.get('alert_type'),
            'alert_active': data.get('alert_active', False),
            'synced_at': datetime.utcnow().isoformat()
        }
        
        # Generate document ID (device_id + timestamp)
        device_id = data.get('device_id', 'unknown')
        timestamp = data.get('timestamp', int(datetime.now().timestamp() * 1000))
        doc_id = f"{device_id}_{timestamp}"
        
        # Add to Firestore
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)
        doc_ref.set(doc_data)
        
        logger.info(f"Data synced to Firestore: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing to Firestore: {e}")
        return False


def batch_sync_to_firestore(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Batch sync multiple records to Firestore.
    
    Args:
        records: List of sensor data dictionaries with 'record_id' and 'data'
        
    Returns:
        Dictionary with success and failure counts
    """
    if not CLOUD_AVAILABLE:
        logger.warning("Batch sync skipped: libraries not available")
        return {'success': 0, 'failed': 0}
    
    success_count = 0
    failed_count = 0
    
    try:
        db = get_firestore_client()
        batch = db.batch()
        
        for record in records:
            try:
                record_id = record.get('record_id')
                data = record.get('data')
                
                # Prepare document
                doc_data = {
                    'local_record_id': record_id,
                    'device_id': data.get('device_id'),
                    'location': data.get('location'),
                    'device_timestamp': data.get('timestamp'),
                    'server_timestamp': firestore.SERVER_TIMESTAMP,
                    'sensors': data.get('sensors', {}),
                    'alert_type': data.get('alert_type'),
                    'alert_active': data.get('alert_active', False),
                    'synced_at': datetime.utcnow().isoformat()
                }
                
                # Generate document ID
                device_id = data.get('device_id', 'unknown')
                timestamp = data.get('timestamp', int(datetime.now().timestamp() * 1000))
                doc_id = f"{device_id}_{timestamp}_{record_id}"
                
                # Add to batch
                doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)
                batch.set(doc_ref, doc_data)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error preparing batch item: {e}")
                failed_count += 1
        
        # Commit batch
        if success_count > 0:
            batch.commit()
            logger.info(f"Batch sync completed: {success_count} records synced")
        
    except Exception as e:
        logger.error(f"Error in batch sync: {e}")
        failed_count = len(records)
        success_count = 0
    
    return {'success': success_count, 'failed': failed_count}


def backup_to_cloud_storage(data: Dict[str, Any], filename: str = None) -> bool:
    """
    Backup data to Google Cloud Storage as JSON.
    
    Args:
        data: Data to backup
        filename: Optional filename (auto-generated if not provided)
        
    Returns:
        True if backup successful, False otherwise
    """
    if not CLOUD_AVAILABLE or not STORAGE_BUCKET:
        logger.warning("Cloud Storage backup skipped: not configured")
        return False
    
    try:
        client = get_storage_client()
        bucket = client.bucket(STORAGE_BUCKET)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            device_id = data.get('device_id', 'unknown')
            filename = f"backups/{device_id}/{timestamp}.json"
        
        # Create blob and upload
        blob = bucket.blob(filename)
        blob.upload_from_string(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        
        logger.info(f"Data backed up to Cloud Storage: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error backing up to Cloud Storage: {e}")
        return False


def query_firestore_data(
    device_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query sensor data from Firestore.
    
    Args:
        device_id: Filter by device ID
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results
        
    Returns:
        List of sensor data dictionaries
    """
    if not CLOUD_AVAILABLE:
        logger.warning("Query skipped: Cloud libraries not available")
        return []
    
    try:
        db = get_firestore_client()
        query = db.collection(FIRESTORE_COLLECTION)
        
        # Apply filters
        if device_id:
            query = query.where('device_id', '==', device_id)
        
        if start_date:
            query = query.where('server_timestamp', '>=', start_date)
        
        if end_date:
            query = query.where('server_timestamp', '<=', end_date)
        
        # Order and limit
        query = query.order_by('server_timestamp', direction=firestore.Query.DESCENDING)
        query = query.limit(limit)
        
        # Execute query
        docs = query.stream()
        results = [doc.to_dict() for doc in docs]
        
        logger.info(f"Retrieved {len(results)} records from Firestore")
        return results
        
    except Exception as e:
        logger.error(f"Error querying Firestore: {e}")
        return []


def get_cloud_statistics() -> Dict[str, Any]:
    """
    Get statistics from Cloud Firestore.
    
    Returns:
        Dictionary with statistics
    """
    if not CLOUD_AVAILABLE:
        return {'error': 'Cloud libraries not available'}
    
    try:
        db = get_firestore_client()
        
        # Get total documents
        docs = db.collection(FIRESTORE_COLLECTION).limit(1000).stream()
        total_docs = sum(1 for _ in docs)
        
        # Get active alerts
        alerts = db.collection(FIRESTORE_COLLECTION)\
            .where('alert_active', '==', True)\
            .stream()
        active_alerts = sum(1 for _ in alerts)
        
        return {
            'total_records': total_docs,
            'active_alerts': active_alerts,
            'collection': FIRESTORE_COLLECTION,
            'project_id': PROJECT_ID
        }
        
    except Exception as e:
        logger.error(f"Error getting cloud statistics: {e}")
        return {'error': str(e)}


def test_cloud_connection() -> Dict[str, Any]:
    """
    Test connection to Google Cloud services.
    
    Returns:
        Dictionary with connection status
    """
    results = {
        'firestore': False,
        'storage': False,
        'errors': []
    }
    
    if not CLOUD_AVAILABLE:
        results['errors'].append("Google Cloud libraries not installed")
        return results
    
    # Test Firestore
    try:
        db = get_firestore_client()
        # Try to list collections
        list(db.collections(page_size=1))
        results['firestore'] = True
    except Exception as e:
        results['errors'].append(f"Firestore: {str(e)}")
    
    # Test Cloud Storage
    if STORAGE_BUCKET:
        try:
            client = get_storage_client()
            bucket = client.bucket(STORAGE_BUCKET)
            bucket.exists()
            results['storage'] = True
        except Exception as e:
            results['errors'].append(f"Storage: {str(e)}")
    
    return results


if __name__ == '__main__':
    # Test script
    print("=== Google Cloud Integration Test ===\n")
    
    print("Configuration:")
    print(f"  Project ID: {PROJECT_ID or 'Not set'}")
    print(f"  Credentials: {CREDENTIALS_PATH or 'Default credentials'}")
    print(f"  Firestore Collection: {FIRESTORE_COLLECTION}")
    print(f"  Storage Bucket: {STORAGE_BUCKET or 'Not set'}")
    print(f"  Libraries Available: {CLOUD_AVAILABLE}\n")
    
    if CLOUD_AVAILABLE and PROJECT_ID:
        print("Testing connection...")
        test_results = test_cloud_connection()
        print(f"  Firestore: {'✓' if test_results['firestore'] else '✗'}")
        print(f"  Storage: {'✓' if test_results['storage'] else '✗'}")
        
        if test_results['errors']:
            print("\nErrors:")
            for error in test_results['errors']:
                print(f"  - {error}")
    else:
        print("Cloud integration not configured.")
        print("\nTo enable cloud sync:")
        print("1. Install: pip install google-cloud-firestore google-cloud-storage")
        print("2. Set environment variables:")
        print("   - GCP_PROJECT_ID")
        print("   - GOOGLE_APPLICATION_CREDENTIALS (path to service account key)")
        print("   - FIRESTORE_COLLECTION (optional)")
        print("   - GCS_BUCKET_NAME (optional)")
