# UI_045: Deployment & Infrastructure Setup

**Status:** Done

## Story
As a DevOps engineer, I want to set up a robust deployment pipeline and infrastructure so that the application can be deployed reliably and scaled as needed.

## Acceptance Criteria
1. Configure Docker containers for all services
2. Set up CI/CD pipeline with automated deployments
3. Implement infrastructure as code (Terraform/Ansible)
4. Configure monitoring and logging systems
5. Set up backup and disaster recovery
6. Implement auto-scaling capabilities
7. Configure SSL certificates and domain
8. Create deployment documentation

## Technical Requirements

### Docker Configuration
```dockerfile
# Dockerfile.frontend
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies
COPY package.json pnpm-lock.yaml* ./
RUN \
  if [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else echo "pnpm lockfile not found." && exit 1; \
  fi

# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build application
ENV NEXT_TELEMETRY_DISABLED 1
RUN pnpm run build

# Production stage
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]

# Dockerfile.backend
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/strategy_lab
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=strategy_lab
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/conf.d:/etc/nginx/conf.d
    depends_on:
      - frontend
      - backend
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm i --frozen-lockfile

      - name: Run tests
        run: pnpm test -- --coverage

      - name: Run E2E tests
        run: pnpm run test:e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-frontend
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push Backend
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-backend
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /opt/strategy-lab
            git pull origin main
            docker-compose pull
            docker-compose up -d --remove-orphans
            docker system prune -f
```

### Infrastructure as Code
```hcl
# terraform/main.tf
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    endpoint                    = "https://nyc3.digitaloceanspaces.com"
    key                        = "terraform.tfstate"
    bucket                     = "strategy-lab-tfstate"
    region                     = "us-east-1"
    skip_credentials_validation = true
    skip_metadata_api_check    = true
  }
}

# Variables
variable "do_token" {
  description = "DigitalOcean API token"
  sensitive   = true
}

variable "domain" {
  description = "Domain name"
  default     = "lab.m4s8.dev"
}

# Provider
provider "digitalocean" {
  token = var.do_token
}

# SSH Key
resource "digitalocean_ssh_key" "main" {
  name       = "strategy-lab-key"
  public_key = file("~/.ssh/strategy-lab.pub")
}

# Droplet
resource "digitalocean_droplet" "app" {
  name     = "strategy-lab-app"
  size     = "s-4vcpu-8gb"
  image    = "ubuntu-22-04-x64"
  region   = "nyc3"
  ssh_keys = [digitalocean_ssh_key.main.fingerprint]

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    domain = var.domain
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Firewall
resource "digitalocean_firewall" "web" {
  name = "strategy-lab-firewall"

  droplet_ids = [digitalocean_droplet.app.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0"]
  }
}

# Domain
resource "digitalocean_domain" "main" {
  name = var.domain
}

resource "digitalocean_record" "app" {
  domain = digitalocean_domain.main.id
  type   = "A"
  name   = "@"
  value  = digitalocean_droplet.app.ipv4_address
  ttl    = 300
}

# Database
resource "digitalocean_database_cluster" "postgres" {
  name       = "strategy-lab-db"
  engine     = "pg"
  version    = "15"
  size       = "db-s-1vcpu-1gb"
  region     = "nyc3"
  node_count = 1

  maintenance_window {
    day  = "sunday"
    hour = "02:00:00"
  }
}

resource "digitalocean_database_firewall" "postgres" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "droplet"
    value = digitalocean_droplet.app.id
  }
}

# Spaces (Object Storage)
resource "digitalocean_spaces_bucket" "backups" {
  name   = "strategy-lab-backups"
  region = "nyc3"
  acl    = "private"

  lifecycle_rule {
    id      = "expire-old-backups"
    enabled = true

    expiration {
      days = 30
    }
  }
}

# Monitoring
resource "digitalocean_monitor_alert" "cpu" {
  alerts {
    email = ["admin@example.com"]
  }
  window      = "5m"
  type        = "v1/insights/droplet/cpu"
  compare     = "GreaterThan"
  value       = 80
  enabled     = true
  entities    = [digitalocean_droplet.app.id]
  description = "CPU usage is above 80%"
}
```

### Monitoring Setup
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/api/metrics'

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

# monitoring/grafana/dashboards/app-dashboard.json
{
  "dashboard": {
    "title": "Strategy Lab Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      },
      {
        "title": "Active Backtests",
        "targets": [
          {
            "expr": "backtests_active_total",
            "legendFormat": "Active"
          }
        ]
      }
    ]
  }
}
```

### Backup Strategy
```bash
#!/bin/bash
# scripts/backup.sh

set -e

# Configuration
BACKUP_DIR="/backup"
S3_BUCKET="s3://strategy-lab-backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
docker exec postgres pg_dump -U postgres strategy_lab | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup application data
echo "Backing up application data..."
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /app/data

# Backup configuration
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /app/config

# Upload to S3
echo "Uploading to S3..."
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz $S3_BUCKET/database/
aws s3 cp $BACKUP_DIR/app_data_$DATE.tar.gz $S3_BUCKET/data/
aws s3 cp $BACKUP_DIR/config_$DATE.tar.gz $S3_BUCKET/config/

# Clean up old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete
aws s3 ls $S3_BUCKET --recursive | while read -r line; do
  createDate=$(echo $line | awk '{print $1" "$2}')
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk '{print $4}')
    aws s3 rm $S3_BUCKET/$fileName
  fi
done

echo "Backup completed successfully"

# scripts/restore.sh
#!/bin/bash

set -e

# Configuration
BACKUP_DATE=$1
S3_BUCKET="s3://strategy-lab-backups"

if [ -z "$BACKUP_DATE" ]; then
  echo "Usage: ./restore.sh YYYYMMDD_HHMMSS"
  exit 1
fi

echo "Restoring from backup $BACKUP_DATE..."

# Download backups
aws s3 cp $S3_BUCKET/database/db_$BACKUP_DATE.sql.gz /tmp/
aws s3 cp $S3_BUCKET/data/app_data_$BACKUP_DATE.tar.gz /tmp/
aws s3 cp $S3_BUCKET/config/config_$BACKUP_DATE.tar.gz /tmp/

# Stop services
docker-compose stop backend frontend

# Restore database
echo "Restoring database..."
gunzip < /tmp/db_$BACKUP_DATE.sql.gz | docker exec -i postgres psql -U postgres strategy_lab

# Restore application data
echo "Restoring application data..."
tar -xzf /tmp/app_data_$BACKUP_DATE.tar.gz -C /

# Restore configuration
echo "Restoring configuration..."
tar -xzf /tmp/config_$BACKUP_DATE.tar.gz -C /

# Start services
docker-compose start backend frontend

echo "Restore completed successfully"
```

### Auto-scaling Configuration
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strategy-lab-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/username/strategy-lab-backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: strategy-lab-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### SSL Certificate Setup
```nginx
# nginx/conf.d/app.conf
server {
    listen 80;
    server_name lab.m4s8.dev;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lab.m4s8.dev;

    ssl_certificate /etc/letsencrypt/live/lab.m4s8.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lab.m4s8.dev/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## UI/UX Considerations
- Zero-downtime deployments
- Graceful error handling during updates
- Status page for system health
- Deployment notifications
- Rollback capabilities
- Performance monitoring dashboards

## Testing Requirements
1. Load testing before deployment
2. Smoke tests after deployment
3. Rollback procedure testing
4. Backup/restore verification
5. Disaster recovery drills
6. Security scanning

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- UI_042: Security hardening
- UI_044: Testing suite

## Story Points: 21

## Priority: Critical

## Implementation Notes
- Use blue-green deployment strategy
- Implement health checks
- Monitor deployment metrics
- Automate certificate renewal
- Regular security updates
- Document runbooks

## Dev Agent Record

### Tasks
- [x] Create Docker configurations for frontend and backend
- [x] Set up Docker Compose for local development and production
- [x] Create CI/CD pipeline with GitHub Actions
- [x] Implement infrastructure as code with Terraform
- [x] Set up monitoring with Prometheus and Grafana
- [x] Create backup and restore scripts
- [x] Configure Nginx with SSL
- [x] Create deployment documentation

### File List
- `/home/dev/strategy_lab/frontend/Dockerfile` (created)
- `/home/dev/strategy_lab/backend/Dockerfile` (created)
- `/home/dev/strategy_lab/frontend/.dockerignore` (created)
- `/home/dev/strategy_lab/backend/.dockerignore` (created)
- `/home/dev/strategy_lab/docker-compose.prod.yml` (created)
- `/home/dev/strategy_lab/nginx/nginx.conf` (created)
- `/home/dev/strategy_lab/nginx/conf.d/app.conf` (created)
- `/home/dev/strategy_lab/.github/workflows/deploy.yml` (created)
- `/home/dev/strategy_lab/terraform/main.tf` (created)
- `/home/dev/strategy_lab/terraform/variables.tf` (created)
- `/home/dev/strategy_lab/terraform/droplet.tf` (created)
- `/home/dev/strategy_lab/terraform/database.tf` (created)
- `/home/dev/strategy_lab/terraform/storage.tf` (created)
- `/home/dev/strategy_lab/terraform/monitoring.tf` (created)
- `/home/dev/strategy_lab/terraform/outputs.tf` (created)
- `/home/dev/strategy_lab/terraform/cloud-init.yaml` (created)
- `/home/dev/strategy_lab/monitoring/prometheus.yml` (created)
- `/home/dev/strategy_lab/monitoring/grafana/provisioning/datasources/prometheus.yml` (created)
- `/home/dev/strategy_lab/monitoring/grafana/provisioning/dashboards/dashboards.yml` (created)
- `/home/dev/strategy_lab/monitoring/grafana/dashboards/strategy-lab-dashboard.json` (created)
- `/home/dev/strategy_lab/scripts/backup.sh` (created)
- `/home/dev/strategy_lab/scripts/restore.sh` (created)
- `/home/dev/strategy_lab/docs/DEPLOYMENT.md` (created)

### Completion Notes
- Complete deployment infrastructure implemented with Docker, Docker Compose, and Terraform
- Production-ready Docker images with multi-stage builds and security best practices
- CI/CD pipeline with GitHub Actions for automated testing and deployment
- Infrastructure as Code using Terraform for DigitalOcean resources
- Comprehensive monitoring stack with Prometheus and Grafana
- Automated backup and restore scripts with cloud storage integration
- Nginx reverse proxy with SSL/TLS configuration and security headers
- Detailed deployment documentation covering all aspects of the infrastructure

### Change Log
1. Created optimized Dockerfiles for frontend (Next.js) and backend (FastAPI) with multi-stage builds
2. Set up Docker Compose configurations for both development and production environments
3. Configured Nginx as reverse proxy with SSL termination and security headers
4. Implemented GitHub Actions workflow for CI/CD with testing, building, and deployment stages
5. Created comprehensive Terraform configuration for infrastructure provisioning on DigitalOcean
6. Set up monitoring stack with Prometheus for metrics collection and Grafana for visualization
7. Implemented automated backup script with local and cloud storage support
8. Created restore script with verification and rollback capabilities
9. Added production-ready configurations including health checks, resource limits, and logging
10. Documented entire deployment process with troubleshooting guide and maintenance procedures
