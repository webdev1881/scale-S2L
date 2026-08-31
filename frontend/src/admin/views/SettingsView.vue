<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api, ApiError } from '@/shared/api'
import type { DeviceSettings } from '@/shared/types'

const form = ref<DeviceSettings | null>(null)
const saving = ref(false)

async function load() {
  form.value = await api.settings()
}

async function save() {
  if (!form.value) return
  saving.value = true
  try {
    form.value = await api.saveSettings(form.value)
    ElMessage.success('Настройки сохранены')
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : 'Не удалось сохранить')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-card v-if="form" shadow="never" class="card">
      <template #header>Устройство</template>
      <el-form :model="form" label-width="230px">
        <el-form-item label="Название магазина">
          <el-input v-model="form.store_name" maxlength="60" />
        </el-form-item>
        <el-form-item label="Валюта">
          <el-input v-model="form.currency" maxlength="4" style="width: 100px" />
        </el-form-item>
        <el-form-item label="Размер этикетки, мм">
          <el-input-number v-model="form.label_width_mm" :min="20" :max="120" />
          <span class="times">×</span>
          <el-input-number v-model="form.label_height_mm" :min="20" :max="120" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="form" shadow="never" class="card">
      <template #header>Штрихкод</template>
      <el-form :model="form" label-width="230px">
        <el-form-item label="Шаблон EAN-13">
          <el-input v-model="form.barcode_template" maxlength="12" style="width: 220px" />
          <div class="hint">
            P — цифра PLU, W — цифра значения, остальные символы копируются как есть.
            Например <code>22PPPPPWWWWW</code>: префикс 22, пять цифр PLU, пять цифр значения.
          </div>
        </el-form-item>
        <el-form-item label="Что кодировать">
          <el-radio-group v-model="form.barcode_value">
            <el-radio-button value="weight">Масса, г</el-radio-button>
            <el-radio-button value="total">Сумма, коп</el-radio-button>
          </el-radio-group>
          <div class="hint">Зависит от того, как настроены кассы в торговой сети.</div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="form" shadow="never" class="card">
      <template #header>Поведение киоска</template>
      <el-form :model="form" label-width="230px">
        <el-form-item label="Минимальная масса, г">
          <el-input-number v-model="form.min_print_weight_g" :min="0" :max="1000" />
          <div class="hint">Ниже этого значения печать не разрешается.</div>
        </el-form-item>
        <el-form-item label="Печатать только по стабильному весу">
          <el-switch v-model="form.require_stable" />
          <div class="hint">
            Отключать только для отладки: этикетка с «дрожащим» весом врёт покупателю.
          </div>
        </el-form-item>
        <el-form-item label="Сброс экрана, с">
          <el-input-number v-model="form.kiosk_idle_reset_s" :min="10" :max="600" />
        </el-form-item>
      </el-form>
    </el-card>

    <div class="actions">
      <el-button type="primary" :loading="saving" @click="save">Сохранить</el-button>
      <el-button @click="load">Отменить изменения</el-button>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 780px;
}

.times {
  margin: 0 10px;
  color: var(--s2l-muted);
}

.hint {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--s2l-muted);
}

.actions {
  display: flex;
  gap: 10px;
}
</style>
