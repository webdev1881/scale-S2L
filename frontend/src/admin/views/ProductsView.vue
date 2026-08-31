<script setup lang="ts">
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { api, ApiError } from '@/shared/api'
import { formatMoney } from '@/shared/format'
import type { Product } from '@/shared/types'

type ProductForm = Omit<Product, 'id'>

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
  category: 'Прочее',
  tare_g: 0,
  shelf_life_days: 0,
  composition: '',
  emoji: '',
  active: 1,
})

const form = reactive<ProductForm>(emptyForm())

const rules: FormRules<ProductForm> = {
  plu: [{ required: true, type: 'number', min: 1, max: 99999, message: 'PLU от 1 до 99999' }],
  name: [{ required: true, message: 'Укажите название' }],
  price: [{ required: true, type: 'number', min: 0, message: 'Цена не может быть отрицательной' }],
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
      ElMessage.success('Товар добавлен')
    } else {
      await api.updateProduct(editingId.value, { ...form })
      ElMessage.success('Товар сохранён')
    }
    dialogVisible.value = false
    await load()
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : 'Не удалось сохранить')
  }
}

async function remove(product: Product) {
  const confirmed = await ElMessageBox.confirm(
    `Скрыть «${product.name}» из каталога? Журнал операций сохранится.`,
    'Удаление товара',
    { type: 'warning', confirmButtonText: 'Скрыть', cancelButtonText: 'Отмена' },
  ).catch(() => false)
  if (!confirmed) return
  await api.deleteProduct(product.id)
  ElMessage.success('Товар скрыт')
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <el-input
        v-model="search"
        placeholder="Поиск по названию или PLU"
        clearable
        style="max-width: 320px"
        @input="load"
      />
      <el-button type="primary" @click="openCreate">Добавить товар</el-button>
    </div>

    <el-table :data="products" v-loading="loading" stripe height="calc(100vh - 190px)">
      <el-table-column prop="plu" label="PLU" width="90" sortable />
      <el-table-column label="Название" min-width="240">
        <template #default="{ row }">
          <span class="emoji">{{ row.emoji }}</span> {{ row.name }}
          <el-tag v-if="!row.active" type="info" size="small">скрыт</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="Категория" width="140" />
      <el-table-column label="Ед." width="90">
        <template #default="{ row }">{{ row.unit === 'piece' ? 'шт' : 'кг' }}</template>
      </el-table-column>
      <el-table-column label="Цена" width="120" align="right">
        <template #default="{ row }">{{ formatMoney(row.price) }}</template>
      </el-table-column>
      <el-table-column prop="tare_g" label="Тара, г" width="100" align="right" />
      <el-table-column prop="shelf_life_days" label="Срок, дн" width="110" align="right" />
      <el-table-column label="" width="170" align="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">Изменить</el-button>
          <el-button v-if="row.active" link type="danger" @click="remove(row)">Скрыть</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId === null ? 'Новый товар' : 'Изменение товара'"
      width="560px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="150px">
        <el-form-item label="PLU" prop="plu">
          <el-input-number v-model="form.plu" :min="1" :max="99999" />
        </el-form-item>
        <el-form-item label="Название" prop="name">
          <el-input v-model="form.name" maxlength="120" />
        </el-form-item>
        <el-form-item label="Единица">
          <el-radio-group v-model="form.unit">
            <el-radio-button value="weight">Весовой</el-radio-button>
            <el-radio-button value="piece">Штучный</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="form.unit === 'piece' ? 'Цена за шт' : 'Цена за кг'" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item label="Категория">
          <el-input v-model="form.category" />
        </el-form-item>
        <el-form-item label="Тара, г">
          <el-input-number v-model="form.tare_g" :min="0" :max="5000" />
        </el-form-item>
        <el-form-item label="Срок годности, дн">
          <el-input-number v-model="form.shelf_life_days" :min="0" :max="3650" />
        </el-form-item>
        <el-form-item label="Значок">
          <el-input v-model="form.emoji" maxlength="4" style="width: 100px" />
        </el-form-item>
        <el-form-item label="Состав">
          <el-input v-model="form.composition" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="Показывать в киоске">
          <el-switch
            :model-value="form.active === 1"
            @update:model-value="(v: boolean) => (form.active = v ? 1 : 0)"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Отмена</el-button>
        <el-button type="primary" @click="submit">Сохранить</el-button>
      </template>
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
</style>
