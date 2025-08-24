-- Strategy Lab Database Schema

-- Strategies table
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    sharpe DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    total_trades INTEGER,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Backtests table
CREATE TABLE backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Backtest equity curve points
CREATE TABLE equity_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id UUID REFERENCES backtests(id) ON DELETE CASCADE,
    day INTEGER NOT NULL,
    value DOUBLE PRECISION NOT NULL
);

-- Optimizations table
CREATE TABLE optimizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    method VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    objective VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress DOUBLE PRECISION DEFAULT 0.0,
    best_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- System metrics (for historical tracking)
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cpu_usage DOUBLE PRECISION NOT NULL,
    memory_used DOUBLE PRECISION NOT NULL,
    memory_total DOUBLE PRECISION NOT NULL,
    disk_io DOUBLE PRECISION NOT NULL,
    threads_active INTEGER NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_strategies_status ON strategies(status);
CREATE INDEX idx_strategies_type ON strategies(strategy_type);
CREATE INDEX idx_backtests_strategy_id ON backtests(strategy_id);
CREATE INDEX idx_backtests_status ON backtests(status);
CREATE INDEX idx_equity_points_backtest_id ON equity_points(backtest_id);
CREATE INDEX idx_optimizations_strategy_id ON optimizations(strategy_id);
CREATE INDEX idx_optimizations_status ON optimizations(status);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);

-- Sample data
INSERT INTO strategies (id, name, description, strategy_type, status, sharpe, win_rate, total_trades, last_modified) VALUES
('11111111-1111-1111-1111-111111111111', 'Order Book Imbalance', 'Trades based on bid-ask volume imbalances', 'order_book', 'active', 1.80, 0.62, 1250, NOW()),
('22222222-2222-2222-2222-222222222222', 'Bid-Ask Bounce', 'Mean reversion strategy on bid-ask spread', 'mean_reversion', 'active', 1.50, 0.58, 890, NOW());