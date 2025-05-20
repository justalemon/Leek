FROM python:3.13.3-slim-bookworm AS build
WORKDIR /src
COPY leek/ ./leek
COPY pyproject.toml .
COPY setup.py .
RUN <<EOF
python -m pip install -U pip build
python -m build
EOF

FROM python:3.13.3-slim-bookworm
LABEL "org.opencontainers.image.source"="https://github.com/justalemon/Leek"
WORKDIR /dist
COPY --from=build src/dist /dist
RUN <<EOF
python -m pip install -U pip
python -m pip install --find-links /dist/ leekbot[extras]
apt-get update
apt-get upgrade
python -m playwright install-deps
python -m playwright install firefox
python -m pip cache purge
apt-get clean
rm -rf /var/cache/apt/archives 
rm -rf /var/lib/apt/lists/*
rm -rf /dist
EOF

CMD ["python", "-m", "leek"]
