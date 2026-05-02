FROM python:3.11-slim

# Prevents .pyc files, enables stdout logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /

# Install system deps (needed for psycopg2 and sentence-transformers)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000


# WHY gunicorn not runserver?
# manage.py runserver is single-threaded, not built for concurrent requests.
# One slow request blocks all others.
# Gunicorn spawns multiple worker processes.
# workers=3 handles 3 concurrent requests simultaneously.
# Formula: workers = (2 * CPU cores) + 1
CMD ["gunicorn", "docqa.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]

