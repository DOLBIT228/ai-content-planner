from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .repository import InMemoryRepository, NotFoundError
from .ai_layers import AIConfigurationError, AIResponseError
from .schemas import CampaignCreate, RegenerateRequest, serialize
from .services import ContentOSService

app = FastAPI(title="AI Content OS", version="0.1.0")
FRONTEND_DIST = Path("frontend/dist")
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
repo = InMemoryRepository()
service = ContentOSService(repo)


@app.get("/", include_in_schema=False)
def frontend():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Run the React app with `cd frontend && npm install && npm run dev`, then open http://127.0.0.1:5173/."}


def not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    if payload.sales_percentage + payload.image_percentage > 100:
        raise HTTPException(status_code=422, detail="sales_percentage + image_percentage cannot exceed 100")
    return serialize(service.create_campaign(payload))


@app.get("/campaigns")
def list_campaigns():
    return serialize(repo.list_campaigns())


@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    try:
        campaign = repo.get_campaign(campaign_id)
    except NotFoundError as exc:
        raise not_found(exc)
    return serialize({"campaign": campaign, "channels": repo.list_channels(campaign_id), "entries": repo.list_entries(campaign_id)})


@app.get("/knowledge-documents")
def list_knowledge_documents():
    return serialize(repo.list_documents())


@app.post("/knowledge-documents", status_code=status.HTTP_201_CREATED)
async def upload_knowledge_document(request: Request, filename: str = "knowledge-file", content_type: str | None = Header(default=None)):
    data = await request.body()
    if not data:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    return serialize(service.add_knowledge_document(filename, content_type or "application/octet-stream", data))


@app.delete("/knowledge-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_document(document_id: int):
    try:
        repo.delete_document(document_id)
    except NotFoundError as exc:
        raise not_found(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int):
    try:
        repo.delete_campaign(campaign_id)
    except NotFoundError as exc:
        raise not_found(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/campaigns/{campaign_id}/generate-plan")
def generate_plan(campaign_id: int):
    try:
        return serialize(service.generate_plan(campaign_id))
    except NotFoundError as exc:
        raise not_found(exc)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except AIResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/content-entries/{entry_id}/generate")
def generate_entry(entry_id: int):
    try:
        return serialize(service.generate_entry(entry_id))
    except NotFoundError as exc:
        raise not_found(exc)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except AIResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/content-entries/{entry_id}/regenerate")
def regenerate_entry(entry_id: int, payload: RegenerateRequest):
    try:
        return serialize(service.regenerate_entry(entry_id, payload.feedback))
    except NotFoundError as exc:
        raise not_found(exc)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except AIResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/content-entries/{entry_id}/approve")
def approve_entry(entry_id: int):
    try:
        return serialize(service.approve_entry(entry_id))
    except NotFoundError as exc:
        raise not_found(exc)


@app.post("/content-entries/{entry_id}/reject")
def reject_entry(entry_id: int):
    try:
        return serialize(service.reject_entry(entry_id))
    except NotFoundError as exc:
        raise not_found(exc)


@app.delete("/content-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int):
    try:
        repo.delete_entry(entry_id)
    except NotFoundError as exc:
        raise not_found(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
