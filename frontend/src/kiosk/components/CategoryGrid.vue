<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Category } from '@/shared/types'

const { t } = useI18n()

const props = defineProps<{ categories: Category[]; cols: number; rows: number }>()
defineEmits<{ open: [category: Category] }>()
</script>

<template>
  <TransitionGroup
    tag="div"
    name="card"
    class="grid"
    :style="{ '--cols': props.cols, '--rows': props.rows }"
  >
    <button
      v-for="(category, index) in categories"
      :key="category.name"
      class="card"
      :style="{ '--i': index }"
      @click="$emit('open', category)"
    >
      <div class="photo">
        <img v-if="category.image" :src="`/products/${category.image}`" :alt="category.name" />
      </div>
      <div class="body">
        <span class="name">{{ category.name }}</span>
      </div>
    </button>

    <p v-if="!categories.length" key="empty" class="empty">{{ t('kiosk.nothingFound') }}</p>
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
  border: 2px solid var(--s2l-line);
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card:active {
  border-color: var(--s2l-accent);
}

.photo {
  /* Доля высоты карточки под фото — желаемая, а не жёсткая: при обычных размерах
     подписи выполняется точно, а при увеличенном шрифте фото уступает место,
     иначе подпись не помещается в плашку и наезжает на фотографию */
  flex: 0 1 calc(var(--ui-photo-group, 60) * 1%);
  /* Фотография не исчезает совсем даже при очень крупной подписи */
  min-height: 34%;
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
  /* Подпись занимает столько, сколько нужно её содержимому, но не больше двух
     третей карточки: иначе при крупном шрифте от фотографии не остаётся ничего */
  flex: none;
  max-height: 66%;
  overflow: hidden;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px 12px;
}

.name {
  font-size: calc(26px * var(--ui-group-title, 1));
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
