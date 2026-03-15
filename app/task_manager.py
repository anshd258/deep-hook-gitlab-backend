import asyncio
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class TaskManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance.active_tasks = {}
        return cls._instance

    def __init__(self):
        # Using singleton pattern, init logic in __new__ or guarded here
        if not hasattr(self, 'active_tasks'):
            self.active_tasks: Dict[Tuple[int, int], asyncio.Task] = {}

    async def cancel_task(self, project_id: int, mr_iid: int):
        key = (project_id, mr_iid)
        task = self.active_tasks.get(key)
        if task:
            if not task.done():
                logger.info(f"Cancelling existing task for Project {project_id} MR {mr_iid}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task for Project {project_id} MR {mr_iid} cancelled successfully")
                except Exception as e:
                    logger.error(f"Error awaiting cancelled task: {e}")
            self.active_tasks.pop(key, None)

    def add_task(self, project_id: int, mr_iid: int, coro):
        key = (project_id, mr_iid)
        
        # We assume cancel_task was called before this if needed, 
        # or we can enforce it here. Enforcing it is safer.
        # However, since add_task is synchronous (returns Task), we can't await cancel_task here.
        # The handler should await cancel_task before calling add_task.
        
        if key in self.active_tasks and not self.active_tasks[key].done():
             logger.warning(f"Overwriting active task for Project {project_id} MR {mr_iid} without awaiting cancellation!")
        
        task = asyncio.create_task(coro)
        self.active_tasks[key] = task
        
        def done_callback(t):
            if self.active_tasks.get(key) == t:
                self.active_tasks.pop(key, None)
            
            try:
                t.result()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Task for Project {project_id} MR {mr_iid} failed: {e}")

        task.add_done_callback(done_callback)
        return task

task_manager = TaskManager()
