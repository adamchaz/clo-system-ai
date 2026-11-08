"""
Analysis (as-of) date handling.

The analysis date is the "as of" date for portfolio calculations: which thresholds are in
force, time-to-maturity measures, reinvestment status, and QuantLib valuations. It is NOT the
wall-clock time - audit timestamps, token expiry etc. should keep using datetime.now().

Rules:
  * The default comes only from settings.default_analysis_date (env DEFAULT_ANALYSIS_DATE).
  * Endpoints take the date through analysis_date_param (query string) or
    resolve_analysis_date (request bodies) and pass it down explicitly.
  * Business logic never substitutes date.today() for a missing analysis date.
  * QuantLib work for a specific date runs inside ql_evaluation_date(d).

Note that every deal's holdings are a snapshot as of the workbook's analysis date
(2016-03-23); choosing another date shifts time-based measures but does not roll the
portfolio forward.
"""

import threading
from contextlib import contextmanager
from datetime import date, datetime
from typing import Iterator, Optional, Union

import QuantLib as ql
from fastapi import HTTPException, Query, status

from .config import settings

# Supported range: before the earliest deal (2012) through well past the latest stated
# maturity (2028). Fixed bounds, deliberately not tied to the system clock.
MIN_ANALYSIS_DATE = date(2010, 1, 1)
MAX_ANALYSIS_DATE = date(2035, 12, 31)

DateInput = Union[None, str, date, datetime]


def default_analysis_date() -> date:
    """The configured default analysis date."""
    return settings.default_analysis_date


def resolve_analysis_date(value: DateInput = None) -> date:
    """Turn an optional request value into a validated analysis date.

    Accepts None (-> default), a date, a datetime, or an ISO string such as
    "2016-03-23" or "2016-03-23T00:00:00Z". Raises ValueError for unparseable input or a
    date outside [MIN_ANALYSIS_DATE, MAX_ANALYSIS_DATE].
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        resolved = default_analysis_date()
    elif isinstance(value, datetime):
        resolved = value.date()
    elif isinstance(value, date):
        resolved = value
    elif isinstance(value, str):
        try:
            resolved = datetime.fromisoformat(value.strip().replace("Z", "+00:00")).date()
        except ValueError:
            raise ValueError(f"Invalid analysis_date '{value}'; expected YYYY-MM-DD") from None
    else:
        raise ValueError(f"Invalid analysis_date type: {type(value).__name__}")

    if not (MIN_ANALYSIS_DATE <= resolved <= MAX_ANALYSIS_DATE):
        raise ValueError(
            f"analysis_date {resolved.isoformat()} is outside the supported range "
            f"{MIN_ANALYSIS_DATE.isoformat()} to {MAX_ANALYSIS_DATE.isoformat()}"
        )
    return resolved


def resolve_analysis_date_or_422(value: DateInput = None) -> date:
    """resolve_analysis_date for request handlers: invalid input becomes HTTP 422."""
    try:
        return resolve_analysis_date(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def analysis_date_param(
    analysis_date: Optional[date] = Query(
        None,
        description="As-of date for the calculation (YYYY-MM-DD). Defaults to the system "
                    "analysis date (DEFAULT_ANALYSIS_DATE, 2016-03-23).",
    )
) -> date:
    """FastAPI dependency for the `analysis_date` query parameter."""
    return resolve_analysis_date_or_422(analysis_date)


# QuantLib keeps its evaluation date in a process-wide singleton, so concurrent requests
# for different dates would overwrite each other. Serialize QuantLib sections.
_ql_lock = threading.RLock()


def _to_ql_date(d: date) -> ql.Date:
    return ql.Date(d.day, d.month, d.year)


@contextmanager
def ql_evaluation_date(analysis_date: date) -> Iterator[None]:
    """Run QuantLib calculations as of `analysis_date`, restoring the previous date after.

    Holds a process-wide lock for the duration, so keep the block limited to QuantLib work.
    """
    with _ql_lock:
        instance = ql.Settings.instance()
        previous = instance.evaluationDate
        instance.evaluationDate = _to_ql_date(analysis_date)
        try:
            yield
        finally:
            instance.evaluationDate = previous
