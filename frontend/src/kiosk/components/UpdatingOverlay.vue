<script setup lang="ts">
/**
 * Блокирующий экран на время, пока нет связи с бэкендом (перезапуск службы,
 * обновление прошивки, обрыв сети). Весы сами переподключаются по WebSocket
 * (см. `shared/weight.ts`) — киоск не перезагружается, а просто ждёт и не
 * даёт покупателю тыкать в каталог, который всё равно не отработает печать.
 */
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="updating">
    <!-- Сначала слово, потом картинка: покупатель у прибора читает экран сверху вниз,
         и первым он должен получить ответ «что происходит», а не разглядывать
         иллюстрацию. Картинка держит паузу и показывает, что прибор занят, а не сломан. -->
    <div class="wait">
      <div class="spinner"></div>
      <p class="label">{{ t('kiosk.updating') }}</p>
    </div>
    <img class="picture" src="/updating.jpg" alt="" draggable="false" />
  </div>
</template>

<style scoped>
.updating {
  position: fixed;
  inset: 0;
  z-index: 2500;
  cursor: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 40px;
  background: var(--s2l-splash-bg);
}

/* Доля экрана, а не пиксели: тот же приём, что у карточек каталога — прибор стоит
   дальше от покупателя, чем монитор от разработчика. Скругление и тень повторяют
   плитки киоска, чтобы картинка читалась как часть интерфейса, а не как обои. */
.picture {
  width: min(52vw, 720px);
  max-height: 46vh;
  object-fit: cover;
  border-radius: calc(var(--s2l-radius) * 1.5);
  box-shadow: 0 18px 48px var(--s2l-shadow-strong);
}

/* Ожидание идёт строкой: кружок рядом с надписью, а не под ней — иначе экран
   растягивается на всю высоту и картинке места не остаётся. */
.wait {
  display: flex;
  align-items: center;
  gap: 32px;
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
