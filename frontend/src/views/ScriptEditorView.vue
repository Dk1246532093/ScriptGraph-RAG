<template>
  <div class="script-editor-view">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h1>剧本编辑 - {{ novelTitle }}</h1>
      </div>
      <div class="header-actions">
        <el-dropdown @command="handleExport" :disabled="scriptData.length === 0">
          <el-button type="success">
            <el-icon><Download /></el-icon> 导出<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="yaml">导出 YAML</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
              <el-dropdown-item command="fountain">导出 Fountain</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="scriptData.length > 0" class="editor-container">
      <!-- 场景列表侧边栏 -->
      <div class="scene-sidebar">
        <div class="sidebar-header">
          <h3>场景列表</h3>
          <span class="scene-count">{{ scriptData.length }} 个场景</span>
        </div>
        <div class="scene-list">
          <div
            v-for="(scene, sIndex) in scriptData"
            :key="sIndex"
            :class="['scene-list-item', { active: currentSceneIndex === sIndex }]"
            @click="selectScene(sIndex)"
          >
            <div class="scene-item-title">场景 {{ sIndex + 1 }}: {{ scene.title }}</div>
            <div class="scene-item-meta">
              <span class="meta-location">{{ scene.location }}</span>
              <span class="meta-beats">{{ scene.beats?.length || 0 }} 节拍</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 编辑区域 -->
      <div class="editor-content">
        <div v-if="currentScene" class="scene-editor">
          <!-- 场景信息 -->
          <div class="section scene-info-section">
            <h3 class="section-title">场景信息</h3>
            <div class="form-row">
              <el-form-item label="场景标题" class="flex-2">
                <el-input v-model="currentScene.title" placeholder="场景标题" />
              </el-form-item>
              <el-form-item label="地点" class="flex-1">
                <el-input v-model="currentScene.location" placeholder="地点" />
              </el-form-item>
            </div>
            <el-form-item label="场景概述">
              <el-input
                v-model="currentScene.summary"
                type="textarea"
                :rows="2"
                placeholder="场景概述"
              />
            </el-form-item>
          </div>

          <!-- Beats 列表 -->
          <div class="section beats-section">
            <div class="section-header">
              <h3 class="section-title">节拍列表 ({{ currentScene.beats?.length || 0 }})</h3>
              <el-button type="primary" size="small" @click="addBeat">
                <el-icon><Plus /></el-icon> 添加节拍
              </el-button>
            </div>

            <div class="beats-list">
              <div
                v-for="(beat, bIndex) in currentScene.beats"
                :key="bIndex"
                class="beat-card"
              >
                <div class="beat-header">
                  <span class="beat-number">节拍 {{ bIndex + 1 }}</span>
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="removeBeat(bIndex)"
                  >
                    <el-icon><Delete /></el-icon> 删除
                  </el-button>
                </div>

                <div class="beat-form">
                  <div class="form-row">
                    <el-form-item label="标题" class="flex-2">
                      <el-input v-model="beat.title" placeholder="节拍标题" />
                    </el-form-item>
                    <el-form-item label="主题" class="flex-1">
                      <el-input v-model="beat.theme" placeholder="主题" />
                    </el-form-item>
                  </div>
                  <div class="form-row">
                    <el-form-item label="地点" class="flex-1">
                      <el-input v-model="beat.location" placeholder="具体地点" />
                    </el-form-item>
                    <el-form-item label="氛围" class="flex-1">
                      <el-input v-model="beat.atmosphere" placeholder="氛围描述" />
                    </el-form-item>
                  </div>

                  <!-- 台词列表 -->
                  <div class="script-lines-section">
                    <div class="lines-header">
                      <span class="lines-title">台词列表 ({{ beat.script?.length || 0 }})</span>
                      <el-button type="primary" link size="small" @click="addLine(bIndex)">
                        <el-icon><Plus /></el-icon> 添加台词
                      </el-button>
                    </div>

                    <div class="lines-list">
                      <div
                        v-for="(line, lIndex) in beat.script"
                        :key="lIndex"
                        class="line-card"
                      >
                        <div class="line-header">
                          <span class="line-number">#{{ lIndex + 1 }}</span>
                          <el-button
                            type="danger"
                            link
                            size="small"
                            @click="removeLine(bIndex, lIndex)"
                          >
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </div>

                        <div class="line-form">
                          <div class="form-row">
                            <el-form-item label="角色" class="flex-1">
                              <el-input v-model="line.character" placeholder="角色名" />
                            </el-form-item>
                            <el-form-item label="表情" class="flex-1">
                              <el-input v-model="line.expression" placeholder="表情（如：痛苦、坚定）" />
                            </el-form-item>
                          </div>
                          <el-form-item label="动作">
                            <el-input
                              v-model="line.action"
                              type="textarea"
                              :rows="2"
                              placeholder="动作描述"
                            />
                          </el-form-item>
                          <div class="form-row">
                            <el-form-item label="情绪" class="flex-1">
                              <el-input
                                v-model="line.voice.emotion"
                                placeholder="情绪（如：决绝、悲伤）"
                              />
                            </el-form-item>
                            <el-form-item label="语气" class="flex-1">
                              <el-input
                                v-model="line.voice.tone"
                                placeholder="语气（如：低沉、颤抖）"
                              />
                            </el-form-item>
                          </div>
                          <el-form-item label="台词内容">
                            <el-input
                              v-model="line.voice.text"
                              type="textarea"
                              :rows="3"
                              placeholder="台词内容"
                            />
                          </el-form-item>
                        </div>
                      </div>
                    </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowDown, Download, Plus, Delete } from '@element-plus/icons-vue'
import { getScriptHistoryDetail, exportScriptFromData } from '@/api/script'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const scriptId = ref('')
const novelTitle = ref('')
const scriptData = ref<any[]>([])
const currentSceneIndex = ref(0)

// 当前选中的场景
const currentScene = computed(() => {
  if (scriptData.value.length === 0) return null
  return scriptData.value[currentSceneIndex.value]
})

// 获取剧本数据
const fetchScriptData = async () => {
  const id = route.query.scriptId as string
  if (!id) {
    ElMessage.error('缺少剧本ID')
    router.push('/history')
    return
  }

  scriptId.value = id
  loading.value = true

  try {
    const response = await getScriptHistoryDetail(id)
    scriptData.value = response.script || []
    novelTitle.value = response.task?.novel_title || '未知小说'
  } catch (error: any) {
    ElMessage.error(`获取剧本失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 选择场景
const selectScene = (index: number) => {
  currentSceneIndex.value = index
}

// 添加节拍
const addBeat = () => {
  if (!currentScene.value) return

  if (!currentScene.value.beats) {
    currentScene.value.beats = []
  }

  currentScene.value.beats.push({
    beat_id: `beat_${Date.now()}`,
    title: '新节拍',
    theme: '',
    location: currentScene.value.location || '',
    atmosphere: '',
    characters: [],
    script: []
  })

  ElMessage.success('已添加节拍')
}

// 删除节拍
const removeBeat = async (index: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个节拍吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (currentScene.value && currentScene.value.beats) {
      currentScene.value.beats.splice(index, 1)
      ElMessage.success('已删除')
    }
  } catch {
    // 用户取消
  }
}

// 添加台词
const addLine = (beatIndex: number) => {
  if (!currentScene.value) return

  const beat = currentScene.value.beats[beatIndex]
  if (!beat.script) {
    beat.script = []
  }

  beat.script.push({
    character: '',
    expression: '',
    action: '',
    voice: {
      emotion: '',
      tone: '',
      text: ''
    }
  })

  ElMessage.success('已添加台词')
}

// 删除台词
const removeLine = async (beatIndex: number, lineIndex: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这句台词吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const beat = currentScene.value?.beats[beatIndex]
    if (beat && beat.script) {
      beat.script.splice(lineIndex, 1)
      ElMessage.success('已删除')
    }
  } catch {
    // 用户取消
  }
}

// 导出剧本
const handleExport = async (format: 'yaml' | 'json' | 'fountain') => {
  if (scriptData.value.length === 0) {
    ElMessage.warning('暂无剧本可导出')
    return
  }

  try {
    const content = await exportScriptFromData(
      scriptData.value,
      format,
      novelTitle.value,
      '',
      false
    )

    // 创建 Blob 并下载
    const blob = new Blob([content as string], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    const extension = format === 'fountain' ? 'fountain' : format
    link.download = `${novelTitle.value || '剧本'}_编辑版.${extension}`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(`已导出 ${format.toUpperCase()} 格式剧本`)
  } catch (error: any) {
    ElMessage.error(`导出失败: ${error.message || '未知错误'}`)
  }
}

// 返回上一页
const goBack = () => {
  router.push('/history')
}

onMounted(() => {
  fetchScriptData()
})
</script>

<style scoped>
.script-editor-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.back-btn {
  padding: 8px 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.loading-container {
  padding: 40px;
}

.empty-state {
  padding: 60px 0;
}

/* 编辑器布局 */
.editor-container {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  min-height: calc(100vh - 200px);
}

/* 侧边栏 */
.scene-sidebar {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 200px);
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.scene-count {
  font-size: 13px;
  color: #909399;
}

.scene-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.scene-list-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.scene-list-item:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
}

.scene-list-item.active {
  background: #ecf5ff;
  border-color: #409eff;
}

.scene-item-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scene-item-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.meta-beats {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 编辑区域 */
.editor-content {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  padding: 24px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .el-form-item {
  margin-bottom: 16px;
}

.flex-1 {
  flex: 1;
}

.flex-2 {
  flex: 2;
}

/* Beat 卡片 */
.beat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.beat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.beat-number {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

/* 台词列表 */
.script-lines-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #dcdfe6;
}

.lines-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.lines-title {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.line-card {
  background: #fff;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
}

.line-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.line-number {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.line-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }

  :deep(.el-form-item__label) {
    font-size: 13px;
    color: #606266;
  }
}
</style>
