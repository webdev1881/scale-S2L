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
  /** Набор идёт прямо сейчас: карточки не переставляются, а просто проявляются. */
  calm?: boolean
}>()
defineEmits<{ select: [product: Product] }>()
</script>

<template>
  <TransitionGroup
    tag="div"
    name="card"
    class="grid"
    :class="{ calm: props.calm }"
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
        <span class="name-slot"><span class="name">{{ product.name }}</span></span>
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
  /* Уходящие карточки на время перехода не помещаются в страницу и создают
     неявные ряды. Нулевая высота держит их вне раскладки: иначе ряды страницы
     сжимаются, и фильтрация выглядит рывком. */
  grid-auto-rows: 0;
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
     соседние карточки не сдвигаются в момент выбора. Цвет — тот же, что у плашки
     с названием: карточка читается как одна фигура. */
  border: 1px solid var(--ui-plate-bg, #1d2129);
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card.active {
  border-color: var(--s2l-accent);
  background: var(--s2l-selected);
}

/* Выбранная карточка красит плашку акцентом: на тёмной подложке одной лишь
   рамки мало, чтобы выбор читался с расстояния */
.card.active .body {
  background: var(--s2l-accent-dark);
}

.card.active .price {
  color: var(--s2l-accent-ink, #fff);
}

.photo {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Фото занимает заданную долю высоты, плашка забирает весь остаток */
  flex: 0 1 calc(var(--ui-photo-product, 60) * 1%);
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
  /* Плашка занимает всю текстовую часть карточки, а не только строку под текстом:
     подпись читается как отдельная панель, а не как надпись на белом поле.
     Ширина и цвет — из настроек прибора, цвет текста выводится из яркости заливки. */
  flex: 1;
  /* Плашка не бывает ниже двух строк подписи и ниже доли, заданной в настройках.
     Название клампится в две строки, и плашка ростом в полторы срезает вторую
     посередине букв — это читается как поломка. Доля высоты под фото —
     желаемая, поэтому уступает именно фотография. */
  min-height: max(
    calc(19px * var(--ui-name, 1) * 1.25 * 2 + 16px),
    calc(var(--ui-plate-height, 30) * 1%)
  );
  overflow: hidden;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  background: var(--ui-plate-bg, #1d2129);
  color: var(--ui-plate-ink, #f4f7fb);
}

/* Обрезка по строкам живёт на вложенном элементе: у flex-элемента браузер
   приводит display к flow-root, и -webkit-line-clamp перестаёт работать —
   название разрасталось на четыре строки и лезло на фотографию. */
.name-slot {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.name {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: calc(19px * var(--ui-name, 1));
  font-weight: 600;
  line-height: 1.2;
}

.price {
  flex: none;
  font-size: calc(19px * var(--ui-price, 1));
  font-weight: 700;
  color: var(--ui-plate-accent, #4fc98a);
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

/* Пока набирают код или название, список пересобирается на каждой цифре.
   Перестановка соседей тут не помогает, а мешает: карточки не успевают доехать
   до новых мест и на следующем нажатии едут заново — особенно заметно, когда их
   осталось мало и ехать далеко. Поэтому в наборе карточки не двигаются вовсе,
   а новые просто проявляются.

   Отсутствие перехода у `.card-move` — это не украшение: Vue проверяет, есть ли
   у класса перестановки переход, и без него пропускает всю перестановку целиком,
   не трогая позиции. */
.grid.calm .card-move,
.grid.calm .card-leave-active {
  transition: none;
}

/* Уходящая карточка не должна прожить и кадра: иначе оставшиеся встают на места
   вокруг неё, а через кадр перескакивают. */
.grid.calm .card-leave-active {
  display: none;
}

.grid.calm .card-enter-active {
  transition: opacity 0.12s ease;
  transition-delay: 0s;
}

.grid.calm .card-enter-from {
  opacity: 0;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  .card-enter-active,
  .card-leave-active,
  .card-move {
    transition: none;
  }
}
</style>
