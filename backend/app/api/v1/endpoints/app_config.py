"""
Public application configuration for the frontend.

Lets the UI learn server-side defaults (currently the analysis date and its allowed range)
instead of hard-coding them. Contains nothing sensitive, so it is served without
authentication.
"""

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from ....core.analysis_date import MAX_ANALYSIS_DATE, MIN_ANALYSIS_DATE, default_analysis_date

router = APIRouter()


class AnalysisDateConfig(BaseModel):
    default: date
    min: date
    max: date


class AppConfigResponse(BaseModel):
    analysis_date: AnalysisDateConfig


@router.get("", response_model=AppConfigResponse)
async def get_app_config() -> AppConfigResponse:
    """Server defaults the frontend needs (GET /api/v1/config)."""
    return AppConfigResponse(
        analysis_date=AnalysisDateConfig(
            default=default_analysis_date(),
            min=MIN_ANALYSIS_DATE,
            max=MAX_ANALYSIS_DATE,
        )
    )
