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
          {{ generating ? '生成中...' : '生成剧本' }}
        </el-button>
      </div>

      <!-- 知识图谱展示区域 -->
      <div v-if="knowledgeGraph.nodes.length > 0" class="section">
        <h2 class="section-title">知识图谱</h2>
        <KnowledgeGraph 
          :nodes="knowledgeGraph.nodes" 
          :edges="knowledgeGraph.edges"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { getNovelDetail, getNovelChapters } from '@/api/novel'
  import { generateScript } from '@/api/script'
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

  // 知识图谱数据
  const knowledgeGraph = ref({
    nodes: [] as any[],
    edges: [] as any[]
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

  // 生成剧本
  const handleGenerateScript = async () => {
    if (selectedChapters.value.size === 0) {
      ElMessage.warning('请至少选择一章')
      return
    }

    generating.value = true

    try {
      const selectedChapterIds = Array.from(selectedChapters.value)
      const res: any = await generateScript({
        novel_id: novelId.value,
        chapter_ids: selectedChapterIds,
        config: {
          style: config.value.style,
          characters: config.value.characters,
          requirements: config.value.requirements
        }
      })

      ElMessage.success('剧本生成成功，知识图谱已提取')
      console.log('生成结果：', res)

      // 保存知识图谱数据
      if (res.knowledge_graph) {
        knowledgeGraph.value = res.knowledge_graph
      }
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '生成剧本失败')
      console.error(error)
    } finally {
      generating.value = false
    }
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
</style>