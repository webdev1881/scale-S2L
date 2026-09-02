<script setup lang="ts">
/**
 * Экранная клавиатура собственная, а не системная (squeekboard/onboard):
 * на киоске нужен полный контроль раскладки и никакой зависимости от сессии ОС.
 */
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{ value: string }>()
/**
 * Клавиши только сообщают о нажатии, строку меняет её владелец. Если считать
 * текущее значение из пропа, два быстрых нажатия в одном тике прочитают одно и
 * то же старое значение и цифра потеряется.
 */
const emit = defineEmits<{ key: [value: string]; backspace: []; clear: []; submit: [] }>()

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'C', '0', '⌫']

function press(key: string) {
  if (key === 'C') return emit('clear')
  if (key === '⌫') return emit('backspace')
  emit('key', key)
}
</script>

<template>
  <div class="numpad">
    <div class="display">{{ value || '—' }}</div>
    <div class="keys">
      <button v-for="key in KEYS" :key="key" class="key" @click="press(key)">{{ key }}</button>
    </div>
    <button class="submit" :disabled="!value" @click="emit('submit')">
      {{ t('numpad.find') }}
    </button>
  </div>
</template>

<style scoped>
.numpad {
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* Блок выезжает справа поверх карточек и занимает всю высоту сетки, а не
     фиксированную высоту клавиатуры: цели касания от этого только крупнее. */
  height: 100%;
  padding: 12px 14px 16px;
  background: var(--s2l-kb-bg);
  border-left: 1px solid var(--s2l-kb-line);
}

.display {
  flex: none;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: var(--s2l-soft);
  border-radius: 12px;
}

.keys {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(4, 1fr);
  gap: 10px;
  min-height: 0;
  max-width: 420px;
  align-self: center;
  width: 100%;
}

.key {
  min-height: 0;
  font-size: 24px;
  font-weight: 600;
  background: var(--s2l-panel);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.key:active {
  background: var(--s2l-soft-active);
}

.submit {
  flex: none;
  min-height: 56px;
  font-size: 19px;
  font-weight: 600;
  color: #fff;
  background: var(--s2l-accent);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.submit:disabled {
  background: var(--s2l-disabled);
}
</style>
