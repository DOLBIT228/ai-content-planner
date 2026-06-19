from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response, status

from .repository import InMemoryRepository, NotFoundError
from .schemas import CampaignCreate, RegenerateRequest, serialize
from .services import ContentOSService

app = FastAPI(title="AI Content OS", version="0.1.0")
repo = InMemoryRepository()
service = ContentOSService(repo)


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


@app.post("/content-entries/{entry_id}/generate")
def generate_entry(entry_id: int):
    try:
        return serialize(service.generate_entry(entry_id))
    except NotFoundError as exc:
        raise not_found(exc)


@app.post("/content-entries/{entry_id}/regenerate")
def regenerate_entry(entry_id: int, payload: RegenerateRequest):
    try:
        return serialize(service.regenerate_entry(entry_id, payload.feedback))
    except NotFoundError as exc:
        raise not_found(exc)


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
