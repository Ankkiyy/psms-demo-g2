"""
Cloud Integration Module for PSMS

This module provides integration with Google Cloud Platform
for the Patient Security Management System.
"""

from .cloud_sync import (
    sync_to_firestore,
    batch_sync_to_firestore,
    backup_to_cloud_storage,
    query_firestore_data,
    get_cloud_statistics,
    test_cloud_connection
)

__version__ = '1.0.0'
__all__ = [
    'sync_to_firestore',
    'batch_sync_to_firestore',
    'backup_to_cloud_storage',
    'query_firestore_data',
    'get_cloud_statistics',
    'test_cloud_connection'
]
