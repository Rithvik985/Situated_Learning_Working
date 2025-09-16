"""
MinIO client utilities for Situated Learning System
"""
import os
import io
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import logging
import traceback

logger = logging.getLogger(__name__)

class MinIOClient:
    """MinIO client for file storage operations"""
    
    def __init__(self):
        # Get MinIO configuration from environment
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "password1234")
        self.bucket_name = os.getenv("MINIO_BUCKET", "situated-learning")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        logger.info("Initializing MinIO client:")
        logger.info(f"  Endpoint: {endpoint}")
        logger.info(f"  Access Key: {access_key}")
        logger.info(f"  Bucket: {self.bucket_name}")
        logger.info(f"  Secure: {secure}")
        
        # Initialize MinIO client
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        logger.info("MinIO client initialized")
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def initialize_connection(self):
        """Initialize MinIO connection and ensure bucket exists"""
        try:
            logger.info("Initializing MinIO connection...")
            self._ensure_bucket_exists()
            logger.info("MinIO connection initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize MinIO connection: {e}")
            logger.warning("MinIO operations may be limited until connection is established")
    
    def upload_file(self, file_path: str, object_name: str, content_type: str = "application/pdf") -> str:
        """
        Upload a file to MinIO
        
        Args:
            file_path: Local path to the file
            object_name: Object name in MinIO (including path)
            content_type: MIME type of the file
            
        Returns:
            str: Object name of the uploaded file
        """
        try:
            logger.info(f"Uploading file to MinIO:")
            logger.info(f"  File path: {file_path}")
            logger.info(f"  Object name: {object_name}")
            logger.info(f"  Bucket: {self.bucket_name}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get file size
            file_size = os.path.getsize(file_path)
            logger.info(f"  File size: {file_size} bytes")
            
            # Upload to MinIO
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            
            logger.info(f"✅ Successfully uploaded file to MinIO: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"❌ MinIO Error uploading file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error uploading file {file_path}: {e}")
            raise
    
    def upload_file_object(self, file_object: BinaryIO, object_name: str, 
                          file_size: int, content_type: str = "application/pdf") -> str:
        """
        Upload a file object to MinIO
        
        Args:
            file_object: File-like object to upload
            object_name: Object name in MinIO (including path)
            file_size: Size of the file in bytes
            content_type: MIME type of the file
            
        Returns:
            str: Object name of the uploaded file
        """
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_object,
                file_size,
                content_type=content_type
            )
            logger.info(f"✅ Uploaded file object: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"❌ Error uploading file object to {object_name}: {e}")
            raise
    
    def get_file_object(self, object_name: str) -> Optional[bytes]:
        """
        Get a file object from MinIO
        
        Args:
            object_name: Object name in MinIO (including path)
            
        Returns:
            bytes: File content as bytes
        """
        try:
            logger.info(f"Getting file from MinIO: {self.bucket_name}/{object_name}")
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"✅ Retrieved file from MinIO: {object_name}, size: {len(data)} bytes")
            return data
        except S3Error as e:
            logger.error(f"❌ Error getting file object {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error getting file object {object_name}: {e}")
            return None
    
    def delete_file(self, object_name: str):
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"✅ Deleted file: {object_name}")
        except S3Error as e:
            logger.error(f"❌ Error deleting file {object_name}: {e}")
            raise
    
    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_size(self, object_name: str) -> Optional[int]:
        """Get file size from MinIO"""
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            return stat.size
        except S3Error as e:
            logger.error(f"Error getting file size for {object_name}: {e}")
            return None

# Global MinIO client instance
minio_client = MinIOClient()
