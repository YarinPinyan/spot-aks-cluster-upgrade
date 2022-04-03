FROM python:3.8-slim

# Create app dir
COPY src/requirements.txt ./

RUN pip install -r requirements.txt

COPY src /app

ENTRYPOINT ["python", "app/main.py"]