from pydantic import BaseModel


class AnswerBankEntryOut(BaseModel):
    semantic_key: str
    label: str
    value: str
    is_sensitive: bool
    policy: str
    version: int

    class Config:
        from_attributes = True


class AnswerBankEntryUpdate(BaseModel):
    value: str
