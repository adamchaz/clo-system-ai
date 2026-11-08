# Analysis Date System

**Last updated**: November 8, 2026 (rewritten after the analysis-date rework, commits
`a939a4a`, `49c4338`, `62f451f`, `dfc9cea`, `c9c4fde`)

## Overview

The **analysis date** is the "as of" date for portfolio calculations: which concentration
thresholds are in force, time-to-maturity measures (days to maturity, long-dated tests,
weighted average life), reinvestment status, and QuantLib valuations.

Three kinds of date are kept separate:

| Concept | What it is | Where it lives |
|---|---|---|
| **Analysis date** | The as-of date a calculation runs for. Defaults to 2016-03-23; users can pick another. | `settings.default_analysis_date`, request parameters, frontend global state |
| **Data snapshot date** | The date a deal's holdings, ratings and LIBOR are a snapshot of. | `clo_deals.data_as_of` (2016-03-23 for all ten deals) |
| **Wall-clock time** | Real current time - audit timestamps, token expiry, file names. | `datetime.now(...)` |

### Why 2016-03-23

Every "Mag N Inputs" tab in `TradeHypoPrelimv32.xlsm` has `Analysis date = 2016-03-23`
(cell C3, repeated in the CLO Inputs block). The deals (MAG6-MAG17, 2012-2016 vintages), their
holdings, ratings and the LIBOR rate (~0.61%) all reflect that date. Analysing them against the
real current date would make every deal look past its reinvestment period and close to maturity.

### What changing the date does - and doesn't do

Picking another analysis date (e.g. 2018-06-30) shifts **time-based** measures: years to
maturity, long-dated asset tests, reinvestment status, which thresholds apply. It does **not**
roll holdings, ratings or prices forward - there is no projection. The UI says so whenever the
analysis date differs from a deal's snapshot date (see [Data snapshot date](#data-snapshot-date)).

---

## Configuration

```bash
DEFAULT_ANALYSIS_DATE=2016-03-23   # default when a request doesn't specify one
```

- Supported range for any requested date: **2010-01-01 to 2035-12-31** (fixed bounds, not tied
  to the system clock). Outside it - or unparseable - the API returns **422**.
- Single source of truth: `backend/app/core/config.py` (`Settings.default_analysis_date`). No
  other backend or frontend code hard-codes 2016-03-23.
- QuantLib's global evaluation date is initialised to this value at startup (it used to be the
  real current date). `QUANTLIB_DATE_TODAY_AUTO` was removed.

---

## Backend

### `app/core/analysis_date.py`

| Function | Use |
|---|---|
| `default_analysis_date()` | The configured default. |
| `resolve_analysis_date(value)` | `None` / date / datetime / ISO string -> validated `date`. Raises `ValueError`. |
| `resolve_analysis_date_or_422(value)` | Same, raising HTTP 422 - for request bodies. |
| `analysis_date_param` | FastAPI dependency for the `analysis_date` query parameter. |
| `ql_evaluation_date(d)` | Context manager: runs QuantLib work as of `d`, restoring the previous date afterwards, under a process-wide lock (QuantLib's setting is global). |
| `MIN_ANALYSIS_DATE`, `MAX_ANALYSIS_DATE` | The supported range. |

```python
# Query parameter
@router.get("/{deal_id}/summary")
async def summary(deal_id: str, analysis_date: date = Depends(analysis_date_param)): ...

# Request body - resolve BEFORE any try/except Exception, or a 422 becomes a 500
analysis_date = resolve_analysis_date_or_422(request.analysis_date)

# QuantLib pricing for a specific date
with ql_evaluation_date(analysis_date):
    npv = bond.NPV()
```

### Rules for application code

1. **Business logic never reads the calendar date.** Services, models and repositories must not
   call `date.today()` or `datetime.today()`; they take the analysis date explicitly. Enforced by
   Ruff rule TID251 (`cd backend && ruff check app`, config in `backend/ruff.toml`). Genuine
   wall-clock uses carry `# noqa: TID251` with a reason. `datetime.now()` remains allowed for
   timestamps.
2. **Entry points require the date.** These have no default - a missing date is a `TypeError`:
   - `ConcentrationTestIntegrationService.run_portfolio_concentration_tests`
   - `ConcentrationThresholdService.get_deal_thresholds`, `.get_deal_specific_thresholds`
   - `ConcentrationThresholdRepository.get_all_deal_thresholds`, `.get_deal_specific_thresholds_only`
   - `DatabaseDrivenConcentrationTest.initialize_for_deal`
   - `CreditMigrationService.run_portfolio_simulation`, `.run_deal_specific_simulation`
   - `RiskAnalyticsService.calculate_portfolio_risk_metrics` (`as_of_date`), `.analyze_concentration`,
     `.compare_portfolios`, `.generate_comprehensive_report`
3. **Endpoints resolve, then pass down.** The endpoint is the only place a default is applied.
4. **VBA-style model objects** (`YieldCurve`, `IncentiveFee`, the credit-migration model, the
   concentration engine constructor) may default at construction - they receive their real date
   through their setup call. `YieldCurve.calculate_present_value` defaults to the curve's own
   analysis date.

### Endpoints that accept the date

| Endpoint | How |
|---|---|
| `GET /api/v1/portfolios/` | query `analysis_date` (drives `days_to_maturity`) |
| `GET /api/v1/portfolios/{deal_id}/summary` | query `analysis_date` (echoed with `data_as_of`) |
| `GET /api/v1/portfolios/{deal_id}/assets` | query `analysis_date` |
| `GET /api/v1/portfolios/{deal_id}/triggers` | query `analysis_date` |
| `POST /api/v1/portfolios/{deal_id}/concentration-tests` | body `analysis_date` |
| `POST /api/v1/portfolio-analytics/{portfolio_id}/concentration` and `/concentration-test` | body `analysis_date` |
| `GET /api/v1/concentration-thresholds/deals/{deal_id}/thresholds` | query `analysis_date` |
| `GET /api/v1/concentration-thresholds/deals/{deal_id}/concentration-tests` | query `analysis_date` |
| `GET /api/v1/risk/{deal_id}/metrics` | query `as_of_date` (name kept for existing clients) |
| `GET /api/v1/risk/{deal_id}/concentration` | query `analysis_date` |
| `POST /api/v1/risk/portfolio-comparison` | query `analysis_date` |
| `POST /api/v1/risk/{deal_id}/risk-report` | query `analysis_date` (one date for metrics, concentration and `data_as_of_date`) |
| `POST /api/v1/credit-migration/simulate/portfolio`, `/simulate/deal` | body `analysis_date` |
| `GET /api/v1/config` | **public**; returns `{"analysis_date": {"default", "min", "max"}}` |

All accept `YYYY-MM-DD`; omitted means the configured default; invalid or out-of-range means 422.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/portfolios/MAG16/summary?analysis_date=2018-06-30"
# -> {"analysis_date": "2018-06-30", "data_as_of": "2016-03-23", ...}

curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"analysis_date": "2018-06-30"}' \
  "http://localhost:8000/api/v1/portfolios/MAG6/concentration-tests"
```

Example of a date-sensitive result: MAG6's long-dated test (#43) is 25.8% at 2016-03-23 and 0%
at 2018-06-30; MAG17's `days_to_maturity` is 4,411 at the default and 3,582 at 2018-06-30.

---

## Data snapshot date

- Column `clo_deals.data_as_of` (DATE), added by `backend/migrations/011_clo_deals_data_as_of.sql`
  (idempotent) and filled by `scripts/rebuild_dev_db_from_excel.py` from each tab's C3 cell.
- Returned as `data_as_of` by `GET /portfolios/` (per deal) and `GET /portfolios/{id}/summary`.
- The frontend's `DataSnapshotNotice` shows an info alert on the portfolio list and portfolio
  detail pages when the analysis date differs from the snapshot date(s), e.g. *"MAG16 holdings
  are a snapshot as of March 23, 2016. Results for June 30, 2018 shift time-based measures ...
  but do not roll holdings, ratings or prices forward."*

---

## Frontend

There is **one analysis date for the whole app**.

| Piece | File | Role |
|---|---|---|
| Top-bar control | `components/common/UI/AnalysisDateControl.tsx` | "As of Mar 23, 2016" button; opens `AnalysisDatePicker` in a popover. Highlighted when a non-default date is chosen. |
| Picker | `components/common/UI/AnalysisDatePicker.tsx` | Date input with min/max, reset, and quick dates derived from the default (prior year-end, quarter-ends, year-end). Dates are parsed as local dates (no off-by-one west of UTC). |
| State | `store/slices/analysisDateSlice.ts` | `selected` = user choice or `null` for the server default; plus `defaultDate`, `minDate`, `maxDate` from `/config`. Invalid/out-of-range values are ignored; the default is stored as `null`. |
| Hook | `hooks/useAnalysisDate.ts` | `analysisDate` (display), `analysisDateParam` (send to API; `undefined` = server default), `isDefault`, `setAnalysisDate`, `resetAnalysisDate`. |
| Sync | `components/common/Layout/AnalysisDateSync.tsx` (mounted in `AppLayout`) | Loads `GET /api/v1/config`; mirrors the selection to the URL as `?asOf=YYYY-MM-DD`. |
| Notice | `components/common/UI/DataSnapshotNotice.tsx` | Explains a difference between analysis date and data snapshot. |

### URL behaviour (`?asOf=`)
- A chosen date is written to the URL and **kept when navigating** (links don't need to carry it).
- Shared links, reloads and the back button restore the date from the URL.
- The parameter is removed when the default is in use; malformed, out-of-range or default
  values in the URL are ignored and cleaned up. Other query parameters are preserved.

### Data fetching
- `useGetPortfoliosQuery` and `useGetPortfolioSummaryQuery` (exported from `store/api/cloApi.ts`)
  are wrappers that pass the global date **inside the query argument**, so it is part of the
  RTK Query cache key and changing the date refetches. With the default date they pass exactly
  the previous arguments, so default-date cache entries - used by optimistic updates and
  prefetching - are unchanged.
- `PortfolioDetail` sends `analysis_date` with its concentration-test requests and re-runs them
  when the date changes.
- New endpoints that depend on the date: add it to the endpoint's query argument (not silently
  in the base query - that would not change the cache key and pages would show stale data).

### Using it in a component
```tsx
const { analysisDate, analysisDateParam, isDefault, setAnalysisDate } = useAnalysisDate();
// display: analysisDate (may be null until /config has loaded)
// API:     analysisDateParam (undefined => let the server default apply)
```

---

## Testing

- Backend: default-date concentration results were checked against the baseline for all ten
  deals after every step; the backend suite runs against the isolated `clo_dev_test` database.
- Frontend: `store/slices/analysisDateSlice.test.ts`, `components/common/Layout/AnalysisDateSync.test.tsx`
  (real router - see the note in that file about Jest 27 and react-router v7),
  `components/common/UI/DataSnapshotNotice.test.tsx`.

## Known limitations

- Holdings are not rolled forward; there is no projection to other dates.
- Several services still return mock data and ignore the date in substance (waterfall, parts of
  risk and rebalancing) even though they accept it.
- `POST /risk/{deal_id}/risk-report` and the credit-migration simulation endpoints are broken
  for reasons unrelated to dates (see `CLAUDE.md` known issues).
