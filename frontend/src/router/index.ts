import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/UploadView.vue')
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraphView.vue')
  },
  {
    path: '/script',
    name: 'Script',
    component: () => import('@/views/ScriptView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
