<script setup lang="ts">
/**
 * Крупное сообщение поверх каталога: «нет связи», «товар не найден», «заберите
 * товар». Обычный `ElMessage` в углу экрана покупатель у прибора не видит —
 * весы стоят дальше, чем монитор от разработчика, и мелкий текст без пульсации
 * теряется среди карточек. Размер, цвет, пульсация и время показа — настройка
 * админки, а не разработчика: у разных залов разная громкость важного сообщения.
 */
defineProps<{
  message: string
  fontSize: number
  color: string
  pulse: boolean
}>()
</script>

<template>
  <Transition name="kiosk-toast">
    <div v-if="message" class="kiosk-toast-wrap">
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

.kiosk-toast {
  padding: 0.7em 1.1em;
  border-radius: calc(var(--s2l-radius) * 1.5);
  box-shadow: 0 18px 48px var(--s2l-shadow-strong);
  color: #fff;
  font-weight: 700;
  line-height: 1.25;
  text-align: center;
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
