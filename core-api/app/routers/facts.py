import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.fact_base import FactBase
from app.models.user import User
from app.schemas.fact import FactOut, FactUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/facts", tags=["facts"])


def _get_owned_fact(fact_id: uuid.UUID, db: Session, user: User) -> FactBase:
    fact = db.get(FactBase, fact_id)
    if not fact or fact.user_id != user.id:
        raise HTTPException(status_code=404, detail="Fact not found")
    return fact


@router.get("", response_model=list[FactOut])
def list_facts(
    confirmed: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(FactBase).filter(FactBase.user_id == user.id)
    if confirmed is True:
        query = query.filter(FactBase.confirmed_at.isnot(None))
    elif confirmed is False:
        query = query.filter(FactBase.confirmed_at.is_(None))
    return query.all()


@router.patch("/{fact_id}", response_model=FactOut)
def edit_fact(
    fact_id: uuid.UUID,
    payload: FactUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fact = _get_owned_fact(fact_id, db, user)
    if fact.confirmed_at is not None:
        raise HTTPException(status_code=400, detail="Cannot edit a confirmed fact; create a new version instead")
    fact.payload = payload.payload
    db.commit()
    db.refresh(fact)
    return fact


@router.post("/{fact_id}/confirm", response_model=FactOut)
def confirm_fact(
    fact_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fact = _get_owned_fact(fact_id, db, user)
    fact.confirmed_at = func.now()
    db.commit()
    db.refresh(fact)
    return fact


@router.delete("/{fact_id}", status_code=204)
def reject_fact(
    fact_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fact = _get_owned_fact(fact_id, db, user)
    if fact.confirmed_at is not None:
        raise HTTPException(status_code=400, detail="Cannot delete a confirmed fact")
    db.delete(fact)
    db.commit()
