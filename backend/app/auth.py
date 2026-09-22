"""Пароль на админку.

Прибор смотрит в интернет через туннель Cloudflare, и админка с настройками,
каталогом и чисткой базы торчит наружу вместе с ним. Обычная HTTP-авторизация
(Basic) выбрана за то, что ей не нужен ни фронтенд, ни сессии: браузер сам
спрашивает логин и пароль и сам подставляет их в каждый запрос админки —
включая XHR к API с той же страницы. Токен 1С и киоск она не трогает.

Пароль задаётся в `.env` (`S2L_ADMIN_PASSWORD`); пустой — админка без пароля,
это режим разработки, и при старте об этом пишется предупреждение.
"""
from __future__ import annotations

import base64
import binascii
import logging
import secrets

from fastapi import Request, Response

from .config import get_settings

log = logging.getLogger("s2l")

# Что киоск делает сам, без оператора: печать и работа с платформой. Всё
# остальное, что меняет состояние прибора, — дело админки. Приём из 1С
# защищён своим токеном (`api/import_1c.py`) и сюда не входит.
KIOSK_WRITES = ("/api/print", "/api/scale/tare", "/api/scale/zero")
# Чтение, которого киоску не нужно, а наружу отдавать незачем: журнал продаж и
# растры напечатанных этикеток.
PRIVATE_READS = ("/api/transactions", "/labels/")


def needs_auth(request: Request) -> bool:
    if not get_settings().admin_password:
        return False
    path = request.url.path
    if path == "/admin" or path.startswith("/admin/") or path == "/admin.html":
        return True
    if path.startswith(PRIVATE_READS):
        return True
    if path.startswith("/api/catalog/1c-import"):
        return False
    if path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
        return not path.startswith(KIOSK_WRITES)
    return False


def authorized(request: Request) -> bool:
    settings = get_settings()
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        raw = base64.b64decode(header[6:], validate=True).decode("utf-8")
    except (ValueError, binascii.Error):
        return False
    user, _, password = raw.partition(":")
    # Сравнение постоянного времени: по длительности ответа пароль не подобрать.
    return secrets.compare_digest(user, settings.admin_user) and secrets.compare_digest(
        password, settings.admin_password
    )


def challenge() -> Response:
    return Response(
        "Потрібен пароль адміністратора",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Aurora S2L admin", charset="UTF-8"'},
    )


def warn_if_open() -> None:
    if not get_settings().admin_password:
        log.warning("Админка без пароля: задайте S2L_ADMIN_PASSWORD в .env перед выходом в интернет")
