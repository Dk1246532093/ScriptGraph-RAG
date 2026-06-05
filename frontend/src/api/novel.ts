import api from './request'

// 获取小说列表
export const getNovels = () => {
  return api.get('/novels')
}

// 上传小说
export const uploadNovel = (formData: FormData) => {
  // 不设置 Content-Type，让浏览器自动设置（包含 boundary）
  return api.post('/novels/upload', formData)
}

// 获取小说详情
export const getNovelDetail = (id: string) => {
  return api.get(`/novels/${id}`)
}

// 获取小说章节列表
export const getNovelChapters = (id: string) => {
  return api.get(`/novels/${id}/chapters`)
}

// 获取章节内容
export const getChapterContent = (novelId: string, chapterId: string) => {
  return api.get(`/novels/${novelId}/chapters/${chapterId}`)
}

// 删除小说
export const deleteNovel = (id: string) => {
  return api.delete(`/novels/${id}`)
}
