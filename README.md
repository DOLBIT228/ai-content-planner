# AI Content OS

Clean backend skeleton for an AI content operating system with separated strategic planning, copywriting, and human review layers.

## Product flow

```text
Campaign → AI Plan → Content Entries → AI Generate → Human Review
```

The system intentionally does **not** generate post copy during planning. Planning creates structured `ContentEntry` drafts only; writing happens per entry after the plan exists.

## Core entities

- `Campaign`: top-level container with campaign dates, status, sales/image mix, and the brand `brief`.
- `CampaignChannel`: channel-specific volume configuration for posts, carousels, reels, and stories.
- `ContentEntry`: individual planned content item with topic, goal, angle, review status, optional generated `post_text`, feedback, and AI score.

`Campaign.brief` is core context for all AI layers. If it is empty, the backend uses the fallback: `Use premium luxury marketing tone`.

## API

### Campaigns

- `POST /campaigns`
- `GET /campaigns`
- `GET /campaigns/{id}`
- `DELETE /campaigns/{id}`

### AI planning layer

- `POST /campaigns/{id}/generate-plan`

Creates draft `ContentEntry` records from campaign config, channels, sales/image ratio, brief, and knowledge base context. It never writes `post_text`.

### AI writer layer

- `POST /content-entries/{id}/generate`

Generates copy for one planned entry and moves it to `generated`.

### Regeneration and review

- `POST /content-entries/{id}/regenerate`
- `POST /content-entries/{id}/approve`
- `POST /content-entries/{id}/reject`
- `DELETE /content-entries/{id}`

## Run locally

Install backend dependencies and create your local environment file:

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your OpenRouter values:

```dotenv
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openai/gpt-4.1-mini
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=AI Content Planner
```

`OPENROUTER_API_KEY` is required for AI generation. `OPENROUTER_MODEL` is optional and defaults to `openai/gpt-4.1-mini` when omitted. The backend automatically loads `.env` at startup, so you do not need to export these variables manually.

Run the backend:

```bash
uvicorn app.main:app --reload
```

In a second terminal, install and run the React frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the React UI at:

```text
http://127.0.0.1:5173/
```

Swagger remains available at:

```text
http://127.0.0.1:8000/docs
```

For production-style serving through FastAPI, build the React app first:

```bash
cd frontend
npm run build
```

Then start the backend and open:

```text
http://127.0.0.1:8000/
```

## Test

```bash
python -m unittest discover -s tests
```
