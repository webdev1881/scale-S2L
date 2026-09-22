<script setup lang="ts">
/**
 * Схема экрана киоска для блоков настроек: что именно на приборе меняет этот
 * блок. Рисуется кодом, а не картинкой из файла: подсветка зоны — это заливка
 * того же прямоугольника, а не второй файл на каждую зону, и схема красится в
 * цвета темы админки без перерисовки.
 */
export type SketchZone =
  | 'screen'
  | 'header'
  | 'grid'
  | 'card'
  | 'footer'
  | 'keyboard'
  | 'label'
  | 'overlay'

defineProps<{ zone: SketchZone }>()
</script>

<template>
  <svg class="sketch" viewBox="0 0 160 100" aria-hidden="true">
    <!-- Этикетка: свой рисунок, экран ей не нужен -->
    <template v-if="zone === 'label'">
      <rect x="30" y="14" width="100" height="72" rx="6" class="paper on" />
      <rect x="40" y="24" width="80" height="6" rx="2" class="ink" />
      <rect x="40" y="34" width="56" height="5" rx="2" class="ink" />
      <g class="ink">
        <rect x="40" y="48" width="3" height="20" />
        <rect x="45" y="48" width="1.5" height="20" />
        <rect x="49" y="48" width="3" height="20" />
        <rect x="54" y="48" width="1.5" height="20" />
        <rect x="58" y="48" width="2" height="20" />
        <rect x="62" y="48" width="3" height="20" />
        <rect x="67" y="48" width="1.5" height="20" />
        <rect x="71" y="48" width="2.5" height="20" />
      </g>
      <rect x="86" y="48" width="34" height="5" rx="2" class="ink" />
      <rect x="86" y="56" width="34" height="5" rx="2" class="ink" />
      <rect x="80" y="66" width="40" height="7" rx="2" class="ink" />
    </template>

    <template v-else>
      <!-- Экран -->
      <rect x="2" y="2" width="156" height="96" rx="6" class="frame" :class="{ on: zone === 'screen' }" />
      <!-- Шапка весов: три плитки -->
      <g :class="{ on: zone === 'header', dim: zone !== 'header' && zone !== 'screen' }">
        <rect x="8" y="8" width="46" height="16" rx="3" class="tile" />
        <rect x="57" y="8" width="46" height="16" rx="3" class="tile" />
        <rect x="106" y="8" width="46" height="16" rx="3" class="tile accent" />
      </g>
      <!-- Сетка карточек 3x2 -->
      <g :class="{ on: zone === 'grid' || zone === 'card', dim: zone !== 'grid' && zone !== 'card' && zone !== 'screen' }">
        <template v-for="(x, i) in [8, 57, 106]" :key="'r1' + i">
          <rect :x="x" y="29" width="46" height="24" rx="3" class="tile" :class="{ pick: zone === 'card' && i === 0 }" />
          <rect :x="x" y="45" width="46" height="8" rx="0" class="plate" />
        </template>
        <template v-for="(x, i) in [8, 57, 106]" :key="'r2' + i">
          <rect :x="x" y="56" width="46" height="24" rx="3" class="tile" />
          <rect :x="x" y="72" width="46" height="8" rx="0" class="plate" />
        </template>
      </g>
      <!-- Нижняя панель: выбранный товар и две кнопки -->
      <g :class="{ on: zone === 'footer' || zone === 'keyboard', dim: zone !== 'footer' && zone !== 'keyboard' && zone !== 'screen' }">
        <rect x="8" y="84" width="40" height="10" rx="3" class="tile" />
        <rect x="52" y="84" width="48" height="10" rx="3" class="tile accent" />
        <rect x="104" y="84" width="48" height="10" rx="3" class="tile accent" />
      </g>
      <!-- Клавиатура выезжает поверх сетки -->
      <g v-if="zone === 'keyboard'" class="on">
        <rect x="30" y="50" width="100" height="32" rx="4" class="tile" />
        <template v-for="row in [56, 63, 70]" :key="row">
          <rect v-for="k in 8" :key="k" :x="36 + (k - 1) * 11.5" :y="row" width="9" height="5" rx="1" class="key" />
        </template>
        <rect x="48" y="77" width="64" height="3" rx="1" class="key" />
      </g>
      <!-- Экран ожидания поверх всего -->
      <g v-if="zone === 'overlay'" class="on">
        <rect x="2" y="2" width="156" height="96" rx="6" class="veil" />
        <circle cx="80" cy="44" r="9" class="ring" />
        <rect x="56" y="60" width="48" height="6" rx="2" class="ink" />
      </g>
    </template>
  </svg>
</template>

<style scoped>
.sketch {
  display: block;
  width: 100%;
  height: auto;
}

.frame {
  fill: var(--el-fill-color-lighter);
  stroke: var(--el-border-color);
  stroke-width: 1.5;
}

.frame.on {
  stroke: var(--s2l-accent);
  stroke-width: 2.5;
}

.tile {
  fill: var(--el-fill-color-dark);
}

.tile.accent {
  fill: var(--el-color-primary-light-5);
}

.plate {
  fill: var(--el-color-primary-light-3);
}

.key {
  fill: var(--el-bg-color);
}

.paper {
  fill: var(--el-bg-color);
  stroke: var(--el-border-color);
  stroke-width: 1.5;
}

.ink {
  fill: var(--el-text-color-regular);
}

.veil {
  fill: var(--el-fill-color-darker);
  opacity: 0.85;
}

.ring {
  fill: none;
  stroke: var(--s2l-accent);
  stroke-width: 3;
  stroke-dasharray: 40 16;
}

/* Подсветка зоны: живой цвет и рамка; всё остальное приглушено, чтобы взгляд
   сразу находил, о какой части экрана речь. */
.on .tile,
.on.tile,
.on .paper {
  stroke: var(--s2l-accent);
  stroke-width: 1.5;
}

.on .tile.pick {
  fill: var(--s2l-accent);
  opacity: 0.7;
}

.dim {
  opacity: 0.35;
}
</style>
