# Разворачивание на новых весах

Прибор — Rongta Aurora S2 с Ubuntu 24.04. Всё ПО живёт в одном docker-образе;
на приборе нужны только docker, chromium и каталог `/opt/s2l` с тремя вещами:
`compose.yml`, `.env` и `data/`.

## Быстрый путь: клон с работающего прибора

Самый короткий способ получить такие же весы — скопировать с готовых `data/`:
там настройки (`settings.json`), каталог с ценами (`s2l.db`) и журнал операций.

1. На **готовом** приборе заберите каталог данных:

   ```bash
   sudo tar -C /opt/s2l -czf s2l-data.tgz data
   ```

2. На **новом** приборе, свежая Ubuntu 24.04, есть сеть:

   ```bash
   git clone https://github.com/webdev1881/scale-S2L.git
   tar -xzf s2l-data.tgz            # появится ./data
   sudo scale-S2L/deploy/docker/install.sh ./data
   ```

3. Проверьте `/opt/s2l/.env` — порт весов и принтер (см. ниже) — и перезагрузите:

   ```bash
   sudo reboot
   ```

После загрузки на экране киоск. Админка — `http://<адрес-прибора>:8000/admin`.

Журнал операций в клоне остаётся от исходного прибора. Если он не нужен, перед
копированием очистите таблицу или просто не берите `s2l.db` — каталог тогда
придётся залить выгрузкой (следующий раздел).

## Чистый прибор: каталог из выгрузки

Если клонировать не с чего:

```bash
git clone https://github.com/webdev1881/scale-S2L.git
sudo scale-S2L/deploy/docker/install.sh
```

Контейнер поднимется с пустым каталогом (демо-товары на реальном железе не
заводятся). Каталог заливается из выгрузки товароучёта, которая уже лежит в образе
(`docs/prod.xlsx` на момент сборки), снимки — тоже:

```bash
cd /opt/s2l
docker compose exec s2l python tools/import_products.py                    # план
docker compose exec s2l python tools/import_products.py --apply            # залить
```

Цен в выгрузке нет: `--random-prices` ставит заглушки, настоящие цены — через
админку или будущую выгрузку с колонкой цены.

## Что настроить в `.env`

| переменная | что это | Aurora S2 |
| --- | --- | --- |
| `S2L_HAL_BACKEND` | `real` — железо, `fake` — симулятор | `real` |
| `S2L_SCALE_PORT` | порт весовой платы | `/dev/ttyS4` (или `/dev/s2l-scale` с udev) |
| `S2L_SCALE_BAUDRATE` | скорость | `19200` |
| `S2L_PRINTER_DEVICE` | принтер этикеток | `/dev/usb/lp0` (или `/dev/s2l-printer`) |
| `S2L_SCALE_*_G` | метрология: НПВ, деления, наименьшая навеска | как в примере |

Устройства должны существовать **до** запуска контейнера — иначе `docker compose
up` откажется стартовать. Для USB-переходников впишите `idVendor`/`idProduct` из
`lsusb` в `deploy/udev/99-s2l-devices.rules`, и имена станут постоянными.

## Обновление

Образ собирается на GitHub при каждом пуше в `main` и уезжает в
`ghcr.io/webdev1881/scale-s2l:latest`. На приборе:

```bash
cd /opt/s2l
docker compose pull && docker compose up -d
```

Данные в `data/` обновление не трогает. Откат на точный образ — по тегу с хешем
коммита: `image: ghcr.io/webdev1881/scale-s2l:<sha>` в `compose.yml`.

Открытая вкладка киоска после обновления продолжает работать на прежней сборке
фронта, пока её не перезагрузят — `sudo systemctl restart s2l-kiosk`.

## Проверка

```bash
cd /opt/s2l
docker compose ps                      # healthy?
docker compose logs -f --tail 50       # лог бэкенда: HAL, весы, принтер, запросы
curl -s http://127.0.0.1:8000/api/status   # состояние весов и принтера
```

Если в логе `HAL: real | весы: serial | принтер: usb_raw` — железо подхвачено.
`scale.no_link` в киоске — плата не отвечает на указанном порту: проверьте
`S2L_SCALE_PORT` и что устройство проброшено в контейнер (`docker compose config`
покажет итоговый список `devices`).

## Без реестра

Если у прибора нет доступа к GitHub, образ можно привезти файлом:

```bash
# на машине с доступом
docker pull ghcr.io/webdev1881/scale-s2l:latest
docker save ghcr.io/webdev1881/scale-s2l:latest | gzip > s2l-image.tgz
# на приборе
gunzip -c s2l-image.tgz | docker load
```

`install.sh` при этом всё равно попробует `docker compose pull` — ошибку можно
проигнорировать, образ уже на месте.

## Что где лежит на приборе

```
/opt/s2l/
  compose.yml     описание контейнера (из deploy/docker)
  .env            железо и метрология этого прибора
  data/
    settings.json настройки из админки
    s2l.db        каталог и журнал операций
    labels/       растры напечатанных этикеток
```

Репозиторий на приборе не нужен: он используется один раз, чтобы запустить
`install.sh`, и может быть удалён.
