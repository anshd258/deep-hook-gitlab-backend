from fastapi import FastAPI
from app.webhook import router
from app.config import settings
import logging
from dotenv import load_dotenv
import os

load_dotenv()

print(os.getenv("ANTHROPIC_API_KEY"))
# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

deephook = FastAPI(title="GitLab Webhook Receiver")

deephook.include_router(router)

@deephook.get("/")
def read_root():
    return {"message": "GitLab Webhook Receiver is running"}
