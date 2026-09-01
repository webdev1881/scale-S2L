<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Category } from '@/shared/types'

const { t } = useI18n()

const props = defineProps<{ categories: Category[]; cols: number; rows: number }>()
defineEmits<{ open: [category: Category] }>()
</script>

<template>
  <div class="grid" :style="{ '--cols': props.cols, '--rows': props.rows }">
    <button
      v-for="category in categories"
      :key="category.name"
      class="card"
      @click="$emit('open', category)"
    >
      <div class="photo">
        <img v-if="category.image" :src="`/products/${category.image}`" :alt="category.name" />
      </div>
      <div class="body">
        <span class="name">{{ category.name }}</span>
      </div>
    </button>

    <p v-if="!categories.length" class="empty">{{ t('kiosk.nothingFound') }}</p>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  /* Страница фиксирована по столбцам и строкам: неполный ряд не обрезается краем
     области, вместо прокрутки — пагинация. */
  grid-template-columns: repeat(var(--cols), minmax(0, 1fr));
  grid-template-rows: repeat(var(--rows), minmax(0, 1fr));
  gap: 16px;
  min-height: 0;
  height: 100%;
  padding: 4px;
  overflow: hidden;
}

.card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  text-align: left;
  background: var(--s2l-panel);
  border: 2px solid var(--s2l-line);
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card:active {
  border-color: var(--s2l-accent);
}

.photo {
  /* Фото забирает остаток высоты ряда, подпись всегда помещается целиком */
  flex: 1;
  min-height: 0;
  background: var(--s2l-soft);
}

.photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px 12px;
}

.name {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}

.empty {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
  color: var(--s2l-muted);
  font-size: 20px;
}
</style>
