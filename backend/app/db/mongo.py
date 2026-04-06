"""
ClimaScope - MongoDB Database Connection
Handles MongoDB connection and database operations
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set")
DATABASE_NAME = os.getenv(
    "DATABASE_NAME", 
    "climascope"
)

# Async MongoDB client for FastAPI
async_client: Optional[AsyncIOMotorClient] = None
async_database = None

# Sync MongoDB client for scripts
sync_client: Optional[MongoClient] = None
sync_database = None

def get_mongo_db():
    """
    Get async MongoDB database instance
    """
    global async_database
    if async_database is None:
        raise HTTPException(
            status_code=500,
            detail="Database not initialized. Call init_db() first."
        )
    return async_database

def get_sync_db():
    """
    Get sync MongoDB database instance (for scripts)
    """
    global sync_database
    if sync_database is None:
        raise Exception("Sync database not initialized. Call init_sync_db() first.")
    return sync_database

async def init_db():
    """
    Initialize async MongoDB connection
    """
    global async_client, async_database
    
    try:
        # Create async MongoDB client
        async_client = AsyncIOMotorClient(MONGO_URI)
        async_database = async_client[DATABASE_NAME]
        
        # Test connection
        await async_client.server_info()
        logger.info(f"Connected to MongoDB: {MONGO_URI}")
        logger.info(f"Using database: {DATABASE_NAME}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

def init_sync_db():
    """
    Initialize sync MongoDB connection (for scripts)
    """
    global sync_client, sync_database
    
    try:
        # Create sync MongoDB client
        sync_client = MongoClient(MONGO_URI)
        sync_database = sync_client[DATABASE_NAME]
        
        # Test connection
        sync_client.server_info()
        logger.info(f"Connected to MongoDB (sync): {MONGO_URI}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB (sync): {str(e)}")
        raise

async def create_indexes():
    """
    Create database indexes for better performance
    """
    db = get_mongo_db()
    
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("created_at")
        
        # Devices collection indexes
        await db.devices.create_index([("user_id", 1), ("device_id", 1)], unique=True)
        await db.devices.create_index("user_id")
        await db.devices.create_index("created_at")
        
        # Sensor data collection indexes
        await db.sensor_data.create_index([("device_id", 1), ("timestamp", -1)])
        await db.sensor_data.create_index("timestamp")
        await db.sensor_data.create_index("device_id")
        
        # Alerts collection indexes
        await db.alerts.create_index([("user_id", 1), ("timestamp", -1)])
        await db.alerts.create_index("user_id")
        await db.alerts.create_index("severity")
        await db.alerts.create_index("timestamp")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Index creation warning: {str(e)}")

async def close_db():
    """
    Close MongoDB connection
    """
    global async_client
    if async_client:
        async_client.close()
        logger.info("MongoDB connection closed")

def close_sync_db():
    """
    Close sync MongoDB connection
    """
    global sync_client
    if sync_client:
        sync_client.close()
        logger.info("MongoDB sync connection closed")
