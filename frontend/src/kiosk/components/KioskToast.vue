<script setup lang="ts">
/**
 * Крупное сообщение поверх каталога: «нет связи», «товар не найден», «заберите
 * товар». Обычный `ElMessage` в углу экрана покупатель у прибора не видит —
 * весы стоят дальше, чем монитор от разработчика, и мелкий текст без пульсации
 * теряется среди карточек. Размер, цвет, пульсация и время показа — настройка
 * админки, а не разработчика: у разных залов разная громкость важного сообщения.
 *
 * `blocking` — для беды, которая сама не пройдёт: кончилась бумага, открыта
 * крышка. Такое сообщение не тает по таймеру и накрывает экран: покупатель
 * иначе продолжает тыкать в карточки, а этикетки всё равно не будет.
 */
defineProps<{
  message: string
  fontSize: number
  color: string
  pulse: boolean
  blocking?: boolean
}>()
</script>

<template>
  <Transition name="kiosk-toast">
    <div v-if="message" class="kiosk-toast-wrap" :class="{ blocking }">
      <div class="kiosk-toast" :class="{ pulse }" :style="{ fontSize: `${fontSize}px`, background: color }">
        {{ message }}
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.kiosk-toast-wrap {
  position: fixed;
  top: 4vh;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3000;
  max-width: 86vw;
  /* Тост не должен перехватывать касание: он информирует, а не блокирует каталог. */
  pointer-events: none;
}

/* Блокирующее сообщение: тёмная пелена во весь экран, касания в неё и упираются.
   Сообщение посередине, а не сверху: смотреть больше не на что. */
.kiosk-toast-wrap.blocking {
  inset: 0;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: none;
  padding: 0 7vw;
  background: var(--s2l-splash-bg);
  transform: none;
  pointer-events: auto;
}

.kiosk-toast {
  padding: 0.7em 1.1em;
  border-radius: calc(var(--s2l-radius) * 1.5);
  box-shadow: 0 18px 48px var(--s2l-shadow-strong);
  color: #fff;
  font-weight: 700;
  line-height: 1.25;
  text-align: center;
  /* Перенос строки из самого текста («Закінчився папір» + строка про сотрудника):
     где рвать длинную фразу, решает перевод, а не ширина экрана. */
  white-space: pre-line;
}

.kiosk-toast.pulse {
  animation: kiosk-toast-pulse 1s ease-in-out infinite;
}

@keyframes kiosk-toast-pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.kiosk-toast-enter-active,
.kiosk-toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.kiosk-toast-enter-from,
.kiosk-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-16px);
}

@media (prefers-reduced-motion: reduce) {
  .kiosk-toast.pulse {
    animation: none;
  }
}
</style>
