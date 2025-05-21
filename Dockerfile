# Dockerfile for Django + Gunicorn + WhiteNoise
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files into STATIC_ROOT (configured in settings.py)
RUN python manage.py collectstatic --noinput

# Expose application port
EXPOSE 8000

# Use Gunicorn to serve the Django app, WhiteNoise will handle static files
CMD ["gunicorn", "agent_chatbot.wsgi:application", "--bind", "0.0.0.0:8000"]