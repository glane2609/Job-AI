FROM python:3.11

# Install Chromium & chromedriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Render provides $PORT automatically
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT}
