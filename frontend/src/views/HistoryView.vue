<template>
  <div class="history-view">
    <div class="page-header">
      <h1>剧本生成历史</h1>
      <p class="subtitle">查看所有已生成的剧本记录</p>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list" v-loading="loading">
      <div v-if="historyList.length === 0" class="empty-state">
        <el-empty description="暂无历史记录" />
      </div>

      <div v-else class="history-cards">
        <div
          v-for="item in historyList"
          :key="item.script_id"
          class="history-card"
        >
          <div class="card-header">
            <h3 class="novel-title">{{ item.novel_title }}</h3>
            <el-tag :type="getStatusType(item.status)" size="small">
              {{ getStatusText(item.status) }}
            </el-tag>
          </div>

          <div class="card-meta">
            <span class="meta-item">
              <el-icon><Calendar /></el-icon>
              {{ formatDate(item.created_at) }}
            </span>
            <span class="meta-item">
              <el-icon><Document /></el-icon>
              {{ item.script_id.substring(0, 8) }}
            </span>
          </div>

          <div class="card-content">
            <div class="content-tags">
              <el-tag v-if="item.has_scenes" type="info" size="small">场景</el-tag>
              <el-tag v-if="item.has_knowledge_graph" type="success" size="small">知识图谱</el-tag>
              <el-tag v-if="item.has_script" type="warning" size="small">剧本</el-tag>
            </div>
          </div>

          <div class="card-actions">
            <el-button
              v-if="item.has_knowledge_graph"
              type="primary"
              size="small"
              @click.stop="viewKnowledgeGraph(item.script_id)"
            >
              <el-icon><Share /></el-icon> 查看图谱
            </el-button>
            <el-button
              v-if="item.has_script"
              type="success"
              size="small"
              @click.stop="viewScript(item.script_id)"
            >
              <el-icon><Reading /></el-icon> 查看剧本
            </el-button>
            <el-button
              v-if="item.has_script"
              type="info"
              size="small"
              @click.stop="handleExport(item.script_id, 'yaml')"
            >
              导出
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识图谱弹窗 -->
    <el-dialog
      v-model="kgVisible"
      title="知识图谱"
      width="90%"
      :fullscreen="isFullscreen"
    >
      <template #header>
        <div class="dialog-header">
          <span>知识图谱</span>
          <el-button link @click="isFullscreen = !isFullscreen">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </div>
      </template>

      <div v-if="kgLoading" class="detail-loading">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else-if="kgData" class="detail-content">
        <KnowledgeGraph
          :nodes="kgData.nodes || []"
          :edges="kgData.edges || []"
          height="600px"
        />
      </div>

      <div v-else class="empty-state">
        <el-empty description="暂无知识图谱数据" />
      </div>
    </el-dialog>

    <!-- 剧本弹窗 -->
    <el-dialog
      v-model="scriptVisible"
      :title="currentScriptTitle"
      width="90%"
      :fullscreen="isFullscreen"
    >
      <template #header>
        <div class="dialog-header">
          <span>{{ currentScriptTitle }} - 剧本</span>
          <el-button link @click="isFullscreen = !isFullscreen">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </div>
      </template>

      <div v-if="scriptLoading" class="detail-loading">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else-if="scriptData && scriptData.length > 0" class="detail-content">
        <div class="script-scenes">
          <div
            v-for="(scene, sIndex) in scriptData"
            :key="sIndex"
            class="scene-item"
          >
            <h4>{{ scene.title }}</h4>
            <div class="beats-list">
              <div
                v-for="(beat, bIndex) in scene.beats"
                :key="bIndex"
                class="beat-item"
              >
                <h5>{{ beat.title }} ({{ beat.theme }})</h5>
                <div class="lines-list">
                  <div
                    v-for="(line, lIndex) in beat.script"
                    :key="lIndex"
                    class="line-item"
                  >
                    <div class="line-header">
                      <span class="character">{{ line.character }}</span>
                      <span v-if="line.expression" class="expression">({{ line.expression }})</span>
                    </div>
                    <div v-if="line.action" class="action">
                      <span class="label">动作：</span>{{ line.action }}
                    </div>
                    <div class="dialogue">
                      <span class="label">语言：</span>{{ line.voice?.text || line.text }}
                    </div>
                    <div v-if="line.voice?.emotion || line.voice?.tone" class="voice-info">
                      <span v-if="line.voice?.emotion" class="voice-tag emotion">情绪：{{ line.voice.emotion }}</span>
                      <span v-if="line.voice?.tone" class="voice-tag tone">语气：{{ line.voice.tone }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-empty description="暂无剧本数据" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Calendar, Document, FullScreen, Share, Reading } from '@element-plus/icons-vue'
import { getScriptHistory, getScriptHistoryDetail, exportScript } from '@/api/script'
import KnowledgeGraph from '@/components/KnowledgeGraph.vue'

interface HistoryItem {
  script_id: string
  novel_title: string
  novel_id: string
  status: string
  created_at: string
  updated_at: string
  config: any
  has_scenes: boolean
  has_knowledge_graph: boolean
  has_script: boolean
}

const loading = ref(false)
const historyList = ref<HistoryItem[]>([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref<any>(null)
const isFullscreen = ref(false)
const activeTab = ref('info') // info, kg, script

// 知识图谱弹窗
const kgVisible = ref(false)
const kgData = ref<any>(null)
const kgLoading = ref(false)

// 剧本弹窗
const scriptVisible = ref(false)
const scriptData = ref<any>(null)
const scriptLoading = ref(false)
const currentScriptTitle = ref('')

// 获取历史记录列表
const fetchHistory = async () => {
  loading.value = true
  try {
    const response = await getScriptHistory()
    historyList.value = response.history || []
  } catch (error: any) {
    ElMessage.error(`获取历史记录失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 查看详情
const viewDetail = async (scriptId: string) => {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null

  try {
    const response = await getScriptHistoryDetail(scriptId)
    detailData.value = response
  } catch (error: any) {
    ElMessage.error(`获取详情失败: ${error.message || '未知错误'}`)
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

// 查看知识图谱
const viewKnowledgeGraph = async (scriptId: string) => {
  kgVisible.value = true
  kgLoading.value = true
  kgData.value = null

  try {
    const response = await getScriptHistoryDetail(scriptId)
    kgData.value = response.knowledge_graph
  } catch (error: any) {
    ElMessage.error(`获取知识图谱失败: ${error.message || '未知错误'}`)
    kgVisible.value = false
  } finally {
    kgLoading.value = false
  }
}

// 查看剧本
const viewScript = async (scriptId: string) => {
  scriptVisible.value = true
  scriptLoading.value = true
  scriptData.value = null

  try {
    const response = await getScriptHistoryDetail(scriptId)
    scriptData.value = response.script || []
    currentScriptTitle.value = response.task?.novel_title || '剧本'
  } catch (error: any) {
    ElMessage.error(`获取剧本失败: ${error.message || '未知错误'}`)
    scriptVisible.value = false
  } finally {
    scriptLoading.value = false
  }
}

// 导出剧本
const handleExport = async (scriptId: string, format: 'yaml' | 'json' | 'fountain') => {
  try {
    const response = await exportScript(scriptId, format, false)
    const content = response as unknown as string

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `剧本_${scriptId.substring(0, 8)}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(`已导出 ${format.toUpperCase()} 格式`)
  } catch (error: any) {
    ElMessage.error(`导出失败: ${error.message || '未知错误'}`)
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'scenes_generated': 'success',
    'kg_generated': 'success',
    'script_generated': 'success',
    'completed': 'success',
    'failed': 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'scenes_generated': '场景已生成',
    'kg_generated': '知识图谱已生成',
    'script_generated': '剧本已生成',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #303133;
}

.page-header .subtitle {
  color: #909399;
  margin: 0;
}

.history-list {
  min-height: 200px;
}

.empty-state {
  padding: 60px 0;
}

.history-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.history-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
}

.history-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.history-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.history-card .card-header .novel-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #303133;
  flex: 1;
  margin-right: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-card .card-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  color: #909399;
  font-size: 13px;
}

.history-card .card-meta .meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.history-card .card-content {
  margin-bottom: 16px;
}

.history-card .card-content .content-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.history-card .card-actions {
  display: flex;
  gap: 10px;
}

/* 详情弹窗样式 */
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.detail-loading {
  padding: 40px;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 10px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
  color: #303133;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.script-scenes .scene-item {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.script-scenes .scene-item h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #303133;
}

.script-scenes .scene-item .beats-list .beat-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
}

.script-scenes .scene-item .beats-list .beat-item h5 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px;
  color: #606266;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item:last-child {
  border-bottom: none;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .line-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .character {
  font-weight: 600;
  color: #409eff;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .expression {
  font-size: 13px;
  color: #909399;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .action {
  font-size: 13px;
  color: #722ed1;
  margin-bottom: 4px;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .action .label {
  font-weight: 600;
  color: #531dab;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .dialogue {
  color: #303133;
  line-height: 1.6;
  margin-bottom: 4px;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .dialogue .label {
  font-weight: 600;
  color: #262626;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .voice-info {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .voice-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .voice-tag.emotion {
  color: #52c41a;
  background: #f6ffed;
}

.script-scenes .scene-item .beats-list .beat-item .lines-list .line-item .voice-tag.tone {
  color: #1890ff;
  background: #e6f7ff;
}
</style>
