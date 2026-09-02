<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { api } from '@/shared/api'
import { elementLocale, setLocale } from '@/shared/i18n'
import type { Status } from '@/shared/types'

const { t, locale } = useI18n()
const route = useRoute()
const status = ref<Status | null>(null)
let poll: number | undefined

async function refresh() {
  try {
    status.value = await api.status()
  } catch {
    status.value = null
  }
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
        <div class="header-right">
          <!-- Место для кнопок текущего раздела: страница настроек телепортирует
               сюда «Зберегти», чтобы кнопка не уезжала вниз вместе с формой. -->
          <div id="admin-actions" class="header-actions"></div>
          <a href="/" target="_blank" class="kiosk-link">{{ t('admin.status.openKiosk') }}</a>
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
