import api from './request'

// 生成剧本（超时时间设置为5分钟，因为AI处理可能需要较长时间）
export const generateScript = (data: {
  novel_id: string
  chapter_ids: string[]
  config?: {
    style?: string
    characters?: string
    requirements?: string
  }
}) => {
  return api.post('/scripts/generate', data, {
    timeout: 300000  // 5分钟
  })
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
