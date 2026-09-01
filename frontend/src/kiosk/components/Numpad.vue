<script setup lang="ts">
/**
 * Экранная клавиатура собственная, а не системная (squeekboard/onboard):
 * на киоске нужен полный контроль раскладки и никакой зависимости от сессии ОС.
 */
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{ value: string }>()
const emit = defineEmits<{ 'update:value': [value: string]; submit: [] }>()

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'C', '0', '⌫']

function press(key: string) {
  if (key === 'C') return emit('update:value', '')
  if (key === '⌫') return emit('update:value', props.value.slice(0, -1))
  if (props.value.length >= 5) return
  emit('update:value', props.value + key)
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
}

.display {
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
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.key {
  min-height: 64px;
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
  min-height: 60px;
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
