from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.answer_bank import AnswerBankEntry
from app.models.user import User
from app.schemas.answer_bank import AnswerBankEntryOut, AnswerBankEntryUpdate
from app.services.answer_bank import SEMANTIC_KEY_REGISTRY, default_policy
from app.services.auth import get_current_user

router = APIRouter(prefix="/answer-bank", tags=["answer-bank"])


@router.get("", response_model=list[AnswerBankEntryOut])
def list_answers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = {
        row.semantic_key: row
        for row in db.query(AnswerBankEntry).filter(AnswerBankEntry.user_id == user.id)
    }
    out = []
    for key, spec in SEMANTIC_KEY_REGISTRY.items():
        row = existing.get(key)
        out.append(
            AnswerBankEntryOut(
                semantic_key=key,
                label=spec.label,
                value=row.value if row else "",
                is_sensitive=spec.is_sensitive,
                policy=row.policy if row else default_policy(spec.is_sensitive),
                version=row.version if row else 0,
            )
        )
    return out


@router.put("/{semantic_key}", response_model=AnswerBankEntryOut)
def upsert_answer(
    semantic_key: str,
    payload: AnswerBankEntryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    spec = SEMANTIC_KEY_REGISTRY.get(semantic_key)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Unknown answer bank key: {semantic_key}")

    row = (
        db.query(AnswerBankEntry)
        .filter(AnswerBankEntry.user_id == user.id, AnswerBankEntry.semantic_key == semantic_key)
        .first()
    )
    if row:
        row.value = payload.value
        row.version += 1
    else:
        row = AnswerBankEntry(
            user_id=user.id,
            semantic_key=semantic_key,
            value=payload.value,
            is_sensitive=spec.is_sensitive,
            policy=default_policy(spec.is_sensitive),
            version=1,
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return AnswerBankEntryOut(
        semantic_key=row.semantic_key,
        label=spec.label,
        value=row.value,
        is_sensitive=row.is_sensitive,
        policy=row.policy,
        version=row.version,
    )
