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
    <button class="nav" :disabled="page === 0" @click="go(-1)">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5 8 12l7 7" /></svg>
    </button>

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

    <button class="nav" :disabled="page >= pages - 1" @click="go(1)">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7" /></svg>
    </button>
  </div>
</template>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  gap: 14px;
}

/* Стрелка нарисована контуром, а не типографским знаком: «‹» у каждого шрифта
   свой и получается тонким и мелким, а тут толщина и размер заданы явно. */
.nav {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 56px;
  background: var(--s2l-panel);
  border: 2px solid var(--s2l-line);
  border-radius: 14px;
  box-shadow: 0 2px 0 var(--s2l-line);
  cursor: pointer;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.nav svg {
  width: 30px;
  height: 30px;
  fill: none;
  stroke: var(--s2l-accent);
  stroke-width: 3.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav:active:not(:disabled) {
  background: var(--s2l-accent);
  border-color: var(--s2l-accent-dark);
  box-shadow: none;
  transform: translateY(2px);
}

.nav:active:not(:disabled) svg {
  stroke: #fff;
}

/* Недоступная сторона не исчезает, а гаснет: покупателю видно, что страница
   крайняя, а не что кнопка пропала. */
.nav:disabled {
  background: transparent;
  border-color: var(--s2l-disabled);
  box-shadow: none;
  cursor: default;
}

.nav:disabled svg {
  stroke: var(--s2l-disabled);
}

.dots {
  display: flex;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.dot {
  width: 28px;
  height: 28px;
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
  min-width: 72px;
  text-align: right;
  font-size: 17px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--s2l-muted);
}
</style>
