# J-Doc Chat Permanent Deployment Instructions

This guide provides detailed steps to deploy your J-Doc Chat application permanently using Docker Compose and Nginx with SSL.

## 1. Prerequisites

Before you begin, ensure you have the following:

- A Linux server (e.g., Ubuntu 20.04+) with root access or `sudo` privileges.
- Docker and Docker Compose installed on your server.
- A registered domain name (e.g., `j-doc-chat.com`) and a subdomain for the API (e.g., `api.j-doc-chat.com`).
- An OpenAI API Key.

## 2. Server Setup

### 2.1 Update System and Install Docker

Connect to your server via SSH and run the following commands:

```bash
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER # Add your user to the docker group
newgrp docker # Apply group changes immediately

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx and Certbot
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 2.2 Clone the J-Doc Chat Repository

Navigate to a suitable directory (e.g., `/opt/`) and clone your application:

```bash
sudo mkdir -p /opt/j-doc-chat
cd /opt/j-doc-chat

# Assuming you have your repository hosted, replace with your actual clone command
git clone <your-repository-url> .

# If you received a zip file, upload it to /opt/j-doc-chat and unzip it:
# sudo apt install unzip
# sudo unzip j-doc-chat-complete.zip
```

### 2.3 Configure Environment Variables

Copy the example environment file and edit it with your actual values:

```bash
cp .env.example .env
sudo nano .env
```

Edit the `.env` file to include your OpenAI API key and set the `CORS_ORIGINS` and `VITE_API_URL` to your domain names:

```ini
# .env file content
OPENAI_API_KEY=sk-your-openai-api-key-here
CHROMA_PERSIST_DIR=/app/chroma
MAX_FILE_SIZE_MB=20
CORS_ORIGINS=https://j-doc-chat.com,https://api.j-doc-chat.com
VITE_API_URL=https://api.j-doc-chat.com
```

## 3. SSL Certificate Setup with Certbot

Obtain SSL certificates for your domain and API subdomain using Certbot. This will automatically configure Nginx.

```bash
sudo certbot --nginx -d j-doc-chat.com -d www.j-doc-chat.com -d api.j-doc-chat.com
```

Follow the prompts. Certbot will ask for your email and agree to terms of service. It will also offer to redirect HTTP traffic to HTTPS, which you should accept.

**Important**: Certbot will create an Nginx configuration file. You will need to replace this with the provided `nginx.prod.conf` file in the next step.

## 4. Nginx Configuration

Replace the default Nginx configuration with the provided production configuration. This file is located at `j-doc-chat/nginx.prod.conf`.

```bash
sudo rm /etc/nginx/sites-enabled/default # Remove default Nginx config
sudo cp /opt/j-doc-chat/nginx.prod.conf /etc/nginx/nginx.conf

# Create a directory for SSL certificates and copy them
sudo mkdir -p /opt/j-doc-chat/ssl
sudo cp -r /etc/letsencrypt/live/j-doc-chat.com/* /opt/j-doc-chat/ssl/

# Test Nginx configuration and restart
sudo nginx -t
sudo systemctl restart nginx
```

## 5. Deploy with Docker Compose

Now, build and run your Docker containers using the production Docker Compose file:

```bash
cd /opt/j-doc-chat
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

This will build the Docker images for your frontend and backend, and then start the services in detached mode.

## 6. Verify Deployment

Open your web browser and navigate to `https://j-doc-chat.com` (or your chosen domain). You should see the J-Doc Chat application.

You can also check the status of your Docker containers:

```bash
docker-compose -f docker-compose.prod.yml ps
```

And view logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

## 7. Ongoing Maintenance

### Auto-renewal of SSL Certificates

Certbot automatically sets up a cron job for certificate renewal. You can test it:

```bash
sudo certbot renew --dry-run
```

### Application Updates

To update your application to the latest version:

```bash
cd /opt/j-doc-chat
git pull origin main # Or download and unzip the new version
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
docker image prune -f # Clean up old images
```

### Backups

Regularly back up your `uploads` and `chroma` volumes. You can use the `backup.sh` script provided in the `DEPLOYMENT.md` file for guidance.

## Troubleshooting

Refer to the `DEPLOYMENT.md` file in the project root for detailed troubleshooting steps.

---

**J-Doc Chat - Enjoy chatting with your documents!**

