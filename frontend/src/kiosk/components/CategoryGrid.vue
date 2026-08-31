<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Category } from '@/shared/types'

const { t } = useI18n()

defineProps<{ categories: Category[] }>()
defineEmits<{ open: [category: Category] }>()
</script>

<template>
  <div class="grid">
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
        <span class="count">{{ t('kiosk.itemsCount', { count: category.count }) }}</span>
      </div>
    </button>

    <p v-if="!categories.length" class="empty">{{ t('kiosk.nothingFound') }}</p>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  padding: 4px;
  align-content: start;
}

.card {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  text-align: left;
  background: var(--s2l-panel);
  border: 2px solid #e3e8ef;
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card:active {
  border-color: var(--s2l-accent);
}

.photo {
  aspect-ratio: 4 / 3;
  background: #eef1f5;
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
  padding: 12px 14px 14px;
}

.name {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}

.count {
  font-size: 14px;
  color: var(--s2l-muted);
}

.empty {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
  color: var(--s2l-muted);
  font-size: 20px;
}
</style>
