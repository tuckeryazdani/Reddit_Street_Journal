FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# git is only needed for the optional website-publishing step.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first, so this layer is rebuilt only when they change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reddit_street_journal ./reddit_street_journal

# No credentials are baked into the image. Pass them at run time:
#   docker run --env-file .env -v "$PWD/state:/app/state" reddit-street-journal
# See the README for mounting the Google service-account key.
ENTRYPOINT ["python", "-m", "reddit_street_journal"]
