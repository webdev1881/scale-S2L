<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { api } from '@/shared/api'
import { elementLocale, setLocale } from '@/shared/i18n'
import type { Status, UpdatedAt } from '@/shared/types'

const { t, locale } = useI18n()
const route = useRoute()
const status = ref<Status | null>(null)
let poll: number | undefined

/**
 * Даты последних обновлений в шапке. Оператор приходит к прибору с вопросом
 * «свежий ли тут каталог и та ли сборка» — и ответ должен быть на экране всегда,
 * а не за тремя кликами. Время опроса берём с часов браузера: оно отвечает на
 * другой вопрос — жива ли связь с прибором прямо сейчас.
 */
const updated = ref<UpdatedAt | null>(null)
const polledAt = ref<Date | null>(null)

async function refresh() {
  try {
    status.value = await api.status()
    polledAt.value = new Date()
  } catch {
    status.value = null
  }
  try {
    updated.value = await api.updatedAt()
  } catch {
    /* не ответил — оставляем прежние отметки, они не устарели от одного сбоя */
  }
}

/** «22.09 14:05» — день и время без года: прибор смотрят сегодняшними глазами. */
function stamp(value: string | null | undefined) {
  if (!value) return t('admin.status.updatedNever')
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function clock(date: Date | null) {
  if (!date) return '—'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

onMounted(async () => {
  refresh()
  poll = window.setInterval(refresh, 3000)
  // Админка подхватывает язык из настроек устройства — как и киоск.
  try {
    setLocale((await api.settings()).language)
  } catch {
    /* настройки недоступны — остаёмся на языке по умолчанию */
  }
})

watch(locale, () => (document.title = t('title.admin')), { immediate: true })

onUnmounted(() => window.clearInterval(poll))
</script>

<template>
  <el-config-provider :locale="elementLocale(locale)">
    <el-container class="admin">
    <el-aside width="220px" class="aside">
      <div class="logo">Aurora S2L</div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <span>{{ t('admin.nav.products') }}</span>
        </el-menu-item>
        <el-menu-item index="/transactions">
          <el-icon><Tickets /></el-icon>
          <span>{{ t('admin.nav.transactions') }}</span>
        </el-menu-item>
        <el-menu-item index="/simulator">
          <el-icon><Monitor /></el-icon>
          <span>{{ t('admin.nav.simulator') }}</span>
        </el-menu-item>
        <el-menu-item index="/label">
          <el-icon><PriceTag /></el-icon>
          <span>{{ t('admin.nav.label') }}</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>{{ t('admin.nav.settings') }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="badges">
          <el-tag :type="status?.scale.online ? 'success' : 'danger'" effect="dark" size="small">
            {{ status?.scale.online ? t('admin.status.scaleOnline') : t('admin.status.scaleOffline') }}
          </el-tag>
          <el-tag :type="status?.printer.online ? 'success' : 'danger'" effect="dark" size="small">
            {{
              status?.printer.online
                ? t('admin.status.printerOnline')
                : t('admin.status.printerOffline')
            }}
          </el-tag>
          <el-tag :type="status?.backend === 'fake' ? 'warning' : 'info'" size="small">
            HAL: {{ status?.backend ?? '—' }}
          </el-tag>
        </div>
        <!-- Даты последних обновлений: каталог из 1С, правка настроек, версия ПО
             и время последнего успешного опроса прибора. -->
        <dl class="updated">
          <div>
            <dt>{{ t('admin.status.updatedCatalog') }}</dt>
            <dd>
              {{ stamp(updated?.catalog_at) }}
              <span v-if="updated?.catalog_products" class="dim">
                · {{ updated.catalog_products }}
              </span>
            </dd>
          </div>
          <div>
            <dt>{{ t('admin.status.updatedSettings') }}</dt>
            <dd>{{ stamp(updated?.settings_at) }}</dd>
          </div>
          <div>
            <dt>{{ t('admin.status.updatedBuild') }}</dt>
            <dd>
              {{ stamp(updated?.build_at) }}
              <span v-if="updated?.build_sha" class="dim">
                · {{ updated.build_sha.slice(0, 7) }}
              </span>
            </dd>
          </div>
          <div>
            <dt>{{ t('admin.status.updatedPage') }}</dt>
            <dd :class="{ stale: !status }">{{ clock(polledAt) }}</dd>
          </div>
        </dl>
        <div class="header-right">
          <!-- Место для кнопок текущего раздела: страница настроек телепортирует
               сюда «Зберегти», чтобы кнопка не уезжала вниз вместе с формой. -->
          <div id="admin-actions" class="header-actions"></div>
          <!-- В той же вкладке, а не в новой: на приборе админку открывают из самого
               киоска (семь касаний по «Товар не обрано»), и возврат должен вернуть ту
               же вкладку, а не завести второй киоск рядом с первым. -->
          <a href="/" class="kiosk-link">{{ t('admin.status.openKiosk') }}</a>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<style scoped>
.admin {
  height: 100%;
}

.aside {
  background: #1f2937;
  color: #e5e7eb;
}

.logo {
  padding: 20px 18px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #cbd5e1;
  --el-menu-hover-bg-color: #374151;
  --el-menu-active-color: #ffffff;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.badges {
  display: flex;
  gap: 8px;
}

/* Даты живут между плашками состояния и кнопками раздела: строка мелкая, читают
   её редко, но она обязана быть на месте всегда. На узком окне переносится. */
.updated {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 18px;
  margin: 0 18px;
  font-size: 12px;
  line-height: 1.3;
}

.updated dt {
  color: var(--el-text-color-placeholder);
}

.updated dd {
  margin: 0;
  font-weight: 600;
  white-space: nowrap;
}

.updated .dim {
  font-weight: 400;
  color: var(--el-text-color-secondary);
}

/* Связь с прибором потеряна: время опроса замерло, и это должно быть видно. */
.updated dd.stale {
  color: var(--el-color-danger);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 18px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.kiosk-link {
  color: var(--s2l-accent);
  text-decoration: none;
  font-weight: 600;
}

.main {
  background: var(--s2l-bg);
  overflow: auto;
}
</style>
