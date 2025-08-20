-- Strategy Lab Database Schema
-- PostgreSQL database schema for high-frequency trading strategy backtesting

-- Create database if not exists
-- CREATE DATABASE strategy_lab;

-- Use strategy_lab database
-- \c strategy_lab;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    tags TEXT[] DEFAULT '{}',
    UNIQUE(name, version)
);

-- Backtest runs table
CREATE TABLE IF NOT EXISTS backtest_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    initial_capital DECIMAL(20, 2) NOT NULL,
    final_equity DECIMAL(20, 2),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    parameters JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    ticks_processed BIGINT DEFAULT 0,
    execution_time_ms BIGINT,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    total_return DOUBLE PRECISION,
    annualized_return DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    sortino_ratio DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    calmar_ratio DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    avg_win DECIMAL(20, 2),
    avg_loss DECIMAL(20, 2),
    largest_win DECIMAL(20, 2),
    largest_loss DECIMAL(20, 2),
    avg_trade_duration_ms BIGINT,
    max_consecutive_wins INTEGER,
    max_consecutive_losses INTEGER,
    commission_total DECIMAL(20, 2),
    slippage_total DECIMAL(20, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    trade_number INTEGER NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 4) NOT NULL,
    exit_price DECIMAL(20, 4) NOT NULL,
    quantity INTEGER NOT NULL,
    pnl DECIMAL(20, 2) NOT NULL,
    commission DECIMAL(20, 2),
    slippage DECIMAL(20, 2),
    max_adverse_excursion DECIMAL(20, 4),
    max_favorable_excursion DECIMAL(20, 4),
    entry_reason TEXT,
    exit_reason TEXT,
    CONSTRAINT valid_side CHECK (side IN ('long', 'short'))
);

-- Optimization runs table
CREATE TABLE IF NOT EXISTS optimization_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    optimization_type VARCHAR(50) NOT NULL,
    parameter_ranges JSONB NOT NULL,
    optimization_metric VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_combinations INTEGER,
    completed_combinations INTEGER DEFAULT 0,
    best_parameters JSONB,
    best_metric_value DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms BIGINT,
    CONSTRAINT valid_opt_type CHECK (optimization_type IN ('grid_search', 'genetic', 'walk_forward', 'bayesian')),
    CONSTRAINT valid_opt_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Optimization results table
CREATE TABLE IF NOT EXISTS optimization_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    optimization_id UUID NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
    parameters JSONB NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    sharpe_ratio DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    total_return DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    total_trades INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Walk-forward windows table
CREATE TABLE IF NOT EXISTS walk_forward_windows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    optimization_id UUID NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
    window_number INTEGER NOT NULL,
    training_start TIMESTAMP WITH TIME ZONE NOT NULL,
    training_end TIMESTAMP WITH TIME ZONE NOT NULL,
    testing_start TIMESTAMP WITH TIME ZONE NOT NULL,
    testing_end TIMESTAMP WITH TIME ZONE NOT NULL,
    in_sample_parameters JSONB NOT NULL,
    in_sample_sharpe DOUBLE PRECISION,
    out_of_sample_sharpe DOUBLE PRECISION,
    in_sample_return DOUBLE PRECISION,
    out_of_sample_return DOUBLE PRECISION,
    parameter_stability DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Market data cache table (for processed data)
CREATE TABLE IF NOT EXISTS market_data_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    contract_month VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    file_path TEXT NOT NULL,
    total_rows BIGINT,
    l1_count BIGINT,
    l2_count BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    UNIQUE(symbol, contract_month, date)
);

-- System metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(50) NOT NULL,
    job_id UUID,
    cpu_usage DOUBLE PRECISION,
    memory_usage_mb BIGINT,
    disk_io_read_mb DOUBLE PRECISION,
    disk_io_write_mb DOUBLE PRECISION,
    network_io_sent_mb DOUBLE PRECISION,
    network_io_recv_mb DOUBLE PRECISION,
    active_threads INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for better query performance
CREATE INDEX idx_backtest_runs_strategy_id ON backtest_runs(strategy_id);
CREATE INDEX idx_backtest_runs_status ON backtest_runs(status);
CREATE INDEX idx_backtest_runs_created_at ON backtest_runs(created_at DESC);

CREATE INDEX idx_trades_backtest_id ON trades(backtest_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_pnl ON trades(pnl DESC);

CREATE INDEX idx_optimization_runs_strategy_id ON optimization_runs(strategy_id);
CREATE INDEX idx_optimization_runs_status ON optimization_runs(status);
CREATE INDEX idx_optimization_results_optimization_id ON optimization_results(optimization_id);
CREATE INDEX idx_optimization_results_metric_value ON optimization_results(metric_value DESC);

CREATE INDEX idx_walk_forward_windows_optimization_id ON walk_forward_windows(optimization_id);
CREATE INDEX idx_market_data_cache_lookup ON market_data_cache(symbol, contract_month, date);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp DESC);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW v_recent_backtests AS
SELECT 
    br.id,
    s.name as strategy_name,
    s.version as strategy_version,
    br.start_time,
    br.end_time,
    br.initial_capital,
    br.final_equity,
    br.status,
    pm.sharpe_ratio,
    pm.max_drawdown,
    pm.total_return,
    pm.win_rate,
    pm.total_trades,
    br.created_at
FROM backtest_runs br
JOIN strategies s ON br.strategy_id = s.id
LEFT JOIN performance_metrics pm ON pm.backtest_id = br.id
ORDER BY br.created_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW v_strategy_performance AS
SELECT 
    s.id,
    s.name,
    s.version,
    COUNT(DISTINCT br.id) as total_backtests,
    AVG(pm.sharpe_ratio) as avg_sharpe_ratio,
    AVG(pm.total_return) as avg_return,
    AVG(pm.max_drawdown) as avg_max_drawdown,
    AVG(pm.win_rate) as avg_win_rate,
    MAX(pm.sharpe_ratio) as best_sharpe,
    MIN(pm.max_drawdown) as best_drawdown
FROM strategies s
LEFT JOIN backtest_runs br ON s.id = br.strategy_id
LEFT JOIN performance_metrics pm ON br.id = pm.backtest_id
WHERE br.status = 'completed'
GROUP BY s.id, s.name, s.version;

-- Create materialized view for optimization analysis
CREATE MATERIALIZED VIEW mv_optimization_summary AS
SELECT 
    opt.id,
    opt.strategy_id,
    s.name as strategy_name,
    opt.optimization_type,
    opt.optimization_metric,
    opt.total_combinations,
    opt.completed_combinations,
    opt.best_metric_value,
    COUNT(DISTINCT res.id) as result_count,
    AVG(res.sharpe_ratio) as avg_sharpe,
    MAX(res.sharpe_ratio) as max_sharpe,
    MIN(res.max_drawdown) as min_drawdown,
    opt.created_at
FROM optimization_runs opt
JOIN strategies s ON opt.strategy_id = s.id
LEFT JOIN optimization_results res ON opt.id = res.optimization_id
GROUP BY opt.id, opt.strategy_id, s.name, opt.optimization_type, 
         opt.optimization_metric, opt.total_combinations, 
         opt.completed_combinations, opt.best_metric_value, opt.created_at;

-- Create index on materialized view
CREATE INDEX idx_mv_optimization_summary_strategy ON mv_optimization_summary(strategy_id);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_optimization_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_optimization_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO strategy_lab_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO strategy_lab_user;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO strategy_lab_user;