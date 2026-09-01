<script setup lang="ts">
/**
 * Экранная клавиатура для поиска: своя, а не системная.
 *
 * Раскладка идёт за языком интерфейса — украинская и русская отличаются не только
 * буквами (і, ї, є, ґ против ы, э, ъ), и подсовывать покупателю чужую нельзя.
 * Клавиши гасят mousedown, чтобы поле ввода не теряло фокус при наборе.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

defineProps<{ hasText: boolean }>()

/**
 * Клавиатура сообщает о намерении, а строку меняет владелец состояния.
 * Если считать текущее значение из пропа, два быстрых нажатия в одном тике
 * прочитают одно и то же старое значение, и символ потеряется.
 */
const emit = defineEmits<{ key: [char: string]; backspace: []; clear: []; done: [] }>()

const DIGITS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

const LAYOUTS: Record<string, string[][]> = {
  uk: [
    ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ї'],
    ['ф', 'і', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'є'],
    ['я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', 'ґ'],
  ],
  ru: [
    ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ'],
    ['ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э'],
    ['я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю'],
  ],
}

const rows = computed(() => LAYOUTS[locale.value] ?? LAYOUTS.uk)

</script>

<template>
  <div class="keyboard" @mousedown.prevent>
    <div class="row digits">
      <button v-for="digit in DIGITS" :key="digit" class="key" @click="emit('key', digit)">
        {{ digit }}
      </button>
    </div>

    <div v-for="(row, index) in rows" :key="index" class="row">
      <button v-for="char in row" :key="char" class="key" @click="emit('key', char)">
        {{ char.toUpperCase() }}
      </button>
      <button v-if="index === rows.length - 1" class="key wide" @click="emit('backspace')">⌫</button>
    </div>

    <div class="row bottom">
      <button class="key action" :disabled="!hasText" @click="emit('clear')">
        {{ t('keyboard.clear') }}
      </button>
      <button class="key space" @click="emit('key', ' ')">{{ t('keyboard.space') }}</button>
      <button class="key action done" @click="emit('done')">{{ t('keyboard.done') }}</button>
    </div>
  </div>
</template>

<style scoped>
.keyboard {
  display: flex;
  flex-direction: column;
  gap: 8px;
  /* Ровно та высота, на которую киоск поднимает своё содержимое */
  height: var(--s2l-kb-height);
  padding: 12px 14px 16px;
  background: var(--s2l-kb-bg);
  border-top: 1px solid var(--s2l-kb-line);
  box-shadow: 0 -8px 24px var(--s2l-shadow-strong);
}

.row {
  display: flex;
  flex: 1;
  gap: 8px;
  justify-content: center;
  min-height: 0;
}

.key {
  flex: 1;
  /* Клавиша заведомо крупнее пальца: промах на киоске дороже лишнего места */
  min-width: 0;
  height: 100%;
  font-size: clamp(17px, 2vw, 23px);
  font-weight: 600;
  color: var(--s2l-ink);
  background: var(--s2l-key);
  border: none;
  border-radius: 10px;
  box-shadow: 0 1px 0 var(--s2l-key-shadow);
  cursor: pointer;
}

.key:active:not(:disabled) {
  background: var(--s2l-soft-active);
  transform: translateY(1px);
  box-shadow: none;
}

.key:disabled {
  color: var(--s2l-disabled-ink);
  cursor: default;
}

.digits {
  flex: 0.85;
}

.wide {
  flex: 0 0 96px;
}

.bottom {
  margin-top: 2px;
}

.action {
  flex: 0 0 190px;
  font-size: clamp(15px, 1.4vw, 18px);
}

.space {
  flex: 1;
  font-size: clamp(14px, 1.3vw, 17px);
  color: var(--s2l-muted);
}

.done {
  color: #ffffff;
  background: var(--s2l-accent);
  box-shadow: 0 1px 0 var(--s2l-accent-dark);
}

.done:active {
  background: var(--s2l-accent-dark);
}
</style>
