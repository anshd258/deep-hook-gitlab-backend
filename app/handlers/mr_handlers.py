import logging
from deep_hook_review import DeepConfig
from app.task_manager import task_manager
from app.services.review_service import run_review_pipeline

logger = logging.getLogger(__name__)

async def handle_mr_event(
    project_id: int,
    mr_iid: int,
    action: str,
    deep_config: DeepConfig | None = None,
):
    logger.info("Handling MR event (%s): Project %s, MR %s", action, project_id, mr_iid)
    
    await task_manager.cancel_task(project_id, mr_iid)
    
    task_manager.add_task(
        project_id,
        mr_iid,
        run_review_pipeline(project_id, mr_iid, action, deep_config=deep_config),
    )
