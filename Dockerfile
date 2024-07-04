FROM python:3.12.4-slim-bookworm
LABEL "org.opencontainers.image.source"="https://github.com/justalemon/Leek"
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
