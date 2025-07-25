from typing import Annotated
from fastapi import APIRouter, Path, Request, Response
from fastapi.params import Form
from sqlmodel import Session, func, select
from zoneinfo import ZoneInfo

from app.tools.home import home

from .model import Notes
from app.tools.engine import engine

notes_router = APIRouter()

@notes_router.get("/")
async def read_notes(request: Request):
    user_timezone = ZoneInfo(request.headers.get("x-vercel-ip-timezone")) if request.headers.get("x-vercel-ip-timezone") else ZoneInfo("UTC")
    user_uid = request.state.auth["user_id"]
    
    with Session(engine) as session:
        notes_query = session.exec(select(Notes.uid, Notes.note, Notes.created_at, Notes.updated_at)
          .where(Notes.user_uid == user_uid)
          .order_by(func.coalesce(Notes.updated_at, Notes.created_at).desc())
          .limit(10))
        notes_data = notes_query.all()

        notes = []
        
        for note in notes_data:
            notes.append({
                "uid": note.uid,
                "note": note.note,
                "created_at": note.created_at.replace(tzinfo=ZoneInfo("UTC"))
                  .astimezone(user_timezone).strftime("%B %d, %Y %H:%M:%S"),
                "updated_at": note.updated_at.replace(tzinfo=ZoneInfo("UTC"))
                  .astimezone(user_timezone).strftime("%B %d, %Y %H:%M:%S")
                  if note.updated_at else None
            })

        html_string = home.get_template("notes/index.html").render(
            request=request,
            notes=notes,
            user_timezone=user_timezone
        )
        return Response(content=html_string, media_type="text/html")

@notes_router.post("/create/")
async def create_notes(request: Request, note: str = Form()):
    """
    Create a new note.
    """
    user_uid = request.state.auth["user_id"]
    new_note = Notes(note=note, user_uid=user_uid)
    with Session(engine) as session:
        session.add(new_note)
        session.commit()
        session.refresh(new_note)
    return {"message": "Note created successfully", "note_id": new_note.uid}

@notes_router.post("/update/")
async def update_note(request: Request, uid: str = Form(), note: str = Form()):
    """
    Update an existing note.
    """
    user_uid = request.state.auth["user_id"]
    with Session(engine) as session:
        note_query = session.exec(select(Notes).where(Notes.uid == uid, Notes.user_uid == user_uid))
        existing_note = note_query.first()
        if not existing_note:
            return Response(status_code=404, content="Note not found")
        
        existing_note.note = note
        session.add(existing_note)
        session.commit()
        session.refresh(existing_note)
    
    return {"message": "Note updated successfully", "note_id": existing_note.uid}

@notes_router.get("/{uid:int}/")
async def read_note(request: Request, uid: int):
    """
    Read a specific note by its UID.
    """
    user_uid = request.state.auth["user_id"]
    with Session(engine) as session:
        note_query = session.exec(select(Notes.note, Notes.uid).where(Notes.uid == uid, Notes.user_uid == user_uid))
        note = note_query.first()
        if not note:
            return Response(status_code=404, content="Note not found")
        
        html_string = home.get_template("notes/uid/index.html").render(
            request=request,
            note=note,
            user_timezone=ZoneInfo("UTC")
        )
        return Response(content=html_string, media_type="text/html")
