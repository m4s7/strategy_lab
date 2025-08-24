-- TimescaleDB Schema Optimizations for Strategy Lab

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS equity_points CASCADE;
DROP TABLE IF EXISTS system_metrics CASCADE;
DROP TABLE IF EXISTS backtests CASCADE;
DROP TABLE IF EXISTS optimizations CASCADE;
DROP TABLE IF EXISTS strategies CASCADE;

-- Strategies table (regular table, not time-series)
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    sharpe DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    total_trades INTEGER,
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Backtests table (time-series based on created_at)
CREATE TABLE backtests (
    id UUID DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    initial_capital DOUBLE PRECISION,
    start_date DATE,
    end_date DATE,
    total_return DOUBLE PRECISION,
    total_return_amount DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    total_trades INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (created_at, id)
);

-- Convert backtests to hypertable
SELECT create_hypertable('backtests', 'created_at', 
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

-- Equity points table (time-series)
CREATE TABLE equity_points (
    backtest_id UUID NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    day_number INTEGER NOT NULL,
    PRIMARY KEY (time, backtest_id)
);

-- Convert equity_points to hypertable
SELECT create_hypertable('equity_points', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);

-- System metrics table (high-frequency time-series)
CREATE TABLE system_metrics (
    time TIMESTAMPTZ NOT NULL,
    cpu_usage DOUBLE PRECISION NOT NULL,
    memory_used DOUBLE PRECISION NOT NULL,
    memory_total DOUBLE PRECISION NOT NULL,
    disk_io DOUBLE PRECISION NOT NULL,
    threads_active INTEGER NOT NULL,
    api_latency_ms DOUBLE PRECISION,
    active_strategies INTEGER,
    PRIMARY KEY (time)
);

-- Convert system_metrics to hypertable with smaller chunks for high-frequency data
SELECT create_hypertable('system_metrics', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Optimizations table (time-series based on created_at)
CREATE TABLE optimizations (
    id UUID DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    method VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    objective VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress DOUBLE PRECISION DEFAULT 0.0,
    best_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (created_at, id)
);

-- Convert optimizations to hypertable
SELECT create_hypertable('optimizations', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

-- Create indexes for better query performance
CREATE INDEX idx_strategies_status ON strategies(status);
CREATE INDEX idx_strategies_type ON strategies(strategy_type);
CREATE INDEX idx_strategies_updated ON strategies(updated_at DESC);

CREATE INDEX idx_backtests_strategy_id ON backtests(strategy_id, created_at DESC);
CREATE INDEX idx_backtests_status ON backtests(status, created_at DESC);

CREATE INDEX idx_equity_points_backtest ON equity_points(backtest_id, time DESC);

CREATE INDEX idx_optimizations_strategy ON optimizations(strategy_id, created_at DESC);
CREATE INDEX idx_optimizations_status ON optimizations(status, created_at DESC);

-- Create continuous aggregates for system metrics (1-minute aggregates)
CREATE MATERIALIZED VIEW system_metrics_1min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', time) AS bucket,
    AVG(cpu_usage) AS avg_cpu,
    MAX(cpu_usage) AS max_cpu,
    AVG(memory_used) AS avg_memory,
    AVG(disk_io) AS avg_disk_io,
    AVG(api_latency_ms) AS avg_latency,
    COUNT(*) AS sample_count
FROM system_metrics
GROUP BY bucket
WITH NO DATA;

-- Create continuous aggregates for system metrics (1-hour aggregates)
CREATE MATERIALIZED VIEW system_metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    AVG(cpu_usage) AS avg_cpu,
    MAX(cpu_usage) AS max_cpu,
    MIN(cpu_usage) AS min_cpu,
    AVG(memory_used) AS avg_memory,
    MAX(memory_used) AS max_memory,
    AVG(disk_io) AS avg_disk_io,
    AVG(api_latency_ms) AS avg_latency,
    COUNT(*) AS sample_count
FROM system_metrics
GROUP BY bucket
WITH NO DATA;

-- Add refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('system_metrics_1min',
    start_offset => INTERVAL '10 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('system_metrics_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Add compression policy for system_metrics (compress data older than 7 days)
SELECT add_compression_policy('system_metrics', 
    INTERVAL '7 days',
    if_not_exists => TRUE);

-- Add compression policy for equity_points (compress data older than 30 days)
SELECT add_compression_policy('equity_points', 
    INTERVAL '30 days',
    if_not_exists => TRUE);

-- Add retention policy for system_metrics (drop data older than 1 year)
SELECT add_retention_policy('system_metrics', 
    INTERVAL '1 year',
    if_not_exists => TRUE);

-- Insert sample strategies
INSERT INTO strategies (id, name, description, strategy_type, status, sharpe, win_rate, total_trades) VALUES
('11111111-1111-1111-1111-111111111111', 'Order Book Imbalance', 'Trades based on bid-ask volume imbalances', 'order_book', 'active', 1.80, 0.62, 1250),
('22222222-2222-2222-2222-222222222222', 'Bid-Ask Bounce', 'Mean reversion strategy on bid-ask spread', 'mean_reversion', 'active', 1.50, 0.58, 890),
('33333333-3333-3333-3333-333333333333', 'Momentum Breakout', 'Captures momentum after range breakouts', 'momentum', 'testing', 1.65, 0.55, 450);

-- Insert sample system metrics for the last hour
INSERT INTO system_metrics (time, cpu_usage, memory_used, memory_total, disk_io, threads_active, api_latency_ms, active_strategies)
SELECT 
    generate_series(
        NOW() - INTERVAL '1 hour',
        NOW(),
        INTERVAL '10 seconds'
    ) AS time,
    30 + random() * 40 AS cpu_usage,
    4 + random() * 2 AS memory_used,
    16.0 AS memory_total,
    random() * 200 AS disk_io,
    8 + floor(random() * 8)::INTEGER AS threads_active,
    5 + random() * 15 AS api_latency_ms,
    3 AS active_strategies;

-- Grant permissions to strategy_user
GRANT ALL ON ALL TABLES IN SCHEMA public TO strategy_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO strategy_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO strategy_user;