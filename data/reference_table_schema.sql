
-- Reference Data Database Schema for CLO System
-- Generated from Reference Table analysis

-- Historical Interest Rates
CREATE TABLE historical_rates (
    id INTEGER PRIMARY KEY,
    rate_date DATE NOT NULL,
    rate_type VARCHAR(50) NOT NULL,
    rate_value DECIMAL(10, 6) NOT NULL,
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rates_date_type (rate_date, rate_type)
);

-- Business Holidays Calendar
CREATE TABLE business_holidays (
    id INTEGER PRIMARY KEY,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(100),
    country VARCHAR(10) DEFAULT 'US',
    market VARCHAR(20) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_holidays_date (holiday_date)
);

-- Yield Curves
CREATE TABLE yield_curves (
    id INTEGER PRIMARY KEY,
    curve_date DATE NOT NULL,
    tenor VARCHAR(10) NOT NULL,
    rate DECIMAL(10, 6) NOT NULL,
    curve_type VARCHAR(50) DEFAULT 'Treasury',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_curves_date_tenor (curve_date, tenor)
);

-- Rating Transition Matrices
CREATE TABLE rating_transition_matrices (
    id INTEGER PRIMARY KEY,
    agency VARCHAR(10) NOT NULL,
    from_rating VARCHAR(20) NOT NULL,
    to_rating VARCHAR(20) NOT NULL,
    probability DECIMAL(8, 6) NOT NULL,
    time_period VARCHAR(20) DEFAULT '1_year',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_transitions_agency_from (agency, from_rating)
);

-- Reference Cashflows
CREATE TABLE reference_cashflows (
    id INTEGER PRIMARY KEY,
    asset_id VARCHAR(50),
    payment_date DATE NOT NULL,
    principal_amount DECIMAL(20, 2) DEFAULT 0,
    interest_amount DECIMAL(20, 2) DEFAULT 0,
    cashflow_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cashflows_asset_date (asset_id, payment_date)
);

-- Amortization Schedules
CREATE TABLE amortization_schedules (
    id INTEGER PRIMARY KEY,
    schedule_id VARCHAR(50) NOT NULL,
    payment_date DATE NOT NULL,
    principal_amount DECIMAL(20, 2) NOT NULL,
    remaining_balance DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_amortization_schedule_date (schedule_id, payment_date)
);

-- Deal Parameters
CREATE TABLE deal_parameters (
    id INTEGER PRIMARY KEY,
    deal_name VARCHAR(100) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT,
    parameter_type VARCHAR(50),
    effective_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_deal_params (deal_name, parameter_name)
);
