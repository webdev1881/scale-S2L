<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { formatKg } from '@/shared/format'
import { translateError } from '@/shared/i18n'
import type { Product } from '@/shared/types'
import { useWeightStore } from '@/shared/weight'

const { t } = useI18n()
const weight = useWeightStore()

const grams = ref(0)
const paperOut = ref(false)
const coverOpen = ref(false)
const products = ref<Product[]>([])
const previewId = ref<number | null>(null)
const previewSrc = ref<string | null>(null)
const isFake = ref(true)

const QUICK = [0, 150, 320, 500, 850, 1200, 2500]

const netKg = computed(() => formatKg(Math.max(weight.reading.net_g, 0)))

async function put(value: number) {
  grams.value = value
  try {
    await api.simWeight(value)
  } catch (error) {
    isFake.value = false
    ElMessage.warning(
      error instanceof ApiError ? error.message : t('admin.simulator.unavailable'),
    )
  }
}

async function togglePrinter() {
  await api.simPrinter({ paper_out: paperOut.value, cover_open: coverOpen.value })
}

async function refreshPreview() {
  if (previewId.value === null) return
  const response = await fetch(api.labelPreviewUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      product_id: previewId.value,
      weight_g: Math.max(weight.reading.net_g, 0),
    }),
  })
  if (!response.ok) return
  if (previewSrc.value) URL.revokeObjectURL(previewSrc.value)
  previewSrc.value = URL.createObjectURL(await response.blob())
}

onMounted(async () => {
  weight.connect()
  products.value = await api.products()
  previewId.value = products.value[0]?.id ?? null
  const status = await api.status()
  isFake.value = status.backend === 'fake'
  // Ползунок должен показывать то, что уже лежит на платформе, а не ноль.
  const target = status.scale.detail.target_g
  if (typeof target === 'number') grams.value = Math.round(target)
})

onUnmounted(() => {
  weight.disconnect()
  if (previewSrc.value) URL.revokeObjectURL(previewSrc.value)
})
</script>

<template>
  <div class="page">
    <el-alert
      v-if="!isFake"
      type="info"
      show-icon
      :closable="false"
      :title="t('admin.simulator.realTitle')"
      :description="t('admin.simulator.realText')"
    />

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>{{ t('admin.simulator.platform') }}</template>

          <div class="readout">
            <span class="digits">{{ netKg }}</span>
            <span class="unit">кг</span>
            <el-tag v-if="weight.reading.error" type="danger" size="small">
              {{ translateError(weight.reading.error) }}
            </el-tag>
            <el-tag v-else :type="weight.reading.stable ? 'success' : 'warning'" size="small">
              {{ weight.reading.stable ? t('admin.simulator.stable') : t('admin.simulator.unstable') }}
            </el-tag>
          </div>

          <el-slider
            v-model="grams"
            :min="0"
            :max="5000"
            :step="10"
            :disabled="!isFake"
            show-input
            @change="put(grams)"
          />

          <div class="quick">
            <el-button
              v-for="value in QUICK"
              :key="value"
              size="small"
              :disabled="!isFake"
              @click="put(value)"
            >
              {{ value }} г
            </el-button>
          </div>

          <div class="row">
            <el-button @click="api.tare()">{{ t('admin.simulator.tare') }}</el-button>
            <el-button @click="api.zero()">{{ t('admin.simulator.zero') }}</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>{{ t('admin.simulator.printer') }}</template>
          <div class="switch-row">
            <span>{{ t('admin.simulator.paperOut') }}</span>
            <el-switch v-model="paperOut" :disabled="!isFake" @change="togglePrinter" />
          </div>
          <div class="switch-row">
            <span>{{ t('admin.simulator.coverOpen') }}</span>
            <el-switch v-model="coverOpen" :disabled="!isFake" @change="togglePrinter" />
          </div>
          <p class="hint">{{ t('admin.simulator.printerHint') }}</p>
        </el-card>

        <el-card shadow="never" class="preview-card">
          <template #header>{{ t('admin.simulator.preview') }}</template>
          <div class="row">
            <el-select v-model="previewId" :placeholder="t('admin.simulator.product')" style="width: 260px">
              <el-option
                v-for="product in products"
                :key="product.id"
                :label="`${product.plu} — ${product.name}`"
                :value="product.id"
              />
            </el-select>
            <el-button type="primary" @click="refreshPreview">
              {{ t('admin.simulator.render') }}
            </el-button>
          </div>
          <img v-if="previewSrc" :src="previewSrc" class="preview" alt="Этикетка" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.readout {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.digits {
  font-size: 46px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.unit {
  color: var(--s2l-muted);
}

.quick,
.row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--s2l-muted);
}

.preview-card {
  margin-top: 16px;
}

.preview {
  display: block;
  width: 100%;
  margin-top: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
}
</style>
