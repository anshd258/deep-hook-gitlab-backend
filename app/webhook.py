from fastapi import APIRouter, Request, Header, BackgroundTasks, HTTPException
from app.handlers.mr_handlers import handle_mr_event
from app.gitlab_client import GitLabClient
from app.services.review_service import REVIEW_HEADER
from app.deep_config import load_project_registry, DeepConfigError
from deep_hook_review.config import config_from_yml
from deep_hook_review.core import DeepHookError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def _comment_missing_or_invalid_deep_config(
    *,
    project_id: int,
    mr_iid: int,
    config_path: str,
    error: Exception,
) -> None:
    body = f"""{REVIEW_HEADER}

⚠️ Deep config is missing/invalid/not set for this project.

Expected config at: `{config_path}`
Error: `{error}`

DeepHook will not run a review until this is fixed."""
    try:
        client = GitLabClient()
        await client.post_mr_comment(project_id, mr_iid, body)
    except Exception as e:
        logger.warning(
            "Failed to post missing/invalid deep config comment "
            "(project_id=%s, mr_iid=%s, config_path=%s): %s",
            project_id,
            mr_iid,
            config_path,
            e,
        )


@router.post("/webhook/gitlab")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gitlab_event: str = Header(None),
):
    if not x_gitlab_event:
        logger.warning("Missing X-Gitlab-Event header")
        raise HTTPException(status_code=400, detail="Missing X-Gitlab-Event header")

    try:
        payload = await request.json()
    except Exception:
        logger.warning("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info("Received event: %s", x_gitlab_event)

    if x_gitlab_event == "Merge Request Hook":
        try:
            project_id = int(payload["project"]["id"])
            mr_iid = int(payload["object_attributes"]["iid"])
            action = payload["object_attributes"]["action"]

            if action in ["open", "update"]:
                try:
                    registry = load_project_registry()
                except DeepConfigError as e:
                    logger.error("Failed to load project registry: %s", e)
                    return {"status": "ok"}

                config_path = registry.get(project_id)
                if not config_path:
                    logger.info(
                        "Project %s is not registered in deep registry; ignoring MR event "
                        "(mr_iid=%s, action=%s)",
                        project_id,
                        mr_iid,
                        action,
                    )
                    return {"status": "ok"}

                try:
                    deep_config = config_from_yml(config_path)
                except DeepHookError as e:
                    logger.error(
                        "Failed to load deep config for project %s at %s: %s",
                        project_id,
                        config_path,
                        e,
                    )
                    if action == "open":
                        await _comment_missing_or_invalid_deep_config(
                            project_id=project_id,
                            mr_iid=mr_iid,
                            config_path=config_path,
                            error=e,
                        )
                    return {"status": "ok"}

                background_tasks.add_task(
                    handle_mr_event, project_id, mr_iid, action, deep_config
                )

        except KeyError as e:
            logger.error("Missing key in Merge Request Hook payload: %s", e)

    return {"status": "ok"}
