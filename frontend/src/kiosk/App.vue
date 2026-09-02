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
const gridAnim = ref<'dive' | 'rise' | 'page-next' | 'page-prev' | 'none'>('dive')
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
/**
 * Цвет текста на плашке не настраивается, а выводится из её яркости: иначе
 * достаточно одного неудачного выбора, чтобы подпись пропала на заливке.
 */
function plateInk(hex: string): { ink: string; accent: string } {
  const value = /^#[0-9a-fA-F]{6}$/.test(hex) ? hex : '#1d2129'
  const r = parseInt(value.slice(1, 3), 16)
  const g = parseInt(value.slice(3, 5), 16)
  const b = parseInt(value.slice(5, 7), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.6
    ? { ink: '#1d2129', accent: '#1f7a4d' }
    : { ink: '#f4f7fb', accent: '#4fc98a' }
}

const uiScales = computed<Record<string, string>>(() => {
  const plate = plateInk(settings.value?.ui_plate_color ?? '#1d2129')
  return {
  '--ui-weight': String(settings.value?.ui_scale_weight ?? 1),
  '--ui-group-title': String(settings.value?.ui_scale_group_title ?? 1),
  '--ui-name': String(settings.value?.ui_scale_product_name ?? 1),
  '--ui-price': String(settings.value?.ui_scale_product_price ?? 1),
  '--ui-code': String(settings.value?.ui_scale_product_code ?? 1),
  '--ui-footer': String(settings.value?.ui_scale_footer ?? 1),
    '--ui-photo-group': String(settings.value?.ui_photo_group ?? 60),
    '--ui-photo-product': String(settings.value?.ui_photo_product ?? 60),
    '--ui-plate-height': String(settings.value?.ui_plate_height ?? 30),
    '--ui-plate-bg': settings.value?.ui_plate_color ?? '#1d2129',
    '--ui-plate-ink': plate.ink,
    '--ui-plate-accent': plate.accent,
  }
})
const minWeight = computed(() => settings.value?.min_print_weight_g ?? 5)
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

/** Что листаем — зависит от того, показываем группы или товары. */
const pageCount = computed(() => {
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

/**
 * Смена страницы. Свайп листает без перехода: страница уже съездила за пальцем,
 * и добавленный поверх сдвиг читается как второе, чужое движение. Переход
 * остаётся кнопкам пейджера — там движение единственное и оно объясняет, куда
 * ушла страница.
 */
let pageTurnSilent = false

function turnPage(delta: number, animated = true) {
  const next = page.value + delta
  if (next < 0 || next >= pageCount.value) return false
  pageTurnSilent = !animated
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

const ribbonPrev = ref<HTMLElement | null>(null)
const ribbonCurrent = ref<HTMLElement | null>(null)
const ribbonNext = ref<HTMLElement | null>(null)

/**
 * Соседние страницы висят в разметке всё время жеста, а не появляются на первом
 * движении: собрать восемь карточек с фотографиями посреди движения — это
 * пропущенный кадр ровно там, где палец пошёл. На касании же пауза незаметна.
 */
const dragActive = ref(false)
const swipeDragging = ref(false)
let swipeFrom: { x: number; y: number; at: number; id: number; width: number } | null = null
let settleTimer = 0
// Браузер шлёт click даже после протяжки на сотню пикселей, поэтому выбор товара
// после состоявшегося жеста гасим вручную.
let swipeJustHappened = false

const reducedMotion = () =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/** Три полосы ленты: предыдущая, текущая, следующая. */
function ribbonParts() {
  return [
    { el: ribbonPrev.value, base: '-100%' },
    { el: ribbonCurrent.value, base: '0px' },
    { el: ribbonNext.value, base: '100%' },
  ]
}

function moveRibbon(shift: number, motion: string) {
  for (const { el, base } of ribbonParts()) {
    if (!el) continue
    el.style.transition = motion
    el.style.transform = `translateX(calc(${base} + ${shift}px))`
  }
}

function restRibbon() {
  for (const { el } of ribbonParts()) {
    if (!el) continue
    el.style.transition = ''
    el.style.transform = ''
  }
}

function onSwipeStart(event: PointerEvent) {
  // Второй палец в жесте не участвует: это масштабирование или случайное касание.
  if (!event.isPrimary || settleTimer) return
  const width = (event.currentTarget as HTMLElement).getBoundingClientRect().width
  swipeFrom = { x: event.clientX, y: event.clientY, at: event.timeStamp, id: event.pointerId, width }
  swipeDragging.value = false
  if (pageCount.value > 1) dragActive.value = true
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
  moveRibbon(shift, 'none')
}

function onSwipeEnd(event: PointerEvent) {
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
  settleRibbon(dir, from?.width ?? 0)
  // Гасим выбор после любой протяжки, а не только после смены страницы: палец
  // отпущен над чужой карточкой, и её открытие выглядело бы промахом прибора.
  if (dragged) {
    swipeJustHappened = true
    window.setTimeout(() => (swipeJustHappened = false), 300)
  }
}

/**
 * Лента доезжает до места и только в конце меняет страницу: соседняя к этому
 * моменту стоит ровно там, где окажется новая текущая, поэтому подмены не видно.
 * Доводим в ту же сторону, куда вели, — возврат почти ушедшей страницы читался бы
 * как отказ прибора листать.
 */
function settleRibbon(dir: number, width: number) {
  window.clearTimeout(settleTimer)
  const finish = () => {
    settleTimer = 0
    if (dir !== 0) turnPage(dir, false)
    restRibbon()
    dragActive.value = false
  }
  if (reducedMotion()) return finish()
  moveRibbon(dir === 0 ? 0 : -dir * width, `transform ${SETTLE_MS}ms ${SETTLE_EASE}`)
  settleTimer = window.setTimeout(finish, SETTLE_MS)
}

function cancelSwipe() {
  const width = swipeFrom?.width ?? 0
  swipeFrom = null
  swipeDragging.value = false
  settleRibbon(0, width)
}

function openCategory(category: Category) {
  if (swipeJustHappened) return
  openedCategory.value = category
  selected.value = null
  page.value = 0
}

function backToCategories() {
  openedCategory.value = null
  selected.value = null
  search.value = ''
  pluInput.value = ''
  page.value = 0
}

function selectProduct(product: Product) {
  if (swipeJustHappened) return
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
  if (showNumpad.value && !target.closest('.pad') && !target.closest('.toggle')) {
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
  // Касание самих результатов и пейджера — продолжение поиска, а не отказ от
  // него: клавиатура уходит, набранное остаётся. Класс сетки здесь обязан
  // совпадать с разметкой — с исчезнувшим `.catalog` касание карточки откатывало
  // экран к состоянию до набора, и палец попадал уже по другому товару.
  if (target.closest('.grid-slot') || target.closest('.pager')) return closeKeyboard()
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

// Смена уровня старше листания: при провале в группу страница тоже сбрасывается
// на нулевую, и без этого условия переход читался бы как листание назад.
watch([showCategories, page], ([toGroups, next], [wasGroups, prev]) => {
  if (toGroups !== wasGroups) gridAnim.value = toGroups ? 'rise' : 'dive'
  // Имя без единого CSS-правила: Vue не находит перехода и меняет страницу сразу.
  else if (pageTurnSilent) gridAnim.value = 'none'
  else gridAnim.value = next > prev ? 'page-next' : 'page-prev'
  pageTurnSilent = false
})

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
      <!-- Весы стоят шапкой во всю ширину: показание нужно видеть с любого места
           у прибора, а не только стоя напротив левого края экрана. Клавиатура
           выезжает ниже и их не задевает. -->
      <header class="scale">
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
            <!-- Возврат стоит между поиском и набором кода: все три кнопки про одно
                 и то же — как покупатель ищет товар. Стрелка не нужна, надпись и
                 так говорит, куда ведёт. -->
            <button v-if="!showCategories" class="back" @click="backToCategories">
              {{ t('kiosk.allGroups') }}
            </button>
            <button
              class="toggle"
              :class="{ on: showNumpad }"
              @click="showNumpad ? cancelNumpad() : openNumpad()"
            >
              <!-- Клавиши цифрового блока прямо на кнопке: она открывает именно их,
                   и с расстояния фигура читается раньше надписи. -->
              <svg class="toggle-icon" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="6" cy="6" r="1.8" />
                <circle cx="12" cy="6" r="1.8" />
                <circle cx="18" cy="6" r="1.8" />
                <circle cx="6" cy="12" r="1.8" />
                <circle cx="12" cy="12" r="1.8" />
                <circle cx="18" cy="12" r="1.8" />
                <circle cx="6" cy="18" r="1.8" />
                <circle cx="12" cy="18" r="1.8" />
                <circle cx="18" cy="18" r="1.8" />
              </svg>
              {{ t('kiosk.byCode') }}
            </button>
          </div>
        </div>

        <!-- Карточки и цифровой блок лежат в одной обёртке: блок перекрывает
             именно сетку и ровно по её границам, а не занимает собственный ряд
             колонки. -->
        <div class="catalog-area">
          <div
            class="grid-slot"
            @pointerdown="onSwipeStart"
            @pointermove="onSwipeMove"
            @pointerup="onSwipeEnd"
            @pointercancel="cancelSwipe"
          >
          <!-- Без mode="out-in": уходящая и приходящая сетки лежат в одной ячейке и
               меняются внахлёст. Последовательный режим требует, чтобы уход
               обязательно завершился, и любая заминка оставила бы каталог пустым.
               Номер страницы входит в ключ: страница уезжает целиком, а не
               карточка за карточкой. Иначе на время перехода в сетке оказывается
               вдвое больше карточек, ряды пересобираются и кадр дёргается. -->
          <!-- Соседние страницы ленты: висят по краям всё время жеста и едут
               вместе с текущей. Касаний не ловят — палец в этот момент ведёт
               ленту, а не выбирает товар. -->
          <div v-if="dragActive && page > 0" ref="ribbonPrev" class="page side prev">
            <CategoryGrid
              v-if="showCategories"
              :categories="categoriesOn(page - 1)"
              :cols="cols"
              :rows="visibleRows"
            />
            <ProductGrid
              v-else
              :products="productsOn(page - 1)"
              :selected-id="selected?.id ?? null"
              :currency="currency"
              :cols="cols"
              :rows="visibleRows"
            />
          </div>

          <div ref="ribbonCurrent" class="page">
            <Transition :name="gridAnim">
              <CategoryGrid
                v-if="showCategories"
                :key="`groups:${page}`"
                :categories="pagedCategories"
                :cols="cols"
                :rows="visibleRows"
                @open="openCategory"
              />
              <ProductGrid
                v-else
                :key="`products:${page}`"
                :products="pagedProducts"
                :selected-id="selected?.id ?? null"
                :currency="currency"
                :cols="cols"
                :rows="visibleRows"
                @select="selectProduct"
              />
            </Transition>
          </div>

          <div
            v-if="dragActive && page < pageCount - 1"
            ref="ribbonNext"
            class="page side next"
          >
            <CategoryGrid
              v-if="showCategories"
              :categories="categoriesOn(page + 1)"
              :cols="cols"
              :rows="visibleRows"
            />
            <ProductGrid
              v-else
              :products="productsOn(page + 1)"
              :selected-id="selected?.id ?? null"
              :currency="currency"
              :cols="cols"
              :rows="visibleRows"
            />
          </div>
          </div>

          <!-- Цифры выезжают справа поверх карточек: блок узкий, и поджимать ради
               него весь каталог незачем — набирающий код смотрит в него, а не в
               сетку, а остальным карточки остаются видны. -->
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

          <!-- Пока товар не выбран, кнопка печати всё равно ничего не делает, а
               подпись «Оберіть товар» только сообщает об этом. Вместо мёртвой
               подписи стоит кнопка поиска: это и есть следующий шаг покупателя. -->
          <button v-if="!selected" class="print search-cta" @click="openSearch">
            <svg class="cta-icon" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="M16.5 16.5 21 21" />
            </svg>
            {{ t('kiosk.searchCta') }}
          </button>
          <button v-else class="print" :disabled="!!printBlockReason || printing" @click="print">
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
  min-height: 52px;
  padding: 0 4px;
}

/* Возврат — основной путь назад, поэтому он окрашен акцентом, а не выглядит
   вспомогательной серой кнопкой. Ростом он в строку поиска, рядом с которой стоит. */
.back {
  display: flex;
  flex: none;
  align-items: center;
  height: 64px;
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

.grid-slot {
  min-height: 0;
  display: grid;
  /* Уезжающая страница не должна выглядывать из-под весов и пейджера */
  overflow: hidden;
  /* Горизонтальный жест наш: иначе браузер забирает его под свою навигацию и
     присылает pointercancel посреди свайпа. */
  touch-action: pan-y;
}

/* Полосы ленты лежат в одной ячейке; боковые сдвинуты на свою ширину и видны
   только когда лента поехала. Сдвиг задан в CSS, а не в стиле элемента: до
   первого движения пальца писать в стиль некому. */
.page {
  display: grid;
  min-height: 0;
  /* Свой слой: браузер не пересобирает страницу на каждом кадре жеста */
  will-change: transform;
}

/* Уходящая и приходящая сетки внутри полосы лежат в одной ячейке: без этого
   переход между уровнями каталога выстроил бы их в два ряда. */
.page > * {
  grid-area: 1 / 1;
  min-height: 0;
}

.side {
  pointer-events: none;
}

.prev {
  transform: translateX(-100%);
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

/* Подмена без перехода (`none`) — это конец свайпа: лента уже доехала, и уходящая
   страница не должна прожить даже кадра. Vue держит её в DOM до следующего кадра,
   и на новой странице с меньшим числом карточек старые просвечивали в пустых
   ячейках — тот самый блик в конце жеста. */
.none-leave-active {
  display: none;
}

/* Листание: страница уходит в ту сторону, куда её листают, а следующая приходит
   с противоположной. Движение совпадает со стрелкой пейджера и с самим свайпом. */
.page-next-enter-active,
.page-next-leave-active,
.page-prev-enter-active,
.page-prev-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.26s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.page-next-enter-from,
.page-prev-leave-to {
  opacity: 0;
  transform: translateX(7%);
}

.page-next-leave-to,
.page-prev-enter-from {
  opacity: 0;
  transform: translateX(-7%);
}

@media (prefers-reduced-motion: reduce) {
  .grid-slot,
  .dive-enter-active,
  .dive-leave-active,
  .rise-enter-active,
  .rise-leave-active,
  .page-next-enter-active,
  .page-next-leave-active,
  .page-prev-enter-active,
  .page-prev-leave-active {
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

/* Второй вход в поиск после поля — и выглядит как вход, а не как служебная
   белая кнопка: та же заливка, что у «ПОШУК товару» внизу, та же посадка на
   тень, что у «Усі групи» рядом. Цвет — из настроек, вместе с плашкой карточек. */
.toggle {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 22px;
  height: 64px;
  font-size: 19px;
  font-weight: 700;
  color: var(--ui-plate-ink, #f4f7fb);
  background: var(--ui-plate-bg, #1d2129);
  border: none;
  border-radius: 14px;
  box-shadow: 0 2px 0 rgb(0 0 0 / 25%);
  cursor: pointer;
}

.toggle-icon {
  flex: none;
  width: 22px;
  height: 22px;
  fill: currentcolor;
}

/* Пока блок цифр открыт, кнопка стоит вдавленной: панель на экране и так видна,
   а смена цвета на произвольной заливке из настроек читалась бы хуже. */
.toggle.on,
.toggle:active {
  box-shadow: none;
  transform: translateY(2px);
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

/* Поиск — не печать, поэтому и не зелёный: заливка та же, что у плашки с
   названием и рамки карточек, — кнопка принадлежит каталогу, а не действию
   печати, и следует за цветом, выбранным в админке. */
.search-cta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: var(--ui-plate-ink, #f4f7fb);
  background: var(--ui-plate-bg, #1d2129);
}

.search-cta:active {
  opacity: 0.85;
}

.cta-icon {
  flex: none;
  width: 30px;
  height: 30px;
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

/* Цифровой блок занимает ту же ячейку, что и сетка карточек (второй ряд
   колонки), и прижат к правому краю — он лежит поверх карточек, а не двигает
   их. Ячейка задана явно: авторазмещение отправило бы блок новым рядом вниз. */
.catalog-area {
  position: relative;
  display: grid;
  min-height: 0;
}

.pad {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  width: min(420px, 42%);
  border-radius: var(--s2l-radius);
  overflow: hidden;
  box-shadow: -10px 0 28px var(--s2l-shadow-strong);
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
