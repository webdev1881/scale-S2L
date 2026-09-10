<script setup lang="ts">
/**
 * Конструктор этикетки: слева живое превью с перетаскиваемыми блоками, справа их
 * список и свойства выбранного.
 *
 * Превью рисует бэкенд тем же рендером, что и печать, — своей отрисовки здесь нет
 * намеренно: «на экране одно, на бумаге другое» должно оставаться структурно
 * невозможным. Несохранённая раскладка уходит в запрос превью, поэтому двигать
 * блоки можно, ничего не сохраняя.
 */
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave } from 'vue-router'

import { api } from '@/shared/api'
import type { DeviceSettings, LabelBlock, LabelLayout, Product } from '@/shared/types'

const { t } = useI18n()

const settings = ref<DeviceSettings | null>(null)
const products = ref<Product[]>([])
const sampleId = ref<number | null>(null)
const sampleWeight = ref(740)
const selected = ref(0)
const previewUrl = ref('')
const sheet = ref<HTMLElement | null>(null)
const saving = ref(false)

const blocks = computed(() => settings.value?.label_layout.blocks ?? [])
const widthMm = computed(() => settings.value?.label_width_mm ?? 56)
const heightMm = computed(() => settings.value?.label_height_mm ?? 40)
const current = computed(() => blocks.value[selected.value] ?? null)

const KINDS = [
  'store',
  'name',
  'weight',
  'price',
  'total',
  'barcode',
  'packed',
  'best_before',
  'composition',
  'text',
  'line',
] as const

function blockTitle(block: LabelBlock) {
  return block.kind === 'text' && block.text ? block.text : t(`admin.label.kind.${block.kind}`)
}

// --- история правок ---------------------------------------------------------

/**
 * Отмена — первое, чего ждут от редактора: блок легко утащить не туда, а вернуть
 * его мышью на прежнее место уже не выйдет. Храним снимки раскладки целиком: в ней
 * десяток блоков, и городить обратные операции ради этого незачем.
 */
const HISTORY_LIMIT = 50
const history = ref<string[]>([])
const future = ref<string[]>([])
let savedState = ''
let applying = false

function snapshot() {
  return JSON.stringify(settings.value?.label_layout ?? {})
}

/** Запомнить состояние ДО правки. Вызывается один раз на осмысленное действие. */
function remember() {
  if (applying || !settings.value) return
  history.value.push(snapshot())
  if (history.value.length > HISTORY_LIMIT) history.value.shift()
  future.value = []
}

function apply(state: string) {
  if (!settings.value) return
  applying = true
  settings.value.label_layout = JSON.parse(state) as LabelLayout
  selected.value = Math.max(0, Math.min(selected.value, blocks.value.length - 1))
  void nextTick(() => (applying = false))
  schedulePreview()
}

function undo() {
  const state = history.value.pop()
  if (state === undefined) return
  future.value.push(snapshot())
  apply(state)
}

function redo() {
  const state = future.value.pop()
  if (state === undefined) return
  history.value.push(snapshot())
  apply(state)
}

const dirty = computed(() => Boolean(settings.value) && snapshot() !== savedState)

// --- превью -----------------------------------------------------------------

let previewTimer: number | undefined
let lastUrl = ''
// Номер запроса: превью рисуется миллисекунды, но при быстрой правке ответы
// приходят вперемешку, и медленный затирал бы свежий.
let previewToken = 0

/** Перерисовка идёт с задержкой: пока блок тянут пальцем, кадров десятки. */
function schedulePreview() {
  window.clearTimeout(previewTimer)
  previewTimer = window.setTimeout(refreshPreview, 180)
}

async function refreshPreview() {
  if (!settings.value || !sampleId.value) return
  const token = ++previewToken
  try {
    const blob = await api.labelPreview({
      product_id: sampleId.value,
      weight_g: sampleWeight.value,
      layout: settings.value.label_layout,
    })
    if (token !== previewToken) return
    // Прежний объект отпускаем сами: их тут делаются сотни за сессию правки.
    if (lastUrl) URL.revokeObjectURL(lastUrl)
    lastUrl = URL.createObjectURL(blob)
    previewUrl.value = lastUrl
  } catch {
    if (token === previewToken) ElMessage.warning(t('admin.label.previewFailed'))
  }
}

// --- перетаскивание с прилипанием -------------------------------------------

const SNAP_MM = 1.2
const guides = ref<{ x: number[]; y: number[] }>({ x: [], y: [] })
let drag: { index: number; x: number; y: number; blockX: number; blockY: number } | null = null

function mmPerPx() {
  const box = sheet.value?.getBoundingClientRect()
  return box && box.width ? widthMm.value / box.width : 0
}

/**
 * Куда прилипать: края этикетки и края соседних блоков. Ровнять их на глаз по
 * растру в четверть натуральной величины невозможно, а бумага разницу покажет.
 */
function snapTargets(index: number) {
  const x = [0, widthMm.value]
  const y = [0, heightMm.value]
  blocks.value.forEach((block, i) => {
    if (i === index) return
    x.push(block.x, block.x + (block.width || widthMm.value - block.x))
    y.push(block.y, block.y + (block.height || block.size / 8))
  })
  return { x, y }
}

function snap(value: number, targets: number[], hits: number[]) {
  for (const target of targets) {
    if (Math.abs(value - target) <= SNAP_MM) {
      hits.push(target)
      return target
    }
  }
  return value
}

function onGrab(index: number, event: PointerEvent) {
  const block = blocks.value[index]
  selected.value = index
  remember()
  drag = { index, x: event.clientX, y: event.clientY, blockX: block.x, blockY: block.y }
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onDrag(event: PointerEvent) {
  if (!drag) return
  const scale = mmPerPx()
  const block = blocks.value[drag.index]
  let x = clamp(drag.blockX + (event.clientX - drag.x) * scale, 0, widthMm.value - 2)
  let y = clamp(drag.blockY + (event.clientY - drag.y) * scale, 0, heightMm.value - 2)
  // Alt отключает прилипание: иногда блок нужен именно там, куда его ведут.
  if (event.altKey) {
    guides.value = { x: [], y: [] }
  } else {
    const targets = snapTargets(drag.index)
    const hitX: number[] = []
    const hitY: number[] = []
    x = snap(x, targets.x, hitX)
    y = snap(y, targets.y, hitY)
    guides.value = { x: hitX, y: hitY }
  }
  block.x = x
  block.y = y
  schedulePreview()
}

function onDrop() {
  drag = null
  guides.value = { x: [], y: [] }
}

function clamp(value: number, low: number, high: number) {
  return Math.round(Math.min(Math.max(value, low), high) * 10) / 10
}

/** Рамка блока в процентах — превью тянется по ширине окна, проценты переживают это. */
function frame(block: LabelBlock) {
  const w = block.width || widthMm.value - block.x - 1.5
  // Высота текста известна только рендеру; для рамки берём кегль в миллиметрах.
  const h = block.height || (block.kind === 'line' ? 0.4 : (block.size / 8) * block.lines * 1.2)
  return {
    left: `${(block.x / widthMm.value) * 100}%`,
    top: `${(block.y / heightMm.value) * 100}%`,
    width: `${(w / widthMm.value) * 100}%`,
    height: `${(h / heightMm.value) * 100}%`,
  }
}

/** Блок, ушедший за край, на бумаге просто не напечатается — и это надо видеть. */
function outside(block: LabelBlock) {
  const w = block.width || widthMm.value - block.x
  const h = block.height || block.size / 8
  return block.x + w > widthMm.value + 0.5 || block.y + h > heightMm.value + 0.5
}

const outsideCount = computed(() => blocks.value.filter(outside).length)

// --- правка списка ----------------------------------------------------------

function addBlock() {
  remember()
  blocks.value.push({
    kind: 'text',
    x: 2,
    y: 2,
    width: 0,
    height: 0,
    size: 18,
    bold: false,
    align: 'left',
    caption: false,
    lines: 1,
    box: false,
    text: t('admin.label.newText'),
    visible: true,
  })
  selected.value = blocks.value.length - 1
  schedulePreview()
}

function duplicate() {
  if (!current.value) return
  remember()
  const copy = { ...current.value, x: clamp(current.value.x + 2, 0, widthMm.value - 2) }
  blocks.value.splice(selected.value + 1, 0, copy)
  selected.value += 1
  schedulePreview()
}

function removeBlock(index: number) {
  if (!blocks.value.length) return
  remember()
  blocks.value.splice(index, 1)
  selected.value = Math.max(0, Math.min(selected.value, blocks.value.length - 1))
  schedulePreview()
}

/** Порядок в списке — порядок отрисовки: последний блок ложится поверх соседей. */
function move(index: number, delta: number) {
  const next = index + delta
  if (next < 0 || next >= blocks.value.length) return
  remember()
  const [block] = blocks.value.splice(index, 1)
  blocks.value.splice(next, 0, block)
  selected.value = next
  schedulePreview()
}

async function resetLayout() {
  if (!settings.value) return
  remember()
  settings.value.label_layout = await api.labelLayoutDefault()
  selected.value = 0
  schedulePreview()
}

async function save() {
  if (!settings.value) return
  saving.value = true
  try {
    settings.value = await api.saveSettings(settings.value)
    savedState = snapshot()
    ElMessage.success(t('admin.settings.saved'))
  } catch {
    ElMessage.error(t('admin.settings.saveFailed'))
  } finally {
    saving.value = false
  }
}

// --- клавиатура -------------------------------------------------------------

let nudging = false
let nudgeTimer: number | undefined

/**
 * Стрелками блок ставится точнее, чем мышью: шаг 0.5 мм, с Shift — 5 мм. Поля со
 * значениями остаются, но подгонять положение числами в двух полях мучительно.
 */
function onKey(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  if (target && /^(INPUT|TEXTAREA)$/.test(target.tagName)) return
  const ctrl = event.ctrlKey || event.metaKey

  if (ctrl && event.key.toLowerCase() === 'z') {
    event.preventDefault()
    return event.shiftKey ? redo() : undo()
  }
  if (ctrl && event.key.toLowerCase() === 'y') {
    event.preventDefault()
    return redo()
  }
  if (ctrl && event.key.toLowerCase() === 'd') {
    event.preventDefault()
    return duplicate()
  }
  if (!current.value) return
  if (event.key === 'Delete') {
    event.preventDefault()
    return removeBlock(selected.value)
  }

  const step = event.shiftKey ? 5 : 0.5
  const moves: Record<string, [number, number]> = {
    ArrowLeft: [-step, 0],
    ArrowRight: [step, 0],
    ArrowUp: [0, -step],
    ArrowDown: [0, step],
  }
  const delta = moves[event.key]
  if (!delta) return
  event.preventDefault()
  // Серия нажатий подряд — одна правка в истории: иначе отмена шла бы по полшага.
  if (!nudging) remember()
  nudging = true
  window.clearTimeout(nudgeTimer)
  nudgeTimer = window.setTimeout(() => (nudging = false), 600)
  current.value.x = clamp(current.value.x + delta[0], 0, widthMm.value - 2)
  current.value.y = clamp(current.value.y + delta[1], 0, heightMm.value - 2)
  schedulePreview()
}

// --- загрузка и уход со страницы --------------------------------------------

function warnUnsaved(event: BeforeUnloadEvent) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}

onMounted(async () => {
  const [cfg, items] = await Promise.all([api.settings(), api.products()])
  settings.value = cfg
  products.value = items
  savedState = snapshot()
  // Товар выбираем после того, как список опций отрисован: заданный раньше, он
  // остаётся выбранным, но подпись в поле пустует — Element запоминает её в момент
  // присваивания, а запоминать ещё нечего.
  await nextTick()
  sampleId.value = items[0]?.id ?? null
  await refreshPreview()
  window.addEventListener('keydown', onKey)
  window.addEventListener('beforeunload', warnUnsaved)
})

onBeforeUnmount(() => {
  window.clearTimeout(previewTimer)
  window.clearTimeout(nudgeTimer)
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('beforeunload', warnUnsaved)
  if (lastUrl) URL.revokeObjectURL(lastUrl)
})

// Уход с вкладки с несохранённой раскладкой — самая обидная потеря: работа исчезает
// молча, потому что соседний пункт меню в одном клике.
onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm(t('admin.label.leaveText'), t('admin.label.leaveTitle'), {
      confirmButtonText: t('admin.label.leaveDrop'),
      cancelButtonText: t('admin.label.leaveStay'),
      type: 'warning',
    })
    return true
  } catch {
    return false
  }
})

watch([sampleId, sampleWeight], schedulePreview)
watch(
  () => settings.value?.label_layout,
  () => schedulePreview(),
  { deep: true },
)
</script>

<template>
  <div class="label-view">
    <Teleport v-if="settings" to="#admin-actions" defer>
      <el-button-group>
        <el-button :disabled="!history.length" :title="t('admin.label.undo')" @click="undo">
          ↶
        </el-button>
        <el-button :disabled="!future.length" :title="t('admin.label.redo')" @click="redo">
          ↷
        </el-button>
      </el-button-group>
      <el-button plain @click="resetLayout">{{ t('admin.label.reset') }}</el-button>
      <el-button type="primary" :loading="saving" @click="save">
        {{ t('admin.settings.save') }}<span v-if="dirty" class="dot">•</span>
      </el-button>
    </Teleport>

    <el-card v-if="settings" shadow="never" class="card preview-card">
      <template #header>{{ t('admin.label.preview') }}</template>

      <div class="sample">
        <el-select v-model="sampleId" filterable class="sample-product">
          <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-input-number v-model="sampleWeight" :min="0" :max="15000" :step="100" />
        <span class="hint">{{ t('admin.label.sampleHint') }}</span>
      </div>

      <!-- Лист этикетки: пропорции держит сам растр, поэтому рамки блоков считаются
           в процентах и переживают любое масштабирование окна. -->
      <div
        ref="sheet"
        class="sheet"
        @pointermove="onDrag"
        @pointerup="onDrop"
        @pointercancel="onDrop"
      >
        <img v-if="previewUrl" :src="previewUrl" class="paper" alt="" draggable="false" />

        <!-- Направляющие видно ровно в тот момент, когда блок к ним пристал -->
        <div
          v-for="(g, i) in guides.x"
          :key="`x${i}`"
          class="guide guide-x"
          :style="{ left: `${(g / widthMm) * 100}%` }"
        ></div>
        <div
          v-for="(g, i) in guides.y"
          :key="`y${i}`"
          class="guide guide-y"
          :style="{ top: `${(g / heightMm) * 100}%` }"
        ></div>

        <div
          v-for="(block, index) in blocks"
          :key="index"
          class="frame"
          :class="{ on: index === selected, off: !block.visible, outside: outside(block) }"
          :style="frame(block)"
          @pointerdown="onGrab(index, $event)"
        >
          <span class="tag">{{ blockTitle(block) }}</span>
        </div>
      </div>

      <p class="hint keys">{{ t('admin.label.keysHint') }}</p>
      <p v-if="outsideCount" class="warn">
        {{ t('admin.label.outside', { count: outsideCount }) }}
      </p>
    </el-card>

    <el-card v-if="settings" shadow="never" class="card">
      <template #header>{{ t('admin.label.blocks') }}</template>

      <div class="list">
        <button
          v-for="(block, index) in blocks"
          :key="index"
          class="row"
          :class="{ on: index === selected, outside: outside(block) }"
          @click="selected = index"
        >
          <span class="row-name">{{ blockTitle(block) }}</span>
          <span class="row-pos">{{ block.x }} × {{ block.y }} мм</span>
        </button>
      </div>

      <div class="list-actions">
        <el-button size="small" @click="addBlock">{{ t('admin.label.add') }}</el-button>
        <el-button size="small" :disabled="!blocks.length" @click="duplicate">
          {{ t('admin.label.duplicate') }}
        </el-button>
        <el-button size="small" :disabled="!blocks.length" @click="move(selected, -1)">↑</el-button>
        <el-button size="small" :disabled="!blocks.length" @click="move(selected, 1)">↓</el-button>
        <el-button
          size="small"
          type="danger"
          plain
          :disabled="!blocks.length"
          @click="removeBlock(selected)"
        >
          {{ t('admin.label.remove') }}
        </el-button>
      </div>

      <el-form v-if="current" label-width="150px" class="props" @change="remember">
        <el-form-item :label="t('admin.label.kind.title')">
          <el-select v-model="current.kind">
            <el-option
              v-for="kind in KINDS"
              :key="kind"
              :label="t(`admin.label.kind.${kind}`)"
              :value="kind"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="current.kind === 'text'" :label="t('admin.label.text')">
          <el-input v-model="current.text" maxlength="60" />
        </el-form-item>
        <el-form-item :label="t('admin.label.position')">
          <el-input-number v-model="current.x" :min="0" :max="widthMm" :step="0.5" />
          <el-input-number v-model="current.y" :min="0" :max="heightMm" :step="0.5" />
        </el-form-item>
        <el-form-item :label="t('admin.label.size')">
          <el-input-number v-model="current.width" :min="0" :max="widthMm" :step="0.5" />
          <el-input-number v-model="current.height" :min="0" :max="heightMm" :step="0.5" />
          <div class="hint">{{ t('admin.label.sizeHint') }}</div>
        </el-form-item>
        <el-form-item v-if="current.kind !== 'line'" :label="t('admin.label.font')">
          <el-input-number v-model="current.size" :min="8" :max="96" />
          <el-checkbox v-model="current.bold">{{ t('admin.label.bold') }}</el-checkbox>
        </el-form-item>
        <el-form-item v-if="current.kind !== 'line'" :label="t('admin.label.align')">
          <el-radio-group v-model="current.align">
            <el-radio-button value="left">←</el-radio-button>
            <el-radio-button value="center">↔</el-radio-button>
            <el-radio-button value="right">→</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          v-if="['name', 'composition', 'text'].includes(current.kind)"
          :label="t('admin.label.lines')"
        >
          <el-input-number v-model="current.lines" :min="1" :max="6" />
        </el-form-item>
        <el-form-item :label="t('admin.label.extras')">
          <el-checkbox v-model="current.caption">{{ t('admin.label.caption') }}</el-checkbox>
          <el-checkbox v-model="current.box">{{ t('admin.label.box') }}</el-checkbox>
          <el-checkbox v-model="current.visible">{{ t('admin.label.visible') }}</el-checkbox>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.label-view {
  display: grid;
  grid-template-columns: minmax(420px, 1fr) minmax(380px, 460px);
  gap: 20px;
  align-items: start;
}

.sample {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.sample-product {
  width: 260px;
}

/* Лист держит пропорции этикетки: рамки блоков позиционируются в процентах от него */
.sheet {
  position: relative;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  touch-action: none;
}

.paper {
  display: block;
  width: 100%;
  image-rendering: pixelated;
}

.frame {
  position: absolute;
  border: 1px dashed rgb(64 158 255 / 70%);
  background: rgb(64 158 255 / 6%);
  cursor: grab;
}

.frame.on {
  border: 2px solid #409eff;
  background: rgb(64 158 255 / 14%);
}

.frame.off {
  border-style: dotted;
  opacity: 0.4;
}

.frame.outside {
  border-color: #f56c6c;
  background: rgb(245 108 108 / 12%);
}

/* Направляющие рисуются поверх листа и живут ровно один кадр перетаскивания */
.guide {
  position: absolute;
  background: #f56c6c;
  pointer-events: none;
}

.guide-x {
  top: 0;
  bottom: 0;
  width: 1px;
}

.guide-y {
  left: 0;
  right: 0;
  height: 1px;
}

.tag {
  position: absolute;
  top: -2px;
  left: 2px;
  font-size: 10px;
  line-height: 1.2;
  color: #1d4f86;
  background: rgb(255 255 255 / 80%);
  padding: 0 3px;
  border-radius: 3px;
  pointer-events: none;
  white-space: nowrap;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 260px;
  overflow: auto;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  font: inherit;
  text-align: left;
  background: var(--el-fill-color-light);
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
}

.row.on {
  border-color: #409eff;
  background: rgb(64 158 255 / 10%);
}

.row.outside .row-pos {
  color: #f56c6c;
}

.row-pos {
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.list-actions {
  display: flex;
  gap: 8px;
  margin: 12px 0 4px;
  flex-wrap: wrap;
}

.props {
  margin-top: 8px;
}

.props :deep(.el-input-number) {
  margin-right: 8px;
}

.hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
}

.keys {
  margin: 10px 0 0;
}

.warn {
  margin: 6px 0 0;
  font-size: 12px;
  color: #f56c6c;
}

/* Точка у «Сохранить» — единственный признак несохранённой правки: отдельная
   надпись рядом с кнопкой читалась бы как ещё одна кнопка. */
.dot {
  margin-left: 6px;
  font-size: 18px;
  line-height: 1;
}
</style>
