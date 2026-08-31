<script setup lang="ts">
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { formatMoney } from '@/shared/format'
import type { Product } from '@/shared/types'

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
      <el-button type="primary" @click="openCreate">
        {{ t('admin.products.add') }}
      </el-button>
    </div>

    <el-table :data="products" v-loading="loading" stripe height="calc(100vh - 190px)">
      <el-table-column prop="plu" label="PLU" width="90" sortable />
      <el-table-column :label="t('admin.products.name')" min-width="240">
        <template #default="{ row }">
          <span class="emoji">{{ row.emoji }}</span> {{ row.name }}
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
        <el-form-item label="PLU" prop="plu">
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
