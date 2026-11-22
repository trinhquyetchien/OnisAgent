FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home app \
    && mkdir -p /app/data/local \
    && chown -R app:app /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app src ./src
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app models/checkpoints/kev/kev_intent_model.joblib ./models/checkpoints/kev/kev_intent_model.joblib

USER app

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn src.main:app --host \"$APP_HOST\" --port \"$APP_PORT\""]
