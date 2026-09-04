<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Category } from '@/shared/types'

const { t } = useI18n()

const props = defineProps<{
  categories: Category[]
  cols: number
  rows: number
  /** Меняется сама сетка, а не список: карточки не переставляются. */
  calm?: boolean
}>()
defineEmits<{ open: [category: Category] }>()
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
      v-for="(category, index) in categories"
      :key="category.name"
      class="card"
      :style="{ '--i': index }"
      @click="$emit('open', category)"
    >
      <div class="photo">
        <img v-if="category.image" loading="lazy" :src="`/products/${category.image}`" :alt="category.name" />
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
  /* Рамка того же цвета, что и плашка с названием: карточка читается как одна
     фигура и обводится тем же цветом, который выбран в админке. */
  border: 1px solid var(--ui-plate-bg, #1d2129);
  border-radius: var(--s2l-radius);
  cursor: pointer;
  transition: border-color 0.15s;
}

.card:active {
  border-color: var(--s2l-accent);
}

.photo {
  /* Фотография забирает всё, что осталось от плашки: две настройки на одну и ту же
     высоту всегда спорят, и одна из них оказывается обманом. */
  flex: 1 1 auto;
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
  /* Плашка занимает всю текстовую часть карточки, а не только строку под текстом:
     подпись читается как отдельная панель, а не как надпись на белом поле.
     Ширина и цвет — из настроек прибора, цвет текста выводится из яркости заливки. */
  /* Высота плашки — ровно та, что задана в настройках: остаток карточки забирает
     фотография. Пола в две строки больше нет — он и был тем барьером, из-за
     которого ползунок ниже определённого значения переставал что-либо менять. */
  flex: 0 0 calc(var(--ui-plate-height, 30) * 1%);
  min-height: 0;
  overflow: hidden;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  background: var(--ui-plate-bg, #1d2129);
  color: var(--ui-plate-ink, #f4f7fb);
}

.name {
  font-size: calc(26px * var(--ui-group-title, 1));
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: var(--ui-plate-lines, 2);
  -webkit-box-orient: vertical;
  overflow: hidden;
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

/* Спокойный режим: карточки не переставляются и не влетают, только проявляются.
   Отсутствие перехода у `.card-move` — не украшение: Vue проверяет, есть ли у
   класса перестановки переход, и без него пропускает FLIP целиком. */
.grid.calm .card-move,
.grid.calm .card-leave-active {
  transition: none;
}

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
