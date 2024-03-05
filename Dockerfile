FROM python:3.11.8-slim-bookworm
WORKDIR /app
COPY leek/ ./leek
COPY pyproject.toml .
COPY setup.py .
RUN <<EOF
python -m pip install -U pip
pip install .
EOF
WORKDIR /
RUN rm -r /app
CMD ["python", "-m", "leek"]
