<script setup lang="ts">
/**
 * Стартовая заставка: пиксели слетаются со всех сторон и складываются в надпись SMK.
 *
 * Вместо спиннера — потому что киоск включается один раз за смену, и первое, что видит
 * зал, должно выглядеть как включение прибора, а не как загрузка веб-страницы.
 * Точки берутся из растра самого текста, поэтому надпись всегда совпадает со шрифтом
 * и масштабируется под любой экран.
 */
import { onMounted, onUnmounted, ref } from 'vue'

const emit = defineEmits<{ done: [] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const leaving = ref(false)

const TEXT = 'SMK'
const INK = '#1747c9'
const FLY_MS = 1050 // сборка надписи
const HOLD_MS = 450 // пауза, чтобы надпись успели прочитать
const MAX_PARTICLES = 4200

interface Particle {
  x: number
  y: number
  tx: number
  ty: number
  sx: number
  sy: number
  delay: number
  size: number
}

let raf = 0
let guard = 0
let finished = false

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

function buildParticles(width: number, height: number): Particle[] {
  // Текст рисуется на служебном холсте, затем разбирается по пикселям.
  const probe = document.createElement('canvas')
  probe.width = width
  probe.height = height
  const pen = probe.getContext('2d')
  if (!pen) return []

  const fontSize = Math.min(width * 0.26, height * 0.42)
  pen.fillStyle = '#000'
  pen.textAlign = 'center'
  pen.textBaseline = 'middle'
  pen.font = `700 ${fontSize}px "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
  pen.letterSpacing = `${fontSize * 0.06}px`
  pen.fillText(TEXT, width / 2, height / 2)

  const data = pen.getImageData(0, 0, width, height).data
  // Шаг подбирается так, чтобы число частиц не зависело от разрешения экрана.
  let step = Math.max(3, Math.round(Math.sqrt((width * height) / MAX_PARTICLES / 6)))
  const points: Particle[] = []

  for (let y = 0; y < height; y += step) {
    for (let x = 0; x < width; x += step) {
      if (data[(y * width + x) * 4 + 3] < 128) continue
      // Старт — за пределами экрана, с любой из четырёх сторон.
      const side = Math.floor(Math.random() * 4)
      const spread = 1.4
      let sx = 0
      let sy = 0
      if (side === 0) {
        sx = Math.random() * width
        sy = -height * (0.2 + Math.random() * spread)
      } else if (side === 1) {
        sx = width * (1 + Math.random() * spread)
        sy = Math.random() * height
      } else if (side === 2) {
        sx = Math.random() * width
        sy = height * (1 + Math.random() * spread)
      } else {
        sx = -width * (0.2 + Math.random() * spread)
        sy = Math.random() * height
      }
      points.push({
        x: sx,
        y: sy,
        sx,
        sy,
        tx: x,
        ty: y,
        // Небольшой разброс задержек — надпись «собирается», а не появляется рывком.
        delay: Math.random() * 0.28,
        size: step - 1,
      })
    }
  }
  return points
}

function run() {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return finish()

  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  const width = Math.floor(element.clientWidth * ratio)
  const height = Math.floor(element.clientHeight * ratio)
  element.width = width
  element.height = height

  const particles = buildParticles(width, height)
  if (!particles.length) return finish()

  const started = performance.now()

  const frame = (now: number) => {
    const elapsed = now - started
    context.clearRect(0, 0, width, height)
    context.fillStyle = INK

    for (const p of particles) {
      const local = (elapsed / FLY_MS - p.delay) / (1 - p.delay)
      const t = easeOutCubic(Math.min(Math.max(local, 0), 1))
      p.x = p.sx + (p.tx - p.sx) * t
      p.y = p.sy + (p.ty - p.sy) * t
      context.globalAlpha = 0.25 + 0.75 * t
      context.fillRect(p.x, p.y, p.size, p.size)
    }
    context.globalAlpha = 1

    if (elapsed < FLY_MS + HOLD_MS) {
      raf = requestAnimationFrame(frame)
    } else {
      finish()
    }
  }

  raf = requestAnimationFrame(frame)
  // Страховка: в фоновой вкладке requestAnimationFrame не вызывается, и без этого
  // таймера заставка осталась бы висеть поверх киоска навсегда.
  guard = window.setTimeout(finish, FLY_MS + HOLD_MS + 500)
}

function finish() {
  if (finished) return
  finished = true
  window.clearTimeout(guard)
  cancelAnimationFrame(raf)
  leaving.value = true
  // Ждём затухание оверлея, иначе киоск «выпрыгивает» из-под заставки.
  window.setTimeout(() => emit('done'), 320)
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
  transition: opacity 0.3s ease;
}

.splash.leaving {
  opacity: 0;
}

.stage {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
