<script setup lang="ts">
import { formatMoney } from '@/shared/format'
import type { Product } from '@/shared/types'

defineProps<{ products: Product[]; selectedId: number | null; currency: string }>()
defineEmits<{ select: [product: Product] }>()
</script>

<template>
  <div class="grid">
    <button
      v-for="product in products"
      :key="product.id"
      class="card"
      :class="{ active: product.id === selectedId }"
      @click="$emit('select', product)"
    >
      <span class="emoji">{{ product.emoji || '🏷️' }}</span>
      <span class="name">{{ product.name }}</span>
      <span class="price">
        {{ formatMoney(product.price) }} {{ currency }}/{{ product.unit === 'piece' ? 'шт' : 'кг' }}
      </span>
      <span class="plu">PLU {{ product.plu }}</span>
    </button>

    <p v-if="!products.length" class="empty">Ничего не найдено</p>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 14px;
  /* min-height:0 обязателен: без него grid-элемент растёт по контенту
     и перекрывает поиск и нижнюю панель вместо того, чтобы прокручиваться */
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  padding: 4px;
  align-content: start;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  /* Цель касания заведомо больше пальца: на киоске промах дороже лишнего места */
  min-height: 150px;
  padding: 14px;
  text-align: left;
  background: var(--s2l-panel);
  border: 3px solid transparent;
  border-radius: var(--s2l-radius);
  cursor: pointer;
}

.card.active {
  border-color: var(--s2l-accent);
  background: #f0faf4;
}

.emoji {
  font-size: 34px;
  line-height: 1;
}

.name {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.25;
}

.price {
  margin-top: auto;
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
