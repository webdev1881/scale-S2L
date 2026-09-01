import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// переменные тёмной темы Element Plus включаются классом dark на <html>
import 'element-plus/theme-chalk/dark/css-vars.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import { i18n } from '@/shared/i18n'
import { applyTheme, storedTheme } from '@/shared/boot'
import '@/shared/styles/base.css'

import App from './App.vue'

// Тема прошлого запуска применяется до монтирования: иначе заставка успевает
// мигнуть чужим фоном, пока не пришли настройки с сервера.
applyTheme(storedTheme())

createApp(App).use(createPinia()).use(i18n).use(ElementPlus).mount('#app')
