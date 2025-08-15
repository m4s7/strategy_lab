# Strategy Lab Deployment Guide

## Overview

This guide covers the deployment process for Strategy Lab, including infrastructure setup, deployment procedures, monitoring, and maintenance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Initial Deployment](#initial-deployment)
4. [Continuous Deployment](#continuous-deployment)
5. [Monitoring](#monitoring)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

## Prerequisites

### Local Requirements
- Git
- Docker and Docker Compose
- Terraform >= 1.0
- SSH key pair for server access
- Domain name (e.g., lab.m4s8.dev)

### Cloud Accounts
- DigitalOcean account with API token
- GitHub account with repository access
- Cloudflare account (optional, for DNS)

### Environment Variables
Create a `.env.prod` file with:
```bash
# Database
DB_USER=postgres
DB_PASSWORD=<secure-password>
DB_NAME=strategy_lab

# Redis
REDIS_PASSWORD=<secure-password>

# Application
JWT_SECRET=<secure-secret>
CORS_ORIGINS=https://lab.m4s8.dev
NEXT_PUBLIC_API_URL=https://lab.m4s8.dev/api

# Monitoring
GRAFANA_PASSWORD=<secure-password>
```

## Infrastructure Setup

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create terraform.tfvars

```hcl
do_token         = "your-digitalocean-token"
cloudflare_token = "your-cloudflare-token"
domain          = "lab.m4s8.dev"
admin_email     = "admin@m4s8.dev"
```

### 3. Plan Infrastructure

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

This will create:
- Ubuntu 22.04 droplet (4 vCPU, 8GB RAM)
- PostgreSQL 15 managed database
- Redis 7 managed cache
- VPC for network isolation
- Firewall rules
- Object storage for backups
- Monitoring alerts

### 5. Note Outputs

```bash
terraform output -json > infrastructure.json
```

## Initial Deployment

### 1. SSH to Server

```bash
ssh deploy@<floating-ip>
```

### 2. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/strategy-lab.git
sudo chown -R deploy:deploy strategy-lab
cd strategy-lab
```

### 3. Configure Environment

```bash
# Copy production environment file
cp .env.prod.example .env.prod
# Edit with your values
nano .env.prod
```

### 4. Initial SSL Certificate

```bash
# Run certbot
docker-compose -f docker-compose.prod.yml --profile certbot up certbot
```

### 5. Start Services

```bash
# Pull images
docker-compose -f docker-compose.prod.yml pull

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

### 6. Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl https://lab.m4s8.dev/api/health
curl https://lab.m4s8.dev
```

## Continuous Deployment

### GitHub Actions Setup

1. Add secrets to GitHub repository:
   - `DEPLOY_HOST`: Server IP address
   - `DEPLOY_USER`: deploy
   - `DEPLOY_KEY`: Private SSH key
   - `DB_USER`, `DB_PASSWORD`, `DB_NAME`
   - `JWT_SECRET`, `REDIS_PASSWORD`
   - `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`
   - `GRAFANA_PASSWORD`
   - `SLACK_WEBHOOK` (optional)

2. Deployment workflow triggers on:
   - Push to main branch
   - Manual workflow dispatch

### Deployment Process

1. **Tests**: Run unit and integration tests
2. **Build**: Build Docker images and push to registry
3. **Deploy**:
   - SSH to server
   - Pull latest code
   - Update environment variables
   - Pull new images
   - Run migrations
   - Restart services with zero downtime
4. **Verify**: Run smoke tests
5. **Notify**: Send deployment status

### Manual Deployment

```bash
# SSH to server
ssh deploy@<server-ip>

# Navigate to project
cd /opt/strategy-lab

# Pull latest changes
git pull origin main

# Deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Clean up
docker system prune -af
```

## Monitoring

### Access Monitoring Tools

1. **Grafana**: https://lab.m4s8.dev:3001
   - Username: admin
   - Password: (from GRAFANA_PASSWORD)

2. **Prometheus**: http://lab.m4s8.dev:9090 (internal only)

### Key Metrics

1. **Application Metrics**
   - Request rate and latency
   - Error rate
   - Active backtests
   - WebSocket connections

2. **System Metrics**
   - CPU and memory usage
   - Disk usage
   - Network I/O

3. **Database Metrics**
   - Connection pool usage
   - Query performance
   - Replication lag

### Alerts

Configured alerts:
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Error rate > 5%
- Service down > 2 minutes

## Backup and Recovery

### Automated Backups

Backups run daily at 2 AM via cron:
```bash
# View backup schedule
crontab -l

# Manual backup
./scripts/backup.sh
```

### Backup Contents
- PostgreSQL database dump
- Redis data snapshot
- Application data
- Configuration files
- Docker volumes

### Restore Process

1. **List available backups**:
```bash
ls -la /backup/strategy-lab/manifest_*.json
```

2. **Restore from local backup**:
```bash
./scripts/restore.sh 20240115_020000
```

3. **Restore from cloud**:
```bash
./scripts/restore.sh 20240115_020000 --from-cloud
```

### Disaster Recovery

1. **Create new infrastructure**:
```bash
cd terraform
terraform apply
```

2. **Restore from backup**:
```bash
# On new server
./scripts/restore.sh <latest-backup> --from-cloud
```

## Troubleshooting

### Common Issues

1. **Service won't start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service>

# Check disk space
df -h

# Check memory
free -h
```

2. **Database connection issues**
```bash
# Test connection
docker exec -it strategy-lab-postgres psql -U postgres -d strategy_lab

# Check firewall rules
docker exec -it strategy-lab-backend nc -zv postgres 5432
```

3. **SSL certificate issues**
```bash
# Renew certificate
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Reload nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Debug Mode

Enable debug logging:
```bash
# Edit .env.prod
DEBUG=true
LOG_LEVEL=debug

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Performance Issues

1. **Check resource usage**:
```bash
docker stats
htop
iotop
```

2. **Database slow queries**:
```sql
-- Connect to database
docker exec -it strategy-lab-postgres psql -U postgres -d strategy_lab

-- Show slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## Security Considerations

### SSL/TLS
- Certificates auto-renew via Let's Encrypt
- TLS 1.2+ enforced
- HSTS enabled

### Firewall Rules
- SSH: Restricted to specific IPs (configure in Terraform)
- HTTP/HTTPS: Public access
- Database: VPC only
- Monitoring: Internal only

### Security Updates
```bash
# Manual updates
sudo apt update && sudo apt upgrade

# Automatic updates enabled for security patches
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Secrets Management
- Never commit secrets to Git
- Use environment variables
- Rotate secrets regularly
- Use strong passwords (min 16 characters)

### Monitoring Security
- Fail2ban configured for SSH protection
- Log monitoring for suspicious activity
- Regular security scans

## Maintenance

### Regular Tasks

**Daily**:
- Monitor alerts and metrics
- Check backup completion

**Weekly**:
- Review logs for errors
- Check disk usage
- Update dependencies

**Monthly**:
- Security updates
- Performance review
- Backup restoration test
- Certificate renewal check

### Scaling

**Vertical Scaling**:
```bash
# Update droplet size in terraform/variables.tf
droplet_size = "s-8vcpu-16gb"

# Apply changes
terraform apply
```

**Horizontal Scaling**:
- Implement Kubernetes deployment (see k8s/ directory)
- Use load balancer for multiple instances
- Configure database read replicas

## Support

For issues or questions:
1. Check application logs
2. Review monitoring dashboards
3. Consult error messages
4. Contact: admin@m4s8.dev
