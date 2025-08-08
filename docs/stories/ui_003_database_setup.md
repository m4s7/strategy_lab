# Story UI_003: Database Setup and Connection

## Story Details
- **Story ID**: UI_003
- **Epic**: Epic 1 - Foundation Infrastructure
- **Story Points**: 3
- **Priority**: Critical
- **Type**: Technical Foundation
- **Status**: Done

## User Story
**As a** developer
**I want** a properly configured database layer
**So that** I can persist application data reliably

## Acceptance Criteria

### 1. SQLite Database Configuration
- [ ] SQLite database file created in correct location (`data/strategy_lab.db`)
- [ ] Database directory structure established
- [ ] File permissions configured properly
- [ ] Backup location identified and configured

### 2. SQLAlchemy ORM Setup
- [ ] Async SQLAlchemy engine configured
- [ ] Session management with async context managers
- [ ] Connection pooling configured appropriately
- [ ] Database URL configuration in settings

### 3. Initial Schema Creation
- [ ] `backtests` table with proper columns and types
- [ ] `backtest_results` table with foreign key relationships
- [ ] `optimization_jobs` table for optimization tracking
- [ ] `user_preferences` table for settings persistence
- [ ] Proper indexes created for performance

### 4. Database Migration System
- [ ] Alembic migration tool configured
- [ ] Initial migration scripts created
- [ ] Migration command structure documented
- [ ] Rollback capability tested

### 5. Database Health and Monitoring
- [ ] Database connection health check endpoint
- [ ] Connection retry logic implemented
- [ ] Proper error handling for database failures
- [ ] Connection pool monitoring

## Technical Requirements

### Database Schema
```sql
-- Backtests table
CREATE TABLE backtests (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    config JSON NOT NULL,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_path TEXT
);

-- Backtest Results table
CREATE TABLE backtest_results (
    id TEXT PRIMARY KEY,
    backtest_id TEXT REFERENCES backtests(id) ON DELETE CASCADE,
    metrics JSON NOT NULL,
    equity_curve BLOB,  -- Compressed time series data
    trades_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimization Jobs table
CREATE TABLE optimization_jobs (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    optimization_type TEXT CHECK(optimization_type IN ('grid', 'genetic', 'walk_forward')),
    config JSON NOT NULL,
    status TEXT,
    best_params JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- User Preferences table
CREATE TABLE user_preferences (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Performance Indexes
```sql
CREATE INDEX idx_backtests_status ON backtests(status);
CREATE INDEX idx_backtests_created_desc ON backtests(created_at DESC);
CREATE INDEX idx_backtests_strategy ON backtests(strategy_id);
CREATE INDEX idx_results_backtest ON backtest_results(backtest_id);
CREATE INDEX idx_optimization_status ON optimization_jobs(status);
```

### SQLAlchemy Models
```python
# Base model with common fields
class BaseModel(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# Backtest model
class Backtest(BaseModel):
    __tablename__ = "backtests"

    id: Mapped[str] = mapped_column(primary_key=True)
    strategy_id: Mapped[str]
    config: Mapped[dict] = mapped_column(JSON)
    status: Mapped[BacktestStatus]
    started_at: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    error_message: Mapped[Optional[str]]
    result_path: Mapped[Optional[str]]

    # Relationships
    results: Mapped[List["BacktestResult"]] = relationship(back_populates="backtest")
```

## Definition of Done
- [ ] Database file created and accessible
- [ ] All tables created with proper schema
- [ ] SQLAlchemy models defined and working
- [ ] Database connection health check passes
- [ ] Migration system functional
- [ ] Sample data can be inserted and retrieved
- [ ] Connection pool working under load
- [ ] Backup/restore procedures documented

## Testing Checklist
- [ ] Database connection successful
- [ ] All CRUD operations work on each table
- [ ] Foreign key constraints enforced
- [ ] Indexes improve query performance
- [ ] Migration up/down operations work
- [ ] Connection pool handles concurrent requests
- [ ] Database file permissions correct

## Integration Points
- **FastAPI Integration**: Database dependency injection
- **Configuration**: Environment-based database URL
- **Health Monitoring**: Database health in overall system health
- **Data Models**: Pydantic models that match SQLAlchemy models

## Performance Requirements
- Database query response time < 100ms for simple operations
- Connection pool supports up to 10 concurrent connections
- Database file size monitoring and alerting
- Query optimization with proper indexing

## Security Considerations
- Database file permissions (read/write for application only)
- SQL injection prevention through ORM
- Sensitive data encryption at rest (if needed)
- Connection string security

## Implementation Notes
- Use async SQLAlchemy for better performance
- Implement proper connection cleanup
- Add database migration versioning
- Include database seeding for development
- Configure proper logging for database operations

## Follow-up Stories
- UI_004: WebSocket Infrastructure
- UI_011: System Dashboard (will display database status)
- UI_013: Data Configuration Interface (will query database)
