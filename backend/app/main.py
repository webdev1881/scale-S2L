from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import catalog, device
from .config import BASE_DIR, LABELS_DIR, get_settings
from .db import SessionLocal, init_db
from .hal.registry import build_devices, get_devices, set_devices
from .seed import seed_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("s2l")

FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    with SessionLocal() as db:
        added = seed_if_empty(db)
        if added:
            log.info("Загружен демо-каталог: %s позиций", added)

    devices = build_devices(settings)
    set_devices(devices)
    await devices.scale.start()
    await devices.printer.start()
    log.info("HAL: %s | весы: %s | принтер: %s", settings.hal_backend,
             devices.scale.status().kind, devices.printer.status().kind)
    try:
        yield
    finally:
        await devices.scale.stop()
        await devices.printer.stop()


app = FastAPI(title="Aurora S2L", version="0.1.0", lifespan=lifespan)

# Vite dev-сервер живёт на другом порту; в проде фронт отдаётся этим же приложением.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(device.router)
app.mount("/labels", StaticFiles(directory=LABELS_DIR), name="labels")


@app.get("/healthz")
def healthz() -> JSONResponse:
    try:
        devices = get_devices()
        ok = devices.scale.status().online
        return JSONResponse({"status": "ok" if ok else "degraded", "backend": devices.backend})
    except RuntimeError:
        return JSONResponse({"status": "starting"}, status_code=503)


def _mount_frontend() -> None:
    """Собранный фронт отдаётся тем же процессом: на киоске не нужен отдельный nginx."""
    if not FRONTEND_DIST.exists():
        log.warning("Сборка фронта не найдена (%s) — работаем как чистое API", FRONTEND_DIST)
        return
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Без no-cache браузер держит старый index.html по эвристике и после обновления
    # киоск продолжает грузить предыдущую сборку. Файлы в /assets хешированы — их кэш безопасен.
    NO_CACHE = {"Cache-Control": "no-cache"}

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/{path:path}", include_in_schema=False)
    def admin_spa(path: str = "") -> FileResponse:
        return FileResponse(FRONTEND_DIST / "admin.html", headers=NO_CACHE)

    @app.get("/", include_in_schema=False)
    @app.get("/{path:path}", include_in_schema=False)
    def kiosk_spa(path: str = "") -> FileResponse:
        candidate = FRONTEND_DIST / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html", headers=NO_CACHE)


_mount_frontend()
