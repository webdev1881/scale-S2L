"""Проверка разбора кадра весовой платы без железа.

Запуск:  python backend/tests_serial_frames.py

Кадр подтверждён на приборе (issue #1): 8 байт, шесть ASCII-цифр граммов между
двумя обрамляющими байтами. Здесь проверяется главное, что нельзя проверить
на столе без весов: восстановление синхронизации после потери байта и то, что
склеенные половинки соседних кадров не принимаются за правдоподобный вес.
"""
import sys

sys.path.insert(0, r"D:\Code___2026\scale S2L\backend")

from app.hal.scale.serial_scale import SerialScale  # noqa: E402

STX, ETX = b"\x02", b"\x03"


def frame(grams: int, head: bytes = STX, tail: bytes = ETX) -> bytes:
    return head + f"{grams:06d}".encode("ascii") + tail


def feed(scale: SerialScale, data: bytes) -> None:
    scale._buffer.extend(data)
    scale._consume()


def case(name: str, ok: bool, extra: str = "") -> None:
    print(f"[{'OK ' if ok else 'FAIL'}] {name}{' — ' + extra if extra else ''}")
    if not ok:
        globals()["failed"] = True


failed = False

# 1. Чистый поток
s = SerialScale("/dev/null")
feed(s, frame(1240) + frame(1240) + frame(1240) + frame(1240) + frame(1240))
case("чистый поток: вес", s._gross_g == 1240, f"{s._gross_g} г")
case("чистый поток: 5 кадров", s._frames == 5, f"frames={s._frames}")
case("чистый поток: стабильность", s._stable is True)
case("обрамление зафиксировано", s._prefix == repr(STX) and s._suffix == repr(ETX),
     f"{s._prefix} .. {s._suffix}")

# 2. Разрыв синхронизации: теряем один байт в середине потока
s = SerialScale("/dev/null")
stream = frame(1000) + frame(2000)[1:] + frame(3000) + frame(3000) + frame(3000) + frame(3000)
feed(s, stream)
case("после потери байта поток восстановлен", s._gross_g == 3000, f"{s._gross_g} г")
case("склеенные половинки не приняты за кадр", s._frames <= 5, f"frames={s._frames}")

# 3. Мусор не порождает кадров
s = SerialScale("/dev/null")
feed(s, bytes(range(0x41, 0x41 + 40)))
case("мусор игнорируется", s._frames == 0 and s._error is not None, f"frames={s._frames}")
case("буфер не растёт", len(s._buffer) <= 4 * 8, f"{len(s._buffer)} байт")

# 4. Нестабильный вес не объявляется стабильным
s = SerialScale("/dev/null", division_g=5)
for grams in (1000, 1200, 1400, 1600, 1800):
    feed(s, frame(grams))
case("прыгающий вес нестабилен", s._stable is False)
for _ in range(5):
    feed(s, frame(1800))
case("успокоившийся вес стабилен", s._stable is True)

# 5. Дрожание в пределах цены деления считается стабильным
s = SerialScale("/dev/null", division_g=5)
for grams in (1000, 1005, 1000, 1005, 1000):
    feed(s, frame(grams))
case("дрожание в пределах деления — стабильно", s._stable is True)

# 6. Разбор совпадает с образцом из тикета
raw = frame(1240)
reference = float(int(str(raw, encoding="ascii")[1 : len(raw) - 1]) / 1000)
s = SerialScale("/dev/null")
feed(s, raw)
case("совпадает с реализацией из issue #1", s._gross_g / 1000 == reference,
     f"{s._gross_g / 1000} == {reference}")

# 7. Знак минус в обрамлении
s = SerialScale("/dev/null")
feed(s, frame(250, head=b"-", tail=b"\r"))
case("отрицательный вес", s._gross_g == -250, f"{s._gross_g} г")

print("\nИТОГ:", "есть падения" if failed else "все проверки пройдены")
sys.exit(1 if failed else 0)
