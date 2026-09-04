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
  /** Открыт ли цифровой блок: кнопка в шапке показывает это вдавленностью. */
  codeOpen: boolean
}>()
defineEmits<{ toggleCode: [] }>()
const { t } = useI18n()

const netKg = computed(() => formatKg(Math.max(props.reading.net_g, 0)))

// Пока товар не выбран, показываем нули, а не прочерк: место числа занято
// числом, и при выборе меняется только значение, а не вид блока.
const priceText = computed(() => {
  const per = props.product?.unit === 'piece' ? t('kiosk.perPiece') : t('kiosk.perKg')
  // Валюта стоит рядом в «Вартості» и в итоге внизу — в цене она только удлиняет
  // строку, из-за которой число приходится ужимать.
  return `${formatMoney(props.product?.price ?? 0)} ${per}`
})

// Стоимость пересчитывается на каждый отсчёт весов — покупатель видит сумму
// ещё до печати, а не узнаёт её из этикетки.
const costText = computed(() => `${formatMoney(props.total)} ${props.currency}`)

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
  <div class="weight-panel">
    <!-- Состояние весов красит рамку самой плитки показания, а не всей шапки:
         дрожание веса — свойство показания, а цена, сумма и набор кода к нему
         отношения не имеют. -->
    <div class="tile readout" :class="`tone-${state.tone}`">
      <!-- Часы и связь стоят строкой над показанием: за ними следят краем глаза,
           а вес — то, ради чего на этот блок смотрят. Кнопок тары и нуля здесь
           нет: это работа оператора, и её место в админке. -->
      <div class="status">
        <span class="dot" :class="{ ok: connected }"></span>
        <span class="conn">{{ connected ? t('kiosk.connected') : t('kiosk.disconnected') }}</span>
      </div>

      <div class="value">
        <span class="digits">{{ netKg }}</span>
        <span class="unit">кг</span>
        <!-- Подписи идут рядом с числом, а не под ним: на 768 px лишний ряд в
             шапке отнимает высоту у карточек. Пустая платформа сообщением не
             считается, но строка сохраняет высоту, чтобы шапка не дёргалась. -->
        <div class="notes">
          <!-- Стабильный вес сообщением не считается: это норма, а рамка плитки
               и так его показывает. Остаются только взвешивание и ошибки. -->
          <div class="state">{{ state.tone === 'ok' ? '' : state.text }}</div>
          <div v-if="reading.tare_g > 0" class="tare">
            {{ t('weight.tareValue', { value: formatKg(reading.tare_g) }) }}
          </div>
        </div>
      </div>
    </div>

    <dl class="figures">
      <div class="tile figure price">
        <dt>{{ t('weight.price') }}</dt>
        <dd>{{ priceText }}</dd>
      </div>
      <div class="tile figure cost">
        <dt>{{ t('weight.cost') }}</dt>
        <dd>{{ costText }}</dd>
      </div>
    </dl>

    <!-- Набор кода — тоже вход в каталог, и стоит он в шапке рядом с ценой:
         покупатель, который знает код, не ищет глазами строку поиска. -->
    <button class="tile code-toggle" :class="{ on: codeOpen }" @click="$emit('toggleCode')">
      <svg class="code-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="6" cy="6" r="1.8" />
        <circle cx="12" cy="6" r="1.8" />
        <circle cx="18" cy="6" r="1.8" />
        <circle cx="6" cy="12" r="1.8" />
        <circle cx="12" cy="12" r="1.8" />
        <circle cx="18" cy="12" r="1.8" />
        <circle cx="6" cy="18" r="1.8" />
        <circle cx="12" cy="18" r="1.8" />
        <circle cx="18" cy="18" r="1.8" />
      </svg>
      <span>{{ t('kiosk.byCode') }}</span>
    </button>
  </div>
</template>

<style scoped>
.weight-panel {
  display: grid;
  /* показание | цена | стоимость | набор кода. Первые три равной ширины: это
     величины одного порядка, и разный размер плиток делал из них иерархию,
     которой нет. */
  grid-template-columns: repeat(3, 1fr) auto;
  /* Плитки одинаковой высоты: шапка читается как один ряд, а не как число,
     к которому что-то приставили сбоку. */
  align-items: stretch;
  gap: 12px;
  padding: 12px;
  background: var(--s2l-panel);
  border-radius: var(--s2l-radius);
}

/* Общая форма всех блоков шапки: один радиус, одни отступы, одна высота.
   Содержимое прижато к верху, чтобы подписи всех плиток встали на одну строку:
   при центрировании их разводило по вертикали разной высотой содержимого. */
.tile {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 2px;
  min-width: 0;
  /* Отступы плиток идут за тем же ползунком, что и цифры: иначе увеличенное
     показание упирается в края собственной плитки. */
  padding: calc(10px * var(--ui-weight, 1)) calc(18px * var(--ui-weight, 1));
  border: 2px solid transparent;
  border-radius: 14px;
}

/* Показание обведено второстепенным цветом: та же рамка, что у цены и суммы,
   так что три плитки шапки читаются как один ряд, а не как разные блоки.
   Эта же рамка сообщает состояние весов — цветом, а не отдельным значком. */
.readout {
  background: var(--s2l-soft);
  border-color: var(--s2l-accent);
  transition: border-color 0.2s;
}

/* Спокойное состояние — тот же цвет, что и у соседних плиток: «стабильно» это
   норма, а не событие, ради которого шапке стоит менять вид. */
.readout.tone-ok {
  border-color: var(--s2l-accent);
}

.readout.tone-busy {
  border-color: var(--s2l-warn);
}

.readout.tone-error {
  border-color: var(--s2l-danger);
}

.value {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

/* Число занимает остаток плитки и стоит в нём по центру: подпись сверху уже
   выровнена с соседями, а число не должно липнуть к ней. */
.value,
.figure dd {
  margin-block: auto;
}

/* Строка подписи одной высоты во всех плитках — иначе числа под ней разъедутся.
   Высота задана точно, а не минимумом: у строки связи есть кружок индикатора, и
   по содержимому она выходила на пару пикселей ниже подписи цены. */
.status,
.figure dt {
  /* Обе подписи — flex по центру: у строки связи текст и так центрировался рядом
     с кружком индикатора, а подпись цены прижималась к верху своей коробки и
     оказывалась выше на несколько пикселей. */
  display: flex;
  align-items: center;
  height: calc(1.6em);
  font-size: calc(17px * var(--ui-weight, 1));
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
  /* Тот же кегль, что у подписей цены и стоимости: от него считается высота
     строки подписи, и разный размер разводил числа под ней на пару пикселей. */
  font-size: calc(17px * var(--ui-weight, 1));
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

.digits {
  /* Все числа шапки одного кегля: вес, цена и стоимость — величины одного
     порядка важности, и разный размер делал из них иерархию, которой нет. */
  font-size: calc(38px * var(--ui-weight, 1));
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  /* Табличные цифры + фиксированная ширина: число не «прыгает» при дрожании веса */
}

.unit {
  font-size: calc(22px * var(--ui-weight, 1));
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

/* Обёртка списка не рисуется и не занимает колонку: цена и стоимость встают в
   сетку шапки сами и получают там по равной доле. */
.figures {
  display: contents;
}

/* Кнопка набора кода — такая же плитка, как цена и стоимость, только цветом
   каталога: тот же радиус, та же высота, та же посадка на тень, что у кнопок
   поиска в каталоге. Имя класса не `code`: так называется код товара на
   карточке, а одинаковые имена в разных компонентах уже ловили коллизией. */
.code-toggle {
  align-items: center;
  flex-direction: row;
  gap: 12px;
  min-width: calc(190px * var(--ui-weight, 1));
  font-size: calc(20px * var(--ui-weight, 1));
  font-weight: 700;
  color: var(--ui-plate-ink, #f4f7fb);
  background: var(--ui-plate-bg, #1d2129);
  box-shadow: 0 2px 0 rgb(0 0 0 / 25%);
  cursor: pointer;
}

.code-icon {
  flex: none;
  width: calc(24px * var(--ui-weight, 1));
  height: calc(24px * var(--ui-weight, 1));
  fill: currentcolor;
}

/* Пока блок цифр открыт, кнопка стоит вдавленной: панель на экране и так видна,
   а смена цвета на произвольной заливке из настроек читалась бы хуже. */
.code-toggle.on,
.code-toggle:active {
  box-shadow: none;
  transform: translateY(2px);
}

/* Цена и стоимость — то, ради чего покупатель кладёт товар на платформу, и
   выглядят они соответственно: цена обведена акцентом, стоимость им залита.
   Место освободилось от кнопок тары и нуля, ушедших в админку. */
.figure {
  min-width: 0;
}

.figure dt {
  font-size: calc(17px * var(--ui-weight, 1));
  white-space: nowrap;
}

.figure dd {
  margin: 0;
  font-size: calc(38px * var(--ui-weight, 1));
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  /* Тот же интерлиньяж, что у показания: иначе коробка числа выше на треть строки
     и числа стоят на разной высоте при одинаковых подписях. */
  line-height: 1;
  white-space: nowrap;
}

.figure.price {
  background: var(--s2l-panel);
  border-color: var(--s2l-accent);
}

.figure.price dt {
  color: var(--s2l-muted);
}

.figure.price dd {
  color: var(--s2l-accent);
}

/* Сумма — единственное число, которое покупатель уносит с собой, поэтому она
   не подписана цветом, а залита им целиком. */
.figure.cost {
  background: var(--s2l-accent);
  border-color: var(--s2l-accent);
}

.figure.cost dt {
  color: var(--s2l-accent-ink, #fff);
  opacity: 0.82;
}

.figure.cost dd {
  color: var(--s2l-accent-ink, #fff);
}
</style>
