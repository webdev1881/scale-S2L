<script setup lang="ts">
/**
 * Стартовая заставка: пиксели слетаются со всех сторон и складываются в надпись SMK.
 *
 * Вместо спиннера — потому что киоск включается один раз за смену, и первое, что видит
 * зал, должно выглядеть как включение прибора, а не как загрузка веб-страницы.
 * Точки берутся из растра самого текста, поэтому надпись всегда совпадает со шрифтом
 * и масштабируется под любой экран.
 *
 * Кадр рисуется прямой записью в ImageData, а не тысячами fillRect: на процессоре
 * прибора (Intel J6412) вызовы канвы упираются в CPU уже на нескольких тысячах
 * частиц, а запись в буфер стоит одинаково при любом их количестве.
 */
import { onMounted, onUnmounted, ref } from 'vue'

const emit = defineEmits<{ done: [] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const leaving = ref(false)

const TEXT = 'SMK'
const FLY_MS = 1150 // сборка надписи
const SWEEP_MS = 420 // блик по собранной надписи
const HOLD_MS = 260 // пауза, чтобы надпись успели прочитать
const FADE_MS = 320

const MAX_PARTICLES = 26000
const MIN_STEP = 2
const DOT = 2 // сторона точки в пикселях холста

// Градиент по ширине надписи + светлый набор для блика
const PALETTE: [number, number, number][] = [
  [47, 111, 228],
  [35, 92, 214],
  [23, 71, 201],
  [18, 58, 176],
  [13, 47, 143],
  [10, 38, 120],
]
const HIGHLIGHT: [number, number, number] = [120, 176, 255]
const ALPHA_LEVELS = 32

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
  bucket: Uint8Array
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
  for (let y = 0; y < height; y += step) {
    for (let x = 0; x < width; x += step) {
      if (data[(y * width + x) * 4 + 3] < 128) continue
      targets.push(x, y)
      if (x < minX) minX = x
      if (x > maxX) maxX = x
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
    bucket: new Uint8Array(count),
  }

  const spanX = Math.max(maxX - minX, 1)
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
    field.bucket[i] = Math.min(
      PALETTE.length - 1,
      Math.floor(((tx - minX) / spanX) * PALETTE.length),
    )
  }
  return field
}

/** Готовые ABGR-значения на каждую пару «цвет × прозрачность»: в кадре только выборка. */
function buildColorTable(): Uint32Array {
  const colors = [...PALETTE, HIGHLIGHT]
  const table = new Uint32Array(colors.length * ALPHA_LEVELS)
  for (let c = 0; c < colors.length; c++) {
    const [r, g, b] = colors[c]
    for (let a = 0; a < ALPHA_LEVELS; a++) {
      const alpha = Math.round((a / (ALPHA_LEVELS - 1)) * 255)
      table[c * ALPHA_LEVELS + a] = (alpha << 24) | (b << 16) | (g << 8) | r
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
  const highlightRow = PALETTE.length * ALPHA_LEVELS

  const started = performance.now()
  const sweepBand = width * 0.08
  const OFFSCREEN = -1e9

  const frame = (now: number) => {
    const elapsed = now - started
    const flyPhase = Math.min(elapsed / FLY_MS, 1)
    const sweepPhase = Math.min(Math.max((elapsed - FLY_MS) / SWEEP_MS, 0), 1)
    const sweeping = sweepPhase > 0 && sweepPhase < 1
    const sweepX = sweeping ? -sweepBand + sweepPhase * (width + 2 * sweepBand) : OFFSCREEN

    pixels.fill(0)

    for (let i = 0; i < field.count; i++) {
      const delay = field.delay[i]
      const local = (flyPhase - delay) / (1 - delay)
      if (local <= 0) continue
      const t = local >= 1 ? 1 : local
      const e = t >= 1 ? 1 : easeOutBack(t)
      const swing = t >= 1 ? 0 : Math.sin(Math.PI * t)

      const x = (field.sx[i] + field.dx[i] * e + field.ax[i] * swing) | 0
      const y = (field.sy[i] + field.dy[i] * e + field.ay[i] * swing) | 0
      if (x < 0 || y < 0 || x >= width - DOT || y >= height - DOT) continue

      const level = ((0.2 + 0.8 * t) * (ALPHA_LEVELS - 1)) | 0
      const lit = sweeping && x - sweepX < sweepBand && sweepX - x < sweepBand
      const colour = colors[(lit ? highlightRow : field.bucket[i] * ALPHA_LEVELS) + level]

      let idx = y * width + x
      for (let row = 0; row < DOT; row++, idx += width) {
        for (let col = 0; col < DOT; col++) pixels[idx + col] = colour
      }
    }

    context.putImageData(image, 0, 0)

    if (elapsed < FLY_MS + SWEEP_MS + HOLD_MS) {
      raf = requestAnimationFrame(frame)
    } else {
      finish()
    }
  }

  raf = requestAnimationFrame(frame)
  // Страховка: в фоновой вкладке requestAnimationFrame не вызывается, и без этого
  // таймера заставка осталась бы висеть поверх киоска навсегда.
  guard = window.setTimeout(finish, FLY_MS + SWEEP_MS + HOLD_MS + 600)
}

function finish() {
  if (finished) return
  finished = true
  window.clearTimeout(guard)
  cancelAnimationFrame(raf)
  leaving.value = true
  // Ждём затухание оверлея, иначе киоск «выпрыгивает» из-под заставки.
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
  background: #ffffff;
  transition:
    opacity 0.32s ease,
    transform 0.32s ease;
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
