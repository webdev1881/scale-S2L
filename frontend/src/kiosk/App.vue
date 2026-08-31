<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { formatKg, formatMoney, localeTag } from '@/shared/format'
import { elementLocale, setLocale, translateError } from '@/shared/i18n'
import type { Category, DeviceSettings, Product } from '@/shared/types'
import { useWeightStore } from '@/shared/weight'

import CategoryGrid from './components/CategoryGrid.vue'
import Numpad from './components/Numpad.vue'
import ProductGrid from './components/ProductGrid.vue'
import SplashScreen from './components/SplashScreen.vue'
import WeightPanel from './components/WeightPanel.vue'

const { t, locale } = useI18n()
const weight = useWeightStore()

const booting = ref(true)

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const settings = ref<DeviceSettings | null>(null)

const search = ref('')
const openedCategory = ref<Category | null>(null)
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

const searching = computed(() => search.value.trim().length > 0)
/** Группы показываются, пока покупатель не провалился внутрь и не начал искать. */
const showCategories = computed(() => !searching.value && openedCategory.value === null)

const visibleProducts = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return products.value.filter((product) => {
    if (
      !searching.value &&
      openedCategory.value &&
      product.category !== openedCategory.value.name
    ) {
      return false
    }
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
  if (!selected.value) return t('blocked.selectProduct')
  if (selected.value.unit === 'piece') return null
  if (weight.reading.error) return translateError(weight.reading.error)
  if (netG.value < minWeight.value) return t('blocked.putGoods')
  if (requireStable.value && !weight.reading.stable) return t('blocked.waitStable')
  return null
})

async function loadCatalog() {
  const [items, cats, cfg] = await Promise.all([api.products(), api.categories(), api.settings()])
  products.value = items
  categories.value = cats
  settings.value = cfg
  // Язык задаётся на устройстве, а не в браузере покупателя.
  setLocale(cfg.language)
}

function openCategory(category: Category) {
  openedCategory.value = category
  selected.value = null
}

function backToCategories() {
  openedCategory.value = null
  selected.value = null
  search.value = ''
}

function selectProduct(product: Product) {
  selected.value = product
  showNumpad.value = false
}

function findByPlu() {
  const plu = Number(pluInput.value)
  const found = products.value.find((product) => product.plu === plu)
  if (!found) {
    ElMessage.warning(t('kiosk.pluNotFound', { plu: pluInput.value }))
    return
  }
  // Проваливаемся в группу найденного товара, чтобы покупатель понимал, где он.
  openedCategory.value =
    categories.value.find((category) => category.name === found.category) ?? null
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
    const message =
      error instanceof ApiError ? translateError(error.message) : t('kiosk.printFailed')
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
  openedCategory.value = null
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

watch([search, openedCategory, selected], bumpIdle)

// Заголовок вкладки — тоже часть интерфейса, он меняется вместе с языком.
watch(locale, () => (document.title = t('title.kiosk')), { immediate: true })
</script>

<template>
  <el-config-provider :locale="elementLocale(locale)">
    <SplashScreen v-if="booting" @done="booting = false" />

    <div class="kiosk">
      <header class="topbar">
        <button v-if="!showCategories" class="back" @click="backToCategories">
          <span class="arrow">←</span> {{ t('kiosk.allGroups') }}
        </button>
        <div v-else class="crumb">{{ t('kiosk.chooseGroup') }}</div>

        <div class="status">
          <span class="dot" :class="{ ok: weight.connected }"></span>
          <span class="conn">{{
            weight.connected ? t('kiosk.connected') : t('kiosk.disconnected')
          }}</span>
          <span class="clock">{{ clock.toLocaleTimeString(localeTag()) }}</span>
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

        <section class="catalog">
          <div class="search-row">
            <input
              v-model="search"
              class="search"
              type="text"
              :placeholder="t('kiosk.searchPlaceholder')"
              autocomplete="off"
            />
            <button class="toggle" :class="{ on: showNumpad }" @click="showNumpad = !showNumpad">
              123
            </button>
          </div>

          <CategoryGrid v-if="showCategories" :categories="categories" @open="openCategory" />
          <ProductGrid
            v-else
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
            <div class="pick-name">{{ selected.name }}</div>
            <div class="pick-meta">
              {{ formatMoney(selected.price) }} {{ currency }}/{{
                selected.unit === 'piece' ? t('kiosk.perPiece') : t('kiosk.perKg')
              }}
              <template v-if="selected.unit === 'weight'">
                · {{ formatKg(netG) }} {{ t('kiosk.perKg') }}
              </template>
              <template v-if="selected.tare_g">
                · {{ t('kiosk.tare') }} {{ selected.tare_g }} г
              </template>
            </div>
          </template>
          <div v-else class="pick-empty">{{ t('kiosk.noProduct') }}</div>
        </div>

        <div class="sum">
          <span class="sum-label">{{ t('kiosk.total') }}</span>
          <span class="sum-value">{{ formatMoney(total) }} {{ currency }}</span>
        </div>

        <button class="print" :disabled="!!printBlockReason || printing" @click="print">
          <template v-if="printing">{{ t('kiosk.printing') }}</template>
          <template v-else-if="printBlockReason">{{ printBlockReason }}</template>
          <template v-else>{{ t('kiosk.print') }}</template>
        </button>
      </footer>

      <el-dialog
        v-model="labelVisible"
        :title="t('kiosk.takeLabel')"
        width="560px"
        align-center
        @close="closeLabel"
      >
        <img v-if="labelUrl" :src="labelUrl" class="label-img" alt="" />
        <p v-else class="label-note">{{ t('kiosk.sentToPrinter') }}</p>
        <template #footer>
          <el-button type="primary" size="large" @click="closeLabel">
            {{ t('kiosk.done') }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </el-config-provider>
</template>

<style scoped>
.kiosk {
  display: grid;
  grid-template-rows: auto 1fr auto;
  height: 100%;
  gap: 12px;
  padding: 12px;
  /* Киоск не прокручивается целиком: скроллится только сетка карточек */
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 14px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
}

.crumb {
  font-size: 18px;
  font-weight: 600;
  color: var(--s2l-muted);
}

.back {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 52px;
  padding: 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: var(--s2l-ink);
  background: #eef1f5;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.back:active {
  background: #dfe4ea;
}

.arrow {
  font-size: 22px;
  line-height: 1;
}

/* Индикатор, подпись и часы — одной строкой */
.status {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  color: var(--s2l-muted);
  white-space: nowrap;
}

.dot {
  flex: none;
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
  grid-template-columns: minmax(300px, 32%) 1fr;
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

.catalog {
  display: grid;
  grid-template-rows: auto 1fr;
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
