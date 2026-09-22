<script setup lang="ts">
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { formatMoney } from '@/shared/format'
import { orderedCategories } from '@/shared/catalog'
import type { Category, Product } from '@/shared/types'

type ProductForm = Omit<Product, 'id'>

const { t } = useI18n()

const products = ref<Product[]>([])
const loading = ref(false)
const search = ref('')

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const emptyForm = (): ProductForm => ({
  plu: 0,
  name: '',
  unit: 'weight',
  price: 0,
  category: '',
  tare_g: 0,
  shelf_life_days: 0,
  composition: '',
  emoji: '',
  image: '',
  active: 1,
})

const form = reactive<ProductForm>(emptyForm())

// message как функция: правило создаётся один раз, а язык может смениться позже.
const rules: FormRules<ProductForm> = {
  plu: [
    {
      required: true,
      type: 'number',
      min: 1,
      max: 99999,
      message: () => t('admin.products.pluRule'),
    },
  ],
  name: [{ required: true, message: () => t('admin.products.nameRule') }],
  price: [
    { required: true, type: 'number', min: 0, message: () => t('admin.products.priceRule') },
  ],
}

async function load() {
  loading.value = true
  try {
    products.value = await api.products({ search: search.value, only_active: false })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(product: Product) {
  editingId.value = product.id
  const { id: _id, ...rest } = product
  Object.assign(form, rest)
  dialogVisible.value = true
}

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editingId.value === null) {
      await api.createProduct({ ...form })
      ElMessage.success(t('admin.products.created'))
    } else {
      await api.updateProduct(editingId.value, { ...form })
      ElMessage.success(t('admin.products.updated'))
    }
    dialogVisible.value = false
    await load()
  } catch (error) {
    ElMessage.error(
      error instanceof ApiError ? error.message : t('admin.products.saveFailed'),
    )
  }
}

async function remove(product: Product) {
  const confirmed = await ElMessageBox.confirm(
    t('admin.products.confirmHide', { name: product.name }),
    t('admin.products.confirmTitle'),
    {
      type: 'warning',
      confirmButtonText: t('admin.products.hide'),
      cancelButtonText: t('admin.products.cancel'),
    },
  ).catch(() => false)
  if (!confirmed) return
  await api.deleteProduct(product.id)
  ElMessage.success(t('admin.products.removed'))
  await load()
}

// --- обложки групп ---------------------------------------------------------
// Группы собираются из товаров, поэтому правятся не в строке таблицы, а
// отдельным окном: там их десяток, и оператору удобнее видеть их списком.
const coversVisible = ref(false)
const categories = ref<Category[]>([])
const coverBusy = ref('')

async function openCovers() {
  coversVisible.value = true
  // Тот же порядок, что на экране прибора: перетаскивать список, который стоит
  // иначе, чем видит покупатель, — значит собирать порядок вслепую.
  categories.value = orderedCategories(await api.categories())
}

// --- порядок групп ---------------------------------------------------------
// Перетаскивание нативное (`draggable`), без библиотеки: строк десяток, список
// вертикальный, а лишняя зависимость в админке прибора стоит дороже.
const dragFrom = ref<number | null>(null)
const dragOver = ref<number | null>(null)

function dragStart(index: number, event: DragEvent) {
  dragFrom.value = index
  event.dataTransfer?.setData('text/plain', String(index))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function dragEnter(index: number) {
  if (dragFrom.value !== null) dragOver.value = index
}

async function drop(index: number) {
  const from = dragFrom.value
  dragFrom.value = null
  dragOver.value = null
  if (from === null || from === index) return

  const next = [...categories.value]
  const [moved] = next.splice(from, 1)
  next.splice(index, 0, moved)
  // Показываем сразу, не дожидаясь ответа: перетаскивание должно ощущаться
  // мгновенным, а список короткий — откатить его при ошибке ничего не стоит.
  const previous = categories.value
  categories.value = next
  try {
    categories.value = orderedCategories(
      await api.setCategoryOrder(next.map((category) => category.name)),
    )
    ElMessage.success(t('admin.products.orderSaved'))
  } catch (error) {
    categories.value = previous
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.products.orderFailed'))
  }
}

const FORMATS: Record<string, string> = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
}

async function pickCover(category: Category, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  // Поле очищаем сразу: иначе повторный выбор того же файла не даёт события.
  input.value = ''
  if (!file) return
  const format = FORMATS[file.type]
  if (!format) return ElMessage.warning(t('admin.products.coverFormat'))

  coverBusy.value = category.name
  try {
    const base64 = await readBase64(file)
    const saved = await api.setCategoryImage(category.name, base64, format)
    replaceCategory(saved)
    ElMessage.success(t('admin.products.coverSaved'))
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.products.coverFailed'))
  } finally {
    coverBusy.value = ''
  }
}

async function resetCover(category: Category) {
  coverBusy.value = category.name
  try {
    replaceCategory(await api.clearCategoryImage(category.name))
    ElMessage.success(t('admin.products.coverCleared'))
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.products.coverFailed'))
  } finally {
    coverBusy.value = ''
  }
}

function replaceCategory(saved: Category) {
  categories.value = categories.value.map((c) => (c.name === saved.name ? saved : c))
}

/** Файл в base64 без префикса `data:`: бэкенд ждёт голые данные, как из 1С. */
function readBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(reader.error)
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
    reader.readAsDataURL(file)
  })
}

/** Снимок мог смениться, а имя файла — нет: браузер обязан перечитать его. */
function coverSrc(category: Category) {
  return `/products/${category.image}?v=${coverBusy.value === category.name ? '' : Date.now()}`
}

// --- очистка данных --------------------------------------------------------
// Каталог приходит из 1С полным срезом, поэтому «удалить лишнее» — это не правка
// карточек по одной, а очистка целыми областями: журнал, скрытые товары, всё.
const purgeVisible = ref(false)
const purgeBusy = ref('')

type PurgeScope = 'journal' | 'inactive' | 'all'

const PURGE_SCOPES: PurgeScope[] = ['journal', 'inactive', 'all']

function purgeTitle(scope: PurgeScope) {
  return t(`admin.products.purge${scope[0].toUpperCase()}${scope.slice(1)}`)
}

function purgeDesc(scope: PurgeScope) {
  return t(`admin.products.purge${scope[0].toUpperCase()}${scope.slice(1)}Desc`)
}

async function purge(scope: PurgeScope) {
  const confirmed = await ElMessageBox.confirm(
    t('admin.products.purgeConfirm', { what: purgeTitle(scope).toLowerCase() }),
    t('admin.products.purgeConfirmTitle'),
    {
      type: 'warning',
      confirmButtonText: t('admin.products.purgeRun'),
      cancelButtonText: t('admin.products.cancel'),
      confirmButtonClass: 'el-button--danger',
    },
  ).catch(() => false)
  if (!confirmed) return

  purgeBusy.value = scope
  try {
    const done = await api.purgeCatalog(scope)
    ElMessage.success(t('admin.products.purgeDone', { ...done }))
    purgeVisible.value = false
    await load()
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.products.purgeFailed'))
  } finally {
    purgeBusy.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <el-input
        v-model="search"
        :placeholder="t('admin.products.search')"
        clearable
        style="max-width: 320px"
        @input="load"
      />
      <el-button @click="openCovers">{{ t('admin.products.covers') }}</el-button>
      <el-button type="danger" plain @click="purgeVisible = true">
        {{ t('admin.products.purge') }}
      </el-button>
      <el-button type="primary" @click="openCreate">
        {{ t('admin.products.add') }}
      </el-button>
    </div>

    <el-table :data="products" v-loading="loading" stripe height="calc(100vh - 190px)">
      <el-table-column prop="plu" :label="t('admin.products.code')" width="90" sortable />
      <el-table-column :label="t('admin.products.name')" min-width="240">
        <template #default="{ row }">
          <img v-if="row.image" :src="`/products/${row.image}`" class="row-thumb" alt="" />
          <span v-else class="emoji">{{ row.emoji }}</span>
          {{ row.name }}
          <el-tag v-if="!row.active" type="info" size="small">
            {{ t('admin.products.hidden') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category" :label="t('admin.products.category')" width="140" />
      <el-table-column :label="t('admin.products.unit')" width="90">
        <template #default="{ row }">
          {{ row.unit === 'piece' ? t('kiosk.perPiece') : t('kiosk.perKg') }}
        </template>
      </el-table-column>
      <el-table-column :label="t('admin.products.price')" width="120" align="right">
        <template #default="{ row }">{{ formatMoney(row.price) }}</template>
      </el-table-column>
      <el-table-column
        prop="tare_g"
        :label="t('admin.products.tare')"
        width="100"
        align="right"
      />
      <el-table-column
        prop="shelf_life_days"
        :label="t('admin.products.shelfLife')"
        width="110"
        align="right"
      />
      <el-table-column label="" width="170" align="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">
            {{ t('admin.products.edit') }}
          </el-button>
          <el-button v-if="row.active" link type="danger" @click="remove(row)">
            {{ t('admin.products.hide') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="
        editingId === null ? t('admin.products.newTitle') : t('admin.products.editTitle')
      "
      width="560px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="150px">
        <el-form-item :label="t('admin.products.code')" prop="plu">
          <el-input-number v-model="form.plu" :min="1" :max="99999" />
        </el-form-item>
        <el-form-item :label="t('admin.products.name')" prop="name">
          <el-input v-model="form.name" maxlength="120" />
        </el-form-item>
        <el-form-item :label="t('admin.products.unit')">
          <el-radio-group v-model="form.unit">
            <el-radio-button value="weight">{{ t('admin.products.unitWeight') }}</el-radio-button>
            <el-radio-button value="piece">{{ t('admin.products.unitPiece') }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="
            form.unit === 'piece'
              ? t('admin.products.pricePerPiece')
              : t('admin.products.pricePerKg')
          " prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item :label="t('admin.products.category')">
          <el-input v-model="form.category" />
        </el-form-item>
        <el-form-item :label="t('admin.products.tare')">
          <el-input-number v-model="form.tare_g" :min="0" :max="5000" />
        </el-form-item>
        <el-form-item :label="t('admin.products.shelfLife')">
          <el-input-number v-model="form.shelf_life_days" :min="0" :max="3650" />
        </el-form-item>
        <el-form-item :label="t('admin.products.emoji')">
          <el-input v-model="form.emoji" maxlength="4" style="width: 100px" />
        </el-form-item>
        <el-form-item :label="t('admin.products.image')">
          <el-input v-model="form.image" maxlength="120" placeholder="tomato-cherry.jpg" />
          <div class="hint">{{ t('admin.products.imageHint') }}</div>
          <img v-if="form.image" :src="`/products/${form.image}`" class="thumb" alt="" />
        </el-form-item>
        <el-form-item :label="t('admin.products.composition')">
          <el-input v-model="form.composition" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="t('admin.products.showInKiosk')">
          <el-switch
            :model-value="form.active === 1"
            @update:model-value="(v: boolean) => (form.active = v ? 1 : 0)"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('admin.products.cancel') }}</el-button>
        <el-button type="primary" @click="submit">{{ t('admin.products.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="purgeVisible" :title="t('admin.products.purgeTitle')" width="520px">
      <div class="hint covers-hint">{{ t('admin.products.purgeHint') }}</div>
      <div class="covers">
        <div v-for="scope in PURGE_SCOPES" :key="scope" class="cover">
          <div class="cover-body">
            <div class="cover-name">{{ purgeTitle(scope) }}</div>
            <div class="hint">{{ purgeDesc(scope) }}</div>
          </div>
          <div class="cover-actions">
            <el-button
              size="small"
              type="danger"
              :plain="scope !== 'all'"
              :loading="purgeBusy === scope"
              @click="purge(scope)"
            >
              {{ t('admin.products.purgeRun') }}
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="coversVisible" :title="t('admin.products.coversTitle')" width="560px">
      <div class="hint covers-hint">{{ t('admin.products.coversHint') }}</div>
      <div class="hint covers-hint">{{ t('admin.products.orderHint') }}</div>
      <div class="covers">
        <div
          v-for="(category, index) in categories"
          :key="category.name"
          class="cover"
          :class="{ dragging: dragFrom === index, over: dragOver === index && dragFrom !== index }"
          draggable="true"
          @dragstart="dragStart(index, $event)"
          @dragenter.prevent="dragEnter(index)"
          @dragover.prevent
          @drop.prevent="drop(index)"
          @dragend="dragFrom = null; dragOver = null"
        >
          <span class="cover-grip" aria-hidden="true">⠿</span>
          <img v-if="category.image" :src="coverSrc(category)" class="cover-thumb" alt="" />
          <div v-else class="cover-thumb empty">—</div>
          <div class="cover-body">
            <div class="cover-name">{{ category.name }}</div>
            <div class="hint">
              {{ category.count }} ·
              {{
                category.custom_image
                  ? t('admin.products.coverOwn')
                  : t('admin.products.coverAuto')
              }}
            </div>
          </div>
          <div class="cover-actions">
            <!-- Скрытый input вместо el-upload: файл уходит не отдельным
                 запросом, а тем же JSON, что и снимки из 1С. -->
            <el-button
              size="small"
              :loading="coverBusy === category.name"
              @click="($refs['file-' + category.name] as HTMLInputElement[])[0].click()"
            >
              {{ t('admin.products.coverUpload') }}
            </el-button>
            <input
              :ref="'file-' + category.name"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              @change="pickCover(category, $event)"
            />
            <el-button
              v-if="category.custom_image"
              size="small"
              link
              type="danger"
              @click="resetCover(category)"
            >
              {{ t('admin.products.coverReset') }}
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.emoji {
  margin-right: 4px;
}

.row-thumb {
  width: 34px;
  height: 26px;
  object-fit: cover;
  border-radius: 4px;
  vertical-align: middle;
  margin-right: 6px;
}

.covers-hint {
  margin-bottom: 12px;
}

.covers {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 60vh;
  overflow-y: auto;
}

.cover {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: grab;
}

.cover.dragging {
  opacity: 0.45;
}

/* Куда встанет группа: подсвечиваем строку целиком, а не тонкую черту между
   строками — по ней трудно попасть, а промах отменяет перетаскивание. */
.cover.over {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.cover-grip {
  flex: none;
  color: var(--el-text-color-placeholder);
  font-size: 18px;
  line-height: 1;
  cursor: grab;
}

.cover-thumb {
  width: 76px;
  height: 56px;
  object-fit: cover;
  border-radius: 6px;
  flex: none;
}

.cover-thumb.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-placeholder);
}

.cover-body {
  flex: 1;
  min-width: 0;
}

.cover-name {
  font-weight: 600;
}

.cover-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: none;
}

.thumb {
  display: block;
  width: 160px;
  margin-top: 8px;
  border-radius: 6px;
}

.hint {
  width: 100%;
  margin-top: 4px;
  font-size: 12px;
  color: var(--s2l-muted);
}
</style>
