// 全局类型定义

// 章节
export interface Chapter {
  id: number
  title: string
  content: string
}

// 人物节点
export interface Character {
  id: string
  name: string
  type: 'Character'
  description?: string
}

// 地点节点
export interface Location {
  id: string
  name: string
  type: 'Location'
  description?: string
}

// 事件节点
export interface Event {
  id: string
  name: string
  type: 'Event'
  description?: string
}

// 知识图谱节点
export type KGNode = Character | Location | Event

// 知识图谱边
export interface KGEdge {
  source: string
  target: string
  relation: string
  strength?: number
}

// 知识图谱数据
export interface KnowledgeGraph {
  nodes: KGNode[]
  edges: KGEdge[]
}

// 剧本对话
export interface Dialogue {
  speaker: string
  emotion: string
  action: string
  text: string
}

// 剧本场景
export interface Scene {
  id: string
  location: string
  time: string
  summary: string
  dialogues: Dialogue[]
}

// 剧本
export interface Script {
  title: string
  characters: { id: string; name: string }[]
  scenes: Scene[]
}
