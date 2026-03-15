import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class GitLabClient:
    def __init__(self):
        self.base_url = settings.GITLAB_URL.rstrip('/')
        self.headers = {"PRIVATE-TOKEN": settings.GITLAB_TOKEN}

    async def get_current_user(self):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v4/user"
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching current user: {e.response.text}")
                raise

    async def get_mr_notes(self, project_id: int, mr_iid: int, per_page: int = 100):
        """Fetch all MR notes, paginating until no more pages."""
        all_notes = []
        page = 1
        async with httpx.AsyncClient() as client:
            while True:
                url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes?per_page={per_page}&page={page}"
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    notes = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Error fetching MR notes: {e.response.text}")
                    raise
                if not notes:
                    break
                all_notes.extend(notes)
                if len(notes) < per_page:
                    break
                page += 1
        return all_notes

    async def delete_mr_note(self, project_id: int, mr_iid: int, note_id: int):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes/{note_id}"
            logger.info(f"Deleting comment {note_id} from project {project_id} MR {mr_iid}")
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"Error deleting MR note: {e.response.text}")
                raise

    async def get_mr_changes(self, project_id: int, mr_iid: int):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
            logger.info(f"Fetching changes for project {project_id} MR {mr_iid} from {url}")
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching MR changes: {e.response.text}")
                raise

    async def post_mr_comment(self, project_id: int, mr_iid: int, body: str):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
            try:
                response = await client.post(url, headers=self.headers, json={"body": body})
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error posting MR comment: {e.response.text}")
                raise

    async def update_mr_note(self, project_id: int, mr_iid: int, note_id: int, body: str):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes/{note_id}"
            try:
                response = await client.put(url, headers=self.headers, json={"body": body})
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error updating MR note: {e.response.text}")
                raise
