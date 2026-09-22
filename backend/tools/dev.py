"""Запуск проекта на машине разработчика: бэкенд плюс браузер с киоском.

Поднимает uvicorn с автоперезагрузкой, ждёт, пока `/healthz` ответит, и
открывает киоск в браузере по умолчанию (`--admin` — ещё и админку). Ctrl+C
останавливает всё. На приборе не используется: там браузер поднимает
`s2l-kiosk.service`, а бэкенд — docker.

    cd backend && .venv/Scripts/python tools/dev.py            # киоск
    cd backend && .venv/Scripts/python tools/dev.py --admin    # киоск и админка
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:8000"


def healthy() -> bool:
    try:
        return urllib.request.urlopen(f"{URL}/healthz", timeout=1).status == 200
    except Exception:  # noqa: BLE001 — сервер ещё не поднялся, это нормально
        return False


def main() -> int:
    if healthy():
        print(f"бэкенд уже отвечает на {URL} — открываю браузер")
        server = None
    else:
        server = subprocess.Popen(
            # 0.0.0.0, а не localhost: выгрузку из 1С проверяют с другой машины.
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=BACKEND,
        )
        for _ in range(60):
            if healthy():
                break
            if server.poll() is not None:
                print("uvicorn завершился, не успев подняться", file=sys.stderr)
                return server.returncode or 1
            time.sleep(0.5)
        else:
            print("бэкенд не ответил за 30 секунд", file=sys.stderr)
            server.terminate()
            return 1

    webbrowser.open(f"{URL}/")
    if "--admin" in sys.argv:
        webbrowser.open(f"{URL}/admin")
    print(f"киоск: {URL}/   админка: {URL}/admin")

    if server is None:
        return 0
    try:
        return server.wait()
    except KeyboardInterrupt:
        server.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
