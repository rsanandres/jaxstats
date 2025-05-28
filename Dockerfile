FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt && pip list
COPY ./app ./app

# Create a default .env file without RIOT_API_KEY
RUN echo "APP_ENV=development\nDEBUG=true\nPORT=8000\nHOST=0.0.0.0" > ./app/.env

EXPOSE 8000
CMD ["sh", "-c", "echo 'Python path:' && python -c 'import sys; print(\"\\n\".join(sys.path))' && echo '\nInstalled packages:' && pip list && echo '\nStarting application...' && uvicorn app.main:app --host 0.0.0.0 --port 8000"] 