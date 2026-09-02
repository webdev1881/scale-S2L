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
    <div class="readout">
      <!-- Часы и связь стоят строкой над показанием: за ними следят краем глаза,
           а вес — то, ради чего на этот блок смотрят. Кнопок тары и нуля здесь
           нет: это работа оператора, и её место в админке. -->
      <div class="status">
        <span class="dot" :class="{ ok: connected }"></span>
        <span class="conn">{{ connected ? t('kiosk.connected') : t('kiosk.disconnected') }}</span>
        <span class="clock">{{ clock }}</span>
      </div>

      <div class="value">
        <span class="digits">{{ netKg }}</span>
        <span class="unit">кг</span>
        <!-- Подписи идут рядом с числом, а не под ним: на 768 px лишний ряд в
             шапке отнимает высоту у карточек. Пустая платформа сообщением не
             считается, но строка сохраняет высоту, чтобы шапка не дёргалась. -->
        <div class="notes">
          <div class="state">{{ state.text }}</div>
          <div v-if="reading.tare_g > 0" class="tare">
            {{ t('weight.tareValue', { value: formatKg(reading.tare_g) }) }}
          </div>
        </div>
      </div>
    </div>

    <dl class="figures">
      <div class="figure price" :class="{ empty: !product }">
        <dt>{{ t('weight.price') }}</dt>
        <dd>{{ priceText }}</dd>
      </div>
      <div class="figure cost" :class="{ empty: !product }">
        <dt>{{ t('weight.cost') }}</dt>
        <dd>{{ costText }}</dd>
      </div>
    </dl>
  </div>
</template>

<style scoped>
.weight-panel {
  display: grid;
  /* показание с часами | цена и стоимость */
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 24px;
  padding: 12px 20px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
  border: 3px solid transparent;
  transition: border-color 0.2s;
}

.readout {
  display: flex;
  flex-direction: column;
  gap: 2px;
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
  gap: 10px;
}

/* Подписи прижаты к низу числа: так они читаются как продолжение показания,
   а не как отдельный столбец. */
.notes {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 6px;
  min-width: 0;
}

.status {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
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

/* Часы крупнее подписи связи: время смотрят чаще, чем состояние прибора */
.status .clock {
  margin-left: auto;
  padding-left: 18px;
  font-size: calc(21px * var(--ui-weight, 1));
  font-variant-numeric: tabular-nums;
  font-weight: 700;
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

/* Цена и стоимость — то, ради чего покупатель кладёт товар на платформу, и
   выглядят они соответственно: цена обведена акцентом, стоимость им залита.
   Место освободилось от кнопок тары и нуля, ушедших в админку. */
.figure {
  display: flex;
  flex: 1;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  padding: 10px 18px;
  border-radius: 14px;
}

.figure dt {
  font-size: calc(17px * var(--ui-weight, 1));
  white-space: nowrap;
}

.figure dd {
  margin: 0;
  font-size: calc(30px * var(--ui-weight, 1));
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.figure.price {
  background: var(--s2l-panel);
  border: 2px solid var(--s2l-accent);
}

.figure.price dt {
  color: var(--s2l-muted);
}

.figure.price dd {
  color: var(--s2l-accent);
}

/* Пока товар не выбран, показывать нечего: акцент на прочерке обещал бы число,
   которого нет. Блоки ждут выбора серыми. */
.figure.empty {
  background: var(--s2l-soft);
  border-color: transparent;
}

.figure.empty dt,
.figure.empty dd {
  color: var(--s2l-muted);
}

/* Сумма — единственное число, которое покупатель уносит с собой, поэтому она
   не подписана цветом, а залита им целиком. */
.figure.cost {
  background: var(--s2l-accent);
  border: 2px solid var(--s2l-accent);
}

.figure.cost dt {
  color: rgb(255 255 255 / 82%);
}

.figure.cost dd {
  font-size: calc(38px * var(--ui-weight, 1));
  color: #fff;
}

/* Заливку суммы снимаем адресно: правило `.figure.cost` идёт ниже общего
   `.figure.empty` и иначе перебивает его. */
.figure.cost.empty {
  background: var(--s2l-soft);
  border-color: transparent;
}

.figure.cost.empty dt,
.figure.cost.empty dd {
  color: var(--s2l-muted);
}
</style>
