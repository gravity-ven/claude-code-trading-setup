-- ============================================================================
-- Swing Trading Dashboard Database Schema
-- ============================================================================
--
-- PostgreSQL 13+ with TimescaleDB extension for time-series data
-- Implements complete database architecture from technical_blueprint.md
--
-- Features:
-- - Hypertables for efficient time-series storage
-- - Compression policies for older data
-- - Retention policies for data management
-- - Indexes for fast queries
-- - Real-time continuous aggregates
--
-- Author: Spartan Research Station
-- Version: 1.0.0
-- ============================================================================

-- Enable TimescaleDB extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Drop existing tables (if recreating schema)
-- DROP TABLE IF EXISTS market_indices CASCADE;
-- DROP TABLE IF EXISTS volatility_indicators CASCADE;
-- DROP TABLE IF EXISTS credit_spreads CASCADE;
-- DROP TABLE IF EXISTS treasury_yields CASCADE;
-- DROP TABLE IF EXISTS forex_rates CASCADE;
-- DROP TABLE IF EXISTS commodities CASCADE;
-- DROP TABLE IF EXISTS sentiment_indicators CASCADE;
-- DROP TABLE IF EXISTS market_breadth CASCADE;
-- DROP TABLE IF EXISTS sector_rotation CASCADE;
-- DROP TABLE IF EXISTS capital_flows CASCADE;

-- ============================================================================
-- Table 1: Market Indices
-- ============================================================================
CREATE TABLE market_indices (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10),
    country VARCHAR(50),
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    volume BIGINT,
    change_pct NUMERIC(8,4),
    PRIMARY KEY (time, symbol)
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('market_indices', 'time', if_not_exists => TRUE);

-- Add compression policy (compress data older than 7 days)
ALTER TABLE market_indices SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,exchange'
);

SELECT add_compression_policy('market_indices', INTERVAL '7 days');

-- Retention policy (keep data for 5 years)
SELECT add_retention_policy('market_indices', INTERVAL '5 years');

-- Indexes
CREATE INDEX idx_market_indices_symbol ON market_indices (symbol, time DESC);
CREATE INDEX idx_market_indices_country ON market_indices (country, time DESC);

-- ============================================================================
-- Table 2: Volatility Indicators
-- ============================================================================
CREATE TABLE volatility_indicators (
    time TIMESTAMPTZ NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value NUMERIC(10,4),
    change NUMERIC(10,4),
    change_pct NUMERIC(8,4),
    source VARCHAR(100),
    PRIMARY KEY (time, indicator_name)
);

SELECT create_hypertable('volatility_indicators', 'time', if_not_exists => TRUE);

ALTER TABLE volatility_indicators SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'indicator_name'
);

SELECT add_compression_policy('volatility_indicators', INTERVAL '7 days');
SELECT add_retention_policy('volatility_indicators', INTERVAL '5 years');

CREATE INDEX idx_volatility_name ON volatility_indicators (indicator_name, time DESC);

-- ============================================================================
-- Table 3: Credit Spreads
-- ============================================================================
CREATE TABLE credit_spreads (
    time TIMESTAMPTZ NOT NULL,
    spread_type VARCHAR(50) NOT NULL,
    value NUMERIC(10,4),
    change NUMERIC(10,4),
    unit VARCHAR(10) DEFAULT 'bps',
    source VARCHAR(100),
    PRIMARY KEY (time, spread_type)
);

SELECT create_hypertable('credit_spreads', 'time', if_not_exists => TRUE);

ALTER TABLE credit_spreads SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'spread_type'
);

SELECT add_compression_policy('credit_spreads', INTERVAL '7 days');
SELECT add_retention_policy('credit_spreads', INTERVAL '10 years');

CREATE INDEX idx_credit_spreads_type ON credit_spreads (spread_type, time DESC);

-- ============================================================================
-- Table 4: Treasury Yields
-- ============================================================================
CREATE TABLE treasury_yields (
    time TIMESTAMPTZ NOT NULL,
    maturity VARCHAR(20) NOT NULL,
    yield NUMERIC(8,4),
    change NUMERIC(8,4),
    unit VARCHAR(10) DEFAULT '%',
    source VARCHAR(100),
    PRIMARY KEY (time, maturity)
);

SELECT create_hypertable('treasury_yields', 'time', if_not_exists => TRUE);

ALTER TABLE treasury_yields SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'maturity'
);

SELECT add_compression_policy('treasury_yields', INTERVAL '7 days');
SELECT add_retention_policy('treasury_yields', INTERVAL '30 years');

CREATE INDEX idx_treasury_maturity ON treasury_yields (maturity, time DESC);

-- ============================================================================
-- Table 5: Forex Rates
-- ============================================================================
CREATE TABLE forex_rates (
    time TIMESTAMPTZ NOT NULL,
    pair VARCHAR(10) NOT NULL,
    rate NUMERIC(12,6),
    change NUMERIC(12,6),
    change_pct NUMERIC(8,4),
    source VARCHAR(100),
    PRIMARY KEY (time, pair)
);

SELECT create_hypertable('forex_rates', 'time', if_not_exists => TRUE);

ALTER TABLE forex_rates SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'pair'
);

SELECT add_compression_policy('forex_rates', INTERVAL '7 days');
SELECT add_retention_policy('forex_rates', INTERVAL '5 years');

CREATE INDEX idx_forex_pair ON forex_rates (pair, time DESC);

-- ============================================================================
-- Table 6: Commodities
-- ============================================================================
CREATE TABLE commodities (
    time TIMESTAMPTZ NOT NULL,
    commodity_name VARCHAR(50) NOT NULL,
    price NUMERIC(12,4),
    change NUMERIC(12,4),
    change_pct NUMERIC(8,4),
    volume BIGINT,
    unit VARCHAR(20),
    source VARCHAR(100),
    PRIMARY KEY (time, commodity_name)
);

SELECT create_hypertable('commodities', 'time', if_not_exists => TRUE);

ALTER TABLE commodities SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'commodity_name'
);

SELECT add_compression_policy('commodities', INTERVAL '7 days');
SELECT add_retention_policy('commodities', INTERVAL '10 years');

CREATE INDEX idx_commodity_name ON commodities (commodity_name, time DESC);

-- ============================================================================
-- Table 7: Sentiment Indicators
-- ============================================================================
CREATE TABLE sentiment_indicators (
    time TIMESTAMPTZ NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value NUMERIC(10,4),
    status VARCHAR(50),
    source VARCHAR(100),
    PRIMARY KEY (time, indicator_name)
);

SELECT create_hypertable('sentiment_indicators', 'time', if_not_exists => TRUE);

ALTER TABLE sentiment_indicators SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'indicator_name'
);

SELECT add_compression_policy('sentiment_indicators', INTERVAL '7 days');
SELECT add_retention_policy('sentiment_indicators', INTERVAL '5 years');

CREATE INDEX idx_sentiment_name ON sentiment_indicators (indicator_name, time DESC);

-- ============================================================================
-- Table 8: Market Breadth
-- ============================================================================
CREATE TABLE market_breadth (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    value NUMERIC(10,4),
    advancing INT,
    declining INT,
    unchanged INT,
    ratio NUMERIC(8,4),
    source VARCHAR(100),
    PRIMARY KEY (time, metric_name)
);

SELECT create_hypertable('market_breadth', 'time', if_not_exists => TRUE);

ALTER TABLE market_breadth SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'metric_name'
);

SELECT add_compression_policy('market_breadth', INTERVAL '7 days');
SELECT add_retention_policy('market_breadth', INTERVAL '5 years');

CREATE INDEX idx_breadth_metric ON market_breadth (metric_name, time DESC);

-- ============================================================================
-- Table 9: Sector Rotation
-- ============================================================================
CREATE TABLE sector_rotation (
    time TIMESTAMPTZ NOT NULL,
    sector_name VARCHAR(50) NOT NULL,
    etf_symbol VARCHAR(10),
    price NUMERIC(12,4),
    change_pct NUMERIC(8,4),
    relative_strength NUMERIC(8,4),
    volume BIGINT,
    recommendation VARCHAR(10),
    PRIMARY KEY (time, sector_name)
);

SELECT create_hypertable('sector_rotation', 'time', if_not_exists => TRUE);

ALTER TABLE sector_rotation SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sector_name'
);

SELECT add_compression_policy('sector_rotation', INTERVAL '7 days');
SELECT add_retention_policy('sector_rotation', INTERVAL '5 years');

CREATE INDEX idx_sector_name ON sector_rotation (sector_name, time DESC);
CREATE INDEX idx_sector_rs ON sector_rotation (relative_strength DESC, time DESC);

-- ============================================================================
-- Table 10: Capital Flows
-- ============================================================================
CREATE TABLE capital_flows (
    time TIMESTAMPTZ NOT NULL,
    flow_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    amount NUMERIC(18,4),
    unit VARCHAR(20) DEFAULT 'millions',
    change NUMERIC(18,4),
    source VARCHAR(100),
    PRIMARY KEY (time, flow_type, category)
);

SELECT create_hypertable('capital_flows', 'time', if_not_exists => TRUE);

ALTER TABLE capital_flows SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'flow_type,category'
);

SELECT add_compression_policy('capital_flows', INTERVAL '7 days');
SELECT add_retention_policy('capital_flows', INTERVAL '5 years');

CREATE INDEX idx_capital_flow_type ON capital_flows (flow_type, time DESC);
CREATE INDEX idx_capital_category ON capital_flows (category, time DESC);

-- ============================================================================
-- Continuous Aggregates (Real-time materialized views)
-- ============================================================================

-- Daily aggregates for market indices
CREATE MATERIALIZED VIEW market_indices_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    symbol,
    exchange,
    country,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM market_indices
GROUP BY bucket, symbol, exchange, country
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('market_indices_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to calculate moving average
CREATE OR REPLACE FUNCTION calculate_moving_average(
    p_symbol VARCHAR,
    p_period INT
)
RETURNS TABLE(time TIMESTAMPTZ, ma NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.time,
        AVG(m.close) OVER (
            ORDER BY m.time
            ROWS BETWEEN p_period - 1 PRECEDING AND CURRENT ROW
        ) AS ma
    FROM market_indices m
    WHERE m.symbol = p_symbol
    ORDER BY m.time DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate relative strength
CREATE OR REPLACE FUNCTION calculate_relative_strength(
    p_symbol VARCHAR,
    p_benchmark VARCHAR DEFAULT 'SPY',
    p_days INT DEFAULT 30
)
RETURNS NUMERIC AS $$
DECLARE
    symbol_return NUMERIC;
    benchmark_return NUMERIC;
BEGIN
    -- Calculate symbol return
    SELECT
        (last(close, time) - first(close, time)) / first(close, time) * 100
    INTO symbol_return
    FROM market_indices
    WHERE symbol = p_symbol
        AND time >= NOW() - (p_days || ' days')::INTERVAL;

    -- Calculate benchmark return
    SELECT
        (last(close, time) - first(close, time)) / first(close, time) * 100
    INTO benchmark_return
    FROM market_indices
    WHERE symbol = p_benchmark
        AND time >= NOW() - (p_days || ' days')::INTERVAL;

    -- Return relative strength
    RETURN COALESCE(symbol_return - benchmark_return, 0);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Views
-- ============================================================================

-- Latest market data view
CREATE OR REPLACE VIEW latest_market_data AS
SELECT DISTINCT ON (symbol)
    symbol,
    exchange,
    country,
    close AS price,
    change_pct,
    volume,
    time AS last_update
FROM market_indices
ORDER BY symbol, time DESC;

-- Latest sector rotation view
CREATE OR REPLACE VIEW latest_sector_rotation AS
SELECT DISTINCT ON (sector_name)
    sector_name,
    etf_symbol,
    price,
    change_pct,
    relative_strength,
    recommendation,
    time AS last_update
FROM sector_rotation
ORDER BY sector_name, time DESC;

-- ============================================================================
-- Grants (adjust user as needed)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO swing_dashboard_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO swing_dashboard_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO swing_dashboard_user;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE market_indices IS 'Global market indices data (US, China, India, Japan, Germany)';
COMMENT ON TABLE volatility_indicators IS 'Volatility indices (VIX, VVIX, SKEW, MOVE)';
COMMENT ON TABLE credit_spreads IS 'Credit spreads (HY OAS, IG BBB, EM spreads)';
COMMENT ON TABLE treasury_yields IS 'US Treasury yields across maturities';
COMMENT ON TABLE forex_rates IS 'Foreign exchange rates';
COMMENT ON TABLE commodities IS 'Commodity prices (gold, silver, oil, copper)';
COMMENT ON TABLE sentiment_indicators IS 'Market sentiment indicators';
COMMENT ON TABLE market_breadth IS 'Market breadth metrics (advance/decline)';
COMMENT ON TABLE sector_rotation IS 'Sector performance and rotation';
COMMENT ON TABLE capital_flows IS 'Fund flows and capital movements';

-- ============================================================================
-- Vacuum and Analyze
-- ============================================================================

VACUUM ANALYZE;

-- ============================================================================
-- Schema creation complete
-- ============================================================================

SELECT 'Swing Trading Dashboard schema created successfully!' AS status;
