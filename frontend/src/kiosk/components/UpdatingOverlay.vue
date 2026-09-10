<script setup lang="ts">
/**
 * Блокирующий экран на время, пока нет связи с бэкендом (перезапуск службы,
 * обновление прошивки, обрыв сети). Весы сами переподключаются по WebSocket
 * (см. `shared/weight.ts`) — киоск не перезагружается, а просто ждёт и не
 * даёт покупателю тыкать в каталог, который всё равно не отработает печать.
 */
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="updating">
    <div class="spinner"></div>
    <p class="label">{{ t('kiosk.updating') }}</p>
  </div>
</template>

<style scoped>
.updating {
  position: fixed;
  inset: 0;
  z-index: 2500;
  cursor: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 56px;
  background: var(--s2l-splash-bg);
}

.spinner {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  border: 12px solid var(--s2l-soft);
  border-top-color: var(--s2l-accent);
  animation: spin 0.9s linear infinite;
}

.label {
  margin: 0;
  font-size: 88px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--s2l-ink);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
