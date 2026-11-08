#!/usr/bin/env python3
"""
Rebuild the core CLO tables in the local dev database directly from
TradeHypoPrelimv32.xlsm.

Written after the 2026-11-08 incident where backend tests ran
Base.metadata.drop_all() against clo_dev. The historical migration scripts
were one-off, order-dependent, and partly never committed, so this script
replaces them with a single reproducible build from the Excel source of truth.

What it builds (in dependency order):
  1. Missing tables via SQLAlchemy create_all (existing tables are untouched)
  2. users                          - the 4 documented dev accounts (bcrypt)
  3. clo_deals                      - "Mag N Inputs" Date Inputs / CLO Inputs blocks
  4. assets                         - "All Assets" tab (384 assets)
  5. deal_assets                    - "Mag N Inputs" Deal Collateral block (cols D/E)
  6. clo_tranches                   - "Mag N Inputs" CLO Liabilities block
  7. concentration_test_definitions - definitions from migrations/005 (54 VBA tests)
     deal_concentration_thresholds  - "Mag N Inputs" Concentration Limits block (cols L-O)

Yield curves are not in the workbook; restore them separately with
backend/scripts/migrate_yield_curves.py.

Usage (from repo root, backend venv):
    backend/venv/Scripts/python.exe scripts/rebuild_dev_db_from_excel.py --confirm

Safety: refuses to run unless the target is clo_dev on localhost/127.0.0.1,
and only replaces rows in the tables listed above (users are upserted).
"""

import argparse
import datetime as dt
import os
import re
import sys
import uuid
import warnings
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
EXCEL = REPO / "TradeHypoPrelimv32.xlsm"
DEFINITIONS_SQL = BACKEND / "migrations" / "005_vba_enum_realignment.sql"

sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)  # so app config picks up backend/.env.development

import openpyxl  # noqa: E402
from passlib.context import CryptContext  # noqa: E402
from psycopg2.extras import Json, execute_batch  # noqa: E402
from sqlalchemy.engine.url import make_url  # noqa: E402

warnings.filterwarnings("ignore")

DEALS = [6, 7, 8, 9, 11, 12, 14, 15, 16, 17]
ANALYSIS_DATE = dt.date(2016, 3, 23)

DEV_USERS = [
    # email, password, first, last, role
    ("admin@clo-system.com", "admin123", "System", "Administrator", "ADMIN"),
    ("manager@clo-system.com", "manager123", "Portfolio", "Manager", "MANAGER"),
    ("analyst@clo-system.com", "analyst123", "Risk", "Analyst", "ANALYST"),
    ("demo@clo-system.com", "demo12345", "Demo", "User", "VIEWER"),
]

# Tables whose contents this script owns and fully replaces.
REPLACED_TABLES = [
    "deal_concentration_thresholds",
    "concentration_test_definitions",
    "clo_tranches",
    "deal_assets",
    "assets",
    "clo_deals",
]


# --------------------------------------------------------------------------
# Value helpers
# --------------------------------------------------------------------------

def blank(v):
    return v is None or (isinstance(v, str) and v.strip() in ("", "N/A", "NA", "n/a"))


def to_str(v):
    if blank(v):
        return None
    return str(v).strip()


def to_dec(v, places=None):
    if blank(v) or isinstance(v, bool):
        return None
    try:
        d = Decimal(str(v).replace("$", "").replace(",", "").strip())
    except Exception:
        return None
    return round(d, places) if places is not None else d


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return None


def to_bool(v):
    """Excel flags are TRUE/FALSE, 1/0, or 'Yes'/'No'. Empty means False."""
    if blank(v):
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    return str(v).strip().lower() in ("true", "yes", "y", "1", "x")


def to_int(v, default=None):
    d = to_dec(v)
    return int(d) if d is not None else default


# --------------------------------------------------------------------------
# Excel extraction
# --------------------------------------------------------------------------

def block_lookup(rows, block_title):
    """Return {label: value} for a two-column label/value block under a row-2 title."""
    titles = rows[1]
    col = next(i for i, v in enumerate(titles) if isinstance(v, str) and v.strip() == block_title)
    out = {}
    for r in rows[2:40]:
        label = r[col]
        if isinstance(label, str) and label.strip():
            out.setdefault(label.strip().lower(), r[col + 1])
    return out


def read_deal(wb, n):
    ws = wb[f"Mag {n} Inputs"]
    rows = list(ws.iter_rows(min_row=1, max_row=40, values_only=True))
    dates = block_lookup(rows, "Date Inputs")
    inputs = block_lookup(rows, "CLO Inputs")
    months = to_int(dates.get("months between payments"))
    return {
        "deal_id": f"MAG{n}",
        "deal_name": f"Magnetar MAG{n} CLO",
        "manager_name": "Magnetar Capital",
        "pricing_date": to_date(dates.get("pricing date")),
        "closing_date": to_date(dates.get("closing date")),
        "effective_date": to_date(dates.get("effective date")),
        "first_payment_date": to_date(dates.get("first payment date")),
        "no_call_date": to_date(dates.get("non call period")),
        "reinvestment_end_date": to_date(dates.get("reinvestment end date")),
        "maturity_date": to_date(dates.get("stated maturity date")),
        "payment_frequency": 12 // months if months else None,
        "target_par_amount": to_dec(inputs.get("target par amount"), 2),
        "deal_status": "Revolving",
    }


def read_positions(wb, n):
    ws = wb[f"Mag {n} Inputs"]
    out = {}
    for r in ws.iter_rows(min_row=4, values_only=True):
        bid, par = r[3], r[4]
        if blank(bid) or not isinstance(par, (int, float)) or par == 0:
            continue
        bid = str(bid).strip()
        if bid in out:
            raise ValueError(f"MAG{n}: duplicate position {bid}")
        out[bid] = to_dec(par, 2)
    return out


def read_tranches(wb, n):
    ws = wb[f"Mag {n} Inputs"]
    rows = list(ws.iter_rows(min_row=1, max_row=40, values_only=True))
    col = next(i for i, v in enumerate(rows[2]) if v == "Tranche Number")
    numbers = []
    for v in rows[2][col + 1:]:
        if not isinstance(v, (int, float)):
            break
        numbers.append(int(v))
    attrs = {}
    for r in rows[3:40]:
        label = r[col]
        if isinstance(label, str) and label.strip():
            attrs[label.strip().lower()] = r[col + 1: col + 1 + len(numbers)]

    def attr(prefix):
        key = next(k for k in attrs if k.startswith(prefix))
        return attrs[key]

    names, orig, cur = attr("cdo class name"), attr("original balance"), attr("current balance")
    spread, pik, equity, ctype = attr("spread"), attr("pikable"), attr("equity tranche"), attr("coupon type")
    deal_id = f"MAG{n}"
    out = []
    for i, num in enumerate(numbers):
        is_equity = to_bool(equity[i])
        floating = str(ctype[i]).strip().lower() == "floating"
        out.append({
            "tranche_id": f"{deal_id}-{num}",
            "deal_id": deal_id,
            "tranche_name": to_str(names[i]),
            "initial_balance": to_dec(orig[i], 2),
            "current_balance": to_dec(cur[i], 2),
            "coupon_rate": None,
            "coupon_type": "EQUITY" if is_equity else ("FLOATING" if floating else "FIXED"),
            "index_name": "LIBOR" if floating and not is_equity else None,
            "margin": None if is_equity else to_dec(spread[i], 6),
            "mdy_rating": None,
            "sp_rating": None,
            "seniority_level": num,
            "payment_rank": num,
            "interest_deferrable": True if is_equity else to_bool(pik[i]),
        })
    return out


def read_tests(wb, n):
    ws = wb[f"Mag {n} Inputs"]
    out = []
    for r in ws.iter_rows(min_row=4, max_row=120, values_only=True):
        num, name, _minmax, threshold, overwrite = r[11], r[12], r[13], r[14], r[15]
        if isinstance(num, (int, float)):
            value = overwrite if not blank(overwrite) else threshold
            out.append((int(num), to_str(name), to_dec(value)))
    return out


ASSET_MAP = {
    # db column: (excel header, converter)
    "blkrock_id": ("BLKRockID", to_str),
    "issue_name": ("Issue Name", to_str),
    "issuer_name": ("Issuer Name", to_str),
    "issuer_id": ("ISSUER ID", to_str),
    "tranche": ("Tranche", to_str),
    "bond_loan": ("Bond/Loan", to_str),
    "par_amount": ("Par Amount", lambda v: to_dec(v, 2)),
    "market_value": ("Market Value", lambda v: to_dec(v, 4)),
    "currency": ("Currency", to_str),
    "amount_issued": ("Amount Issued", lambda v: to_dec(v, 2)),
    "facility_size": ("Facility Size", lambda v: to_dec(v, 2)),
    "unfunded_amount": ("Unfunded Amount", lambda v: to_dec(v, 2)),
    "maturity": ("Maturity", to_date),
    "dated_date": ("Dated Date", to_date),
    "issue_date": ("Issue Date", to_date),
    "first_payment_date": ("First Payment Date", to_date),
    "date_of_default": ("Date of Defaulted", to_date),
    "coupon": ("Coupon", lambda v: to_dec(v, 6)),
    "coupon_type": ("Coupon Type", to_str),
    "index_name": ("Index", to_str),
    "cpn_spread": ("Coupon Spread", lambda v: to_dec(v, 6)),
    "libor_floor": ("Libor Floor", lambda v: to_dec(v, 6)),
    "index_cap": ("Index Cap", lambda v: to_dec(v, 6)),
    "commit_fee": ("Commitment Fee", lambda v: to_dec(v, 6)),
    "payment_freq": ("Payment Frequency", lambda v: to_int(v, 4)),
    "amortization_type": ("Amortization Type", to_str),
    "day_count": ("Day Count", to_str),
    "business_day_conv": ("Business Day Convention", to_str),
    "payment_eom": ("PMT EOM", to_bool),
    "piking": ("PiKing", to_bool),
    "pik_amount": ("PIK Amount", lambda v: to_dec(v, 2)),
    "wal": ("WAL", lambda v: to_dec(v, 4)),
    "mdy_rating": ("Moody's Rating-21", to_str),
    "sp_rating": ("S&P Facility Rating", to_str),
    "mdy_dp_rating": ("Moody's Default Probability Rating-18", to_str),
    "mdy_dp_rating_warf": ("Moody's Rating WARF", to_str),
    "mdy_recovery_rate": ("Moody's Recovery Rate-23", lambda v: to_dec(v, 4)),
    "mdy_facility_rating": ("Moody Facility Rating", to_str),
    "mdy_facility_outlook": ("Moody Facility Outlook", to_str),
    "mdy_issuer_rating": ("Moody Issuer Rating", to_str),
    "mdy_issuer_outlook": ("Moody Issuer outlook", to_str),
    "mdy_snr_sec_rating": ("Moody's Senior Secured Rating", to_str),
    "mdy_snr_unsec_rating": ("Moody Senior Unsecured Rating", to_str),
    "mdy_sub_rating": ("Moody Subordinate Rating", to_str),
    "mdy_credit_est_rating": ("Moody's Credit Estimate", to_str),
    "mdy_credit_est_date": ("Moody's Credit Estimate Date", to_date),
    "sandp_facility_rating": ("S&P Facility Rating", to_str),
    "sandp_issuer_rating": ("S&P Issuer Rating", to_str),
    "sandp_snr_sec_rating": ("S&P Senior Secured Rating", to_str),
    "sandp_subordinate": ("S&P Subordinated Rating", to_str),
    "sandp_rec_rating": ("S&P Recovery Rating", to_str),
    "mdy_industry": ("Moody's Industry", to_str),
    "sp_industry": ("S&P Industry", to_str),
    "country": ("Country ", to_str),
    "seniority": ("Seniority", to_str),
    "mdy_asset_category": ("Moody Asset Category", to_str),
    "sp_priority_category": ("S&P Priority Category", to_str),
    "analyst_opinion": ("Credit Opinion", to_str),
}

FLAG_MAP = {
    "deferred_interest": "Deferred Interest Bond",
    "default_obligation": "Default Obligation",
    "delayed_drawdown": "Delayed Drawdown ",
    "revolver": "Revolver",
    "letter_of_credit": "Letter of Credit",
    "participation": "Participation",
    "dip": "DIP",
    "convertible": "Convertible",
    "structured_finance": "Structured Finance",
    "bridge_loan": "Bridge Loan",
    "current_pay": "Current Pay",
    "cov_lite": "Cov-Lite",
    "first_lien_last_out": "First Lien Last Out Loan",
}


def read_assets(wb):
    rows = list(wb["All Assets"].iter_rows(min_row=1, values_only=True))
    hdr = list(rows[0])
    idx = {h: i for i, h in enumerate(hdr) if h is not None}
    missing = [h for h, _ in ASSET_MAP.values() if h not in idx] + [h for h in FLAG_MAP.values() if h not in idx]
    if missing:
        raise ValueError(f"'All Assets' is missing expected columns: {missing}")
    now = dt.datetime.now()
    out = []
    for r in rows[1:]:
        if blank(r[idx["BLKRockID"]]):
            continue
        rec = {col: conv(r[idx[h]]) for col, (h, conv) in ASSET_MAP.items()}
        rec["flags"] = Json({k: to_bool(r[idx[h]]) for k, h in FLAG_MAP.items()})
        rec["created_at"] = rec["updated_at"] = now
        out.append(rec)
    return out


def definitions_insert_sql():
    sql = DEFINITIONS_SQL.read_text(encoding="utf-8")
    m = re.search(r"INSERT INTO concentration_test_definitions .*?;\s*$", sql, re.S | re.M)
    if not m:
        raise ValueError("Could not find definitions INSERT in 005_vba_enum_realignment.sql")
    return m.group(0)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def insert_rows(cur, table, rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('%(' + c + ')s' for c in cols)})"
    execute_batch(cur, sql, rows, page_size=200)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm", action="store_true", help="actually write to the database")
    args = ap.parse_args()

    from app.core.config import settings
    url = make_url(settings.database_url)
    if url.database != "clo_dev" or url.host not in ("127.0.0.1", "localhost"):
        sys.exit(f"Refusing to run: target is {url.host}/{url.database}, expected local clo_dev")
    if not args.confirm:
        sys.exit("Dry guard: re-run with --confirm to rebuild clo_dev from Excel")

    print(f"Reading {EXCEL.name} ...")
    wb = openpyxl.load_workbook(EXCEL, read_only=True, data_only=True)
    deals = [read_deal(wb, n) for n in DEALS]
    assets = read_assets(wb)
    positions = {n: read_positions(wb, n) for n in DEALS}
    tranches = [t for n in DEALS for t in read_tranches(wb, n)]
    tests = {n: read_tests(wb, n) for n in DEALS}

    asset_ids = {a["blkrock_id"] for a in assets}
    for n, pos in positions.items():
        unknown = set(pos) - asset_ids
        if unknown:
            raise ValueError(f"MAG{n} has positions not in 'All Assets': {sorted(unknown)[:5]}")

    # Register every model on Base, then create any missing tables.
    import logging
    logging.disable(logging.WARNING)
    import app.main  # noqa: F401  (imports all routers -> all models)
    from app.core.database import Base, engine
    logging.disable(logging.NOTSET)
    Base.metadata.create_all(bind=engine)
    print("Schema: create_all done")

    # The concentration models declare CHECK constraints that never existed in
    # the real schema (migration 001 only documents the values in comments) and
    # are stale, e.g. valid_mag_version allows only MAG6/MAG14/MAG17. Drop them
    # so the rebuilt tables match the pre-wipe database.
    with engine.begin() as conn:
        from sqlalchemy import text
        for table, constraint in [
            ("concentration_test_definitions", "valid_test_category"),
            ("concentration_test_definitions", "valid_result_type"),
            ("deal_concentration_thresholds", "positive_threshold_value"),
            ("deal_concentration_thresholds", "valid_mag_version"),
            ("deal_concentration_thresholds", "valid_rating_agency"),
            ("concentration_test_executions", "valid_pass_fail_status"),
            ("concentration_test_executions", "valid_threshold_source"),
            ("concentration_test_executions", "non_zero_denominator"),
        ]:
            conn.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}"))

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()

        # Users: upsert by email, keep existing user_id.
        for email, password, first, last, role in DEV_USERS:
            cur.execute(
                """
                INSERT INTO users (user_id, username, email, password_hash, first_name, last_name,
                                   role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, now(), now())
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash, role = EXCLUDED.role,
                    is_active = true, updated_at = now()
                """,
                (str(uuid.uuid4()), email.split("@")[0], email, pwd.hash(password), first, last, role),
            )

        cur.execute(f"TRUNCATE {', '.join(REPLACED_TABLES)} RESTART IDENTITY CASCADE")

        now = dt.datetime.now()
        insert_rows(cur, "clo_deals", [{**d, "created_at": now, "updated_at": now} for d in deals])
        insert_rows(cur, "assets", assets)
        insert_rows(cur, "deal_assets", [
            {"deal_id": f"MAG{n}", "blkrock_id": bid, "par_amount": par,
             "position_status": "Active", "created_at": now}
            for n, pos in positions.items() for bid, par in pos.items()
        ])
        insert_rows(cur, "clo_tranches", [{**t, "created_at": now} for t in tranches])

        # The model only has Python-side defaults; migration 001 created these
        # columns with DEFAULT CURRENT_TIMESTAMP, which the raw INSERT relies on.
        cur.execute("""
            ALTER TABLE concentration_test_definitions
                ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
                ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP
        """)
        cur.execute(definitions_insert_sql())
        cur.execute("SELECT test_number, test_id, default_threshold FROM concentration_test_definitions")
        defs = {num: (tid, default) for num, tid, default in cur.fetchall()}

        threshold_rows, defaulted = [], []
        for n, items in tests.items():
            for num, name, value in items:
                if num not in defs:
                    raise ValueError(f"MAG{n} test #{num} ({name}) has no definition")
                tid, default = defs[num]
                note = f"Excel: Mag {n} Inputs"
                if value is None:
                    value, note = default, note + " (N/A in Excel - definition default)"
                    defaulted.append(f"MAG{n}#{num}")
                threshold_rows.append({
                    "deal_id": f"MAG{n}", "test_id": tid, "threshold_value": value,
                    "effective_date": ANALYSIS_DATE, "expiry_date": None,
                    "mag_version": f"MAG{n}", "notes": note, "created_by": None,
                    "created_at": now, "updated_at": now,
                })
        insert_rows(cur, "deal_concentration_thresholds", threshold_rows)

        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()

    print(f"Committed: {len(deals)} deals, {len(assets)} assets, "
          f"{sum(len(p) for p in positions.values())} positions, {len(tranches)} tranches, "
          f"{len(defs)} test definitions, {len(threshold_rows)} thresholds "
          f"({len(defaulted)} N/A -> default: {', '.join(defaulted)})")


if __name__ == "__main__":
    main()
