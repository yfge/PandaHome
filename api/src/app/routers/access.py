"""Authenticated management of persisted public entries and their maintenance."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth.auth import require_role
from ..database.database import get_db
from ..models.db_models import User
from ..models.published_service import PublishedService
from ..models.response import Response
from ..models.user import UserRole
from ..schemas.access import ServiceConfig
from ..schemas.relay import RelayProfile
from ..services.access.controller import AccessController
from ..services.access.store import list_services, service_view
from ..services.relay_profile import RelayProfileError


async def active_admin(user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="An active administrator account is required.")
    return user


router = APIRouter(prefix="/api/access", tags=["public access"], dependencies=[Depends(active_admin)])


def get_access_controller(request: Request) -> AccessController:
    return request.app.state.access_controller


@router.get("/relay-config")
async def relay_config(controller: AccessController = Depends(get_access_controller)):
    try:
        return Response.success(data=controller.relay_profile())
    except RelayProfileError:
        raise HTTPException(status_code=503, detail="Unable to read relay configuration.") from None


@router.put("/relay-config")
async def update_relay_config(request: Request, controller: AccessController = Depends(get_access_controller)):
    # A normal FastAPI/Pydantic model error can echo the complete request body
    # (including a new token). Validate locally and expose no error.input data.
    try:
        profile = RelayProfile.model_validate(await request.json())
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid relay configuration.") from None
    try:
        async with controller.lock:
            result = await controller.save_relay_profile(profile)
        return Response.success(data=result)
    except Exception:
        raise HTTPException(status_code=503, detail="Unable to apply relay configuration. Previous settings retained.") from None


def get_row(db: Session, service_id: int) -> PublishedService:
    row = db.get(PublishedService, service_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Public service not found.")
    return row


def persist(db: Session, row: PublishedService, config: ServiceConfig) -> None:
    if config.domain:
        for other in list_services(db):
            if other.id != row.id and other.domain:
                hostname = other.domain if other.rr == "@" else f"{other.rr}.{other.domain}"
                if hostname == config.hostname:
                    raise HTTPException(status_code=409, detail="This DNS hostname is reserved by another service.")
    for key, value in config.model_dump().items():
        setattr(row, key, value)
    runtime = row.runtime or {}
    row.runtime = {k: v for k, v in runtime.items() if k in {"mapping", "alert_failed"}}
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="This public port and protocol are reserved by another service."
        ) from None


@router.get("/state")
async def state(db: Session = Depends(get_db), controller: AccessController = Depends(get_access_controller)):
    return Response.success(
        data={
            "network": controller.network,
            "relay": controller.relay.status(),
            "services": [
                service_view(
                    row, checked_since=getattr(controller, "started_at", None), stale_after=controller.interval * 3
                )
                for row in list_services(db)
            ],
            "poll_interval_seconds": controller.interval,
        }
    )


@router.post("/detect")
async def detect(controller: AccessController = Depends(get_access_controller)):
    report = await controller.detect()
    controller.wake()
    return Response.success(data=report)


@router.post("/services")
async def create(
    config: ServiceConfig, db: Session = Depends(get_db), controller: AccessController = Depends(get_access_controller)
):
    async with controller.lock:
        row = PublishedService()
        persist(db, row, config)
        controller.wake()
        return Response.success(data=service_view(row))


@router.put("/services/{service_id}")
async def update(
    service_id: int,
    config: ServiceConfig,
    db: Session = Depends(get_db),
    controller: AccessController = Depends(get_access_controller),
):
    async with controller.lock:
        row = get_row(db, service_id)
        persist(db, row, config)
        controller.wake()
        return Response.success(data=service_view(row))


@router.delete("/services/{service_id}")
async def delete(
    service_id: int, db: Session = Depends(get_db), controller: AccessController = Depends(get_access_controller)
):
    async with controller.lock:
        row = get_row(db, service_id)
        try:
            await controller.reconciler.cleanup(db, row)
            remaining = [
                controller.reconciler.relay_mapping(r)
                for r in list_services(db)
                if r.id != row.id and r.enabled and (r.runtime or {}).get("active_mode") == "relay"
            ]
            await controller.relay.apply(remaining)
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Entry cleanup failed. Configuration retained; retry when the router is available.",
            ) from None
        db.delete(row)
        db.commit()
        controller.wake()
        return Response.success(data={"deleted": service_id})


@router.post("/services/{service_id}/check")
async def check(
    service_id: int, db: Session = Depends(get_db), controller: AccessController = Depends(get_access_controller)
):
    get_row(db, service_id)
    await controller.reconcile()
    db.expire_all()
    return Response.success(data=service_view(get_row(db, service_id)))
