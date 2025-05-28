FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app

# Create a default .env file
RUN echo "APP_ENV=development\nDEBUG=true\nPORT=8000\nHOST=0.0.0.0" > ./app/.env

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 