from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import auth
from .api import catalog, device, import_1c
from .config import BASE_DIR, FRONTEND_DIST, LABELS_DIR, PHOTOS_DIR, get_settings
from .db import SessionLocal, init_db
from .hal.registry import build_devices, get_devices, set_devices
from .seed import seed_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("s2l")



@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    auth.warn_if_open()
    # Демо-каталог — для разработки на симуляторе. На приборе пустая база должна
    # остаться пустой: её заполняют клоном с другого прибора или выгрузкой из
    # товароучёта, а демо-товары ссылаются на снимки, которых в сборке давно нет.
    if settings.hal_backend == "fake" and settings.seed_demo:
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



@app.middleware("http")
async def admin_auth(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Пароль на всё, чем управляет оператор; киоск и 1С проходят без него."""
    if auth.needs_auth(request) and not auth.authorized(request):
        return auth.challenge()
    return await call_next(request)


app.include_router(catalog.router)
app.include_router(device.router)
app.include_router(import_1c.router)
app.mount("/labels", StaticFiles(directory=LABELS_DIR), name="labels")


# `/health` — тот путь, по которому обработка 1С проверяет связь («Проверить связь»);
# `/healthz` — то же для docker HEALTHCHECK и tools/dev.py. Без явного маршрута
# запрос уходил в SPA-заглушку и отвечал 200 с index.html — «связь есть» при
# любом состоянии сервиса.
@app.get("/health")
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

    # Снимки товаров: сначала присланные на прибор (`data/photos`, выгрузка из 1С),
    # потом демо-набор из сборки. Имя файла — код товара, поэтому боевой снимок
    # перекрывает демо-снимок того же кода, не трогая сборку.
    @app.get("/products/{name}", include_in_schema=False)
    def product_photo(name: str) -> FileResponse:
        for folder in (PHOTOS_DIR, FRONTEND_DIST / "products"):
            candidate = folder / name
            if candidate.is_file():
                return FileResponse(candidate)
        raise HTTPException(404)

    @app.get("/", include_in_schema=False)
    @app.get("/{path:path}", include_in_schema=False)
    def kiosk_spa(path: str = "") -> FileResponse:
        candidate = FRONTEND_DIST / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html", headers=NO_CACHE)


_mount_frontend()
