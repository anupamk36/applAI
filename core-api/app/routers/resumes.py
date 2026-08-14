import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.fact_base import FactBase
from app.models.resume import Resume
from app.models.user import User
from app.schemas.fact import ResumeOut, ResumeUploadResult
from app.services.auth import get_current_user
from app.services.resume_parser import extract_text, parse_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("", response_model=ResumeUploadResult, status_code=201)
def upload_resume(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported")

    file_bytes = file.file.read()

    storage_dir = os.path.join(settings.resume_storage_dir, str(user.id))
    os.makedirs(storage_dir, exist_ok=True)
    storage_key = os.path.join(storage_dir, f"{uuid.uuid4()}{ext}")
    with open(storage_key, "wb") as f:
        f.write(file_bytes)

    resume = Resume(
        user_id=user.id,
        kind="uploaded_original",
        storage_key=storage_key,
        original_filename=file.filename,
    )
    db.add(resume)
    db.flush()

    try:
        text = extract_text(file_bytes, file.filename)
        candidate_facts = parse_resume(text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    resume.parsed_at = func.now()

    fact_rows = [
        FactBase(user_id=user.id, kind=f["kind"], payload=f["payload"], source="resume_upload")
        for f in candidate_facts
    ]
    db.add_all(fact_rows)
    db.commit()

    for row in fact_rows:
        db.refresh(row)
    db.refresh(resume)

    return ResumeUploadResult(resume=ResumeOut.model_validate(resume), candidate_facts=fact_rows)


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Resume).filter(Resume.user_id == user.id).all()
