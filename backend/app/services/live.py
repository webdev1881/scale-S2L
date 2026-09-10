"""Оповещение киоска о правках, сделанных в админке.

Киоск перечитывал настройки только при возврате на начальный экран: оператор менял
сетку или цену, шёл к прибору и не понимал, почему ничего не изменилось. Опрашивать
по таймеру ради события, которое случается раз в день, — расточительство, поэтому
админка сама говорит, что тронула, а киоск слушает.

Очередь на каждого подписчика, а не общий список: киоск на приборе один, но админку
открывают и с ноутбука, и с телефона, и потерянное оповещение выглядит ровно как
«настройка не применилась».
"""

from __future__ import annotations

import asyncio

# Что изменилось: настройки устройства или каталог товаров.
Kind = str

_listeners: set[asyncio.Queue[Kind]] = set()
# Цикл событий, в котором живут очереди. Обработчики FastAPI синхронные, а значит
# выполняются в отдельном потоке: положить туда напрямую можно, но разбудить ждущего
# слушателя — нет, и оповещение доходило через раз.
_loop: asyncio.AbstractEventLoop | None = None


def subscribe() -> asyncio.Queue[Kind]:
    global _loop
    _loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Kind] = asyncio.Queue()
    _listeners.add(queue)
    return queue


def unsubscribe(queue: asyncio.Queue[Kind]) -> None:
    _listeners.discard(queue)


def notify(kind: Kind) -> None:
    """Позвать всех слушателей. Вызывается из обычных (не async) обработчиков."""
    listeners = list(_listeners)
    if not listeners:
        return
    loop = _loop
    for queue in listeners:
        # Класть в очередь только через её цикл событий: иначе `put_nowait` из
        # рабочего потока оставляет ждущего слушателя спящим до следующего события.
        # Очередь без предела, переполнением уронить нас нельзя, а отвалившийся
        # слушатель уберётся сам при закрытии сокета.
        if loop is None or loop.is_closed():
            queue.put_nowait(kind)
        else:
            loop.call_soon_threadsafe(queue.put_nowait, kind)
