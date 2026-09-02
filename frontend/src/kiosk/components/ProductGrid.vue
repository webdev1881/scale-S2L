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
  <TransitionGroup
    tag="div"
    name="card"
    class="grid"
    :style="{ '--cols': props.cols, '--rows': props.rows }"
  >
    <button
      v-for="(product, index) in products"
      :key="product.id"
      class="card"
      :class="{ active: product.id === selectedId }"
      :style="{ '--i': index }"
      @click="$emit('select', product)"
    >
      <div class="photo">
        <img v-if="product.image" :src="`/products/${product.image}`" :alt="product.name" />
        <span v-else class="emoji">{{ product.emoji || '🏷️' }}</span>
        <!-- Код лежит поверх фотографии без подложки: он нужен тем, кто набирает
             его на клавиатуре, и не должен занимать строку в подписи. -->
        <span class="code">{{ t('kiosk.code') }} {{ product.plu }}</span>
      </div>

      <!-- Название слева, цена справа: взгляд идёт по строке от «что» к «сколько» -->
      <div class="body">
        <span class="name">{{ product.name }}</span>
        <span class="price">
          {{ formatMoney(product.price) }} {{ currency }}/{{
            product.unit === 'piece' ? t('kiosk.perPiece') : t('kiosk.perKg')
          }}
        </span>
      </div>
    </button>

    <p v-if="!products.length" key="empty" class="empty">{{ t('kiosk.nothingFound') }}</p>
  </TransitionGroup>
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
  border: 3px solid var(--s2l-line);
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card.active {
  border-color: var(--s2l-accent);
  background: var(--s2l-selected);
}

.photo {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Доля высоты карточки под фото задаётся в настройках прибора */
  /* Ровно заданная доля высоты, а не остаток: иначе крупная подпись
     съедает фотографию и настройка перестаёт означать обещанное */
  flex: 0 0 calc(var(--ui-photo-product, 60) * 1%);
  min-height: 0;
  background: var(--s2l-soft);
}

.code {
  position: absolute;
  top: 6px;
  left: 8px;
  font-size: calc(14px * var(--ui-code, 1));
  font-weight: 600;
  color: #46505f;
  /* Подложки нет — снимки на белом, а лёгкая тень удерживает читаемость,
     если фотографию заменят на тёмную */
  text-shadow: 0 1px 2px rgb(255 255 255 / 85%);
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
  min-height: 0;
  overflow: hidden;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px 10px;
}

.name {
  flex: 1;
  min-width: 0;
  font-size: calc(19px * var(--ui-name, 1));
  font-weight: 600;
  line-height: 1.2;
  /* Длинное название переносится на вторую строку, дальше — многоточие */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.price {
  flex: none;
  font-size: calc(19px * var(--ui-price, 1));
  font-weight: 700;
  color: var(--s2l-accent);
  white-space: nowrap;
}

.empty {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
  color: var(--s2l-muted);
  font-size: 20px;
}

/* Фильтрация и листание анимируются самими карточками: TransitionGroup даёт
   перестановку соседей (move), а лесенка задержек превращает подмену страницы
   в проявление, а не в мгновенную подмену. */
.card-enter-active {
  transition:
    opacity 0.26s ease,
    transform 0.26s cubic-bezier(0.2, 0.7, 0.2, 1);
  transition-delay: calc(var(--i, 0) * 22ms);
}

.card-leave-active {
  transition:
    opacity 0.14s ease,
    transform 0.14s ease;
}

.card-enter-from {
  opacity: 0;
  transform: translateY(14px) scale(0.96);
}

.card-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

.card-move {
  transition: transform 0.28s cubic-bezier(0.2, 0.7, 0.2, 1);
}

@media (prefers-reduced-motion: reduce) {
  .card-enter-active,
  .card-leave-active,
  .card-move {
    transition: none;
  }
}
</style>
