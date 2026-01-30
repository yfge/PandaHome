from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..models.response import Response
from ..services.status import StatusService

router = APIRouter(prefix="/api", tags=["status"])


def get_status_service(request: Request) -> StatusService:
    service = getattr(request.app.state, "status_service", None)
    if isinstance(service, StatusService):
        return service

    upnp_service = getattr(request.app.state, "upnp_service", None)
    service = StatusService(upnp_service=upnp_service)
    request.app.state.status_service = service
    return service


@router.get("/status")
async def get_status_snapshot(status_service: StatusService = Depends(get_status_service)):
    """Return a cached system status snapshot (CPU/memory/disk/services)."""
    try:
        return Response.success(data=status_service.get_status())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
