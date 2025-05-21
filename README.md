# Agentic Chatbot README

This document explains how to set up and run the Agentic Chatbot project from scratch, using Docker, Docker Compose, and ngrok for local webhooks.

---

## 🛠️ Prerequisites

* **Git** (to clone the repo)
* **Docker & Docker Compose** (v1.27+)
* **ngrok** (for exposing local webhooks)
* A **Twilio** account with WhatsApp/SMS sandbox enabled
* An **OpenAI** API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/agentic_chatbot.git
cd agentic_chatbot
```

---

## 2. Environment Variables

Create a `.env` file in the project root:

```ini
# Django
DJANGO_SECRET_KEY=your_django_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,https://abcd1234.ngrok.io

# Database (Postgres)
postgres_db=agentdb
postgres_user=agentuser
postgres_password=secret
postgres_host=db
postgres_port=5432

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# (Optional) Redis URL
REDIS_URL=redis://redis:6379/0
```

> **Note:** Make sure this file is **NOT** committed to version control.

---

## 3. Build and Run with Docker Compose

```bash
# 1. Build images and start services in detached mode
docker-compose up -d --build

# 2. (First time) Create database tables
docker-compose exec web python manage.py migrate

# 3. (Optional) Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# 4. Create a superuser
docker-compose exec web python manage.py createsuperuser
```

You should now have four containers running:

* `web` (Django + Gunicorn)
* `db` (PostgreSQL)
* `redis` (Celery broker)
* `worker` (Celery worker)

Check with:

```bash
docker-compose ps
```

---

## 4. Expose Locally with ngrok

```bash
# Start ngrok on port 8000
ngrok http 8000
```

Copy the **Forwarding HTTPS** URL (e.g. `https://abcd1234.ngrok.io`) and update your Twilio sandbox webhook to:

```
https://<your-tunnel>.ngrok.io/api/twilio/inbound/
```
---

## 5. Frequently Used Commands

### Tail logs for all services

```bash
docker-compose logs -f --tail=100
```

### Run Django shell

```bash
docker-compose exec web python manage.py shell
```

### Clear all data (Django flush)

```bash
docker-compose exec web python manage.py flush --no-input
```

### Delete & recreate migrations (catalog example)

```bash
docker-compose exec web python manage.py migrate catalog zero
docker-compose exec web python manage.py makemigrations catalog
docker-compose exec web python manage.py migrate catalog
```

### Demo
Video: https://1drv.ms/v/c/d97b815d286fe43f/EavLDz_aU1pDjRt8s1igfLMBJlfM-ivPjroPxRX-1eozcw?e=cThxeJ

