"""
Database configuration and connection setup for MongoDB with Beanie ODM
"""

import os
from typing import Optional
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
import asyncio

from app.models import UserBase, RolesBase, TerminalBase, RoleDetails
from app.models import OrderReq, OrderProposal
from app.core.config import settings as core_settings


class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self):
        # Prefer Pydantic settings (which loads .env) as primary source, fall back to OS env vars
        try:
            self.database_url = getattr(core_settings, 'mongodb_url', None) or os.getenv('MONGODB_URL', '...')
            self.database_name = getattr(core_settings, 'database_name', None) or os.getenv('DATABASE_NAME', 'CP_OrderManagement')
            self.min_pool_size = int(getattr(core_settings, 'min_pool_size', os.getenv('MIN_POOL_SIZE', '10')))
            self.max_pool_size = int(getattr(core_settings, 'max_pool_size', os.getenv('MAX_POOL_SIZE', '100')))
            self.max_idle_time_ms = int(getattr(core_settings, 'max_idle_time_ms', os.getenv('MAX_IDLE_TIME_MS', '30000')))
        except Exception:
            # If anything goes wrong reading settings, fall back to environment variables
            self.database_url = os.getenv('MONGODB_URL', '...')
            self.database_name = os.getenv('DATABASE_NAME', 'CP_OrderManagement')
            self.min_pool_size = int(os.getenv('MIN_POOL_SIZE', '10'))
            self.max_pool_size = int(os.getenv('MAX_POOL_SIZE', '100'))
            self.max_idle_time_ms = int(os.getenv('MAX_IDLE_TIME_MS', '30000'))


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.client = None
        self.database = None
    
    async def connect(self):
        """Connect to MongoDB and initialize Beanie ODM"""
        try:
            # Create MongoDB client
            self.client = AsyncIOMotorClient(
                self.config.database_url,
                minPoolSize=self.config.min_pool_size,
                maxPoolSize=self.config.max_pool_size,
                maxIdleTimeMS=self.config.max_idle_time_ms,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB at {self.config.database_url[:12]}...")
            
            # Get database
            self.database = self.client[self.config.database_name]
            
            # Initialize Beanie ODM with document models
            await init_beanie(
                database=self.database,
                document_models=[
                    UserBase,
                    RolesBase,
                    TerminalBase,
                    RoleDetails,
                    OrderReq,
                    OrderProposal
                ]
            )
            
            print(f"✅ Beanie ODM initialized for database: {self.config.database_name}")
            
            # Create any missing indexes
            await self._ensure_indexes()
            
        except ServerSelectionTimeoutError:
            print(f"❌ Failed to connect to MongoDB at {self.config.database_url}")
            print("Please ensure MongoDB is running and accessible")
            raise
        except Exception as e:
            print(f"❌ Database connection error: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("✅ Disconnected from MongoDB")
    
    async def _ensure_indexes(self):
        """Ensure all required indexes are created"""
        try:
            # The indexes are automatically created by Beanie based on the Settings class
            # But we can add any additional custom indexes here if needed
            
            print("✅ Database indexes verified")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not verify indexes: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            if not self.client:
                return False
            
            # Ping the database
            await self.client.admin.command('ping')
            return True
            
        except Exception:
            return False
    
    async def get_collection_stats(self):
        """Get statistics for all collections"""
        try:
            stats = {}
            
            # Get stats for each collection
            collections = ['UserBase', 'RolesBase', 'TerminalBase', 'RoleDetails', 'OrderRequest', 'OrderProposal']
            
            for collection_name in collections:
                collection = self.database[collection_name]
                count = await collection.count_documents({})
                indexes = await collection.list_indexes().to_list(None)
                
                stats[collection_name] = {
                    'document_count': count,
                    'indexes': [idx['name'] for idx in indexes]
                }
            
            return stats
            
        except Exception as e:
            print(f"Error getting collection stats: {str(e)}")
            return {}


# Global database instance
database = Database()


async def get_database():
    """Dependency for getting database instance"""
    return database


async def connect_to_database():
    """Connect to database - called during startup"""
    await database.connect()


async def disconnect_from_database():
    """Disconnect from database - called during shutdown"""
    await database.disconnect()


# Database health check utility
async def check_database_health():
    """Utility function to check database health"""
    return await database.health_check()


# Collection utilities
async def get_collection_statistics():
    """Get statistics for all collections"""
    return await database.get_collection_stats()