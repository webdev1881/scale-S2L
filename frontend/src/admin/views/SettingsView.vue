<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api, ApiError } from '@/shared/api'
import { KIOSK_FONTS, KIOSK_FONT_KEYS } from '@/shared/fonts'
import { LOCALE_NAMES, SUPPORTED_LOCALES, setLocale } from '@/shared/i18n'
import type { DeviceSettings } from '@/shared/types'

import KioskSketch, { type SketchZone } from '../components/KioskSketch.vue'

const { t } = useI18n()

const form = ref<DeviceSettings | null>(null)
const saving = ref(false)

/**
 * Блоки страницы. Четыре десятка настроек одной простынёй оператор читал сверху
 * вниз, ища нужную; теперь каждая живёт в блоке про свою часть экрана, а схема
 * рядом показывает, о какой части речь. Список здесь же — из него собирается
 * и оглавление слева.
 */
const SECTIONS: { id: string; zone: SketchZone }[] = [
  { id: 'device', zone: 'screen' },
  { id: 'label', zone: 'label' },
  { id: 'weighing', zone: 'header' },
  { id: 'session', zone: 'overlay' },
  { id: 'catalog', zone: 'grid' },
  { id: 'controls', zone: 'footer' },
  { id: 'look', zone: 'card' },
]

const active = ref(SECTIONS[0]!.id)
let observer: IntersectionObserver | undefined

function jump(id: string) {
  document.getElementById(`s-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function load() {
  form.value = await api.settings()
  setLocale(form.value.language)
}

/**
 * Пресеты — именованные снимки настроек: переключиться между «залом» и
 * «прилавком» одной кнопкой в шапке, не подбирая заново десяток полей.
 * Сохраняют то, что сейчас в форме, а не то, что уже на диске — незачем
 * сперва жать «Сохранить», чтобы потом сохранить пресет с тем же значением.
 */
const presets = ref<string[]>([])
const selectedPreset = ref('')
const presetBusy = ref(false)

async function loadPresets() {
  presets.value = await api.settingsPresets()
}

async function applySelectedPreset() {
  if (!selectedPreset.value) return
  presetBusy.value = true
  try {
    form.value = await api.applyPreset(selectedPreset.value)
    setLocale(form.value.language)
    ElMessage.success(t('admin.settings.presetApplied', { name: selectedPreset.value }))
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.settings.presetApplyFailed'))
  } finally {
    presetBusy.value = false
  }
}

async function saveAsPreset() {
  if (!form.value) return
  let name: string
  try {
    const result = await ElMessageBox.prompt('', t('admin.settings.presetSaveTitle'), {
      inputPlaceholder: t('admin.settings.presetNamePrompt'),
      confirmButtonText: t('admin.settings.confirm'),
      cancelButtonText: t('admin.settings.cancel'),
      inputValidator: (value: string) => !!value?.trim() || t('admin.settings.presetNameRequired'),
    })
    name = result.value.trim()
  } catch {
    return // диалог отменён
  }
  presetBusy.value = true
  try {
    presets.value = await api.savePreset(name, form.value)
    selectedPreset.value = name
    ElMessage.success(t('admin.settings.presetSaved', { name }))
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.settings.presetSaveFailed'))
  } finally {
    presetBusy.value = false
  }
}

async function deleteSelectedPreset() {
  if (!selectedPreset.value) return
  const name = selectedPreset.value
  try {
    await ElMessageBox.confirm(t('admin.settings.presetDeleteConfirm', { name }), t('admin.settings.presetDeleteTitle'), {
      type: 'warning',
      confirmButtonText: t('admin.settings.confirm'),
      cancelButtonText: t('admin.settings.cancel'),
    })
  } catch {
    return // отменено
  }
  presetBusy.value = true
  try {
    presets.value = await api.deletePreset(name)
    selectedPreset.value = ''
    ElMessage.success(t('admin.settings.presetDeleted'))
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : t('admin.settings.presetDeleteFailed'))
  } finally {
    presetBusy.value = false
  }
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

onMounted(async () => {
  await load()
  void loadPresets()
  // Оглавление подсвечивает блок, который сейчас в верхней части окна.
  observer = new IntersectionObserver(
    (entries) => {
      const hit = entries.find((e) => e.isIntersecting)
      if (hit) active.value = hit.target.id.slice(2)
    },
    { rootMargin: '-20% 0px -70% 0px' },
  )
  requestAnimationFrame(() => {
    document.querySelectorAll('.block').forEach((el) => observer?.observe(el))
  })
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div v-if="form" class="page">
    <nav class="toc">
      <button
        v-for="section in SECTIONS"
        :key="section.id"
        class="toc-item"
        :class="{ on: active === section.id }"
        @click="jump(section.id)"
      >
        <KioskSketch :zone="section.zone" class="toc-sketch" />
        <span>{{ t(`admin.settings.sections.${section.id}`) }}</span>
      </button>
    </nav>

    <el-form :model="form" label-position="top" class="blocks">
      <!-- Пристрій -->
      <section id="s-device" class="block">
        <header class="block-head">
          <KioskSketch zone="screen" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.device') }}</h2>
            <p>{{ t('admin.settings.sections.deviceLead') }}</p>
          </div>
        </header>
        <div class="fields">
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
        </div>
      </section>

      <!-- Етикетка і штрихкод -->
      <section id="s-label" class="block">
        <header class="block-head">
          <KioskSketch zone="label" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.label') }}</h2>
            <p>{{ t('admin.settings.sections.labelLead') }}</p>
          </div>
        </header>
        <div class="fields">
          <el-form-item :label="t('admin.settings.labelSize')">
            <el-input-number v-model="form.label_width_mm" :min="20" :max="56" />
            <span class="times">×</span>
            <el-input-number v-model="form.label_height_mm" :min="20" :max="120" />
            <div class="hint">{{ t('admin.settings.labelSizeHint') }}</div>
          </el-form-item>
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
        </div>
      </section>

      <!-- Зважування і друк -->
      <section id="s-weighing" class="block">
        <header class="block-head">
          <KioskSketch zone="header" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.weighing') }}</h2>
            <p>{{ t('admin.settings.sections.weighingLead') }}</p>
          </div>
        </header>
        <div class="fields">
          <el-form-item :label="t('admin.settings.minWeight')">
            <el-input-number v-model="form.min_print_weight_g" :min="0" :max="1000" />
            <div class="hint">{{ t('admin.settings.minWeightHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.requireStable')">
            <el-switch v-model="form.require_stable" />
            <div class="hint">{{ t('admin.settings.requireStableHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.scaleButtons')">
            <el-switch v-model="form.kiosk_scale_buttons" />
            <div class="hint">{{ t('admin.settings.scaleButtonsHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.clearHold')">
            <el-input-number v-model="form.kiosk_clear_hold_s" :min="0.2" :max="10" :step="0.1" />
            <div class="hint">{{ t('admin.settings.clearHoldHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.afterPrint')">
            <el-radio-group v-model="form.kiosk_after_print">
              <el-radio-button value="home">{{ t('admin.settings.afterPrintHome') }}</el-radio-button>
              <el-radio-button value="catalog">{{ t('admin.settings.afterPrintCatalog') }}</el-radio-button>
              <el-radio-button value="search">{{ t('admin.settings.afterPrintSearch') }}</el-radio-button>
            </el-radio-group>
            <div class="hint">{{ t('admin.settings.afterPrintHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.unselect')">
            <el-input-number v-model="form.kiosk_unselect_s" :min="0" :max="60" :step="1" />
            <div class="hint">{{ t('admin.settings.unselectHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.labelMax')">
            <el-input-number v-model="form.kiosk_label_max_s" :min="5" :max="120" :step="5" />
            <div class="hint">{{ t('admin.settings.labelMaxHint') }}</div>
          </el-form-item>
        </div>
      </section>

      <!-- Екран і сесія -->
      <section id="s-session" class="block">
        <header class="block-head">
          <KioskSketch zone="overlay" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.session') }}</h2>
            <p>{{ t('admin.settings.sections.sessionLead') }}</p>
          </div>
        </header>
        <div class="fields">
          <el-form-item :label="t('admin.settings.idleReset')">
            <el-input-number v-model="form.kiosk_idle_reset_s" :min="10" :max="600" />
          </el-form-item>
          <el-form-item :label="t('admin.settings.splash')">
            <el-input-number v-model="form.splash_seconds" :min="0" :max="10" :step="0.5" />
            <div class="hint">{{ t('admin.settings.splashHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.headerOnContact')">
            <el-switch v-model="form.kiosk_header_on_contact" />
            <div class="hint">{{ t('admin.settings.headerOnContactHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.forceUpdating')">
            <el-switch v-model="form.kiosk_force_updating" />
            <div class="hint">{{ t('admin.settings.forceUpdatingHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.updatingPhotoScale')">
            <el-input-number v-model="form.kiosk_updating_photo_scale" :min="0" :max="100" :step="2" />
            <div class="hint">{{ t('admin.settings.updatingPhotoScaleHint') }}</div>
          </el-form-item>
        </div>
      </section>

      <!-- Каталог -->
      <section id="s-catalog" class="block">
        <header class="block-head">
          <KioskSketch zone="grid" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.catalog') }}</h2>
            <p>{{ t('admin.settings.sections.catalogLead') }}</p>
          </div>
        </header>
        <div class="fields">
          <el-form-item :label="t('admin.settings.useGroups')">
            <el-switch v-model="form.kiosk_use_groups" />
            <div class="hint">{{ t('admin.settings.useGroupsHint') }}</div>
          </el-form-item>
          <!-- Сетка групп показывается только тогда, когда группы включены:
               настройка, которая ничего не меняет, хуже отсутствующей. -->
          <el-form-item v-if="form.kiosk_use_groups" :label="t('admin.settings.grid')">
            <el-input-number v-model="form.grid_cols" :min="2" :max="6" />
            <span class="times">×</span>
            <el-input-number v-model="form.grid_rows" :min="1" :max="5" />
            <div class="hint">
              {{ t('admin.settings.gridHint', { count: form.grid_cols * form.grid_rows }) }}
            </div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.gridProducts')">
            <el-input-number v-model="form.product_grid_cols" :min="2" :max="6" />
            <span class="times">×</span>
            <el-input-number v-model="form.product_grid_rows" :min="1" :max="5" />
            <div class="hint">
              {{
                t('admin.settings.gridProductsHint', {
                  count: form.product_grid_cols * form.product_grid_rows,
                })
              }}
            </div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.peek')">
            <el-input-number v-model="form.kiosk_peek_percent" :min="0" :max="60" :step="2" />
            <div class="hint">{{ t('admin.settings.peekHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.showCode')">
            <el-switch v-model="form.kiosk_show_code" />
            <div class="hint">{{ t('admin.settings.showCodeHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.onlyWithPhoto')">
            <el-switch v-model="form.kiosk_only_with_photo" />
            <div class="hint">{{ t('admin.settings.onlyWithPhotoHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.photoFirst')">
            <el-switch v-model="form.kiosk_photo_first" :disabled="form.kiosk_only_with_photo" />
            <div class="hint">{{ t('admin.settings.photoFirstHint') }}</div>
          </el-form-item>
        </div>
      </section>

      <!-- Кнопки і клавіатура -->
      <section id="s-controls" class="block">
        <header class="block-head">
          <KioskSketch zone="keyboard" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.controls') }}</h2>
            <p>{{ t('admin.settings.sections.controlsLead') }}</p>
          </div>
        </header>
        <div class="fields">
          <el-form-item :label="t('admin.settings.searchButton')">
            <el-switch v-model="form.kiosk_search_button" />
            <div class="hint">{{ t('admin.settings.searchButtonHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.backButton')">
            <el-switch v-model="form.kiosk_back_button" />
            <div class="hint">{{ t('admin.settings.backButtonHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.searchWidth')">
            <el-input-number
              v-model="form.kiosk_search_width"
              :min="20"
              :max="80"
              :step="5"
              :disabled="!form.kiosk_search_button || !form.kiosk_back_button"
            />
            <div class="hint">{{ t('admin.settings.searchWidthHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.codeButton')">
            <el-switch v-model="form.kiosk_code_button" />
            <div class="hint">{{ t('admin.settings.codeButtonHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.keyboardWidth')">
            <el-input-number v-model="form.kiosk_keyboard_width" :min="40" :max="100" :step="5" />
            <div class="hint">{{ t('admin.settings.keyboardWidthHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.keyboardHeight')">
            <el-input-number v-model="form.kiosk_keyboard_height" :min="20" :max="50" :step="1" />
            <div class="hint">{{ t('admin.settings.keyboardHeightHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.keyboardFont')">
            <el-select v-model="form.kiosk_keyboard_font" style="width: 220px">
              <el-option
                v-for="key in KIOSK_FONT_KEYS"
                :key="key"
                :value="key"
                :label="t(`admin.settings.fonts.${key}`)"
                :style="{ fontFamily: KIOSK_FONTS[key] }"
              />
            </el-select>
            <!-- Образец тем же шрифтом и кеглем, что на клавишах: подбирать шрифт
                 по названию в списке — гадать. -->
            <div
              class="font-sample"
              :style="{
                fontFamily: KIOSK_FONTS[form.kiosk_keyboard_font],
                fontSize: form.kiosk_keyboard_font_size + 'px',
                fontWeight: form.kiosk_keyboard_bold ? 700 : 400,
              }"
            >
              Й Ц У К Е Н Г Ш Щ З Х Ї · 1 2 3
            </div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.keyboardFontSize')">
            <el-input-number v-model="form.kiosk_keyboard_font_size" :min="14" :max="40" :step="1" />
          </el-form-item>
          <el-form-item :label="t('admin.settings.keyboardBold')">
            <el-switch v-model="form.kiosk_keyboard_bold" />
          </el-form-item>
        </div>
      </section>

      <!-- Розміри і кольори -->
      <section id="s-look" class="block">
        <header class="block-head">
          <KioskSketch zone="card" class="block-sketch" />
          <div>
            <h2>{{ t('admin.settings.sections.look') }}</h2>
            <p>{{ t('admin.settings.sections.lookLead') }}</p>
          </div>
        </header>
        <div class="fields">
          <el-form-item :label="t('admin.settings.scaleWeight')">
            <el-input-number v-model="form.ui_scale_weight" :min="0.7" :max="2" :step="0.1" />
          </el-form-item>
          <el-form-item :label="t('admin.settings.scaleFooter')">
            <el-input-number v-model="form.ui_scale_footer" :min="0.7" :max="2" :step="0.1" />
          </el-form-item>
          <el-form-item :label="t('admin.settings.scaleGroupTitle')">
            <el-input-number v-model="form.ui_scale_group_title" :min="0.7" :max="2" :step="0.1" />
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
          <el-form-item :label="t('admin.settings.photoScale')">
            <el-input-number v-model="form.ui_photo_scale" :min="60" :max="160" :step="1" />
            <div class="hint">{{ t('admin.settings.photoScaleHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.photoScaleGroup')">
            <el-input-number v-model="form.ui_photo_scale_group" :min="60" :max="160" :step="1" />
            <div class="hint">{{ t('admin.settings.photoScaleGroupHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.plateHeight')">
            <el-input-number v-model="form.ui_plate_height" :min="1" :max="60" :step="1" />
            <div class="hint">{{ t('admin.settings.plateHeightHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.primaryColor')">
            <el-color-picker v-model="form.ui_primary_color" />
            <div class="hint">{{ t('admin.settings.primaryHint') }}</div>
          </el-form-item>
          <el-form-item :label="t('admin.settings.secondaryColor')">
            <el-color-picker v-model="form.ui_secondary_color" />
            <div class="hint">{{ t('admin.settings.secondaryHint') }}</div>
          </el-form-item>
        </div>
      </section>
    </el-form>

    <!-- Кнопки живут в шапке: форма длинная, и кнопка сохранения не должна
         уезжать под нижний край вместе с ней. `defer` нужен потому, что шапка
         рисуется тем же обходом, что и эта страница. -->
    <Teleport to="#admin-actions" defer>
      <el-select
        v-model="selectedPreset"
        class="preset-select"
        clearable
        filterable
        :placeholder="t('admin.settings.presetPlaceholder')"
      >
        <el-option v-for="name in presets" :key="name" :label="name" :value="name" />
      </el-select>
      <el-button :disabled="!selectedPreset" :loading="presetBusy" @click="applySelectedPreset">
        {{ t('admin.settings.presetApply') }}
      </el-button>
      <el-button :loading="presetBusy" @click="saveAsPreset">
        {{ t('admin.settings.presetSaveAs') }}
      </el-button>
      <el-button
        :disabled="!selectedPreset"
        :loading="presetBusy"
        type="danger"
        plain
        @click="deleteSelectedPreset"
      >
        {{ t('admin.settings.presetDelete') }}
      </el-button>
      <el-button type="primary" :loading="saving" @click="save">
        {{ t('admin.settings.save') }}
      </el-button>
      <el-button @click="load">{{ t('admin.settings.reset') }}</el-button>
    </Teleport>
  </div>
</template>

<style scoped>
.preset-select {
  width: 180px;
}

.page {
  display: grid;
  grid-template-columns: 200px minmax(0, 860px);
  gap: 24px;
  align-items: start;
}

/* Оглавление прилипает к верху: блоков семь, страница длинная, а к нужному
   блоку хочется прыгать, а не листать. */
.toc {
  position: sticky;
  top: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toc-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  font: inherit;
  font-size: 13px;
  text-align: left;
  color: var(--el-text-color-regular);
  background: none;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.toc-item:hover {
  background: var(--el-fill-color-light);
}

.toc-item.on {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  font-weight: 600;
}

.toc-sketch {
  flex: none;
  width: 44px;
}

.blocks {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.block {
  padding: 18px 22px 8px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  /* Якорь встаёт под шапкой админки, а не за ней */
  scroll-margin-top: 16px;
}

.block-head {
  display: flex;
  align-items: center;
  gap: 18px;
  padding-bottom: 14px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.block-sketch {
  flex: none;
  width: 120px;
}

.block-head h2 {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
}

.block-head p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--s2l-muted);
}

/* Две колонки полей с подписью сверху: вдвое короче простыни с подписями слева,
   а подсказка остаётся под своим полем, а не справа от него. */
.fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 28px;
  row-gap: 4px;
}

.fields :deep(.el-form-item) {
  margin-bottom: 14px;
}

.fields :deep(.el-form-item__label) {
  margin-bottom: 4px;
  font-weight: 500;
  line-height: 1.3;
}

.times {
  margin: 0 10px;
  color: var(--s2l-muted);
}

.font-sample {
  width: 100%;
  margin-top: 8px;
  padding: 8px 12px;
  line-height: 1.2;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.hint {
  /* Иначе flex-контейнер el-form-item ставит подсказку справа от контрола */
  width: 100%;
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--s2l-muted);
}

@media (max-width: 900px) {
  .page {
    grid-template-columns: 1fr;
  }

  .toc {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
  }

  .fields {
    grid-template-columns: 1fr;
  }
}
</style>
