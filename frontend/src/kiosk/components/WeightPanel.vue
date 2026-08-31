<script setup lang="ts">
import { computed } from 'vue'

import { formatKg } from '@/shared/format'
import type { WeightReading } from '@/shared/types'

const props = defineProps<{ reading: WeightReading; connected: boolean }>()
defineEmits<{ tare: []; zero: [] }>()

const netKg = computed(() => formatKg(Math.max(props.reading.net_g, 0)))

const state = computed(() => {
  if (!props.connected) return { text: 'Нет связи с весами', tone: 'error' as const }
  if (props.reading.error) return { text: props.reading.error, tone: 'error' as const }
  if (props.reading.net_g < 5) return { text: 'Положите товар на платформу', tone: 'idle' as const }
  if (!props.reading.stable) return { text: 'Взвешивание…', tone: 'busy' as const }
  return { text: 'Вес стабилен', tone: 'ok' as const }
})
</script>

<template>
  <div class="weight-panel" :class="`tone-${state.tone}`">
    <div class="value">
      <span class="digits">{{ netKg }}</span>
      <span class="unit">кг</span>
    </div>

    <div class="state">{{ state.text }}</div>

    <div v-if="reading.tare_g > 0" class="tare">Тара: {{ formatKg(reading.tare_g) }} кг</div>

    <div class="actions">
      <button class="btn" @click="$emit('tare')">Тара</button>
      <button class="btn" @click="$emit('zero')">Ноль</button>
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
  background: #eef1f5;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.btn:active {
  background: #dfe4ea;
}
</style>
