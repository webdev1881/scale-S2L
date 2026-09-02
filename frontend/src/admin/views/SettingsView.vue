<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { LOCALE_NAMES, SUPPORTED_LOCALES, setLocale } from '@/shared/i18n'
import type { DeviceSettings } from '@/shared/types'

const { t } = useI18n()

const form = ref<DeviceSettings | null>(null)
const saving = ref(false)

async function load() {
  form.value = await api.settings()
  setLocale(form.value.language)
}

async function save() {
  if (!form.value) return
  saving.value = true
  try {
    form.value = await api.saveSettings(form.value)
    // Язык применяется сразу — иначе оператор не увидит результат своего выбора.
    setLocale(form.value.language)
    ElMessage.success(t('admin.settings.saved'))
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.settings.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-card v-if="form" shadow="never" class="card">
      <template #header>{{ t('admin.settings.device') }}</template>
      <el-form :model="form" label-width="260px">
        <el-form-item :label="t('admin.settings.language')">
          <el-radio-group v-model="form.language">
            <el-radio-button v-for="code in SUPPORTED_LOCALES" :key="code" :value="code">
              {{ LOCALE_NAMES[code] }}
            </el-radio-button>
          </el-radio-group>
          <div class="hint">{{ t('admin.settings.languageHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('admin.settings.theme')">
          <el-radio-group v-model="form.theme">
            <el-radio-button value="dark">{{ t('admin.settings.themeDark') }}</el-radio-button>
            <el-radio-button value="light">{{ t('admin.settings.themeLight') }}</el-radio-button>
          </el-radio-group>
          <div class="hint">{{ t('admin.settings.themeHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('admin.settings.storeName')">
          <el-input v-model="form.store_name" maxlength="60" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.currency')">
          <el-input v-model="form.currency" maxlength="4" style="width: 100px" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.labelSize')">
          <el-input-number v-model="form.label_width_mm" :min="20" :max="56" />
          <span class="times">×</span>
          <el-input-number v-model="form.label_height_mm" :min="20" :max="120" />
          <div class="hint">{{ t('admin.settings.labelSizeHint') }}</div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="form" shadow="never" class="card">
      <template #header>{{ t('admin.settings.barcode') }}</template>
      <el-form :model="form" label-width="260px">
        <el-form-item :label="t('admin.settings.template')">
          <el-input v-model="form.barcode_template" maxlength="12" style="width: 220px" />
          <div class="hint">
            {{ t('admin.settings.templateHint', { example: '22PPPPPWWWWW' }) }}
          </div>
        </el-form-item>
        <el-form-item :label="t('admin.settings.encode')">
          <el-radio-group v-model="form.barcode_value">
            <el-radio-button value="weight">{{ t('admin.settings.encodeWeight') }}</el-radio-button>
            <el-radio-button value="total">{{ t('admin.settings.encodeTotal') }}</el-radio-button>
          </el-radio-group>
          <div class="hint">{{ t('admin.settings.encodeHint') }}</div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="form" shadow="never" class="card">
      <template #header>{{ t('admin.settings.kiosk') }}</template>
      <el-form :model="form" label-width="260px">
        <el-form-item :label="t('admin.settings.minWeight')">
          <el-input-number v-model="form.min_print_weight_g" :min="0" :max="1000" />
          <div class="hint">{{ t('admin.settings.minWeightHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('admin.settings.requireStable')">
          <el-switch v-model="form.require_stable" />
          <div class="hint">{{ t('admin.settings.requireStableHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('admin.settings.idleReset')">
          <el-input-number v-model="form.kiosk_idle_reset_s" :min="10" :max="600" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.splash')">
          <el-input-number v-model="form.splash_seconds" :min="0" :max="10" :step="0.5" />
          <div class="hint">{{ t('admin.settings.splashHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('admin.settings.grid')">
          <el-input-number v-model="form.grid_cols" :min="2" :max="6" />
          <span class="times">×</span>
          <el-input-number v-model="form.grid_rows" :min="1" :max="5" />
          <div class="hint">
            {{ t('admin.settings.gridHint', { count: form.grid_cols * form.grid_rows }) }}
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="form" shadow="never" class="card">
      <template #header>{{ t('admin.settings.scales') }}</template>
      <p class="hint hint-block">{{ t('admin.settings.scalesHint') }}</p>
      <el-form :model="form" label-width="260px">
        <el-form-item :label="t('admin.settings.scaleWeight')">
          <el-input-number v-model="form.ui_scale_weight" :min="0.7" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.scaleGroupTitle')">
          <el-input-number v-model="form.ui_scale_group_title" :min="0.7" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.photoGroup')">
          <el-input-number v-model="form.ui_photo_group" :min="30" :max="85" :step="5" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.scaleProductName')">
          <el-input-number v-model="form.ui_scale_product_name" :min="0.7" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.scaleProductPrice')">
          <el-input-number v-model="form.ui_scale_product_price" :min="0.7" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.scaleProductCode')">
          <el-input-number v-model="form.ui_scale_product_code" :min="0.7" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.photoProduct')">
          <el-input-number v-model="form.ui_photo_product" :min="30" :max="85" :step="5" />
        </el-form-item>
        <el-form-item :label="t('admin.settings.scaleFooter')">
          <el-input-number v-model="form.ui_scale_footer" :min="0.7" :max="2" :step="0.1" />
        </el-form-item>
      </el-form>
    </el-card>

    <div class="actions">
      <el-button type="primary" :loading="saving" @click="save">
        {{ t('admin.settings.save') }}
      </el-button>
      <el-button @click="load">{{ t('admin.settings.reset') }}</el-button>
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

.hint-block {
  margin: 0 0 12px;
}

.hint {
  /* Иначе flex-контейнер el-form-item ставит подсказку справа от контрола */
  width: 100%;
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
