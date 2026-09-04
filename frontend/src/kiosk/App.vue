<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
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
/**
 * Как меняется сетка: провал в группу и возврат — приближением, листание —
 * сдвигом в сторону движения. Направление берётся из самой смены состояния,
 * а не из обработчиков: страницу листают и пейджером, и свайпом, и поиском.
 */
const gridAnim = ref<'dive' | 'rise'>('dive')
const selected = ref<Product | null>(null)
const pluInput = ref('')
const showNumpad = ref(false)
const keyboardOpen = ref(false)
const searchInput = ref<HTMLInputElement | null>(null)

const printing = ref(false)
const labelUrl = ref<string | null>(null)
const labelVisible = ref(false)

let idleTimer: number | undefined
let labelTimer: number | undefined

const currency = computed(() => settings.value?.currency ?? '₴')

/**
 * Масштабы подписей и доля фото уезжают в CSS-переменные корня киоска: вёрстка
 * считает размеры от них, а значения приходят из настроек прибора. Без этого
 * каждый размер пришлось бы пробрасывать пропом до каждой карточки.
 */
/**
 * Цвет текста на плашке не настраивается, а выводится из её яркости: иначе
 * достаточно одного неудачного выбора, чтобы подпись пропала на заливке.
 */
function rgbOf(hex: string, fallback: string) {
  const value = /^#[0-9a-fA-F]{6}$/.test(hex) ? hex : fallback
  return [
    parseInt(value.slice(1, 3), 16),
    parseInt(value.slice(3, 5), 16),
    parseInt(value.slice(5, 7), 16),
  ] as const
}

const luminanceOf = ([r, g, b]: readonly number[]) => (0.299 * r + 0.587 * g + 0.114 * b) / 255

/** Затемнение для «посадки» кнопок на тень: тот же цвет, только глуше. */
function darken(hex: string, fallback: string, amount: number) {
  const shade = rgbOf(hex, fallback).map((c) => Math.round(c * (1 - amount)))
  return `#${shade.map((c) => c.toString(16).padStart(2, '0')).join('')}`
}

/**
 * Цвет текста поверх заливки не настраивается, а выводится из её яркости: иначе
 * достаточно одного неудачного выбора, чтобы подпись пропала.
 */
function inkOn(hex: string, fallback: string) {
  return luminanceOf(rgbOf(hex, fallback)) > 0.6 ? '#1d2129' : '#f4f7fb'
}

/** Цена на тёмной плашке: на светлой заливке зелёный тускнеет, на тёмной — светлеет. */
function plateAccent(hex: string) {
  return luminanceOf(rgbOf(hex, '#1d2129')) > 0.6 ? '#1f7a4d' : '#4fc98a'
}

const uiScales = computed<Record<string, string>>(() => {
  const primary = settings.value?.ui_primary_color ?? '#1d2129'
  const secondary = settings.value?.ui_secondary_color ?? '#1f7a4d'
  return {
    // Второстепенный цвет подменяет сам токен акцента: его используют все
    // компоненты киоска, поэтому перекрашивать их по одному не нужно.
    '--s2l-accent': secondary,
    '--s2l-accent-dark': darken(secondary, '#1f7a4d', 0.22),
    '--s2l-accent-ink': inkOn(secondary, '#1f7a4d'),
  '--ui-weight': String(settings.value?.ui_scale_weight ?? 1),
  '--ui-group-title': String(settings.value?.ui_scale_group_title ?? 1),
  '--ui-name': String(settings.value?.ui_scale_product_name ?? 1),
  '--ui-price': String(settings.value?.ui_scale_product_price ?? 1),
  '--ui-code': String(settings.value?.ui_scale_product_code ?? 1),
  '--ui-footer': String(settings.value?.ui_scale_footer ?? 1),
    '--ui-photo-group': String(settings.value?.ui_photo_group ?? 60),
    '--ui-photo-product': String(settings.value?.ui_photo_product ?? 60),
    '--ui-plate-height': String(settings.value?.ui_plate_height ?? 30),
    // На низкой плашке две строки не помещаются, и вторая срезалась бы посередине
    // букв. Ниже порога подпись сворачивается в одну строку с многоточием.
    '--ui-plate-lines': (settings.value?.ui_plate_height ?? 30) < 18 ? '1' : '2',
    '--ui-plate-bg': primary,
    '--ui-plate-ink': inkOn(primary, '#1d2129'),
    '--ui-plate-accent': plateAccent(primary),
  }
})
const minWeight = computed(() => settings.value?.min_print_weight_g ?? 5)
const scaleButtons = computed(() => settings.value?.kiosk_scale_buttons ?? true)
const requireStable = computed(() => settings.value?.require_stable ?? true)

// Сетка своя на каждом уровне: групп мало и им идут крупные карточки,
// товаров в группе больше и плотность нужна другая.
const cols = computed(() =>
  showCategories.value
    ? (settings.value?.grid_cols ?? 4)
    : (settings.value?.product_grid_cols ?? 4),
)
const rows = computed(() =>
  showCategories.value
    ? (settings.value?.grid_rows ?? 2)
    : (settings.value?.product_grid_rows ?? 2),
)
/**
 * Открытая клавиатура забирает нижнюю половину экрана. Если оставить прежнее число
 * строк, карточки сожмутся до нечитаемых полосок, поэтому во время набора показываем
 * один ряд — остальное доступно листанием или после «Готово».
 */
const visibleRows = computed(() => (keyboardOpen.value ? 1 : rows.value))
const pageSize = computed(() => cols.value * visibleRows.value)

/**
 * Набранный код фильтрует каталог наравне со строкой поиска: результат виден
 * сразу, а не после нажатия «Знайти» — покупатель набирает цифру и тут же видит,
 * туда ли он идёт.
 */
const searching = computed(() => search.value.trim().length > 0 || pluInput.value.length > 0)
/** Группы показываются, пока покупатель не провалился внутрь и не начал искать. */
const showCategories = computed(() => !searching.value && openedCategory.value === null)

const visibleProducts = computed(() => {
  const needle = search.value.trim().toLowerCase()
  const code = pluInput.value
  return products.value.filter((product) => {
    if (
      !searching.value &&
      openedCategory.value &&
      product.category !== openedCategory.value.name
    ) {
      return false
    }
    if (code && !String(product.plu).startsWith(code)) return false
    if (!needle) return true
    return product.name.toLowerCase().includes(needle) || String(product.plu).startsWith(needle)
  })
})

/**
 * Заголовок показывается только там, где он что-то сообщает. На экране групп
 * карточки говорят сами за себя, и подпись над ними — лишний шум.
 */
const catalogTitle = computed(() => {
  // Код показываем в заголовке: строки с ним на экране нет, и без подписи
  // отфильтрованный каталог выглядел бы поредевшим сам по себе.
  if (pluInput.value) return t('kiosk.codeResults', { code: pluInput.value })
  if (searching.value) return t('kiosk.searchResults')
  if (openedCategory.value) return openedCategory.value.name
  return ''
})

/**
 * Выбранный товар занимает блок карточек целиком: дальше покупатель кладёт его на
 * платформу и смотрит на весы, а соседние карточки в этот момент только отвлекают
 * и подставляются под случайное касание.
 */
const showSingle = computed(() => selected.value !== null && !showCategories.value)

/** Что листаем — зависит от того, показываем группы или товары. */
const pageCount = computed(() => {
  if (showSingle.value) return 1
  const length = showCategories.value ? categories.value.length : visibleProducts.value.length
  return Math.max(1, Math.ceil(length / pageSize.value))
})

/** Срез страницы по её номеру: под палец подставляется соседняя, а не текущая. */
function categoriesOn(index: number) {
  return categories.value.slice(index * pageSize.value, (index + 1) * pageSize.value)
}

function productsOn(index: number) {
  return visibleProducts.value.slice(index * pageSize.value, (index + 1) * pageSize.value)
}

const pagedCategories = computed(() => categoriesOn(page.value))
const pagedProducts = computed(() => productsOn(page.value))

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

/** Смена страницы: лента сама доедет до нового места — двигать нечего. */
function turnPage(delta: number) {
  const next = page.value + delta
  if (next < 0 || next >= pageCount.value) return false
  page.value = next
  return true
}

// Свайп по сетке — равноправная замена пейджеру: у витрины палец тянется провести
// по карточкам раньше, чем искать кнопку. Страницы идут лентой: соседние стоят
// вплотную слева и справа и едут вместе с текущей один в один за пальцем.
//
// Под пальцем лента двигается в обход Vue — сдвиги пишутся прямо в стиль трёх
// элементов. Через реактивное состояние каждое движение пальца перерисовывало бы
// весь киоск, и лента дёргалась бы именно там, где обязана быть гладкой.
const SWIPE_START_PX = 8 // с какого сдвига считаем, что ведут, а не промахнулись
const SWIPE_COMMIT_RATIO = 0.25 // четверть ширины — страница пролистана
// На широком экране четверть — это уже 340 px, длиннее удобного движения кистью,
// поэтому порог ограничен и сверху.
const SWIPE_COMMIT_MAX_PX = 200
const SWIPE_FLICK_PX = 24 // короткий бросок — по скорости, а не по длине
const SWIPE_FLICK_SPEED = 0.5 // px/мс
const SWIPE_EDGE_RATIO = 0.12 // на краю каталога лента почти не поддаётся
const SWIPE_EDGE_MAX = 56
const SETTLE_MS = 280 // столько лента доезжает после отпускания
const SETTLE_EASE = 'cubic-bezier(0.2, 0.7, 0.2, 1)'

/**
 * Лента — один элемент со всеми страницами подряд. Листание сводится к её сдвигу:
 * ничего не монтируется, не подменяется и не меняет размеров, поэтому дёргаться
 * нечему. Раньше страницы собирались по три (текущая и соседние) и в конце жеста
 * подменялись — каждая такая подмена была поводом для рывка.
 */
const ribbonEl = ref<HTMLElement | null>(null)
const swipeDragging = ref(false)
let swipeFrom: { x: number; y: number; at: number; id: number; width: number } | null = null
let settleTimer = 0
// Браузер шлёт click даже после протяжки на сотню пикселей, поэтому выбор товара
// после состоявшегося жеста гасим вручную.
let swipeJustHappened = false

const reducedMotion = () =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/**
 * Номером страницы владеет Vue, сдвигом под пальцем — обработчик жеста, и живут
 * они в разных переменных. Писать обоим в `transform` нельзя: ручная правка
 * стиля и реактивная привязка затирают друг друга, и лента остаётся на месте.
 */
const ribbonStyle = computed(() => ({ '--page': String(page.value) }))

/**
 * Сдвиг под пальцем пишется прямо в стиль: через реактивное состояние каждое
 * движение перерисовывало бы весь киоск, и лента дёргалась бы там, где обязана
 * быть гладкой.
 */
function moveRibbon(shift: number) {
  const el = ribbonEl.value
  if (!el) return
  // Под пальцем лента идёт без сглаживания: задержка читается как залипание.
  el.style.transition = 'none'
  el.style.setProperty('--shift', `${shift}px`)
}

/** Палец отпущен: сдвиг снимается, и лента доезжает переходом из CSS. */
function restRibbon() {
  const el = ribbonEl.value
  if (!el) return
  el.style.transition = ''
  el.style.removeProperty('--shift')
}

function onSwipeStart(event: PointerEvent) {
  // Второй палец в жесте не участвует: это масштабирование или случайное касание.
  if (!event.isPrimary || settleTimer) return
  const width = (event.currentTarget as HTMLElement).getBoundingClientRect().width
  swipeFrom = { x: event.clientX, y: event.clientY, at: event.timeStamp, id: event.pointerId, width }
  swipeDragging.value = false
}

function onSwipeMove(event: PointerEvent) {
  const from = swipeFrom
  if (!from || event.pointerId !== from.id) return
  const dx = event.clientX - from.x
  const dy = event.clientY - from.y
  if (!swipeDragging.value) {
    // Пока не ясно, ведут вбок или просто дрожит палец на карточке, — не мешаем.
    if (Math.abs(dx) < SWIPE_START_PX || Math.abs(dx) <= Math.abs(dy)) return
    swipeDragging.value = true
    // Захват берём только когда жест состоялся: захват на самом касании отнимает
    // у карточки click, и обычный тап перестал бы открывать товар.
    try {
      ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
    } catch {
      /* указатель уже отпущен — жест доживёт и без захвата */
    }
  }
  // На краю каталога подставлять нечего, и лента почти не поддаётся — это и есть
  // ответ «дальше ничего нет», понятный без подписи.
  const edge = (dx < 0 && page.value >= pageCount.value - 1) || (dx > 0 && page.value <= 0)
  const shift = edge
    ? Math.max(-SWIPE_EDGE_MAX, Math.min(SWIPE_EDGE_MAX, dx * SWIPE_EDGE_RATIO))
    : dx
  moveRibbon(shift)
}

/**
 * Захват снимаем явно. Обычно браузер отпускает его сам на `pointerup`, но если
 * этого не случилось, следующее касание уходит захватившему элементу — сетке, —
 * и нажатие по кнопке пейджера пропадает. Со стороны это выглядит как «кнопка
 * срабатывает только со второго раза».
 */
function releaseCapture(event: PointerEvent) {
  const el = event.currentTarget as HTMLElement | null
  try {
    if (el?.hasPointerCapture?.(event.pointerId)) el.releasePointerCapture(event.pointerId)
  } catch {
    /* указателя уже нет — снимать нечего */
  }
}

function onSwipeEnd(event: PointerEvent) {
  releaseCapture(event)
  const from = swipeFrom
  const dragged = swipeDragging.value
  swipeFrom = null
  swipeDragging.value = false
  let dir = 0
  if (from && event.pointerId === from.id) {
    const dx = event.clientX - from.x
    const speed = Math.abs(dx) / Math.max(event.timeStamp - from.at, 1)
    const flick = Math.abs(dx) >= SWIPE_FLICK_PX && speed >= SWIPE_FLICK_SPEED
    const enough = Math.min(from.width * SWIPE_COMMIT_RATIO, SWIPE_COMMIT_MAX_PX)
    const wanted = dx < 0 ? 1 : -1
    const exists = wanted > 0 ? page.value < pageCount.value - 1 : page.value > 0
    if (exists && (Math.abs(dx) >= enough || flick)) dir = wanted
  }
  settleRibbon(dir)
  // Гасим выбор после любой протяжки, а не только после смены страницы: палец
  // отпущен над чужой карточкой, и её открытие выглядело бы промахом прибора.
  if (dragged) {
    swipeJustHappened = true
    window.setTimeout(() => (swipeJustHappened = false), 300)
  }
}

/**
 * Отпустили — лента доезжает до места. Номер страницы меняем сразу, а не в конце:
 * реактивный стиль ставит ленту ровно туда, куда её и вело, и переход доигрывает
 * сам. Подменять при этом нечего — все страницы уже в ленте.
 */
function settleRibbon(dir: number) {
  window.clearTimeout(settleTimer)
  if (dir !== 0) turnPage(dir)
  restRibbon()
  // Пока лента доезжает, новый жест её не перехватывает: иначе сдвиг считался бы
  // от старого положения.
  if (!reducedMotion()) {
    settleTimer = window.setTimeout(() => (settleTimer = 0), SETTLE_MS)
  }
}

function cancelSwipe(event?: PointerEvent) {
  if (event) releaseCapture(event)
  swipeFrom = null
  swipeDragging.value = false
  settleRibbon(0)
}

function openCategory(category: Category) {
  if (swipeJustHappened) return
  openedCategory.value = category
  selected.value = null
  page.value = 0
}

// Клик по возврату браузер может продублировать по элементу, оказавшемуся под
// пальцем. Короткое окно после возврата гасит такой «сквозной» фокус в поле.
let backJustHappened = false

function backToCategories() {
  backJustHappened = true
  window.setTimeout(() => (backJustHappened = false), 350)
  openedCategory.value = null
  selected.value = null
  search.value = ''
  pluInput.value = ''
  page.value = 0
}

function selectProduct(product: Product) {
  if (swipeJustHappened) return
  // Повторное касание развёрнутой карточки возвращает к сетке: это единственный
  // способ передумать, не уходя к списку групп.
  if (selected.value?.id === product.id) {
    selected.value = null
    return
  }
  selected.value = product
  // Товар выбран по коду — показываем, где он лежит, и снимаем фильтр: иначе в
  // каталоге осталась бы одна карточка, а строки с кодом на экране уже нет.
  if (pluInput.value) {
    openedCategory.value =
      categories.value.find((category) => category.name === product.category) ?? null
    page.value = 0
    pluInput.value = ''
  }
  closeNumpad()
  closeKeyboard()
}

const SEARCH_MAX_LENGTH = 40

/** Состояние экрана до начала набора — к нему возвращаемся, если поиск бросили. */
let beforeSearch: { search: string; category: Category | null; page: number } | null = null

function keyPress(char: string) {
  if (search.value.length >= SEARCH_MAX_LENGTH) return
  search.value += char
}

/** Снимок экрана до набора кода — на случай отказа от него. */
let beforeCode: { category: Category | null; page: number } | null = null

function openNumpad() {
  if (!showNumpad.value) beforeCode = { category: openedCategory.value, page: page.value }
  showNumpad.value = true
  keyboardOpen.value = false
}

/** Набор кода завершён — найденное остаётся на экране. */
function closeNumpad() {
  showNumpad.value = false
  beforeCode = null
}

/** Набор брошен — возвращаем экран туда, откуда покупатель начал набирать. */
function cancelNumpad() {
  if (beforeCode) {
    openedCategory.value = beforeCode.category
    page.value = beforeCode.page
  }
  pluInput.value = ''
  closeNumpad()
}

function openKeyboard() {
  if (backJustHappened) return searchInput.value?.blur()
  if (!keyboardOpen.value) {
    beforeSearch = { search: search.value, category: openedCategory.value, page: page.value }
  }
  keyboardOpen.value = true
  showNumpad.value = false
}

/**
 * Кнопка поиска в нижней панели: клавиатура и фокус в поле — один жест.
 * Фокус ставим после отрисовки, иначе он приходит в поле, которое ещё не
 * встало на своё место рядом с заголовком.
 */
function openSearch() {
  openKeyboard()
  void nextTick(() => searchInput.value?.focus())
}

/** Ко всем товарам: снимает набранный код, закрывает блок цифр и уходит к группам. */
function allProducts() {
  cancelNumpad()
  backToCategories()
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
  const target = event.target as HTMLElement | null
  if (!target) return
  // Пейджер листает результаты и к отказу от набора отношения не имеет.
  if (target.closest('.pager')) return
  if (showNumpad.value && !target.closest('.pad') && !target.closest('.code-toggle')) {
    // Касание результатов — продолжение набора: блок уходит, найденное остаётся.
    // Всё остальное — отказ, и экран возвращается к состоянию до набора.
    if (target.closest('.grid-slot')) closeNumpad()
    else cancelNumpad()
  }
  if (!keyboardOpen.value) return
  if (target.closest('.keyboard') || target.closest('.search-field')) return
  // Кнопка поиска — часть набора, а не касание мимо: иначе повторное нажатие
  // сначала отменяло бы поиск, а потом открывало его заново.
  if (target.closest('.search-cta')) return
  // Касание результатов — продолжение поиска, а не отказ от него: клавиатура
  // уходит, набранное остаётся. Класс сетки здесь обязан совпадать с разметкой —
  // с исчезнувшим `.catalog` касание карточки откатывало экран к состоянию до
  // набора, и палец попадал уже по другому товару.
  //
  // Пейджер клавиатуру не закрывает вовсе: закрытие возвращает нижнюю панель и
  // распрямляет сетку, пейджер уезжает из-под пальца, и `click` прилетает уже по
  // кнопке «ПОШУК товару» — та открывает клавиатуру заново. Со стороны это
  // выглядело так, будто стрелка пейджера вызывает клавиатуру.
  if (target.closest('.grid-slot')) return closeKeyboard()
  cancelKeyboard()
}

/** Длину кода держит владелец строки, а не клавиши: см. Numpad. */
function padKey(key: string) {
  if (pluInput.value.length >= 5) return
  pluInput.value += key
}

/**
 * Каталог уже отфильтрован набранным кодом, поэтому кнопка только подтверждает
 * выбор: берём точное совпадение, а если его нет — единственный оставшийся товар.
 */
function findByPlu() {
  const plu = Number(pluInput.value)
  const exact = products.value.find((product) => product.plu === plu)
  const found = exact ?? (visibleProducts.value.length === 1 ? visibleProducts.value[0] : null)
  if (!found) {
    ElMessage.warning(t('kiosk.pluNotFound', { plu: pluInput.value }))
    return
  }
  // selectProduct сам провалится в группу товара и снимет фильтр по коду.
  selectProduct(found)
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
  window.addEventListener('pointerdown', bumpIdle)
  window.addEventListener('pointerdown', onPointerDown, true)
  bumpIdle()
})

onUnmounted(() => {
  weight.disconnect()
  window.clearTimeout(idleTimer)
  window.clearTimeout(labelTimer)
  window.removeEventListener('pointerdown', bumpIdle)
  window.removeEventListener('pointerdown', onPointerDown, true)
})

watch([search, openedCategory, selected], bumpIdle)

// Смена уровня старше листания: при провале в группу страница тоже сбрасывается
// на нулевую, и без этого условия переход читался бы как листание назад.
// Переход нужен только смене уровня: листание внутри уровня — сдвиг ленты.
watch([showCategories, showSingle], ([toGroups, single], [wasGroups, wasSingle]) => {
  if (single !== wasSingle) gridAnim.value = single ? 'dive' : 'rise'
  else if (toGroups !== wasGroups) gridAnim.value = toGroups ? 'rise' : 'dive'
})

/** Уровень каталога. Номер страницы в ключ не входит — иначе лента пересоберётся. */
const ribbonKey = computed(() =>
  showCategories.value ? 'groups' : showSingle.value ? `one:${selected.value?.id}` : 'products',
)

/**
 * Пока меняется сама сетка — столбцы под выехавшей панелью, ряды под клавиатурой —
 * карточки не анимируются. Это не изменение списка, а изменение раскладки: влёт
 * снизу со ступенчатой задержкой поверх меняющейся ширины выглядит рывком.
 */
const layoutCalm = ref(false)
let layoutCalmTimer = 0
watch([cols, visibleRows], () => {
  layoutCalm.value = true
  window.clearTimeout(layoutCalmTimer)
  layoutCalmTimer = window.setTimeout(() => (layoutCalm.value = false), 350)
})

const calmCards = computed(() => searching.value || layoutCalm.value)

/**
 * Как только набранный код оставил один товар, панель уходит сама: искали именно
 * его, а нажать по карточке, накрытой панелью, нельзя. Фильтр при этом остаётся —
 * на экране ровно та карточка, ради которой набирали код.
 */
watch([pluInput, visibleProducts], () => {
  if (showNumpad.value && pluInput.value.length > 0 && visibleProducts.value.length === 1) {
    closeNumpad()
  }
})

// Новый запрос начинает просмотр заново.
watch(search, () => (page.value = 0))

/**
 * Размер страницы меняется, когда клавиатура сжимает сетку до одного ряда или
 * оператор правит сетку в админке. Номер страницы при этом не трогаем: сброс на
 * первую съедал нажатие на стрелку (оно как раз и закрывает клавиатуру), а
 * пересчёт по позиции первой карточки — тем более, он срабатывал уже после клика
 * и откатывал страницу назад. Достаточно ограничения ниже: если страницы больше
 * нет, номер подтянется к последней существующей.
 */
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
      <!-- Весы стоят шапкой во всю ширину: показание нужно видеть с любого места
           у прибора, а не только стоя напротив левого края экрана. Клавиатура
           выезжает ниже и их не задевает. -->
      <header class="scale">
        <WeightPanel
          :reading="weight.reading"
          :connected="weight.connected"
          :currency="currency"
          :product="selected"
          :total="total"
          :code-open="showNumpad"
          @toggle-code="showNumpad ? cancelNumpad() : openNumpad()"
        />
      </header>

      <section class="main" :class="{ 'kb-open': keyboardOpen }">
        <!-- Отдельной шапки нет: строка состояния переехала в блок весов, за
             которым покупатель и так следит. Освободившаяся высота отдана карточкам. -->

        <!-- Возврат живёт рядом с заголовком выбора: обе подписи
             про одно и то же — где покупатель находится. Строка сохраняет высоту
             и на верхнем уровне, иначе карточки меняли бы размер между экранами. -->
        <!-- Голова каталога и поиск живут в одной строке: пустое место слева от
             заголовка дешевле, чем ряд карточек, сжатый до полоски. -->
        <div class="head-row">
          <div class="catalog-head">
            <h1 v-if="catalogTitle" class="catalog-title">{{ catalogTitle }}</h1>
          </div>

          <div class="search-row">
            <!-- Поля не видно, пока поиск не вызвали: набирать негде и незачем, а
                 кнопки «ПОШУК товару» и «за Кодом» и так на виду. Появляется оно
                 вместе с клавиатурой и остаётся, пока в нём что-то набрано. -->
            <div v-if="keyboardOpen || search" class="search-field" :class="{ focused: keyboardOpen }">
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
            <!-- Возврат стоит рядом с полем поиска: обе кнопки про одно и то же —
                 как покупатель ищет товар. Стрелка не нужна, надпись и так
                 говорит, куда ведёт. Набор кода переехал в шапку. -->
            <button
              class="back"
              :class="{ hidden: showCategories }"
              :aria-hidden="showCategories"
              @click="backToCategories"
            >
              {{ t('kiosk.allProducts') }}
            </button>
          </div>
        </div>

        <!-- Карточки и цифровой блок лежат в одной обёртке: блок перекрывает
             именно сетку и ровно по её границам, а не занимает собственный ряд
             колонки. -->
        <div class="catalog-area">
          <div
            class="grid-slot"
            :class="{ 'has-peek': pageCount > 1 }"
            @pointerdown="onSwipeStart"
            @pointermove="onSwipeMove"
            @pointerup="onSwipeEnd"
            @pointercancel="cancelSwipe"
          >
          <!-- Одна лента: все страницы стоят подряд, листание — её сдвиг. Смена
               уровня каталога (группы, товары, развёрнутый товар) меняет ключ, и
               тогда работает переход наложением; номер страницы в ключ не входит,
               иначе лента пересобиралась бы на каждом листании. -->
          <Transition :name="gridAnim">
            <!-- Обёртка нужна затем, что переход уровня анимирует `transform`, а на
                 ленте тем же свойством живёт сдвиг страницы: на одном элементе они
                 затирали друг друга, и лента оставалась на первой странице. -->
            <div :key="ribbonKey" class="track">
              <div ref="ribbonEl" class="ribbon" :style="ribbonStyle">
                <template v-if="showCategories">
                  <CategoryGrid
                    v-for="index in pageCount"
                    :key="index"
                    class="page"
                    :categories="categoriesOn(index - 1)"
                    :cols="cols"
                    :rows="visibleRows"
                    :calm="calmCards"
                    @open="openCategory"
                  />
                </template>

                <!-- Выбранный товар — одна карточка на весь блок -->
                <ProductGrid
                  v-else-if="showSingle && selected"
                  class="page"
                  :products="[selected]"
                  :selected-id="selected.id"
                  :cols="1"
                  :rows="1"
                  single
                  :ratio="visibleRows / cols"
                  @select="selectProduct"
                />

                <template v-else>
                  <ProductGrid
                    v-for="index in pageCount"
                    :key="index"
                    class="page"
                    :products="productsOn(index - 1)"
                    :selected-id="selected?.id ?? null"
                    :cols="cols"
                    :rows="visibleRows"
                    :calm="calmCards"
                    @select="selectProduct"
                  />
                  </template>
              </div>
              </div>
          </Transition>
          </div>

          <!-- Цифровой блок выходит панелью у правого края блока карточек, ростом
               ровно с него, и под собой ничего не двигает. Затемнения нет: код
               набирают, чтобы найти товар, и найденное нужно уметь нажать — при
               затемнении карточки переставали ловить касание. -->
          <Transition name="pad">
            <Numpad
              v-if="showNumpad"
              :value="pluInput"
              class="pad"
              @key="padKey"
              @backspace="pluInput = pluInput.slice(0, -1)"
              @clear="pluInput = ''"
              @submit="findByPlu"
            />
          </Transition>
        </div>

        <Pager v-if="pageCount > 1" v-model:page="page" :pages="pageCount" />

        <!-- Футер собран теми же плитками, что и шапка: сумма слева, выбранный
             товар посередине, действие справа — под большой палец. -->
        <footer class="bottom">
          <!-- Сумма живёт в шапке, повторять её здесь незачем. Освободившееся
               место отдано таре и обнулению — их включают в админке там, где
               покупатель сам ставит тару. -->
          <div v-if="scaleButtons" class="scale-actions">
            <button class="tile scale-btn" @click="api.tare()">{{ t('weight.tare') }}</button>
            <button class="tile scale-btn" @click="api.zero()">{{ t('weight.zero') }}</button>
          </div>

          <div class="tile pick">
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

          <!-- Пока набирают код, кнопка поиска бессмысленна: поиск уже открыт. На
               её месте стоит возврат ко всем товарам — единственное, что в этот
               момент нужно, и выглядит он так же, как соседи по слоту. -->
          <button v-if="showNumpad" class="tile action" @click="allProducts">
            {{ t('kiosk.allProducts') }}
          </button>
          <!-- Пока товар не выбран, кнопка печати всё равно ничего не делает, а
               подпись «Оберіть товар» только сообщает об этом. Вместо мёртвой
               подписи стоит кнопка поиска: это и есть следующий шаг покупателя,
               то есть главное действие экрана — и красится оно акцентом, как
               печать, которая займёт то же место. -->
          <button v-else-if="!selected" class="tile action search-cta" @click="openSearch">
            <svg class="cta-icon" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="M16.5 16.5 21 21" />
            </svg>
            <span>{{ t('kiosk.searchCta') }}</span>
          </button>
          <button
            v-else
            class="tile action"
            :disabled="!!printBlockReason || printing"
            @click="print"
          >
            <template v-if="printing">{{ t('kiosk.printing') }}</template>
            <template v-else-if="printBlockReason">{{ printBlockReason }}</template>
            <template v-else>{{ t('kiosk.print') }}</template>
          </button>
        </footer>

        <!-- Клавиатура поиска выезжает снизу внутри этой колонки: она широкая,
             и весы остаются видны целиком, а сжимается только каталог. -->
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
  /* Весы шапкой во всю ширину, каталог под ними */
  grid-template-rows: auto 1fr;
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
  /* голова с поиском / сетка / пагинация / итог */
  grid-template-rows: auto 1fr auto auto;
  gap: 10px;
  min-height: 0;
  /* Клавиатура выезжает внутри этой колонки и поджимает только её */
  transition: padding-bottom 0.22s ease;
}

.main.kb-open {
  padding-bottom: var(--s2l-kb-height);
}

/* Заголовок каталога и поиск стоят в одну строку: слева от заголовка всё равно
   пусто, а ряду карточек эта высота нужнее — сжатая до полоски карточка не
   читается. Заодно поиск прижимается к весам и уходит подальше от кнопки,
   которая его открывает. */
.head-row {
  display: grid;
  /* Пустой строка схлопывается, и карточки встают вплотную к весам: держать
     ради невидимого поля поиска 64 px — дороже, чем сдвиг сетки в тот момент,
     когда поиск открывают (он всё равно перестраивает экран). */
  min-height: 0;
  grid-template-columns: auto minmax(340px, 1fr);
  align-items: center;
  gap: 14px;
  min-width: 0;
}

/* Итоговая панель на время набора уходит: выбранного товара в этот момент нет,
   а её 114 px — разница между читаемой карточкой и полоской. Одной перестановки
   заголовка на 1366x768 не хватает: клавиатура и панель вдвоём не оставляют
   ряду ничего. */
.main.kb-open .bottom {
  display: none;
}

/* Строка сохраняет высоту и при пустом содержимом: иначе карточки меняли бы
   размер при переходе между уровнями каталога */
.catalog-head {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 4px;
}

/* Возврат — основной путь назад, поэтому он окрашен акцентом, а не выглядит
   вспомогательной серой кнопкой. Ростом он в строку поиска, рядом с которой стоит. */
/* На верхнем уровне кнопки возврата нет вовсе: держать её невидимой значило бы
   держать и её 64 px, а строка головы должна схлопываться, чтобы карточки встали
   вплотную к весам. От проваливания касания в поле поиска страхует окно в 350 мс
   после возврата — само поле в этот момент тоже скрыто. */
.back.hidden {
  display: none;
}

.back {
  display: flex;
  flex: none;
  /* Прижата к правому краю: без поля поиска рядом она иначе липнет к заголовку
     группы, будто относится к нему, а не к навигации. */
  margin-left: auto;
  align-items: center;
  height: 64px;
  padding: 0 26px;
  font-size: 20px;
  font-weight: 700;
  color: var(--s2l-accent-ink, #fff);
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

.catalog-title {
  margin: 0;
  font-size: calc(24px * var(--ui-group-title, 1));
  font-weight: 700;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grid-slot {
  min-height: 0;
  display: grid;
  /* Полоска, в которой виден край следующей страницы. Место под неё резервируется
     на всё время листания, а не только когда следующая страница есть: иначе на
     последней странице жёлоб пропадал, и карточки дёргались по ширине ровно в тот
     кадр, когда лента доезжала до края — особенно заметно при возврате назад. */
  --s2l-peek: 0px;
  /* Уезжающая страница не должна выглядывать из-под весов и пейджера */
  overflow: hidden;
  /* Горизонтальный жест наш: иначе браузер забирает его под свою навигацию и
     присылает pointercancel посреди свайпа. */
  touch-action: pan-y;
}

/* Полоса уровня: её двигает переход между группами, товарами и развёрнутой
   карточкой. Лента внутри отвечает только за номер страницы. */
.track {
  display: grid;
  min-height: 0;
}

/* Лента: страницы стоят подряд, каждая шириной в блок. Двигается она целиком,
   поэтому собственный слой нужен ей, а не отдельным страницам. */
.ribbon {
  display: flex;
  min-height: 0;
  height: 100%;
  /* Номер страницы приезжает из состояния, сдвиг — из жеста; складываются они
     здесь, поэтому ни одна из сторон не затирает другую. */
  transform: translateX(calc(var(--shift, 0px) - var(--page, 0) * 100%));
  transition: transform 280ms cubic-bezier(0.2, 0.7, 0.2, 1);
  will-change: transform;
}

.page {
  display: grid;
  flex: 0 0 100%;
  min-height: 0;
}

/* Жёлоб справа, в котором виден край следующей страницы: подсказка, что ленту
   можно потянуть. Место занято, пока страниц больше одной, — иначе на последней
   странице карточки меняли бы ширину. Затухание живёт на самом блоке и начинается
   ровно там, где кончается текущая страница. */
.grid-slot.has-peek {
  --s2l-peek: calc(64px * var(--ui-name, 1));
  padding-right: var(--s2l-peek);
  -webkit-mask-image: linear-gradient(
    to right,
    #000 calc(100% - var(--s2l-peek)),
    rgb(0 0 0 / 35%) calc(100% - var(--s2l-peek) * 0.4),
    transparent
  );
  mask-image: linear-gradient(
    to right,
    #000 calc(100% - var(--s2l-peek)),
    rgb(0 0 0 / 35%) calc(100% - var(--s2l-peek) * 0.4),
    transparent
  );
}

.next {
  transform: translateX(100%);
}

/* Обе сетки занимают одну и ту же ячейку: во время перехода они наложены,
   а не выстроены друг за другом, поэтому высота кадра не скачет. */
.grid-slot > * {
  grid-area: 1 / 1;
  min-height: 0;
}

/* Провал в группу и возврат: приближение внутрь и отдаление наружу. Направление
   читается само, без подписей и стрелок. */
.dive-enter-active,
.dive-leave-active,
.rise-enter-active,
.rise-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.22s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.dive-enter-from {
  opacity: 0;
  transform: scale(0.94);
}

.dive-leave-to {
  opacity: 0;
  transform: scale(1.05);
}

.rise-enter-from {
  opacity: 0;
  transform: scale(1.05);
}

.rise-leave-to {
  opacity: 0;
  transform: scale(0.94);
}

@media (prefers-reduced-motion: reduce) {
  .catalog-area,
  .grid-slot,
  .ribbon,
  .dive-enter-active,
  .dive-leave-active,
  .rise-enter-active,
  .rise-leave-active {
    transition: none;
  }
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

/* Футер — такой же ряд плиток, что и шапка: один радиус, одни отступы, одна
   высота. Порядок читается слева направо: сколько платить, за что, что дальше. */
.bottom {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: stretch;
  gap: 12px;
  padding: 12px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
}

.bottom .tile {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  min-width: 0;
  /* Плитки футера крупные: до них тянутся стоя у прибора, а сумма и кнопка
     печати — то, ради чего к нему подходят. Масштабируются вместе со шрифтом. */
  min-height: calc(110px * var(--ui-footer, 1));
  padding: calc(12px * var(--ui-footer, 1)) calc(16px * var(--ui-footer, 1));
  border: 2px solid transparent;
  border-radius: 14px;
}

/* Тара и обнуление — не действие экрана, а работа с платформой, поэтому они
   спокойные: та же плитка, но без заливки акцентом, которая занята печатью. */
.scale-actions {
  display: flex;
  gap: 12px;
}

.bottom .scale-btn {
  align-items: center;
  justify-content: center;
  min-width: calc(150px * var(--ui-footer, 1));
  font-size: calc(20px * var(--ui-footer, 1));
  font-weight: 700;
  color: var(--s2l-ink);
  background: var(--s2l-soft);
  border-color: var(--s2l-line);
  box-shadow: 0 2px 0 var(--s2l-soft-active);
  cursor: pointer;
}

.bottom .scale-btn:active {
  background: var(--s2l-soft-active);
  box-shadow: none;
  transform: translateY(2px);
}

.pick {
  background: var(--s2l-soft);
}

.pick-name {
  font-size: calc(22px * var(--ui-footer, 1));
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pick-meta,
.pick-empty {
  font-size: calc(17px * var(--ui-footer, 1));
  color: var(--s2l-muted);
}

/* Единственное действие экрана — печать или, пока товар не выбран, поиск.
   Оно всегда справа, под большой палец, и всегда акцентное.
   Селектор с `.bottom`: общее правило плитки ставит содержимое в колонку и весит
   больше — иконка лупы оказывалась над надписью, а не перед ней. */
.bottom .action {
  align-items: center;
  flex-direction: row;
  justify-content: center;
  gap: 14px;
  /* Размеры тянутся тем же ползунком, что и шрифт: зашитые пиксели означали бы,
     что настройка масштаба меняет надпись, но не кнопку под ней. */
  /* Одна ширина на все состояния слота — поиск, возврат ко всем товарам, печать:
     иначе слот прыгает при каждой смене надписи. Верхний предел считается от
     ширины экрана, а не от строки: доля строки для grid-элемента считается от его
     же ячейки, и кнопка вместо ограничения получала произвольное число. */
  min-width: min(calc(300px * var(--ui-footer, 1)), 62vw);
  padding: 0 calc(26px * var(--ui-footer, 1));
  font-size: calc(24px * var(--ui-footer, 1));
  font-weight: 700;
  color: var(--s2l-accent-ink, #fff);
  background: var(--s2l-accent);
  box-shadow: 0 3px 0 var(--s2l-accent-dark);
  cursor: pointer;
}

.action:active:not(:disabled) {
  background: var(--s2l-accent-dark);
  box-shadow: none;
  transform: translateY(3px);
}

.action:disabled {
  background: var(--s2l-disabled);
  box-shadow: none;
  cursor: default;
}

.cta-icon {
  flex: none;
  width: calc(30px * var(--ui-footer, 1));
  height: calc(30px * var(--ui-footer, 1));
  fill: none;
  stroke: currentcolor;
  stroke-width: 2.4;
  stroke-linecap: round;
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
  right: 20%;
  bottom: 0;
  left: 20%;
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

/* Цифровой блок занимает ту же ячейку, что и сетка карточек (второй ряд
   колонки), и прижат к правому краю — он лежит поверх карточек, а не двигает
   их. Ячейка задана явно: авторазмещение отправило бы блок новым рядом вниз. */
.catalog-area {
  position: relative;
  display: grid;
  min-height: 0;
}

/* Панель прижата к блоку карточек: набор кода — состояние каталога, а не всего
   киоска, поэтому весы, строка поиска и итоговая панель остаются нетронутыми.
   Сетке при этом не нужно ни сжиматься, ни сдвигаться, а карточки слева от
   панели остаются рабочими: по ним и выбирают найденный товар. */
.pad {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 3000;
  width: min(420px, 42%);
  /* Рамка основного цвета: панель принадлежит каталогу — её открывают той же
     кнопкой «за Кодом» и ею же ищут товар. */
  border: 2px solid var(--ui-plate-bg, #1d2129);
  border-radius: var(--s2l-radius);
  overflow: hidden;
  box-shadow: -14px 0 40px var(--s2l-shadow-strong);
}


.pad-enter-active,
.pad-leave-active {
  transition: transform 0.22s ease;
}

.pad-enter-from,
.pad-leave-to {
  transform: translateX(100%);
}
</style>
