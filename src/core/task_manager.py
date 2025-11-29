import asyncio
import logging
from typing import Coroutine, Any, List, Tuple
from enum import IntEnum

logger = logging.getLogger("OSINT_Tool")

class TaskPriority(IntEnum):
    HIGH = 0    # Critical tasks (e.g., verification)
    NORMAL = 1  # Standard tasks (e.g., search)
    LOW = 2     # Background tasks (e.g., passive checks)

class TaskManager:
    """
    Manages asynchronous task execution with priority queues and concurrency limits.
    """
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize the TaskManager.
        
        Args:
            max_workers: Maximum number of concurrent tasks.
        """
        self.max_workers = max_workers
        self.queue = asyncio.PriorityQueue()
        self.workers = []
        self.active_tasks = 0
        self._shutdown = False
        self._results = []
        
    async def start(self):
        """Start the worker pool."""
        logger.info(f"Starting TaskManager with {self.max_workers} workers")
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
            
    async def stop(self):
        """Stop the worker pool and wait for remaining tasks."""
        self._shutdown = True
        await self.queue.join()
        
        for worker in self.workers:
            worker.cancel()
            
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("TaskManager stopped")

    async def submit(self, coro: Coroutine, priority: TaskPriority = TaskPriority.NORMAL) -> asyncio.Future:
        """
        Submit a coroutine for execution.
        
        Args:
            coro: The coroutine to execute.
            priority: Task priority (lower value = higher priority).
            
        Returns:
            A Future representing the task result.
        """
        future = asyncio.get_running_loop().create_future()
        await self.queue.put((priority, coro, future))
        return future

    async def _worker(self):
        """Worker coroutine that processes tasks from the queue."""
        while not self._shutdown:
            try:
                # Get a task from the queue
                priority, coro, future = await self.queue.get()
                
                self.active_tasks += 1
                try:
                    # SECURITY: Wrap with timeout to prevent hung tasks from blocking workflow
                    # Default timeout: 10 minutes (600 seconds)
                    result = await asyncio.wait_for(coro, timeout=600)
                    if not future.cancelled():
                        future.set_result(result)
                except asyncio.TimeoutError:
                    error_msg = "Task execution timeout (exceeded 600 seconds)"
                    logger.error(error_msg)
                    if not future.cancelled():
                        future.set_exception(TimeoutError(error_msg))
                except Exception as e:
                    if not future.cancelled():
                        future.set_exception(e)
                    logger.error(f"Task execution failed: {e}")
                finally:
                    self.active_tasks -= 1
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")

    @property
    def is_idle(self) -> bool:
        """Check if there are no active tasks and the queue is empty."""
        return self.active_tasks == 0 and self.queue.empty()
