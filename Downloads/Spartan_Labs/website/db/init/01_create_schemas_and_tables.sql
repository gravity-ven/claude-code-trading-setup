-- Spartan Research Station - Complete Database Schema
-- PostgreSQL 15 + TimescaleDB Extension
-- Database-First Architecture: ALL data stored here, NEVER refetch from APIs
-- Version: 2.0.0

-- ==============================================================================
-- Enable Required Extensions
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Fuzzy text search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- GIN indexes for better performance
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- GIST indexes

-- ==============================================================================
-- Create Schemas
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS economic_data;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS system;

-- ==============================================================================
-- MARKET DATA TABLES
-- ==============================================================================

-- Table 1: Market Indices (S&P 500, NASDAQ, Dow, etc.)
CREATE TABLE market_data.indices (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,  -- ^GSPC, ^IXIC, ^DJI, etc.
    name VARCHAR(100) NOT NULL,
    price NUMERIC(20, 4),
    open_price NUMERIC(20, 4),
    high_price NUMERIC(20, 4),
    low_price NUMERIC(20, 4),
    volume BIGINT,
    change NUMERIC(20, 4),
    change_percent NUMERIC(10, 4),
    market_cap BIGINT,
    source VARCHAR(50),  -- yfinance, polygon, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('market_data.indices', 'timestamp', if_not_exists => TRUE);

-- Add compression policy (compress data older than 7 days)
SELECT add_compression_policy('market_data.indices', INTERVAL '7 days', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX idx_indices_symbol ON market_data.indices (symbol, timestamp DESC);
CREATE INDEX idx_indices_timestamp ON market_data.indices (timestamp DESC);

-- Table 2: Commodities (Gold, Oil, Copper, etc.)
CREATE TABLE market_data.commodities (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,  -- GC=F (Gold), CL=F (WTI Oil), etc.
    name VARCHAR(100) NOT NULL,
    price NUMERIC(20, 4),
    open_price NUMERIC(20, 4),
    high_price NUMERIC(20, 4),
    low_price NUMERIC(20, 4),
    volume BIGINT,
    change NUMERIC(20, 4),
    change_percent NUMERIC(10, 4),
    unit VARCHAR(20),  -- oz, barrel, lb, etc.
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol)
);

SELECT create_hypertable('market_data.commodities', 'timestamp', if_not_exists => TRUE);
SELECT add_compression_policy('market_data.commodities', INTERVAL '7 days', if_not_exists => TRUE);
CREATE INDEX idx_commodities_symbol ON market_data.commodities (symbol, timestamp DESC);

-- Table 3: Forex Rates (USD/EUR, USD/JPY, etc.)
CREATE TABLE market_data.forex_rates (
    timestamp TIMESTAMPTZ NOT NULL,
    pair VARCHAR(10) NOT NULL,  -- EURUSD, GBPUSD, etc.
    base_currency CHAR(3),
    quote_currency CHAR(3),
    bid NUMERIC(20, 8),
    ask NUMERIC(20, 8),
    mid NUMERIC(20, 8),
    change NUMERIC(20, 8),
    change_percent NUMERIC(10, 4),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, pair)
);

SELECT create_hypertable('market_data.forex_rates', 'timestamp', if_not_exists => TRUE);
SELECT add_compression_policy('market_data.forex_rates', INTERVAL '7 days', if_not_exists => TRUE);
CREATE INDEX idx_forex_pair ON market_data.forex_rates (pair, timestamp DESC);

-- Table 4: Crypto Prices (BTC, ETH, SOL, etc.)
CREATE TABLE market_data.crypto_prices (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,  -- BTC-USD, ETH-USD, etc.
    name VARCHAR(100),
    price NUMERIC(20, 8),
    market_cap BIGINT,
    volume_24h BIGINT,
    circulating_supply BIGINT,
    total_supply BIGINT,
    change_24h NUMERIC(20, 8),
    change_percent_24h NUMERIC(10, 4),
    dominance_percent NUMERIC(10, 4),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol)
);

SELECT create_hypertable('market_data.crypto_prices', 'timestamp', if_not_exists => TRUE);
SELECT add_compression_policy('market_data.crypto_prices', INTERVAL '7 days', if_not_exists => TRUE);
CREATE INDEX idx_crypto_symbol ON market_data.crypto_prices (symbol, timestamp DESC);

-- Table 5: Treasury Yields (2Y, 10Y, 30Y)
CREATE TABLE market_data.treasury_yields (
    date DATE NOT NULL,
    yield_1m NUMERIC(10, 4),
    yield_3m NUMERIC(10, 4),
    yield_6m NUMERIC(10, 4),
    yield_1y NUMERIC(10, 4),
    yield_2y NUMERIC(10, 4),
    yield_5y NUMERIC(10, 4),
    yield_7y NUMERIC(10, 4),
    yield_10y NUMERIC(10, 4),
    yield_20y NUMERIC(10, 4),
    yield_30y NUMERIC(10, 4),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date)
);

SELECT create_hypertable('market_data.treasury_yields', 'date', if_not_exists => TRUE);
CREATE INDEX idx_treasury_date ON market_data.treasury_yields (date DESC);

-- Table 6: Credit Spreads (High Yield, Investment Grade)
CREATE TABLE market_data.credit_spreads (
    date DATE NOT NULL,
    hy_oas NUMERIC(10, 4),  -- High Yield Option-Adjusted Spread
    ig_aaa NUMERIC(10, 4),  -- Investment Grade AAA
    ig_aa NUMERIC(10, 4),   -- Investment Grade AA
    ig_a NUMERIC(10, 4),    -- Investment Grade A
    ig_bbb NUMERIC(10, 4),  -- Investment Grade BBB
    em_spread NUMERIC(10, 4),  -- Emerging Markets
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date)
);

SELECT create_hypertable('market_data.credit_spreads', 'date', if_not_exists => TRUE);
CREATE INDEX idx_credit_date ON market_data.credit_spreads (date DESC);

-- Table 7: Volatility Indicators (VIX, VVIX, SKEW, MOVE)
CREATE TABLE market_data.volatility_indicators (
    timestamp TIMESTAMPTZ NOT NULL,
    vix NUMERIC(10, 4),      -- CBOE Volatility Index
    vvix NUMERIC(10, 4),     -- VIX of VIX
    skew NUMERIC(10, 4),     -- CBOE SKEW Index
    move NUMERIC(10, 4),     -- Bond Market Volatility
    gvz NUMERIC(10, 4),      -- Gold Volatility
    ovx NUMERIC(10, 4),      -- Oil Volatility
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp)
);

SELECT create_hypertable('market_data.volatility_indicators', 'timestamp', if_not_exists => TRUE);
SELECT add_compression_policy('market_data.volatility_indicators', INTERVAL '7 days', if_not_exists => TRUE);
CREATE INDEX idx_volatility_timestamp ON market_data.volatility_indicators (timestamp DESC);

-- ==============================================================================
-- ECONOMIC DATA TABLES
-- ==============================================================================

-- Table 8: Economic Indicators (GDP, CPI, Unemployment, etc.)
CREATE TABLE economic_data.indicators (
    date DATE NOT NULL,
    indicator_code VARCHAR(50) NOT NULL,  -- GDP, CPIAUCSL, UNRATE, etc.
    indicator_name VARCHAR(200),
    value NUMERIC(20, 4),
    frequency VARCHAR(20),  -- daily, monthly, quarterly, annual
    units VARCHAR(50),
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, indicator_code)
);

SELECT create_hypertable('economic_data.indicators', 'date', if_not_exists => TRUE);
CREATE INDEX idx_indicators_code ON economic_data.indicators (indicator_code, date DESC);
CREATE INDEX idx_indicators_date ON economic_data.indicators (date DESC);

-- Table 9: FRED Series Cache (Complete FRED data cache)
CREATE TABLE economic_data.fred_series (
    series_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    value NUMERIC(20, 4),
    title VARCHAR(500),
    frequency VARCHAR(20),
    units VARCHAR(100),
    seasonal_adjustment VARCHAR(50),
    last_updated TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (series_id, date)
);

SELECT create_hypertable('economic_data.fred_series', 'date', if_not_exists => TRUE);
CREATE INDEX idx_fred_series ON economic_data.fred_series (series_id, date DESC);
CREATE INDEX idx_fred_date ON economic_data.fred_series (date DESC);

-- ==============================================================================
-- ANALYTICS TABLES
-- ==============================================================================

-- Table 10: Asset Correlations (60-day rolling)
CREATE TABLE analytics.correlations (
    date DATE NOT NULL,
    asset_1 VARCHAR(20) NOT NULL,
    asset_2 VARCHAR(20) NOT NULL,
    period_days INTEGER DEFAULT 60,
    correlation NUMERIC(10, 6),
    calculation_method VARCHAR(50) DEFAULT 'pearson',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, asset_1, asset_2, period_days)
);

SELECT create_hypertable('analytics.correlations', 'date', if_not_exists => TRUE);
CREATE INDEX idx_correlations_assets ON analytics.correlations (asset_1, asset_2, date DESC);

-- Table 11: Sector Rotation (Sector ETF performance)
CREATE TABLE analytics.sector_rotation (
    date DATE NOT NULL,
    sector VARCHAR(50) NOT NULL,  -- Technology, Healthcare, Energy, etc.
    etf_symbol VARCHAR(10),  -- XLK, XLV, XLE, etc.
    price NUMERIC(20, 4),
    volume BIGINT,
    change_1d NUMERIC(10, 4),
    change_1w NUMERIC(10, 4),
    change_1m NUMERIC(10, 4),
    change_ytd NUMERIC(10, 4),
    relative_strength NUMERIC(10, 4),  -- vs S&P 500
    rank INTEGER,  -- 1-11 ranking
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, sector)
);

SELECT create_hypertable('analytics.sector_rotation', 'date', if_not_exists => TRUE);
CREATE INDEX idx_sector_date ON analytics.sector_rotation (date DESC, rank);

-- Table 12: Sentiment Indicators
CREATE TABLE analytics.sentiment_indicators (
    timestamp TIMESTAMPTZ NOT NULL,
    put_call_ratio NUMERIC(10, 4),
    fear_greed_index INTEGER,  -- 0-100
    aaii_bullish NUMERIC(10, 4),
    aaii_bearish NUMERIC(10, 4),
    aaii_neutral NUMERIC(10, 4),
    investor_sentiment VARCHAR(20),  -- bullish, bearish, neutral
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp)
);

SELECT create_hypertable('analytics.sentiment_indicators', 'timestamp', if_not_exists => TRUE);
CREATE INDEX idx_sentiment_timestamp ON analytics.sentiment_indicators (timestamp DESC);

-- Table 13: Market Breadth (Advance/Decline, New Highs/Lows)
CREATE TABLE analytics.market_breadth (
    date DATE NOT NULL,
    exchange VARCHAR(20) NOT NULL,  -- NYSE, NASDAQ
    advances INTEGER,
    declines INTEGER,
    unchanged INTEGER,
    new_highs INTEGER,
    new_lows INTEGER,
    advancing_volume BIGINT,
    declining_volume BIGINT,
    total_volume BIGINT,
    advance_decline_ratio NUMERIC(10, 4),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, exchange)
);

SELECT create_hypertable('analytics.market_breadth', 'date', if_not_exists => TRUE);
CREATE INDEX idx_breadth_date ON analytics.market_breadth (date DESC, exchange);

-- ==============================================================================
-- SYSTEM TABLES
-- ==============================================================================

-- Table 14: Data Sources Configuration
CREATE TABLE system.data_sources (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) UNIQUE NOT NULL,
    source_name VARCHAR(100),
    category VARCHAR(50),  -- stocks, forex, crypto, economic, commodities
    api_endpoint TEXT,
    auth_method VARCHAR(50),  -- api_key, oauth, none
    rate_limit VARCHAR(100),
    cost VARCHAR(50),  -- free, paid, freemium
    priority INTEGER DEFAULT 5,  -- 1 = highest
    fallback_chain TEXT,  -- JSON array of fallback sources
    enabled BOOLEAN DEFAULT TRUE,
    health_check_url TEXT,
    last_health_check TIMESTAMPTZ,
    health_status VARCHAR(20) DEFAULT 'unknown',  -- operational, degraded, critical
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sources_enabled ON system.data_sources (enabled, priority);
CREATE INDEX idx_sources_health ON system.data_sources (health_status);

-- Table 15: Download Log (Audit trail)
CREATE TABLE system.download_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source_id VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200),
    success BOOLEAN,
    response_time_ms INTEGER,
    rows_inserted INTEGER,
    error_message TEXT,
    http_status INTEGER,
    data_category VARCHAR(50),
    FOREIGN KEY (source_id) REFERENCES system.data_sources(source_id)
);

CREATE INDEX idx_download_timestamp ON system.download_log (timestamp DESC);
CREATE INDEX idx_download_source ON system.download_log (source_id, timestamp DESC);
CREATE INDEX idx_download_success ON system.download_log (success, timestamp DESC);

-- Table 16: Health Status (Real-time health tracking)
CREATE TABLE system.health_status (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'unknown',  -- operational, degraded, critical, unknown
    last_success TIMESTAMPTZ,
    last_failure TIMESTAMPTZ,
    consecutive_failures INTEGER DEFAULT 0,
    consecutive_successes INTEGER DEFAULT 0,
    uptime_percent NUMERIC(10, 4),
    avg_response_time_ms INTEGER,
    total_requests BIGINT DEFAULT 0,
    successful_requests BIGINT DEFAULT 0,
    failed_requests BIGINT DEFAULT 0,
    last_error TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (source_id) REFERENCES system.data_sources(source_id)
);

CREATE INDEX idx_health_status ON system.health_status (status);
CREATE INDEX idx_health_updated ON system.health_status (updated_at DESC);

-- Table 17: API Rate Limits Tracking
CREATE TABLE system.api_rate_limits (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    requests_made INTEGER DEFAULT 0,
    requests_limit INTEGER,
    requests_remaining INTEGER,
    reset_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (source_id) REFERENCES system.data_sources(source_id),
    UNIQUE(source_id, period_start)
);

CREATE INDEX idx_rate_limits_source ON system.api_rate_limits (source_id, period_start DESC);

-- ==============================================================================
-- Helper Functions
-- ==============================================================================

-- Function: Get latest data for a symbol
CREATE OR REPLACE FUNCTION market_data.get_latest_quote(p_symbol VARCHAR)
RETURNS TABLE(
    symbol VARCHAR,
    price NUMERIC,
    change NUMERIC,
    change_percent NUMERIC,
    timestamp TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.symbol,
        i.price,
        i.change,
        i.change_percent,
        i.timestamp
    FROM market_data.indices i
    WHERE i.symbol = p_symbol
    ORDER BY i.timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate correlation between two assets
CREATE OR REPLACE FUNCTION analytics.calculate_correlation(
    p_asset_1 VARCHAR,
    p_asset_2 VARCHAR,
    p_days INTEGER DEFAULT 60
)
RETURNS NUMERIC AS $$
DECLARE
    v_correlation NUMERIC;
BEGIN
    SELECT corr(a1.price, a2.price) INTO v_correlation
    FROM market_data.indices a1
    JOIN market_data.indices a2
        ON a1.timestamp = a2.timestamp
    WHERE a1.symbol = p_asset_1
      AND a2.symbol = p_asset_2
      AND a1.timestamp >= NOW() - (p_days || ' days')::INTERVAL;

    RETURN v_correlation;
END;
$$ LANGUAGE plpgsql;

-- Function: Update health status
CREATE OR REPLACE FUNCTION system.update_health_status(
    p_source_id VARCHAR,
    p_success BOOLEAN,
    p_response_time_ms INTEGER DEFAULT NULL,
    p_error TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    IF p_success THEN
        UPDATE system.health_status
        SET
            status = 'operational',
            last_success = NOW(),
            consecutive_successes = consecutive_successes + 1,
            consecutive_failures = 0,
            total_requests = total_requests + 1,
            successful_requests = successful_requests + 1,
            avg_response_time_ms = COALESCE(
                (avg_response_time_ms * (total_requests - 1) + p_response_time_ms) / total_requests,
                p_response_time_ms
            ),
            uptime_percent = (successful_requests + 1)::NUMERIC / (total_requests + 1) * 100,
            updated_at = NOW()
        WHERE source_id = p_source_id;
    ELSE
        UPDATE system.health_status
        SET
            status = CASE
                WHEN consecutive_failures + 1 >= 3 THEN 'critical'
                WHEN consecutive_failures + 1 >= 2 THEN 'degraded'
                ELSE 'operational'
            END,
            last_failure = NOW(),
            consecutive_failures = consecutive_failures + 1,
            consecutive_successes = 0,
            total_requests = total_requests + 1,
            failed_requests = failed_requests + 1,
            uptime_percent = successful_requests::NUMERIC / (total_requests + 1) * 100,
            last_error = p_error,
            updated_at = NOW()
        WHERE source_id = p_source_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- Sample Data (for testing)
-- ==============================================================================

-- Insert sample data sources
INSERT INTO system.data_sources (source_id, source_name, category, rate_limit, cost, priority) VALUES
('yfinance', 'Yahoo Finance', 'stocks', 'unlimited', 'free', 1),
('fred_api', 'FRED Economic Data', 'economic', '120/minute', 'free', 1),
('polygon_io', 'Polygon.io', 'stocks', '5/minute (free)', 'paid', 1),
('alpha_vantage', 'Alpha Vantage', 'stocks', '25/day', 'free', 2),
('binance', 'Binance', 'crypto', '1200/minute', 'free', 1),
('coinbase', 'Coinbase Pro', 'crypto', '10/second', 'free', 2)
ON CONFLICT (source_id) DO NOTHING;

-- Initialize health status for all sources
INSERT INTO system.health_status (source_id)
SELECT source_id FROM system.data_sources
ON CONFLICT (source_id) DO NOTHING;

-- ==============================================================================
-- Performance Optimization
-- ==============================================================================

-- Analyze tables for query planner
ANALYZE market_data.indices;
ANALYZE market_data.commodities;
ANALYZE market_data.forex_rates;
ANALYZE market_data.crypto_prices;
ANALYZE economic_data.indicators;
ANALYZE economic_data.fred_series;
ANALYZE analytics.correlations;

-- ==============================================================================
-- Grants and Permissions
-- ==============================================================================

GRANT USAGE ON SCHEMA market_data TO spartan_user;
GRANT USAGE ON SCHEMA economic_data TO spartan_user;
GRANT USAGE ON SCHEMA analytics TO spartan_user;
GRANT USAGE ON SCHEMA system TO spartan_user;

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA market_data TO spartan_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA economic_data TO spartan_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA analytics TO spartan_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA system TO spartan_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA market_data TO spartan_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA economic_data TO spartan_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO spartan_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA system TO spartan_user;

-- ==============================================================================
-- Database Ready
-- ==============================================================================

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Spartan Research Station Database v2.0';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Schemas: 4 (market_data, economic_data, analytics, system)';
    RAISE NOTICE 'Tables: 17 (all with TimescaleDB hypertables where applicable)';
    RAISE NOTICE 'Extensions: timescaledb, pg_trgm, uuid-ossp, btree_gin, btree_gist';
    RAISE NOTICE 'Status: READY FOR PRE-LOADER';
    RAISE NOTICE '========================================';
END $$;