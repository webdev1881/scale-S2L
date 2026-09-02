<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatKg, formatMoney } from '@/shared/format'
import { translateError } from '@/shared/i18n'
import type { Product, WeightReading } from '@/shared/types'

const props = defineProps<{
  reading: WeightReading
  connected: boolean
  clock: string
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
  if (props.reading.net_g < 5) return { text: '', tone: 'idle' as const }
  if (!props.reading.stable) return { text: t('weight.weighing'), tone: 'busy' as const }
  return { text: t('weight.stable'), tone: 'ok' as const }
})
</script>

<template>
  <div class="weight-panel" :class="`tone-${state.tone}`">
    <!-- Показание, подписи и кнопки стоят в строку: в шапке высота дороже ширины -->
    <div class="readout">
      <div class="value">
        <span class="digits">{{ netKg }}</span>
        <span class="unit">кг</span>
      </div>
      <div class="captions">
        <!-- Состояние связи показывается здесь, а не отдельной строкой: покупатель
             и так смотрит на этот блок, а на 768 px строка ради трёх слов не окупается. -->
        <div class="status">
          <span class="dot" :class="{ ok: connected }"></span>
          <span class="conn">{{ connected ? t('kiosk.connected') : t('kiosk.disconnected') }}</span>
          <span class="clock">{{ clock }}</span>
        </div>
        <!-- Пустая платформа — это норма, а не сообщение: подсказка в шапке
             висела бы почти всё время и превращалась в шум. Строка сохраняет
             высоту, чтобы шапка не дёргалась при появлении текста. -->
        <div class="state">{{ state.text }}</div>
        <div v-if="reading.tare_g > 0" class="tare">
          {{ t('weight.tareValue', { value: formatKg(reading.tare_g) }) }}
        </div>
      </div>
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
  display: grid;
  /* показание с подписями | цена и стоимость | кнопки */
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 24px;
  padding: 14px 20px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
  border: 3px solid transparent;
  transition: border-color 0.2s;
}

.readout {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.captions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
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
  gap: 8px;
}

.status {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: calc(16px * var(--ui-weight, 1));
  color: var(--s2l-muted);
  white-space: nowrap;
}

.status .dot {
  width: 10px;
  height: 10px;
  flex: none;
  border-radius: 50%;
  background: var(--s2l-danger);
}

.status .dot.ok {
  background: var(--s2l-accent);
}

.status .clock {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--s2l-ink);
}

.digits {
  /* В шапке высота дороже: показание крупное, но не во весь экран */
  font-size: calc(clamp(48px, 6.2vw, 92px) * var(--ui-weight, 1));
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  /* Табличные цифры + фиксированная ширина: число не «прыгает» при дрожании веса */
}

.unit {
  font-size: calc(clamp(20px, 2.4vw, 34px) * var(--ui-weight, 1));
  color: var(--s2l-muted);
}

.state {
  min-height: calc(1.3em);
  font-size: calc(clamp(16px, 1.7vw, 22px) * var(--ui-weight, 1));
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
  font-size: calc(16px * var(--ui-weight, 1));
  color: var(--s2l-muted);
}

.figures {
  display: flex;
  gap: 12px;
  margin: 0;
  min-width: 0;
}

.figure {
  display: flex;
  flex: 1;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  padding: 10px 14px;
  background: var(--s2l-soft);
  border-radius: 12px;
}

.figure dt {
  font-size: calc(17px * var(--ui-weight, 1));
  color: var(--s2l-muted);
}

.figure dd {
  margin: 0;
  font-size: calc(26px * var(--ui-weight, 1));
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.figure.cost {
  background: var(--s2l-selected);
}

.figure.cost dd {
  font-size: calc(34px * var(--ui-weight, 1));
  color: var(--s2l-accent);
}

.actions {
  display: flex;
  gap: 12px;
}

.btn {
  min-width: 128px;
  min-height: 64px;
  font-size: calc(22px * var(--ui-weight, 1));
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
