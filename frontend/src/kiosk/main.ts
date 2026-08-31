import ElementPlus from 'element-plus'
import ru from 'element-plus/es/locale/lang/ru'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import '@/shared/styles/base.css'

import App from './App.vue'

createApp(App).use(createPinia()).use(ElementPlus, { locale: ru }).mount('#app')
