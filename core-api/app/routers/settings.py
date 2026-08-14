from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User, UserSettings
from app.schemas.preferences import SettingsOut, SettingsUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_settings(db: Session, user: User) -> UserSettings:
    settings = db.get(UserSettings, user.id)
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_settings(db, user)


@router.patch("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = _get_settings(db, user)
    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings
