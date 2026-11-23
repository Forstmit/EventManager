from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .schemas import EventCreate, EventRead
from .services import EventService
from .exceptions import (
    EventManagerError, EventNotFoundError, EventCapacityError,
    InvalidRegistrationError
)
from .logger import logger

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EventManager", description="Система организации мероприятий")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )


@app.get("/api/events", response_model=list[EventRead])
def list_events(db: Session = Depends(get_db)):
    return EventService(db).list_events()

@app.get("/api/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    try:
        return EventService(db).get_event(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/api/events", response_model=EventRead, status_code=201)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    try:
        return EventService(db).create_event(data)
    except EventManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.put("/api/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, data: EventCreate, db: Session = Depends(get_db)):
    try:
        return EventService(db).update_event(event_id, data)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EventManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    try:
        EventService(db).delete_event(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/api/events/{event_id}/registration", response_model=EventRead)
def change_registration(event_id: int, delta: int, db: Session = Depends(get_db)):
    try:
        return EventService(db).change_registration(event_id, delta)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (EventCapacityError, InvalidRegistrationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/statistics")
def statistics(db: Session = Depends(get_db)):
    return EventService(db).get_statistics()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("Непредвиденная ошибка при обработке %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})
