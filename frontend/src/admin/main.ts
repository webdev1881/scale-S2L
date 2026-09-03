import * as Icons from '@element-plus/icons-vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import { i18n } from '@/shared/i18n'
import '@/shared/styles/base.css'

import App from './App.vue'
import './styles.css'
import { router } from './router'

const app = createApp(App)
for (const [name, component] of Object.entries(Icons)) {
  app.component(name, component)
}
app.use(createPinia()).use(router).use(i18n).use(ElementPlus).mount('#app')
