"""Private TCP access through frp XTCP, with an optional STCP fallback."""

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..auth.auth import require_role
from ..database.database import get_db
from ..models.db_models import User
from ..models.p2p_service import P2PService
from ..models.response import Response
from ..models.user import UserRole
from ..schemas.p2p import P2PServiceConfig
from ..services.p2p import P2PManager


async def active_admin(user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


router = APIRouter(prefix="/api/p2p", tags=["p2p"], dependencies=[Depends(active_admin)])


def get_p2p_manager(request: Request) -> P2PManager:
    return request.app.state.p2p_manager


def _service(db: Session, service_id: int) -> P2PService:
    row = db.get(P2PService, service_id)
    if row is None:
        raise HTTPException(status_code=404, detail="P2P service not found")
    return row


@router.get("")
async def get_state(db: Session = Depends(get_db), manager: P2PManager = Depends(get_p2p_manager)):
    """Inspect local provider state; this does not assert that a peer is connected."""
    rows = db.query(P2PService).order_by(P2PService.id).all()
    return Response.success(data={
        "provider": manager.status(),
        "services": [manager.service_view(row).model_dump() for row in rows],
    })


@router.post("/services", status_code=201)
async def create_service(
    config: P2PServiceConfig, db: Session = Depends(get_db), manager: P2PManager = Depends(get_p2p_manager),
):
    """Persist a private TCP target and reconcile the home-side frpc."""
    row = P2PService(**config.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    await manager.reconcile()
    return Response.success(data=manager.service_view(row).model_dump())


@router.put("/services/{service_id}")
async def update_service(
    service_id: int, config: P2PServiceConfig,
    db: Session = Depends(get_db), manager: P2PManager = Depends(get_p2p_manager),
):
    """Update or disable a target; disabling removes both provider proxy types."""
    row = _service(db, service_id)
    for key, value in config.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    await manager.reconcile()
    return Response.success(data=manager.service_view(row).model_dump())


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: int, db: Session = Depends(get_db), manager: P2PManager = Depends(get_p2p_manager),
):
    """Remove a target and reconcile the remaining provider proxies."""
    row = _service(db, service_id)
    db.delete(row)
    db.commit()
    await manager.reconcile()
    return Response.success(data={"deleted": True})


@router.post("/services/{service_id}/rotate-key")
async def rotate_key(
    service_id: int, db: Session = Depends(get_db), manager: P2PManager = Depends(get_p2p_manager),
):
    """Replace this service's access key; visitors need a new configuration."""
    row = _service(db, service_id)
    row.secret_key = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(row)
    await manager.reconcile()
    return Response.success(data=manager.service_view(row).model_dump())


@router.post("/reconcile")
async def reconcile(manager: P2PManager = Depends(get_p2p_manager)):
    """Retry provider setup without claiming a successful remote connection."""
    await manager.reconcile()
    return Response.success(data=manager.status())


@router.get("/services/{service_id}/visitor", response_class=PlainTextResponse)
async def visitor_config(
    service_id: int, bind_port: int = Query(default=18080, ge=1, le=65535),
    db: Session = Depends(get_db), manager: P2PManager = Depends(get_p2p_manager),
):
    """Download credential-bearing visitor TOML; never return it in normal status."""
    row = _service(db, service_id)
    try:
        content = manager.render_visitor(row, bind_port=bind_port)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PlainTextResponse(content, headers={
        "Content-Disposition": f'attachment; filename="pandahome-p2p-{service_id}.toml"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })


@router.get("/ca", response_class=PlainTextResponse)
async def trusted_ca(manager: P2PManager = Depends(get_p2p_manager)):
    """Export the configured public CA so visitors can verify the frps server."""
    configured = manager.config.tls_trusted_ca_file
    if not configured:
        raise HTTPException(status_code=409, detail="A trusted CA file is not configured")
    try:
        path = Path(configured).expanduser()
        if path.stat().st_size > 1024 * 1024:
            raise OSError("Certificate file too large")
        content = path.read_text(encoding="ascii")
        if "PRIVATE KEY" in content or "-----BEGIN CERTIFICATE-----" not in content:
            raise ValueError("Not a public CA certificate")
    except (OSError, UnicodeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail="The public CA certificate could not be read") from exc
    return PlainTextResponse(content, headers={
        "Content-Disposition": 'attachment; filename="frps-ca.crt"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })
