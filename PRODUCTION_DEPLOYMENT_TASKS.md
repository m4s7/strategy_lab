# Strategy Lab Production Deployment Tasks

## Overview
Production deployment plan for Strategy Lab with TimescaleDB, without Docker, for single-user private network deployment.

## Task List

### TimescaleDB Setup
- [ ] **Install PostgreSQL with TimescaleDB extension** - Install PostgreSQL and TimescaleDB extension for time-series optimization
- [ ] **Create TimescaleDB database and hypertables for time-series data** - Convert system_metrics, equity_points tables to hypertables
- [ ] **Update database schema for TimescaleDB optimization** - Modify schema to use TimescaleDB-specific features
- [ ] **Configure TimescaleDB continuous aggregates for metrics** - Pre-compute hourly/daily aggregates for performance
- [ ] **Set up TimescaleDB compression policies for historical data** - Compress data older than 30 days to save space
- [ ] **Add TimescaleDB retention policies for old data** - Auto-delete data older than 1 year

### Database Performance
- [ ] **Implement database connection pooling with pgBouncer** - Optimize connection handling for TimescaleDB
- [ ] **Update API server to use TimescaleDB features** - Leverage time-series queries and aggregations

### Application Build & Configuration
- [ ] **Build frontend and backend in production mode** - Compile Rust with --release, build Next.js for production
- [ ] **Configure environment variables for production** - Set DATABASE_URL with TimescaleDB connection
- [ ] **Configure CORS for production environment** - Restrict to specific origins

### Service Management
- [ ] **Configure systemd services for backend and frontend** - Create service files for automatic startup
- [ ] **Set up automatic restart on failure with systemd** - Configure restart policies
- [ ] **Add graceful shutdown handling for services** - Proper SIGTERM handling

### Networking & Security
- [ ] **Set up Nginx as reverse proxy for both services** - Route /api to backend, / to frontend
- [ ] **Configure firewall rules for services** - Only expose ports 80/443

### Real-time Features
- [ ] **Implement WebSocket server for real-time monitoring** - Stream time-series data from TimescaleDB

### Monitoring & Logging
- [ ] **Add health checks and monitoring endpoints** - Include TimescaleDB health status
- [ ] **Add structured logging with log levels** - Log TimescaleDB query performance
- [ ] **Set up log rotation with logrotate** - Manage application and database logs
- [ ] **Create monitoring dashboard using TimescaleDB queries** - Real-time metrics with TimescaleDB aggregations

### Deployment & Maintenance
- [ ] **Create deployment script for easy updates** - Include TimescaleDB migration handling
- [ ] **Create TimescaleDB backup strategy with pg_dump** - Backup with TimescaleDB-specific options
- [ ] **Document TimescaleDB maintenance procedures** - Compression, retention, backup procedures

## Priority Order

### Phase 1: Database Foundation (Critical)
1. Install PostgreSQL with TimescaleDB extension
2. Create TimescaleDB database and hypertables
3. Update database schema for TimescaleDB optimization
4. Update API server to use TimescaleDB features

### Phase 2: Production Build (Critical)
5. Build frontend and backend in production mode
6. Configure environment variables for production
7. Configure CORS for production environment

### Phase 3: Service Infrastructure (Critical)
8. Configure systemd services for backend and frontend
9. Set up Nginx as reverse proxy for both services
10. Configure firewall rules for services

### Phase 4: Reliability (Important)
11. Set up automatic restart on failure with systemd
12. Add graceful shutdown handling for services
13. Add health checks and monitoring endpoints
14. Implement database connection pooling with pgBouncer

### Phase 5: Performance & Monitoring (Important)
15. Configure TimescaleDB continuous aggregates for metrics
16. Implement WebSocket server for real-time monitoring
17. Create monitoring dashboard using TimescaleDB queries
18. Add structured logging with log levels

### Phase 6: Maintenance & Operations (Nice to have)
19. Set up TimescaleDB compression policies for historical data
20. Add TimescaleDB retention policies for old data
21. Set up log rotation with logrotate
22. Create deployment script for easy updates
23. Create TimescaleDB backup strategy with pg_dump
24. Document TimescaleDB maintenance procedures

## Notes
- No authentication required (single user, private network)
- No Docker containerization
- Focus on TimescaleDB for time-series data optimization
- All services run directly on the host system with systemd

## Current Status
- [x] Standalone API server created
- [x] Frontend API routes updated to proxy to backend
- [x] Database schema created with TimescaleDB optimizations
- [x] TimescaleDB installation script created
- [x] Database setup and migration scripts created
- [x] Production build scripts created
- [x] SystemD service configuration created
- [x] Nginx reverse proxy configuration created
- [x] WebSocket server for real-time monitoring implemented
- [x] Complete deployment script created
- [ ] Production deployment execution pending

## Scripts Created
- `scripts/install_timescaledb.sh` - Installs PostgreSQL with TimescaleDB
- `scripts/setup_database.sh` - Creates database and user
- `scripts/run_migrations.sh` - Runs database migrations
- `scripts/build_production.sh` - Builds frontend and backend for production
- `scripts/setup_services.sh` - Configures systemd services
- `scripts/setup_nginx.sh` - Sets up Nginx reverse proxy
- `deploy.sh` - Master deployment script that runs everything

## Ready for Production
All components are implemented and ready. Run `sudo bash deploy.sh` to deploy everything.

Last Updated: 2025-08-24