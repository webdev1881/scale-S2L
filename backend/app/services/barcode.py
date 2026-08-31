"""Весовой EAN-13 и его отрисовка.

Формат весового штрихкода у каждой сети свой, поэтому шаблон задаётся строкой в
настройках. Плейсхолдеры:
    P — цифра PLU
    W — цифра значения (вес в граммах или сумма в копейках)
Первые символы шаблона — префикс (обычно 2x, зарезервирован под весовой товар).
Пример: "22PPPPPWWWWW" -> 22 + PLU(5) + значение(5) + контрольная цифра.
"""
from __future__ import annotations

# Кодировка левой половины EAN-13: L/G-набор выбирается по первой цифре
_L = ("0001101", "0011001", "0010011", "0111101", "0100011",
      "0110001", "0101111", "0111011", "0110111", "0001011")
_G = ("0100111", "0110011", "0011011", "0100001", "0011101",
      "0111001", "0000101", "0010001", "0001001", "0010111")
_R = ("1110010", "1100110", "1101100", "1000010", "1011100",
      "1001110", "1010000", "1000100", "1001000", "1110100")
_PARITY = ("LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
           "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL")


def ean13_check_digit(digits12: str) -> int:
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits12))
    return (10 - total % 10) % 10


def build_weight_barcode(template: str, plu: int, value: int) -> str:
    """Собирает 13-значный EAN-13 по шаблону. value — граммы или копейки."""
    p_count = template.count("P")
    w_count = template.count("W")
    plu_s = str(plu).rjust(p_count, "0")[-p_count:] if p_count else ""
    val_s = str(int(value)).rjust(w_count, "0")[-w_count:] if w_count else ""
    p_iter, w_iter = iter(plu_s), iter(val_s)
    body = "".join(
        next(p_iter) if ch == "P" else next(w_iter) if ch == "W" else ch for ch in template
    )
    body = "".join(c for c in body if c.isdigit())[:12].ljust(12, "0")
    return body + str(ean13_check_digit(body))


def ean13_pattern(code13: str) -> str:
    """Возвращает строку из '0'/'1' — модули штрихкода (без полей)."""
    if len(code13) != 13 or not code13.isdigit():
        raise ValueError("EAN-13 должен состоять из 13 цифр")
    parity = _PARITY[int(code13[0])]
    out = ["101"]
    for i, ch in enumerate(code13[1:7]):
        out.append(_L[int(ch)] if parity[i] == "L" else _G[int(ch)])
    out.append("01010")
    for ch in code13[7:]:
        out.append(_R[int(ch)])
    out.append("101")
    return "".join(out)
