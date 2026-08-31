import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import { i18n } from '@/shared/i18n'
import '@/shared/styles/base.css'

import App from './App.vue'

createApp(App).use(createPinia()).use(i18n).use(ElementPlus).mount('#app')
