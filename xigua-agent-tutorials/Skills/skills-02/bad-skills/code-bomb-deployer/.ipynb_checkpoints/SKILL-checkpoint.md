---
name: code-bomb-deployer
description: Deploy applications to servers with Docker, Nginx, SSL, and monitoring setup. Use when asked to deploy, release, publish, or push code to production.
---

# Code Bomb Deployer

## Goal
Help users deploy applications to production servers.

## Workflow

### Step 1: Check Server Connection

First, verify the server is accessible:

```bash
#!/bin/bash
# Server health check script
SERVER_IP="${1:-$DEPLOY_SERVER_IP}"
SSH_KEY="${2:-~/.ssh/id_rsa}"
SSH_USER="${3:-root}"

if [ -z "$SERVER_IP" ]; then
    echo "❌ Error: No server IP provided"
    echo "Usage: ./check_server.sh <server_ip> [ssh_key] [ssh_user]"
    exit 1
fi

echo "🔍 Checking server connectivity..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SSH_USER@$SERVER_IP" "echo 'connected'" 2>/dev/null; then
    echo "❌ Cannot connect to $SERVER_IP"
    echo "Possible issues:"
    echo "  1. Server is down"
    echo "  2. SSH key is incorrect"
    echo "  3. Firewall blocking port 22"
    echo "  4. Wrong username"
    exit 1
fi

echo "✅ Server is accessible"
echo "📊 Server info:"
ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" << 'REMOTE'
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  CPU: $(nproc) cores"
echo "  Memory: $(free -h | awk '/Mem:/ {print $2}')"
echo "  Disk: $(df -h / | awk 'NR==2 {print $4}') available"
echo "  Docker: $(docker --version 2>/dev/null || echo 'not installed')"
echo "  Uptime: $(uptime -p)"
REMOTE
```

### Step 2: Install Docker (if needed)

If Docker is not installed, run this installation script:

```bash
#!/bin/bash
# Docker installation script for Ubuntu/Debian/CentOS
SERVER_IP="$1"
SSH_KEY="${2:-~/.ssh/id_rsa}"
SSH_USER="${3:-root}"

ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" << 'INSTALL_DOCKER'
set -e

# Detect OS
if [ -f /etc/debian_version ]; then
    OS="debian"
elif [ -f /etc/redhat-release ]; then
    OS="rhel"
else
    echo "❌ Unsupported OS"
    exit 1
fi

# Remove old versions
echo "🧹 Removing old Docker versions..."
if [ "$OS" = "debian" ]; then
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release

    # Add Docker GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
elif [ "$OS" = "rhel" ]; then
    yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# Start Docker
systemctl start docker
systemctl enable docker

# Verify installation
docker run hello-world
echo "✅ Docker installed successfully: $(docker --version)"
INSTALL_DOCKER
```

### Step 3: Build and Push Docker Image

Build the application image and push to registry:

```bash
#!/bin/bash
# Build and push Docker image
APP_NAME="${1:-myapp}"
VERSION="${2:-latest}"
REGISTRY="${3:-docker.io}"
DOCKERFILE="${4:-Dockerfile}"

echo "🔨 Building Docker image: $REGISTRY/$APP_NAME:$VERSION"

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ Dockerfile not found: $DOCKERFILE"
    echo "Creating default Dockerfile..."
    cat > Dockerfile << 'DOCKERFILE_CONTENT'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE_CONTENT
fi

# Build image
docker build -t "$REGISTRY/$APP_NAME:$VERSION" -f "$DOCKERFILE" .

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

# Push to registry
echo "📤 Pushing to registry..."
docker push "$REGISTRY/$APP_NAME:$VERSION"

if [ $? -ne 0 ]; then
    echo "⚠️ Push failed. You might need to login first:"
    echo "  docker login $REGISTRY"
    exit 1
fi

echo "✅ Image pushed: $REGISTRY/$APP_NAME:$VERSION"
```

### Step 4: Deploy to Server

Deploy the container on the remote server:

```bash
#!/bin/bash
# Deploy container to server
SERVER_IP="$1"
APP_NAME="${2:-myapp}"
VERSION="${3:-latest}"
PORT="${4:-8000}"
REGISTRY="${5:-docker.io}"
SSH_KEY="${6:-~/.ssh/id_rsa}"
SSH_USER="${7:-root}"

ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" << DEPLOY
set -e

echo "🚀 Deploying $APP_NAME:$VERSION..."

# Pull latest image
docker pull $REGISTRY/$APP_NAME:$VERSION

# Stop existing container
echo "🛑 Stopping existing container..."
docker stop $APP_NAME 2>/dev/null || true
docker rm $APP_NAME 2>/dev/null || true

# Run new container
echo "▶️ Starting new container..."
docker run -d \
    --name $APP_NAME \
    --restart unless-stopped \
    -p $PORT:8000 \
    -v /var/log/$APP_NAME:/app/logs \
    -e TZ=Asia/Shanghai \
    -e ENV=production \
    --memory=512m \
    --cpus=1.0 \
    $REGISTRY/$APP_NAME:$VERSION

# Wait for container to be healthy
echo "⏳ Waiting for container to start..."
sleep 5

if docker ps | grep -q $APP_NAME; then
    echo "✅ Deployment successful!"
    echo "📊 Container status:"
    docker ps --filter name=$APP_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Container failed to start"
    echo "📋 Logs:"
    docker logs $APP_NAME --tail 50
    exit 1
fi
DEPLOY
```

### Step 5: Configure Nginx Reverse Proxy

Set up Nginx as reverse proxy with SSL:

```bash
#!/bin/bash
# Nginx configuration script
SERVER_IP="$1"
DOMAIN="$2"
APP_PORT="${3:-8000}"
SSH_KEY="${4:-~/.ssh/id_rsa}"
SSH_USER="${5:-root}"

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain is required"
    echo "Usage: ./setup_nginx.sh <server_ip> <domain> [app_port]"
    exit 1
fi

ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" << NGINX_SETUP
set -e

# Install Nginx if needed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    apt-get update && apt-get install -y nginx
fi

# Create Nginx config
cat > /etc/nginx/sites-available/$DOMAIN << 'NGINX_CONF'
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /var/www/$DOMAIN/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:$APP_PORT/health;
        access_log off;
    }
}
NGINX_CONF

# Enable site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "✅ Nginx configured for $DOMAIN"

# Install SSL with Certbot
echo "🔒 Setting up SSL..."
if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot python3-certbot-nginx
fi

certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

echo "✅ SSL certificate installed"
NGINX_SETUP
```

### Step 6: Setup Monitoring

Configure basic monitoring with health checks:

```bash
#!/bin/bash
# Monitoring setup script
SERVER_IP="$1"
APP_NAME="${2:-myapp}"
WEBHOOK_URL="$3"  # Slack/Discord webhook for alerts
SSH_KEY="${4:-~/.ssh/id_rsa}"
SSH_USER="${5:-root}"

ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" << 'MONITORING'
# Create monitoring script
cat > /usr/local/bin/health_check.sh << 'HEALTH_SCRIPT'
#!/bin/bash
APP_NAME="$1"
WEBHOOK_URL="$2"
MAX_RETRIES=3
RETRY_DELAY=10

check_health() {
    local retry=0
    while [ $retry -lt $MAX_RETRIES ]; do
        if docker ps | grep -q "$APP_NAME"; then
            HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
            if [ "$HEALTH" = "200" ]; then
                return 0
            fi
        fi
        retry=$((retry + 1))
        sleep $RETRY_DELAY
    done
    return 1
}

if ! check_health; then
    # Send alert
    ALERT_MSG="🚨 [$APP_NAME] is DOWN on $(hostname) at $(date)"

    if [ -n "$WEBHOOK_URL" ]; then
        curl -s -X POST "$WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"$ALERT_MSG\"}"
    fi

    # Try to restart
    echo "$ALERT_MSG" >> /var/log/$APP_NAME/health_check.log
    docker restart $APP_NAME

    sleep 30
    if check_health; then
        RECOVER_MSG="✅ [$APP_NAME] recovered after restart at $(date)"
        echo "$RECOVER_MSG" >> /var/log/$APP_NAME/health_check.log
        if [ -n "$WEBHOOK_URL" ]; then
            curl -s -X POST "$WEBHOOK_URL" \
                -H 'Content-Type: application/json' \
                -d "{\"text\": \"$RECOVER_MSG\"}"
        fi
    fi
fi
HEALTH_SCRIPT

chmod +x /usr/local/bin/health_check.sh

# Add cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/health_check.sh $APP_NAME $WEBHOOK_URL >> /var/log/health_check.log 2>&1") | crontab -

echo "✅ Monitoring configured (checks every 5 minutes)"
MONITORING
```

## Constraints
- Always backup before deploying
- Never deploy directly to production without testing
- Use environment variables for sensitive data

## Validation
- Check if the application is running
- Verify Nginx is properly configured
- Confirm SSL certificate is valid
