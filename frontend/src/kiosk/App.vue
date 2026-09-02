<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { formatKg, formatMoney, localeTag } from '@/shared/format'
import { elementLocale, setLocale, translateError } from '@/shared/i18n'
import { applyTheme, rememberSplash, storedSplashMs } from '@/shared/boot'
import type { Category, DeviceSettings, Product } from '@/shared/types'
import { useWeightStore } from '@/shared/weight'

import CategoryGrid from './components/CategoryGrid.vue'
import Keyboard from './components/Keyboard.vue'
import Numpad from './components/Numpad.vue'
import Pager from './components/Pager.vue'
import ProductGrid from './components/ProductGrid.vue'
import SplashScreen from './components/SplashScreen.vue'
import WeightPanel from './components/WeightPanel.vue'

const { t, locale } = useI18n()
const weight = useWeightStore()

// Длительность заставки берётся из настроек прошлого запуска: сервер ответит
// уже после того, как заставка стартует. Ноль — заставку не показываем вовсе.
const splashMs = ref(storedSplashMs())
const booting = ref(splashMs.value > 0)

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const settings = ref<DeviceSettings | null>(null)

const search = ref('')
const openedCategory = ref<Category | null>(null)
const page = ref(0)
const selected = ref<Product | null>(null)
const pluInput = ref('')
const showNumpad = ref(false)
const keyboardOpen = ref(false)
const searchInput = ref<HTMLInputElement | null>(null)

const printing = ref(false)
const labelUrl = ref<string | null>(null)
const labelVisible = ref(false)

const clock = ref(new Date())
let clockTimer: number | undefined
let idleTimer: number | undefined
let labelTimer: number | undefined

const currency = computed(() => settings.value?.currency ?? '₴')

/**
 * Масштабы подписей и доля фото уезжают в CSS-переменные корня киоска: вёрстка
 * считает размеры от них, а значения приходят из настроек прибора. Без этого
 * каждый размер пришлось бы пробрасывать пропом до каждой карточки.
 */
const uiScales = computed<Record<string, string>>(() => ({
  '--ui-weight': String(settings.value?.ui_scale_weight ?? 1),
  '--ui-group-title': String(settings.value?.ui_scale_group_title ?? 1),
  '--ui-name': String(settings.value?.ui_scale_product_name ?? 1),
  '--ui-price': String(settings.value?.ui_scale_product_price ?? 1),
  '--ui-code': String(settings.value?.ui_scale_product_code ?? 1),
  '--ui-footer': String(settings.value?.ui_scale_footer ?? 1),
  '--ui-photo-group': String(settings.value?.ui_photo_group ?? 60),
  '--ui-photo-product': String(settings.value?.ui_photo_product ?? 60),
}))
const minWeight = computed(() => settings.value?.min_print_weight_g ?? 5)
const requireStable = computed(() => settings.value?.require_stable ?? true)

const cols = computed(() => settings.value?.grid_cols ?? 4)
const rows = computed(() => settings.value?.grid_rows ?? 2)
/**
 * Открытая клавиатура забирает нижнюю половину экрана. Если оставить прежнее число
 * строк, карточки сожмутся до нечитаемых полосок, поэтому во время набора показываем
 * один ряд — остальное доступно листанием или после «Готово».
 */
const visibleRows = computed(() => (keyboardOpen.value ? 1 : rows.value))
const pageSize = computed(() => cols.value * visibleRows.value)

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

/**
 * Заголовок показывается только там, где он что-то сообщает. На экране групп
 * карточки говорят сами за себя, и подпись над ними — лишний шум.
 */
const catalogTitle = computed(() => {
  if (searching.value) return t('kiosk.searchResults')
  if (openedCategory.value) return openedCategory.value.name
  return ''
})

/** Что листаем — зависит от того, показываем группы или товары. */
const pageCount = computed(() => {
  const length = showCategories.value ? categories.value.length : visibleProducts.value.length
  return Math.max(1, Math.ceil(length / pageSize.value))
})

const pagedCategories = computed(() =>
  categories.value.slice(page.value * pageSize.value, (page.value + 1) * pageSize.value),
)

const pagedProducts = computed(() =>
  visibleProducts.value.slice(page.value * pageSize.value, (page.value + 1) * pageSize.value),
)

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
  // Язык и тема задаются на устройстве, а не в браузере покупателя.
  setLocale(cfg.language)
  applyTheme(cfg.theme)
  splashMs.value = rememberSplash(cfg.splash_seconds)
}

/**
 * Перечитываем настройки на возврате к начальному экрану: оператор меняет тему
 * или язык в админке, и киоск подхватывает это сам, без перезапуска сервиса.
 * Опроса по таймеру не заводим — сброс и так случается регулярно.
 */
async function refreshSettings() {
  try {
    const cfg = await api.settings()
    settings.value = cfg
    setLocale(cfg.language)
    applyTheme(cfg.theme)
    rememberSplash(cfg.splash_seconds)
  } catch {
    /* сеть моргнула — киоск продолжает работать на прежних настройках */
  }
}

function openCategory(category: Category) {
  openedCategory.value = category
  selected.value = null
  page.value = 0
}

function backToCategories() {
  openedCategory.value = null
  selected.value = null
  search.value = ''
  page.value = 0
}

function selectProduct(product: Product) {
  selected.value = product
  showNumpad.value = false
  closeKeyboard()
}

const SEARCH_MAX_LENGTH = 40

/** Состояние экрана до начала набора — к нему возвращаемся, если поиск бросили. */
let beforeSearch: { search: string; category: Category | null; page: number } | null = null

function keyPress(char: string) {
  if (search.value.length >= SEARCH_MAX_LENGTH) return
  search.value += char
}

function openKeyboard() {
  if (!keyboardOpen.value) {
    beforeSearch = { search: search.value, category: openedCategory.value, page: page.value }
  }
  keyboardOpen.value = true
  showNumpad.value = false
}

/** Набор завершён осознанно — результаты остаются на экране. */
function closeKeyboard() {
  keyboardOpen.value = false
  beforeSearch = null
  searchInput.value?.blur()
}

/** Поиск брошен — возвращаем экран туда, откуда покупатель начал набирать. */
function cancelKeyboard() {
  if (beforeSearch) {
    search.value = beforeSearch.search
    openedCategory.value = beforeSearch.category
    page.value = beforeSearch.page
  }
  closeKeyboard()
}

function onPointerDown(event: PointerEvent) {
  if (!keyboardOpen.value) return
  const target = event.target as HTMLElement | null
  if (!target) return
  if (target.closest('.keyboard') || target.closest('.search-field')) return
  // Касание самих результатов — это продолжение поиска, а не отказ от него.
  if (target.closest('.catalog')) return closeKeyboard()
  cancelKeyboard()
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
  page.value = 0
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
  void refreshSettings()
  selected.value = null
  search.value = ''
  openedCategory.value = null
  page.value = 0
  pluInput.value = ''
  showNumpad.value = false
  keyboardOpen.value = false
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
  window.addEventListener('pointerdown', onPointerDown, true)
  bumpIdle()
})

onUnmounted(() => {
  weight.disconnect()
  window.clearInterval(clockTimer)
  window.clearTimeout(idleTimer)
  window.clearTimeout(labelTimer)
  window.removeEventListener('pointerdown', bumpIdle)
  window.removeEventListener('pointerdown', onPointerDown, true)
})

watch([search, openedCategory, selected], bumpIdle)

// Ввод в поиск или смена настроек сетки могут оставить нас на несуществующей странице.
watch([search, pageSize], () => (page.value = 0))
watch(pageCount, (count) => {
  if (page.value > count - 1) page.value = count - 1
})

// Заголовок вкладки — тоже часть интерфейса, он меняется вместе с языком.
watch(locale, () => (document.title = t('title.kiosk')), { immediate: true })
</script>

<template>
  <el-config-provider :locale="elementLocale(locale)">
    <SplashScreen v-if="booting" :duration-ms="splashMs" @done="booting = false" />

    <div class="kiosk" :style="uiScales">
      <!-- Весы занимают всю высоту экрана и не сжимаются ничем: ни шапкой,
           ни выехавшей клавиатурой. Это единственный блок, за которым покупатель
           следит непрерывно. -->
      <aside class="scale">
        <WeightPanel
          :reading="weight.reading"
          :connected="weight.connected"
          :clock="clock.toLocaleTimeString(localeTag())"
          :currency="currency"
          :product="selected"
          :total="total"
          @tare="api.tare()"
          @zero="api.zero()"
        />
      </aside>

      <section class="main" :class="{ 'kb-open': keyboardOpen || showNumpad }">
        <!-- Отдельной шапки нет: строка состояния переехала в блок весов, за
             которым покупатель и так следит. Освободившаяся высота отдана карточкам. -->

        <!-- Возврат живёт рядом с заголовком выбора: обе подписи
             про одно и то же — где покупатель находится. Строка сохраняет высоту
             и на верхнем уровне, иначе карточки меняли бы размер между экранами. -->
        <div class="catalog-head">
          <button v-if="!showCategories" class="back" @click="backToCategories">
            <span class="arrow">←</span> {{ t('kiosk.allGroups') }}
          </button>
          <h1 v-if="catalogTitle" class="catalog-title">{{ catalogTitle }}</h1>
        </div>

        <div class="search-row">
            <div class="search-field" :class="{ focused: keyboardOpen }">
              <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="7" />
                <path d="M16.5 16.5 21 21" />
              </svg>
              <input
                ref="searchInput"
                v-model="search"
                class="search"
                type="text"
                :placeholder="t('kiosk.searchPlaceholder')"
                autocomplete="off"
                @focus="openKeyboard"
              />
              <button v-if="search" class="clear" @click="search = ''">×</button>
            </div>
            <button
              class="toggle"
              :class="{ on: showNumpad }"
              @click="((showNumpad = !showNumpad), (keyboardOpen = false))"
            >
              123
            </button>
          </div>

          <CategoryGrid
            v-if="showCategories"
            :categories="pagedCategories"
            :cols="cols"
            :rows="visibleRows"
            @open="openCategory"
          />
          <ProductGrid
            v-else
            :products="pagedProducts"
            :selected-id="selected?.id ?? null"
            :currency="currency"
            :cols="cols"
            :rows="visibleRows"
            @select="selectProduct"
          />

        <Pager v-if="pageCount > 1" v-model:page="page" :pages="pageCount" />

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

        <!-- Экранный ввод выезжает внутри правой колонки, поэтому весы остаются
             видны целиком, а сжимается только сетка каталога. -->
        <Transition name="kb">
          <Keyboard
            v-if="keyboardOpen"
            class="sheet"
            :has-text="search.length > 0"
            @key="keyPress"
            @backspace="search = search.slice(0, -1)"
            @clear="search = ''"
            @done="closeKeyboard"
          />
          <Numpad
            v-else-if="showNumpad"
            v-model:value="pluInput"
            class="sheet"
            @submit="findByPlu"
          />
        </Transition>
      </section>

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
  /* Две колонки во всю высоту: весы слева, всё остальное справа */
  grid-template-columns: minmax(290px, 29%) 1fr;
  height: 100%;
  gap: 12px;
  padding: 12px;
  /* Киоск не прокручивается целиком: скроллится только сетка карточек */
  overflow: hidden;
}

.scale {
  min-height: 0;
}

.main {
  position: relative;
  display: grid;
  /* возврат с заголовком / поиск / сетка / пагинация / итог */
  grid-template-rows: auto auto 1fr auto auto;
  gap: 10px;
  min-height: 0;
  /* Клавиатура выезжает внутри этой колонки и поджимает только её */
  transition: padding-bottom 0.22s ease;
}

.main.kb-open {
  padding-bottom: var(--s2l-kb-height);
}

/* Строка сохраняет высоту и при пустом содержимом: иначе карточки меняли бы
   размер при переходе между уровнями каталога */
.catalog-head {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 52px;
  padding: 0 4px;
}

/* Возврат — основной путь назад, поэтому он окрашен акцентом, а не выглядит
   вспомогательной серой кнопкой рядом с крупным заголовком */
.back {
  display: flex;
  flex: none;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 0 26px;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  background: var(--s2l-accent);
  border: none;
  border-radius: 14px;
  box-shadow: 0 2px 0 var(--s2l-accent-dark);
  cursor: pointer;
}

.back:active {
  background: var(--s2l-accent-dark);
  box-shadow: none;
  transform: translateY(2px);
}

.arrow {
  font-size: 26px;
  line-height: 1;
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

.catalog-title {
  margin: 0;
  font-size: calc(24px * var(--ui-group-title, 1));
  font-weight: 700;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-row {
  display: flex;
  gap: 10px;
}

/* Поиск — главный элемент экрана после весов, поэтому он крупный,
   с иконкой и заметной подсветкой фокуса. */
.search-field {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  height: 64px;
  padding: 0 18px;
  background: var(--s2l-panel);
  border: 3px solid transparent;
  border-radius: 16px;
  box-shadow: 0 2px 10px var(--s2l-shadow);
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.search-field.focused {
  border-color: var(--s2l-accent);
  box-shadow: 0 4px 18px rgb(31 122 77 / 18%);
}

.search-icon {
  flex: none;
  width: 28px;
  height: 28px;
  fill: none;
  stroke: var(--s2l-muted);
  stroke-width: 2.2;
  stroke-linecap: round;
}

.search-field.focused .search-icon {
  stroke: var(--s2l-accent);
}

.search {
  flex: 1;
  min-width: 0;
  height: 100%;
  font-size: 24px;
  color: var(--s2l-ink);
  background: transparent;
  border: none;
  outline: none;
}

.search::placeholder {
  color: var(--s2l-muted);
}

.clear {
  flex: none;
  width: 46px;
  height: 46px;
  font-size: 28px;
  line-height: 1;
  color: var(--s2l-muted);
  background: var(--s2l-soft);
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.clear:active {
  background: var(--s2l-soft-active);
}

.toggle {
  width: 72px;
  height: 64px;
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
  padding: 10px 16px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
}

.pick-name {
  font-size: calc(24px * var(--ui-footer, 1));
  font-weight: 600;
}

.pick-meta,
.pick-empty {
  font-size: calc(17px * var(--ui-footer, 1));
  color: var(--s2l-muted);
}

.sum {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.sum-label {
  font-size: calc(16px * var(--ui-footer, 1));
  color: var(--s2l-muted);
}

.sum-value {
  font-size: calc(42px * var(--ui-footer, 1));
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.print {
  min-width: 330px;
  min-height: 84px;
  padding: 0 26px;
  font-size: calc(24px * var(--ui-footer, 1));
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
  background: var(--s2l-disabled);
  cursor: default;
}

.label-img {
  display: block;
  width: 100%;
  border: 1px solid var(--s2l-line);
  border-radius: 8px;
}

.label-note {
  text-align: center;
  color: var(--s2l-muted);
}

.sheet {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 2000;
  border-radius: var(--s2l-radius);
  overflow: hidden;
}

.kb-enter-active,
.kb-leave-active {
  transition: transform 0.22s ease;
}

.kb-enter-from,
.kb-leave-to {
  transform: translateY(100%);
}
</style>
