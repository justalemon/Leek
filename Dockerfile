FROM python:3.11.1-slim-bullseye
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "-m", "leek"]
