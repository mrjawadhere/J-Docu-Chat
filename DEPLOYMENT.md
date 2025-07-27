# DocuChat Deployment Guide

This guide covers various deployment strategies for DocuChat, from local development to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB minimum for application + document storage
- **Network**: Stable internet connection for OpenAI API

### Software Requirements

- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.11+ (for manual deployment)
- **Node.js**: 20+ (for manual deployment)
- **Git**: For cloning the repository

### API Keys

- **OpenAI API Key**: Required for embeddings and chat functionality
  - Sign up at [OpenAI Platform](https://platform.openai.com/)
  - Ensure sufficient credits for usage

## Local Development

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd docuchat

# Copy environment file
cp .env.example .env

# Edit .env with your OpenAI API key
nano .env

# Start with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Development Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key-here"
export CHROMA_PERSIST_DIR="./chroma"
export MAX_FILE_SIZE_MB=20

# Create necessary directories
mkdir -p uploads chroma

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Set environment variables
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
pnpm run dev --host
```

## Docker Deployment

### Using Docker Compose (Recommended)

#### Basic Deployment

```bash
# Clone and setup
git clone <repository-url>
cd docuchat
cp .env.example .env

# Edit environment variables
nano .env
```

```bash
# .env file content
OPENAI_API_KEY=sk-your-openai-api-key-here
CHROMA_PERSIST_DIR=/app/chroma
MAX_FILE_SIZE_MB=20
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
VITE_API_URL=http://localhost:8000
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update and restart
git pull
docker-compose build
docker-compose up -d
```

#### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHROMA_PERSIST_DIR=/app/chroma
      - MAX_FILE_SIZE_MB=20
      - CORS_ORIGINS=["https://yourdomain.com"]
    volumes:
      - uploads_data:/app/uploads
      - chroma_data:/app/chroma
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=https://api.yourdomain.com
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  uploads_data:
  chroma_data:
```

### Individual Container Deployment

#### Backend Container

```bash
# Build backend image
cd backend
docker build -t docuchat-backend .

# Run backend container
docker run -d \
  --name docuchat-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  -e CHROMA_PERSIST_DIR="/app/chroma" \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/chroma:/app/chroma \
  docuchat-backend
```

#### Frontend Container

```bash
# Build frontend image
cd frontend
docker build -t docuchat-frontend \
  --build-arg VITE_API_URL=http://localhost:8000 .

# Run frontend container
docker run -d \
  --name docuchat-frontend \
  -p 5173:80 \
  docuchat-frontend
```

## Production Deployment

### Server Setup

#### System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y nginx certbot python3-certbot-nginx htop
```

#### SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/docuchat
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

#### Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/docuchat
cd /opt/docuchat

# Clone repository
git clone <repository-url> .

# Setup environment
cp .env.example .env
nano .env
```

```bash
# Production .env
OPENAI_API_KEY=sk-your-production-api-key
CHROMA_PERSIST_DIR=/app/chroma
MAX_FILE_SIZE_MB=20
CORS_ORIGINS=["https://yourdomain.com"]
VITE_API_URL=https://api.yourdomain.com
```

```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Enable auto-start
sudo systemctl enable docker
```

#### Systemd Service (Alternative)

```ini
# /etc/systemd/system/docuchat.service
[Unit]
Description=DocuChat Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/docuchat
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable docuchat.service
sudo systemctl start docuchat.service
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

```yaml
# ecs-task-definition.json
{
  "family": "docuchat",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "docuchat-backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/docuchat-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/docuchat",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Using AWS App Runner

```yaml
# apprunner.yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building DocuChat"
run:
  runtime-version: latest
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env: PORT
  env:
    - name: OPENAI_API_KEY
      value: "your-api-key"
```

### Google Cloud Platform

#### Using Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/docuchat-backend', './backend']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/docuchat-backend']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'docuchat-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/docuchat-backend'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
```

### Digital Ocean

#### Using App Platform

```yaml
# .do/app.yaml
name: docuchat
services:
  - name: backend
    source_dir: /backend
    github:
      repo: your-username/docuchat
      branch: main
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: OPENAI_API_KEY
        value: your-api-key
        type: SECRET
    health_check:
      http_path: /api/v1/health
  - name: frontend
    source_dir: /frontend
    github:
      repo: your-username/docuchat
      branch: main
    build_command: pnpm build
    environment_slug: node-js
    instance_count: 1
    instance_size_slug: basic-xxs
```

## Monitoring & Maintenance

### Health Monitoring

#### Basic Health Checks

```bash
# Check application health
curl -f http://localhost:8000/api/v1/health

# Check detailed health
curl http://localhost:8000/api/v1/health/detailed

# Check container status
docker-compose ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Automated Monitoring Script

```bash
#!/bin/bash
# monitor.sh

BACKEND_URL="http://localhost:8000/api/v1/health"
FRONTEND_URL="http://localhost:5173"
SLACK_WEBHOOK="your-slack-webhook-url"

check_service() {
    local url=$1
    local service=$2
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $service is healthy"
        return 0
    else
        echo "❌ $service is down"
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 DocuChat $service is down!\"}" \
            "$SLACK_WEBHOOK"
        return 1
    fi
}

check_service "$BACKEND_URL" "Backend"
check_service "$FRONTEND_URL" "Frontend"

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️ Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEMORY_USAGE" -gt 80 ]; then
    echo "⚠️ Memory usage is at ${MEMORY_USAGE}%"
fi
```

```bash
# Add to crontab for regular monitoring
crontab -e
# Add: */5 * * * * /path/to/monitor.sh
```

### Log Management

#### Log Rotation

```bash
# /etc/logrotate.d/docuchat
/opt/docuchat/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f /opt/docuchat/docker-compose.prod.yml restart
    endscript
}
```

#### Centralized Logging

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        
  frontend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Backup Strategy

#### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/docuchat"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Chroma database
docker run --rm \
    -v docuchat_chroma_data:/source \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/chroma_$DATE.tar.gz" -C /source .

# Backup uploads
docker run --rm \
    -v docuchat_uploads_data:/source \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/uploads_$DATE.tar.gz" -C /source .

# Backup metadata
cp /opt/docuchat/backend/uploads/kb_metadata.json "$BACKUP_DIR/metadata_$DATE.json"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.json" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Automated Backups

```bash
# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/docuchat/backup.sh
```

### Updates and Maintenance

#### Application Updates

```bash
#!/bin/bash
# update.sh

cd /opt/docuchat

# Pull latest changes
git pull origin main

# Backup current state
./backup.sh

# Build new images
docker-compose -f docker-compose.prod.yml build

# Update services with zero downtime
docker-compose -f docker-compose.prod.yml up -d

# Clean up old images
docker image prune -f

echo "Update completed successfully"
```

#### Security Updates

```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Docker updates
sudo apt update docker-ce docker-ce-cli containerd.io

# SSL certificate renewal
sudo certbot renew --quiet

# Restart services if needed
sudo systemctl restart nginx
docker-compose -f docker-compose.prod.yml restart
```

## Troubleshooting

### Common Issues

#### Backend Issues

1. **OpenAI API Key Error**
   ```bash
   # Check API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   
   # Verify environment variable
   docker exec docuchat-backend env | grep OPENAI
   ```

2. **Database Connection Issues**
   ```bash
   # Check Chroma database
   docker exec docuchat-backend ls -la /app/chroma
   
   # Check permissions
   docker exec docuchat-backend ls -la /app/uploads
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Increase memory limits
   # Edit docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

#### Frontend Issues

1. **Build Failures**
   ```bash
   # Clear cache and rebuild
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache frontend
   ```

2. **API Connection Issues**
   ```bash
   # Check network connectivity
   docker exec docuchat-frontend curl -f http://backend:8000/api/v1/health
   
   # Verify environment variables
   docker exec docuchat-frontend env | grep VITE
   ```

#### Performance Issues

1. **Slow Response Times**
   ```bash
   # Check resource usage
   htop
   iotop
   
   # Monitor API response times
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health
   ```

2. **High Memory Usage**
   ```bash
   # Check for memory leaks
   docker stats --no-stream
   
   # Restart services
   docker-compose restart
   ```

### Debug Mode

#### Enable Debug Logging

```bash
# Backend debug mode
docker-compose -f docker-compose.yml \
    -f docker-compose.debug.yml up -d
```

```yaml
# docker-compose.debug.yml
version: '3.8'

services:
  backend:
    environment:
      - LOG_LEVEL=DEBUG
      - DEBUG=true
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

#### Access Container Shells

```bash
# Backend container
docker exec -it docuchat-backend bash

# Frontend container
docker exec -it docuchat-frontend sh

# Check logs in real-time
docker-compose logs -f --tail=100 backend
```

### Recovery Procedures

#### Disaster Recovery

1. **Complete System Failure**
   ```bash
   # Restore from backup
   cd /opt/docuchat
   
   # Stop services
   docker-compose down
   
   # Restore data
   docker run --rm \
       -v docuchat_chroma_data:/target \
       -v /opt/backups/docuchat:/backup \
       alpine tar xzf /backup/chroma_latest.tar.gz -C /target
   
   # Restart services
   docker-compose up -d
   ```

2. **Database Corruption**
   ```bash
   # Reset Chroma database
   docker-compose down
   docker volume rm docuchat_chroma_data
   docker-compose up -d
   
   # Re-upload documents through UI
   ```

This deployment guide provides comprehensive instructions for deploying DocuChat in various environments, from development to production. Choose the deployment method that best fits your infrastructure and requirements.

