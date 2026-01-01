-- ============================================================================
-- Trading LLM Database Schema
-- PostgreSQL schema for AI-powered trading signals and trade tracking
-- ============================================================================

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS trading_llm_trade_notes CASCADE;
DROP TABLE IF EXISTS trading_llm_trades CASCADE;
DROP TABLE IF EXISTS trading_llm_signals CASCADE;
DROP TABLE IF EXISTS trading_llm_market_context CASCADE;
DROP TABLE IF EXISTS trading_llm_performance_daily CASCADE;

-- ============================================================================
-- TRADING SIGNALS TABLE
-- Stores all generated trading signals from the AI engine
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_llm_signals (
    id SERIAL PRIMARY KEY,

    -- Symbol identification
    symbol VARCHAR(20) NOT NULL,
    asset_class VARCHAR(20) NOT NULL CHECK (asset_class IN ('futures', 'stocks', 'forex', 'bonds', 'crypto', 'cfds')),

    -- Signal details
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('strong_buy', 'buy', 'hold', 'sell', 'strong_sell')),
    time_horizon VARCHAR(20) NOT NULL CHECK (time_horizon IN ('scalp', 'intraday', 'swing', 'position', 'investment')),
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),

    -- Price levels
    entry_price DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    risk_reward_ratio DECIMAL(10, 2),
    position_size_percent DECIMAL(5, 2),

    -- Analysis details
    reasoning TEXT,
    supporting_factors JSONB DEFAULT '[]'::jsonb,
    risk_factors JSONB DEFAULT '[]'::jsonb,
    data_sources JSONB DEFAULT '[]'::jsonb,

    -- Context at time of signal
    market_context JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Validation
    is_valid BOOLEAN DEFAULT TRUE,
    invalidated_reason TEXT
);

-- Indexes for signals table
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_llm_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_asset_class ON trading_llm_signals(asset_class);
CREATE INDEX IF NOT EXISTS idx_signals_signal_type ON trading_llm_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON trading_llm_signals(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_signals_created ON trading_llm_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_valid ON trading_llm_signals(is_valid) WHERE is_valid = TRUE;

-- ============================================================================
-- TRADES TABLE
-- Stores actual trades taken based on signals
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_llm_trades (
    id SERIAL PRIMARY KEY,

    -- Link to signal (optional - trades can be manual)
    signal_id INTEGER REFERENCES trading_llm_signals(id) ON DELETE SET NULL,

    -- Trade identification
    symbol VARCHAR(20) NOT NULL,
    asset_class VARCHAR(20) NOT NULL CHECK (asset_class IN ('futures', 'stocks', 'forex', 'bonds', 'crypto', 'cfds')),

    -- Trade direction
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('long', 'short')),

    -- Entry details
    entry_price DECIMAL(20, 8) NOT NULL,
    entry_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Position sizing
    quantity DECIMAL(20, 8),
    position_size DECIMAL(20, 8),
    position_size_percent DECIMAL(5, 2),

    -- Risk management
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    trailing_stop DECIMAL(20, 8),

    -- Exit details (filled when trade is closed)
    exit_price DECIMAL(20, 8),
    exit_time TIMESTAMP,
    exit_reason VARCHAR(50) CHECK (exit_reason IN ('stop_loss', 'take_profit', 'trailing_stop', 'manual', 'signal_invalidated', 'time_expiry')),

    -- P&L
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    realized_pnl_percent DECIMAL(10, 4) DEFAULT 0,
    fees DECIMAL(20, 8) DEFAULT 0,

    -- Trade metadata
    confidence INTEGER,
    reasoning TEXT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled', 'expired')),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Additional data
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for trades table
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trading_llm_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_asset_class ON trading_llm_trades(asset_class);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trading_llm_trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trading_llm_trades(entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trading_llm_trades(realized_pnl DESC) WHERE status = 'closed';
CREATE INDEX IF NOT EXISTS idx_trades_signal ON trading_llm_trades(signal_id);

-- ============================================================================
-- TRADE NOTES TABLE
-- Stores notes and learnings from trades
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_llm_trade_notes (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trading_llm_trades(id) ON DELETE CASCADE,
    note_type VARCHAR(20) NOT NULL CHECK (note_type IN ('entry', 'during', 'exit', 'review', 'learning')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trade_notes_trade ON trading_llm_trade_notes(trade_id);

-- ============================================================================
-- MARKET CONTEXT HISTORY TABLE
-- Stores historical market context snapshots
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_llm_market_context (
    id SERIAL PRIMARY KEY,

    -- Barometer data
    composite_score DECIMAL(5, 2),
    risk_status VARCHAR(10) CHECK (risk_status IN ('GREEN', 'YELLOW', 'RED')),

    -- Individual signals
    credit_signal VARCHAR(20),
    yield_curve_signal VARCHAR(20),
    copper_gold_signal VARCHAR(20),
    vix_level DECIMAL(10, 2),

    -- Macro regime
    growth_regime VARCHAR(20),
    inflation_regime VARCHAR(20),
    liquidity_regime VARCHAR(20),
    market_mode VARCHAR(20),

    -- COT positioning snapshot
    cot_signals JSONB DEFAULT '{}'::jsonb,

    -- Active patterns
    active_patterns JSONB DEFAULT '[]'::jsonb,

    -- Timestamp
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_context_time ON trading_llm_market_context(snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_context_risk ON trading_llm_market_context(risk_status);

-- ============================================================================
-- DAILY PERFORMANCE TABLE
-- Aggregated daily performance metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_llm_performance_daily (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,

    -- Trade counts
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    break_even_trades INTEGER DEFAULT 0,

    -- P&L metrics
    gross_pnl DECIMAL(20, 8) DEFAULT 0,
    net_pnl DECIMAL(20, 8) DEFAULT 0,
    total_fees DECIMAL(20, 8) DEFAULT 0,

    -- Win/Loss metrics
    win_rate DECIMAL(5, 2) DEFAULT 0,
    profit_factor DECIMAL(10, 2) DEFAULT 0,
    avg_win DECIMAL(20, 8) DEFAULT 0,
    avg_loss DECIMAL(20, 8) DEFAULT 0,
    largest_win DECIMAL(20, 8) DEFAULT 0,
    largest_loss DECIMAL(20, 8) DEFAULT 0,

    -- By asset class
    pnl_by_asset_class JSONB DEFAULT '{}'::jsonb,
    trades_by_asset_class JSONB DEFAULT '{}'::jsonb,

    -- Context
    avg_confidence DECIMAL(5, 2) DEFAULT 0,
    avg_market_score DECIMAL(5, 2) DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_performance_date ON trading_llm_performance_daily(trade_date DESC);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Latest active signals
CREATE OR REPLACE VIEW trading_llm_active_signals AS
SELECT *
FROM trading_llm_signals
WHERE is_valid = TRUE
  AND (expires_at IS NULL OR expires_at > NOW())
ORDER BY confidence DESC, created_at DESC;

-- Open trades
CREATE OR REPLACE VIEW trading_llm_open_trades AS
SELECT t.*, s.signal_type, s.time_horizon
FROM trading_llm_trades t
LEFT JOIN trading_llm_signals s ON t.signal_id = s.id
WHERE t.status = 'open'
ORDER BY t.entry_time DESC;

-- Trade performance summary
CREATE OR REPLACE VIEW trading_llm_performance_summary AS
SELECT
    COUNT(*) as total_trades,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_trades,
    COUNT(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 END) as winning_trades,
    COUNT(CASE WHEN status = 'closed' AND realized_pnl < 0 THEN 1 END) as losing_trades,
    COUNT(CASE WHEN status = 'closed' AND realized_pnl = 0 THEN 1 END) as break_even_trades,
    COALESCE(SUM(CASE WHEN status = 'closed' THEN realized_pnl END), 0) as total_pnl,
    COALESCE(AVG(CASE WHEN status = 'closed' THEN realized_pnl END), 0) as avg_pnl,
    COALESCE(AVG(confidence), 0) as avg_confidence,
    CASE
        WHEN COUNT(CASE WHEN status = 'closed' THEN 1 END) > 0
        THEN ROUND(
            COUNT(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 END)::DECIMAL /
            COUNT(CASE WHEN status = 'closed' THEN 1 END) * 100, 2
        )
        ELSE 0
    END as win_rate
FROM trading_llm_trades;

-- Performance by asset class
CREATE OR REPLACE VIEW trading_llm_performance_by_asset AS
SELECT
    asset_class,
    COUNT(*) as total_trades,
    COUNT(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 END) as wins,
    COUNT(CASE WHEN status = 'closed' AND realized_pnl < 0 THEN 1 END) as losses,
    COALESCE(SUM(CASE WHEN status = 'closed' THEN realized_pnl END), 0) as total_pnl,
    COALESCE(AVG(CASE WHEN status = 'closed' THEN realized_pnl END), 0) as avg_pnl
FROM trading_llm_trades
GROUP BY asset_class
ORDER BY total_pnl DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update trade P&L when closing
CREATE OR REPLACE FUNCTION calculate_trade_pnl()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'closed' AND NEW.exit_price IS NOT NULL THEN
        IF NEW.direction = 'long' THEN
            NEW.realized_pnl = (NEW.exit_price - NEW.entry_price) * COALESCE(NEW.quantity, 1);
            NEW.realized_pnl_percent = ((NEW.exit_price - NEW.entry_price) / NEW.entry_price) * 100;
        ELSE
            NEW.realized_pnl = (NEW.entry_price - NEW.exit_price) * COALESCE(NEW.quantity, 1);
            NEW.realized_pnl_percent = ((NEW.entry_price - NEW.exit_price) / NEW.entry_price) * 100;
        END IF;
        NEW.realized_pnl = NEW.realized_pnl - COALESCE(NEW.fees, 0);
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for P&L calculation
DROP TRIGGER IF EXISTS trigger_calculate_pnl ON trading_llm_trades;
CREATE TRIGGER trigger_calculate_pnl
BEFORE UPDATE ON trading_llm_trades
FOR EACH ROW
EXECUTE FUNCTION calculate_trade_pnl();

-- Function to update daily performance
CREATE OR REPLACE FUNCTION update_daily_performance(p_date DATE)
RETURNS VOID AS $$
DECLARE
    v_stats RECORD;
BEGIN
    SELECT
        COUNT(*) as total_trades,
        COUNT(CASE WHEN realized_pnl > 0 THEN 1 END) as winning_trades,
        COUNT(CASE WHEN realized_pnl < 0 THEN 1 END) as losing_trades,
        COUNT(CASE WHEN realized_pnl = 0 THEN 1 END) as break_even_trades,
        COALESCE(SUM(realized_pnl), 0) as net_pnl,
        COALESCE(SUM(fees), 0) as total_fees,
        COALESCE(AVG(realized_pnl), 0) as avg_pnl,
        COALESCE(AVG(confidence), 0) as avg_confidence,
        COALESCE(MAX(CASE WHEN realized_pnl > 0 THEN realized_pnl END), 0) as largest_win,
        COALESCE(MIN(CASE WHEN realized_pnl < 0 THEN realized_pnl END), 0) as largest_loss
    INTO v_stats
    FROM trading_llm_trades
    WHERE DATE(exit_time) = p_date AND status = 'closed';

    INSERT INTO trading_llm_performance_daily (
        trade_date, total_trades, winning_trades, losing_trades, break_even_trades,
        net_pnl, total_fees, avg_confidence, largest_win, largest_loss,
        win_rate, updated_at
    ) VALUES (
        p_date, v_stats.total_trades, v_stats.winning_trades, v_stats.losing_trades,
        v_stats.break_even_trades, v_stats.net_pnl, v_stats.total_fees,
        v_stats.avg_confidence, v_stats.largest_win, v_stats.largest_loss,
        CASE WHEN v_stats.total_trades > 0
            THEN ROUND(v_stats.winning_trades::DECIMAL / v_stats.total_trades * 100, 2)
            ELSE 0 END,
        NOW()
    )
    ON CONFLICT (trade_date) DO UPDATE SET
        total_trades = EXCLUDED.total_trades,
        winning_trades = EXCLUDED.winning_trades,
        losing_trades = EXCLUDED.losing_trades,
        break_even_trades = EXCLUDED.break_even_trades,
        net_pnl = EXCLUDED.net_pnl,
        total_fees = EXCLUDED.total_fees,
        avg_confidence = EXCLUDED.avg_confidence,
        largest_win = EXCLUDED.largest_win,
        largest_loss = EXCLUDED.largest_loss,
        win_rate = EXCLUDED.win_rate,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA (for testing - remove in production)
-- ============================================================================

-- Uncomment to insert sample data:
/*
INSERT INTO trading_llm_signals (symbol, asset_class, signal_type, time_horizon, confidence, entry_price, stop_loss, take_profit, risk_reward_ratio, position_size_percent, reasoning, supporting_factors, risk_factors, data_sources)
VALUES
    ('ES', 'futures', 'buy', 'swing', 75, 4800.00, 4750.00, 4900.00, 2.0, 2.5, 'Bullish momentum with strong barometer readings', '["Risk-On macro regime", "Commercial accumulation in COT"]'::jsonb, '["VIX elevated"]'::jsonb, '["Barometers API", "CFTC COT"]'::jsonb),
    ('EURUSD', 'forex', 'sell', 'swing', 65, 1.0850, 1.0900, 1.0750, 2.0, 1.5, 'USD strength expected', '["Yield differentials favor USD"]'::jsonb, '["ECB hawkish rhetoric"]'::jsonb, '["Macro Regime Tracker"]'::jsonb),
    ('AAPL', 'stocks', 'buy', 'position', 80, 180.00, 170.00, 200.00, 2.0, 3.0, 'Strong earnings momentum', '["Green barometer status", "Sector rotation favoring tech"]'::jsonb, '[]'::jsonb, '["Breakthrough Insights", "Barometers API"]'::jsonb);
*/

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to the postgres user (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables were created
DO $$
BEGIN
    RAISE NOTICE 'Trading LLM Schema Installation Complete';
    RAISE NOTICE 'Tables created: trading_llm_signals, trading_llm_trades, trading_llm_trade_notes, trading_llm_market_context, trading_llm_performance_daily';
    RAISE NOTICE 'Views created: trading_llm_active_signals, trading_llm_open_trades, trading_llm_performance_summary, trading_llm_performance_by_asset';
END $$;
