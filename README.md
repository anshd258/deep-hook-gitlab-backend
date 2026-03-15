# GitLab Webhook Receiver

A FastAPI backend to receive GitLab webhook events and automate Merge Request interactions.

## Features

- **Merge Request Events**:
  - Handles MR Open events.
  - Handles MR Update events.
  - Detects new commits pushed to MRs.
- **Async Processing**: Uses FastAPI BackgroundTasks to handle events without blocking the webhook response.

## Setup with uv

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and running the application.

1.  **Install uv**:
    If you haven't already, install `uv`:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Install Dependencies**:
    ```bash
    uv sync
    ```

3.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your GitLab details:
    ```bash
    cp .env.example .env
    # Edit .env with your GITLAB_URL and GITLAB_TOKEN
    ```
    - `GITLAB_URL`: Your GitLab instance URL (e.g., `https://gitlab.com`).
    - `GITLAB_TOKEN`: A Personal Access Token with `api` scope.

4.  **Run Server**:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

## Usage

### GitLab Webhook Configuration

1. Go to your GitLab Project > Settings > Webhooks.
2. URL: `http://<your-server-ip>:8000/webhook/gitlab`
3. Secret Token: (Optional, not implemented in this MVP but recommended for production)
4. Trigger:
   - Select "Merge request events".
   - Select "Comments".
5. SSL verification: Enable if using HTTPS.

## Development

- **Run Tests**:
  Use the provided `test_webhook.sh` script to send mock webhook events:
  ```bash
  chmod +x test_webhook.sh
  ./test_webhook.sh
  ```

- **Linting**:
  ```bash
  uv run ruff check .
  ```
