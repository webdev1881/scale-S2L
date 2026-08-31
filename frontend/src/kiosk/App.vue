<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import { api, ApiError } from '@/shared/api'
import { formatKg, formatMoney } from '@/shared/format'
import type { DeviceSettings, Product } from '@/shared/types'
import { useWeightStore } from '@/shared/weight'

import Numpad from './components/Numpad.vue'
import ProductGrid from './components/ProductGrid.vue'
import WeightPanel from './components/WeightPanel.vue'

const weight = useWeightStore()

const products = ref<Product[]>([])
const categories = ref<string[]>([])
const settings = ref<DeviceSettings | null>(null)

const search = ref('')
const activeCategory = ref('')
const selected = ref<Product | null>(null)
const pluInput = ref('')
const showNumpad = ref(false)

const printing = ref(false)
const labelUrl = ref<string | null>(null)
const labelVisible = ref(false)

const clock = ref(new Date())
let clockTimer: number | undefined
let idleTimer: number | undefined
let labelTimer: number | undefined

const currency = computed(() => settings.value?.currency ?? '₴')
const minWeight = computed(() => settings.value?.min_print_weight_g ?? 5)
const requireStable = computed(() => settings.value?.require_stable ?? true)

const visibleProducts = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return products.value.filter((product) => {
    if (activeCategory.value && product.category !== activeCategory.value) return false
    if (!needle) return true
    return product.name.toLowerCase().includes(needle) || String(product.plu).startsWith(needle)
  })
})

const netG = computed(() => {
  const tare = selected.value?.tare_g ?? 0
  return Math.max(weight.reading.net_g - tare, 0)
})

const total = computed(() => {
  if (!selected.value) return 0
  if (selected.value.unit === 'piece') return selected.value.price
  return (selected.value.price * netG.value) / 1000
})

/** Почему кнопка печати недоступна — текст показывается прямо на кнопке. */
const printBlockReason = computed(() => {
  if (!selected.value) return 'Выберите товар'
  if (selected.value.unit === 'piece') return null
  if (weight.reading.error) return weight.reading.error
  if (netG.value < minWeight.value) return 'Положите товар на платформу'
  if (requireStable.value && !weight.reading.stable) return 'Дождитесь стабилизации'
  return null
})

async function loadCatalog() {
  const [items, cats, cfg] = await Promise.all([api.products(), api.categories(), api.settings()])
  products.value = items
  categories.value = cats
  settings.value = cfg
}

function selectProduct(product: Product) {
  selected.value = product
  showNumpad.value = false
}

function findByPlu() {
  const plu = Number(pluInput.value)
  const found = products.value.find((product) => product.plu === plu)
  if (!found) {
    ElMessage.warning('Товар с PLU ' + pluInput.value + ' не найден')
    return
  }
  selectProduct(found)
  pluInput.value = ''
}

async function print() {
  if (!selected.value || printBlockReason.value) return
  printing.value = true
  try {
    const result = await api.print(selected.value.id)
    labelUrl.value = result.label_url
    labelVisible.value = true
    // Этикетку показываем ненадолго: киоск обязан сам вернуться в исходное состояние.
    window.clearTimeout(labelTimer)
    labelTimer = window.setTimeout(closeLabel, 8000)
  } catch (error) {
    const message = error instanceof ApiError ? error.message : 'Ошибка печати'
    ElMessage({ message, type: 'warning', duration: 4000 })
  } finally {
    printing.value = false
  }
}

function closeLabel() {
  labelVisible.value = false
  labelUrl.value = null
  reset()
}

function reset() {
  selected.value = null
  search.value = ''
  activeCategory.value = ''
  pluInput.value = ''
  showNumpad.value = false
}

function bumpIdle() {
  window.clearTimeout(idleTimer)
  const seconds = settings.value?.kiosk_idle_reset_s ?? 45
  idleTimer = window.setTimeout(() => {
    if (!labelVisible.value) reset()
  }, seconds * 1000)
}

onMounted(async () => {
  weight.connect()
  await loadCatalog()
  clockTimer = window.setInterval(() => (clock.value = new Date()), 1000)
  window.addEventListener('pointerdown', bumpIdle)
  bumpIdle()
})

onUnmounted(() => {
  weight.disconnect()
  window.clearInterval(clockTimer)
  window.clearTimeout(idleTimer)
  window.clearTimeout(labelTimer)
  window.removeEventListener('pointerdown', bumpIdle)
})

watch([search, activeCategory, selected], bumpIdle)
</script>

<template>
  <div class="kiosk">
    <header class="topbar">
      <div class="brand">{{ settings?.store_name ?? 'Aurora S2L' }}</div>
      <div class="right">
        <span class="dot" :class="{ ok: weight.connected }"></span>
        <span class="conn">{{ weight.connected ? 'Весы подключены' : 'Нет связи' }}</span>
        <span class="clock">{{ clock.toLocaleTimeString('ru-RU') }}</span>
      </div>
    </header>

    <main class="body">
      <aside class="left">
        <WeightPanel
          :reading="weight.reading"
          :connected="weight.connected"
          @tare="api.tare()"
          @zero="api.zero()"
        />
        <Numpad
          v-if="showNumpad"
          v-model:value="pluInput"
          class="numpad-block"
          @submit="findByPlu"
        />
      </aside>

      <section class="right">
        <div class="search-row">
          <input
            v-model="search"
            class="search"
            type="text"
            placeholder="Поиск товара или PLU"
            autocomplete="off"
          />
          <button class="toggle" :class="{ on: showNumpad }" @click="showNumpad = !showNumpad">
            123
          </button>
        </div>

        <div class="chips">
          <button :class="{ on: !activeCategory }" @click="activeCategory = ''">Все</button>
          <button
            v-for="category in categories"
            :key="category"
            :class="{ on: activeCategory === category }"
            @click="activeCategory = category"
          >
            {{ category }}
          </button>
        </div>

        <ProductGrid
          :products="visibleProducts"
          :selected-id="selected?.id ?? null"
          :currency="currency"
          @select="selectProduct"
        />
      </section>
    </main>

    <footer class="bottom">
      <div class="pick">
        <template v-if="selected">
          <div class="pick-name">{{ selected.emoji }} {{ selected.name }}</div>
          <div class="pick-meta">
            {{ formatMoney(selected.price) }} {{ currency }}/{{
              selected.unit === 'piece' ? 'шт' : 'кг'
            }}
            <template v-if="selected.unit === 'weight'"> · {{ formatKg(netG) }} кг</template>
            <template v-if="selected.tare_g"> · тара {{ selected.tare_g }} г</template>
          </div>
        </template>
        <div v-else class="pick-empty">Товар не выбран</div>
      </div>

      <div class="sum">
        <span class="sum-label">К оплате</span>
        <span class="sum-value">{{ formatMoney(total) }} {{ currency }}</span>
      </div>

      <button class="print" :disabled="!!printBlockReason || printing" @click="print">
        <template v-if="printing">Печать…</template>
        <template v-else-if="printBlockReason">{{ printBlockReason }}</template>
        <template v-else>Напечатать этикетку</template>
      </button>
    </footer>

    <el-dialog
      v-model="labelVisible"
      title="Заберите этикетку"
      width="560px"
      align-center
      @close="closeLabel"
    >
      <img v-if="labelUrl" :src="labelUrl" class="label-img" alt="Этикетка" />
      <p v-else class="label-note">Этикетка отправлена на принтер</p>
      <template #footer>
        <el-button type="primary" size="large" @click="closeLabel">Готово</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kiosk {
  display: grid;
  grid-template-rows: auto 1fr auto;
  height: 100%;
  gap: 12px;
  padding: 12px;
  /* Киоск не прокручивается целиком: скроллится только сетка товаров */
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
}

.brand {
  font-size: 21px;
  font-weight: 700;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--s2l-muted);
  font-size: 15px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--s2l-danger);
}

.dot.ok {
  background: var(--s2l-accent);
}

.clock {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--s2l-ink);
}

.body {
  display: grid;
  grid-template-columns: minmax(320px, 34%) 1fr;
  gap: 12px;
  min-height: 0;
}

.left {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.numpad-block {
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
  padding: 14px;
}

.right {
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 12px;
  min-height: 0;
}

.search-row {
  display: flex;
  gap: 10px;
}

.search {
  flex: 1;
  height: 62px;
  padding: 0 18px;
  font-size: 20px;
  border: none;
  border-radius: 12px;
  background: var(--s2l-panel);
  outline: none;
}

.toggle {
  width: 76px;
  font-size: 19px;
  font-weight: 700;
  border: none;
  border-radius: 12px;
  background: var(--s2l-panel);
  cursor: pointer;
}

.toggle.on {
  background: var(--s2l-accent);
  color: #fff;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chips button {
  min-height: 46px;
  padding: 0 18px;
  font-size: 16px;
  border: none;
  border-radius: 23px;
  background: var(--s2l-panel);
  cursor: pointer;
}

.chips button.on {
  background: var(--s2l-accent);
  color: #fff;
}

.bottom {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 18px;
  padding: 12px 18px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
}

.pick-name {
  font-size: 21px;
  font-weight: 600;
}

.pick-meta,
.pick-empty {
  font-size: 15px;
  color: var(--s2l-muted);
}

.sum {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.sum-label {
  font-size: 14px;
  color: var(--s2l-muted);
}

.sum-value {
  font-size: 38px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.print {
  min-width: 330px;
  min-height: 84px;
  padding: 0 26px;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  background: var(--s2l-accent);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.print:active:not(:disabled) {
  background: var(--s2l-accent-dark);
}

.print:disabled {
  background: #c4ccd6;
  cursor: default;
}

.label-img {
  display: block;
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
}

.label-note {
  text-align: center;
  color: var(--s2l-muted);
}
</style>
