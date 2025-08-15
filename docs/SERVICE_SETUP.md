# Strategy Lab Service Setup Guide

This guide explains how to set up Strategy Lab as system services on Ubuntu Server.

## Overview

The setup includes:
- **Backend**: FastAPI application running on port 8000
- **Frontend**: Next.js application running on port 3000
- **Nginx**: Reverse proxy handling HTTPS and routing
- **PostgreSQL**: Database server
- **Redis**: Cache and session storage

## Prerequisites

1. Ubuntu Server (20.04+ recommended)
2. Domain pointing to your server (lab.m4s8.dev)
3. PostgreSQL and Redis installed
4. Python 3.12+ with uv package manager
5. Node.js 20+ with pnpm
6. Nginx installed
7. Certbot for SSL certificates

## Quick Setup

1. **Run the setup script** (as root/sudo):
   ```bash
   sudo ./scripts/setup-services.sh
   ```

2. **Configure environment variables**:
   ```bash
   sudo nano /home/dev/strategy_lab/.env.production
   ```
   Update database credentials and JWT secret.

3. **Set up the database**:
   ```bash
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE strategylab;
   CREATE USER strategylab WITH PASSWORD 'your-secure-password';
   GRANT ALL PRIVILEGES ON DATABASE strategylab TO strategylab;
   \q

   # Run migrations
   cd /home/dev/strategy_lab/backend
   uv run alembic upgrade head
   ```

4. **Start services**:
   ```bash
   ./scripts/manage-services.sh start
   ```

5. **Check health**:
   ```bash
   ./scripts/health-check.sh
   ```

## Service Management

Use the management script for common tasks:

```bash
# Check status
./scripts/manage-services.sh status

# Start all services
./scripts/manage-services.sh start

# Stop services
./scripts/manage-services.sh stop

# Restart services
./scripts/manage-services.sh restart

# View logs
./scripts/manage-services.sh logs

# Follow logs in real-time
./scripts/manage-services.sh follow

# Update and restart
./scripts/manage-services.sh update
```

## Manual Service Control

### Backend Service
```bash
# Start/stop/restart
sudo systemctl start strategylab-backend
sudo systemctl stop strategylab-backend
sudo systemctl restart strategylab-backend

# View logs
sudo journalctl -u strategylab-backend -f
tail -f /var/log/strategylab/backend.log
```

### Frontend Service
```bash
# Start/stop/restart
sudo systemctl start strategylab-frontend
sudo systemctl stop strategylab-frontend
sudo systemctl restart strategylab-frontend

# View logs
sudo journalctl -u strategylab-frontend -f
tail -f /var/log/strategylab/frontend.log
```

### Nginx
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# View logs
tail -f /var/log/nginx/strategylab-*.log
```

## File Locations

- **Service files**: `/etc/systemd/system/strategylab-*.service`
- **Nginx config**: `/home/dev/strategy_lab/nginx/sites-available/lab.m4s8.dev`
- **Environment file**: `/home/dev/strategy_lab/.env.production`
- **Log files**: `/var/log/strategylab/`
- **Nginx cache**: `/var/cache/nginx/strategylab/`

## SSL Certificate

The setup script will automatically obtain a Let's Encrypt certificate. To renew manually:

```bash
sudo certbot renew
```

Automatic renewal is handled by certbot's systemd timer.

## Troubleshooting

### Service won't start
1. Check logs: `sudo journalctl -u strategylab-backend -n 50`
2. Verify environment file exists and is readable
3. Ensure PostgreSQL and Redis are running
4. Check file permissions

### 502 Bad Gateway
1. Ensure backend service is running
2. Check if backend is listening on port 8000
3. Review nginx error logs

### Frontend build fails
1. Check Node.js and pnpm versions
2. Clear Next.js cache: `rm -rf /home/dev/strategy_lab/frontend/.next`
3. Reinstall dependencies: `cd frontend && pnpm install`

### Database connection issues
1. Verify PostgreSQL is running
2. Check credentials in `.env.production`
3. Ensure database exists and user has permissions
4. Test connection: `psql -U strategylab -d strategylab -h localhost`

## Security Considerations

1. **Firewall**: Only ports 80 and 443 should be open
2. **SSL**: Always use HTTPS in production
3. **Environment**: Keep `.env.production` secure (chmod 600)
4. **Updates**: Regularly update dependencies and system packages
5. **Monitoring**: Set up monitoring for service health

## Backup

Regular backups should include:
- PostgreSQL database
- Redis data (if persistent)
- Environment configuration
- Application logs

Use the provided backup script:
```bash
./scripts/backup.sh
```

## Performance Tuning

### Backend
- Adjust worker count in service file based on CPU cores
- Configure PostgreSQL for your workload
- Monitor Redis memory usage

### Frontend
- Enable Next.js production optimizations
- Configure CDN for static assets
- Monitor build sizes

### Nginx
- Tune worker processes and connections
- Adjust cache sizes based on traffic
- Enable HTTP/2 and compression

## Support

For issues:
1. Check service logs
2. Run health check script
3. Review this documentation
4. Check GitHub issues
