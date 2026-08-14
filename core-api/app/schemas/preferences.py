from pydantic import BaseModel, Field


class JobPreferences(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    target_countries: list[str] = Field(default_factory=lambda: ["IN"])
    ctc_min: float | None = None
    ctc_max: float | None = None
    industries: list[str] = Field(default_factory=list)
    company_size_bands: list[str] = Field(default_factory=list)
    blocklist_companies: list[str] = Field(default_factory=list)


class SettingsOut(BaseModel):
    threshold: float
    daily_cap: int
    auto_apply_enabled: bool
    calibration_complete: bool
    job_preferences: JobPreferences

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    threshold: float | None = Field(default=None, ge=0, le=1)
    daily_cap: int | None = Field(default=None, ge=1, le=25)
    auto_apply_enabled: bool | None = None
    job_preferences: JobPreferences | None = None
