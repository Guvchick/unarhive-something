FROM python:3.11-slim

LABEL maintainer="UnArchive Bot"
LABEL description="Telegram bot for archive extraction and media conversion"

# System deps: ffmpeg (video) + unrar (full RAR4/RAR5 support from non-free repo)
RUN echo "deb http://deb.debian.org/debian bookworm non-free" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        unrar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Runtime directories (overridden by volumes in compose)
RUN mkdir -p temp logs data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["python", "bot.py"]
