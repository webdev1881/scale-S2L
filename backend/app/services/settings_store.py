"""Настройки устройства: JSON-файл рядом с базой, правится из админки без рестарта.

Файл, а не строка в БД: настройки прибора — это то, что переносят на новый
экземпляр, кладут в резервную копию и правят руками, когда админка недоступна.
Ради этого они не должны быть заперты внутри SQLite вместе с товарами.

Запись атомарна: сначала временный файл, затем замена. Иначе обесточивание
киоска в момент сохранения оставило бы обрезанный JSON, а с ним прибор
поднялся бы на значениях по умолчанию.
"""
from __future__ import annotations

import json
import os

from pydantic import BaseModel, Field

from .label_layout import LabelLayout

from ..config import SETTINGS_EXAMPLE_FILE, SETTINGS_FILE, SETTINGS_PRESETS_FILE


class DeviceSettings(BaseModel):
    # Язык киоска, админки и печатной этикетки. Переключается в настройках админки.
    language: str = Field(default="uk", pattern="^(uk|ru)$")
    # Тема киоска.
    theme: str = Field(default="light", pattern="^(dark|light)$")
    store_name: str = "Рулька"
    currency: str = "₴"
    # Печатающий узел Aurora S2 берёт ленту шириной не более 56 мм
    label_width_mm: float = Field(default=56, ge=20, le=56)
    label_height_mm: float = Field(default=40, ge=20, le=120)
    # Шаблон весового EAN-13: P — цифра PLU, W — цифра значения
    # Раскладка этикетки: что где напечатано. Собирается конструктором в админке,
    # печать и превью рисуются по ней одним и тем же рендером.
    label_layout: LabelLayout = Field(default_factory=LabelLayout)
    barcode_template: str = "22PPPPPWWWWW"
    # weight — в штрихкод уходит масса в граммах, total — сумма в копейках
    barcode_value: str = Field(default="weight", pattern="^(weight|total)$")
    # Наименьшая навеска прибора — 40 г, ниже взвешивать нельзя
    min_print_weight_g: int = 40
    require_stable: bool = True
    # Тара и обнуление в киоске: покупателю они не нужны, а случайное нажатие
    # посреди взвешивания портит покупку — но на прилавке с ручной тарой без них
    # не обойтись, поэтому решение оставлено оператору.
    kiosk_scale_buttons: bool = True
    # Уровень групп в каталоге. Прибор вешают на отдел, и тогда группы — лишний
    # экран между покупателем и карточкой: ассортимент отдела помещается в сетку
    # товаров. Там, где прибор один на весь зал, они по-прежнему нужны.
    kiosk_use_groups: bool = True
    # Код товара на карточке. Нужен там, где покупатель набирает его на цифровом
    # блоке; в отделе, где ищут глазами и пальцем, он только занимает угол снимка.
    kiosk_show_code: bool = True
    # «кг» и «шт» рядом с ценой. В отделе, где всё продаётся на вес, единица
    # одна на весь прибор и только удлиняет строку — из-за неё число приходится
    # ужимать. Там, где рядом лежат весовые и штучные, она нужна.
    kiosk_show_unit: bool = True
    # Кнопка «Код товару» в шапке, а с ней и весь набор кода. Нужна там, где
    # покупатель знает код и не хочет искать глазами; в отделе с полусотней позиций
    # она только занимает место рядом с ценой и стоимостью.
    kiosk_code_button: bool = True
    # Шапка весов только после первого контакта покупателя (касание или груз на
    # платформе). На стартовом экране нули и «0,00 грн» читаются как сломанный
    # прибор, а карточкам высота нужнее; выключают там, где показание должно быть
    # видно всегда — например, если весами пользуется и продавец.
    kiosk_header_on_contact: bool = True
    # Показывать только товары со снимком. Карточка без фото среди фотографий
    # выглядит как дыра; группа, в которой таких товаров не осталось, тоже уходит.
    kiosk_only_with_photo: bool = False
    # Товары со снимком — первыми. Слабее предыдущей настройки: та убирает
    # бесфотографенные вовсе, эта оставляет их, но уводит на последние страницы,
    # где покупатель их всё же найдёт.
    kiosk_photo_first: bool = False
    # Кнопки нижней панели. Поиск нужен не везде: в отделе с полусотней позиций
    # его не открывают ни разу, а место он занимает. Возврат ко всем товарам
    # выключают только там, где групп нет вовсе (`kiosk_use_groups`), — иначе из
    # группы не выйти, пока не сработает сброс по простою.
    kiosk_search_button: bool = True
    kiosk_back_button: bool = True
    # Какую долю нижней панели занимает поиск, проценты. Остальное достаётся
    # возврату. 50 — поровну; больше — поиск шире, как там, где им пользуются чаще.
    kiosk_search_width: int = Field(default=50, ge=20, le=80)
    # Плитка выбранного товара и ряд кнопок делят нижнюю панель поровну: одна
    # кнопка — половина экрана, две — по четверти. При обычной раскладке кнопки
    # забирали четыре пятых панели, а ширина плитки скакала вслед за длиной
    # надписи на кнопке.
    kiosk_actions_full_width: bool = False
    # Ширина экранной клавиатуры, проценты ширины каталога. Клавиша должна быть
    # заведомо крупнее пальца, но во всю ширину 1920 клавиатура растягивается так,
    # что до дальних букв тянутся рукой через весь экран.
    kiosk_keyboard_width: int = Field(default=60, ge=40, le=100)
    # Высота клавиатуры, проценты высоты экрана. 32 — то же, что было зашито на
    # экране прибора (340 px из 1080). Выше — крупнее клавиши, но каталог под
    # клавиатурой сжимается до одного ряда карточек.
    kiosk_keyboard_height: int = Field(default=32, ge=20, le=50)
    # Шрифт клавиш: ключ из списка во фронтенде (`shared/fonts.ts`), кегль в
    # пикселях и жирность. 23 px и жирный — то, что давала прежняя зашитая
    # `clamp(17px, 2vw, 23px)` на экране 1920.
    kiosk_keyboard_font: str = Field(default="system", pattern="^(system|arial|dejavu|ubuntu|mono|serif)$")
    kiosk_keyboard_font_size: int = Field(default=23, ge=14, le=40)
    kiosk_keyboard_bold: bool = True
    # Сколько процентов следующей карточки видно в жёлобе подсказки при листании.
    # 0 — жёлоба нет вовсе. Задаётся долей карточки, а не пикселями: карточка меняет
    # ширину вместе с числом колонок, и зашитый пиксель означал бы разную подсказку
    # на разных сетках.
    kiosk_peek_percent: int = Field(default=28, ge=0, le=60)
    # Сколько секунд бездействия до сброса экрана киоска
    kiosk_idle_reset_s: int = 45
    # Сколько секунд платформа должна простоять пустой после снятия товара, чтобы
    # киоск вернулся к началу — после печати или без неё. Полсекунды: платформа
    # качается, пока товар снимают, и мгновенный ноль поймал бы середину движения,
    # но дольше держать чужой выбор перед следующим покупателем незачем.
    kiosk_clear_hold_s: float = Field(default=0.5, ge=0.2, le=10)
    # Товар выбран, но не напечатан (нажали карточку с пустой платформой и ушли):
    # через столько секунд пустой платформы выбор снимается. 0 — не снимать, ждать
    # сброса по простою. Дольше, чем `kiosk_clear_hold_s`: до печати покупатель
    # ещё может положить товар, и торопить его незачем.
    kiosk_unselect_s: float = Field(default=5, ge=0, le=60)
    # Куда возвращается экран после печати (и после того, как товар сняли):
    # home — начальный экран; catalog — та же группа и страница, откуда нажали
    # товар; search — каталог с открытой клавиатурой поиска. Два последних — для
    # покупателя, который взвешивает несколько товаров подряд и не хочет каждый
    # раз идти с начала.
    kiosk_after_print: str = Field(default="home", pattern="^(home|catalog|search)$")
    # Штучному товару вес не нужен для цены, но касание его карточки при пустой
    # платформе печатало этикетку мгновенно — и экран уходил к началу. На весах
    # самообслуживания это ловушка: покупатель задел карточку, получил чужую
    # этикетку и не понял, что произошло. Поэтому и штучный требует, чтобы товар
    # лежал на платформе; наименьшая навеска при этом не проверяется — пучок
    # зелени легче её. Выключают там, где штучное кладут мимо платформы.
    kiosk_piece_needs_load: bool = True
    # Верхний предел показа этикетки: товар с платформы могут не снять вовсе, и без
    # предела экран остался бы занятым чужой покупкой навсегда.
    kiosk_label_max_s: float = Field(default=25, ge=5, le=120)
    # Реальный принтер прибора не отдаёт статус бумаги и крышки ни по одному
    # проверенному протоколу (USB-класс принтеров, ESC/POS, документированная
    # команда TSPL2 `<ESC>!?` — молчит на все запросы), поэтому единственный
    # доступный признак беды — покупатель раз за разом не забирает товар после
    # печати (см. `kiosk_label_max_s`). Один срыв ничего не значит — человек мог
    # просто отвлечься, — поэтому экран блокируется только после нескольких
    # подряд идущих срывов.
    kiosk_print_fail_streak: int = Field(default=2, ge=1, le=5)
    # Длительность стартовой заставки. 0 — не показывать её вовсе.
    splash_seconds: float = Field(default=3.0, ge=0, le=10)
    # Тестовый рубильник: показать блокирующий экран «Оновлення» без реального
    # разрыва связи с бэкендом — чтобы проверить его на приборе и в вёрстке.
    kiosk_force_updating: bool = False
    # Ручной рубильник для сотрудника: принтер не отдаёт статус бумаги и крышки
    # по USB (см. kiosk_print_fail_streak), поэтому единственный быстрый способ
    # сообщить о проблеме — увидеть её самому (мигает кнопка на принтере) и
    # включить блокировку вручную, не дожидаясь, пока это поймает эвристика по
    # срывам выдачи.
    kiosk_printer_alert: bool = False
    # Размер картинки на экране «Оновлення», проценты ширины/высоты экрана.
    # 0 — картинки нет вовсе, 100 — во весь экран; надпись и крутилка держатся
    # поверх неё своей панелью, поэтому размер картинки их не задевает.
    kiosk_updating_photo_scale: int = Field(default=52, ge=0, le=100)
    # Где на экране «Оновлення» держится надпись с крутилкой, доля высоты экрана
    # от верха. 0 — прижата к самому верху, 100 — к низу. Диапазон широкий
    # специально: под разные картинки и вкус оператора подходит разное место.
    kiosk_updating_text_position: int = Field(default=3, ge=0, le=100)
    # Крупные тосты вместо мелкого системного сообщения: «товар не найден»,
    # «нет бумаги», «заберите товар». Весы стоят дальше от покупателя, чем
    # монитор от разработчика — маленький текст в углу экрана там не видно.
    kiosk_toast_font_size: int = Field(default=32, ge=16, le=64)
    kiosk_toast_duration_s: float = Field(default=4.0, ge=1, le=15)
    kiosk_toast_color: str = Field(default="#d97706", pattern="^#[0-9a-fA-F]{6}$")
    kiosk_toast_pulse: bool = True

    # Масштабы подписей и доля высоты карточки под фотографию. Экран прибора стоит
    # от покупателя дальше, чем монитор от разработчика, и подходящий размер
    # подбирается на месте, а не подгоняется в вёрстке.
    ui_scale_weight: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_group_title: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_product_name: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_product_price: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_product_code: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_footer: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_photo_group: int = Field(default=60, ge=30, le=85)
    ui_photo_product: int = Field(default=60, ge=30, le=85)
    # Плашка с наименованием: доля ширины карточки и цвет заливки. Цвет текста
    # не настраивается — он выбирается по яркости плашки, иначе легко получить
    # светлую подпись на светлой заливке.
    # Высота плашки, а не ширина: длинное название переносится на вторую строку,
    # и если плашка рассчитана на одну, вторая обрезается посередине букв.
    # Масштаб снимка внутри карточки, проценты. 100 — как есть: фотография
    # заполняет отведённое место и кадрируется по краям. Больше — приближение,
    # меньше — снимок стоит целиком с полями, если товар снят издалека.
    # Отдельно для товара и для группы: карточка группы крупнее и берёт обложкой
    # снимок первого товара — то, что в мелкой карточке кадрировано в самый раз,
    # в крупной оказывается приближено.
    ui_photo_scale: int = Field(default=100, ge=60, le=160)
    ui_photo_scale_group: int = Field(default=100, ge=60, le=160)
    # Фон под снимком — виден по краям, если фото не занимает всё отведённое
    # место (масштаб ниже 100, прозрачный PNG, снимок ещё грузится). Белый по
    # умолчанию: карточка и так на белой панели, серая плашка под фото была
    # лишней границей внутри и той же карточки.
    ui_photo_bg: str = Field(default="#ffffff", pattern="^#[0-9a-fA-F]{6}$")
    ui_plate_height: int = Field(default=30, ge=1, le=60)
    # Основной цвет — всё, что относится к каталогу: плашки карточек, их рамки,
    # кнопка набора кода. Второстепенный — действия и итоги: печать, поиск,
    # возврат, стрелки, цена и сумма. Оба живут в настройках, потому что цвет
    # сети подбирают на месте, а не пересобирают ради него прошивку.
    ui_primary_color: str = Field(default="#1d2129", pattern="^#[0-9a-fA-F]{6}$")
    ui_secondary_color: str = Field(default="#1f7a4d", pattern="^#[0-9a-fA-F]{6}$")
    # Сетка каталога: столбцов x строк на страницу. Подбирается под диагональ экрана,
    # поэтому вынесено в настройки, а не зашито в вёрстку.
    # 4x2 подобрано под экран Aurora S2 (15.6", 1366x768): при трёх рядах карточка
    # сжимается до 131 px и фото товара перестаёт читаться.
    # Сетки разные: групп мало и они могут быть крупными, товаров в группе больше.
    grid_cols: int = Field(default=4, ge=2, le=6)
    grid_rows: int = Field(default=2, ge=1, le=5)
    product_grid_cols: int = Field(default=4, ge=2, le=6)
    product_grid_rows: int = Field(default=2, ge=1, le=5)


def load_settings() -> DeviceSettings:
    if not SETTINGS_FILE.exists():
        # Первый запуск: кладём файл на диск, чтобы его было что открыть и поправить.
        # За основу — образец из репозитория (`settings.example.json`): там уже
        # подобранные сетка, кегли и цвета, и прибор из коробки выглядит как надо,
        # а не как набор значений по умолчанию. Образца нет или он битый — берём
        # умолчания модели.
        return save_settings(_from_example())
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        # Ширина этикетки могла быть сохранена до того, как появился предел принтера.
        # Подрезаем её, а не роняем весь файл в значения по умолчанию.
        # Старое имя основного цвета: файл переносят с прибора на прибор, и
        # переименование поля не должно сбрасывать подобранный цвет.
        if isinstance(data, dict) and "ui_plate_color" in data:
            data.setdefault("ui_primary_color", data.pop("ui_plate_color"))
        if isinstance(data, dict) and isinstance(data.get("label_width_mm"), (int, float)):
            data["label_width_mm"] = min(float(data["label_width_mm"]), 56)
        return DeviceSettings.model_validate(data)
    except (OSError, ValueError, json.JSONDecodeError):
        # Битый или недоступный файл не должен ронять киоск.
        return DeviceSettings()


def _from_example() -> DeviceSettings:
    try:
        return DeviceSettings.model_validate(
            json.loads(SETTINGS_EXAMPLE_FILE.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError):
        return DeviceSettings()


def save_settings(settings: DeviceSettings) -> DeviceSettings:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(settings.model_dump(), ensure_ascii=False, indent=2)
    temp = SETTINGS_FILE.with_suffix(".json.tmp")
    temp.write_text(payload + "\n", encoding="utf-8")
    os.replace(temp, SETTINGS_FILE)
    return settings


def _read_presets() -> dict[str, dict]:
    if not SETTINGS_PRESETS_FILE.exists():
        return {}
    try:
        data = json.loads(SETTINGS_PRESETS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, json.JSONDecodeError):
        # Битый файл пресетов не должен ронять страницу настроек — просто нет пресетов.
        return {}


def _write_presets(presets: dict[str, dict]) -> None:
    SETTINGS_PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(presets, ensure_ascii=False, indent=2)
    temp = SETTINGS_PRESETS_FILE.with_suffix(".json.tmp")
    temp.write_text(payload + "\n", encoding="utf-8")
    os.replace(temp, SETTINGS_PRESETS_FILE)


def list_presets() -> list[str]:
    """Имена пресетов по алфавиту — оператор выбирает по названию, порядок сохранения не важен."""
    return sorted(_read_presets())


def save_preset(name: str, settings: DeviceSettings) -> None:
    """Сохраняет текущие настройки под именем `name`, заменяя одноимённый пресет."""
    presets = _read_presets()
    presets[name] = settings.model_dump()
    _write_presets(presets)


def apply_preset(name: str) -> DeviceSettings:
    """Поднимает пресет в основные настройки прибора и сразу их сохраняет."""
    presets = _read_presets()
    if name not in presets:
        raise KeyError(name)
    return save_settings(DeviceSettings.model_validate(presets[name]))


def delete_preset(name: str) -> None:
    presets = _read_presets()
    if presets.pop(name, None) is not None:
        _write_presets(presets)
