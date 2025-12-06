# Synchronization utilities for asyncio

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class SyncUtils:
    """Synchronization utilities for coordinating async operations"""
    
    def __init__(self):
        self.put_locks: Dict[str, asyncio.Lock] = {}
        self.order_locks: Dict[str, asyncio.Lock] = {}
        self.proposal_locks: Dict[str, asyncio.Lock] = {}
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        
    def get_put_lock(self, resource_id: str) -> asyncio.Lock:
        """Get or create a lock for PUT operations on a specific resource"""
        if resource_id not in self.put_locks:
            self.put_locks[resource_id] = asyncio.Lock()
        return self.put_locks[resource_id]
    
    def get_order_lock(self, order_req_id: str) -> asyncio.Lock:
        """Get or create a lock for order operations"""
        if order_req_id not in self.order_locks:
            self.order_locks[order_req_id] = asyncio.Lock()
        return self.order_locks[order_req_id]
    
    def get_proposal_lock(self, proposal_id: str) -> asyncio.Lock:
        """Get or create a lock for proposal operations"""
        if proposal_id not in self.proposal_locks:
            self.proposal_locks[proposal_id] = asyncio.Lock()
        return self.proposal_locks[proposal_id]
    
    def get_semaphore(self, name: str, limit: int = 1) -> asyncio.Semaphore:
        """Get or create a semaphore for rate limiting"""
        if name not in self.semaphores:
            self.semaphores[name] = asyncio.Semaphore(limit)
        return self.semaphores[name]
    
    @asynccontextmanager
    async def synchronized_put_operation(self, resource_id: str):
        """Context manager for synchronized PUT operations"""
        lock = self.get_put_lock(resource_id)
        async with lock:
            logger.debug(f"Acquired PUT lock for resource {resource_id}")
            try:
                yield
            finally:
                logger.debug(f"Released PUT lock for resource {resource_id}")
    
    @asynccontextmanager
    async def synchronized_order_operation(self, order_req_id: str):
        """Context manager for synchronized order operations"""
        lock = self.get_order_lock(order_req_id)
        async with lock:
            logger.debug(f"Acquired order lock for {order_req_id}")
            try:
                yield
            finally:
                logger.debug(f"Released order lock for {order_req_id}")
    
    @asynccontextmanager
    async def synchronized_proposal_operation(self, proposal_id: str):
        """Context manager for synchronized proposal operations"""
        lock = self.get_proposal_lock(proposal_id)
        async with lock:
            logger.debug(f"Acquired proposal lock for {proposal_id}")
            try:
                yield
            finally:
                logger.debug(f"Released proposal lock for {proposal_id}")
    
    @asynccontextmanager
    async def rate_limited_operation(self, name: str, limit: int = 1):
        """Context manager for rate-limited operations"""
        semaphore = self.get_semaphore(name, limit)
        async with semaphore:
            logger.debug(f"Acquired semaphore {name} ({limit} limit)")
            try:
                yield
            finally:
                logger.debug(f"Released semaphore {name}")
    
    async def wait_for_condition(
        self, 
        condition_func: callable, 
        timeout: float = 30.0,
        poll_interval: float = 0.5
    ) -> bool:
        """
        Wait for a condition to become true
        
        Args:
            condition_func: Async function that returns bool
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check condition in seconds
            
        Returns:
            bool: True if condition met, False if timeout
        """
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            try:
                if await condition_func():
                    return True
            except Exception as e:
                logger.warning(f"Condition check failed: {str(e)}")
            
            await asyncio.sleep(poll_interval)
        
        logger.warning(f"Condition wait timeout after {timeout}s")
        return False
    
    async def execute_with_retry(
        self,
        operation_func: callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> Any:
        """
        Execute an operation with retry logic
        
        Args:
            operation_func: Async function to execute
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries
            backoff_factor: Multiplier for delay on each retry
            
        Returns:
            Result of operation_func
            
        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        delay = retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                result = await operation_func()
                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    logger.warning(
                        f"Operation failed on attempt {attempt + 1}, "
                        f"retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(
                        f"Operation failed after {max_retries + 1} attempts: {str(e)}"
                    )
        
        raise last_exception
    
    def cleanup_locks(self, max_age_minutes: int = 60):
        """
        Cleanup unused locks (basic implementation)
        Note: This is a simple cleanup - in production you'd want more sophisticated logic
        """
        # This is a placeholder for lock cleanup logic
        # In a real implementation, you'd track lock usage and clean up unused ones
        pass

class OrderSyncManager(SyncUtils):
    """Specialized sync manager for order processing"""
    
    def __init__(self):
        super().__init__()
        self.order_expiry_locks: Dict[str, asyncio.Lock] = {}
    
    async def synchronized_order_update(
        self, 
        order_req_id: str, 
        update_func: callable
    ) -> Any:
        """Synchronized order update operation"""
        async with self.synchronized_order_operation(order_req_id):
            return await update_func()
    
    async def synchronized_proposal_update(
        self, 
        proposal_id: str, 
        update_func: callable
    ) -> Any:
        """Synchronized proposal update operation"""
        async with self.synchronized_proposal_operation(proposal_id):
            return await update_func()

# Global sync utilities instance
sync_utils = SyncUtils()
order_sync_manager = OrderSyncManager()