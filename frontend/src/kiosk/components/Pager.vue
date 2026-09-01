<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{ page: number; pages: number }>()
const emit = defineEmits<{ 'update:page': [value: number] }>()

function go(delta: number) {
  const next = props.page + delta
  if (next < 0 || next >= props.pages) return
  emit('update:page', next)
}
</script>

<template>
  <div class="pager">
    <button class="nav" :disabled="page === 0" @click="go(-1)">‹</button>

    <div class="dots">
      <button
        v-for="index in pages"
        :key="index"
        class="dot"
        :class="{ on: index - 1 === page }"
        @click="emit('update:page', index - 1)"
      >
        <span class="sr">{{ index }}</span>
      </button>
    </div>

    <span class="counter">{{ t('kiosk.pageOf', { page: page + 1, pages }) }}</span>

    <button class="nav" :disabled="page >= pages - 1" @click="go(1)">›</button>
  </div>
</template>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  gap: 14px;
}

.nav {
  /* Стрелки — основная навигация пальцем, поэтому крупные */
  width: 84px;
  height: 46px;
  font-size: 26px;
  line-height: 1;
  color: var(--s2l-ink);
  background: var(--s2l-panel);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.nav:active:not(:disabled) {
  background: var(--s2l-soft-active);
}

.nav:disabled {
  color: var(--s2l-disabled-ink);
  cursor: default;
}

.dots {
  display: flex;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.dot {
  width: 26px;
  height: 26px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: var(--s2l-disabled);
  cursor: pointer;
}

.dot.on {
  background: var(--s2l-accent);
}

.sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}

.counter {
  min-width: 66px;
  text-align: right;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
  color: var(--s2l-muted);
}
</style>
