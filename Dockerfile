# Образ прибора: собранный фронт и бэкенд в одном контейнере.
#
# Сборка фронта идёт в отдельной стадии на node, в готовый образ попадает только
# `dist`: на приборе нет ни node, ни npm, и ставить их ради сборки незачем. Бэкенд
# отдаёт фронт сам (см. `_mount_frontend` в app/main.py), поэтому nginx не нужен.
#
# Собирать образ на самом приборе не стоит — J6412 будет ставить зависимости минут
# десять. Собранный образ уезжает в реестр (см. .github/workflows/docker.yml), а на
# приборе делается только `docker compose pull`.

# ---- фронтенд --------------------------------------------------------------
FROM node:20-alpine AS web
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- прибор ----------------------------------------------------------------
FROM python:3.12-slim

# Шрифт с кириллицей для растра этикетки: `services/fonts.py` ищет DejaVu первым.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Пути повторяют раскладку репозитория: бэкенд ищет фронт в ../frontend/dist,
# выгрузку каталога — в ../docs/prod.xlsx, а данные держит в ./data.
WORKDIR /opt/s2l/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/tools ./tools
COPY docs/prod.xlsx /opt/s2l/docs/prod.xlsx
COPY --from=web /src/frontend/dist /opt/s2l/frontend/dist

# Служба не работает от root: ей нужны порт и два устройства, не больше. Группы
# dialout (20) и lp (7) совпадают с Ubuntu на приборе — через них выдаётся доступ
# к весовой плате и принтеру (см. deploy/docker/compose.yml, group_add).
RUN useradd --system --uid 1000 --create-home s2l \
    && mkdir -p data/labels data/photos \
    && chown -R s2l:s2l /opt/s2l
USER s2l

ENV S2L_HOST=0.0.0.0 S2L_PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
VOLUME ["/opt/s2l/backend/data"]

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
