import api from './request'

// 生成剧本
export const generateScript = (data: {
  novel_id: string
  chapter_ids: string[]
  config?: {
    style?: string
    characters?: string
    requirements?: string
  }
}) => {
  return api.post('/scripts/generate', data)
}

// 获取剧本详情
export const getScript = (scriptId: string) => {
  return api.get(`/scripts/${scriptId}`)
}

// 获取剧本列表
export const getScripts = (novelId?: string) => {
  const params = novelId ? { novel_id: novelId } : {}
  return api.get('/scripts', { params })
}
