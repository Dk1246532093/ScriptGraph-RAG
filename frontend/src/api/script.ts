import api from './request'

// 生成剧本（非流式，超时时间设置为5分钟）
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

// 流式生成剧本（SSE）
export const generateScriptStream = (
  data: {
    novel_id: string
    chapter_ids: string[]
    config?: {
      style?: string
      characters?: string
      requirements?: string
    }
  },
  handlers: {
    onProgress?: (data: { stage: string; message: string; progress: number; script_id?: string }) => void
    onScenesReady?: (data: { scenes: any[]; scene_count: number; progress: number }) => void
    onKnowledgeGraphReady?: (data: { knowledge_graph: { nodes: any[]; edges: any[] }; kg_node_count: number; kg_edge_count: number; progress: number }) => void
    onSceneGenerated?: (data: { scene: any; scene_index: number; total_scenes: number; progress: number; accumulated_beats: number; accumulated_lines: number }) => void
    onScriptReady?: (data: { script_scene_count: number; script_beat_count: number; script_line_count: number; progress: number }) => void
    onCompleted?: (data: { script_id: string; novel_id: string; novel_title: string; scene_count: number; kg_node_count: number; kg_edge_count: number }) => void
    onError?: (message: string) => void
  }
) => {
  const controller = new AbortController()

  // 使用 fetch API 直接发起 SSE 请求
  const start = async () => {
    try {
      const response = await fetch('/api/v1/scripts/generate/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(data),
        signal: controller.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is null')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 处理 SSE 事件
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const event of events) {
          const lines = event.split('\n')
          let eventType = ''
          let eventData = ''

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7)
            } else if (line.startsWith('data: ')) {
              eventData = line.slice(6)
            }
          }

          if (eventData) {
            try {
              const parsedData = JSON.parse(eventData)
              handleEvent(eventType, parsedData, handlers)
            } catch (e) {
              console.error('Failed to parse SSE data:', eventData)
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        handlers.onError?.(error.message || '请求失败')
      }
    }
  }

  const handleEvent = (
    eventType: string,
    data: any,
    handlers: any
  ) => {
          switch (eventType) {
            case 'progress':
              handlers.onProgress?.(data)
              break
            case 'scenes_ready':
              handlers.onScenesReady?.(data)
              break
            case 'knowledge_graph_ready':
              handlers.onKnowledgeGraphReady?.(data)
              break
            case 'scene_generated':
              handlers.onSceneGenerated?.(data)
              break
            case 'script_ready':
              handlers.onScriptReady?.(data)
              break
            case 'completed':
              handlers.onCompleted?.(data)
              break
            case 'error':
              handlers.onError?.(data.message)
              break
          }
  }

  return {
    start,
    abort: () => controller.abort()
  }
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

// 从已保存的剧本任务导出（GET）
export const exportScript = (
  scriptId: string,
  format: 'yaml' | 'json' | 'fountain' = 'yaml',
  download: boolean = true
) => {
  return api.get(
    `/scripts/${scriptId}/export`,
    {
      params: { format, download },
      responseType: download ? 'blob' : 'json'
    }
  )
}

// 从剧本数据直接导出（POST）- 支持前端修改后导出
export const exportScriptFromData = (
  scriptData: any[],
  format: 'yaml' | 'json' | 'fountain' = 'yaml',
  novelTitle: string = '',
  novelId: string = '',
  download: boolean = false
): Promise<string> => {
  return api.post(
    '/scripts/export',
    {
      script_data: scriptData,
      novel_title: novelTitle,
      novel_id: novelId,
      format,
      download
    },
    {
      responseType: 'text',
      transformResponse: [(data) => data] // 不自动解析 JSON，保持原始文本
    }
  ) as Promise<string>
}
