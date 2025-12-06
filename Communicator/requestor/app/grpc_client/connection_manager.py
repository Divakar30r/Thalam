# gRPC Connection Manager for streaming connections

import asyncio
import grpc
import logging
from typing import Dict, Optional, Set
from contextlib import asynccontextmanager

from ..core.config import RequestorConfig
from ..core.exceptions import StreamingConnectionError

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages gRPC streaming connections with pooling and reuse"""
    
    def __init__(self, max_connections: int = 5):
        self.config = RequestorConfig()
        self.max_connections = max_connections
        self.active_connections: Dict[str, grpc.aio.Channel] = {}
        self.connection_usage: Dict[str, int] = {}
        self.connection_lock = asyncio.Lock()
        self._closed = False
    
    async def get_connection(self, connection_id: str = "default") -> grpc.aio.Channel:
        """
        Get or create a gRPC connection
        
        Args:
            connection_id: Identifier for the connection
            
        Returns:
            gRPC channel
        """
        async with self.connection_lock:
            if self._closed:
                raise StreamingConnectionError("Connection manager is closed")
            
            if connection_id in self.active_connections:
                channel = self.active_connections[connection_id]
                
                # Check if channel is still valid
                try:
                    await asyncio.wait_for(channel.channel_ready(), timeout=1.0)
                    self.connection_usage[connection_id] += 1
                    return channel
                except:
                    # Channel is dead, remove it
                    await self._remove_connection(connection_id)
            
            # Create new connection if under limit
            if len(self.active_connections) >= self.max_connections:
                # Remove least used connection
                await self._remove_least_used_connection()
            
            return await self._create_connection(connection_id)
    
    async def _create_connection(self, connection_id: str) -> grpc.aio.Channel:
        """Create a new gRPC connection"""
        try:
            server_address = f"{self.config.processor_grpc_host}:{self.config.processor_grpc_port}"
            
            channel = grpc.aio.insecure_channel(server_address)
            
            # Test connection
            await channel.channel_ready()
            
            self.active_connections[connection_id] = channel
            self.connection_usage[connection_id] = 1
            
            logger.info(f"Created gRPC connection {connection_id} to {server_address}")
            return channel
            
        except Exception as e:
            logger.error(f"Failed to create gRPC connection {connection_id}: {str(e)}")
            raise StreamingConnectionError(f"Connection creation failed: {str(e)}")
    
    async def _remove_connection(self, connection_id: str):
        """Remove a specific connection"""
        if connection_id in self.active_connections:
            channel = self.active_connections[connection_id]
            try:
                await channel.close()
            except:
                pass  # Ignore errors during close
            
            del self.active_connections[connection_id]
            del self.connection_usage[connection_id]
            
            logger.info(f"Removed gRPC connection {connection_id}")
    
    async def _remove_least_used_connection(self):
        """Remove the least used connection to make room"""
        if not self.active_connections:
            return
        
        # Find least used connection
        least_used_id = min(self.connection_usage, key=self.connection_usage.get)
        await self._remove_connection(least_used_id)
    
    @asynccontextmanager
    async def connection_context(self, connection_id: str = "default"):
        """Context manager for connection usage"""
        channel = await self.get_connection(connection_id)
        try:
            yield channel
        finally:
            # Connection usage is already tracked in get_connection
            pass
    
    async def close_connection(self, connection_id: str):
        """Close a specific connection"""
        async with self.connection_lock:
            await self._remove_connection(connection_id)
    
    async def close_all_connections(self):
        """Close all active connections"""
        async with self.connection_lock:
            connection_ids = list(self.active_connections.keys())
            
            for connection_id in connection_ids:
                await self._remove_connection(connection_id)
            
            self._closed = True
            logger.info("Closed all gRPC connections")
    
    def get_connection_stats(self) -> Dict[str, int]:
        """Get connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "max_connections": self.max_connections,
            "total_usage": sum(self.connection_usage.values()),
            "connections": dict(self.connection_usage)
        }
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all connections"""
        results = {}
        
        for connection_id, channel in self.active_connections.items():
            try:
                await asyncio.wait_for(channel.channel_ready(), timeout=2.0)
                results[connection_id] = True
            except:
                results[connection_id] = False
        
        return results
    
    async def cleanup_dead_connections(self) -> int:
        """Remove dead connections and return count removed"""
        dead_connections = []
        
        for connection_id, channel in self.active_connections.items():
            try:
                await asyncio.wait_for(channel.channel_ready(), timeout=1.0)
            except:
                dead_connections.append(connection_id)
        
        for connection_id in dead_connections:
            await self._remove_connection(connection_id)
        
        logger.info(f"Cleaned up {len(dead_connections)} dead connections")
        return len(dead_connections)

# Global connection manager instance
connection_manager = ConnectionManager()