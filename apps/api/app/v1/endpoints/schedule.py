from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import SessionLocal
from app.models.calendar_event import CalendarEvent
from app.schemas.schedule import (
    CalendarEventCreate,
    CalendarEventOut,
    CalendarEventUpdate,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _query_calendar_events(
    db: Session,
    start: datetime | None,
    end: datetime | None,
):
    if start and end and end < start:
        raise HTTPException(status_code=400, detail="end must be greater than or equal to start")

    query = db.query(CalendarEvent)
    if start is not None:
        query = query.filter(CalendarEvent.time >= start)
    if end is not None:
        query = query.filter(CalendarEvent.time <= end)

    return query.order_by(CalendarEvent.time.asc(), CalendarEvent.id.asc()).all()


@router.get("/schedule/events", response_model=list[CalendarEventOut])
def list_schedule_events(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return _query_calendar_events(db=db, start=start, end=end)


@router.get("/admin/schedule/events", response_model=list[CalendarEventOut])
def list_schedule_events_admin(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    return _query_calendar_events(db=db, start=start, end=end)


@router.post("/admin/schedule/events", response_model=CalendarEventOut, status_code=201)
def create_schedule_event(
    data: CalendarEventCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    event = CalendarEvent(
        name=data.name,
        time=data.time,
        game=data.game,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.patch("/admin/schedule/events/{event_id}", response_model=CalendarEventOut)
def update_schedule_event(
    event_id: int,
    data: CalendarEventUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete("/admin/schedule/events/{event_id}", status_code=204)
def delete_schedule_event(
    event_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    db.delete(event)
    db.commit()
    return Response(status_code=204)
