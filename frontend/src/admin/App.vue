<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api } from '@/shared/api'
import type { Status } from '@/shared/types'

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

onMounted(() => {
  refresh()
  poll = window.setInterval(refresh, 3000)
})

onUnmounted(() => window.clearInterval(poll))
</script>

<template>
  <el-container class="admin">
    <el-aside width="220px" class="aside">
      <div class="logo">Aurora S2L</div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <span>Товары</span>
        </el-menu-item>
        <el-menu-item index="/transactions">
          <el-icon><Tickets /></el-icon>
          <span>Журнал</span>
        </el-menu-item>
        <el-menu-item index="/simulator">
          <el-icon><Monitor /></el-icon>
          <span>Симулятор</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>Настройки</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="badges">
          <el-tag :type="status?.scale.online ? 'success' : 'danger'" effect="dark" size="small">
            Весы: {{ status?.scale.online ? 'на связи' : 'нет связи' }}
          </el-tag>
          <el-tag :type="status?.printer.online ? 'success' : 'danger'" effect="dark" size="small">
            Принтер: {{ status?.printer.online ? 'готов' : 'ошибка' }}
          </el-tag>
          <el-tag :type="status?.backend === 'fake' ? 'warning' : 'info'" size="small">
            HAL: {{ status?.backend ?? '—' }}
          </el-tag>
        </div>
        <a href="/" target="_blank" class="kiosk-link">Открыть киоск →</a>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
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
