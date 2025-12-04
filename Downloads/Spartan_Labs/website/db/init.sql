-- Spartan Research Station - PostgreSQL Initialization Script
-- This script runs automatically when the database container first starts

-- Create database (if using different name)
-- CREATE DATABASE IF NOT EXISTS spartan_research_db;

-- Connect to database
\c spartan_research_db;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create schemas
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS cache;

-- ===== MARKET DATA SCHEMA =====

-- Symbols table
CREATE TABLE IF NOT EXISTS market_data.symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    asset_type VARCHAR(50), -- stock, forex, crypto, commodity, index
    exchange VARCHAR(100),
    country VARCHAR(100),
    currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price data table
CREATE TABLE IF NOT EXISTS market_data.prices (
    id BIGSERIAL PRIMARY KEY,
    symbol_id INTEGER REFERENCES market_data.symbols(id),
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol_id, timestamp)
);

-- Correlations table
CREATE TABLE IF NOT EXISTS market_data.correlations (
    id BIGSERIAL PRIMARY KEY,
    symbol1_id INTEGER REFERENCES market_data.symbols(id),
    symbol2_id INTEGER REFERENCES market_data.symbols(id),
    correlation DECIMAL(5, 4), -- -1.0000 to 1.0000
    period_days INTEGER,  -- 10, 20, 30, 50, etc.
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol1_id, symbol2_id, period_days)
);

-- ===== ANALYTICS SCHEMA =====

-- Trading signals
CREATE TABLE IF NOT EXISTS analytics.signals (
    id BIGSERIAL PRIMARY KEY,
    symbol_id INTEGER REFERENCES market_data.symbols(id),
    signal_type VARCHAR(50), -- buy, sell, neutral
    strength DECIMAL(5, 2), -- 0-100
    source VARCHAR(100), -- indicator name
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB, -- Additional signal details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Backtests
CREATE TABLE IF NOT EXISTS analytics.backtests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    strategy VARCHAR(100),
    start_date DATE,
    end_date DATE,
    initial_capital DECIMAL(20, 2),
    final_capital DECIMAL(20, 2),
    total_return DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    win_rate DECIMAL(5, 2),
    profit_factor DECIMAL(10, 2),
    total_trades INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== CACHE SCHEMA =====

-- API response cache
CREATE TABLE IF NOT EXISTS cache.api_responses (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp ON market_data.prices(symbol_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_correlations_symbols ON market_data.correlations(symbol1_id, symbol2_id);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON analytics.signals(symbol_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache.api_responses(expires_at);
CREATE INDEX IF NOT EXISTS idx_symbols_type ON market_data.symbols(asset_type);
CREATE INDEX IF NOT EXISTS idx_symbols_search ON market_data.symbols USING gin(to_tsvector('english', name || ' ' || symbol));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_symbols_updated_at BEFORE UPDATE ON market_data.symbols
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean expired cache
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM cache.api_responses WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Insert sample symbols
INSERT INTO market_data.symbols (symbol, name, asset_type, exchange, country, currency)
VALUES
    ('^GSPC', 'S&P 500', 'index', 'NYSE', 'USA', 'USD'),
    ('^IXIC', 'Nasdaq Composite', 'index', 'NASDAQ', 'USA', 'USD'),
    ('^DJI', 'Dow Jones Industrial Average', 'index', 'NYSE', 'USA', 'USD'),
    ('^RUT', 'Russell 2000', 'index', 'NYSE', 'USA', 'USD'),
    ('^N225', 'Nikkei 225', 'index', 'TSE', 'Japan', 'JPY'),
    ('^VIX', 'VIX Volatility Index', 'index', 'CBOE', 'USA', 'USD'),
    ('BTC-USD', 'Bitcoin', 'crypto', 'Crypto', 'Global', 'USD'),
    ('ETH-USD', 'Ethereum', 'crypto', 'Crypto', 'Global', 'USD'),
    ('EURUSD=X', 'EUR/USD', 'forex', 'FX', 'Global', 'USD'),
    ('GBPUSD=X', 'GBP/USD', 'forex', 'FX', 'Global', 'USD'),
    ('AUDJPY=X', 'AUD/JPY', 'forex', 'FX', 'Global', 'JPY'),
    ('GC=F', 'Gold Futures', 'commodity', 'COMEX', 'USA', 'USD'),
    ('SI=F', 'Silver Futures', 'commodity', 'COMEX', 'USA', 'USD'),
    ('CL=F', 'Crude Oil WTI Futures', 'commodity', 'NYMEX', 'USA', 'USD'),
    ('HG=F', 'Copper Futures', 'commodity', 'COMEX', 'USA', 'USD'),
    ('HYG', 'iShares High Yield Bond ETF', 'etf', 'NYSE', 'USA', 'USD'),
    ('TLT', '20+ Year Treasury Bond ETF', 'etf', 'NASDAQ', 'USA', 'USD'),
    ('IEF', '7-10 Year Treasury ETF', 'etf', 'NASDAQ', 'USA', 'USD'),
    ('SHY', '1-3 Year Treasury ETF', 'etf', 'NASDAQ', 'USA', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA market_data TO spartan;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO spartan;
GRANT ALL PRIVILEGES ON SCHEMA cache TO spartan;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_data TO spartan;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO spartan;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cache TO spartan;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA market_data TO spartan;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO spartan;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cache TO spartan;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Spartan Research Station Database Ready';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Schemas: market_data, analytics, cache';
    RAISE NOTICE 'Sample symbols inserted: 19';
    RAISE NOTICE 'PostgreSQL ONLY - NO SQLite';
    RAISE NOTICE '========================================';
END $$;
