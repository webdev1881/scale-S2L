<script setup lang="ts">
/**
 * Стартовая заставка (~2 с): пиксели слетаются со всех сторон, собираются в надпись
 * SMK и уступают место чистой типографике с переливающимся градиентом.
 *
 * Вместо спиннера — киоск включается один раз за смену, и первое, что видит зал,
 * должно выглядеть как включение прибора, а не как загрузка веб-страницы.
 *
 * Пиксели — приём сборки, а не конечный вид: как только частицы сели, кадр
 * перетекает в тот же текст, нарисованный шрифтом со сглаживанием. Пиксельная
 * лесенка на финальном кадре читалась бы как низкое разрешение экрана.
 *
 * Фаза влёта пишется прямо в ImageData, а не тысячами fillRect: на процессоре
 * прибора (Intel J6412) вызовы канвы упираются в CPU уже на нескольких тысячах
 * точек, а запись в буфер стоит одинаково при любом их числе.
 */
import { onMounted, onUnmounted, ref } from 'vue'

const emit = defineEmits<{ done: [] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const leaving = ref(false)

const TEXT = 'SMK'

// Итого ~2 с вместе с растворением
const FLY_MS = 1050 // влёт и сборка из частиц
const CRISP_MS = 280 // переход от зерна к шрифту
const HOLD_MS = 400 // перелив по готовой надписи
const FADE_MS = 300

const MAX_PARTICLES = 26000
const MIN_STEP = 2

// Палитра Element Plus вокруг primary #409EFF. Светлые токены (#79bbff, #a0cfff)
// в заливку не берём: они рассчитаны на фоны и рамки и на белом выцветают.
// Кольцо замкнуто, чтобы перелив шёл без стыка.
const RAMP: [number, number, number][] = [
  [41, 98, 173],
  [51, 126, 204], // #337ecc
  [64, 158, 255], // #409eff — primary
  [102, 177, 255], // #66b1ff
  [64, 158, 255],
  [51, 126, 204],
]
const RAMP_STEPS = 64 // степень двойки: индекс берётся через & (RAMP_STEPS - 1)
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
  font: string
  fontSize: number
  minX: number
  maxX: number
  baseline: number
  lineHeight: number
}

/** Мягкий «перелёт» с доводкой: частица чуть проскакивает цель и садится на место. */
function easeOutBack(t: number): number {
  const c1 = 1.02
  const c3 = c1 + 1
  const p = t - 1
  return 1 + c3 * p * p * p + c1 * p * p
}

function easeOutCubic(t: number): number {
  const p = 1 - t
  return 1 - p * p * p
}

function fontFor(size: number): string {
  return `700 ${size}px "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
}

function buildField(width: number, height: number): Field | null {
  const probe = document.createElement('canvas')
  probe.width = width
  probe.height = height
  const pen = probe.getContext('2d', { willReadFrequently: true })
  if (!pen) return null

  const fontSize = Math.min(width * 0.29, height * 0.46)
  const font = fontFor(fontSize)
  pen.fillStyle = '#000'
  pen.textAlign = 'center'
  pen.textBaseline = 'middle'
  pen.font = font
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

  const lineHeight = Math.max(2, Math.round(fontSize * 0.035))
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
    font,
    fontSize,
    minX,
    maxX,
    baseline: Math.min(maxY + Math.round(fontSize * 0.16), height - lineHeight - 2),
    lineHeight,
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

/** Таблица ABGR на пару «оттенок градиента × прозрачность» для фазы влёта. */
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

/**
 * Тот же перелив для чистой надписи: кольцо цветов повторяется по ширине и
 * сдвигается со временем. Полоса шире надписи на цикл с каждой стороны, поэтому
 * при сдвиге не открывается пустой край.
 */
function shimmerGradient(
  context: CanvasRenderingContext2D,
  field: Field,
  elapsed: number,
): CanvasGradient {
  const span = Math.max(field.maxX - field.minX, 1)
  const cycle = span / CYCLES_ACROSS
  const offset = ((elapsed / SHIMMER_MS) % 1) * cycle
  const from = field.minX - cycle + offset
  const to = field.maxX + cycle + offset
  const gradient = context.createLinearGradient(from, 0, to, 0)

  const rings = Math.ceil((to - from) / cycle)
  const stops = rings * RAMP.length
  for (let k = 0; k <= stops; k++) {
    const [r, g, b] = RAMP[k % RAMP.length]
    gradient.addColorStop(Math.min(1, k / stops), `rgb(${r},${g},${b})`)
  }
  return gradient
}

function run() {
  const element = canvas.value
  const view = element?.getContext('2d')
  if (!element || !view) return finish()

  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  const width = Math.floor(element.clientWidth * ratio)
  const height = Math.floor(element.clientHeight * ratio)
  if (!width || !height) return finish()
  element.width = width
  element.height = height

  const field = buildField(width, height)
  if (!field) return finish()

  const grain = document.createElement('canvas')
  grain.width = width
  grain.height = height
  const grainCtx = grain.getContext('2d')
  if (!grainCtx) return finish()

  const image = grainCtx.createImageData(width, height)
  const pixels = new Uint32Array(image.data.buffer)
  const colors = buildColorTable()

  const started = performance.now()
  const total = FLY_MS + CRISP_MS + HOLD_MS
  const dot = field.dot
  const span = Math.max(field.maxX - field.minX, 1)
  const centreX = (field.minX + field.maxX) / 2
  const gradientK = (RAMP_STEPS * CYCLES_ACROSS) / span
  const mask = RAMP_STEPS - 1

  const frame = (now: number) => {
    const elapsed = now - started
    const flyPhase = Math.min(elapsed / FLY_MS, 1)
    const crisp = Math.min(Math.max((elapsed - FLY_MS) / CRISP_MS, 0), 1)
    const phase = (elapsed / SHIMMER_MS) * RAMP_STEPS

    view.clearRect(0, 0, width, height)

    // Пока зерно ещё видно — собираем кадр частиц. После перехода этот проход
    // не нужен вовсе, и на удержании кадр стоит почти ничего.
    if (crisp < 1) {
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

        const level = landed ? ALPHA_LEVELS - 1 : ((0.25 + 0.75 * t) * (ALPHA_LEVELS - 1)) | 0
        const shade = ((x * gradientK + phase) | 0) & mask
        const colour = colors[shade * ALPHA_LEVELS + level]

        let idx = y * width + x
        for (let row = 0; row < dot; row++, idx += width) {
          for (let col = 0; col < dot; col++) pixels[idx + col] = colour
        }
      }
      grainCtx.putImageData(image, 0, 0)
      view.globalAlpha = 1 - crisp
      view.drawImage(grain, 0, 0)
    }

    // Финал — не зерно, а нормально сглаженный шрифт с тем же переливом.
    if (crisp > 0) {
      const gradient = shimmerGradient(view, field, elapsed)
      view.globalAlpha = crisp
      view.fillStyle = gradient
      view.textAlign = 'center'
      view.textBaseline = 'middle'
      view.font = field.font
      view.letterSpacing = `${field.fontSize * 0.06}px`
      view.fillText(TEXT, width / 2, height / 2)

      const half = (span / 2) * easeOutCubic(crisp)
      view.fillRect(centreX - half, field.baseline, half * 2, field.lineHeight)
    }

    view.globalAlpha = 1

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
  background: var(--s2l-splash-bg);
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
