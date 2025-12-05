
import pytest
import asyncio
from src.core.task_manager import TaskManager, TaskPriority

@pytest.mark.asyncio
async def test_task_manager_execution():
    manager = TaskManager(max_workers=2)
    await manager.start()
    
    async def dummy_task(val):
        await asyncio.sleep(0.1)
        return val * 2
        
    try:
        f1 = await manager.submit(dummy_task(10), priority=TaskPriority.NORMAL)
        f2 = await manager.submit(dummy_task(20), priority=TaskPriority.NORMAL)
        
        r1 = await f1
        r2 = await f2
        
        assert r1 == 20
        assert r2 == 40
    finally:
        await manager.stop()

@pytest.mark.asyncio
async def test_task_manager_priority():
    manager = TaskManager(max_workers=1) # Single worker to force ordering
    await manager.start()
    
    execution_order = []
    
    async def task(name):
        execution_order.append(name)
        
    try:
        # Fill the worker
        await manager.submit(asyncio.sleep(0.1), priority=TaskPriority.NORMAL)
        
        # Queue tasks
        await manager.submit(task("low"), priority=TaskPriority.LOW)
        await manager.submit(task("high"), priority=TaskPriority.HIGH)
        await manager.submit(task("normal"), priority=TaskPriority.NORMAL)
        
        # Wait for everything
        await asyncio.sleep(0.5)
        
        # High should be first, then Normal, then Low
        assert execution_order == ["high", "normal", "low"]
    finally:
        await manager.stop()
