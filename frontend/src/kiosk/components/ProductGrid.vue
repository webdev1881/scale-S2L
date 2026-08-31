<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { formatMoney } from '@/shared/format'
import type { Product } from '@/shared/types'

const { t } = useI18n()

const props = defineProps<{
  products: Product[]
  selectedId: number | null
  currency: string
  cols: number
  rows: number
}>()
defineEmits<{ select: [product: Product] }>()
</script>

<template>
  <div class="grid" :style="{ '--cols': props.cols, '--rows': props.rows }">
    <button
      v-for="product in products"
      :key="product.id"
      class="card"
      :class="{ active: product.id === selectedId }"
      @click="$emit('select', product)"
    >
      <div class="photo">
        <img v-if="product.image" :src="`/products/${product.image}`" :alt="product.name" />
        <span v-else class="emoji">{{ product.emoji || '🏷️' }}</span>
      </div>

      <div class="body">
        <span class="name">{{ product.name }}</span>
        <span class="price">
          {{ formatMoney(product.price) }} {{ currency }}/{{
            product.unit === 'piece' ? t('kiosk.perPiece') : t('kiosk.perKg')
          }}
        </span>
        <span class="plu">PLU {{ product.plu }}</span>
      </div>
    </button>

    <p v-if="!products.length" class="empty">{{ t('kiosk.nothingFound') }}</p>
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
  /* Рамка есть всегда: у выбранной карточки она лишь меняет цвет, поэтому
     соседние карточки не сдвигаются в момент выбора. */
  border: 3px solid #e3e8ef;
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card.active {
  border-color: var(--s2l-accent);
  background: #f2fbf6;
}

.photo {
  display: flex;
  align-items: center;
  justify-content: center;
  /* Фото забирает остаток высоты ряда, подпись всегда помещается целиком */
  flex: 1;
  min-height: 0;
  background: #eef1f5;
}

.photo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.emoji {
  font-size: 52px;
  line-height: 1;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px 12px;
}

.name {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.25;
}

.price {
  margin-top: 4px;
  font-size: 17px;
  font-weight: 700;
  color: var(--s2l-accent);
}

.plu {
  font-size: 13px;
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
