import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/bookshelf',
    name: 'Bookshelf',
    component: () => import('@/views/BookshelfView.vue')
  },
  {
    path: '/novel/:id',
    name: 'NovelDetail',
    component: () => import('@/views/NovelDetailView.vue')
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
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryView.vue')
  },
  {
    path: '/script-editor',
    name: 'ScriptEditor',
    component: () => import('@/views/ScriptEditorView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
