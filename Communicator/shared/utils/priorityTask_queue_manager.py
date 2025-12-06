# Priority Queue Manager for gRPC Concurrency

import asyncio
import logging
from typing import Dict, Any, Optional
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TaskPriority(IntEnum):
    """Task priority levels (lower number = higher priority)"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class PriorityTask:
    """Priority task wrapper"""
    priority: TaskPriority
    order_req_id: str
    task_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        # For priority queue ordering (lower priority number = higher priority)
        if self.priority != other.priority:
            return self.priority < other.priority
        # If same priority, order by creation time (FIFO)
        return self.created_at < other.created_at

class PriorityQueueManager:
    """Priority queue manager for gRPC streaming concurrency"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the priority queue manager"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("Priority queue manager started")
    
    async def stop(self):
        """Stop the priority queue manager"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        # Wait for all tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        logger.info("Priority queue manager stopped")
    
    async def add_priority_task(
        self, 
        order_req_id: str,
        task_func: callable,
        priority: TaskPriority = TaskPriority.MEDIUM,
        **kwargs
    ) -> str:
        """
        Add a task to the priority queue
        
        Args:
            order_req_id: Order request ID (used for tracking, not passed to task_func)
            task_func: Async function to execute
            priority: Task priority
            **kwargs: Arguments for task_func (use w_ prefix if conflicts with params above)
            
        Returns:
            task_id: Unique task identifier
        """
        task_id = f"{order_req_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        # Extract worker kwargs (w_ prefix) and rename them
        worker_kwargs = {}
        for key, value in kwargs.items():
            if key.startswith('w_'):
                # Remove w_ prefix for actual function call
                actual_key = key[2:]
                worker_kwargs[actual_key] = value
            else:
                worker_kwargs[key] = value
        
        priority_task = PriorityTask(
            priority=priority,
            order_req_id=order_req_id,
            task_id=task_id,
            payload={
                'func': task_func,
                'kwargs': worker_kwargs
            }
        )
        
        await self.priority_queue.put(priority_task)
        logger.info(f"Added priority task {task_id} with priority {priority.name}")
        return task_id
    
    async def _worker(self):
        """Worker coroutine to process priority queue"""
        while self._running:
            try:
                # Wait for tasks if we haven't reached max concurrency
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next priority task (with timeout to allow checking _running)
                try:
                    priority_task = await asyncio.wait_for(
                        self.priority_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Create and start the task
                task = asyncio.create_task(
                    self._execute_task(priority_task),
                    name=f"priority_task_{priority_task.task_id}"
                )
                
                self.active_tasks[priority_task.task_id] = task
                
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, priority_task: PriorityTask):
        """Execute a priority task"""
        task_id = priority_task.task_id
        try:
            func = priority_task.payload['func']
            kwargs = priority_task.payload['kwargs']
            
            logger.info(f"Executing task {task_id}")
            result = await func(**kwargs)
            
            self.task_results[task_id] = {
                'success': True,
                'result': result,
                'completed_at': datetime.utcnow()
            }
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            self.task_results[task_id] = {
                'success': False,
                'error': str(e),
                'completed_at': datetime.utcnow()
            }
        finally:
            # Remove from active tasks
            self.active_tasks.pop(task_id, None)
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task"""
        return self.task_results.get(task_id)
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get priority queue statistics"""
        return {
            'priority_queue_size': self.priority_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.task_results)
        }
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """Cleanup old task results"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, result in self.task_results.items():
            if result['completed_at'] < cutoff:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.task_results[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old task results")

# Global priority queue manager instance
priority_queue_manager = PriorityQueueManager()
