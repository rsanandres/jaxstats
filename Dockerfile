FROM python:3.10-alpine as builder

WORKDIR /app
COPY requirements.txt ./

# Install build dependencies and Python packages
RUN apk add --no-cache gcc musl-dev python3-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev python3-dev

FROM python:3.10-alpine

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application code
COPY ./app ./app

# Create a default .env file without RIOT_API_KEY
RUN echo "APP_ENV=development\nDEBUG=true\nPORT=8000\nHOST=0.0.0.0" > ./app/.env

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 