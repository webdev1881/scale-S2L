<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api } from '@/shared/api'
import { formatDateTime, formatKg, formatMoney } from '@/shared/format'
import type { Transaction } from '@/shared/types'

const rows = ref<Transaction[]>([])
const loading = ref(false)

const totalSum = computed(() => rows.value.reduce((acc, row) => acc + row.total, 0))

async function load() {
  loading.value = true
  try {
    rows.value = await api.transactions(200)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div class="summary">
        Операций: <b>{{ rows.length }}</b> · на сумму <b>{{ formatMoney(totalSum) }}</b>
      </div>
      <el-button @click="load">Обновить</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe height="calc(100vh - 190px)">
      <el-table-column prop="id" label="№" width="80" />
      <el-table-column label="Время" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="product_name" label="Товар" min-width="220" />
      <el-table-column label="Масса" width="120" align="right">
        <template #default="{ row }">{{ formatKg(row.weight_g) }} кг</template>
      </el-table-column>
      <el-table-column label="Цена" width="110" align="right">
        <template #default="{ row }">{{ formatMoney(row.price) }}</template>
      </el-table-column>
      <el-table-column label="Сумма" width="120" align="right">
        <template #default="{ row }">
          <b>{{ formatMoney(row.total) }}</b>
        </template>
      </el-table-column>
      <el-table-column prop="barcode" label="Штрихкод" width="170" />
      <el-table-column label="Этикетка" width="120">
        <template #default="{ row }">
          <a v-if="row.label_file" :href="`/labels/${row.label_file}`" target="_blank">открыть</a>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
    </el-table>
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
  align-items: center;
  justify-content: space-between;
}

.summary {
  color: var(--s2l-muted);
}

.muted {
  color: var(--s2l-muted);
}
</style>
