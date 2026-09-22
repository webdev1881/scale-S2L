#!/usr/bin/env bash
# Разворачивание Aurora S2L на чистой Ubuntu 24.04 (прибор Rongta Aurora S2).
#
# Что делает:
#   1. ставит docker, chromium и cage (композитор на одно окно);
#   2. заводит пользователя s2l с доступом к порту, принтеру и экрану;
#   3. кладёт в /opt/s2l compose-файл, .env и каталог data/;
#   4. ставит udev-правила и службу киоска, включает автозапуск;
#   5. тянет образ и поднимает контейнер.
#
# Запуск (из каталога с этим скриптом, от root):
#   sudo ./install.sh                     # чистый прибор
#   sudo ./install.sh /путь/к/data        # клон: настройки и каталог с другого прибора
#
# Скрипт идемпотентен: повторный запуск ничего не ломает и только обновляет образ.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET=/opt/s2l
SEED_DATA="${1:-}"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[[ $EUID -eq 0 ]] || { echo "запускать от root: sudo $0" >&2; exit 1; }

say "Пакеты"
apt-get update
apt-get install -y --no-install-recommends docker.io docker-compose-v2 chromium cage
systemctl enable --now docker

say "Пользователь s2l"
if ! id s2l >/dev/null 2>&1; then
    # UID 1000 согласован с s2l-kiosk.service (XDG_RUNTIME_DIR=/run/user/1000)
    useradd --create-home --uid 1000 --shell /usr/sbin/nologin s2l || useradd --create-home --shell /usr/sbin/nologin s2l
fi
# dialout — порт весов, lp — принтер, video/input/render — экран и тач под cage
usermod -aG dialout,lp,video,input,render,docker s2l

say "Файлы прибора в $TARGET"
mkdir -p "$TARGET/data/labels"
cp "$HERE/compose.yml" "$TARGET/compose.yml"
if [[ ! -f "$TARGET/.env" ]]; then
    cp "$HERE/.env.example" "$TARGET/.env"
    echo "   создан $TARGET/.env из примера — проверьте порт весов и принтер"
fi
if [[ -n "$SEED_DATA" ]]; then
    # Клон другого прибора: те же настройки, тот же каталог, тот же журнал.
    cp -a "$SEED_DATA"/. "$TARGET/data/"
    echo "   данные взяты из $SEED_DATA"
fi
chown -R s2l:s2l "$TARGET"

say "udev и киоск"
cp "$HERE/../udev/99-s2l-devices.rules" /etc/udev/rules.d/
udevadm control --reload-rules && udevadm trigger
cp "$HERE/../systemd/s2l-kiosk.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable s2l-kiosk.service

say "Образ и контейнер"
cd "$TARGET"
docker compose pull
docker compose up -d

say "Готово"
docker compose ps
echo
echo "Киоск: http://127.0.0.1:8000   Админка: http://127.0.0.1:8000/admin"
echo "Экран прибора поднимется после перезагрузки: sudo reboot"
