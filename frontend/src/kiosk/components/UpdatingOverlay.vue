<script setup lang="ts">
/**
 * Блокирующий экран на время, пока нет связи с бэкендом (перезапуск службы,
 * обновление прошивки, обрыв сети). Весы сами переподключаются по WebSocket
 * (см. `shared/weight.ts`) — киоск не перезагружается, а просто ждёт и не
 * даёт покупателю тыкать в каталог, который всё равно не отработает печать.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{ photoScale: number; textPosition: number }>()

// Картинка — фон, надпись с крутилкой — поверх неё своей панелью, поэтому
// размер картинки задаётся отдельно и может дорасти до всего экрана: при
// желании оператор гасит панель настроек вовсе (0%) или растягивает картинку
// во весь киоск.
const pictureStyle = computed(() => ({
  width: `${props.photoScale}vw`,
  height: `${props.photoScale}vh`,
}))

// Доля высоты экрана, а не пиксели: 0 — панель прижата к самому верху, 100 —
// к низу. Диапазон широкий специально: под разные картинки и вкусы оператора
// подходит разное место, а не только «сверху» или «по центру».
const waitStyle = computed(() => ({ top: `${props.textPosition}vh` }))
</script>

<template>
  <div class="updating">
    <img
      v-if="photoScale > 0"
      class="picture"
      :style="pictureStyle"
      src="/updating.jpg"
      alt=""
      draggable="false"
    />
    <!-- Своя панель, а не голый текст на фоне: при большой картинке надпись должна
         читаться поверх неё, а не спорить с сюжетом фотографии. -->
    <div class="wait" :style="waitStyle">
      <div class="spinner"></div>
      <p class="label">{{ t('kiosk.updating') }}</p>
    </div>
  </div>
</template>

<style scoped>
.updating {
  position: fixed;
  inset: 0;
  z-index: 2500;
  cursor: none;
  background: var(--s2l-splash-bg);
}

/* Доля экрана, а не пиксели: тот же приём, что у карточек каталога — прибор стоит
   дальше от покупателя, чем монитор от разработчика. Центр экрана — независимо
   от размера, поэтому позиционирование абсолютное, а не в потоке с надписью. */
.picture {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  object-fit: cover;
  border-radius: calc(var(--s2l-radius) * 1.5);
  box-shadow: 0 18px 48px var(--s2l-shadow-strong);
  transition:
    width 0.2s ease,
    height 0.2s ease;
}

/* Покупатель читает экран сверху вниз: сперва ответ «что происходит», потом
   иллюстрация. Абсолютное позиционирование — картинка её не толкает своим
   размером, даже когда та растянута на весь экран. */
.wait {
  position: absolute;
  left: 50%;
  z-index: 1;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 28px 48px;
  background: var(--s2l-panel);
  border-radius: calc(var(--s2l-radius) * 1.5);
  box-shadow: 0 18px 48px var(--s2l-shadow-strong);
}

.spinner {
  flex: none;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  border: 9px solid var(--s2l-soft);
  border-top-color: var(--s2l-accent);
  animation: spin 0.9s linear infinite;
}

.label {
  margin: 0;
  font-size: 64px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--s2l-ink);
}

/* При «уменьшенном движении» кружок не крутится: остаётся картинка и надпись —
   их достаточно, чтобы понять, что прибор занят. */
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
