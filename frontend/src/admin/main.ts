import * as Icons from '@element-plus/icons-vue'
import ElementPlus from 'element-plus'
import ru from 'element-plus/es/locale/lang/ru'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import '@/shared/styles/base.css'

import App from './App.vue'
import { router } from './router'

const app = createApp(App)
for (const [name, component] of Object.entries(Icons)) {
  app.component(name, component)
}
app.use(createPinia()).use(router).use(ElementPlus, { locale: ru }).mount('#app')
