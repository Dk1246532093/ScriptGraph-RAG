<template>
  <div class="script-generate-view">
    <div class="page-header">
      <h1>生成剧本 - {{ novelTitle }}</h1>
    </div>

    <div class="content-container">
      <!-- 选择章节区域 -->
      <div class="section">
        <h2 class="section-title">选择章节</h2>

        <!-- 快速选择 -->
        <div class="quick-select">
          <span class="label">快速选择：第</span>
          <el-input-number v-model="quickStart" :min="1" :max="Math.max(1, chapters.length)" controls-position="right"
            class="number-input" />
          <span class="label">章到第</span>
          <el-input-number v-model="quickEnd" :min="1" :max="Math.max(1, chapters.length)" controls-position="right"
            class="number-input" />
          <span class="label">章</span>
          <el-button type="primary" @click="applyQuickSelect" class="apply-btn">应用</el-button>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button @click="selectAll">全选</el-button>
          <el-button @click="clearAll">清空</el-button>
        </div>

        <!-- 章节网格 -->
        <div class="chapters-grid">
          <div v-for="chapter in chapters" :key="chapter.id"
            :class="['chapter-card', { selected: selectedChapters.has(chapter.id) }]"
            @click="toggleChapter(chapter.id)">
            {{ chapter.title }}
          </div>
        </div>

        <!-- 已选择统计 -->
        <div class="selected-info">
          已选择：{{ selectedRangeText }}（共 {{ selectedChapters.size }} 章）
        </div>
      </div>

      <!-- 生成按钮 -->
      <div class="generate-section">
        <el-button type="primary" size="large" :disabled="selectedChapters.size === 0 || generating"
          :loading="generating" @click="handleGenerateScript">
          {{ generating ? generateProgressText : '生成剧本' }}
        </el-button>
        <el-button v-if="generating && currentStream" size="large" @click="handleCancelGenerate">
          取消
        </el-button>
      </div>

      <!-- 进度条 -->
      <div v-if="generating" class="section progress-section">
        <div class="progress-info">
          <span class="stage-name">{{ currentStage }}</span>
          <span class="progress-percent">{{ progress }}%</span>
        </div>
        <el-progress :percentage="progress" :status="progressStatus" />
        <div class="progress-message">{{ progressMessage }}</div>
      </div>

      <!-- 场景列表 -->
      <div v-if="scenes.length > 0" class="section">
        <h2 class="section-title">场景分镜 ({{ scenes.length }} 个场景)</h2>
        <div class="scenes-list">
          <div v-for="(scene, index) in scenes" :key="index" class="scene-item">
            <div class="scene-header">
              <span class="scene-number">场景 {{ index + 1 }}</span>
              <span class="scene-title">{{ scene.scene_title || '未命名场景' }}</span>
            </div>
            <div class="scene-info">
              <span class="info-tag">地点: {{ scene.location || '未知' }}</span>
              <span class="info-tag">人物: {{ scene.characters?.join(', ') || '无' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 知识图谱展示区域 -->
      <div v-if="knowledgeGraph.nodes.length > 0" class="section">
        <h2 class="section-title">
          知识图谱 
          <span class="subtitle">({{ knowledgeGraph.nodes.length }} 节点, {{ knowledgeGraph.edges.length }} 关系)</span>
        </h2>
        <KnowledgeGraph 
          :nodes="knowledgeGraph.nodes" 
          :edges="knowledgeGraph.edges"
        />
      </div>

      <!-- 剧本展示区域：左场景列表 + 右剧本内容 -->
      <div v-if="scriptScenes.length > 0" class="script-display-section">
        <!-- 左侧：场景列表 -->
        <div class="scene-sidebar">
          <div class="sidebar-header">
            <h3>场景列表</h3>
            <span class="scene-count">{{ scriptScenes.length }} 个场景</span>
          </div>
          <div class="scene-list">
            <div 
              v-for="(scene, index) in scriptScenes" 
              :key="index" 
              :class="['scene-list-item', { active: selectedSceneIndex === index }]"
              @click="selectScene(index)"
            >
              <div class="scene-item-title">场景 {{ index + 1 }}: {{ scene.title }}</div>
              <div class="scene-item-meta">
                <span class="meta-location">📍 {{ scene.location }}</span>
                <span class="meta-beats">{{ scene.beats?.length || 0 }} 节拍</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：剧本内容 -->
        <div class="script-content-area">
          <div v-if="currentScene" class="script-content">
            <!-- 场景标题 -->
            <div class="content-header">
              <h3>{{ currentScene.title }}</h3>
              <div class="scene-info-bar">
                <span class="info-item">📍 {{ currentScene.location }}</span>
                <span class="info-item" v-if="currentScene.summary">💡 {{ currentScene.summary }}</span>
              </div>
            </div>

            <!-- Beat 内容 -->
            <div v-if="currentBeat" class="beat-content">
              <div class="beat-header">
                <span class="beat-tag">节拍 {{ currentBeatIndex + 1 }}/{{ currentScene.beats?.length || 0 }}</span>
                <h4 class="beat-title">{{ currentBeat.title }}</h4>
                <div class="beat-meta">
                  <span class="meta-item">主题: {{ currentBeat.theme }}</span>
                  <span class="meta-item">氛围: {{ currentBeat.atmosphere }}</span>
                  <span class="meta-item">角色: {{ currentBeat.characters?.join(', ') }}</span>
                </div>
              </div>

              <!-- 台词列表 -->
              <div class="script-lines">
                <div 
                  v-for="(line, lIndex) in currentBeat.script" 
                  :key="lIndex" 
                  class="script-line"
                >
                  <div class="character-info">
                    <span class="character-name">{{ line.character }}</span>
                    <span class="character-expression" v-if="line.expression">{{ line.expression }}</span>
                  </div>
                  <div class="line-content">
                    <div class="action-text" v-if="line.action">【{{ line.action }}】</div>
                    <div class="dialogue-text">{{ line.voice?.text || line.text }}</div>
                    <div class="voice-info" v-if="line.voice">
                      <span class="voice-tag">情绪: {{ line.voice.emotion }}</span>
                      <span class="voice-tag">语气: {{ line.voice.tone }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 分页控制 -->
            <div class="beat-pagination">
              <el-pagination
                v-model:current-page="currentBeatPage"
                :page-size="1"
                :total="currentScene.beats?.length || 0"
                layout="prev, pager, next, jumper"
                :pager-count="5"
              />
              <span class="page-info">
                共 {{ currentScene.beats?.length || 0 }} 个节拍
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 剧本统计 -->
      <div v-if="scriptStats.scene_count > 0" class="section stats-section">
        <h2 class="section-title">剧本生成结果</h2>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ scriptStats.scene_count }}</div>
            <div class="stat-label">场景数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ scriptStats.beat_count }}</div>
            <div class="stat-label">节拍数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ scriptStats.line_count }}</div>
            <div class="stat-label">台词数</div>
          </div>
        </div>
        <div class="script-actions" v-if="generatedScriptId">
          <el-button type="success" @click="viewScript">查看完整剧本</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { getNovelDetail, getNovelChapters } from '@/api/novel'
  import { generateScriptStream } from '@/api/script'
  import KnowledgeGraph from '@/components/KnowledgeGraph.vue'

  const route = useRoute()
  const router = useRouter()

  const novelId = ref('')
  const novelTitle = ref('')
  const chapters = ref < any[] > ([])
  const selectedChapters = ref < Set < string >> (new Set())
  const quickStart = ref(1)
  const quickEnd = ref(10)
  const generating = ref(false)

  const config = ref({
    style: '',
    characters: '',
    requirements: ''
  })

  // 流式生成状态
  const progress = ref(0)
  const currentStage = ref('')
  const progressMessage = ref('')
  const scenes = ref<any[]>([])
  const currentStream = ref<{ start: () => Promise<void>; abort: () => void } | null>(null)
  const generatedScriptId = ref('')
  const totalScriptScenes = ref(0)  // 剧本总场景数
  const scriptScenes = ref<any[]>([])  // 实时生成的剧本场景列表
  const scriptStats = ref({
    scene_count: 0,
    beat_count: 0,
    line_count: 0
  })

  // 剧本阅读器状态
  const selectedSceneIndex = ref(0)  // 当前选中的场景索引
  const currentBeatPage = ref(1)  // 当前beat页码（从1开始）

  // 当前选中的场景
  const currentScene = computed(() => {
    if (scriptScenes.value.length === 0) return null
    return scriptScenes.value[selectedSceneIndex.value] || null
  })

  // 当前beat索引（从0开始）
  const currentBeatIndex = computed(() => {
    return currentBeatPage.value - 1
  })

  // 当前选中的beat
  const currentBeat = computed(() => {
    if (!currentScene.value) return null
    return currentScene.value.beats?.[currentBeatIndex.value] || null
  })

  // 知识图谱数据
  const knowledgeGraph = ref({
    nodes: [] as any[],
    edges: [] as any[]
  })

  // 进度条状态
  const progressStatus = computed(() => {
    if (progress.value === 100) return 'success'
    return ''
  })

  // 进度显示文本
  const generateProgressText = computed(() => {
    if (progress.value > 0) {
      return `生成中 ${progress.value}%`
    }
    return '生成中...'
  })

  // 计算已选择的章节范围文本
  const selectedRangeText = computed(() => {
    if (selectedChapters.value.size === 0) {
      return '未选择'
    }

    const indices = chapters.value
      .map((c, i) => selectedChapters.value.has(c.id) ? i + 1 : null)
      .filter(i => i !== null) as number[]

    if (indices.length === 0) {
      return '未选择'
    }

    // 找出连续区间
    const ranges: string[] = []
    let start = indices[0]
    let end = indices[0]

    for (let i = 1; i <= indices.length; i++) {
      if (i < indices.length && indices[i] === end + 1) {
        end = indices[i]
      } else {
        if (start === end) {
          ranges.push(`第 ${start} 章`)
        } else {
          ranges.push(`第 ${start}-${end} 章`)
        }
        if (i < indices.length) {
          start = end = indices[i]
        }
      }
    }

    return ranges.join('、')
  })

  // 获取小说信息
  const fetchNovelInfo = async () => {
    const id = route.query.novelId as string
    if (!id) {
      ElMessage.error('缺少小说ID')
      router.push('/bookshelf')
      return
    }

    novelId.value = id

    try {
      const [novelRes, chaptersRes] = await Promise.all([
        getNovelDetail(id),
        getNovelChapters(id)
      ])

      novelTitle.value = (novelRes as any).title || '未知小说'
      chapters.value = chaptersRes.data || chaptersRes || []

      // 默认选择前10章
      const defaultEnd = Math.min(10, chapters.value.length)
      quickEnd.value = defaultEnd
      for (let i = 0; i < defaultEnd; i++) {
        selectedChapters.value.add(chapters.value[i].id)
      }
    } catch (error) {
      ElMessage.error('获取小说信息失败')
      console.error(error)
    }
  }

  // 快速选择应用
  const applyQuickSelect = () => {
    if (quickStart.value > quickEnd.value) {
      ElMessage.warning('起始章节不能大于结束章节')
      return
    }

    selectedChapters.value.clear()
    for (let i = quickStart.value - 1; i < quickEnd.value && i < chapters.value.length; i++) {
      selectedChapters.value.add(chapters.value[i].id)
    }

    ElMessage.success(`已选择第 ${quickStart.value}-${quickEnd.value} 章`)
  }

  // 全选
  const selectAll = () => {
    chapters.value.forEach(ch => selectedChapters.value.add(ch.id))
  }

  // 清空
  const clearAll = () => {
    selectedChapters.value.clear()
  }

  // 切换章节选择
  const toggleChapter = (chapterId: string) => {
    if (selectedChapters.value.has(chapterId)) {
      selectedChapters.value.delete(chapterId)
    } else {
      selectedChapters.value.add(chapterId)
    }
  }

  // 重置生成状态
  const resetGenerateState = () => {
    progress.value = 0
    currentStage.value = ''
    progressMessage.value = ''
    scenes.value = []
    knowledgeGraph.value = { nodes: [], edges: [] }
    generatedScriptId.value = ''
    totalScriptScenes.value = 0
    scriptScenes.value = []
    scriptStats.value = { scene_count: 0, beat_count: 0, line_count: 0 }
    selectedSceneIndex.value = 0
    currentBeatPage.value = 1
  }

  // 选择场景
  const selectScene = (index: number) => {
    selectedSceneIndex.value = index
    currentBeatPage.value = 1  // 切换到新场景时重置到第一页
  }

  // 取消生成
  const handleCancelGenerate = () => {
    currentStream.value?.abort()
    generating.value = false
    currentStream.value = null
    ElMessage.info('已取消生成')
  }

  // 查看剧本
  const viewScript = () => {
    if (generatedScriptId.value) {
      router.push({
        path: '/script-detail',
        query: { scriptId: generatedScriptId.value }
      })
    }
  }

  // 流式生成剧本
  const handleGenerateScript = async () => {
    if (selectedChapters.value.size === 0) {
      ElMessage.warning('请至少选择一章')
      return
    }

    // 重置状态
    resetGenerateState()
    generating.value = true

    const selectedChapterIds = Array.from(selectedChapters.value)

    // 创建流式请求
    const stream = generateScriptStream(
      {
        novel_id: novelId.value,
        chapter_ids: selectedChapterIds,
        config: {
          style: config.value.style,
          characters: config.value.characters,
          requirements: config.value.requirements
        }
      },
      {
        // 进度更新
        onProgress: (data) => {
          progress.value = data.progress
          currentStage.value = getStageDisplayName(data.stage)
          progressMessage.value = data.message
          console.log(`[${data.stage}] ${data.message} (${data.progress}%)`)
        },

        // 场景分割完成
        onScenesReady: (data) => {
          scenes.value = data.scenes
          progress.value = data.progress
          ElMessage.success(`场景分割完成，共 ${data.scene_count} 个场景`)
        },

        // 知识图谱抽取完成
        onKnowledgeGraphReady: (data) => {
          knowledgeGraph.value = data.knowledge_graph
          progress.value = data.progress
          ElMessage.success(`知识图谱抽取完成，共 ${data.kg_node_count} 个节点`)
        },

        // 单个场景生成完成（流式）
        onSceneGenerated: (data) => {
          scriptScenes.value.push(data.scene)
          totalScriptScenes.value = data.total_scenes
          progress.value = data.progress
          scriptStats.value = {
            scene_count: data.scene_index + 1,
            beat_count: data.accumulated_beats,
            line_count: data.accumulated_lines
          }
          console.log(`Scene ${data.scene_index + 1}/${data.total_scenes} received`)
        },

        // 剧本生成完成
        onScriptReady: (data) => {
          scriptStats.value = {
            scene_count: data.script_scene_count,
            beat_count: data.script_beat_count,
            line_count: data.script_line_count
          }
          progress.value = data.progress
          console.log('剧本统计:', scriptStats.value)
        },

        // 全部完成
        onCompleted: (data) => {
          generating.value = false
          currentStream.value = null
          generatedScriptId.value = data.script_id
          progress.value = 100
          currentStage.value = '完成'
          progressMessage.value = '剧本生成全部完成！'
          ElMessage.success('剧本生成全部完成！')
        },

        // 错误处理
        onError: (message) => {
          generating.value = false
          currentStream.value = null
          ElMessage.error(message || '生成剧本失败')
        }
      }
    )

    currentStream.value = stream
    await stream.start()
  }

  // 获取阶段显示名称
  const getStageDisplayName = (stage: string): string => {
    const stageNames: Record<string, string> = {
      validating: '验证',
      initialized: '初始化',
      scene_splitting: '场景分割',
      knowledge_graph: '知识图谱抽取',
      script_generating: '剧本生成'
    }
    return stageNames[stage] || stage
  }

  onMounted(() => {
    fetchNovelInfo()
  })
</script>

<style scoped>
  .script-generate-view {
    padding: 40px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-header {
    margin-bottom: 30px;
  }

  .page-header h1 {
    font-size: 28px;
    font-weight: 600;
    color: #303133;
  }

  .content-container {
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  .section {
    background: #fff;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  }

  .section-title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e4e7ed;
  }

  .quick-select {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 6px;
  }

  .label {
    color: #606266;
    font-size: 14px;
  }

  .number-input {
    width: 100px;
  }

  .apply-btn {
    margin-left: 8px;
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
  }

  .chapters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }

  .chapter-card {
    padding: 12px 16px;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 14px;
    color: #606266;
    background: #fff;
  }

  .chapter-card:hover {
    border-color: #409eff;
    color: #409eff;
  }

  .chapter-card.selected {
    background: #409eff;
    border-color: #409eff;
    color: #fff;
  }

  .selected-info {
    padding: 16px;
    background: #ecf5ff;
    border-radius: 6px;
    color: #409eff;
    font-size: 14px;
  }

  .generate-section {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }

  .generate-section .el-button {
    width: 200px;
    height: 48px;
    font-size: 16px;
  }

  /* 进度条区域 */
  .progress-section {
    background: #f0f9ff;
    border: 1px solid #91d5ff;
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .stage-name {
    font-size: 16px;
    font-weight: 600;
    color: #1890ff;
  }

  .progress-percent {
    font-size: 18px;
    font-weight: 600;
    color: #1890ff;
  }

  .progress-message {
    margin-top: 10px;
    color: #666;
    font-size: 14px;
  }

  /* 场景列表 */
  .scenes-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .scene-item {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 6px;
    border-left: 4px solid #409eff;
  }

  .scene-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }

  .scene-number {
    background: #409eff;
    color: #fff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
  }

  .scene-title {
    font-weight: 600;
    color: #303133;
  }

  .scene-info {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .info-tag {
    color: #606266;
    font-size: 13px;
  }

  /* 知识图谱副标题 */
  .subtitle {
    font-size: 14px;
    font-weight: normal;
    color: #909399;
    margin-left: 8px;
  }

  /* 统计区域 */
  .stats-section {
    background: #f6ffed;
    border: 1px solid #b7eb8f;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 24px;
  }

  .stat-item {
    text-align: center;
    padding: 20px;
    background: #fff;
    border-radius: 8px;
  }

  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #52c41a;
    margin-bottom: 8px;
  }

  .stat-label {
    font-size: 14px;
    color: #666;
  }

  .script-actions {
    display: flex;
    justify-content: center;
    padding-top: 16px;
    border-top: 1px solid #d9f7be;
  }

  /* 剧本展示区域：左右布局 */
  .script-display-section {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 24px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
    overflow: hidden;
    min-height: 600px;
  }

  /* 左侧场景列表 */
  .scene-sidebar {
    background: #f5f7fa;
    border-right: 1px solid #e4e7ed;
    display: flex;
    flex-direction: column;
  }

  .sidebar-header {
    padding: 20px;
    background: #fff;
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
    padding: 14px;
    background: #fff;
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

  .meta-location {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 60%;
  }

  .meta-beats {
    background: #e6f7ff;
    color: #1890ff;
    padding: 2px 8px;
    border-radius: 10px;
  }

  /* 右侧剧本内容 */
  .script-content-area {
    padding: 24px;
    display: flex;
    flex-direction: column;
  }

  .script-content {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .content-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 2px solid #e4e7ed;
  }

  .content-header h3 {
    margin: 0 0 12px 0;
    font-size: 22px;
    color: #303133;
  }

  .scene-info-bar {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .info-item {
    font-size: 13px;
    color: #606266;
    background: #f5f7fa;
    padding: 6px 12px;
    border-radius: 4px;
  }

  /* Beat 内容 */
  .beat-content {
    flex: 1;
    background: #fafafa;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 20px;
  }

  .beat-header {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e4e7ed;
  }

  .beat-tag {
    display: inline-block;
    background: #722ed1;
    color: #fff;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 12px;
    margin-bottom: 8px;
  }

  .beat-title {
    margin: 0 0 12px 0;
    font-size: 18px;
    color: #303133;
  }

  .beat-meta {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .meta-item {
    font-size: 13px;
    color: #606266;
  }

  /* 台词列表 */
  .script-lines {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .script-line {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid #52c41a;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  .character-info {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
  }

  .character-name {
    font-weight: 600;
    font-size: 16px;
    color: #303133;
  }

  .character-expression {
    font-size: 12px;
    color: #909399;
    background: #f5f7fa;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .line-content {
    padding-left: 12px;
  }

  .action-text {
    font-size: 13px;
    color: #722ed1;
    margin-bottom: 8px;
    font-style: italic;
  }

  .dialogue-text {
    font-size: 15px;
    color: #303133;
    line-height: 1.8;
    margin-bottom: 8px;
  }

  .voice-info {
    display: flex;
    gap: 12px;
  }

  .voice-tag {
    font-size: 12px;
    color: #52c41a;
    background: #f6ffed;
    padding: 2px 8px;
    border-radius: 4px;
  }

  /* 分页控制 */
  .beat-pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 16px;
    border-top: 1px solid #e4e7ed;
  }

  .page-info {
    font-size: 14px;
    color: #606266;
  }
</style>