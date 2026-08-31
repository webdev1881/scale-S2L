import { createRouter, createWebHashHistory } from 'vue-router'

// Хэш-роутинг: админка одинаково открывается и с dev-сервера (/admin.html),
// и из сборки, которую отдаёт FastAPI (/admin) — без правил на стороне сервера.
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/products' },
    { path: '/products', component: () => import('./views/ProductsView.vue') },
    { path: '/transactions', component: () => import('./views/TransactionsView.vue') },
    { path: '/simulator', component: () => import('./views/SimulatorView.vue') },
    { path: '/settings', component: () => import('./views/SettingsView.vue') },
  ],
})
