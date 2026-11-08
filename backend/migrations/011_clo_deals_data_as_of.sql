-- Migration 011: per-deal data snapshot date
--
-- Each deal's holdings, ratings and LIBOR come from a "Mag N Inputs" tab that is a snapshot
-- as of that tab's analysis date (cell C3 "Analysis date", repeated as "Analysis Date" in the
-- CLO Inputs block). Storing it lets the UI warn when the user's analysis date differs:
-- other dates shift time-based measures but do not roll holdings forward.
--
-- Values verified against TradeHypoPrelimv32.xlsm on 2026-11-08: all ten deals = 2016-03-23,
-- and both cells agree on every tab. scripts/rebuild_dev_db_from_excel.py reads the same cell.
--
-- Idempotent: safe to run more than once.

ALTER TABLE clo_deals ADD COLUMN IF NOT EXISTS data_as_of DATE;

COMMENT ON COLUMN clo_deals.data_as_of IS
    'Date the deal''s holdings data is a snapshot of (Excel "Mag N Inputs" C3 analysis date)';

UPDATE clo_deals
SET data_as_of = DATE '2016-03-23'
WHERE deal_id IN ('MAG6', 'MAG7', 'MAG8', 'MAG9', 'MAG11', 'MAG12', 'MAG14', 'MAG15', 'MAG16', 'MAG17')
  AND data_as_of IS NULL;
