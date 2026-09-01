<script setup lang="ts">
/**
 * Стартовая заставка (~2 с): пиксели слетаются со всех сторон и складываются
 * в монолитную надпись SMK, по которой переливается градиент.
 *
 * Вместо спиннера — киоск включается один раз за смену, и первое, что видит зал,
 * должно выглядеть как включение прибора, а не как загрузка веб-страницы.
 * Точки берутся из растра самого текста, поэтому надпись совпадает со шрифтом
 * и масштабируется под любой экран.
 *
 * Кадр пишется прямо в ImageData, а не тысячами fillRect: на процессоре прибора
 * (Intel J6412) вызовы канвы упираются в CPU уже на нескольких тысячах точек,
 * а запись в буфер стоит одинаково при любом их числе. Цвет берётся из заранее
 * посчитанной таблицы, поэтому перелив не стоит ничего сверх выборки из массива.
 */
import { onMounted, onUnmounted, ref } from 'vue'

const emit = defineEmits<{ done: [] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const leaving = ref(false)

const TEXT = 'SMK'

// Итого ~2 с вместе с растворением
const FLY_MS = 1050 // влёт и сборка
const HOLD_MS = 650 // перелив по собранной надписи
const FADE_MS = 300

const MAX_PARTICLES = 26000
const MIN_STEP = 2

// Палитра Element Plus вокруг primary #409EFF. Светлые токены (#79bbff, #a0cfff)
// в заливку не берём: они рассчитаны на фоны и рамки и на белом выцветают.
// Кольцо замкнуто, чтобы перелив шёл без стыка.
const RAMP: [number, number, number][] = [
  [41, 98, 173], // тень
  [51, 126, 204], // #337ecc
  [64, 158, 255], // #409eff — primary
  [102, 177, 255], // #66b1ff — светлый акцент
  [64, 158, 255],
  [51, 126, 204],
]
const RAMP_STEPS = 64 // должно быть степенью двойки: индекс берётся через & (RAMP_STEPS - 1)
const ALPHA_LEVELS = 32
const CYCLES_ACROSS = 1.6 // сколько волн градиента укладывается в ширину надписи
const SHIMMER_MS = 1600 // период перелива

let raf = 0
let guard = 0
let finished = false

interface Field {
  count: number
  sx: Float32Array
  sy: Float32Array
  dx: Float32Array
  dy: Float32Array
  ax: Float32Array // амплитуда дуги по нормали к траектории
  ay: Float32Array
  delay: Float32Array
  dot: number // сторона точки = шагу сетки, иначе между точками остаются просветы
  minX: number
  maxX: number
  baseline: number
}

/** Мягкий «перелёт» с доводкой: частица чуть проскакивает цель и садится на место. */
function easeOutBack(t: number): number {
  const c1 = 1.02
  const c3 = c1 + 1
  const p = t - 1
  return 1 + c3 * p * p * p + c1 * p * p
}

function buildField(width: number, height: number): Field | null {
  const probe = document.createElement('canvas')
  probe.width = width
  probe.height = height
  const pen = probe.getContext('2d', { willReadFrequently: true })
  if (!pen) return null

  const fontSize = Math.min(width * 0.29, height * 0.46)
  pen.fillStyle = '#000'
  pen.textAlign = 'center'
  pen.textBaseline = 'middle'
  pen.font = `700 ${fontSize}px "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
  pen.letterSpacing = `${fontSize * 0.06}px`
  pen.fillText(TEXT, width / 2, height / 2)

  const data = pen.getImageData(0, 0, width, height).data

  // Шаг сетки считается от реального числа закрашенных пикселей, поэтому плотность
  // не скачет вслед за разрешением экрана.
  let ink = 0
  for (let i = 3; i < data.length; i += 4) {
    if (data[i] >= 128) ink++
  }
  if (!ink) return null
  const step = Math.max(MIN_STEP, Math.round(Math.sqrt(ink / MAX_PARTICLES)))

  const targets: number[] = []
  let minX = width
  let maxX = 0
  let maxY = 0
  for (let y = 0; y < height; y += step) {
    for (let x = 0; x < width; x += step) {
      if (data[(y * width + x) * 4 + 3] < 128) continue
      targets.push(x, y)
      if (x < minX) minX = x
      if (x > maxX) maxX = x
      if (y > maxY) maxY = y
    }
  }

  const count = targets.length / 2
  if (!count) return null

  const field: Field = {
    count,
    sx: new Float32Array(count),
    sy: new Float32Array(count),
    dx: new Float32Array(count),
    dy: new Float32Array(count),
    ax: new Float32Array(count),
    ay: new Float32Array(count),
    delay: new Float32Array(count),
    dot: step,
    minX,
    maxX,
    baseline: Math.min(maxY + Math.round(fontSize * 0.16), height - step - 2),
  }

  const centreX = width / 2
  const centreY = height / 2
  const radius = Math.hypot(width, height) * 0.75

  for (let i = 0; i < count; i++) {
    const tx = targets[i * 2]
    const ty = targets[i * 2 + 1]

    // Старт — точка на окружности за пределами экрана: частицы приходят со всех сторон.
    const angle = Math.random() * Math.PI * 2
    const spread = 0.85 + Math.random() * 0.6
    const sx = centreX + Math.cos(angle) * radius * spread
    const sy = centreY + Math.sin(angle) * radius * spread

    const dx = tx - sx
    const dy = ty - sy
    const len = Math.hypot(dx, dy) || 1
    // Смещение по нормали превращает прямой отрезок в дугу — движение читается
    // как влёт по траектории, а не как линейная телепортация.
    const arc = (Math.random() - 0.5) * len * 0.35

    field.sx[i] = sx
    field.sy[i] = sy
    field.dx[i] = dx
    field.dy[i] = dy
    field.ax[i] = (-dy / len) * arc
    field.ay[i] = (dx / len) * arc
    field.delay[i] = Math.random() * 0.34
  }
  return field
}

/**
 * Таблица ABGR на пару «оттенок градиента × прозрачность». Оттенки получаются
 * линейной интерполяцией по кольцу RAMP, поэтому перелив идёт плавно и замкнуто.
 */
function buildColorTable(): Uint32Array {
  const table = new Uint32Array(RAMP_STEPS * ALPHA_LEVELS)
  for (let s = 0; s < RAMP_STEPS; s++) {
    const pos = (s / RAMP_STEPS) * RAMP.length
    const from = RAMP[Math.floor(pos) % RAMP.length]
    const to = RAMP[(Math.floor(pos) + 1) % RAMP.length]
    const k = pos - Math.floor(pos)
    const r = Math.round(from[0] + (to[0] - from[0]) * k)
    const g = Math.round(from[1] + (to[1] - from[1]) * k)
    const b = Math.round(from[2] + (to[2] - from[2]) * k)
    for (let a = 0; a < ALPHA_LEVELS; a++) {
      const alpha = Math.round((a / (ALPHA_LEVELS - 1)) * 255)
      table[s * ALPHA_LEVELS + a] = (alpha << 24) | (b << 16) | (g << 8) | r
    }
  }
  return table
}

function run() {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return finish()

  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  const width = Math.floor(element.clientWidth * ratio)
  const height = Math.floor(element.clientHeight * ratio)
  if (!width || !height) return finish()
  element.width = width
  element.height = height

  const field = buildField(width, height)
  if (!field) return finish()

  const image = context.createImageData(width, height)
  const pixels = new Uint32Array(image.data.buffer)
  const colors = buildColorTable()

  const started = performance.now()
  const total = FLY_MS + HOLD_MS
  const dot = field.dot
  const span = Math.max(field.maxX - field.minX, 1)
  const gradientK = (RAMP_STEPS * CYCLES_ACROSS) / span
  const mask = RAMP_STEPS - 1

  const frame = (now: number) => {
    const elapsed = now - started
    const flyPhase = Math.min(elapsed / FLY_MS, 1)
    const phase = (elapsed / SHIMMER_MS) * RAMP_STEPS

    pixels.fill(0)

    for (let i = 0; i < field.count; i++) {
      const delay = field.delay[i]
      const local = (flyPhase - delay) / (1 - delay)
      if (local <= 0) continue
      const t = local >= 1 ? 1 : local
      const landed = t >= 1
      const e = landed ? 1 : easeOutBack(t)
      const swing = landed ? 0 : Math.sin(Math.PI * t)

      // Округление, а не усечение: sx + dx даёт цель с погрешностью float, и при
      // усечении часть севших точек уезжает на пиксель — в заливке появляется крапина.
      const x = (field.sx[i] + field.dx[i] * e + field.ax[i] * swing + 0.5) | 0
      const y = (field.sy[i] + field.dy[i] * e + field.ay[i] * swing + 0.5) | 0
      if (x < 0 || y < 0 || x >= width - dot || y >= height - dot) continue

      // Севшая точка всегда непрозрачна: надпись должна читаться как монолит,
      // а не как облако разноярких зёрен. Прозрачность работает только на подлёте.
      const level = landed ? ALPHA_LEVELS - 1 : ((0.25 + 0.75 * t) * (ALPHA_LEVELS - 1)) | 0
      const shade = ((x * gradientK + phase) | 0) & mask
      const colour = colors[shade * ALPHA_LEVELS + level]

      let idx = y * width + x
      for (let row = 0; row < dot; row++, idx += width) {
        for (let col = 0; col < dot; col++) pixels[idx + col] = colour
      }
    }

    // Линия под надписью подхватывает тот же перелив и появляется вместе с посадкой.
    if (flyPhase > 0.55) {
      const grow = Math.min((flyPhase - 0.55) / 0.45, 1)
      const centre = (field.minX + field.maxX) / 2
      const half = (span / 2) * grow
      const from = Math.max(0, (centre - half) | 0)
      const to = Math.min(width - 1, (centre + half) | 0)
      for (let row = 0; row < dot; row++) {
        const base = (field.baseline + row) * width
        for (let x = from; x <= to; x++) {
          const shade = ((x * gradientK + phase) | 0) & mask
          pixels[base + x] = colors[shade * ALPHA_LEVELS + ALPHA_LEVELS - 1]
        }
      }
    }

    context.putImageData(image, 0, 0)

    if (elapsed < total) {
      raf = requestAnimationFrame(frame)
    } else {
      finish()
    }
  }

  raf = requestAnimationFrame(frame)
  // Страховка: в фоновой вкладке requestAnimationFrame не вызывается, и без этого
  // таймера заставка осталась бы висеть поверх киоска навсегда.
  guard = window.setTimeout(finish, total + 600)
}

function finish() {
  if (finished) return
  finished = true
  window.clearTimeout(guard)
  cancelAnimationFrame(raf)
  leaving.value = true
  // Ждём растворение оверлея, иначе киоск «выпрыгивает» из-под заставки.
  window.setTimeout(() => emit('done'), FADE_MS)
}

onMounted(() => {
  // Уважаем системную настройку: анимация не должна быть обязательной.
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  if (reduced) {
    window.setTimeout(finish, 600)
    return
  }
  run()
})

onUnmounted(() => {
  cancelAnimationFrame(raf)
  window.clearTimeout(guard)
})
</script>

<template>
  <div class="splash" :class="{ leaving }">
    <canvas ref="canvas" class="stage"></canvas>
  </div>
</template>

<style scoped>
.splash {
  position: fixed;
  inset: 0;
  z-index: 3000;
  /* Тот же фон, что у киоска: переход в интерфейс не даёт вспышки */
  background: #ffffff;
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}

.splash.leaving {
  opacity: 0;
  /* Едва заметный наезд на уходе: надпись «растворяется вперёд», а не гаснет плашкой */
  transform: scale(1.04);
}

.stage {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
