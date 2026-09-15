# CLAUDE.md

ПО для весов самообслуживания Rongta Aurora S2: FastAPI + Vue 3 (Composition API) +
Element Plus. Целевое устройство — Ubuntu 24.04 x86_64 в режиме киоска, экран 1920x1080.
Язык интерфейса — украинский (переключается в админке), язык кода и комментариев —
русский. Паспорт прибора — `docs/hardware/aurora-s2.md`.

## Команды

```bash
# Всё сразу: бэкенд с автоперезагрузкой и браузер с киоском (--admin — и админка)
cd backend && .venv/Scripts/python tools/dev.py

# Только бэкенд (Windows-пути; на Linux — .venv/bin/)
cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# Фронтенд
cd frontend && npm run dev          # киоск :5173/, админка :5173/admin.html
cd frontend && npm run build        # после сборки FastAPI сам отдаёт / и /admin
cd frontend && npm run typecheck    # vue-tsc; запускать перед сдачей изменений

# Образ прибора (симулятор, порт 8000); на прибор — docs/deploy.md
docker compose up --build
```

## Правила проекта — в скиллах

Решения и их причины разложены по скиллам в `.claude/skills/`. Открывайте тот, чью
область правите; в каждом объяснено не только «как», но и «почему так, а не иначе».

| Скилл | О чём |
| --- | --- |
| `hardware-hal` | Слой абстракции железа, метрология, протокол весовой платы |
| `kiosk-catalog` | Сетки, карточки, плашка, строка поиска, пейджер |
| `kiosk-motion` | Свайп-лента, переходы, спокойный режим карточек, заставка |
| `kiosk-input` | Клавиатура и цифровой блок, поиск по названию и коду |
| `kiosk-theme` | Темы и цветовые токены |
| `localization` | Тексты интерфейса и коды ошибок |
| `label-printing` | Растр этикетки и штрихкод |
| `device-settings` | `settings.json`, пути и конфигурация |
| `admin-ui` | Админка |
| `catalog-data` | БД, поиск, мягкое удаление, заливка каталога |
| `product-photos` | Снимки товаров: привязка, вес, загрузка на экран |
| `behaviour-logs` | Логи и замеры поведения: журнал операций, касания, ловушки |
| `deployment` | Docker-образ, compose прибора, install.sh, обновление |

Главное правило, которое стоит помнить всегда: код вне `backend/app/hal/` не обращается
к железу напрямую (подробности — в скилле `hardware-hal`).
