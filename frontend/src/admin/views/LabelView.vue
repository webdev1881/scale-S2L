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
import { ElMessage } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { api } from '@/shared/api'
import type { DeviceSettings, LabelBlock, Product } from '@/shared/types'

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

/** Что печатает блок — на языке оператора, а не на именах полей. */
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

// --- превью -----------------------------------------------------------------

let previewTimer: number | undefined
let lastUrl = ''

/** Перерисовка идёт с задержкой: пока блок тянут пальцем, кадров десятки. */
function schedulePreview() {
  window.clearTimeout(previewTimer)
  previewTimer = window.setTimeout(refreshPreview, 180)
}

async function refreshPreview() {
  if (!settings.value || !sampleId.value) return
  try {
    const blob = await api.labelPreview({
      product_id: sampleId.value,
      weight_g: sampleWeight.value,
      layout: settings.value.label_layout,
    })
    // Прежний объект отпускаем сами: их тут делаются сотни за сессию правки.
    if (lastUrl) URL.revokeObjectURL(lastUrl)
    lastUrl = URL.createObjectURL(blob)
    previewUrl.value = lastUrl
  } catch {
    ElMessage.warning(t('admin.label.previewFailed'))
  }
}

// --- перетаскивание ---------------------------------------------------------

let drag: { index: number; x: number; y: number; blockX: number; blockY: number } | null = null

function mmPerPx() {
  const box = sheet.value?.getBoundingClientRect()
  return box && box.width ? widthMm.value / box.width : 0
}

function onGrab(index: number, event: PointerEvent) {
  const block = blocks.value[index]
  selected.value = index
  drag = { index, x: event.clientX, y: event.clientY, blockX: block.x, blockY: block.y }
  ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
}

function onDrag(event: PointerEvent) {
  if (!drag) return
  const scale = mmPerPx()
  const block = blocks.value[drag.index]
  block.x = clamp(drag.blockX + (event.clientX - drag.x) * scale, 0, widthMm.value - 2)
  block.y = clamp(drag.blockY + (event.clientY - drag.y) * scale, 0, heightMm.value - 2)
  schedulePreview()
}

function onDrop() {
  drag = null
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

// --- правка списка ----------------------------------------------------------

function addBlock() {
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

function removeBlock(index: number) {
  blocks.value.splice(index, 1)
  selected.value = Math.max(0, Math.min(selected.value, blocks.value.length - 1))
  schedulePreview()
}

/** Порядок в списке — порядок отрисовки: последний блок ложится поверх соседей. */
function move(index: number, delta: number) {
  const next = index + delta
  if (next < 0 || next >= blocks.value.length) return
  const [block] = blocks.value.splice(index, 1)
  blocks.value.splice(next, 0, block)
  selected.value = next
  schedulePreview()
}

async function resetLayout() {
  const fresh = await api.labelLayoutDefault()
  if (!settings.value) return
  settings.value.label_layout = fresh
  selected.value = 0
  schedulePreview()
}

async function save() {
  if (!settings.value) return
  saving.value = true
  try {
    settings.value = await api.saveSettings(settings.value)
    ElMessage.success(t('admin.settings.saved'))
  } catch {
    ElMessage.error(t('admin.settings.saveFailed'))
  } finally {
    saving.value = false
  }
}

// --- загрузка ---------------------------------------------------------------

onMounted(async () => {
  const [cfg, items] = await Promise.all([api.settings(), api.products()])
  settings.value = cfg
  products.value = items
  // Товар выбираем после того, как список опций отрисован: заданный раньше, он
  // остаётся выбранным, но подпись в поле пустует — Element запоминает её в момент
  // присваивания, а запоминать ещё нечего.
  await nextTick()
  sampleId.value = items[0]?.id ?? null
  await refreshPreview()
})

onBeforeUnmount(() => {
  window.clearTimeout(previewTimer)
  if (lastUrl) URL.revokeObjectURL(lastUrl)
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
      <el-button plain @click="resetLayout">{{ t('admin.label.reset') }}</el-button>
      <el-button type="primary" :loading="saving" @click="save">{{ t('admin.settings.save') }}</el-button>
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
      <div ref="sheet" class="sheet" @pointermove="onDrag" @pointerup="onDrop" @pointercancel="onDrop">
        <img v-if="previewUrl" :src="previewUrl" class="paper" alt="" draggable="false" />
        <div
          v-for="(block, index) in blocks"
          :key="index"
          class="frame"
          :class="{ on: index === selected, off: !block.visible }"
          :style="frame(block)"
          @pointerdown="onGrab(index, $event)"
        >
          <span class="tag">{{ blockTitle(block) }}</span>
        </div>
      </div>
    </el-card>

    <el-card v-if="settings" shadow="never" class="card">
      <template #header>{{ t('admin.label.blocks') }}</template>

      <div class="list">
        <button
          v-for="(block, index) in blocks"
          :key="index"
          class="row"
          :class="{ on: index === selected }"
          @click="selected = index"
        >
          <span class="row-name">{{ blockTitle(block) }}</span>
          <span class="row-pos">{{ block.x }} × {{ block.y }} мм</span>
        </button>
      </div>

      <div class="list-actions">
        <el-button size="small" @click="addBlock">{{ t('admin.label.add') }}</el-button>
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

      <el-form v-if="current" label-width="150px" class="props">
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
        <el-form-item v-if="['name', 'composition', 'text'].includes(current.kind)" :label="t('admin.label.lines')">
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

.row-pos {
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.list-actions {
  display: flex;
  gap: 8px;
  margin: 12px 0 4px;
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
</style>
