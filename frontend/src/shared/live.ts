/**
 * Оповещения о правках, сделанных в админке. Киоск подписан на них и не опрашивает
 * сервер: оператор трогает настройки раз в день, а опрос стоил бы запроса каждые
 * несколько секунд — при том, что прибор и так держит сокет ради веса.
 */
export type DeviceChange = 'settings' | 'catalog' | 'reconnect'

export function watchDeviceUpdates(onChange: (kind: DeviceChange) => void): () => void {
  let socket: WebSocket | null = null
  let retryDelay = 500
  let retryTimer: number | undefined
  let stopped = false
  let first = true

  function connect() {
    if (stopped) return
    const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
    socket = new WebSocket(`${scheme}://${location.host}/api/ws/updates`)

    socket.onopen = () => {
      retryDelay = 500
      // Пока связи не было, админку могли править: что именно — уже не узнать,
      // поэтому после обрыва киоск перечитывает всё.
      if (!first) onChange('reconnect')
      first = false
    }
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { changed: DeviceChange }
      onChange(payload.changed)
    }
    socket.onclose = () => {
      // Перезапуск сервиса или обрыв сети не должен требовать перезагрузки киоска —
      // то же правило, что и у потока веса.
      retryTimer = window.setTimeout(connect, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 5000)
    }
    socket.onerror = () => socket?.close()
  }

  connect()

  return () => {
    stopped = true
    window.clearTimeout(retryTimer)
    socket?.close()
    socket = null
  }
}
