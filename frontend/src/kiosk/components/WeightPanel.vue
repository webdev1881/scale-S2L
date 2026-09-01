<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatKg, formatMoney } from '@/shared/format'
import { translateError } from '@/shared/i18n'
import type { Product, WeightReading } from '@/shared/types'

const props = defineProps<{
  reading: WeightReading
  connected: boolean
  currency: string
  product: Product | null
  total: number
}>()
defineEmits<{ tare: []; zero: [] }>()

const { t } = useI18n()

const netKg = computed(() => formatKg(Math.max(props.reading.net_g, 0)))

const priceText = computed(() => {
  if (!props.product) return '—'
  const per = props.product.unit === 'piece' ? t('kiosk.perPiece') : t('kiosk.perKg')
  return `${formatMoney(props.product.price)} ${props.currency}/${per}`
})

// Стоимость пересчитывается на каждый отсчёт весов — покупатель видит сумму
// ещё до печати, а не узнаёт её из этикетки.
const costText = computed(() =>
  props.product ? `${formatMoney(props.total)} ${props.currency}` : '—',
)

const state = computed(() => {
  if (!props.connected) return { text: translateError('scale.no_link'), tone: 'error' as const }
  if (props.reading.error) {
    return { text: translateError(props.reading.error), tone: 'error' as const }
  }
  if (props.reading.net_g < 5) return { text: t('weight.putGoods'), tone: 'idle' as const }
  if (!props.reading.stable) return { text: t('weight.weighing'), tone: 'busy' as const }
  return { text: t('weight.stable'), tone: 'ok' as const }
})
</script>

<template>
  <div class="weight-panel" :class="`tone-${state.tone}`">
    <div class="value">
      <span class="digits">{{ netKg }}</span>
      <span class="unit">кг</span>
    </div>

    <div class="state">{{ state.text }}</div>

    <div v-if="reading.tare_g > 0" class="tare">
      {{ t('weight.tareValue', { value: formatKg(reading.tare_g) }) }}
    </div>

    <dl class="figures">
      <div class="figure">
        <dt>{{ t('weight.price') }}</dt>
        <dd>{{ priceText }}</dd>
      </div>
      <div class="figure cost">
        <dt>{{ t('weight.cost') }}</dt>
        <dd>{{ costText }}</dd>
      </div>
    </dl>

    <div class="actions">
      <button class="btn" @click="$emit('tare')">{{ t('weight.tare') }}</button>
      <button class="btn" @click="$emit('zero')">{{ t('weight.zero') }}</button>
    </div>
  </div>
</template>

<style scoped>
.weight-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  height: 100%;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
  border: 3px solid transparent;
  transition: border-color 0.2s;
}

.tone-ok {
  border-color: var(--s2l-accent);
}
.tone-busy {
  border-color: var(--s2l-warn);
}
.tone-error {
  border-color: var(--s2l-danger);
}

.value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 10px;
}

.digits {
  font-size: clamp(56px, 9vw, 132px);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  /* Табличные цифры + фиксированная ширина: число не «прыгает» при дрожании веса */
}

.unit {
  font-size: clamp(20px, 2.4vw, 34px);
  color: var(--s2l-muted);
}

.state {
  text-align: center;
  font-size: clamp(15px, 1.6vw, 20px);
  color: var(--s2l-muted);
  min-height: 1.4em;
}

.tone-ok .state {
  color: var(--s2l-accent);
}
.tone-busy .state {
  color: var(--s2l-warn);
}
.tone-error .state {
  color: var(--s2l-danger);
}

.tare {
  text-align: center;
  font-size: 15px;
  color: var(--s2l-muted);
}

.figures {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 4px 0 0;
}

.figure {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: var(--s2l-soft);
  border-radius: 12px;
}

.figure dt {
  font-size: 15px;
  color: var(--s2l-muted);
}

.figure dd {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.figure.cost {
  background: var(--s2l-selected);
}

.figure.cost dd {
  font-size: 30px;
  color: var(--s2l-accent);
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn {
  flex: 1;
  min-height: 64px;
  font-size: 20px;
  font-weight: 600;
  color: var(--s2l-ink);
  background: var(--s2l-soft);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.btn:active {
  background: var(--s2l-soft-active);
}
</style>
