import asyncio
import logging

from deep_hook_review import run_review, DeepConfig, generate_review_markdown

from app.gitlab_client import GitLabClient
from app.services.change_converter import gitlab_changes_to_deep_hook

logger = logging.getLogger(__name__)

LOADER_BODY = "Analyzing code changes..."
REVIEW_HEADER = "🧠 **DeepHook AI Review**"

LOADER_COMMENT = f"""{REVIEW_HEADER} <img src="https://i.gifer.com/ZZ5H.gif" width="20"/>

{LOADER_BODY}"""

async def _get_last_deephook_note(client: GitLabClient, project_id: int, mr_iid: int) -> tuple[int | None, bool]:
    """
    Get the last DeepHook comment by the bot.
    Returns (note_id, is_loader).
    - If last is loader: reuse it (is_loader=True).
    - If last is completed review: we'll update it to loader (is_loader=False).
    - If none: (None, False) -> create new.
    """
    bot_id = (await client.get_current_user())["id"]
    notes = await client.get_mr_notes(project_id, mr_iid)
    bot_deephook = [
        n for n in notes
        if n.get("author", {}).get("id") == bot_id
        and (n.get("body") or "").strip().startswith(REVIEW_HEADER)
    ]
    if not bot_deephook:
        return None, False
    last = max(bot_deephook, key=lambda n: n["created_at"])
    body = (last.get("body") or "")
    is_loader = LOADER_BODY in body
    return last["id"], is_loader


async def run_review_pipeline(
    project_id: int,
    mr_iid: int,
    action: str = "open",
    *,
    deep_config: DeepConfig | None = None,
):
    client = GitLabClient()
    note_id = None

    try:
        last_id, is_loader = await _get_last_deephook_note(client, project_id, mr_iid)

        if last_id is not None:
            note_id = last_id
            if not is_loader:
                await client.update_mr_note(project_id, mr_iid, note_id, LOADER_COMMENT)
        else:
            new = await client.post_mr_comment(project_id, mr_iid, LOADER_COMMENT)
            note_id = new["id"]

        raw_changes = await client.get_mr_changes(project_id, mr_iid)
        converted = gitlab_changes_to_deep_hook(raw_changes)

        previous_review_text: str | None = None
        if action == "update":
            previous_reviews = await get_previous_reviews(client, project_id, mr_iid)
            if previous_reviews:
                previous_review_text = previous_reviews[-1]["body"]

        config = deep_config if deep_config is not None else DeepConfig()
        review = await run_review(
            converted,
            config,
            previous_review=previous_review_text,
        )

        file_count = len(converted)
        result = f"""{REVIEW_HEADER}

✅ Analysis Complete

Summary:
- {file_count} files reviewed (non-essential paths filtered out)
- tools called {len (review.tool_calls_used)} : {", ".join(review.tool_calls_used)}

{generate_review_markdown(review)}
"""
        await client.update_mr_note(project_id, mr_iid, note_id, result)

    except asyncio.CancelledError:
        logger.info(f"Review cancelled for Project {project_id} MR {mr_iid}")
        if note_id:
            try:
                await client.update_mr_note(project_id, mr_iid, note_id, f"{REVIEW_HEADER}\n\n⏸ Cancelled.")
            except Exception:
                pass
        raise
    except Exception as e:
        logger.error(f"Error in review pipeline: {e}")
        if note_id:
            try:
                await client.update_mr_note(project_id, mr_iid, note_id, f"{REVIEW_HEADER}\n\n❌ Error: {e}")
            except Exception:
                pass


async def get_previous_reviews(client: GitLabClient, project_id: int, mr_iid: int):
    try:
        bot_id = (await client.get_current_user())["id"]
        notes = await client.get_mr_notes(project_id, mr_iid)
        reviews = []
        for note in notes:
            if note.get("author", {}).get("id") != bot_id:
                continue
            body = (note.get("body") or "").strip()
            if body.startswith(REVIEW_HEADER) and LOADER_BODY not in body and "✅ Analysis Complete" in body:
                reviews.append({"id": note["id"], "body": body, "created_at": note["created_at"]})
        reviews.sort(key=lambda r: r["created_at"])
        return reviews
    except Exception as e:
        logger.warning(f"Failed to fetch previous reviews: {e}")
        return []
