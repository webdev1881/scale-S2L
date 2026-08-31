import { defineStore } from 'pinia'
import { ref } from 'vue'

import type { WeightReading } from './types'

const EMPTY: WeightReading = { gross_g: 0, net_g: 0, tare_g: 0, stable: false, error: null }

/**
 * Поток веса по WebSocket. REST не опрашиваем: 10 запросов в секунду с киоска —
 * это лишняя нагрузка и рваная картинка на экране.
 */
export const useWeightStore = defineStore('weight', () => {
  const reading = ref<WeightReading>({ ...EMPTY })
  const connected = ref(false)

  let socket: WebSocket | null = null
  let retryDelay = 500
  let retryTimer: number | undefined

  function connect() {
    const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
    socket = new WebSocket(`${scheme}://${location.host}/api/ws/weight`)

    socket.onopen = () => {
      connected.value = true
      retryDelay = 500
    }
    socket.onmessage = (event) => {
      reading.value = JSON.parse(event.data) as WeightReading
    }
    socket.onclose = () => {
      connected.value = false
      reading.value = { ...EMPTY, error: 'Нет связи с весами' }
      // Перезапуск сервиса или обрыв сети не должен требовать перезагрузки киоска.
      retryTimer = window.setTimeout(connect, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 5000)
    }
    socket.onerror = () => socket?.close()
  }

  function disconnect() {
    window.clearTimeout(retryTimer)
    socket?.close()
    socket = null
  }

  return { reading, connected, connect, disconnect }
})
