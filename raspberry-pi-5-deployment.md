# Flask Mega Tutorial – Raspberry Pi Deployment Guide

This guide explains how to deploy the Flask Mega Tutorial application to a Raspberry Pi running Raspberry Pi OS (Debian-based), including **PostgreSQL / SQLite**, **Nginx**, **Gunicorn**, **systemd**, and **Elasticsearch** for search functionality.

---

## 1. Prerequisites

- Raspberry Pi (Pi 4, Pi 5, or similar)
- Raspberry Pi OS Bookworm or Debian-based Linux
- Python 3.11+ installed
- Basic familiarity with the Linux command line

---

## 2. Clone the Application

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git microblog
cd microblog
```

---

## 3. Create a Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Database Setup

You can use SQLite (default) or PostgreSQL.

### SQLite (default)

No extra configuration is required.

### PostgreSQL (optional)

```bash
sudo apt install postgresql postgresql-contrib libpq-dev
sudo -u postgres createuser -s $USER
sudo -u postgres createdb microblog
```

Update your `.env` or `config.py`:

```
DATABASE_URL=postgresql://username:password@localhost/microblog
```

---

## 5. Install & Configure Elasticsearch

Download and extract Elasticsearch:

```bash
curl -L -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.8.0-linux-aarch64.tar.gz
tar -xzf elasticsearch-8.8.0-linux-aarch64.tar.gz
sudo mv elasticsearch-8.8.0 /opt/elasticsearch
```

Create a systemd service:

```bash
sudo nano /etc/systemd/system/elasticsearch.service
```

```ini
[Unit]
Description=Elasticsearch
After=network.target

[Service]
Type=simple
ExecStart=/opt/elasticsearch/bin/elasticsearch
User=pi
Restart=always
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
```

Test:

```bash
curl http://localhost:9200
```

---

## 6. Gunicorn Service

```bash
nano gunicorn_start.sh
```

```bash
#!/bin/bash
source /home/pi/microblog/.venv/bin/activate
exec gunicorn -b localhost:8000 -w 4 microblog:app
```

Make it executable:

```bash
chmod +x gunicorn_start.sh
```

Create systemd unit:

```bash
sudo nano /etc/systemd/system/microblog.service
```

```ini
[Unit]
Description=Gunicorn instance to serve microblog
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/microblog
Environment="PATH=/home/pi/microblog/.venv/bin"
ExecStart=/home/pi/microblog/gunicorn_start.sh

[Install]
WantedBy=multi-user.target
```

Enable & start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable microblog
sudo systemctl start microblog
```

---

## 7. Nginx Reverse Proxy

```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/microblog
```

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/microblog /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## 8. Environment Variables

Create `.env`:

```
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_password
ELASTICSEARCH_URL=http://localhost:9200
DATABASE_URL=sqlite:///app.db
```

**⚠️ Never commit `.env` to GitHub.**

---

## 9. Running Background Tasks

If using Flask-Migrate:

```bash
flask db upgrade
```

To index existing data in Elasticsearch:

```bash
flask reindex
```

---

## 10. Testing

Visit:

```
http://YOUR_DOMAIN_OR_IP
```

---

## 11. Troubleshooting

- **Gunicorn fails to start** → Check logs:

  ```bash
  journalctl -u microblog --no-pager
  ```

- **Elasticsearch not reachable** → Ensure service is running:

  ```bash
  sudo systemctl status elasticsearch
  ```

- **Email sending fails** → For Mailgun sandbox, only authorized recipients can receive mail unless you use a paid domain.

---
