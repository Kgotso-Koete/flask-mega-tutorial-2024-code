FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    python3-dev \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP=microblog.py
ENV FLASK_ENV=production

# Create translations directory if it doesn't exist
RUN mkdir -p app/translations

# Skip translation compilation during build
# It will be handled at runtime if needed
# To compile translations, run: docker-compose exec web flask translate compile

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
