# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Récupérer l'exécutable uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Configuration de uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Création du user sécurisé
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Optimisation du cache : copie stricte des fichiers de dépendances
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copie du code source
COPY . /app

# Installation du projet local
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Ajout de l'environnement virtuel au PATH
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

# À remplacer dynamiquement par l'agent Antigravity
CMD ["python", "main.py"]
