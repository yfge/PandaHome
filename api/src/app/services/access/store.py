from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...models.published_service import PublishedService
from ...schemas.access import ServiceConfig, ServiceView


def list_services(db: Session) -> list[PublishedService]:
    return list(db.query(PublishedService).order_by(PublishedService.id).all())


def service_view(row: PublishedService, *, checked_since=None, stale_after=None) -> ServiceView:
    config = {key: getattr(row, key) for key in ServiceConfig.model_fields}
    view = ServiceView(id=row.id, **config, **{k: v for k, v in (row.runtime or {}).items() if k not in config})
    checked = view.last_checked
    if checked and checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    expired = checked and stale_after and (datetime.now(timezone.utc) - checked).total_seconds() > stale_after
    previous_run = checked and checked_since and checked < checked_since
    if view.enabled and (expired or previous_run):
        view.status, view.reason_code, view.external_verified = "pending", "checking", False
    return view


def save_runtime(db: Session, row: PublishedService, **updates) -> None:
    row.runtime = {**(row.runtime or {}), **updates}
    db.commit()
