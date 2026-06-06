<template>
  <div class="knowledge-graph">
    <!-- 图谱容器 -->
    <div ref="graphContainer" class="graph-container"></div>
    
    <!-- 图例 -->
    <div class="graph-legend">
      <div class="legend-item">
        <span class="legend-dot character"></span>
        <span>人物 ({{ stats.characters }})</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot location"></span>
        <span>地点 ({{ stats.locations }})</span>
      </div>
      <div class="legend-item">
        <span class="legend-line"></span>
        <span>关系 ({{ edges.length }})</span>
      </div>
    </div>
    
    <!-- 控制按钮 -->
    <div class="graph-controls">
      <el-button size="small" @click="fitGraph">
        <el-icon><FullScreen /></el-icon> 适应屏幕
      </el-button>
      <el-button size="small" @click="resetLayout">
        <el-icon><RefreshRight /></el-icon> 重置布局
      </el-button>
    </div>
    
    <!-- 节点详情弹窗 -->
    <div v-if="selectedNode" class="node-panel">
      <div class="panel-header">
        <h3>{{ selectedNode.name }}</h3>
        <el-icon class="close-btn" @click="selectedNode = null"><Close /></el-icon>
      </div>
      <div class="panel-body">
        <p class="node-type">
          <el-tag :type="selectedNode.type === 'Character' ? 'primary' : 'success'">
            {{ selectedNode.type === 'Character' ? '人物' : '地点' }}
          </el-tag>
        </p>
        <p class="node-desc">{{ selectedNode.description }}</p>
        
        <!-- 相关关系 -->
        <div v-if="relatedEdges.length > 0" class="related-edges">
          <h4>相关关系：</h4>
          <ul>
            <li v-for="(edge, idx) in relatedEdges" :key="idx">
              {{ edge.description }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FullScreen, RefreshRight, Close } from '@element-plus/icons-vue'

interface Node {
  id: string
  name: string
  type: 'Character' | 'Location'
  description?: string
}

interface Edge {
  source: string
  target: string
  relation: string
  description: string
  category: string
  bidirectional?: boolean
}

interface Props {
  nodes: Node[]
  edges: Edge[]
}

const props = defineProps<Props>()

const graphContainer = ref<HTMLElement | null>(null)
const cy = ref<any>(null)
const selectedNode = ref<Node | null>(null)

// 统计信息
const stats = computed(() => ({
  characters: props.nodes.filter(n => n.type === 'Character').length,
  locations: props.nodes.filter(n => n.type === 'Location').length
}))

// 与选中节点相关的关系
const relatedEdges = computed(() => {
  if (!selectedNode.value) return []
  return props.edges.filter(
    e => e.source === selectedNode.value!.id || e.target === selectedNode.value!.id
  )
})

// 初始化 Cytoscape
const initGraph = () => {
  if (!graphContainer.value) return
  
  // 动态导入 cytoscape
  import('cytoscape').then((cytoscapeModule) => {
    const cytoscape = cytoscapeModule.default || cytoscapeModule
    
    // 准备数据
    const cyNodes = props.nodes.map(node => ({
      data: {
        id: node.id,
        name: node.name,
        type: node.type,
        description: node.description,
        color: node.type === 'Character' ? '#409eff' : '#67c23a',
        size: node.type === 'Character' ? 40 : 30
      }
    }))
    
    const cyEdges = props.edges.map((edge, idx) => ({
      data: {
        id: `e${idx}`,
        source: edge.source,
        target: edge.target,
        relation: edge.relation,
        description: edge.description,
        bidirectional: edge.bidirectional
      }
    }))
    
    // 创建图谱
    cy.value = cytoscape({
      container: graphContainer.value,
      elements: [...cyNodes, ...cyEdges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'width': 'data(size)',
            'height': 'data(size)',
            'label': 'data(name)',
            'font-size': '12px',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 5,
            'color': '#333',
            'border-width': 2,
            'border-color': '#fff',
            'border-opacity': 1,
            'shadow-blur': 10,
            'shadow-color': '#ccc',
            'shadow-opacity': 0.5
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#909399',
            'target-arrow-color': '#909399',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.2
          }
        },
        {
          selector: 'edge[bidirectional = true]',
          style: {
            'source-arrow-shape': 'triangle',
            'source-arrow-color': '#909399'
          }
        },
        {
          selector: ':selected',
          style: {
            'border-width': 4,
            'border-color': '#f56c6c'
          }
        }
      ],
      layout: {
        name: 'cose',
        padding: 50,
        nodeRepulsion: 8000,
        idealEdgeLength: 100,
        animate: true
      }
    })
    
    // 点击节点事件
    cy.value.on('tap', 'node', (evt: any) => {
      const nodeData = evt.target.data()
      selectedNode.value = {
        id: nodeData.id,
        name: nodeData.name,
        type: nodeData.type,
        description: nodeData.description
      }
    })
    
    // 点击空白处取消选择
    cy.value.on('tap', (evt: any) => {
      if (evt.target === cy.value) {
        selectedNode.value = null
      }
    })
    
    // 运行布局
    runLayout()
  })
}

// 运行布局
const runLayout = () => {
  if (!cy.value) return
  
  cy.value.layout({
    name: 'cose',
    padding: 50,
    nodeRepulsion: 8000,
    idealEdgeLength: 120,
    edgeElasticity: 100,
    nestingFactor: 5,
    gravity: 30,
    numIter: 1000,
    animate: true,
    animationDuration: 500
  }).run()
}

// 适应屏幕
const fitGraph = () => {
  if (!cy.value) return
  cy.value.fit()
}

// 重置布局
const resetLayout = () => {
  runLayout()
}

// 监听数据变化
watch(() => props.nodes, () => {
  if (cy.value) {
    cy.value.destroy()
  }
  initGraph()
}, { deep: true })

onMounted(() => {
  initGraph()
})

onUnmounted(() => {
  if (cy.value) {
    cy.value.destroy()
  }
})
</script>

<style scoped>
.knowledge-graph {
  position: relative;
  width: 100%;
  height: 500px;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.graph-container {
  width: 100%;
  height: 100%;
}

/* 图例 */
.graph-legend {
  position: absolute;
  top: 15px;
  right: 15px;
  background: #fff;
  padding: 12px 15px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.character {
  background: #409eff;
}

.legend-dot.location {
  background: #67c23a;
}

.legend-line {
  width: 20px;
  height: 2px;
  background: #909399;
}

/* 控制按钮 */
.graph-controls {
  position: absolute;
  bottom: 15px;
  left: 15px;
  display: flex;
  gap: 8px;
}

/* 节点详情面板 */
.node-panel {
  position: absolute;
  top: 15px;
  left: 15px;
  width: 280px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.close-btn {
  cursor: pointer;
  color: #909399;
  font-size: 16px;
}

.close-btn:hover {
  color: #f56c6c;
}

.panel-body {
  padding: 15px;
}

.node-type {
  margin: 0 0 10px 0;
}

.node-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.related-edges {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.related-edges h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #303133;
}

.related-edges ul {
  margin: 0;
  padding-left: 18px;
}

.related-edges li {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
