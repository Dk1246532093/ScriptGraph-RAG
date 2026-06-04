import { defineStore } from 'pinia'
import { ref } from 'vue'

// 全局状态管理
export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const currentNovel = ref<string | null>(null)

  // 方法
  function setLoading(value: boolean) {
    loading.value = value
  }

  function setCurrentNovel(novelId: string | null) {
    currentNovel.value = novelId
  }

  return {
    loading,
    currentNovel,
    setLoading,
    setCurrentNovel
  }
})
